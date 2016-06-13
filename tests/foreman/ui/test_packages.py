# -*- encoding: utf-8 -*-
"""Test class for Packages UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import FAKE_0_YUM_REPO, FAKE_3_YUM_REPO
from robottelo.decorators import tier2
from robottelo.test import UITestCase
from robottelo.ui.session import Session


class PackagesTestCase(UITestCase):
    """Implement tests for packages via UI"""

    @classmethod
    def setUpClass(cls):
        super(PackagesTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        product = entities.Product(organization=cls.organization).create()
        cls.yum_repo = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            content_type='yum',
            url=FAKE_0_YUM_REPO,
        ).create()
        cls.yum_repo2 = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            content_type='yum',
            url=FAKE_3_YUM_REPO,
        ).create()
        cls.yum_repo.sync()
        cls.yum_repo2.sync()

    @tier2
    def test_positive_search_in_repo(self):
        """Create product with yum repository assigned to it. Search for
        packages inside of it

        @Feature: Packages

        @Assert: Content search functionality works as intended and expected
        packages are present inside of repository
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.package.select_repo(self.yum_repo.name)
            self.assertIsNotNone(self.package.search('bear'))
            self.assertIsNotNone(self.package.search('cheetah'))

    @tier2
    def test_positive_search_in_multiple_repos(self):
        """Create product with two different yum repositories assigned to it.
        Search for packages inside of these repositories. Make sure that unique
        packages present in corresponding repos.

        @Feature: Packages

        @Assert: Content search functionality works as intended and expected
        packages are present inside of repositories
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.assertIsNotNone(self.package.search('tiger'))
            self.assertIsNotNone(self.package.search('Lizard'))
            self.package.select_repo(self.yum_repo.name)
            self.assertIsNotNone(self.package.search('tiger'))
            self.assertIsNone(self.package.search('Lizard'))
            self.package.select_repo(self.yum_repo2.name)
            self.assertIsNotNone(self.package.search('Lizard'))
            self.assertIsNone(self.package.search('tiger'))

    @tier2
    def test_positive_check_package_details(self):
        """Create product with yum repository assigned to it. Search for
        package inside of it and then open it. Check all the details about that
        package

        @Feature: Packages

        @Assert: Package is present inside of repository and has all expected
        values in details section
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.package.select_repo(self.yum_repo.name)
            self.package.check_package_details(
                'gorilla',
                [
                    ['Description', 'A dummy package of gorilla'],
                    ['Summary', 'A dummy package of gorilla'],
                    ['Group', 'Internet/Applications'],
                    ['License', 'GPLv2'],
                    ['Url', 'http://tstrachota.fedorapeople.org'],
                    ['Size', '2.39 KB (2452 Bytes)'],
                    ['Filename', 'gorilla-0.62-1.noarch.rpm'],
                    ['Checksum', 'ffd511be32adbf91fa0b3f54f23cd1c02add50578344'
                                 'ff8de44cea4f4ab5aa37'],
                    ['Checksum Type', 'sha256'],
                    ['Source RPM', 'gorilla-0.62-1.src.rpm'],
                    ['Build Host', 'smqe-ws15'],
                    ['Build Time', '1331831364'],
                ]
            )
