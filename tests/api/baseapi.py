# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Base class for all cli tests
"""

import logging
import unittest


def assert_instance_intersects(first, other):
    """Determines if first and other match in type
    """
    r = not isinstance(first, type(other))
    r = r or not isinstance(other, type(first))

    if r:
        return (
            "!Types",
            type(first),
            type(other))
    return True


def assert_list_intersects(first, other):
    """Compares two lists, and determines,
    if each item in first intersects
    with at least one item in other
    """
    grievance = []
    for v in first:
        if not any(intersection(v, i) is True for i in other):
            grievance.append(v)
    if grievance == []:
        return True
    return ("!in", grievance, other)


def assert_dict_intersects(first, other):
    """Compares two dictionaries, and determines,
    if shared keys contain intersecting values
    """
    grievance = {}
    for k in first:
        if k in other:
            self_v = first[k]
            other_v = other[k]
            res = intersection(self_v, other_v)
            if res is not True:
                grievance[k] = res
    if grievance == {}:
        return True
    return ("!in", grievance)


def intersection(first, other):
    """Compares two objects to determine, if they share common information.
       Returns either true, or touple describing the difference
    >>> intersection("n1","n2")
    ('!=', 'n1', 'n2')
    >>> intersection([1,2,3,5],[2,1,0,2,3,4])
    ('!in', [5], [2, 1, 0, 2, 3, 4])
    >>> intersection({"s1":0,"s2":0,"e1":2},{"s1":0,"s2":2,"e2":3})
    ('!in', {'s2': ('!=', 0, 2)})
    >>> intersection(
    ...     {"name":"n1","org":{"name":"o1"}},
    ...     {"name":"n1","org":{"name":"o2"}})
    ...
    ('!in', {'org': ('!in', {'name': ('!=', 'o1', 'o2')})})
    """
    if first is other:
        return True
    elif first == other:
        return True
    elif isinstance(first, type([])):
        return assert_list_intersects(first, other)
    elif hasattr(first, "__dict__") and hasattr(other, "__dict__"):
        self_data = first.__dict__
        other_data = other.__dict__
        return intersection(self_data, other_data)
    elif isinstance(first, type({})):
        return assert_dict_intersects(first, other)
    return ("!=", first, other)


def assert_intersects(first, other, msg=None):
    """Intersection based assert.
    """
    res = intersection(first, other)
    if res is not True:
        raise AssertionError(
            msg or "%r not intersects %r in %r" % (first, other, res)
            )


def is_intersecting(first, other):
    """Compares two objects to determine, if they share common information.
    Returns true or false.
    >>> is_intersecting("n1","n1")
    True
    >>> is_intersecting("n1","n2")
    False
    >>> is_intersecting([1,2,3],[2,1,0,2,3,4])
    True
    >>> is_intersecting([1,2,3,5],[2,1,0,2,3,4])
    False
    >>> is_intersecting({"s1":0,"s2":0,"e1":2},{"s1":0,"s2":0,"e2":3},)
    True
    >>> is_intersecting({"s1":0,"s2":0,"e1":2},{"s1":0,"s2":2,"e2":3},)
    False
    >>> class Test:
    ...     pass
    ...
    >>> t1 = Test()
    >>> t2 = Test()
    >>> t1.a = 1
    >>> t1.b = 1
    >>> t2.a = 1
    >>> t2.c = 2
    >>> is_intersecting(t1,t2)
    True
    """
    if intersection(first, other) is True:
        return True
    return False


class BaseAPI(unittest.TestCase):
    """
    Base class for all cli tests
    """
    def assertIntersects(self, first, other, msg=None):
        assert_intersects(first, other, msg)

    def setUp(self):
        self.logger = logging.getLogger("robottelo")
