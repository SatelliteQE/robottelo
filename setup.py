#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import system, environ
from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    README = f.read()

if system('curl --version | grep NSS 2>/dev/null') != 0:
    environ['PYCURL_SSL_LIBRARY'] = 'openssl'
    system('pip install --compile --install-option="--with-openssl" pycurl')
else:
    environ['PYCURL_SSL_LIBRARY'] = 'nss'
    system('pip install --compile --install-option="--with-nss" pycurl')

setup(
    name='robottelo',
    version='0.1.0',
    description='Robottelo is a test suite which exercises The Foreman.',
    long_description=README,
    author=u'Satellite QE Team',
    url='https://github.com/SatelliteQE/robottelo',
    packages=find_packages(exclude=['tests*']),
    package_data={'': ['LICENSE']},
    include_package_data=True,
    license='GNU GPL v3.0',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
    ),
)
