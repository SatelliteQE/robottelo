import ConfigParser
import logging
import sys
import os

from constants import ROBOTTELO_PROPERTIES


class Configs():

    def __init__(self):
        prop = ConfigParser.RawConfigParser()
        propFile = "%s/%s" % (self.get_root_path(), ROBOTTELO_PROPERTIES)
        if prop.read(propFile):
            self.properties = {}
            for section in prop.sections():
                for option in prop.options(section):
                    self.properties[
                        "%s.%s" % (section, option)
                    ] = prop.get(section, option)
#             self.log_properties()
        else:
            print "Please make sure that you have a robottelo.properties file."
            sys.exit(-1)

        self._configure_logging()
        self.log_root = logging.getLogger("root")


    def log_properties(self):
        keylist = self.properties.keys()
        keylist.sort()
        self.log_root.debug("")
        self.log_root.debug("# ** ** ** list properties ** ** **")
        for key in keylist:
            self.log_root.debug("property %s=%s" % (key, self.properties[key]))
        self.log_root.debug("")

    def get_root_path(self):
        return os.path.realpath(os.path.join(os.path.dirname(__file__), \
            os.pardir, os.pardir))

    def _configure_logging(self):
        try:
            logging.config.fileConfig("%s/logging.conf" % self.get_root_path())
        except Exception:
            log_format = '%(levelname)s %(module)s:%(lineno)d: %(message)s'
            logging.basicConfig(format=log_format)

        for name in ['root', 'robottelo']:
            logger = logging.getLogger(name)
            logger.setLevel(int(self.properties['nosetests.verbosity']))


conf = Configs()
