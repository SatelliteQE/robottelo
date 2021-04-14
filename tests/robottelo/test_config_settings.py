"""Tests for module ``robottelo.config.settings``."""
from unittest import mock

import pytest

from robottelo.config.base import INIReader
from robottelo.config.base import Settings
from robottelo.errors import ImproperlyConfigured

builtin_open = 'builtins.open'


class TestSettings:
    @mock.patch(builtin_open, new_callable=lambda: get_invalid_ini)
    def test_ini_reader(self, mock_open):
        ini_reader = INIReader(None)
        assert ini_reader.get('teste', 'foo') == 'bar'
        assert ini_reader.get('teste', 'bar') == 'foo'
        assert ini_reader.has_section('another')
        assert not ini_reader.has_section('schblaums')

    @mock.patch(builtin_open, new_callable=lambda: get_invalid_ini)
    def test_ini_reader_cast(self, mock_open):
        ini_reader = INIReader(None)
        assert ini_reader.get('awesomeness', 'enabled', cast=bool) is True
        assert ini_reader.get('awesomeness', 'level', cast=int) == 100

    @mock.patch(builtin_open, new_callable=lambda: get_invalid_ini)
    def test_ini_reader_get_default(self, mock_open):
        ini_reader = INIReader(None)
        assert ini_reader.get('a', 'b', default='c') == 'c'

    @mock.patch(builtin_open, new_callable=lambda: get_invalid_ini)
    def test_configure_validation_error(self, mock_open):
        settings = Settings()
        with pytest.raises(ImproperlyConfigured):
            settings.configure()

    @mock.patch(builtin_open, new_callable=lambda: get_valid_ini)
    def test_configure_validation_success(self, mock_open):
        with mock.patch('os.path.isfile', return_value=True):
            settings = Settings()
            settings.configure()
            assert settings.configured
            assert settings.server.hostname == 'example.com'
            assert settings.server.ssh_password == '1234'

    @mock.patch(builtin_open, new_callable=lambda: get_valid_ini)
    def test_configure_with_file_validation_success(self, mock_open):
        with mock.patch('os.path.isfile', return_value=True):
            settings = Settings()
            settings.configure(settings_path='robottelo.properties')
            assert settings.configured
            assert settings.server.hostname == 'example.com'
            assert settings.server.ssh_password == '1234'


class FakeOpen:
    def __init__(self, lines, *args, **kwargs):
        self.lines = (line for line in lines)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def read(self):
        return

    def close(self):
        pass

    def __iter__(self):
        return self.lines

    def readline(self):
        try:
            return self.lines.next()
        except StopIteration:
            return


def get_invalid_ini(path, *args, **kwargs):
    lines = [
        '[teste]',
        'foo=bar',
        'bar=foo',
        '[another]',
        'x=y',
        '[awesomeness]',
        'enabled=true',
        'level=100',
    ]
    return FakeOpen(lines)


def get_valid_ini(path, *args, **kwargs):
    lines = [
        '[server]',
        'hostname=example.com',
        'ssh_password=1234',
        # IniParserDefaults
        '[formatters]',
        'keys=generic',
        '[formatter_generic]',
        'class=logging.Formatter',
        '[handlers]',
        'keys=default',
        '[handler_default]',
        'class=handlers.TimedRotatingFileHandler',
        'args=("",)',
        '[loggers]',
        'keys=root',
        '[logger_root]',
        'level=NOTSET',
        'handlers=default',
    ]
    return FakeOpen(lines)
