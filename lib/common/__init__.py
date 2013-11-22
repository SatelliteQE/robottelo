import ConfigParser
import logging.config
import sys

from constants import ROBOTTELO_PROPERTIES


class Configs():

    def __init__(self):
        logging.config.fileConfig("logging.conf")
        self.log_root = logging.getLogger("root")
        prop = ConfigParser.RawConfigParser()
        if prop.read(ROBOTTELO_PROPERTIES):
            self.properties = {}
            for section in prop.sections():
                for option in prop.options(section):
                    self.properties[
                        "%s.%s" % (section, option)
                    ] = prop.get(section, option)
            self.log_root.setLevel(int(self.properties.get("main.verbosity")))
        else:
            print "Please make sure that you have a robottelo.properties file."
            sys.exit(-1)

    def dumpProperties(self):
        keylist = self.properties.keys()
        keylist.sort()
        for key in keylist:
            self.log_root.debug("property %s=%s" % (key, self.properties[key]))

conf = Configs()
conf.log_root.debug("")
conf.log_root.debug("# ** ** ** list properties ** ** **")
conf.log_root.debug(conf.dumpProperties())
conf.log_root.debug("")
