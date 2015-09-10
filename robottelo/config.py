"""Define and instantiate the configuration class for Robottelo."""

import ConfigParser
import logging
from ConfigParser import NoSectionError
from logging import config

import os

from robottelo.constants import ROBOTTELO_PROPERTIES


class Configs(object):
    """Read Robottelo's config file and set up logging."""
    def __init__(self):
        """Read Robottelo's config file and initialize the logger."""
        # Set instance vars.
        self.properties = {}
        self.logger = logging.getLogger('robottelo')

        # Read the config file, if available.
        conf_parser = ConfigParser.RawConfigParser()
        if conf_parser.read(_config_file()):
            for section in conf_parser.sections():
                for option in conf_parser.options(section):
                    self.properties[
                        "{0}.{1}".format(section, option)
                    ] = conf_parser.get(section, option)
        else:
            self.logger.error(
                'No config file found at "{0}".'.format(_config_file())
            )

        # Configure logging using a value from the config file, if available.
        try:
            _configure_logging(int(self.properties['main.verbosity']))
        except KeyError:
            _configure_logging()

        _configure_third_party_logging()

    def log_properties(self):
        """Print config options to the logging file.

        :returns: Nothing is returned.

        """
        keylist = self.properties.keys()
        keylist.sort()
        self.logger.debug("")
        self.logger.debug("# ** ** ** list properties ** ** **")
        for key in keylist:
            self.logger.debug(
                "property {0}={1}".format(key, self.properties[key])
            )
        self.logger.debug("")


def get_app_root():
    """Return the path to the application root directory.

    :return: A directory path.
    :rtype: str

    """
    return os.path.realpath(os.path.join(
        os.path.dirname(__file__),
        os.pardir,
    ))


def _config_file():
    """Return the path to the application-wide config file.

    :return: A file path.
    :rtype: str

    """
    return os.path.join(get_app_root(), ROBOTTELO_PROPERTIES)


def _configure_logging(verbosity=2):
    """Configure logging for the entire framework.

    If a config named ``logging.conf`` exists in Robottelo's root directory,
    the logger is configured using the options in that file.  Otherwise, a
    custom logging output format is set, and default values are used for all
    other logging options.

    :param int verbosity: Useful values are in the range 1-5 inclusive, and
        higher numbers produce more verbose logging.
    :returns: Nothing is returned.

    """
    try:
        config.fileConfig(os.path.join(get_app_root(), 'logging.conf'))
    except NoSectionError:
        logging.basicConfig(
            format='%(levelname)s %(module)s:%(lineno)d: %(message)s'
        )

    # Translate from robottelo verbosity values to logging verbosity values.
    # This code is inspired by method `Config.configureLogging` in module
    # `nose.config` in the nose source code.
    if verbosity >= 5:
        log_level = logging.DEBUG
    elif verbosity == 4:
        log_level = logging.INFO
    elif verbosity == 3:
        log_level = logging.WARNING
    elif verbosity == 2:
        log_level = logging.ERROR
    else:
        log_level = logging.CRITICAL

    for name in ('nailgun', 'robottelo'):
        logging.getLogger(name).setLevel(log_level)

    # All output should be made by the logging module, including warnings
    logging.captureWarnings(True)


def _configure_third_party_logging():
    """Increase the level of third party packages logging

    :returns: Nothing is returned.

    """
    loggers = (
        'bugzilla',
        'easyprocess',
        'paramiko',
        'pyvirtualdisplay',
        'requests.packages.urllib3.connectionpool',
        'selenium.webdriver.remote.remote_connection',
    )

    for logger in loggers:
        logging.getLogger(logger).setLevel(logging.WARNING)


#: A :class:`Configs` object.
conf = Configs()
