#!/usr/bin/env python

import argparse
import sys
import unittest
from lib.common import conf

PROJECT_DIR = conf.get_root_path()
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

if __name__ == "__main__":

    conf.log_properties()  # for standalone launch of: robottelo_runner.py

    prog = "Robottelo"
    description = "Runs unittest against a Katello instance."
    epilog = "Constructive comments and feedback are welcome."
    version = "%(prog)s 0.1"

    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        epilog=epilog, version=version)

    parser.add_argument(
        '-t',
        '--tests',
        type=str,
        dest='tests',
        action='append',
        help='The name of the tests to be run.')

    [options, ignored_options] = parser.parse_known_args()

    # Validation
    if options.tests is None:
        parser.print_usage()
        sys.exit(-1)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_name in options.tests:
        suite.addTests(loader.loadTestsFromName(test_name))

    runner = unittest.TextTestRunner(
                verbosity=int(conf.properties.get("nosetests.verbosity")))
    result = runner.run(suite)
