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
from robottelo.common.decorators import data, run_only_on
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
        self.content_view.set_repository_ids(repo_ids=[self.repo.id])

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
        self.content_view.set_repository_ids(
            repo_ids=[self.repo.id, docker_repository.id]
        )
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
