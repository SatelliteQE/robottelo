"""Unit tests for the ``content_view_filters`` paths.

A full API reference for content views can be found here:
http://www.katello.org/docs/api/apidoc/content_view_filters.html

"""
from fauxfactory import gen_integer, gen_string
from nailgun import client, entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.constants import DOCKER_REGISTRY_HUB
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase
from six.moves import http_client


class ContentViewFilterTestCase(APITestCase):
    """Tests for content view filters."""

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

    @tier2
    @run_only_on('sat')
    def test_negative_get_with_no_args(self):
        """@Test: Issue an HTTP GET to the base content view filters path.

        @Feature: ContentViewFilter

        @Assert: An HTTP 400 or 422 response is received if a GET request is
        issued with no arguments specified.

        This test targets bugzilla bug #1102120.
        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=settings.server.get_credentials(),
            verify=False,
        )
        self.assertIn(
            response.status_code,
            (http_client.BAD_REQUEST, http_client.UNPROCESSABLE_ENTITY)
        )

    @tier2
    @run_only_on('sat')
    def test_negative_get_with_bad_args(self):
        """@Test: Issue an HTTP GET to the base content view filters path.

        @Feature: ContentViewFilter

        @Assert: An HTTP 400 or 422 response is received if a GET request is
        issued with bad arguments specified.

        This test targets bugzilla bug #1102120.
        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=settings.server.get_credentials(),
            verify=False,
            data={'foo': 'bar'},
        )
        self.assertIn(
            response.status_code,
            (http_client.BAD_REQUEST, http_client.UNPROCESSABLE_ENTITY)
        )

    @tier2
    @run_only_on('sat')
    def test_positive_create_erratum_with_name(self):
        """Test: Create new erratum content filter using different inputs as
        a name

        @Assert: Content view filter created successfully and has correct name
        and type

        @Feature: Content View Filter - Create
        """
        for name in valid_data_list():
            with self.subTest(name):
                cvf = entities.ErratumContentViewFilter(
                    content_view=self.content_view,
                    name=name,
                ).create()
                self.assertEqual(cvf.name, name)
                self.assertEqual(cvf.type, 'erratum')

    @tier2
    @run_only_on('sat')
    def test_positive_create_pkg_group_with_name(self):
        """Test: Create new package group content filter using different inputs
        as a name

        @Assert: Content view filter created successfully and has correct name
        and type

        @Feature: Content View Filter - Create
        """
        for name in valid_data_list():
            with self.subTest(name):
                cvf = entities.PackageGroupContentViewFilter(
                    content_view=self.content_view,
                    name=name,
                ).create()
                self.assertEqual(cvf.name, name)
                self.assertEqual(cvf.type, 'package_group')

    @tier2
    @run_only_on('sat')
    def test_positive_create_rpm_with_name(self):
        """Test: Create new RPM content filter using different inputs as
        a name

        @Assert: Content view filter created successfully and has correct name
        and type

        @Feature: Content View Filter - Create
        """
        for name in valid_data_list():
            with self.subTest(name):
                cvf = entities.RPMContentViewFilter(
                    content_view=self.content_view,
                    name=name,
                ).create()
                self.assertEqual(cvf.name, name)
                self.assertEqual(cvf.type, 'rpm')

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_inclusion(self):
        """Test: Create new content view filter with different inclusion values

        @Assert: Content view filter created successfully and has correct
        inclusion value

        @Feature: Content View Filter - Create
        """
        for inclusion in (True, False):
            with self.subTest(inclusion):
                cvf = entities.RPMContentViewFilter(
                    content_view=self.content_view,
                    inclusion=inclusion,
                ).create()
                self.assertEqual(cvf.inclusion, inclusion)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_description(self):
        """Test: Create new content filter using different inputs as a
        description

        @Assert: Content view filter created successfully and has correct
        description

        @Feature: Content View Filter - Create
        """
        for description in valid_data_list():
            with self.subTest(description):
                cvf = entities.RPMContentViewFilter(
                    content_view=self.content_view,
                    description=description,
                ).create()
                self.assertEqual(cvf.description, description)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_repo(self):
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

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_original_packages(self):
        """Test: Create new content view filter with different 'original
        packages' option values

        @Assert: Content view filter created successfully and has 'original
        packages' value

        @Feature: Content View Filter - Create
        """
        for original_packages in (True, False):
            with self.subTest(original_packages):
                cvf = entities.RPMContentViewFilter(
                    content_view=self.content_view,
                    inclusion=True,
                    repository=[self.repo],
                    original_packages=original_packages,
                ).create()
                self.assertEqual(cvf.original_packages, original_packages)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_docker_repos(self):
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

    @tier2
    @run_only_on('sat')
    def test_negative_create_with_name(self):
        """@Test: Try to create content view filter using invalid names only

        @Assert: Content view filter was not created

        @Feature: Content View Filter - Create
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.RPMContentViewFilter(
                        content_view=self.content_view,
                        name=name,
                    ).create()

    @tier2
    @run_only_on('sat')
    def test_negative_create_with_same_name(self):
        """@Test: Try to create content view filter using same name twice

        @Assert: Second content view filter was not created

        @Feature: Content View Filter - Create
        """
        kwargs = {
            'content_view': self.content_view,
            'name': gen_string('alpha'),
        }
        entities.RPMContentViewFilter(**kwargs).create()
        with self.assertRaises(HTTPError):
            entities.RPMContentViewFilter(**kwargs).create()

    @tier2
    @run_only_on('sat')
    def test_negative_create_without_cv(self):
        """@Test: Try to create content view filter without providing content
        view

        @Assert: Content view filter is not created

        @Feature: Content View Filter - Create
        """
        with self.assertRaises(HTTPError):
            entities.RPMContentViewFilter(content_view=None).create()

    @tier2
    @run_only_on('sat')
    def test_negative_create_with_repo_by_id(self):
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

    @tier2
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
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

    @tier2
    @run_only_on('sat')
    def test_positive_update_name(self):
        """@Test: Update content view filter with new name

        @Assert: Content view filter updated successfully and name was changed

        @Feature: Content View Filter - Update
        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        for name in valid_data_list():
            with self.subTest(name):
                cvf.name = name
                self.assertEqual(cvf.update(['name']).name, name)

    @tier2
    @run_only_on('sat')
    def test_positive_update_description(self):
        """@Test: Update content view filter with new description

        @Assert: Content view filter updated successfully and description was
        changed

        @Feature: Content View Filter - Update
        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        for desc in valid_data_list():
            with self.subTest(desc):
                cvf.description = desc
                self.assertEqual(cvf.update(['description']).description, desc)

    @tier2
    @run_only_on('sat')
    def test_positive_update_inclusion(self):
        """Test: Update content view filter with new inclusion value

        @Assert: Content view filter updated successfully and inclusion value
        was changed

        @Feature: Content View Filter - Update
        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        for inclusion in (True, False):
            with self.subTest(inclusion):
                cvf.inclusion = inclusion
                cvf = cvf.update(['inclusion'])
                self.assertEqual(cvf.inclusion, inclusion)

    @tier2
    @run_only_on('sat')
    def test_positive_update_repo(self):
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

    @tier2
    @run_only_on('sat')
    def test_positive_update_repos(self):
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

    @tier2
    @run_only_on('sat')
    def test_positive_update_original_packages(self):
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
        ).create()
        for original_packages in (True, False):
            with self.subTest(original_packages):
                cvf.original_packages = original_packages
                cvf = cvf.update(['original_packages'])
                self.assertEqual(cvf.original_packages, original_packages)

    @tier2
    @run_only_on('sat')
    def test_positive_update_repo_with_docker(self):
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

    @tier2
    @run_only_on('sat')
    def test_negative_update_name(self):
        """@Test: Try to update content view filter using invalid names only

        @Assert: Content view filter was not updated

        @Feature: Content View Filter - Update
        """
        cvf = entities.RPMContentViewFilter(
            content_view=self.content_view,
        ).create()
        for name in invalid_names_list():
            with self.subTest(name):
                cvf.name = name
                with self.assertRaises(HTTPError):
                    cvf.update(['name'])

    @tier2
    @run_only_on('sat')
    def test_negative_update_same_name(self):
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

    @tier2
    @run_only_on('sat')
    def test_negative_update_cv_by_id(self):
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

    @tier2
    @run_only_on('sat')
    def test_negative_update_repo_by_id(self):
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

    @tier2
    @run_only_on('sat')
    def test_negative_update_repo(self):
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


class ContentViewFilterSearchTestCase(APITestCase):
    """Tests that search through content view filters."""

    @classmethod
    def setUpClass(cls):
        """Create a content view as ``cls.content_view``."""
        super(ContentViewFilterSearchTestCase, cls).setUpClass()
        cls.content_view = entities.ContentView().create()

    @tier1
    @skip_if_bug_open('bugzilla', 1242534)
    def test_positive_search_erratum(self):
        """@Test: Search for an erratum content view filter's rules.

        @Assert: The search completes with no errors.

        @Feature: Content View Filter
        """
        cv_filter = entities.ErratumContentViewFilter(
            content_view=self.content_view
        ).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()

    @tier1
    def test_positive_search_package_group(self):
        """@Test: Search for an package group content view filter's rules.

        @Assert: The search completes with no errors.

        @Feature: Content View Filter
        """
        cv_filter = entities.PackageGroupContentViewFilter(
            content_view=self.content_view
        ).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()

    @tier1
    def test_positive_search_rpm(self):
        """@Test: Search for an rpm content view filter's rules.

        @Assert: The search completes with no errors.

        @Feature: Content View Filter
        """
        cv_filter = entities.RPMContentViewFilter(
            content_view=self.content_view
        ).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()
