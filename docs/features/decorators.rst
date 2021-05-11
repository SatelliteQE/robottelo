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

skip_if_os
----------

``skip_if_os`` skips test based on Foreman/Satellite host os version. It
communicates with host defined on ``robottello.properties`` to get its os
version. Currently it checks only Red Hat Enterprise Linux versions. Example::

    from robottelo.decorators.host import skip_if_os

    @skip_if_os('RHEL6')
    def test_positive_create_custom_ostree_repo(self):
        """Create Custom ostree repository"""

    @skip_if_os('RHEL6', 'RHEL5')
    def test_negative_create_custom_ostree_repo(self):
        """Create Custom ostree repository"""

The first test will be skipped if host os is RHEL6.x.y, where x and y can be
any number. If ``RHEL6.1`` was used as parameter it would skip for any
RHEL6.1.z version and so on.

Arbitrary number versions can be passed as parameters. On second test both RHEL
5 and 6 families would be skipped.

This decorator is used to avoid false failures when an feature is supported
only on one os version. For example, ostree repository is available
in RHEL7 but not in RHEL6.


cacheable
---------

``cacheable`` makes an optional object cache available. This is used when creating factory objects for CLI tests. For example::

    from robottelo.decorators import cacheable

    @cacheable
    def make_role(options=None):
        """create a role using ``hammer role create``"""
