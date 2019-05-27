import os

from logging.config import dictConfig

LOGLEVEL = os.getenv('LOGLEVEL', 'INFO')


def config_logger():
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            },
        },
        'handlers': {
            'default': {
                'level': LOGLEVEL,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'WARNING',
                'propagate': True,
            },
            'bot': {
                'handlers': ['default'],
                'level': LOGLEVEL,
                'propagate': False,
            },
        },
    })
