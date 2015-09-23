# -*- encoding: utf-8 -*-
"""Test class for Content View Filters"""

from ddt import ddt
from fauxfactory import gen_choice, gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    make_content_view,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.repository import Repository
from robottelo.constants import DOCKER_REGISTRY_HUB
from robottelo.decorators import data, skip_if_bug_open
from robottelo.helpers import invalid_values_list, valid_data_list
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
        self.content_view = make_content_view({
            u'organization-id': self.org['id'],
        })
        ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': self.repo['id'],
        })

    @data(*valid_data_list())
    def test_create_cvf_with_different_names(self, name):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different value types as a name and random
        filter content type as a parameter for this filter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        filter_content_type = gen_choice(['rpm', 'package_group', 'erratum'])
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': name,
            'type': filter_content_type,
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': name,
        })
        self.assertEqual(cvf['name'], name)
        self.assertEqual(cvf['type'], filter_content_type)

    @data('rpm', 'package_group', 'erratum')
    def test_create_cvf_with_content_types(self, filter_content_type):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different content types as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'type': filter_content_type,
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['type'], filter_content_type)

    @data('true', 'false')
    def test_create_cvf_with_inclusions(self, inclusion):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different inclusions as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': inclusion,
            'name': self.cvf_name,
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['inclusion'], inclusion)

    @skip_if_bug_open('bugzilla', 1236532)
    def test_create_cvf_with_description(self):
        """Test: Create new content view filter with description and assign it
        to existing content view.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        description

        """
        description = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'description': description,
            'name': self.cvf_name,
            'type': 'package_group',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['description'], description)

    def test_create_cvf_by_cv_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization id for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        ContentView.filter_create({
            'content-view': self.content_view['name'],
            'inclusion': 'true',
            'name': self.cvf_name,
            'organization-id': self.org['id'],
            'type': 'package_group',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })

    def test_create_cvf_by_org_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization name for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        ContentView.filter_create({
            'content-view': self.content_view['name'],
            'inclusion': 'false',
            'name': self.cvf_name,
            'organization': self.org['name'],
            'type': 'erratum',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })

    def test_create_cvf_by_org_label(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization label for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        ContentView.filter_create({
            'content-view': self.content_view['name'],
            'inclusion': 'true',
            'name': self.cvf_name,
            'organization-label': self.org['label'],
            'type': 'erratum',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })

    def test_create_cvf_with_repo_by_id(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository id
        for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': self.cvf_name,
            'repository-ids': self.repo['id'],
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    @skip_if_bug_open('bugzilla', 1228890)
    def test_create_cvf_with_repo_by_name(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository
        name for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'false',
            'name': self.cvf_name,
            'repositories': self.repo['name'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    def test_create_cvf_with_original_packages(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Enable 'original
        packages' option for that filter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': self.cvf_name,
            'original-packages': 'true',
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    def test_create_cvf_with_multiple_repo_with_docker(self):
        """Test: Create new docker repository and add to content view that has
        yum repo already assigned to it. Create new content view filter and
        assign it to mentioned content view. Use these repositories id for
        proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has both
        repositories affected (yum and docker)

        """
        docker_repository = make_repository({
            u'content-type': u'docker',
            u'docker-upstream-name': u'busybox',
            u'product-id': self.product['id'],
            u'url': DOCKER_REGISTRY_HUB,
        })
        ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': docker_repository['id'],
        })
        repos = [self.repo['id'], docker_repository['id']]
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': self.cvf_name,
            'repository-ids': repos,
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 2)
        for repo in cvf['repositories']:
            self.assertIn(repo['id'], repos)

    @data(*invalid_values_list())
    def test_create_cvf_with_different_names_negative(self, name):
        """@Test: Try to create content view filter using invalid names only

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'content-view-id': self.content_view['id'],
                'name': name,
                'type': 'rpm',
            })

    def test_create_location_with_same_names_negative(self):
        """@Test: Try to create content view filter using same name twice

        @Feature: Content View Filter

        @Assert: Second content view filter is not created

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'content-view-id': self.content_view['id'],
                'name': self.cvf_name,
                'type': 'rpm',
            })

    def test_create_cvf_without_type_negative(self):
        """@Test: Try to create content view filter without providing required
        parameter 'type'

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'content-view-id': self.content_view['id'],
                'name': self.cvf_name,
            })

    def test_create_cvf_without_cv_negative(self):
        """@Test: Try to create content view filter without providing content
        view information which should be used as basis for filter

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'name': self.cvf_name,
                'type': 'rpm',
            })

    def test_create_cvf_with_repo_by_id_negative(self):
        """@Test: Try to create content view filter using incorrect repository

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'content-view-id': self.content_view['id'],
                'name': self.cvf_name,
                'repository-ids': gen_string('numeric', 6),
                'type': 'rpm',
            })

    @data(*valid_data_list())
    def test_update_cvf_with_different_names(self, new_name):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to update that filter using different value
        types as a name

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has proper and
        expected name

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertNotEqual(cvf['name'], new_name)
        ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'new-name': new_name,
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': new_name,
        })
        self.assertEqual(cvf['name'], new_name)

    def test_update_cvf_with_repo(self):
        """Test: Create new content view filter and apply it to existing
        content view that has repository assigned to it. Try to update that
        filter and change affected repository on another one.

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has new
        repository affected

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

        new_repo = make_repository({u'product-id': self.product['id']})
        ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': new_repo['id'],
        })

        ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'repository-ids': new_repo['id'],
        })

        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertNotEqual(cvf['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(cvf['repositories'][0]['name'], new_repo['name'])

    def test_update_cvf_with_repo_type(self):
        """Test: Create new content view filter and apply it to existing
        content view that has repository assigned to it. Try to update that
        filter and change affected repository on another one. That new
        repository should have another type from initial one (e.g. yum->docker)

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has new
        repository affected

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])
        docker_repo = make_repository({
            u'content-type': u'docker',
            u'docker-upstream-name': u'busybox',
            u'product-id': self.product['id'],
            u'url': DOCKER_REGISTRY_HUB,
        })
        ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': docker_repo['id'],
        })
        ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'repository-ids': docker_repo['id'],
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertNotEqual(cvf['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(cvf['repositories'][0]['name'], docker_repo['name'])

    def test_update_cvf_with_inclusion(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to update that filter and assign opposite
        inclusion value for it

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has correct and
        expected value for inclusion parameter

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'type': 'rpm',
            'name': self.cvf_name,
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['inclusion'], 'true')
        ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'inclusion': 'false',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['inclusion'], 'false')

    @data(*invalid_values_list())
    def test_update_cvf_with_different_names_negative(self, new_name):
        """@Test: Try to update content view filter using invalid names only

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'name': self.cvf_name,
                'new-name': new_name,
            })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_info({
                u'content-view-id': self.content_view['id'],
                u'name': new_name,
            })

    def test_update_cvf_with_same_name_negative(self):
        """@Test: Try to update content view filter using name of already
        existing entity

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'type': 'rpm',
        })
        new_name = gen_string('alpha', 100)
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': new_name,
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'name': new_name,
                'new-name': self.cvf_name,
            })

    def test_update_cvf_with_inclusion_negative(self):
        """Test: Try to update content view filter and assign incorrect
        inclusion value for it

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': self.cvf_name,
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'inclusion': 'wrong_value',
                'name': self.cvf_name,
            })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        self.assertEqual(cvf['inclusion'], 'true')

    def test_update_cvf_with_non_exist_repo_negative(self):
        """Test: Try to update content view filter using non-existing
        repository ID

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'name': self.cvf_name,
                'repository-ids': gen_string('numeric', 6),
            })

    def test_update_cvf_with_new_repo_negative(self):
        """Test: Try to update filter and assign repository which does not
        belong to filter content view

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        new_repo = make_repository({u'product-id': self.product['id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'name': self.cvf_name,
                'repository-ids': new_repo['id'],
            })

    @data(*valid_data_list())
    def test_delete_cvf_with_different_names(self, name):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using different value
        types as a name

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': name,
            'type': 'rpm',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': name,
        })
        ContentView.filter_delete({
            u'content-view-id': self.content_view['id'],
            u'name': name,
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_info({
                u'content-view-id': self.content_view['id'],
                u'name': name,
            })

    def test_delete_cvf_by_id(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using its id as a
        parameter

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        ContentView.filter_delete({'id': cvf['filter-id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_info({
                u'content-view-id': self.content_view['id'],
                u'name': self.cvf_name,
            })

    def test_delete_cvf_with_org(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using organization and
        content view names where that filter was applied

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': self.cvf_name,
            'type': 'rpm',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': self.cvf_name,
        })
        ContentView.filter_delete({
            u'content-view': self.content_view['name'],
            u'name': self.cvf_name,
            u'organization': self.org['name'],
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_info({
                u'content-view-id': self.content_view['id'],
                u'name': self.cvf_name,
            })

    def test_delete_cvf_with_name_negative(self):
        """Test: Try to delete non-existent filter using generated name

        @Feature: Content View Filter

        @Assert: System returned error

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_delete({
                u'content-view-id': self.content_view['id'],
                u'name': u'invalid_cv_filter',
            })
