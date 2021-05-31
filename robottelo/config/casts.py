"""Configuration casts to help typing the settings."""
from shlex import shlex


class Boolean:
    """Cast a string to boolean.

    String values 1, yes, true, on will result in python's ``True``.
    String values 0, no, false, off will result in python's ``False``.

    :param str value: A string to cast to boolean.

    """

    _booleans = {
        '1': True,
        'yes': True,
        'true': True,
        'on': True,
        '0': False,
        'no': False,
        'false': False,
        'off': False,
    }

    def __call__(self, value):
        value = value.lower()
        if value not in self._booleans:
            raise ValueError(f'Not a boolean: {value}')
        return self._booleans[value]


class List:
    """Cast a comma separated string to a list.

    :param str value: A comma separated string to cast to a list.

    """

    def __call__(self, value):
        lexer = shlex(value, posix=True)
        lexer.whitespace = ','
        lexer.whitespace_split = True
        return [item.strip() for item in lexer]


class LoggingLevel:
    """Cast a string to a logging level.

    :param str value: A string to cast to a logging level.

    """

    import logging

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
            raise ValueError(
                '{} should one of {}.'.format(value, ', '.join(self._logging_levels.keys()))
            )
        return self._logging_levels[value]


class Tuple(List):
    """Cast a comma separated string to a tuple.

    :param str value: A comma separated string to cast to a tuple.

    """

    def __call__(self, value):
        return tuple(super().__call__(value))


class Dict(List):
    """Cast a comma separated list of key=value to a dict.

    :param str value: A comma separated string to cast to a dict.
    """

    def __call__(self, value):
        return dict(v.split('=') for v in super(Dict, self).__call__(value))


class WebdriverDesiredCapabilities(Dict):
    """Cast a comma separated list of key=value to a
    webdriver.DesiredCapabilities dict.

    Convert values ``true`` and ``false`` (ignore case) to a proper boolean.

    :param str value: A comma separated string to cast to a
        webdriver.DesiredCapabilities dict.
    """

    def __call__(self, value):
        desired_capabilities = super().__call__(value)
        for k, v in desired_capabilities.items():
            v = v.lower()
            if v in ('true', 'false'):
                desired_capabilities[k] = v == 'true'
        return desired_capabilities
