import os

from .manager import MastodonManager

if __name__ == '__main__':
    db_url = os.getenv('DATABASE_URL')
    domain = os.getenv('MASTODON_HOST')
    token = os.getenv('MASTODON_ACCESS_TOKEN')

    mastodon_manager = MastodonManager(db_url, domain, token)
    mastodon_manager.run()

