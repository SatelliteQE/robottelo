"""Configuration casts to help typing the settings."""
import logging

from shlex import shlex


class Boolean(object):
    """Cast a string to boolean.

    String values 1, yes, true, on will result in python's ``True``.
    String values 0, no, false, off will result in python's ``False``.

    :param str value: A string to cast to boolean.

    """
    _booleans = {
        '1': True, 'yes': True, 'true': True, 'on': True,
        '0': False, 'no': False, 'false': False, 'off': False,
    }

    def __call__(self, value):
        value = value.lower()
        if value not in self._booleans:
            raise ValueError('Not a boolean: {}'.format(value))
        return self._booleans[value]


class List(object):
    """Cast a comma separated string to a list.

    :param str value: A comma separated string to cast to a list.

    """
    def __call__(self, value):
        lexer = shlex(value, posix=True)
        lexer.whitespace = ','
        lexer.whitespace_split = True
        return [item.strip() for item in lexer]


class LoggingLevel(object):
    """Cast a string to a logging level.

    :param str value: A string to cast to a logging level.

    """
    _logging_levels = {
        'critical': logging.CRITICAL,
        'debug': logging.DEBUG,
        'error': logging.ERROR,
        'info': logging.INFO,
        'warning': logging.WARNING,
    }

    def __call__(self, value):
        value = value.lower()
        if value not in self._logging_levels:
            raise ValueError('{} should one of {}.'.format(
                value,
                ', '.join(self._logging_levels.keys()),
            ))
        return self._logging_levels[value]


class Tuple(List):
    """Cast a comma separated string to a tuple.

    :param str value: A comma separated string to cast to a tuple.

    """
    def __call__(self, value):
        return tuple(super(Tuple, self).__call__(value))
