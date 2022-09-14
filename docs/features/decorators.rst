Decorators
==========

This section explains Robottelo decorators.

.. contents::

Modules
-------

Robottelo decorators are located under
:doc:`decorator package </autoapi/robottelo/decorators/index>`. Most of them are used to
control if a test must be skipped or executed accordingly with specific
configurations.


cacheable
---------

``cacheable`` makes an optional object cache available. This is used when creating factory objects for CLI tests. For example::

    from robottelo.utils.decorators import cacheable

    @cacheable
    def make_role(options=None):
        """create a role using ``hammer role create``"""
