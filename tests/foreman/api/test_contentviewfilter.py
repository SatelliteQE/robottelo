"""Unit tests for the ``content_view_filters`` paths.

A full API reference for content views can be found here:
http://www.katello.org/docs/api/apidoc/content_view_filters.html

"""
import httplib
from ddt import ddt
from fauxfactory import gen_integer, gen_string
from nailgun import client, entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.common.constants import DOCKER_REGISTRY_HUB
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo.test import APITestCase


@run_only_on('sat')
@ddt
class ContentViewFilterTestCase(APITestCase):
    """Tests for content view filters."""

    def _positive_data():
        """Random data for positive creation"""

        return (
            gen_string('alphanumeric', randint(1, 255)),
            gen_string('alpha', randint(1, 255)),
            gen_string('cjk', randint(1, 85)),
            gen_string('latin1', randint(1, 255)),
            gen_string('numeric', randint(1, 255)),
            gen_string('utf8', randint(1, 85)),
            gen_string('html', randint(1, 85)),
        )

    @classmethod
    def setUpClass(cls):
        """Init single organization, product and repository for all tests"""
        super(ContentViewFilterTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()
        cls.repo = entities.Repository(product=cls.product).create()
        cls.repo.sync()

    def setUp(self):
        """Init content view with repo per each test"""
        super(ContentViewFilterTestCase, self).setUp()
        self.content_view = entities.ContentView(
            organization=self.org,
        ).create()
        self.content_view.repository = [self.repo]
        self.content_view.update(['repository'])

    def test_get_with_no_args(self):
        """@Test: Issue an HTTP GET to the base content view filters path.

        @Feature: ContentViewFilter

        @Assert: An HTTP 400 or 422 response is received if a GET request is
        issued with no arguments specified.

        This test targets bugzilla bug #1102120.

        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertIn(
            response.status_code,
            (httplib.BAD_REQUEST, httplib.UNPROCESSABLE_ENTITY)
        )

    def test_get_with_bad_args(self):
        """@Test: Issue an HTTP GET to the base content view filters path.

        @Feature: ContentViewFilter

        @Assert: An HTTP 400 or 422 response is received if a GET request is
        issued with bad arguments specified.

        This test targets bugzilla bug #1102120.

        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=get_server_credentials(),
            verify=False,
            data={'foo': 'bar'},
        )
        self.assertIn(
            response.status_code,
            (httplib.BAD_REQUEST, httplib.UNPROCESSABLE_ENTITY)
        )

    @data(*_positive_data())
    def test_create_erratum_cvf_with_different_names(self, name):
        """Test: Create new erratum content filter using different inputs as
        a name

        @Assert: Content view filter created successfully and has correct name
        and type

        @Feature: Content View Filter - Create

        """
        cvf = entities.ErratumContentViewFilter(
            content_view=self.content_view,
            name=name,
        ).create()
        self.assertEqual(cvf.name, name)
        self.assertEqual(cvf.type, 'erratum')

    @data(*_positive_data())
    def test_create_pck_group_cvf_with_different_names(self, name):
        """Test: Create new package group content filter using different inputs
        as a name

        @Assert: Content view filter created successfully and has correct name
        and type

        @Feature: Content View Filter - Create

        """
        cvf = entities.PackageGroupContentViewFilter(
            content_view=self.content_view,
            name=name,
        ).create()
        self.assertEqual(cvf.name, name)
        self.assertEqual(cvf.type, 'package_group')

    @data(*_positive_data())
    def test_create_rpm_cvf_with_different_names(self, name):
        """Test: Create new RPM content filter using different inputs as
        a name

        @Assert: Content view filter created successfully and has correct name
        and type

        @Feature: Content View Filter - Create

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            name=name,
        ).create()
        self.assertEqual(cvf.name, name)
        self.assertEqual(cvf.type, 'rpm')

    @data(True, False)
    def test_create_cvf_with_inclusion(self, inclusion):
        """Test: Create new content view filter with different inclusion values

        @Assert: Content view filter created successfully and has correct
        inclusion value

        @Feature: Content View Filter - Create

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=inclusion,
        ).create()
        self.assertEqual(cvf.inclusion, inclusion)

    @data(*_positive_data())
    def test_create_cvf_with_description(self, description):
        """Test: Create new content filter using different inputs as a
        description

        @Assert: Content view filter created successfully and has correct
        description

        @Feature: Content View Filter - Create

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            description=description,
        ).create()
        self.assertEqual(cvf.description, description)

    def test_create_cvf_with_repo(self):
        """Test: Create new content filter with repository assigned

        @Assert: Content view filter created successfully and has repository
        assigned

        @Feature: Content View Filter - Create

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo],
        ).create()
        self.assertEqual(cvf.repository[0].id, self.repo.id)

    @data(True, False)
    def test_create_cvf_with_original_packages(self, original_packages):
        """Test: Create new content view filter with different 'original
        packages' option values

        @Assert: Content view filter created successfully and has 'original
        packages' value

        @Feature: Content View Filter - Create

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo],
            original_packages=original_packages,
        ).create()
        self.assertEqual(cvf.original_packages, original_packages)

    def test_create_cvf_with_multiple_repos_with_docker(self):
        """Test: Create new docker repository and add to content view that has
        yum repo already assigned to it. Create new content view filter and
        assign it to the content view.

        @Assert: Content view filter created successfully and has both
        repositories assigned (yum and docker)

        @Feature: Content View Filter - Create

        """
        docker_repository = entities.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=self.product.id,
            url=DOCKER_REGISTRY_HUB,
        ).create()
        self.content_view.repository = [self.repo, docker_repository]
        self.content_view.update(['repository'])
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo, docker_repository],
        ).create()
        self.assertEqual(len(cvf.repository), 2)
        for repo in cvf.repository:
            self.assertIn(repo.id, [self.repo.id, docker_repository.id])

    @data(
        '',
        ' ',
        gen_string('alphanumeric', 300),
        gen_string('alpha', 300),
        gen_string('cjk', 300),
        gen_string('latin1', 300),
        gen_string('numeric', 300),
        gen_string('utf8', 300),
        gen_string('html', 300),
    )
    def test_create_cvf_with_different_names_negative(self, name):
        """@Test: Try to create content view filter using invalid names only

        @Assert: Content view filter was not created

        @Feature: Content View Filter - Create

        """
        with self.assertRaises(HTTPError):
            entities.RPMContentViewFilter(
                content_view=self.content_view,
                name=name,
            ).create()

    def test_create_cvf_with_same_names_negative(self):
        """@Test: Try to create content view filter using same name twice

        @Assert: Second content view filter was not created

        @Feature: Content View Filter - Create

        """
        name = gen_string('alpha', 8)
        entities.RPMContentViewFilter(
            content_view=self.content_view,
            name=name,
        ).create()
        with self.assertRaises(HTTPError):
            entities.RPMContentViewFilter(
                content_view=self.content_view,
                name=name,
            ).create()

    def test_create_cvf_without_cv_negative(self):
        """@Test: Try to create content view filter without providing content
        view

        @Assert: Content view filter is not created

        @Feature: Content View Filter - Create

        """
        with self.assertRaises(HTTPError):
            entities.RPMContentViewFilter(
                content_view=None,
            ).create()

    def test_create_cvf_with_repo_by_id_negative(self):
        """@Test: Try to create content view filter using incorrect repository
        id

        @Assert: Content view filter is not created

        @Feature: Content View Filter - Create

        """
        with self.assertRaises(HTTPError):
            entities.RPMContentViewFilter(
                content_view=self.content_view,
                repository=[gen_integer(10000, 99999)],
            ).create()

    def test_delete_cvf_by_id(self):
        """@Test: Delete content view filter

        @Assert: Content view filter was deleted

        @Feature: Content View Filter - Delete

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        cvf.delete()
        with self.assertRaises(HTTPError):
            cvf.read()

    @data(*_positive_data())
    def test_update_cvf_with_new_name(self, new_name):
        """@Test: Update content view filter with new name

        @Assert: Content view filter updated successfully and name was changed

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        cvf.name = new_name
        self.assertEqual(cvf.update(['name']).name, new_name)

    @data(*_positive_data())
    def test_update_cvf_with_new_description(self, new_description):
        """@Test: Update content view filter with new description

        @Assert: Content view filter updated successfully and description was
        changed

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            description=gen_string('alpha'),
        ).create()
        cvf.description = new_description
        self.assertEqual(
            cvf.update(['description']).description,
            new_description
        )

    @data(True, False)
    def test_update_cvf_with_new_inclusion(self, new_inclusion):
        """Test: Update content view filter with new inclusion value

        @Assert: Content view filter updated successfully and inclusion value
        was changed

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=not new_inclusion,
        ).create()
        cvf.inclusion = new_inclusion
        self.assertEqual(cvf.update(['inclusion']).inclusion, new_inclusion)

    def test_update_cvf_with_new_repo(self):
        """Test: Update content view filter with new repository

        @Assert: Content view filter updated successfully and has new
        repository assigned

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo],
        ).create()
        new_repo = entities.Repository(product=self.product).create()
        new_repo.sync()
        self.content_view.repository = [new_repo]
        self.content_view.update(['repository'])
        cvf.repository = [new_repo]
        cvf = cvf.update(['repository'])
        self.assertEqual(len(cvf.repository), 1)
        self.assertEqual(cvf.repository[0].id, new_repo.id)

    def test_update_cvf_with_multiple_repos(self):
        """Test: Update content view filter with multiple repositories

        @Assert: Content view filter updated successfully and has new
        repositories assigned

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo],
        ).create()
        repos = [
            entities.Repository(product=self.product).create()
            for _
            in range(randint(3, 5))
        ]
        for repo in repos:
            repo.sync()
        self.content_view.repository = repos
        self.content_view.update(['repository'])
        cvf.repository = repos
        cvf = cvf.update(['repository'])
        self.assertEqual(
            set([repo.id for repo in cvf.repository]),
            set([repo.id for repo in repos])
        )

    @data(True, False)
    def test_update_cvf_original_packages(self, new_original_packages):
        """Test: Update content view filter with new 'original packages' option
        value

        @Assert: Content view filter updated successfully and 'original
        packages' value was changed

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo],
            original_packages=not new_original_packages,
        ).create()
        cvf.original_packages = new_original_packages
        self.assertEqual(
            cvf.update(['original_packages']).original_packages,
            new_original_packages
        )

    def test_update_cvf_with_repo_with_docker(self):
        """Test: Update existing content view filter which has yum repository
        assigned with new docker repository

        @Assert: Content view filter was updated successfully and has both
        repositories assigned (yum and docker)

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo],
        ).create()
        docker_repository = entities.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=self.product.id,
            url=DOCKER_REGISTRY_HUB,
        ).create()
        self.content_view.repository = [self.repo, docker_repository]
        self.content_view = self.content_view.update(['repository'])
        cvf.repository = [self.repo, docker_repository]
        cvf = cvf.update(['repository'])
        self.assertEqual(len(cvf.repository), 2)
        for repo in cvf.repository:
            self.assertIn(repo.id, [self.repo.id, docker_repository.id])

    @data(
        '',
        ' ',
        gen_string('alphanumeric', 300),
        gen_string('alpha', 300),
        gen_string('cjk', 300),
        gen_string('latin1', 300),
        gen_string('numeric', 300),
        gen_string('utf8', 300),
        gen_string('html', 300),
    )
    def test_update_cvf_with_different_names_negative(self, new_name):
        """@Test: Try to update content view filter using invalid names only

        @Assert: Content view filter was not updated

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        cvf.name = new_name
        with self.assertRaises(HTTPError):
            cvf.update(['name'])

    def test_update_cvf_with_already_used_name_negative(self):
        """@Test: Try to update content view filter's name to already used one

        @Assert: Content view filter was not updated

        @Feature: Content View Filter - Update

        """
        name = gen_string('alpha', 8)
        entities.RPMContentViewFilter(
            content_view=self.content_view,
            name=name,
        ).create()
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        cvf.name = name
        with self.assertRaises(HTTPError):
            cvf.update(['name'])

    def test_update_cvf_with_cv_by_id_negative(self):
        """@Test: Try to update content view filter using incorrect content
        view ID

        @Assert: Content view filter was not updated

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        cvf.content_view.id = gen_integer(10000, 99999)
        with self.assertRaises(HTTPError):
            cvf.update(['content_view'])

    def test_update_cvf_with_repo_by_id_negative(self):
        """@Test: Try to update content view filter using incorrect repository
        ID

        @Assert: Content view filter was not updated

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            repository=[self.repo],
        ).create()
        cvf.repository[0].id = gen_integer(10000, 99999)
        with self.assertRaises(HTTPError):
            cvf.update(['repository'])

    def test_update_cvf_with_new_repo_negative(self):
        """Test: Try to update content view filter with new repository which
        doesn't belong to filter's content view

        @Assert: Content view filter was not updated

        @Feature: Content View Filter - Update

        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
            inclusion=True,
            repository=[self.repo],
        ).create()
        new_repo = entities.Repository(product=self.product).create()
        new_repo.sync()
        cvf.repository = [new_repo]
        with self.assertRaises(HTTPError):
            cvf.update(['repository'])


class SearchTestCase(APITestCase):
    """Tests that search through content view filters."""

    @classmethod
    def setUpClass(cls):
        """Create a content view as ``cls.content_view``."""
        cls.content_view = entities.ContentView().create()

    @skip_if_bug_open('bugzilla', 1242534)
    def test_search_erratum(self):
        """@Test: Search for an erratum content view filter's rules.

        @Assert: The search completes with no errors.

        @Feature: Content View Filter

        """
        cv_filter = entities.ErratumContentViewFilter(
            content_view=self.content_view
        ).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()

    def test_search_package_group(self):
        """@Test: Search for an package group content view filter's rules.

        @Assert: The search completes with no errors.

        @Feature: Content View Filter

        """
        cv_filter = entities.PackageGroupContentViewFilter(
            content_view=self.content_view
        ).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()

    def test_search_rpm(self):
        """@Test: Search for an rpm content view filter's rules.

        @Assert: The search completes with no errors.

        @Feature: Content View Filter

        """
        cv_filter = entities.RPMContentViewFilter(
            content_view=self.content_view
        ).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()
