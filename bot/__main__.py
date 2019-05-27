import datetime
import os
import time

from multiprocessing.pool import ThreadPool

import feedparser
import requests
import schedule

from packaging import version
from sqlalchemy import func

from .engine import get_session
from .models import Mastodon, Server, Admin

DATABASE_URL = os.getenv('DATABASE_URL')


Session = get_session(DATABASE_URL)


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def get_server_version(domain: str):
    try:
        return requests.get(f'https://{domain}/api/v1/instance').json()['version']
    except Exception:
        return None


def check_mastodon_release():
    """
    Check latest mastodon release.
    Return (version: str, is_new: bool)
    """
    feed = feedparser.parse('https://github.com/tootsuite/mastodon/releases.atom')
    latest_release = feed.entries[0]

    current_version = latest_release.title
    current_updated = latest_release.updated

    session = Session()
    is_new = False
    try:
        mastodon = session.query(Mastodon).one()
        old_version = version.parse(mastodon.version)
        new_version = version.parse(current_version)

        if old_version < new_version:
            is_new = True
            mastodon.version = current_version
            mastodon.updated = current_updated
            session.commit()
    except Exception:
        mastodon = Mastodon()
        mastodon.version = current_version
        mastodon.updated = current_updated
        session.add(mastodon)
        session.commit()

    return current_version, is_new


def check_and_notify(domain: str, release: str):
    try:
        session = Session()
        server = session.query(Server).filter(Server.domain == domain).one()
        print(f'Checking {server.domain}')
        server_version = requests.get(f'https://{domain}/api/v1/instance').json()['version']

        if server.version != server_version:
            server.last_notified = None

        server.last_fetched = func.now()
        server.version = server_version

        session.commit()
    except Exception as e:
        print(e)
        return

    if version.parse(server_version) < version.parse(release):
        print(f'{domain} is still {server_version}')
        if not server.last_notified or utcnow() - server.last_notified > datetime.timedelta(days=1):
            print(f'Notify to {domain}')
            server.last_notified = func.now()

        session.commit()


def do_job():
    print('Starting job')
    session = Session()
    release, is_new = check_mastodon_release()
    print(f'Latest release: {release}')
    if is_new:
        print(f'New version: {release}')
    else:
        pool = ThreadPool()
        for server in session.query(Server).all():
            pool.apply_async(check_and_notify, args=(server.domain, release))

        pool.close()
        pool.join()



schedule.every(1).minutes.do(do_job)
schedule.run_all()
while True:
    schedule.run_pending()
    time.sleep(5)
