.. Robottelo documentation master file, created by
   sphinx-quickstart on Tue May  8 14:10:25 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Robottelo
=========
This is an automation test suite for `The Foreman <http://theforeman.org/>`_ project.

My goal is to design a `keyword <http://en.wikipedia.org/wiki/Keyword-driven_testing>`_, `data <http://en.wikipedia.org/wiki/Data-driven_testing>`_ driven suite that can be used in a continuous integration environment.

Quickstart
==========

This page gives you a good introduction in how to get started with ``Robottelo``. For more information, please read the `documentation <http://robottelo.readthedocs.org/en/latest/>`_.

Requirements:
-------------
If you haven't cloned the source code yet, then make sure to do it now:

::

    git clone git://github.com/omaciel/robottelo.git

Then, run **sudo pip install -r ./requirements.txt** from the root of the project to have all dependencies automatically installed.

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

Contents:

.. toctree::
   :maxdepth: 2

   records
   lib

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
