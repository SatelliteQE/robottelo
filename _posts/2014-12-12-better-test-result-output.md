---
layout: post
title: "Better test result output"
date: 2014-12-12 14:50:00
categories: update
author: Elyézer Rezende
---

[Pull request 1773](https://github.com/SatelliteQE/robottelo/pull/1773) removed the `nocapture` and `nologcapture` nose options from the `robottelo.properties.sample` file. This change was made to provide better test result output.

If you want have the same output as is presented in this post, remove the `nocapture` and `nologcapture` lines from your `robottelo.properties` file or just make them equal 0 instead of 1.

Consider the following Python module:

{% highlight python %}
import logging
import unittest

logging.basicConfig()


class TestCase(unittest.TestCase):
    def test_stdout(self):
        print('something on stdout')
        self.fail('failed')

    def test_logging(self):
        logging.getLogger(__name__).warning('WARNING')
        self.fail('failed')

    def test_logging_stdout(self):
        print('something on stdout')
        logging.getLogger(__name__).warning('WARNING')
        self.fail('failed')
{% endhighlight %}

Running the module with those options enable gives the following result:

    $ nosetests --nocapture --nologcapture test_output.py
    something on stdout
    WARNING:test_output:WARNING
    FWARNING:test_output:WARNING
    Fsomething on stdout
    F
    ======================================================================
    FAIL: test_logging_stdout (test_output.TestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    File "/Users/elyezer/code/robottelo/test_output.py", line 19, in test_logging_stdout
        self.fail('failed')
    AssertionError: failed

    ======================================================================
    FAIL: test_logging (test_output.TestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    File "/Users/elyezer/code/robottelo/test_output.py", line 14, in test_logging
        self.fail('failed')
    AssertionError: failed

    ======================================================================
    FAIL: test_stdout (test_output.TestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    File "/Users/elyezer/code/robottelo/test_output.py", line 10, in test_stdout
        self.fail('failed')
    AssertionError: failed

    ----------------------------------------------------------------------
    Ran 3 tests in 0.002s

    FAILED (failures=3)

As you can see, messages from tests are mixed in with messages from nose, and this results in lines like "Fsomething on stdout". This is not default nose behaviour, but it was done when Robottelo was first created, as the extra output helped find issues.

Robottelo is now much larger and better written, and it is run daily on a Jenkins continuous integration server. As a result, having the output while the automation runs is not good. The extra output makes it difficult to identify which messages correspond to which tests. Disabling the `nocapture` and `nologcapture` options alleviates this issue.

Running the example module without those options gives the following result:

    $ nosetests test_output.py
    FFF
    ======================================================================
    FAIL: test_logging_stdout (test_output.TestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    File "/Users/elyezer/code/robottelo/test_output.py", line 19, in test_logging_stdout
        self.fail('failed')
    AssertionError: failed
    -------------------- >> begin captured stdout << ---------------------
    something on stdout

    --------------------- >> end captured stdout << ----------------------
    -------------------- >> begin captured logging << --------------------
    test_output: WARNING: WARNING
    --------------------- >> end captured logging << ---------------------

    ======================================================================
    FAIL: test_logging (test_output.TestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    File "/Users/elyezer/code/robottelo/test_output.py", line 14, in test_logging
        self.fail('failed')
    AssertionError: failed
    -------------------- >> begin captured logging << --------------------
    test_output: WARNING: WARNING
    --------------------- >> end captured logging << ---------------------

    ======================================================================
    FAIL: test_stdout (test_output.TestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    File "/Users/elyezer/code/robottelo/test_output.py", line 10, in test_stdout
        self.fail('failed')
    AssertionError: failed
    -------------------- >> begin captured stdout << ---------------------
    something on stdout

    --------------------- >> end captured stdout << ----------------------

    ----------------------------------------------------------------------
    Ran 3 tests in 0.002s

    FAILED (failures=3)

At the beginning of the output we can see clearly that all three tests have failed (`FFF` output). And reading the test failures now shows what output corresponds to stdout and what corresponds to logging for that specific test.

Finally, with this update only relevant output will be shown, because just failures and errors output will be shown.
