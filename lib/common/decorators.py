#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import os
import unittest
import bugzilla
import logging

bugzilla_log = logging.getLogger("bugzilla")
bugzilla_log.setLevel(logging.WARNING)

BUGZILLA_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"

def runIf(project):
    "Decorator to skip tests based on server mode"
    mode = os.getenv('PROJECT').replace('/', '')

    if project == mode:
        return lambda func: func
    return unittest.skip("%s specific test." % project)

def bzbug(bz_id):
    mybz = bugzilla.RHBugzilla()
    mybz.connect(BUGZILLA_URL)
    mybug = mybz.getbugsimple(bz_id)
    if (mybug.status == 'NEW') or (mybug.status == 'ASSIGNED'):
        logging.debug(mybug)
        return unittest.skip(mybug)
    else:
        return lambda func: func
