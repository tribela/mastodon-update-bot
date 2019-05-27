import functools
import logging
import re

import mastodon

from lxml import html

from .models import Admin, Server, get_or_create


PATTERN_REGISTER = re.compile(r'\bregister\b')
PATTERN_UNREGISTER = re.compile(r'\bunregister\b')


class MastodonStreamListener(mastodon.StreamListener):

    def __init__(self, api: mastodon.Mastodon, sessionmaker):
        super().__init__()
        self.api = api
        self.Session = sessionmaker
        self.logger = logging.getLogger(__name__)
        self.domain = api.instance().uri

    def on_notification(self, notification):
        if notification['type'] == 'follow':
            self.handle_follow(notification)
        if notification['type'] == 'mention':
            self.handle_mention(notification)

    def handle_follow(self, notification: dict):
        try:
            account = notification['account']
            self.logger.info(f'{account["acct"]} is following me')
        except mastodon.MastodonAPIError as e:
            self.logger.error(e)

    def handle_mention(self, notification: dict):
        account = notification['account']
        status = notification['status']
        content = self.get_plain_content(status)
        self.logger.debug(f'{account["acct"]} is mentioned me: {content}')

        if PATTERN_REGISTER.search(content):
            self.register(account)
        elif PATTERN_UNREGISTER.search(content):
            self.unregister(account)

    def register(self, account):
        acct = self.full_acct(account)
        domain = self.get_domain(account)

        self.logger.info(f'Registering {acct}')

        session = self.Session()
        server, created = get_or_create(
            session, Server,
            domain=domain
        )
        admin, created = get_or_create(
            session, Admin,
            acct=acct,
        )
        admin.server = server
        session.commit()

    def unregister(self, account):
        acct = self.full_acct(account)

        self.logger.info(f'Unregistering {acct}')

        session = self.Session()
        admin = session.query(Admin).filter_by(acct=acct).first()

        if admin:
            server = admin.server
            session.delete(admin)
            if not server.admins:
                session.delete(server)

            session.commit()

    @staticmethod
    def full_acct(account):
        acct = account.acct
        return acct if '@' in account.acct else f'{acct}@{self.domain}'

    @classmethod
    def get_domain(cls, account):
        return cls.full_acct(account).split('@')[1]

    @staticmethod
    def get_plain_content(status):
        if not status['content']:
            return ''
        doc = html.fromstring(status['content'])
        for link in doc.xpath('//a'):
            link.drop_tree()

        for br in doc.xpath('//br'):
            br.tail = '\n' + (br.tail or '')

        content = doc.text_content()
        return content.strip()

    @property
    def stream_user(self):
        wrapper = functools.partial(self.api.stream_user, self)
        functools.update_wrapper(wrapper, self.api.stream_user)
        return wrapper


def make_mastodon_stream(domain: str, token: str, sessionmaker):
    api = mastodon.Mastodon(
        api_base_url=f'https://{domain}/',
        access_token=token
    )
    return MastodonStreamListener(api, sessionmaker)
