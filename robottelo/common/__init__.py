"""Define and instantiate the configuration class for Robottelo."""

import ConfigParser
import logging
import logging.config  # required for the logging configuration
import os

from collections import defaultdict
from ConfigParser import NoSectionError
from robottelo.common.constants import ROBOTTELO_PROPERTIES


class Configs(object):
    """Read Robottelo's config file and set up logging."""
    def __init__(self):
        """Read Robottelo's config file and initialize the logger."""
        conf_parser = ConfigParser.RawConfigParser()
        conf_file = _config_file()
        self.properties = defaultdict(lambda: None)

        self._configure_logging()
        self.logger = logging.getLogger('robottelo')

        if conf_parser.read(conf_file):
            # populate self.properties from the config file
            for section in conf_parser.sections():
                for option in conf_parser.options(section):
                    self.properties[
                        "{0}.{1}".format(section, option)
                    ] = conf_parser.get(section, option)
        else:
            self.logger.error(
                'No config file found at "{0}".'.format(_config_file())
            )

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
                "property {0}={1}".format(key, self.properties[key])
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
                "{0}/logging.conf".format(get_app_root())
            )
        except NoSectionError:
            log_format = '%(levelname)s %(module)s:%(lineno)d: %(message)s'
            logging.basicConfig(format=log_format)

        if self.properties:
            verbosity = self.properties.get('nosetests.verbosity', '1')
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
