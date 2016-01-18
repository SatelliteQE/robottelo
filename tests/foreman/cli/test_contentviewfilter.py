# -*- encoding: utf-8 -*-
"""Test class for Content View Filters"""

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
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.test import CLITestCase


class ContentViewFilterTestCase(CLITestCase):
    """Content View Filter CLI tests"""

    @classmethod
    def setUpClass(cls):
        """Init single organization, product and repository for all tests"""
        super(ContentViewFilterTestCase, cls).setUpClass()
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

    @tier1
    def test_positive_create_with_name_by_cv_id(self):
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

    @tier1
    def test_positive_create_with_content_type_by_cv_id(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different content types as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        for filter_content_type in ('rpm', 'package_group', 'erratum'):
            with self.subTest(filter_content_type):
                cvf_name = gen_string('utf8')
                ContentView.filter_create({
                    'content-view-id': self.content_view['id'],
                    'name': cvf_name,
                    'type': filter_content_type,
                })
                cvf = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': cvf_name,
                })
                self.assertEqual(cvf['type'], filter_content_type)

    @tier1
    def test_positivec_create_with_inclusion_by_cv_id(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Use different inclusions as a parameter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has correct and
        expected parameters

        """
        for inclusion in ('true', 'false'):
            with self.subTest(inclusion):
                cvf_name = gen_string('utf8')
                ContentView.filter_create({
                    'content-view-id': self.content_view['id'],
                    'inclusion': inclusion,
                    'name': cvf_name,
                    'type': 'rpm',
                })
                cvf = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': cvf_name,
                })
                self.assertEqual(cvf['inclusion'], inclusion)

    @tier1
    @skip_if_bug_open('bugzilla', 1236532)
    def test_positive_create_with_description_by_cv_id(self):
        """Test: Create new content view filter with description and assign it
        to existing content view.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        description

        """
        description = gen_string('utf8')
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'description': description,
            'name': cvf_name,
            'type': 'package_group',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(cvf['description'], description)

    @tier1
    def test_positive_create_by_cv_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization id for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view': self.content_view['name'],
            'inclusion': 'true',
            'name': cvf_name,
            'organization-id': self.org['id'],
            'type': 'package_group',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })

    @tier1
    def test_positive_create_by_org_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization name for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view': self.content_view['name'],
            'inclusion': 'false',
            'name': cvf_name,
            'organization': self.org['name'],
            'type': 'erratum',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })

    @tier1
    def test_positive_create_by_org_label(self):
        """Test: Create new content view filter and assign it to existing
        content view by name. Use organization label for reference

        @Feature: Content View Filter

        @Assert: Content view filter created successfully

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view': self.content_view['name'],
            'inclusion': 'true',
            'name': cvf_name,
            'organization-label': self.org['label'],
            'type': 'erratum',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })

    @tier1
    def test_positive_create_with_repo_by_id(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository id
        for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    @tier1
    @skip_if_bug_open('bugzilla', 1228890)
    def test_positive_create_with_repo_by_name(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Use that repository
        name for proper filter assignment.

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'false',
            'name': cvf_name,
            'repositories': self.repo['name'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    @tier1
    def test_positive_create_with_original_pkgs(self):
        """Test: Create new content view filter and assign it to existing
        content view that has repository assigned to it. Enable 'original
        packages' option for that filter

        @Feature: Content View Filter

        @Assert: Content view filter created successfully and has proper
        repository affected

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': cvf_name,
            'original-packages': 'true',
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    @tier1
    def test_positive_create_with_repos_yum_and_docker(self):
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
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': cvf_name,
            'repository-ids': repos,
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 2)
        for repo in cvf['repositories']:
            self.assertIn(repo['id'], repos)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create content view filter using invalid names only

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.filter_create({
                        'content-view-id': self.content_view['id'],
                        'name': name,
                        'type': 'rpm',
                    })

    @tier1
    def test_negative_create_with_same_name(self):
        """Try to create content view filter using same name twice

        @Feature: Content View Filter

        @Assert: Second content view filter is not created

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'type': 'rpm',
            })

    @tier1
    def test_negative_create_without_type(self):
        """Try to create content view filter without providing required
        parameter 'type'

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'content-view-id': self.content_view['id'],
                'name': gen_string('utf8'),
            })

    @tier1
    def test_negative_create_without_cv(self):
        """Try to create content view filter without providing content
        view information which should be used as basis for filter

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'name': gen_string('utf8'),
                'type': 'rpm',
            })

    @tier1
    def test_negative_create_with_invalid_repo_id(self):
        """Try to create content view filter using incorrect repository

        @Feature: Content View Filter

        @Assert: Content view filter is not created

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_create({
                'content-view-id': self.content_view['id'],
                'name': gen_string('utf8'),
                'repository-ids': gen_string('numeric', 6),
                'type': 'rpm',
            })

    @tier2
    def test_positive_update_name(self):
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
            'name': cvf_name,
            'type': 'rpm',
        })
        for new_name in valid_data_list():
            with self.subTest(new_name):
                ContentView.filter_update({
                    'content-view-id': self.content_view['id'],
                    'name': cvf_name,
                    'new-name': new_name,
                })
                cvf = ContentView.filter_info({
                    u'content-view-id': self.content_view['id'],
                    u'name': new_name,
                })
                self.assertEqual(cvf['name'], new_name)
                cvf_name = new_name  # updating cvf name for next iteration

    @tier2
    def test_positive_update_repo_with_same_type(self):
        """Test: Create new content view filter and apply it to existing
        content view that has repository assigned to it. Try to update that
        filter and change affected repository on another one.

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has new
        repository affected

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
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
            'name': cvf_name,
            'repository-ids': new_repo['id'],
        })

        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertNotEqual(cvf['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(cvf['repositories'][0]['name'], new_repo['name'])

    @tier2
    def test_positive_update_repo_with_different_type(self):
        """Test: Create new content view filter and apply it to existing
        content view that has repository assigned to it. Try to update that
        filter and change affected repository on another one. That new
        repository should have another type from initial one (e.g. yum->docker)

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has new
        repository affected

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
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
            'name': cvf_name,
            'repository-ids': docker_repo['id'],
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertNotEqual(cvf['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(cvf['repositories'][0]['name'], docker_repo['name'])

    @tier2
    def test_positive_update_inclusion(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to update that filter and assign opposite
        inclusion value for it

        @Feature: Content View Filter

        @Assert: Content view filter updated successfully and has correct and
        expected value for inclusion parameter

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': cvf_name,
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(cvf['inclusion'], 'true')
        ContentView.filter_update({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'inclusion': 'false',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(cvf['inclusion'], 'false')

    @tier1
    def test_negative_update_with_name(self):
        """Try to update content view filter using invalid names only

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'type': 'rpm',
        })
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.filter_update({
                        'content-view-id': self.content_view['id'],
                        'name': cvf_name,
                        'new-name': new_name,
                    })
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.filter_info({
                        u'content-view-id': self.content_view['id'],
                        u'name': new_name,
                    })

    @tier1
    def test_negative_update_with_same_name(self):
        """Try to update content view filter using name of already
        existing entity

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'type': 'rpm',
        })
        new_name = gen_string('alpha', 100)
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': new_name,
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'name': new_name,
                'new-name': cvf_name,
            })

    @tier1
    def test_negative_update_inclusion(self):
        """Test: Try to update content view filter and assign incorrect
        inclusion value for it

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'inclusion': 'true',
            'name': cvf_name,
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'inclusion': 'wrong_value',
                'name': cvf_name,
            })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        self.assertEqual(cvf['inclusion'], 'true')

    @tier1
    def test_negative_update_with_non_existent_repo_id(self):
        """Test: Try to update content view filter using non-existing
        repository ID

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': gen_string('numeric', 6),
            })

    @tier1
    def test_negative_update_with_invalid_repo_id(self):
        """Test: Try to update filter and assign repository which does not
        belong to filter content view

        @Feature: Content View Filter

        @Assert: Content view filter is not updated

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'repository-ids': self.repo['id'],
            'type': 'rpm',
        })
        new_repo = make_repository({u'product-id': self.product['id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_update({
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': new_repo['id'],
            })

    @tier1
    def test_positive_delete_by_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using different value
        types as a name

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        for name in valid_data_list():
            with self.subTest(name):
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

    @tier1
    def test_positive_delete_by_id(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using its id as a
        parameter

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'type': 'rpm',
        })
        cvf = ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        ContentView.filter_delete({'id': cvf['filter-id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_info({
                u'content-view-id': self.content_view['id'],
                u'name': cvf_name,
            })

    @tier1
    def test_positive_delete_by_org_name(self):
        """Test: Create new content view filter and assign it to existing
        content view by id. Try to delete that filter using organization and
        content view names where that filter was applied

        @Feature: Content View Filter

        @Assert: Content view filter deleted successfully

        """
        cvf_name = gen_string('utf8')
        ContentView.filter_create({
            'content-view-id': self.content_view['id'],
            'name': cvf_name,
            'type': 'rpm',
        })
        ContentView.filter_info({
            u'content-view-id': self.content_view['id'],
            u'name': cvf_name,
        })
        ContentView.filter_delete({
            u'content-view': self.content_view['name'],
            u'name': cvf_name,
            u'organization': self.org['name'],
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_info({
                u'content-view-id': self.content_view['id'],
                u'name': cvf_name,
            })

    @tier1
    def test_negative_delete_by_name(self):
        """Test: Try to delete non-existent filter using generated name

        @Feature: Content View Filter

        @Assert: System returned error

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter_delete({
                u'content-view-id': self.content_view['id'],
                u'name': u'invalid_cv_filter',
            })
