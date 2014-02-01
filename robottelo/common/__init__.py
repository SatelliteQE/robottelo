"""
Configuration class for the Framework
"""

import ConfigParser
import logging
import os
import sys

from robottelo.common.constants import ROBOTTELO_PROPERTIES


class Configs(object):
    """
    Reads configuration attributes and sets up logging
    """

    def __init__(self):
        """
        Reads and initializes configuration attributes
        """

        prop = ConfigParser.RawConfigParser()
        prop_file = os.path.join(self.get_root_path(), ROBOTTELO_PROPERTIES)
        self._properties = None

        if prop.read(prop_file):
            self._properties = {}
            for section in prop.sections():
                for option in prop.options(section):
                    self._properties[
                        "%s.%s" % (section, option)
                    ] = prop.get(section, option)

        self._configure_logging()
        self.logger = logging.getLogger('robottelo')

    @property
    def properties(self):
        if self._properties is None:
            self.logger.error(
                'Please make sure that you have a robottelo.properties file.')
            sys.exit(-1)
        return self._properties

    def log_properties(self):
        """
        Displays available configuration attributes
        """

        keylist = self.properties.keys()
        keylist.sort()
        self.logger.debug("")
        self.logger.debug("# ** ** ** list properties ** ** **")
        for key in keylist:
            self.logger.debug("property %s=%s" % (key, self.properties[key]))
        self.logger.debug("")

    def get_root_path(self):
        """
        Returns correct path to logging config file
        """

        return os.path.realpath(os.path.join(os.path.dirname(__file__),
                                             os.pardir, os.pardir))

    def _configure_logging(self):
        """
        Configures logging for the entire framework
        """

        try:
            logging.config.fileConfig("%s/logging.conf" % self.get_root_path())
        except Exception:
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


conf = Configs()
