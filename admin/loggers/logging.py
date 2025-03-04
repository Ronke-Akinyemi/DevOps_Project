import logging
from logging.config import dictConfig
from colorlog import ColoredFormatter

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "()": ColoredFormatter,
            "format": "%(log_color)s %(levelname)-8s %(asctime)s %(process)s --- "
            "%(lineno)-8s [%(name)s] %(funcName)-24s : %(message)s",
            "log_colors": {
                "DEBUG": "blue",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
        "aws": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            "formatter": "verbose",
            'filename': 'project.log',
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["file", ],
            "propagate": False,
        },
        'sqlalchemy': {
            'level': 'ERROR',  # Set SQLAlchemy logs to ERROR level
            'handlers': ['console'],
            'propagate': False,  # Don't propagate to root logger
        },
        'sqlalchemy.engine': {
            'level': 'ERROR',  # Set the engine logger level to ERROR
            'handlers': ['console'],
            'propagate': False,  # Don't propagate to root logger
        },
    },
}

dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)