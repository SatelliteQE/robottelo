Robottelo
=========

This is an automation test suite for [The Foreman](http://theforeman.org/)
project.

The goal is to design a [data
driven](http://en.wikipedia.org/wiki/Data-driven_testing) test suite that can be
used in a continuous integration environment.

**Robottelo** uses Selenium's
[WebDriver](http://docs.seleniumhq.org/projects/webdriver/) for all user
interface (UI) tests, [Paramiko](http://www.paramiko.org/) for all command line
interface (CLI) tests and [Requests](http://docs.python-requests.org/en/latest/)
for API tests.

Quickstart
==========

This page gives you a brief introduction in how to get started with
**Robottelo**. For more information, please read the
[documentation](http://robottelo.readthedocs.org/en/latest/).

Requirements:
-------------

* If you haven't cloned the source code yet, then make sure to do it now:

```bash
$ git clone git://github.com/omaciel/robottelo.git
```

* Install locally all of **Robottelo**'s dependency modules using ``pip
  install``:

```bash
$ pip install -r requirements.txt
```

**NOTE 1**: You may want to consider running ``yum groupinstall "Development
Tools"`` for **Fedora/RHEL** or **Development** packages if installing python
modules via pip for your OS.

**NOTE 2**: You may also want to consider running ``yum install openssl-devel
python-devel`` packages for ``python-stageportal`` installation.

**NOTE 3**: Some of the modules that will be installed via the pip  command
above are ``python-rhsm`` and ``python-stageportal`` which are only required for
certificates.

Running the tests
=================

All tests are written so that it is possible to run them using Python
[Nosetests](https://nose.readthedocs.org/en/latest/man.html) or Python's
[Unittest](http://docs.python.org/2/library/unittest.html) module. For more
instructions about how to run the tests take a look at the following sections.

Initial Configuration
---------------------

The first thing you need to do is copy the existing
**robottelo.properties.sample** files and save it as **robottelo.properties**
inside of the checkout directory. Then, edit it so that at least the following
attributes are set:

```INI
server.hostname=[FULLY QUALIFIED DOMAIN NAME]
server.ssh.key_private=[PATH TO YOUR SSH KEY]
server.ssh.username=root
project=foreman
locale=en_US
remote=0

[foreman]
admin.username=admin
admin.password=changeme
```

Note that you only need to configure the **ssh key** if you want to run **CLI**
tests. There are other settings to configure what web browser to use for UI
tests and even configuration to run the automation using
[SauceLabs](https://saucelabs.com/). For more information about what web
browsers you can use, check Selenium's WebDriver
[documentation](http://docs.seleniumhq.org/projects/webdriver/).

Testing with Python Nose
------------------------

Tests can be run using the Python Nose module. Assuming that you have Nose
installed (it will be already installed if you installed the required modules),
you can run all tests:

```bash
$ nosetests -c robottelo.properties
```

The test arguments can be either the path to the ``tests`` directory or Python
import-like style:

```bash
$ nosetests -c robottelo.properties tests/foreman/cli/test_user.py
$ nosetests -c robottelo.properties tests.foreman.cli.test_user
```

Run all cli tests (all modules under tests/foreman/cli path):

```bash
$ nosetests -c robottelo.properties tests/foreman/cli
```

Run all UI tests (all modules under tests/foreman/ui path):

```bash
$ nosetests -c robottelo.properties tests/foreman/ui
```

Multiple tests can also be invoked:

```bash
$ nosetests -c robottelo.properties tests.foreman.cli.test_user tests.foreman.cli.test_model
```

Running individual test:

```bash
$ nosetests -c robottelo.properties tests.foreman.cli.test_user:TestUser.test_create_user_utf8
```

Many of the existing tests use the [DDT](http://ddt.readthedocs.org/en/latest/)
module to allow for a more data-driven methodology and in order to run a
specific test you need override the way ``nosetests`` discovers test names. For
instance, if you wanted to run only the ``test_positive_create_1`` data-driven
tests for the ``foreman/cli/test_org.py`` module:

```bash
$ nosetests -c robottelo.properties -m test_positive_create_1 tests/foreman/cli/test_org.py
```

Testing with unittest module
----------------------------

Tests can also be run using Python's **unittest** module:

```bash
$ python -m unittest tests.foreman.cli.test_user
$ python -m unittest tests.foreman.cli.test_user.TestUser
$ python -m unittest tests.foreman.cli.test_user.TestUser.test_create_user_utf8
```

Multiple tests can also be invoked:

```bash
$ python -m unittest tests.foreman.cli.test_user tests.foreman..cli.test_model
```

If you want a more verbose output:

```bash
$ python -m unittest -v tests.foreman.cli.test_user
```

If you have at least Python 2.7 installed, you can take advantage of unittest
simple test dicovery:

```bash
$ python -m unittest discover
```

Run all cli tests (all modules under tests/foreman/cli path):

```bash
$ python -m unittest discover tests/foreman/cli
```

Run all UI tests (all modules under tests/foreman/ui path):

```bash
$ python -m unittest discover tests/foreman/ui
```

If you want a more verbose output:

```bash
$ python -m unittest discover -v
```

For more information about Python's unittest module take a look on the Python's
[documentation](http://docs.python.org/2/library/unittest.html)

Known Issues
============

Author
------

The design and development for this software is led by: [Og
Maciel](http://www.ogmaciel.com)
