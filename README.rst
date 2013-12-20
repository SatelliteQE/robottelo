Robottelo
=========
This is an automation test suite for `The Foreman <http://theforeman.org/>`_ project.

My goal is to design a `keyword <http://en.wikipedia.org/wiki/Keyword-driven_testing>`_, `data <http://en.wikipedia.org/wiki/Data-driven_testing>`_ driven suite that can be used in a continuous integration environment.

Quickstart
==========

This page gives you a good introduction in how to get started with ``Robottelo``. For more information, please read the `documentation <http://robottelo.readthedocs.org/en/latest/>`_.

Requirements:
-------------
1)If you haven't cloned the source code yet, then make sure to do it now:

::

    git clone git://github.com/omaciel/robottelo.git

2)Pre-requisites

a) Consider using virtual-env with system-site-packages
Example:-
virtualenv --system-site-packages robottelo

b) Install locally modules in virtual-env using 'pip install -I'
rest will be picked from system site-packages.
Example:-
pip install -I boto


3)You may require the below packages/software installed.

a) Consider running 'yum groupinstall "Development Tools"'
   for fedora/RHEL or Development packages if installing the below
   modules via pip for your OS.

   NOTE:- [pip inturn installs python-rhsm via python-stageportal via requirements.txt,
           distribution package is only required for certificates]

b) 'yum install python-rhsm' for fedora/RHEL without pip
        (would require candlepin-stage.pem & redhat-uep.pem certs at /etc/rhsm/ca if installing via pip)

c) 'yum install m2crypto' for fedora/RHEL without pip
                        (required steps,
                                          'pip install m2crypto --no-clean' for fedora
                                          'cd /venv/build/M2Crypto'
                                          'chmod u+x fedora_setup.sh'
                                          './fedora_setup.sh build'
                                          './fedora_setup.sh install')

d) 'yum install rpm-python' for fedora/RHEL without pip
        (had no success with pip, I used fedora-package, found the recommended way to use is only via system-site-packages option for virtual-env)

e) 'yum install swig' for fedora/RHEL

4)Then, run **sudo pip install -I -r ./requirements.txt** from the root of the project to have all dependencies automatically installed.

Running the tests
=================

All tests are written so that it is possible to run them using Python Nose or Python's unittest module. For more instructions about how to run the tests take a look on the following sections.

Testing with Python Nose
------------------------
Tests can be run using the Python Nose module. Assuming that you have Nose installed (it will be already installed if you installed the requirements using the following command pip -r requirements.txt), that you have installed and configured **The Foreman** and have copied the **robottelo.properties.sample** file and saved it as **robottelo.properties**. Make sure to edit the **robottelo.properties** file and update the attributes to match your existing configuration. Now you can run all tests:

::

    nosetests -c robottelo.properties

The test arguments may be the path or Python import:

::

    nosetests -c robottelo.properties tests/cli/test_user.py
    nosetests -c robottelo.properties tests.cli.test_user

Run all cli tests (all modules under tests/cli path):

::

    nosetests -c robottelo.properties tests/cli

Run all UI tests (all modules under tests/ui path):

::

    nosetests -c robottelo.properties tests/ui

Multiple tests can also be invoked:

::

    nosetests -c robottelo.properties tests.cli.test_user tests.cli.test_model

Running individual test:

::

    nosetests -c robottelo.properties tests.cli.test_user:TestUser.test_create_user_utf8

For more information about nosestests command and its options see its help:

::

    nosetests --help

Testing with unittest module
----------------------------
Tests can be run using the Python unittest module. Assuming that you have installed and configured **The Foreman** and have copied the **robottelo.properties.sample** file and saved it as **robottelo.properties**. Make sure to edit the **robottelo.properties** file and update the attributes to match your existing configuration. Now you can run the unittest module from the command line to run tests from modules, classes or even individual test methods:

::

    python -m unittest tests.cli.test_user
    python -m unittest tests.cli.test_user.TestUser
    python -m unittest tests.cli.test_user.TestUser.test_create_user_utf8

Multiple tests can also be invoked:

::

    python -m unittest tests.cli.test_user tests.cli.test_model

If you want a more verbose output:

::

    python -m unittest -v tests.cli.test_user

For a list of all the command line options:

::

    python -m unittest -h

If you have at least Python 2.7 installed, you can take advantage of the unittest simple test dicovery:

::

    python -m unittest discover

Run all cli tests (all modules under tests/cli path):

::

    python -m unittest discover tests/cli

Run all UI tests (all modules under tests/ui path):

::

    python -m unittest discover tests/ui

If you want a more verbose output:

::

    python -m unittest discover -v

For more information about the Python's unittest module take a look on the Python's docs http://docs.python.org/2/library/unittest.html

Known Issues
============

Author
------

This software is developed by:
`Og Maciel <http://www.ogmaciel.com>`_.
