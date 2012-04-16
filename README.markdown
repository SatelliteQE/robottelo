Robottelo:
==========

This is an automation test suite for the [*Katello*](http://katello.org/) project based in the [*Robot*](https://code.google.com/p/robotframework/) testing framework.

My goal is to design a [*keyword*](http://en.wikipedia.org/wiki/Keyword-driven_testing), [*data*](Data-driven testing) driven suite that can be used in a continuous integration environment.

Requirements:
=============


Usage:
======

* To run a single test file:
  pybot --variable BROWSER:firefox --variable HOST:www.example.com --variable APP:katello src/tests/e2e.txt

* To run a specific test:
  pybot --variable BROWSER:firefox --variable HOST:www.example.com --variable APP:katello src/tests/e2e.txt

[Og Maciel](http://ogmaciel.tumblr.com)
