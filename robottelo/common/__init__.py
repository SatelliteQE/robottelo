"""Define and instantiate the configuration class for Robottelo."""

import ConfigParser
import logging
import logging.config  # required for the logging configuration
import os
import sys

from ConfigParser import NoSectionError
from robottelo.common.constants import ROBOTTELO_PROPERTIES


class Configs(object):
    """Read Robottelo's config file and set up logging."""
    def __init__(self):
        """Read Robottelo's config file and initialize the logger."""
        conf_parser = ConfigParser.RawConfigParser()
        conf_file = _config_file()
        self._properties = None

        if conf_parser.read(conf_file):
            # populate self._properties from the config file
            self._properties = {}
            for section in conf_parser.sections():
                for option in conf_parser.options(section):
                    self._properties[
                        "{}.{}".format(section, option)
                    ] = conf_parser.get(section, option)

        self._configure_logging()
        self.logger = logging.getLogger('robottelo')

    @property
    def properties(self):
        """Return settings read from the config file.

        If Robottelo's config file could not be read when this object was
        instantiated, return ``None``. This will happen if the config file does
        not exist.

        :return: Application settings, if available.
        :rtype: dict
        :rtype: None

        """
        if self._properties is None:
            self.logger.error(
                'No config file found at "{}".'.format(_config_file())
            )
            sys.exit(-1)
        return self._properties

    def log_properties(self):
        """Print config options to the logging file.

        :rtype: None

        """
        keylist = self.properties.keys()
        keylist.sort()
        self.logger.debug("")
        self.logger.debug("# ** ** ** list properties ** ** **")
        for key in keylist:
            self.logger.debug(
                "property {}={}".format(key, self.properties[key])
            )
        self.logger.debug("")

    def _configure_logging(self):
        """Configure logging for the entire framework.

        If a config named ``logging.conf`` exists in Robottelo's root
        directory, the logger is configured using the options in that file.
        Otherwise, a custom logging output format is set, and default values
        are used for all other logging options.

        :rtype: None

        """
        try:
            logging.config.fileConfig(
                "{}/logging.conf".format(get_app_root())
            )
        except NoSectionError:
            log_format = '%(levelname)s %(module)s:%(lineno)d: %(message)s'
            logging.basicConfig(format=log_format)

        if self._properties:
            verbosity = self._properties.get('nosetests.verbosity', '1')
            log_level = int(verbosity) * 10
        else:
            log_level = logging.DEBUG

        for name in ['root', 'robottelo']:
            logger = logging.getLogger(name)
            logger.setLevel(log_level)


def get_app_root():
    """Return the path to the application root directory.

    :return: A directory path.
    :rtype: str

    """
    return os.path.realpath(os.path.join(
        os.path.dirname(__file__),
        os.pardir,
        os.pardir,
    ))


def _config_file():
    """Return the path to the application-wide config file.

    :return: A file path.
    :rtype: str

    """
    return os.path.join(get_app_root(), ROBOTTELO_PROPERTIES)


conf = Configs()
