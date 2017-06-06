# coding: utf-8
import logging

try:
    # coloredlogs is optional, used only when installed
    import coloredlogs
except ImportError:
    coloredlogs = None


DICT_RESERVED_KEYS = vars(dict).keys()


class SmartDict(dict):
    """
    A Dict which is accessible via attribute dot notation
    """
    def __init__(self, *args, **kwargs):
        """
        :param args: multiple dicts ({}, {}, ..)
        :param kwargs: arbitrary keys='value'

        If ``keyerror=False`` is passed then not found attributes will
        always return None.
        """
        super(SmartDict, self).__init__()
        self['__keyerror'] = kwargs.pop('keyerror', True)
        [self.update(arg) for arg in args if isinstance(arg, dict)]
        self.update(kwargs)

    def __getattr__(self, attr):
        if attr not in DICT_RESERVED_KEYS:
            if self['__keyerror']:
                return self[attr]
            else:
                return self.get(attr)
        return getattr(self, attr)

    def __setattr__(self, key, value):
        if key in DICT_RESERVED_KEYS:
            raise TypeError("You cannot set a reserved name as attribute")
        self.__setitem__(key, value)

    def __copy__(self):
        return self.__class__(self)

    def copy(self):
        return self.__copy__()


def set_logger(verbose):
    """Set logger verbosity used when client is called with -vvvvv"""

    for _logger in logging.Logger.manager.loggerDict.values():  # noqa
        if not isinstance(_logger, logging.Logger):
            continue
        if coloredlogs is not None:
            _logger.propagate = False

            handler = logging.StreamHandler()
            formatter = coloredlogs.ColoredFormatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            _logger.handlers = [handler]
        _logger.setLevel(verbose * 10)
