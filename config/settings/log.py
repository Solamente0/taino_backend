LOGGING = {
    "formatters": {
        "verbose": {
            "format": "\n\n{levelname} {asctime} {pathname} {module} {process:d} {thread:d} {filename} {funcName} {lineno} {message}\n\n",
            "style": "{",
        },
        "simple": {
            "format": "##### {asctime} - {message} #####",
            "style": "{",
        },
    },
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "verbose_console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "simple_console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["simple_console"],
            "level": "INFO",
        },
        "django.request": {
            "handlers": ["verbose_console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
# LOGGING["loggers"]["base_utils.middlewares"] = {
#     "handlers": ["verbose_console"],
#     "level": "DEBUG",
#     "propagate": False,
# }

LOGGING["loggers"]["websockets"] = {
    "handlers": ["verbose_console"],
    "level": "DEBUG",
    "propagate": False,
}

LOGGING["loggers"]["apps.chat.consumers"] = {
    "handlers": ["verbose_console"],
    "level": "DEBUG",
    "propagate": False,
}
#
# LOGGING["loggers"]["base_utils.middlewares"] = {
#     "handlers": ["verbose_console"],
#     "level": "DEBUG",
#     "propagate": False,
# }
