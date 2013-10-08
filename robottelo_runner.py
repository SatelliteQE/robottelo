#!/usr/bin/env python

import argparse
import os
import sys
import unittest

if __name__ == "__main__":

    prog = "Robottelo"
    description = "Runs unittest against a Katello instance."
    usage = "%(prog)s --host <HOST> --project <NAME> --port [<PORT>] --tests [<TEST1>, <TESTn>]"
    epilog = "Constructive comments and feedback can be sent to Og Maciel <omaciel at ogmaciel dot com>."
    version = "%(prog)s 0.1"

    parser = argparse.ArgumentParser(prog=prog, usage=usage, description=description, epilog=epilog, version=version)

    parser.add_argument('-s', '--host', type=str, dest='host', help='Server url')
    parser.add_argument('--project', type=str, dest='project', default='/katello', help='Project can be either "katello" or "headpin"')
    parser.add_argument('--port', type=str, dest='port', default='443', help='Server port, defaults to 443')
    parser.add_argument('--driver', type=str, dest='driver', default='firefox', help='Which WebDriver to use')
    parser.add_argument('-t', '--tests', type=str, action='append', help='The name of the tests to be run.')
    parser.add_argument('--verbose', type=int,  choices=range(1, 6), default=1, help='Debug verbosity level')

    [options, ignored_options] = parser.parse_known_args()

    # Validation
    if options.host is None:
        parser.print_usage()
        sys.exit(-1)
    else:
        os.environ['KATELLO_HOST'] = options.host
        os.environ['PROJECT'] = options.project
        os.environ['KATELLO_PORT'] = options.port
        os.environ['DRIVER_NAME'] = options.driver
        os.environ['VERBOSITY'] = str(options.verbose)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_name in options.tests:
        suite.addTests(loader.loadTestsFromName(test_name))

    runner = unittest.TextTestRunner(verbosity=options.verbose)
    result = runner.run(suite)
