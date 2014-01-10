"""
Configuration class for the Framework
"""

import ConfigParser
import logging
import logging.config
import sys
import os

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
        prop_file = "%s/%s" % (self.get_root_path(), ROBOTTELO_PROPERTIES)

        if prop.read(prop_file):
            self.properties = {}
            for section in prop.sections():
                for option in prop.options(section):
                    self.properties[
                        "%s.%s" % (section, option)
                    ] = prop.get(section, option)
        else:
            print "Please make sure that you have a robottelo.properties file."
            sys.exit(-1)

        self._configure_logging()
        self.log_root = logging.getLogger("root")

    def log_properties(self):
        """
        Displays available configuration attributes
        """

        keylist = self.properties.keys()
        keylist.sort()
        self.log_root.debug("")
        self.log_root.debug("# ** ** ** list properties ** ** **")
        for key in keylist:
            self.log_root.debug("property %s=%s" % (key, self.properties[key]))
        self.log_root.debug("")

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

        for name in ['root', 'robottelo']:
            logger = logging.getLogger(name)
            logger.setLevel(int(self.properties['nosetests.verbosity']) * 10)


conf = Configs()
