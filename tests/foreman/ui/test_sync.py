"""Test class for Custom Sync UI"""

import sys

if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo import entities, orm
from robottelo.common.constants import FAKE_1_YUM_REPO
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.session import Session


RHCT = [('rhel', 'rhct6', 'rhct65', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6.5'),
        ('rhel', 'rhct6', 'rhct65', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct65', 'repo_ver', '6.5'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6Server'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_ver', '6Server')]


@ddt
class Sync(UITestCase):
    """Implements Custom Sync tests in UI"""

    org_name = None
    org_id = None

    def setUp(self):
        super(Sync, self).setUp()
        # Make sure to use the Class' org_name instance
        if Sync.org_name is None:
            org_name = orm.StringField(str_type=('alphanumeric',),
                                       len=(5, 80)).get_value()
            org_attrs = entities.Organization(name=org_name).create()
            Sync.org_name = org_attrs['name']
            Sync.org_id = org_attrs['id']

    @attr('ui', 'sync', 'implemented')
    @data(*generate_strings_list())
    def test_sync_repos(self, repository_name):
        """@Test: Create Content Custom Sync with minimal input parameters

        @Feature: Content Custom Sync - Positive Create

        @Assert: Whether Sync is successful

        """

        # Creates new product
        product_attrs = entities.Product(
            organization=self.org_id
        ).create()
        # Creates new repository
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id']
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(Sync.org_name)
            session.nav.go_to_sync_status()
            sync = self.sync.sync_custom_repos(product_attrs['name'],
                                               [repository_name])
            self.assertIsNotNone(sync)

    @unittest.skip("Test needs to create manifests using stageportal stuff")
    def test_sync_rhrepos(self):
        """@Test: Create Content RedHat Sync with two repos.

        @Feature: Content RedHat Sync - Positive Create

        @Assert: Whether Syncing RedHat Repos is successful

        """

        repos = self.sync.create_repos_tree(RHCT)
        self.login.login(self.katello_user, self.katello_passwd)
        # TODO: Create manifests and import using stageportal stuff.
        self.navigator.go_to_red_hat_repositories()
        self.sync.enable_rh_repos(repos)
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_rh_repos(repos)
        self.assertIsNotNone(sync)
