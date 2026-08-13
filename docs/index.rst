Robottelo
=========

`Robottelo`_ is a test suite which exercises `The Foreman`_. All tests are
automated, suited for use in a continuous integration environment, and `data
driven`_. There are three types of tests:

* UI tests, which rely on Selenium's `WebDriver`_.
* CLI tests, which rely on `ssh2-python`_.
* API tests, which rely on `Requests`_.

.. contents::

Quickstart
==========

The following is only a brief setup guide for `Robottelo`_. The section on
`Running the tests`_ provides a more comprehensive guide to using Robottelo.

Recommendation: Create a virtual Python environment for the following setup.

Create virtual environment for Python 3.x::

    $ python3 -m venv <venv_name>

To activate the virtual environment::

    $ source <venv_name>/bin/activate

To exit the environment::

    $ deactivate

On Fedora, you can install Robottelo with the following commands:

For Python 3.x::

    $ dnf install -y gcc git python3-devel libxml2-devel

Get the source code and install dependencies::

    $ git clone git://github.com/SatelliteQE/robottelo.git
    $ cd robottelo/
    $ pip install -r requirements.txt

That's it! You can now go ahead and start testing The Foreman. However, there
are a few other things you may wish to do before continuing:

1. You may want to install development tools (such as ``gcc``) for your OS. If
running Fedora or Red Hat Enterprise Linux, execute ``yum groupinstall
"Development Tools"``. Make sure to use ``dnf`` instead of ``yum`` if
``dnf`` is available on your system.
2. You may wish to install the optional dependencies listed in
``requirements-optional.txt``. (Use ``pip``, as shown above.) They are required
for tasks like working with certificates, running the internal Robottelo test
suite and checking code quality with pre-commit.

Robottelo on Podman
-------------------

Robottelo is also available on `quay`_.::

    $ podman pull quay.io/satelliteqe/robottelo:latest

It also can be built locally using the Dockerfile, in the main directory.::

    $ podman build -t robottelo .

In order to run tests, you will need to mount your config directory.::

    $ podman run -v {path to conf directory}:/opt/app-root/src/robottelo/conf satelliteqe/robottelo <test command>

You can also mount the entire main directory, to include both the config directory as well as any
new tests you have written.::

    $ podman run -it -v {path to robottelo directory}:/opt/app-root/src/robottelo satelliteqe/robottelo /bin/bash

**Notes:**

- UI tests should be configured to run through a Selenium server.

Running the tests
=================

Before running any tests, you must set up the necessary configuration files::

    $ cd conf/
    $ cp virtwho.yaml.template virtwho.yaml
    $ vi virtwho.yaml
    $ cp broker.yaml.template broker.yaml
    $ vi broker.yaml
    $ cp robottelo.yaml.template robottelo.yaml
    $ vi robottelo.yaml
    $ cp server.yaml.template server.yaml
    $ vi server.yaml
    # [...]
    $ cd ..

That done, you can run tests using ``make``::

    $ make test-robottelo
    $ make test-docstrings
    $ make test-foreman-api
    $ make test-foreman-cli
    $ make test-foreman-ui
    $ make test-foreman-smoke

Robottelo provides two test suites, one for testing Robottelo itself and
another for testing Foreman/Satellite 6. Robottelo's tests are under the
``tests/robottelo`` directory and the Foreman/Satellite 6 tests are under the
``tests/foreman`` directory.

If you want to run tests without the aid of ``make``, you can do that with
either `pytest`_ or `unittest`_. Just specify the path for the test suite you
want to run::

    $ pytest tests/robottelo
    $ pytest tests/foreman
    $ python -m unittest discover -s tests/robottelo -t .

The following sections discuss, in detail, how to update the configuration file
and run tests directly.

Initial Configuration
---------------------

To configure Robottelo, multiple template YAML files are present to execute different test cases in Robottelo.

1. ``server.yaml`` : Populate this file with SSH credentials::

    HOSTNAMES: ["satellite.example.com"]
    SSH_USERNAME: username
    SSH_PASSWORD: password | SSH_KEY: /path/to/ssh/key | SSH_KEY_STRING: ssh_key_as_string

Note that you only need to configure the SSH key if you want to run CLI tests.

Using environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each of the sections in ``conf/`` files can be mapped to an environment variable prefixed with ``ROBOTTELO_``.
For example, if you want to override the server hostname without changing the config file::

    $ export ROBOTTELO_server__hostnames='["satellite.example.com"]'

The env vars follow the format ``ROBOTTELO_{section}__{key}``. Further examples::

    $ export ROBOTTELO_server__ssh_key=/path/to/ssh/key
    $ export ROBOTTELO_ui__grid_url=http://grid.example.com:4444

Using Secrets from Vault
^^^^^^^^^^^^^^^^^^^^^^^^

Robottelo is enabled to fetch secrets from Hashicorp Vault via Dynaconf at runtime.

To enable the integration:

#. Copy .env.example to .env file for Dynaconf settings object to connect with Vault.
#. Set VAULT_ENABLED_FOR_DYNACONF to true to enable Vault integration.
#. Set the corresponding values for VAULT_URL_FOR_DYNACONF, VAULT_MOUNT_POINT_FOR_DYNACONF and VAULT_PATH_FOR_DYNACONF.
#. Run ``make vault-login`` to log in into Vault and to generate and set the OIDC token automatically.
#. Edit config files in ``conf/`` and update settings to take values from Vault with the format ``@format {this._secret_name_in_vault_}``.

Testing with pytest
-------------------

To run all tests::

    $ pytest

It is possible to run a specific subset of tests::

    $ pytest test_case.py
    $ pytest test_case.py::TestClass
    $ pytest test_case.py::TestClass::test_case_name

To get more verbose output, or run multiple tests::

    $ pytest tests/ -v
    $ pytest tests/robottelo/test_decorators.py tests/robottelo/test_cli.py

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


Running UI tests on a local Selenium container
----------------------------------------------

It is possible to run UI tests with a standalone Selenium browser container:

.. code-block:: shell

    $ . selenium_grid.sh
    $ selenium_standalone_start
    Running selenium browser:
    [...]
    <CONTAINER_ID>

We can check that the container started:

.. code-block:: shell

    $ podman ps -a | grep selenium
    <CONTAINER_ID>  docker.io/selenium/standalone-chrome:latest  /opt/bin/entry_po...  4 minutes ago  Up 4 minutes  0.0.0.0:4444->4444/tcp, 0.0.0.0:7900->7900/tcp, 4442-4443/tcp, 5900/tcp, 9000/tcp  standalone-chrome

    $ xdg-open http://localhost:4444/ui/

To clean up the container after the test, run the command:

.. code-block:: shell

    $ selenium_standalone_cleanup


Running UI tests on a local Selenium Grid
-----------------------------------------

.. code-block:: shell

    $ . selenium_grid.sh
    $ selenium_grid_start_hub
    Running selenium hub:
    <HUB_ID>

    $ selenium_grid_start_node
    Running selenium node:
    <NODE_1_ID>

    $ selenium_grid_start_node
    Running selenium node:
    <NODE_2_ID>

    $ selenium_grid_start_node
    Running selenium node:
    <NODE_3_ID>

    $ selenium_grid_start_node
    Running selenium node:
    <NODE_4_ID>

We can check that the containers started:

.. code-block:: shell

    $ podman ps -a | grep selenium
    <HUB_ID>     docker.io/selenium/hub:latest         /opt/bin/entry_po... 33 seconds ago Up 33 seconds ago 0.0.0.0:4442-4445->4442-4445/tcp  selenium-hub
    <NODE_1_ID>  docker.io/selenium/node-chrome:latest /opt/bin/entry_po... 30 seconds ago Up 30 seconds ago                                   selenium-node-chrome-f4qVX
    <NODE_2_ID>  docker.io/selenium/node-chrome:latest /opt/bin/entry_po... 28 seconds ago Up 28 seconds ago                                   selenium-node-chrome-3k56l
    <NODE_3_ID>  docker.io/selenium/node-chrome:latest /opt/bin/entry_po... 26 seconds ago Up 26 seconds ago                                   selenium-node-chrome-KIAOk
    <NODE_4_ID>  docker.io/selenium/node-chrome:latest /opt/bin/entry_po... 24 seconds ago Up 24 seconds ago                                   selenium-node-chrome-JQhOi

    $ xdg-open http://localhost:4444/ui/

To clean up the containers after the test, run the command::

    $ selenium_grid_cleanup


Miscellany
==========

.. toctree::
    :hidden:

    committing
    code_standards
    reviewing_PRs
    features/index
    autoapi/index

Want to contribute? Before submitting code, read through the :doc:`committing
guide </committing>` and **Robottelo** :doc:`code standards </code_standards>`.
Ready to start reviewing pull requests? We have :doc:`a guide </reviewing_PRs>`
for that too! Finally, the :doc:`API reference </autoapi/index>` covers
individual functions, classes, methods and modules.

**Robottelo** is compatible with Python 3.12+.

Bugs are listed `on GitHub <https://github.com/SatelliteQE/robottelo/issues>`_.
If you think you've found a new issue, please open a new bug report there.

You can generate the documentation for Robottelo as follows, so long as you have
`Sphinx`_ and make installed::

    $ cd docs
    $ make html

You can generate a graph of Foreman entities and their dependencies, so long as
you have `graphviz`_ installed::

    $ make graph-entities

To check for code smells::

    $ pre-commit install-hooks
    $ pre-commit run --all-files

.. _data driven: http://en.wikipedia.org/wiki/Data-driven_testing
.. _graphviz: http://graphviz.org/
.. _Pytest: https://docs.pytest.org/en/latest/contents.html
.. _quay: https://quay.io/repository/satelliteqe/robottelo
.. _Requests: http://docs.python-requests.org/en/latest/
.. _Robottelo: https://github.com/SatelliteQE/robottelo
.. _ssh2-python: https://pypi.org/project/ssh2-python/
.. _Sphinx: http://sphinx-doc.org/index.html
.. _The Foreman: http://theforeman.org/
.. _unittest: http://docs.python.org/2/library/unittest.html
.. _WebDriver: http://docs.seleniumhq.org/projects/webdriver/
