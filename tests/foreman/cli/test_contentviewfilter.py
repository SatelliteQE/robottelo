# -*- encoding: utf-8 -*-
"""Test class for Content View Filters

:Requirement: Contentviewfilter

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_choice
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.defaults import Defaults
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_content_view_filter
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product_wait
from robottelo.cli.factory import make_repository
from robottelo.cli.repository import Repository
from robottelo.constants import DOCKER_REGISTRY_HUB
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class ContentViewFilterTestCase(CLITestCase):
    """Content View Filter CLI tests"""

    @classmethod
    def setUpClass(cls):
        """Init single organization, product and repository for all tests"""
        super(ContentViewFilterTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product_wait({'organization-id': cls.org['id']})
        cls.content_view = make_content_view({'organization-id': cls.org['id']})
        for _ in range(2):
            cls.repo = make_repository({'product-id': cls.product['id']})
            Repository.synchronize({'id': cls.repo['id']})
            ContentView.add_repository(
                {'id': cls.content_view['id'], 'repository-id': cls.repo['id']}
            )

    @tier1
    def test_positive_create_with_name_by_cv_id(self):
        """Create new content view filter and assign it to existing content
        view by id. Use different value types as a name and random filter
        content type as a parameter for this filter

        :id: 2cfdf72e-179d-4bba-8aab-288594cac836

        :expectedresults: Content view filter created successfully and has
            correct and expected parameters

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                filter_content_type = gen_choice(['rpm', 'package_group', 'erratum', 'modulemd'])
                ContentView.filter.create(
                    {
                        'content-view-id': self.content_view['id'],
                        'name': name,
                        'organization-id': self.org['id'],
                        'type': filter_content_type,
                    }
                )
                cvf = ContentView.filter.info(
                    {'content-view-id': self.content_view['id'], 'name': name}
                )
                self.assertEqual(cvf['name'], name)
                self.assertEqual(cvf['type'], filter_content_type)

    @tier1
    def test_positive_create_with_content_type_by_cv_id(self):
        """Create new content view filter and assign it to existing content
        view by id. Use different content types as a parameter

        :id: b3e5a58b-eddc-4ceb-ae34-6c0ab5664784

        :expectedresults: Content view filter created successfully and has
            correct and expected parameters

        :CaseImportance: Critical
        """
        for filter_content_type in ('rpm', 'package_group', 'erratum', 'modulemd'):
            with self.subTest(filter_content_type):
                cvf_name = gen_string('utf8')
                ContentView.filter.create(
                    {
                        'content-view-id': self.content_view['id'],
                        'name': cvf_name,
                        'organization-id': self.org['id'],
                        'type': filter_content_type,
                    }
                )
                cvf = ContentView.filter.info(
                    {'content-view-id': self.content_view['id'], 'name': cvf_name}
                )
                self.assertEqual(cvf['type'], filter_content_type)

    @tier1
    def test_positive_create_with_inclusion_by_cv_id(self):
        """Create new content view filter and assign it to existing content
        view by id. Use different inclusions as a parameter

        :id: 4a18ee71-3f0d-4e8b-909e-999d722ebc0a

        :expectedresults: Content view filter created successfully and has
            correct and expected parameters

        :CaseImportance: Critical
        """
        for inclusion in ('true', 'false'):
            with self.subTest(inclusion):
                cvf_name = gen_string('utf8')
                ContentView.filter.create(
                    {
                        'content-view-id': self.content_view['id'],
                        'inclusion': inclusion,
                        'name': cvf_name,
                        'organization-id': self.org['id'],
                        'type': 'rpm',
                    }
                )
                cvf = ContentView.filter.info(
                    {'content-view-id': self.content_view['id'], 'name': cvf_name}
                )
                self.assertEqual(cvf['inclusion'], inclusion)

    @tier1
    def test_positive_create_with_description_by_cv_id(self):
        """Create new content view filter with description and assign it to
        existing content view.

        :id: e283a42a-122b-467c-8d00-d6487f657692

        :expectedresults: Content view filter created successfully and has
            proper description

        :CaseImportance: Low
        """
        description = gen_string('utf8')
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'description': description,
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'package_group',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(cvf['description'], description)

    @run_in_one_thread
    @tier1
    def test_positive_create_with_default_taxonomies(self):
        """Create new content view filter and assign it to existing content
        view by name. Use default organization and location to find necessary
        content view

        :id: 5fd6db3f-5723-44a9-a138-864693680a2f

        :expectedresults: Content view filter created successfully and has
            correct and expected name

        :BZ: 1369609

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        location = make_location()
        Defaults.add({'param-name': 'organization_id', 'param-value': self.org['id']})
        Defaults.add({'param-name': 'location_id', 'param-value': location['id']})
        try:
            ContentView.filter.create(
                {
                    'content-view': self.content_view['name'],
                    'name': name,
                    'type': 'erratum',
                    'inclusion': 'true',
                }
            )
            cvf = ContentView.filter.info(
                {'content-view': self.content_view['name'], 'name': name}
            )
            self.assertEqual(cvf['name'], name)
        finally:
            Defaults.delete({'param-name': 'organization_id'})
            Defaults.delete({'param-name': 'location_id'})

    @tier1
    def test_positive_list_by_name_and_org(self):
        """Create new content view filter and try to list it by its name and
        organization it belongs

        :id: e685892d-9dc3-48f2-8a09-8f861dceaf4e

        :expectedresults: Content view filter created and listed successfully

        :BZ: 1378018

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'package_group',
            }
        )
        cv_filters = ContentView.filter.list(
            {'content-view': self.content_view['name'], 'organization': self.org['name']}
        )
        self.assertGreaterEqual(len(cv_filters), 1)
        self.assertIn(cvf_name, [cvf['name'] for cvf in cv_filters])

    @tier1
    def test_positive_create_by_cv_name(self):
        """Create new content view filter and assign it to existing content
        view by name. Use organization id for reference

        :id: 0fb2fbc2-0d81-451e-9b20-9e996e14c977

        :expectedresults: Content view filter created successfully

        :BZ: 1356906

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view': self.content_view['name'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'package_group',
            }
        )
        ContentView.filter.info({'content-view-id': self.content_view['id'], 'name': cvf_name})

    @tier1
    def test_positive_create_by_org_name(self):
        """Create new content view filter and assign it to existing content
        view by name. Use organization name for reference

        :id: 295847fe-51e4-483d-af2f-b972c8b5064c

        :expectedresults: Content view filter created successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view': self.content_view['name'],
                'inclusion': 'false',
                'name': cvf_name,
                'organization': self.org['name'],
                'type': 'erratum',
            }
        )
        ContentView.filter.info({'content-view-id': self.content_view['id'], 'name': cvf_name})

    @tier1
    def test_positive_create_by_org_label(self):
        """Create new content view filter and assign it to existing content
        view by name. Use organization label for reference

        :id: f233e223-c08c-4ce1-b87a-9e055fdd7b83

        :expectedresults: Content view filter created successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view': self.content_view['name'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-label': self.org['label'],
                'type': 'erratum',
            }
        )
        ContentView.filter.info({'content-view-id': self.content_view['id'], 'name': cvf_name})

    @tier1
    def test_positive_create_with_repo_by_id(self):
        """Create new content view filter and assign it to existing content
        view that has repository assigned to it. Use that repository id for
        proper filter assignment.

        :id: 6d517e09-6a6a-4eed-91fe-9459610c0062

        :expectedresults: Content view filter created successfully and has
            proper repository affected

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'repository-ids': self.repo['id'],
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        # Check that only one, specified above, repository is displayed
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    @tier1
    def test_positive_create_with_repo_by_name(self):
        """Create new content view filter and assign it to existing content
        view that has repository assigned to it. Use that repository name for
        proper filter assignment.

        :id: 1b38c7c1-c8cd-49af-adcf-9e05a9201767

        :expectedresults: Content view filter created successfully and has
            proper repository affected

        :BZ: 1228890

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'inclusion': 'false',
                'name': cvf_name,
                'product': self.product['name'],
                'repositories': self.repo['name'],
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        # Check that only one, specified above, repository is displayed
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    @tier1
    def test_positive_create_with_original_pkgs(self):
        """Create new content view filter and assign it to existing content
        view that has repository assigned to it. Enable 'original packages'
        option for that filter

        :id: 5491233a-9361-435f-87ad-dca97e6d5d2f

        :expectedresults: Content view filter created successfully and has
            proper repository affected

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'original-packages': 'true',
                'repository-ids': self.repo['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

    @tier2
    def test_positive_create_with_repos_yum_and_docker(self):
        """Create new docker repository and add to content view that has yum
        repo already assigned to it. Create new content view filter and assign
        it to mentioned content view. Use these repositories id for proper
        filter assignment.

        :id: 8419a5fa-0530-42a7-964c-7c513443c5c8

        :expectedresults: Content view filter created successfully and has both
            repositories affected (yum and docker)
        """
        docker_repository = make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': 'busybox',
                'product-id': self.product['id'],
                'url': DOCKER_REGISTRY_HUB,
            }
        )
        ContentView.add_repository(
            {'id': self.content_view['id'], 'repository-id': docker_repository['id']}
        )
        repos = [self.repo['id'], docker_repository['id']]
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'repository-ids': repos,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(len(cvf['repositories']), 2)
        for repo in cvf['repositories']:
            self.assertIn(repo['id'], repos)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create content view filter using invalid names only

        :id: f3497a23-6e34-4fee-9964-f95762fc737c

        :expectedresults: Content view filter is not created

        :CaseImportance: Low
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.filter.create(
                        {
                            'content-view-id': self.content_view['id'],
                            'name': name,
                            'organization-id': self.org['id'],
                            'type': 'rpm',
                        }
                    )

    @tier1
    def test_negative_create_with_same_name(self):
        """Try to create content view filter using same name twice

        :id: 7e7444f4-e2b5-406d-a210-49b4008c88d9

        :expectedresults: Second content view filter is not created

        :CaseImportance: Low
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.create(
                {
                    'content-view-id': self.content_view['id'],
                    'name': cvf_name,
                    'organization-id': self.org['id'],
                    'type': 'rpm',
                }
            )

    @tier1
    def test_negative_create_without_type(self):
        """Try to create content view filter without providing required
        parameter 'type'

        :id: 8af65427-d0f0-4661-b062-93e054079f44

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.create(
                {
                    'content-view-id': self.content_view['id'],
                    'name': gen_string('utf8'),
                    'organization-id': self.org['id'],
                }
            )

    @tier1
    def test_negative_create_without_cv(self):
        """Try to create content view filter without providing content
        view information which should be used as basis for filter

        :id: 4ed3828e-52e8-457c-a2af-bb03b00467e8

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.create({'name': gen_string('utf8'), 'type': 'rpm'})

    @tier1
    def test_negative_create_with_invalid_repo_id(self):
        """Try to create content view filter using incorrect repository

        :id: 21fdbeca-ad0a-4e29-93dc-f850b5639f4f

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.create(
                {
                    'content-view-id': self.content_view['id'],
                    'name': gen_string('utf8'),
                    'repository-ids': gen_string('numeric', 6),
                    'organization-id': self.org['id'],
                    'type': 'rpm',
                }
            )

    @tier2
    def test_positive_update_name(self):
        """Create new content view filter and assign it to existing content
        view by id. Try to update that filter using different value types as a
        name

        :id: 70ba8916-5898-4911-9de8-21d2e0fb3df9

        :expectedresults: Content view filter updated successfully and has
            proper and expected name

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        cvf = make_content_view_filter(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        for new_name in valid_data_list():
            with self.subTest(new_name):
                ContentView.filter.update(
                    {
                        'content-view-id': self.content_view['id'],
                        'id': cvf['filter-id'],
                        'new-name': new_name,
                    }
                )
                cvf = ContentView.filter.info(
                    {'content-view-id': self.content_view['id'], 'name': new_name}
                )
                self.assertEqual(cvf['name'], new_name)
                cvf_name = new_name  # updating cvf name for next iteration

    @tier2
    def test_positive_update_repo_with_same_type(self):
        """Create new content view filter and apply it to existing content view
        that has repository assigned to it. Try to update that filter and
        change affected repository on another one.

        :id: b2f444fd-e65e-41ba-9941-620d3cdb260f

        :expectedresults: Content view filter updated successfully and has new
            repository affected

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': self.repo['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])

        new_repo = make_repository({'product-id': self.product['id']})
        ContentView.add_repository(
            {'id': self.content_view['id'], 'repository-id': new_repo['id']}
        )

        ContentView.filter.update(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': new_repo['id'],
            }
        )

        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertNotEqual(cvf['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(cvf['repositories'][0]['name'], new_repo['name'])

    @tier2
    @upgrade
    def test_positive_update_repo_with_different_type(self):
        """Create new content view filter and apply it to existing content view
        that has repository assigned to it. Try to update that filter and
        change affected repository on another one. That new repository should
        have another type from initial one (e.g. yum->docker)

        :id: cf3daa0d-e918-4330-95ad-f88933579829

        :expectedresults: Content view filter updated successfully and has new
            repository affected

        :CaseLevel: Integration
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': self.repo['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertEqual(cvf['repositories'][0]['name'], self.repo['name'])
        docker_repo = make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': 'busybox',
                'product-id': self.product['id'],
                'url': DOCKER_REGISTRY_HUB,
            }
        )
        ContentView.add_repository(
            {'id': self.content_view['id'], 'repository-id': docker_repo['id']}
        )
        ContentView.filter.update(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': docker_repo['id'],
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(len(cvf['repositories']), 1)
        self.assertNotEqual(cvf['repositories'][0]['name'], self.repo['name'])
        self.assertEqual(cvf['repositories'][0]['name'], docker_repo['name'])

    @tier2
    def test_positive_update_inclusion(self):
        """Create new content view filter and assign it to existing content
        view by id. Try to update that filter and assign opposite inclusion
        value for it

        :id: 76b3c66d-8200-4cf0-8cd0-b57de4ff12b0

        :expectedresults: Content view filter updated successfully and has
            correct and expected value for inclusion parameter

        :CaseLevel: Integration
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(cvf['inclusion'], 'true')
        ContentView.filter.update(
            {'content-view-id': self.content_view['id'], 'name': cvf_name, 'inclusion': 'false'}
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(cvf['inclusion'], 'false')

    @tier1
    def test_negative_update_with_name(self):
        """Try to update content view filter using invalid names only

        :id: 6c40e452-f786-4e28-9f03-b1935b55b33a

        :expectedresults: Content view filter is not updated

        :BZ: 1328943

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.filter.update(
                        {
                            'content-view-id': self.content_view['id'],
                            'name': cvf_name,
                            'new-name': new_name,
                        }
                    )
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.filter.info(
                        {'content-view-id': self.content_view['id'], 'name': new_name}
                    )

    @tier1
    def test_negative_update_with_same_name(self):
        """Try to update content view filter using name of already
        existing entity

        :id: 9c1b1c75-af57-4218-9e2d-e69d74f50e04

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        new_name = gen_string('alpha', 100)
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': new_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': self.content_view['id'],
                    'name': new_name,
                    'new-name': cvf_name,
                }
            )

    @tier1
    def test_negative_update_inclusion(self):
        """Try to update content view filter and assign incorrect inclusion
        value for it

        :id: 760400a8-49a5-4a31-924c-c232cb22ddad

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': self.content_view['id'],
                    'inclusion': 'wrong_value',
                    'name': cvf_name,
                }
            )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        self.assertEqual(cvf['inclusion'], 'true')

    @tier1
    def test_negative_update_with_non_existent_repo_id(self):
        """Try to update content view filter using non-existing repository ID

        :id: 457af8c2-fb32-4164-9e19-98676f4ea063

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': self.repo['id'],
                'type': 'rpm',
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': self.content_view['id'],
                    'name': cvf_name,
                    'repository-ids': gen_string('numeric', 6),
                }
            )

    @tier1
    def test_negative_update_with_invalid_repo_id(self):
        """Try to update filter and assign repository which does not belong to
        filter content view

        :id: aa550619-c436-4184-bb29-2becadf69e5b

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'repository-ids': self.repo['id'],
                'type': 'rpm',
            }
        )
        new_repo = make_repository({'product-id': self.product['id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': self.content_view['id'],
                    'name': cvf_name,
                    'repository-ids': new_repo['id'],
                }
            )

    @tier1
    def test_positive_delete_by_name(self):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using different value types as a
        name

        :id: a01baf17-9c3c-4923-bfe0-865a4cbc4223

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                ContentView.filter.create(
                    {
                        'content-view-id': self.content_view['id'],
                        'name': name,
                        'organization-id': self.org['id'],
                        'type': 'rpm',
                    }
                )
                ContentView.filter.info({'content-view-id': self.content_view['id'], 'name': name})
                ContentView.filter.delete(
                    {'content-view-id': self.content_view['id'], 'name': name}
                )
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.filter.info(
                        {'content-view-id': self.content_view['id'], 'name': name}
                    )

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using its id as a parameter

        :id: e3865a11-1ba0-481a-bfe0-f9235901946d

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        cvf = ContentView.filter.info(
            {'content-view-id': self.content_view['id'], 'name': cvf_name}
        )
        ContentView.filter.delete({'id': cvf['filter-id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.info({'content-view-id': self.content_view['id'], 'name': cvf_name})

    @tier1
    def test_positive_delete_by_org_name(self):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using organization and content
        view names where that filter was applied

        :id: 61b25ae5-98d5-4b7d-9197-2b1935054a92

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': self.content_view['id'],
                'name': cvf_name,
                'organization-id': self.org['id'],
                'type': 'rpm',
            }
        )
        ContentView.filter.info({'content-view-id': self.content_view['id'], 'name': cvf_name})
        ContentView.filter.delete(
            {
                'content-view': self.content_view['name'],
                'name': cvf_name,
                'organization': self.org['name'],
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.info({'content-view-id': self.content_view['id'], 'name': cvf_name})

    @tier1
    def test_negative_delete_by_name(self):
        """Try to delete non-existent filter using generated name

        :id: 84509061-6652-4594-b68a-4566c04bc289

        :expectedresults: System returned error

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.filter.delete(
                {'content-view-id': self.content_view['id'], 'name': 'invalid_cv_filter'}
            )
