#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import os
import unittest


def runIf(project):
    "Decorator to skip tests based on server mode"
    mode = os.getenv('PROJECT').replace('/', '')

    if mode == 'sam':
        mode = 'headpin'

    if project == mode:
        return lambda func: func
    return unittest.skip("%s specific test." % project)

