import os

from .manager import MastodonManager

if __name__ == '__main__':
    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    domain = os.getenv('MASTODON_HOST')
    token = os.getenv('MASTODON_ACCESS_TOKEN')
    debug = os.getenv('DEBUG', False)
    if debug in ('False', 'false', '0'):
        debug = False

    mastodon_manager = MastodonManager(db_url, domain, token, debug=debug)
    mastodon_manager.run()
