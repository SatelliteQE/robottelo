# -*- encoding: utf-8 -*-
"""Test class for Packages UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import FAKE_0_YUM_REPO
from robottelo.decorators import tier2
from robottelo.test import UITestCase
from robottelo.ui.session import Session


class PackagesTestCase(UITestCase):
    """Implement tests for packages via UI"""

    @tier2
    def test_positive_search_in_repo(self):
        """Create product with yum repository assigned to it. Search for
        packages inside of it

        @Feature: Packages

        @Assert: Content search functionality works as intended and expected
        packages are present inside of repository
        """
        org = entities.Organization().create()
        product = entities.Product(
            name=gen_string('alpha'),
            organization=org,
        ).create()
        yum_repo = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            content_type='yum',
            url=FAKE_0_YUM_REPO,
        ).create()
        yum_repo.sync()

        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.package.select_repo(yum_repo.name)
            self.assertIsNotNone(self.package.search('bear'))
            self.assertIsNotNone(self.package.search('cheetah'))
