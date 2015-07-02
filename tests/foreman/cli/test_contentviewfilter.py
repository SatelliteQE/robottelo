# -*- encoding: utf-8 -*-
"""Test class for Content View Filters"""

from ddt import ddt
from fauxfactory import gen_choice, gen_string
from random import randint
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    CLIFactoryError,
    make_content_view,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.repository import Repository
from robottelo.common.constants import DOCKER_REGISTRY_HUB
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestContentViewFilter(CLITestCase):
    """Content View Filter CLI tests"""

    @classmethod
    def setUpClass(cls):
        """Init single organization, product and repository for all tests"""
        super(TestContentViewFilter, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({u'organization-id': cls.org['id']})
        cls.repo = make_repository({u'product-id': cls.product['id']})
        Repository.synchronize({u'id': cls.repo['id']})

    def setUp(self):
        """Init content view with repo per each test"""
        super(TestContentViewFilter, self).setUp()
        self.cvf_name = gen_string('utf8')
        try:
            self.content_view = make_content_view({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': self.repo['id'],
        })
        self.assertEqual(result.return_code, 0)

    @data(
        gen_string('alphanumeric', randint(1, 255)),
        gen_string('alpha', randint(1, 255)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 255)),
        gen_string('numeric', randint(1, 255)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    )
    def test_create_cvf_with_different_names(self, name):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different value types as a name and random
        filter content type as a parameter for this filter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        filter_content_type = gen_choice(['rpm', 'package_group', 'erratum'])
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': filter_content_type,
            'name': name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['name'], name)
        self.assertEqual(result.stdout['type'], filter_content_type)

    @data('rpm', 'package_group', 'erratum')
    def test_create_cvf_with_content_types(self, filter_content_type):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different content types as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': filter_content_type,
            'name': self.cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['type'], filter_content_type)

    @data('true', 'false')
    def test_create_cvf_with_inclusions(self, inclusion):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different inclusions as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': inclusion,
            'name': self.cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['inclusion'], inclusion)

    @skip_if_bug_open('bugzilla', 1236532)
    def test_create_cvf_with_description(self):
        """Test: Create new content view filter with description and assign it
        to existing content view.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        description

        """
        description = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'description': description,
            'type': 'package_group',
            'name': self.cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['description'], description)

    def test_create_cvf_by_cv_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization id for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        result = ContentView.filter_create({
            'content-view': self.content_view['name'],
            'organization-id': self.org['id'],
            'type': 'package_group',
            'inclusion': 'true',
            'name': self.cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)

    def test_create_cvf_by_org_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization name for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        result = ContentView.filter_create({
            'content-view': self.content_view['name'],
            'organization': self.org['name'],
            'type': 'erratum',
            'inclusion': 'false',
            'name': self.cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)

    def test_create_cvf_by_org_label(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization label for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        result = ContentView.filter_create({
            'content-view': self.content_view['name'],
            'organization-label': self.org['label'],
            'type': 'erratum',
            'inclusion': 'true',
            'name': self.cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)

    def test_create_cvf_with_repo_by_id(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository id
        for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': self.cvf_name,
            'repository-ids': self.repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

    @skip_if_bug_open('bugzilla', 1228890)
    def test_create_cvf_with_repo_by_name(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository
        name for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'false',
            'name': self.cvf_name,
            'repositories': self.repo['name'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

    def test_create_cvf_with_original_packages(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Enable 'original
        packages' option for that filter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': self.cvf_name,
            'repository-ids': self.repo['id'],
            'original-packages': 'true',
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

    def test_create_cvf_with_multiple_repo_with_docker(self):
        """Test: Create new docker repository and add to content view that has
        yum repo already assigned to it. Create new content view filter and
        assign it to mentioned content view. Use these repositories id for
        proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has both
        repositories affected (yum and docker)

        """
        try:
            docker_repository = make_repository({
                u'content-type': u'docker',
                u'docker-upstream-name': u'busybox',
                u'product-id': self.product['id'],
                u'url': DOCKER_REGISTRY_HUB,
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': docker_repository['id'],
        })
        self.assertEqual(result.return_code, 0)

        repos = '{0},{1}'.format(self.repo['id'], docker_repository['id'])

        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': self.cvf_name,
            'repository-ids': repos,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['repositories']), 2)
        for i in range(2):
            self.assertIn(result.stdout['repositories'][i]['id'], repos)

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

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_location_with_same_names_negative(self):
        """@Test: Try to create content view filter using same name twice

        @Feature: Content View Filter

        @Assert: Second content view filter is not created

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': self.cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': self.cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_cvf_without_type_negative(self):
        """@Test: Try to create content view filter without providing required
        parameter 'type'

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_cvf_without_cv_negative(self):
        """@Test: Try to create content view filter without providing content
        view information which should be used as basis for filter

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        result = ContentView.filter_create({
            'type': 'rpm',
            'name': self.cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_cvf_with_repo_by_id_negative(self):
        """@Test: Try to create content view filter using incorrect repository

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': self.cvf_name,
            'repository-ids': gen_string('numeric', 6),
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)
