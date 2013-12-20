"""
Module for sharing test utilities for api including base test class.
"""

import unittest
import logging.config


def featuring(match, test):
    """Recursively tests, if structure 'match' could be considered
    a subset of 'test'.

    Dictionary matches test if for every key in match there is a key
    in test and their values match.

    List matches if for every item in match a matching item in test
    can be found.

    Other types match if they are equal.

    Example:
    featuring({"a":{"x":1},"b":[2,3]}, {"a":{"w" : 0,"x":1,"y":2}, "b":[1,2,3]})

    """
    if type(match) != type(test):
        return False
    if type(match) is dict:
        return all(
                [
                    k in test and featuring(
                        v, test[k]
                    )
                    for (k, v) in match.items()
                ]
            )
    if type(match) is list:
        return all([any([featuring(m, t) for t in test]) for m in match])
    return match == test


def assert_featuring(match, test):
    """Version of featuring function that fails with Assertion error instead
    of returning False and passes instead of returning True.

    Example:
    assert_featuring({"a":{"x":1},"b":[2,3]},
                     {"a":{"w" : 0,"x":1,"y":2}, "b":[1,2,3]})

    assert_featuring({"a":{"x":1},"b":[2,3]},
                     {"a":{"w" : 0,"x":1,"y":2}, "b":[1,3]})
    AssertionError: [1, 3] lacks 2
    """
    if type(match) != type(test):
        raise AssertionError(
                "Type of {0} is {1} and {2} is {3}".format(
                    match, type(match), test, type(test)
                    )
                )
    elif type(match) is dict:
        for k in match:
            if not k in test:
                raise AssertionError("{0} lacks key {1}".format(test, k))
        for k in match:
            assert_featuring(match[k], test[k])
    elif type(match) is list:
        for k in match:
            exists = any([featuring(k, t) for t in test])
            if not exists:
                raise AssertionError("{0} lacks {1}".format(test, k))
    else:
        assert match == test


class BaseAPI(unittest.TestCase):
    """Base class that all the api tests inherit from"""

    def setUp(self):
        self.logger = logging.getLogger("robottelo")

    def assertFeaturing(self, match, tests):
        """Method to maintain consistency
        with self.assertSomething style of tests

        """

        assert_featuring(match, tests)

