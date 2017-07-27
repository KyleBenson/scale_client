# This file contains various default values that are used throughout the scale client system

# HACK: to default to the last used level (e.g. when re-setting defaults)
last_log_level = None

def set_logging_config(level=None,
                       log_format="%(levelname)-6s : %(name)-55s : %(message)s",
                       loggers=('',)):
    """
    Sets the loggers to the specified format.  Use no args for defaults, which will
    set ALL loggers (the root) to a default format with level WARNING. This is
    useful if a 3rd-party library does logging incorrectly and overwrites our
    configuration: you can just run this function again to correct it.
    :param level: logging level (if unspecified defaults to the last requested level else logging.INFO)
    :param log_format: the format to use (our default pads the names to make it more legible)
    :param loggers: which logger names to set (default sets root a.k.a. all of them)
    :return:
    """
    import logging.config

    # HACK: default to the last used level if possible, else set a default
    global last_log_level
    if level is None:
        if last_log_level is None:
            level = logging.WARNING
        else:
            level = last_log_level
    last_log_level = level

    # Taken from: http://stackoverflow.com/questions/7507825/python-complete-example-of-dict-for-logging-config-dictconfig
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format
            },
        },
        'handlers': {
            'default': {
                # 'level': level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            key: {
                'handlers': ['default'],
                'level': level,
                # 'propagate': True
            } for key in loggers
        }
    }
    logging.config.dictConfig(logging_config)


### Networking-related configuration defaults

DEFAULT_COAP_PORT = 5683
