# -*- encoding: utf-8 -*-
# pylint: disable=too-many-public-methods
"""Test class for Content View Filters"""

from fauxfactory import gen_choice, gen_string
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    CLIFactoryError,
    make_content_view,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.repository import Repository
from robottelo.constants import DOCKER_REGISTRY_HUB
from robottelo.decorators import skip_if_bug_open
from robottelo.helpers import invalid_values_list, valid_data_list
from robottelo.test import CLITestCase


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
        cls.content_view = make_content_view({
            u'organization-id': cls.org['id'],
        })
        ContentView.add_repository({
            u'id': cls.content_view['id'],
            u'repository-id': cls.repo['id'],
        })

    def test_create_cvf_different_names(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different value types as a name and random
        filter content type as a parameter for this filter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        for name in valid_data_list():
            with self.subTest(name):
                filter_content_type = gen_choice([
                    'rpm',
                    'package_group',
                    'erratum',
                ])
                result = ContentView.filter_create({
                    'content-view-id': self.content_view['id'],
                    'type': filter_content_type,
                    'name': name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(len(result.stderr), 0)

                result = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(result.stdout['name'], name)
                self.assertEqual(result.stdout['type'], filter_content_type)

    def test_create_cvf_content_types(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different content types as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        for filter_content_type in ('rpm', 'package_group', 'erratum'):
            with self.subTest(filter_content_type):
                cvf_name = gen_string('utf8')
                result = ContentView.filter_create({
                    'content-view-id': self.content_view['id'],
                    'type': filter_content_type,
                    'name': cvf_name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(len(result.stderr), 0)

                result = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': cvf_name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(result.stdout['type'], filter_content_type)

    def test_create_cvf_inclusions(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different inclusions as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        for inclusion in ('true', 'false'):
            with self.subTest(inclusion):
                cvf_name = gen_string('utf8')
                result = ContentView.filter_create({
                    'content-view-id': self.content_view['id'],
                    'type': 'rpm',
                    'inclusion': inclusion,
                    'name': cvf_name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(len(result.stderr), 0)

                result = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': cvf_name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(result.stdout['inclusion'], inclusion)

    @skip_if_bug_open('bugzilla', 1236532)
    def test_create_cvf_description(self):
        """Test: Create new content view filter with description and assign it
        to existing content view.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        description

        """
        description = gen_string('utf8')
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'description': description,
            'type': 'package_group',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['description'], description)

    def test_create_cvf_by_cv_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization id for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view': self.content_view['name'],
            'organization-id': self.org['id'],
            'type': 'package_group',
            'inclusion': 'true',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

    def test_create_cvf_by_org_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization name for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view': self.content_view['name'],
            'organization': self.org['name'],
            'type': 'erratum',
            'inclusion': 'false',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

    def test_create_cvf_by_org_label(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization label for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view': self.content_view['name'],
            'organization-label': self.org['label'],
            'type': 'erratum',
            'inclusion': 'true',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

    def test_create_cvf_repo_by_id(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository id
        for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': cvf_name,
            'repository-ids': self.repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

    @skip_if_bug_open('bugzilla', 1228890)
    def test_create_cvf_repo_by_name(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository
        name for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'false',
            'name': cvf_name,
            'repositories': self.repo['name'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

    def test_create_cvf_original_pkgs(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Enable 'original
        packages' option for that filter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': cvf_name,
            'repository-ids': self.repo['id'],
            'original-packages': 'true',
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

    def test_create_cvf_repos_docker(self):
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

        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': cvf_name,
            'repository-ids': repos,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['repositories']), 2)
        for i in range(2):
            self.assertIn(result.stdout['repositories'][i]['id'], repos)

    def test_create_cvf_names_negative(self):
        """@Test: Try to create content view filter using invalid names only

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        for name in invalid_values_list():
            with self.subTest(name):
                result = ContentView.filter_create({
                    'content-view-id': self.content_view['id'],
                    'type': 'rpm',
                    'name': name,
                })
                self.assertNotEqual(result.return_code, 0)
                self.assertNotEqual(len(result.stderr), 0)

    def test_create_same_name_negative(self):
        """@Test: Try to create content view filter using same name twice

        @Feature: Content View Filter

        @Assert: Second content view filter is not created

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_no_type_negative(self):
        """@Test: Try to create content view filter without providing required
        parameter 'type'

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_without_cv_negative(self):
        """@Test: Try to create content view filter without providing content
        view information which should be used as basis for filter

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_create_repo_by_id_negative(self):
        """@Test: Try to create content view filter using incorrect repository

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
            'repository-ids': gen_string('numeric', 6),
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_update_cvf_different_names(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to update that filter using different value
        types as a name

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has proper and
        expected name

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
        })
        for new_name in valid_data_list():
            with self.subTest(new_name):
                result = ContentView.filter_update({
                    'content-view-id': self.content_view['id'],
                    'name': cvf_name,
                    'new-name': new_name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(len(result.stderr), 0)

                result = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': new_name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(result.stdout['name'], new_name)
                cvf_name = new_name  # updating cvf name for next iteration

    def test_update_cvf_repo(self):
        """Test: Create new content view filter and apply it to existing
        content view that has repository assigned to it. Try to update that
        filter and change affected repository on another one.

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has new
        repository affected

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
            'repository-ids': self.repo['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['repositories']), 1)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

        new_repo = make_repository({u'product-id': self.product['id']})
        result = ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['repositories']), 1)
        self.assertNotEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(
            result.stdout['repositories'][0]['name'], new_repo['name'])

    def test_update_cvf_repo_type(self):
        """Test: Create new content view filter and apply it to existing
        content view that has repository assigned to it. Try to update that
        filter and change affected repository on another one. That new
        repository should have another type from initial one (e.g. yum->docker)

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has new
        repository affected

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
            'repository-ids': self.repo['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['repositories']), 1)
        self.assertEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])

        try:
            docker_repo = make_repository({
                u'content-type': u'docker',
                u'docker-upstream-name': u'busybox',
                u'product-id': self.product['id'],
                u'url': DOCKER_REGISTRY_HUB,
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ContentView.add_repository({
            u'id': self.content_view['id'],
            u'repository-id': docker_repo['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': docker_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['repositories']), 1)
        self.assertNotEqual(
            result.stdout['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(
            result.stdout['repositories'][0]['name'], docker_repo['name'])

    def test_update_cvf_inclusion(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to update that filter and assign opposite
        inclusion value for it

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has correct and
        expected value for inclusion parameter

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['inclusion'], 'true')

        result = ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'inclusion': 'false',
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['inclusion'], 'false')

    def test_update_diffnames_negative(self):
        """@Test: Try to update content view filter using invalid names only

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                result = ContentView.filter_update({
                    'content-view-id': self.content_view['id'],
                    'name': cvf_name,
                    'new-name': new_name,
                })
                self.assertNotEqual(result.return_code, 0)
                self.assertNotEqual(len(result.stderr), 0)

                result = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': new_name,
                })
                self.assertNotEqual(result.return_code, 0)

    def test_update_samename_negative(self):
        """@Test: Try to update content view filter using name of already
        existing entity

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

        new_name = gen_string('alpha', 100)
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': new_name,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': new_name,
            'new-name': cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_update_inclusion_negative(self):
        """Test: Try to update content view filter and assign incorrect
        inclusion value for it

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'inclusion': 'wrong_value',
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['inclusion'], 'true')

    def test_update_wrongrepo_negative(self):
        """Test: Try to update content view filter using non-existing
        repository ID

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
            'repository-ids': self.repo['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': gen_string('numeric', 6),
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_update_new_repo_negative(self):
        """Test: Try to update filter and assign repository which does not
        belong to filter content view

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
            'repository-ids': self.repo['id'],
        })
        self.assertEqual(result.return_code, 0)

        new_repo = make_repository({u'product-id': self.product['id']})

        result = ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': new_repo['id'],
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_delete_cvf_different_names(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using different value
        types as a name

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        for name in valid_data_list():
            with self.subTest(name):
                result = ContentView.filter_create({
                    'content-view-id': self.content_view['id'],
                    'type': 'rpm',
                    'name': name,
                })
                self.assertEqual(result.return_code, 0)

                result = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': name,
                })
                self.assertEqual(result.return_code, 0)

                result = ContentView.filter_delete({
                    u'content-view-id': self.content_view['id'],
                    u'name': name,
                })
                self.assertEqual(result.return_code, 0)
                self.assertEqual(len(result.stderr), 0)

                result = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': name,
                })
                self.assertNotEqual(result.return_code, 0)

    def test_delete_cvf_by_id(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using its id as a
        parameter

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_delete({
            u'id': result.stdout['filter-id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)

    def test_delete_cvf_org(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using organization and
        content view names where that filter was applied

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        cvf_name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'type': 'rpm',
            'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.filter_delete({
            u'content-view': self.content_view['name'],
            u'organization': self.org['name'],
            u'name': cvf_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertNotEqual(result.return_code, 0)

    def test_delete_cvf_name_negative(self):
        """Test: Try to delete non-existent filter using generated name

        @Feature: Content View Filter

        @Assert: System returned error

        """
        result = ContentView.filter_delete({
            u'content-view-id': self.content_view['id'],
            u'name': u'invalid_cv_filter',
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)
