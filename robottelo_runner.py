#!/usr/bin/env python

import argparse
import os
import sys
import unittest

PROJECT_DIR = os.path.abspath(os.path.curdir)
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

if __name__ == "__main__":

    prog = "Robottelo"
    description = "Runs unittest against a Katello instance."
    epilog = "Constructive comments and feedback are welcome."
    version = "%(prog)s 0.1"

    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        epilog=epilog, version=version)

    parser.add_argument('-s',
                        '--host',
                        type=str,
                        dest='host',
                        help='Server url')
    parser.add_argument(
        '--project',
        type=str,
        dest='project',
        default='/katello',
        help='Project can be either "katello" or "headpin"')
    parser.add_argument(
        '--port',
        type=str,
        dest='port',
        default='443',
        help='Server port, defaults to 443')
    parser.add_argument(
        '--driver',
        type=str,
        dest='driver',
        default='firefox',
        help='Which WebDriver to use')
    parser.add_argument(
        '--locale',
        type=str,
        dest='locale',
        default='en_US',
        help='Run tests using specified locale')

    parser.add_argument(
        '--katello-user',
        type=str,
        dest='katello_user',
        default='admin')
    parser.add_argument(
        '--katello_passwd',
        type=str,
        dest='katello_passwd',
        default='changeme')

    parser.add_argument(
        '-t',
        '--tests',
        type=str,
        action='append',
        help='The name of the tests to be run.')

    parser.add_argument(
        '--verbosity',
        type=int,
        choices=range(1, 6),
        default=1,
        help='Debug verbosity level')

    parser.add_argument(
        '--sauce-user',
        type=str,
        dest='sauce_user',
        help='User name for Sauce Labs')
    parser.add_argument(
        '--sauce-key',
        type=str,
        dest='sauce_key',
        default='',
        help='API key for Sauce Labs')
    parser.add_argument(
        '--sauce-os',
        type=str,
        dest='sauce_os',
        default='LINUX',
        help='OS to use when running tests on Sauce Labs.\
        Options are: LINUX, WIN8, VISTA, MAC')
    parser.add_argument(
        '--sauce-version',
        type=str,
        dest='sauce_version',
        default='21',
        help='Browser version to use on Sauce Labs. \
        See available versions here: https://saucelabs.com/docs/platforms')
    parser.add_argument(
        '--sauce-tunnel',
        type=str,
        dest='sauce_tunnel',
        help='Name of shared Sauce Connect tunnel. \
        Only necessary when connecting to a shared tunnel.')

    parser.add_argument(
        '--sshkey',
        type=str,
        dest='sshkey',
        default=os.path.expanduser('~/.ssh/id_rsa'),
        help='Path to ssh key to connect to server.')
    parser.add_argument(
        '--root',
        type=str,
        dest='root',
        default='root',
        help='User name to connect to server via ssh. Most of the time \
        the default "root" will work.')

    import epdb; epdb.st()
    [options, ignored_options] = parser.parse_known_args()

    # Validation
    if options.host is None:
        parser.print_usage()
        sys.exit(-1)
    else:
        os.environ['KATELLO_HOST'] = options.host
        os.environ['PROJECT'] = options.project
        os.environ['KATELLO_PORT'] = options.port
        os.environ['KATELLO_USER'] = options.katello_user
        os.environ['KATELLO_PASSWD'] = options.katello_passwd
        os.environ['DRIVER_NAME'] = options.driver
        os.environ['VERBOSITY'] = str(options.verbosity)
        os.environ['SSH_KEY'] = options.sshkey
        os.environ['ROOT'] = options.root
        os.environ['LOCALE'] = options.locale
        if options.sauce_user is not None:
            os.environ['SAUCE_USER'] = options.sauce_user
        if options.sauce_tunnel is not None:
            os.environ['SAUCE_TUNNEL'] = options.sauce_tunnel
        os.environ['SAUCE_KEY'] = options.sauce_key
        os.environ['SAUCE_OS'] = options.sauce_os
        os.environ['SAUCE_VERSION'] = options.sauce_version

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_name in options.tests:
        suite.addTests(loader.loadTestsFromName(test_name))

    runner = unittest.TextTestRunner(verbosity=options.verbosity)
    result = runner.run(suite)
