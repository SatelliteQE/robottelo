#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import argparse
import glob
import os
import subprocess

from lib.common import conf

# Borrowed from https://github.com/pulp/pulp/blob/master/run-tests.py
# Find and eradicate any existing .pyc files, so they do not eradicate us!
PROJECT_DIR = conf.get_root_path()

subprocess.call(['find', PROJECT_DIR, '-name', '*.pyc', '-delete'])

parser = argparse.ArgumentParser()

parser.add_argument(
    '-t',
    '--tests',
    dest='tests',
    choices=['cli', 'ui', '*'],
    default='cli',
    help='The type of the tests to be run. Options are CLI, UI, Both')

[options, ignored_options] = parser.parse_known_args()

# Validation
if options.tests is None:
    parser.print_usage()
    sys.exit(-1)

TESTS = [".".join(
    x.split('/')[-2:]
) for x in glob.glob(
    "%s/tests/%s/test_*.py" % (PROJECT_DIR, options.tests))
]

params = [
    'nosetests',
    '--config=%s' % conf.get_root_path() + "/robottelo.properties",
    "--tests",
    ",".join("tests.%s" % test_name[:-3] for test_name in TESTS),
]

os.environ['PYTHONPATH'] = PROJECT_DIR

# for run through: run-tests.py
# This runner caused to not make a single call point in lib/common/__init__.py
# I am not sure why but call of subprocess.call made __init__.py to be
# loaded second time. FIXME please if you aware of / know the solution. thx.
conf.log_properties()
subprocess.call(params)
