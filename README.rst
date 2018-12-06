Robottelo
=========

.. image:: https://codecov.io/gh/SatelliteQE/robottelo/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/SatelliteQE/robottelo

.. image:: https://api.travis-ci.org/SatelliteQE/robottelo.svg?branch=master
  :target: https://travis-ci.org/SatelliteQE/robottelo

.. image:: https://img.shields.io/pypi/pyversions/robottelo.svg
  :target: https://pypi.org/project/robottelo

.. image:: https://img.shields.io/pypi/l/robottelo.svg
  :target: https://pypi.org/project/robottelo

`Robottelo`_ is a test suite which exercises `The Foreman`_. All tests are
automated, suited for use in a continuous integration environment, and `data
driven`_. There are three types of tests:

* UI tests, which rely on Selenium's `WebDriver`_.
* CLI tests, which rely on `Paramiko`_.
* API tests, which rely on `Requests`_.

The `full documentation
<http://robottelo.readthedocs.org/en/latest/index.html>`_ is available on
ReadTheDocs. It can also be generated locally::

    pip install -r requirements.txt
    pip install -r requirements-optional.txt
    make docs

.. _data driven: http://en.wikipedia.org/wiki/Data-driven_testing
.. _Paramiko: http://www.paramiko.org/
.. _Requests: http://docs.python-requests.org/en/latest/
.. _Robottelo: https://github.com/SatelliteQE/robottelo
.. _The Foreman: http://theforeman.org/
.. _WebDriver: http://docs.seleniumhq.org/projects/webdriver/
