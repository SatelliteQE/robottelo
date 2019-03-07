Decorators
==========

This section explains Robottelo decorators.

.. contents::

Modules
-------

Robottelo decorators are located under
:doc:`decorator package </api/robottelo.decorators>`. Most of them are used to
control if a test must be skipped or executed accordingly with specific
configurations.

stubbed
-------

``stubbed`` skips any test it decorates. A reason can be provided as parameter
and its default is "Not Implemented". Most of times it is used to define all
manual (not automated) tests related to a feature. Example::

    from robottelo.decorators import stubbed

    @stubbed()
    def test_negative_create_matcher_attribute_priority(self):
        """Test will be implemented later"""

    @stubbed('Some other reason than not implemented')
    def test_positive_create_matcher_attribute_priority(self):
        """Test will be implemented later"""

Please note that ''stubbed'' is a decorator generator, and cannot be used as a
"classic" Python decorator - it must be ''\@stubbed()'', not ''\@stubbed''
(note the parenthesis).

skip_if_bug_open
----------------

``skip_if_bug_open`` skips test based on bug tracker status. Currently Bugzilla
and Redmine are supported. The decorator receives two parameters. The first
indicates the tracker and must be one of 'bugzilla' or 'redmine'. The second
parameter indicates the bug id on respective bug tracker. Example::

    from robottelo.decorators import skip_if_bug_open

    @skip_if_bug_open('bugzilla', 1297308)
    def test_negative_add_puppet_content(self):
        """Attempt to associate puppet repos within a custom content
        view directly
        """

    @skip_if_bug_open('redmine', 23456789)
    def test_positive_add_puppet_content(self):
        """Attempt to associate puppet repos within a custom content
        view directly
        """

Decorator communicates with bug tracker to know the status of respective bug
id. If it is still open, test will be skipped. Once bz is fixed and moved to
ON_QA or Verified state, test will automatically be run with next builds.

This is useful to allow QE team automating test cases even before a bug is
fixed or a feature is implemented, while test will not be considered a build
fail until the issue has it state changed.

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

tier[n]
---------

This set of decorators defines test levels:

* ``tier1`` marks component level functional tests (that verify defined functional requirements using a range of normal and erroneous input data). Example::

    from robottelo.decorators import tier1

    @tier1
    def test_positive_create_with_username(self):
        """Create User for all variations of Username"""

* ``tier2`` marks integration level functional tests and may include basic non-functional tests (security, performance regression, installation, compose validation). Example::

    from robottelo.decorators import tier2

    @tier2
    def test_positive_view_cve(self):
        """View CVE number(s) in Errata Details page"""

* ``tier3`` marks system level tests::

    from robottelo.decorators import tier3

    @tier3
    def test_positive_sync_with_enabled_notification(self):
        """Receive email after every sync operation"""

* ``tier4`` marks complex and long running tests. Example::

    from robottelo.decorators import tier4

    @tier4
    def test_positive_upload_to_satellite(self):
        """Perform end to end oscap test and upload reports"""

skip_if_not_set
---------------

``skip_if_not_set`` skips test if one or more specified configuration options is not set in ``robottelo.properties``. It is used to define tests specific to a selected (optional) feature. Without the decorator, such tests would fail if the tested feature is not enabled. Example::

    from robottelo.decorators import skip_if_not_set

    @skip_if_not_set('ldap')
    def test_positive_ldap_auth_usergroup_user_add(self):
        """New user added to UserGroup inherits roles"""

cacheable
---------

``cacheable`` makes an optional object cache available. This is used when creating factory objects for CLI tests. For example::

    from robottelo.decorators import cacheable

    @cacheable
    def make_role(options=None):
        """create a role using ``hammer role create``"""

run_only_on
-----------

``run_only_on`` skips test based on a server mode. It takes one parameter that is either 'sat' (to define Satellite specific tests) or 'sam' (to define tests specific to Subscription Asset Manager). For example::

    from robottelo.decorators import run_only_on

    @run_only_on('sat')
    def test_negative_create_with_invalid_name(self):
        """Create a new template with invalid names"""

The server mode is determined from ``settings.project``. Skip this decorator if the test is applicable to both Satellite and SAM.

run_in_one_thread
-----------------

``run_in_one_thread`` defines test that cannot be run in parallel with other tests. This is useful for preventing conflicts between tests that interact with the same component. Example::

    from robottelo.decorators import run_in_one_thread

    @run_in_one_thread
    def test_positive_delete_manifest(self):
        """Check if deleting a manifest removes it from Activation key"""
