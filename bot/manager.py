import datetime
import functools
import logging
import math
import time
import traceback
from multiprocessing.pool import ThreadPool

import feedparser
import mastodon
import requests
import schedule
from packaging import version
from sqlalchemy import func

from .engine import get_session
from .mastodon import MastodonStreamListener
from .models import Mastodon, Server, Admin, UpdateType


class MastodonManager():

    def __init__(self, db_url: str, domain: str, token: str, debug=False):
        self.Session = get_session(db_url)
        self.logger = logging.getLogger(__name__)
        self.debug = debug

        if self.debug:
            self.logger.warning('Running on DEBUG mode')

        self.api = mastodon.Mastodon(
            api_base_url=f'https://{domain}/',
            access_token=token
        )

        self.stream_listener = MastodonStreamListener(self.api, self.Session, debug=debug)

    def should_notify(self, last_notified: datetime.datetime):
        if last_notified is None:
            return True

        session = self.Session()
        release_date = session.query(Mastodon).one().updated
        # Days from release to last notified
        days_notified = (last_notified - release_date).days
        # Days from release to now
        days_passed = (self.utcnow() - release_date).days
        self.logger.debug(f'Days notified: {days_notified}, passed: {days_passed}')

        # 0, 1, 2, 4, 8
        try:
            notified_level = math.log(days_notified, 2) if days_notified else -1
        except ValueError:
            notified_level = -1
        passed_level = math.log(days_passed, 2) if days_passed else -1

        session.close()

        return passed_level - notified_level >= 1 and days_passed >= 1

    def check_mastodon_release(self):
        """
        Check latest mastodon release.
        Return (version: str, is_new: bool)
        """
        feed = feedparser.parse('https://github.com/tootsuite/mastodon/releases.atom')
        latest_release = feed.entries[0]

        current_version = latest_release.title
        current_updated = latest_release.updated

        session = self.Session()
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

        session.close()

        return current_version, is_new

    def check_and_notify(self, domain: str, release: str):
        try:
            session = self.Session()
            server = session.query(Server).filter(Server.domain == domain).one()
            self.logger.debug(f'Checking {server.domain}')
            server_version = requests.get(f'https://{domain}/api/v1/instance').json()['version']

            if server.version != server_version:
                server.last_notified = None

            server.last_fetched = func.now()
            server.version = server_version
        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error(f'Error while checking {domain}')
            session.close()
            return

        if version.parse(server_version) < version.parse(release):
            self.logger.info(f'{domain} is still {server_version}')
            if self.should_notify(server.last_notified):
                self.logger.info(f'Notify to {domain}')
                self.notify_admins(domain, release)
                server.last_notified = func.now()
            else:
                self.logger.debug(f'Not notifying to {domain}')

        session.commit()
        session.close()

    def job(self):
        self.logger.debug('Starting job')
        session = self.Session()
        release, is_new = self.check_mastodon_release()
        self.logger.info(f'Latest release: {release}')
        if is_new:
            self.logger.info(f'New version: {release}')
            self.notify_new_version(release)
        else:
            pool = ThreadPool()
            pool.starmap(self.check_and_notify, (
                (server.domain, release)
                for server in session.query(Server).all()
            ))
            pool.close()
            pool.join()

        session.close()

    def run(self):
        me = self.api.account_verify_credentials()
        self.logger.info(f'I am {me.acct}')
        self.logger.info('Starting mastodon stream')
        self.stream_listener.stream_user(run_async=True, reconnect_async=True)

        self.logger.info('Scheduling jobs')
        if self.debug:
            schedule.every(10).seconds.do(self.job)
        else:
            schedule.every(1).hours.do(self.job)
        schedule.run_all()
        while True:
            schedule.run_pending()
            time.sleep(5)

    def notify_admins(self, domain, release):
        session = self.Session()
        server = session.query(Server).filter_by(domain=domain).first()
        if not server:
            return

        release_date = session.query(Mastodon).first().updated
        days_passed = (self.utcnow() - release_date).days

        for admin in server.admins:
            if admin.update_type == UpdateType.stable and self.is_rc(release):
                continue

            self.post(
                f'@{admin.acct}\n'
                f'{release}가 릴리즈 된 지 {days_passed}일 지났어요\n'
                f'https://github.com/tootsuite/mastodon/releases/{release}',
                visibility='unlisted'
            )

        session.close()

    def notify_new_version(self, release: str):
        self.post(
            f'새로운 마스토돈 {release}가 릴리즈 되었어요!!\n'
            f'https://github.com/tootsuite/mastodon/releases/{release}',
            visibility='public'
        )

        session = self.Session()
        for admin in session.query(Admin).all():
            if admin.update_type == UpdateType.stable and self.is_rc(release):
                continue

            self.post(
                f'@{admin.acct}\n'
                f'새로운 마스토돈 {release}가 릴리즈 되었어요\n'
                f'https://github.com/tootsuite/mastodon/releases/{release}',
                visibility='unlisted'
            )

        session.close()

    @functools.wraps(mastodon.Mastodon.status_post)
    def post(self, status, *args, **kwargs):
        if self.debug:
            self.logger.info(status)
        else:
            try:
                self.api.status_post(status, *args, **kwargs)
            except mastodon.MastodonError as e:
                self.logger.error(traceback.format_exc())

    @staticmethod
    def is_rc(release):
        return 'rc' in release

    @staticmethod
    def utcnow():
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def get_server_version(domain: str):
        try:
            return requests.get(f'https://{domain}/api/v1/instance').json()['version']
        except Exception:
            return None
