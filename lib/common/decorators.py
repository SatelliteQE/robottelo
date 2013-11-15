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
    try:
        mybz = bugzilla.RHBugzilla()
        mybz.connect(BUGZILLA_URL)
        mybug = mybz.getbugsimple(bz_id)
    except (TypeError, ValueError):
        logging.warning("Invalid Bugzilla ID {0}".format(bz_id))
        return lambda func: func
    else:
        if (mybug.status == 'NEW') or (mybug.status == 'ASSIGNED'):
            logging.debug(mybug)
            return unittest.skip("Test skipped due to %s" % mybug)
        else:
            return lambda func: func
