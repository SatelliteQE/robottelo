import unittest
import logging.config

from lib.common import conf

def featuring(match, test):
    """Recursively tests, if structure 'match' could be considered
    a subset of 'test'.

    Dictionary matches test if for every key in match there is a key
    in test and their values match.

    List matches if for every item in match a matching item in test
    can be found.

    Other types match if they are equal.

    """
    if type(match) != type(test):
        return False
    if type(match) is dict:
        return all([k in test and featuring(v, test[k])
                        for (k,v) in match.items()])
    if type(match) is list:
        return all([any([featuring(m, t) for t in test]) for m in match])
    return match == test

def assertFeaturing(match, test):
    """Version of featuring function that fails with Assertion error instead
    of returning False and passes instead of returning True.

    """
    if type(match) != type(test):
        raise AssertionError("Type of {0} is {1} and {2} is {3}"
                .format(match,type(match),test,type(test)))
    elif type(match) is dict:
        for k in match:
            if not k in test:
                raise AssertionError("{0} lacks key {1}".format(test, k))
        for k in match:
            assertFeaturing(match[k], test[k])
    elif type(match) is list:
        for m in match:
            exists = any([featuring(m, t) for t in test])
            if not exists:
                raise AssertionError("{0} lacks {1}".format(test, m))
    else:
        assert match == test

class BaseAPI(unittest.TestCase):
    """Base class that all the api tests inherit from"""

    def setUp(self):
        logging.config.fileConfig("%s/logging.conf" % conf.get_root_path())

        self.verbosity = int(conf.properties['nosetests.verbosity'])
        self.logger = logging.getLogger("robottelo")
        self.logger.setLevel(self.verbosity * 10)

