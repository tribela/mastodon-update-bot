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
                'datefmt': '%Y-%m-%d %H:%M:%S %z'
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
                'propagate': False,
            },
            'bot': {
                'handlers': ['default'],
                'level': LOGLEVEL,
                'propagate': False,
            },
        },
    })
