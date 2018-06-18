# -*- encoding: utf-8 -*-
"""Test class for Packages UI

:Requirement: Packages

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid, upload_manifest
from robottelo.constants import (
    FAKE_0_YUM_REPO,
    FAKE_3_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
    RPM_TO_UPLOAD,
)
from robottelo.decorators import (
    skip_if_bug_open,
    skip_if_not_set,
    tier2,
    upgrade
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators
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

        :id: e182a89f-74e4-4b29-8152-1ea3bd014fd3

        :expectedresults: Content search functionality works as intended and
            expected packages are present inside of repository

        :CaseLevel: Integration
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.package.select_repo(self.yum_repo.name)
            self.assertIsNotNone(self.package.search('bear'))
            self.assertIsNotNone(self.package.search('cheetah'))

    @skip_if_bug_open('bugzilla', 1514457)
    @tier2
    def test_positive_search_in_multiple_repos(self):
        """Create product with two different yum repositories assigned to it.
        Search for packages inside of these repositories. Make sure that unique
        packages present in corresponding repos.

        :id: 249ac04b-8e31-42e9-ac37-08608bf867a1

        :expectedresults: Content search functionality works as intended and
            expected packages are present inside of repositories

        :CaseLevel: Integration
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.assertIsNotNone(self.package.search('tiger'))
            self.assertIsNotNone(self.package.search('Lizard'))
            # First repository
            self.assertIsNotNone(
                self.package.search_in_repo('tiger', self.yum_repo.name))
            self.assertIsNotNone(
                self.package.search_in_repo(
                    'Lizard', self.yum_repo.name, expecting_results=False))
            # Second repository
            self.assertIsNotNone(
                self.package.search_in_repo('Lizard', self.yum_repo2.name))
            self.assertIsNotNone(
                self.package.search_in_repo(
                    'tiger', self.yum_repo2.name, expecting_results=False))

    @tier2
    def test_positive_check_package_details(self):
        """Create product with yum repository assigned to it. Search for
        package inside of it and then open it. Check all the details about that
        package

        :id: 57625386-4a9e-4bea-b2d5-d97326043150

        :expectedresults: Package is present inside of repository and has all
            expected values in details section

        :CaseLevel: Integration
        """
        with Session(self) as session:
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

    @tier2
    @skip_if_bug_open('bugzilla', 1394390)
    def test_positive_check_custom_package_details(self):
        """Upload custom rpm package to repository. Search for package
        and then open it. Check that package details are available

        :id: 679622a7-003e-4887-8622-b95b9468da7d

        :expectedresults: Package is present inside of repository and it
            possible to view its details

        :CaseLevel: Integration

        :BZ: 1387766
        """
        with open(get_data_file(RPM_TO_UPLOAD), 'rb') as handle:
            self.yum_repo.upload_content(files={'content': handle})
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.package.select_repo(self.yum_repo.name)
            self.package.search_and_click(RPM_TO_UPLOAD.split('-')[0])
            self.assertIsNone(self.activationkey.wait_until_element(
                common_locators['alert.error']))
            self.package.check_package_details(
                RPM_TO_UPLOAD.split('-')[0],
                [['Filename', RPM_TO_UPLOAD]]
            )


class RHPackagesTestCase(UITestCase):
    """Implement tests for packages via UI"""

    @classmethod
    @skip_if_not_set('fake_manifest')
    def setUpClass(cls):
        super(RHPackagesTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(cls.organization.id, manifest.content)
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=cls.organization.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        entities.Repository(id=repo_id).sync()

    @tier2
    def test_positive_search_in_rh_repo(self):
        """Synchronize one of RH repos (for example Satellite Tools). Search
        for packages inside of it

        :id: 8eae9cc1-6902-49ed-a474-ef175fe5ab5f

        :expectedresults: Content search functionality works as intended and
            expected packages are present inside of repository

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.package.select_repo(REPOS['rhst7']['name'])
            self.assertIsNotNone(self.package.search('facter'))
            self.assertIsNotNone(self.package.search('katello-agent'))

    @tier2
    @upgrade
    def test_positive_check_file_list(self):
        """Synchronize one of RH repos (for example Satellite Tools). Search
        for packages inside of it. Open one of the package and check list of
        file inside of it

        :id: 01c9dccb-2b2b-4b90-b277-047e772e56e7

        :expectedresults: Content search functionality works as intended and
            package contains expected list of files

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.package.select_repo(REPOS['rhst7']['name'])
            self.package.check_file_list(
                'katello-agent',
                [
                    '/usr/lib/gofer/plugins/katelloplugin.py',
                    '/usr/lib/yum-plugins',
                    '/usr/lib/yum-plugins/package_upload.py',
                    '/usr/sbin/katello-package-upload',
                ]
            )
