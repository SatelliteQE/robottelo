#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    README = f.read()

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
    install_requires=[
        'cachetools==1.1.6',
        'cryptography==1.4',
        'fauxfactory==2.0.9',
        'inflector==2.0.11',
        # 'nailgun',
        'blinker==1.4',
        'numpy==1.11.1',
        'paramiko==2.0.2',
        'pygal==2.2.3',
        'pytest==2.9.2',
        'python-bugzilla==1.2.2',
        'PyYAML==3.11',
        'requests==2.10.0',
        'selenium==2.48.0',
        'six==1.10.0',
        'unittest2==1.1.0',
    ],
    license='GNU GPL v3.0',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux'
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
