import functools
import logging
import re

import mastodon

from lxml import html

from .models import Admin, Server, get_or_create, UpdateType

PATTERN_REGISTER = re.compile(r'\bregister\b')
PATTERN_UNREGISTER = re.compile(r'\bunregister\b')
PATTERN_TYPE = re.compile(r'type: (\w+)')


class MastodonStreamListener(mastodon.StreamListener):

    def __init__(self, api: mastodon.Mastodon, sessionmaker, debug=False):
        super().__init__()
        self.api = api
        self.Session = sessionmaker
        self.logger = logging.getLogger(__name__)
        self.domain = api.instance().uri

        self.debug = debug

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
            self.register(account, status['id'])
        elif PATTERN_UNREGISTER.search(content):
            self.unregister(account, status['id'])
        elif found := PATTERN_TYPE.search(content):
            update_type = found.group(1)
            self.change_update_type(account, status['id'], update_type)

    def register(self, account, reply_id):
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
        session.close()

        self.post(f'@{acct} 구독 되었습니다', visibility='direct', in_reply_to_id=reply_id)

    def unregister(self, account, reply_id):
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

        session.close()

        self.post(f'@{acct} 구독 해지 되었습니다', visibility='direct', in_reply_to_id=reply_id)

    def change_update_type(self, account, reply_id, update_type):
        acct = self.full_acct(account)

        valid_values = set(item.value for item in UpdateType)

        if update_type not in valid_values:
            self.post(
                f'@{acct} Invalid type. valid types are {", ".join(valid_values)}',
                visibility='direct', in_reply_to_id=reply_id)

        self.logger.info(f'Changing update type of {acct} to {update_type}')

        session = self.Session()
        admin = session.query(Admin).filter_by(acct=acct).first()

        if not admin:
            self.post(
                '@{acct} You are not registered. Please send me "register" to register you.',
                visibility='direct', in_reply_to_id=reply_id)
        else:
            admin.update_type = UpdateType(update_type)
            session.commit()
            self.post(
                f'@{acct} Changed update type to {update_type}',
                visibility='direct', in_reply_to_id=reply_id)

        session.close()

    def full_acct(self, account):
        acct = account.acct
        return acct if '@' in account.acct else f'{acct}@{self.domain}'

    def get_domain(self, account):
        return self.full_acct(account).split('@')[1]

    @functools.wraps(mastodon.Mastodon.status_post)
    def post(self, status, *args, **kwargs):
        if self.debug:
            self.logger.info(status)
        else:
            try:
                self.api.status_post(status, *args, **kwargs)
            except mastodon.MastodonError as e:
                self.logger.error(e)

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
