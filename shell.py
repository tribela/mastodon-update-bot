import os

from bot.engine import get_session
from bot.models import *  # noqa
from bot.manager import MastodonManager

Session = get_session(os.getenv('DATABASE_URL'))

session = Session()

db_url = os.getenv('DATABASE_URL')
domain = os.getenv('MASTODON_HOST')
token = os.getenv('MASTODON_ACCESS_TOKEN')

mastodon_manager = MastodonManager(db_url, domain, token)
