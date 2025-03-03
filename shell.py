import os

from mastodon_update_bot.engine import get_session
from mastodon_update_bot.models import *  # noqa
from mastodon_update_bot.manager import MastodonManager

Session = get_session(os.getenv('DATABASE_URL'))

session = Session()

db_url = os.getenv('DATABASE_URL')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
domain = os.getenv('MASTODON_HOST')
token = os.getenv('MASTODON_ACCESS_TOKEN')

mastodon_manager = MastodonManager(db_url, domain, token)
