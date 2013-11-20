#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import argparse
import glob
import os
import subprocess
import sys

# Borrowed from https://github.com/pulp/pulp/blob/master/run-tests.py
# Find and eradicate any existing .pyc files, so they do not eradicate us!
PROJECT_DIR = os.path.abspath(os.path.curdir)
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

subprocess.call(['find', PROJECT_DIR, '-name', '*.pyc', '-delete'])

parser = argparse.ArgumentParser()

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
    default='admin')

parser.add_argument(
    '-t',
    '--tests',
    choices=['cli', 'ui', '*'],
    default='cli',
    help='The type of the tests to be run. Options are CLI, UI, Both')

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

[options, ignored_options] = parser.parse_known_args()

os.environ['KATELLO_HOST'] = options.host
os.environ['PROJECT'] = options.project
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

env = os.environ.copy()


TESTS = [".".join(
    x.split('/')[-2:]
) for x in glob.glob(
    "%s/tests/%s/test_*.py" % (PROJECT_DIR, options.tests))
]

params = [
    'nosetests',
    '--verbosity=%s' % options.verbosity,
    "--tests",
    ",".join("tests.%s" % test_name[:-3] for test_name in TESTS),
]

subprocess.call(params, env=env)
