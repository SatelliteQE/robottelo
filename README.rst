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

Running the test
----------------
Assuming you have already installed and configured **The Foreman**, the simplest way to execute tests is to use the included **robottelo_runner** script. First, make sure to copy the **robottelo.properties.sample** file and save it as **robottelo.properties**. Next, edit the file and update the attributes to match your existing configuration, and run your tests:

::

    python robottelo_runner.py --tests tests.ui.test_Login

Multiple tests can also be invoked:

::

    python robottelo_runner.py --tests tests.ui.test_Login --tests tests.ui.test_Organization

Running individual tests from a test suite from the command line:

::

    python robottelo_runner.py --tests tests.ui.test_Login.test_successful_login

You can also run tests directly using either **unittest** or **nosetests** provided you pass all the expected arguments:

::

    KATELLO_HOST=www.example.com PROJECT=katello DRIVER=firefox python -m unittest tests.ui.test_Login.test_successful_login

or

::

    KATELLO_HOST=www.example.com PROJECT=katello DRIVER=firefox nosetests tests.ui.test_Login.test_successful_login

Known Issues
============

Author
------

This software is developed by:
`Og Maciel <http://www.ogmaciel.com>`_.
