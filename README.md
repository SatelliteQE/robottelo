Robottelo
=========

Robottelo is a test suite which exercises [The Foreman](http://theforeman.org/).
All tests are automated, suited for use in a continuous integration environment,
and [data driven](http://en.wikipedia.org/wiki/Data-driven_testing). There are
three types of tests:

* UI tests, which rely on Selenium's
  [WebDriver](http://docs.seleniumhq.org/projects/webdriver/)
* CLI tests, which rely on [Paramiko](http://www.paramiko.org/)
* API tests, which rely on
  [Requests](http://docs.python-requests.org/en/latest/)

Quickstart
==========

The following is only a brief setup guide for **Robottelo**. More thorough
documentation is available at [Read the
Docs](http://robottelo.readthedocs.org/en/latest/).

Requirements:
-------------

Get the source code (if you haven't done so already) and install dependencies:

```bash
$ git clone git://github.com/omaciel/robottelo.git
$ pip install -r requirements.txt
```

That's it! You can now go ahead and start testing The Foreman. However, there
are a few other things you may wish to do before continuing:

1. You may want to install development tools (such as gcc) for your OS. If
   running **Fedora/RHEL**, execute `yum groupinstall "Development Tools"`.
2. If using `python-stageportal`, you should install `openssl-devel`,
   `python-devel` and `python-rhsm`. They are required for working with
   certificates.

Running the Tests
=================

All tests are written so that it is possible to run them using either Python
[Nosetests](https://nose.readthedocs.org/en/latest/man.html) or Python's
[Unittest](http://docs.python.org/2/library/unittest.html) module. For more
instructions about how to run the tests take a look at the following sections.

Initial Configuration
---------------------

The first thing you need to do is copy the existing
`robottelo.properties.sample` files and save it as `robottelo.properties` inside
of the checkout directory. Then, edit it so that at least the following
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

Testing With Python Nose
------------------------

Tests can be run using the Python Nose module. Assuming that you have Nose
installed (it will be already installed if you installed the required modules),
you can run all tests:

```bash
$ nosetests -c robottelo.properties
```

The test arguments can be either the path to the `tests` directory or Python
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
specific test you need override the way `nosetests` discovers test names. For
instance, if you wanted to run only the `test_positive_create_1` data-driven
tests for the `foreman/cli/test_org.py` module:

```bash
$ nosetests -c robottelo.properties -m test_positive_create_1 tests/foreman/cli/test_org.py
```

Testing With Unittest
---------------------

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

Bugs are listed [on GitHub](https://github.com/omaciel/robottelo/issues). If you
think you've found a new issue, please do one of the following:

* Open a new bug report on Github.
* Join the #robottelo IRC channel on Freenode.

Author
======

The design and development for this software is led by [Og
Maciel](http://www.ogmaciel.com)
