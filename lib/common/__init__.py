import ConfigParser
import logging.config
from constants import *


class Configs():

    def __init__(self):
        logging.config.fileConfig("logging.conf")
        self.log_root = logging.getLogger("root")
        prop = ConfigParser.RawConfigParser()
        prop.read(ROBOTTELO_PROPERTIES)
        self.properties = {}
        for section in prop.sections():
            for option in prop.options(section):
                self.properties["%s.%s" % (section, option)] = \
                prop.get(section, option)

    def dumpProperties(self):
        keylist = self.properties.keys()
        keylist.sort()
        for key in keylist:
            self.log_root.info("property %s=%s" % (key, self.properties[key]))

conf = Configs()
conf.log_root.info("")
conf.log_root.info("# ** ** ** list properties ** ** **")
conf.dumpProperties()
conf.log_root.info("")
