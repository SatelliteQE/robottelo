#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai


class Base(object):
    """
    Singleton used to pass a WedDriver instance to several test modules
    making up a unique test case.
    """

    instance = None

    def __new__(cls):

        if cls.instance is None:
            i = object.__new__(cls)
            cls.instance = i
            # These should only be assigned by a Login User method.
            cls.base_url = None
            cls.driver = None

        else:

            i = cls.instance

        return i
