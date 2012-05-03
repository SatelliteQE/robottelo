Robottelo:
==========

This is an automation test suite for the [*Katello*](http://katello.org/) project based in the [*Robot*](https://code.google.com/p/robotframework/) testing framework.

My goal is to design a [*keyword*](http://en.wikipedia.org/wiki/Keyword-driven_testing), [*data*](Data-driven testing) driven suite that can be used in a continuous integration environment.

Requirements:
-------------

Run **pip install -r ./requirements.txt** from the root of the project to have all dependencies automatically installed.

Usage:
------

Tests can be invoked by using the standard RobotFramework format of running **pybot** and arguments:
::
    pybot --variable BROWSER:firefox --variable HOST:www.example.com --variable APP:katello src/tests/login.txt

Many global variables are provided in the **resources/global.txt** file and should work for a default installation of Katello, but you can overide them by providing new values via the command line:
::
    pybot --variable ADMIN_USER:my_admin --variable ADMIN_PASSWD:my_passwd --variable APP:katello src/tests/login.txt

You can also provide a python **variables** file as an argument, which allows you to have sensitive information outside the source code:
::
    pybot --variablefile /path/to/variables.py src/tests/e2e.txt

The file **variables.py** would then contain:
::
    #!/usr/bin/env python
    # -*- encoding: utf-8 -*-
    # vim: ts=4 sw=4 expandtab ai

    BROWSER = 'firefox'
    HOST = 'www.example.com'
    APP = 'katello'
    ADMIN_USER = admin
    ADMIN_PASSWD = passwd

Author
------

This software is developed by:
`Og Maciel <http://ogmaciel.tumblr.com>`_.
