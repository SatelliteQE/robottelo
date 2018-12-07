Robottelo
=========

`Robottelo`_ is a test suite which exercises `The Foreman`_. All tests are
automated, suited for use in a continuous integration environment, and `data
driven`_. There are three types of tests:

* UI tests, which rely on Selenium's `WebDriver`_.
* CLI tests, which rely on `Paramiko`_.
* API tests, which rely on `Requests`_.

.. contents::

Quickstart
==========

The following is only a brief setup guide for `Robottelo`_. The section on
`Running the Tests`_ provides a more comprehensive guide to using Robottelo.

Robottelo requires SSH access to the Satellite 6 system under test, and this
SSH access is implemented by Paramiko. Install the headers for the following to
ensure that Paramiko's dependencies build correctly:

* OpenSSL
* Python development headers
* libffi

On Fedora, you can install these with the following command:

For python2.x::

    dnf install -y gcc git libffi-devel openssl-devel python2-devel \
        redhat-rpm-config
    
    dnf install libxml2-devel
    
For python3.x::

    dnf install -y gcc git libffi-devel openssl-devel python3-devel \
        redhat-rpm-config
    
    dnf install libxml2-devel

On Red Hat Enterprise Linux 7, you can install these with the following command::

    yum install -y gcc git libffi-devel openssl-devel python-devel \
        redhat-rpm-config
        
    yum install libxml2-devel

For more information, see `Paramiko: Installing
<http://www.paramiko.org/installing.html>`_.

Get the source code and install dependencies::

    $ git clone git://github.com/SatelliteQE/robottelo.git
    $ pip install -r requirements.txt

**Notes:**
    * For python 2.7, run ``pip install configparser`` for Satellite 6.2

That's it! You can now go ahead and start testing The Foreman. However, there
are a few other things you may wish to do before continuing:

1. You may want to install development tools (such as gcc) for your OS. If
   running Fedora or Red Hat Enterprise Linux, execute ``yum groupinstall
   "Development Tools"``. Make sure to use ``dnf`` instead of ``yum`` if
   ``dnf`` is available on your system.
2. You may wish to install the optional dependencies listed in
   ``requirements-optional.txt``. (Use pip, as shown above.) They are required
   for tasks like working with certificates, running the internal robottelo test
   suite and checking code quality with pylint.

Robottelo on Docker
-------------------

Robottelo is also available on `dockerhub`_.::

    $ docker pull satelliteqe/robottelo

It also can be built locally using the Dockerfile, in the main directory.::

    $ docker built -t robottelo .

In order to run tests, you will need to mount your robottelo.properties file.::

    $ docker run -v {path to robottelo dir}/robottelo.properties:/robottelo/robottelo.properties satelliteqe/robottelo <test command>

You can also mount the entire robottelo directory to include the properties file
and any new tests you have written.::

    $ docker run -it -v {path to robottelo dir}:/robottelo satelliteqe/robottelo /bin/bash

**Notes:**

- CLI tests run easiest if you include the root credentials in robottelo.properties
- UI tests should be configured to run through your SauceLabs account.

Running the Tests
=================

Before running any tests, you must create a configuration file::

    $ cp robottelo.properties.sample robottelo.properties
    $ vi robottelo.properties

That done, you can run tests using ``make``::

    $ make test-robottelo
    $ make test-docstrings
    $ make test-foreman-api
    $ make test-foreman-cli
    $ make test-foreman-ui
    $ make test-foreman-smoke

Robottelo provides two test suites, one for testing Robottelo itself and
another for testing Foreman/Satellite 6. Robottelo's tests are under the
tests/robottelo directory and the Foreman/Satellite 6 tests are under the
tests/foreman directory.

If you want to run tests without the aid of ``make``, you can do that with
either `pytest`_ , `unittest`_ or `nose`_. Just specify the path for the test suite you
want to run::

    $ pytest tests/robotello
    $ pytest tests/foreman
    $ python -m unittest discover -s tests/robottelo -t .
    $ python -m unittest discover -s tests/foreman -t .
    $ nosetests tests/robottelo
    $ nosetests tests/foreman

The following sections discuss, in detail, how to update the configuration file
and run tests directly.

Initial Configuration
---------------------

To configure Robottelo, create a file named ``robottelo.properties``. You can
use the ``robottelo.properties.sample`` file as a starting point. Then, edit the
configuration file so that at least the following attributes are set::

    server.hostname=[FULLY QUALIFIED DOMAIN NAME OR IP ADDRESS]
    server.ssh.key_private=[PATH TO YOUR SSH KEY]
    server.ssh.username=root
    project=sat
    locale=en_US
    remote=0
    smoke=0

    [foreman]
    admin.username=admin
    admin.password=changeme

Note that you only need to configure the SSH key if you want to run CLI tests.
There are other settings to configure what web browser to use for UI tests and
even configuration to run the automation using `SauceLabs`_. For more
information about what web browsers you can use, check Selenium's `WebDriver`_
documentation.

Testing With Pytest
---------------------

To run all tests::

    $ pytest

It is possible to run a specific subset of tests::

    $ pytest test_case.py
    $ pytest test_case.py::TestClass
    $ pytest test_case.py::TestClass::test_case_name

To get more verbose output, or run multiple tests::

    $ pytest tests/ -v
    $ pytest tests/robottelo/test_decorators.py \
             tests/robottelo/test_cli.py

To test The Foreman's API, CLI or UI, use the following commands respectively::

    $ pytest tests/foreman/api/
    $ pytest tests/foreman/cli/
    $ pytest tests/foreman/ui/

To collect from three directories in one run::

    $ pytest tests/foreman/{cli,api,ui}/test_host.py

To search in testcase names, in this case it will run just negative tests::

    $ pytest tests/foreman/cli/test_host.py -k negative

To run tests in several threads, in this case 4::

    $ pytest tests/foreman/cli/test_host.py -n 4

For more information about Python's `pytest`_ module, read the documentation.

Testing With Unittest
---------------------

To run all tests::

    $ python -m unittest discover \
        --start-directory tests/ \
        --top-level-directory .

It is possible to run a specific subset of tests::

    $ python -m unittest tests.robottelo.test_decorators
    $ python -m unittest tests.robottelo.test_decorators.DataDecoratorTestCase
    $ python -m unittest tests.robottelo.test_decorators.DataDecoratorTestCase.test_data_decorator_smoke

To get more verbose output, or run multiple tests::

    $ python -m unittest discover -s tests/ -t . -v
    $ python -m unittest \
        tests.robottelo.test_decorators \
        tests.robottelo.test_cli

To test The Foreman's API, CLI or UI, use the following commands respectively::

    $ python -m unittest discover -s tests/foreman/api/
    $ python -m unittest discover -s tests/foreman/cli/
    $ python -m unittest discover -s tests/foreman/ui/

For more information about Python's `unittest`_ module, read the documentation.

Testing With Nose
-----------------

You must have `nose`_ installed to execute the ``nosetests`` command.

To run all tests::

    $ nosetests

It is possible to run a specific subset of tests::

    $ nosetests tests.robottelo.test_decorators
    $ nosetests tests.robottelo.test_decorators:DataDecoratorTestCase
    $ nosetests tests.robottelo.test_decorators:DataDecoratorTestCase.test_data_decorator_smoke

To get more verbose output, or run multiple tests::

    $ nosetests -v
    $ nosetests tests.robottelo.test_decorators tests.robottelo.test_cli

To test The Foreman's API, CLI or UI, use the following commands respectively::

    $ nosetests tests.foreman.api
    $ nosetests tests.foreman.cli
    $ nosetests tests.foreman.ui

Many of the existing tests use `subTest`_ to allow for a more data-driven
methodology.  In order to run a specific test you need to override the way
``nosetests`` discovers test names. For instance, if you wanted to run only the
``test_positive_create_1`` data-driven tests for the ``foreman.cli.test_org``
module::

    $ nosetests -m test_positive_create_1 tests.foreman.cli.test_org

Running UI Tests On a Docker Browser
------------------------------------

It is possible to run UI tests within a docker container. To do this:

* Install docker. It is provided by the ``docker`` package on Fedora and Red
  Hat. Be aware that the package may call ``docker-io`` on old OS releases.
* Make sure that docker is up and running and the user that will run robottelo
  has permission to run docker commands. For more information check the docker
  installation guide https://docs.docker.com/engine/installation/.
* Pull the ``selenium/standalone-firefox`` image
* Set ``browser=docker`` at the ``[robottelo]`` section in the configuration
  file ``robottelo.properties``.

Once you've performed these steps, UI tests will no longer launch a web browser
on your system. Instead, UI tests launch a web browser within a docker
container.

Running UI Tests On SauceLabs
-----------------------------

It is possible to run UI tests on SauceLabs. To do this:

* Set ``browser=saucelabs`` at the ``[robottelo]`` section in the configuration
  file ``robottelo.properties``.
* Select the browser type by setting ``webdriver`` at the ``[robottelo]``
  section in the configuration file. Valid values are ``firefox``, ``chrome``
  and ``ie``.
* Fill ``saucelabs_user`` and ``saucelabs_key`` at the ``[robottelo]`` section
  in the configuration file with your Sauce OnDemand credentials.
* If the machine where Satellite 6 is installed is on a VPN or behind a
  firewall make sure to have SauceConnect running.
* Optional: install ``sauceclient`` python package if you want robottelo to
  report test success or failure back to SauceLabs.

Miscellany
==========

.. toctree::
    :hidden:

    committing
    code_standards
    reviewing_PRs
    features/index
    api/index

Want to contribute? Before submitting code, read through the :doc:`committing
guide </committing>` and **Robottelo** :doc:`code standards </code_standards>`.
Ready to start reviewing pull requests? We have :doc:`a guide </reviewing_PRs>`
for that too! Finally, the :doc:`API reference </api/index>` covers individual
functions, classes, methods and modules.

**Robottelo** is compatible with Python 2.7.

Bugs are listed `on GitHub <https://github.com/SatelliteQE/robottelo/issues>`_.
If you think you've found a new issue, please do one of the following:

* Open a new bug report on Github.
* Join the #robottelo IRC channel on Freenode (irc.freenode.net).

You can generate the documentation for Robottelo as follows, so long as you have
`Sphinx`_ and make installed::

    $ cd docs
    $ make html

You can generate a graph of Foreman entities and their dependencies, so long as
you have `graphviz`_ installed::

    $ make graph-entities

To check for code smells::

    $ make lint

The design and development for this software is led by `Og Maciel`_.

.. _data driven: http://en.wikipedia.org/wiki/Data-driven_testing
.. _dockerhub: https://hub.docker.com/r/satelliteqe/robottelo/
.. _subTest: https://docs.python.org/3/library/unittest.html#unittest.TestCase.subTest
.. _graphviz: http://graphviz.org/
.. _nose: https://nose.readthedocs.org/en/latest/index.html
.. _Og Maciel: http://www.ogmaciel.com
.. _Paramiko: http://www.paramiko.org/
.. _Pytest: https://docs.pytest.org/en/latest/contents.html
.. _Requests: http://docs.python-requests.org/en/latest/
.. _Robottelo: https://github.com/SatelliteQE/robottelo
.. _SauceLabs: https://saucelabs.com/
.. _Sphinx: http://sphinx-doc.org/index.html
.. _The Foreman: http://theforeman.org/
.. _unittest: http://docs.python.org/2/library/unittest.html
.. _WebDriver: http://docs.seleniumhq.org/projects/webdriver/
