import ConfigParser
import logging.config
import sys
import os
from constants import ROBOTTELO_PROPERTIES


class Configs():

    def __init__(self):
        logging.config.fileConfig("%s/logging.conf" % self.get_root_path())
        self.log_root = logging.getLogger("root")
        prop = ConfigParser.RawConfigParser()
        propFile = "%s/%s" % (self.get_root_path(), ROBOTTELO_PROPERTIES)
        if prop.read(propFile):
            self.properties = {}
            for section in prop.sections():
                for option in prop.options(section):
                    self.properties[
                        "%s.%s" % (section, option)
                    ] = prop.get(section, option)
            self.log_root.setLevel(
                int(self.properties.get("nosetests.verbosity")))

#             self.log_properties()
        else:
            print "Please make sure that you have a robottelo.properties file."
            sys.exit(-1)

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

conf = Configs()
