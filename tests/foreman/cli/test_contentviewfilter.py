"""Test class for Content View Filters

:Requirement: Contentviewfilter

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.defaults import Defaults
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_repository
from robottelo.cli.repository import Repository
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list


@pytest.fixture(scope='module')
def sync_repo(module_org, module_product):
    repo = make_repository({'organization-id': module_org.id, 'product-id': module_product.id})
    Repository.synchronize({'id': repo['id']})
    return repo


@pytest.fixture
def content_view(module_org, sync_repo):
    return make_content_view(
        {'organization-id': module_org.id, 'repository-ids': [sync_repo['id']]}
    )


class TestContentViewFilter:
    """Content View Filter CLI tests"""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    @pytest.mark.parametrize('filter_content_type', ['rpm', 'package_group', 'erratum', 'modulemd'])
    def test_positive_create_with_name_by_cv_id(
        self, name, filter_content_type, module_org, content_view
    ):
        """Create new content view filter and assign it to existing content
        view by id. Use different value types as a name and random filter
        content type as a parameter for this filter

        :id: 2cfdf72e-179d-4bba-8aab-288594cac836

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct and expected parameters

        :CaseImportance: Critical
        """
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': name,
                'organization-id': module_org.id,
                'type': filter_content_type,
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': name})
        assert cvf['name'] == name
        assert cvf['type'] == filter_content_type

    @pytest.mark.tier1
    @pytest.mark.parametrize('filter_content_type', ['rpm', 'package_group', 'erratum', 'modulemd'])
    def test_positive_create_with_content_type_by_cv_id(
        self, filter_content_type, module_org, content_view
    ):
        """Create new content view filter and assign it to existing content
        view by id. Use different content types as a parameter

        :id: b3e5a58b-eddc-4ceb-ae34-6c0ab5664784

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct and expected parameters

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': filter_content_type,
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert cvf['type'] == filter_content_type

    @pytest.mark.tier1
    @pytest.mark.parametrize('inclusion', ['true', 'false'])
    def test_positive_create_with_inclusion_by_cv_id(self, inclusion, module_org, content_view):
        """Create new content view filter and assign it to existing content
        view by id. Use different inclusions as a parameter

        :id: 4a18ee71-3f0d-4e8b-909e-999d722ebc0a

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct and expected parameters

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': inclusion,
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert cvf['inclusion'] == inclusion

    @pytest.mark.tier1
    def test_positive_create_with_description_by_cv_id(self, module_org, content_view):
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
                'content-view-id': content_view['id'],
                'description': description,
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'package_group',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert cvf['description'] == description

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier1
    def test_positive_create_with_default_taxonomies(
        self, module_org, module_location, content_view
    ):
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
        Defaults.add({'param-name': 'organization_id', 'param-value': module_org.id})
        Defaults.add({'param-name': 'location_id', 'param-value': module_location.id})
        try:
            ContentView.filter.create(
                {
                    'content-view': content_view['name'],
                    'name': name,
                    'type': 'erratum',
                    'inclusion': 'true',
                },
            )
            cvf = ContentView.filter.info({'content-view': content_view['name'], 'name': name})
            assert cvf['name'] == name
        finally:
            Defaults.delete({'param-name': 'organization_id'})
            Defaults.delete({'param-name': 'location_id'})

    @pytest.mark.tier1
    def test_positive_list_by_name_and_org(self, module_org, content_view):
        """Create new content view filter and try to list it by its name and
        organization it belongs

        :id: e685892d-9dc3-48f2-8a09-8f861dceaf4e

        :expectedresults: Content view filter created and listed successfully

        :BZ: 1378018

        :customerscenario: true

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'package_group',
            },
        )
        cv_filters = ContentView.filter.list(
            {'content-view': content_view['name'], 'organization': module_org.name}
        )
        assert len(cv_filters) >= 1
        assert cvf_name in [cvf['name'] for cvf in cv_filters]

    @pytest.mark.tier1
    def test_positive_create_by_cv_name(self, module_org, content_view):
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
                'content-view': content_view['name'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'package_group',
            },
        )
        ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})

    @pytest.mark.tier1
    def test_positive_create_by_org_name(self, module_org, content_view):
        """Create new content view filter and assign it to existing content
        view by name. Use organization name for reference

        :id: 295847fe-51e4-483d-af2f-b972c8b5064c

        :expectedresults: Content view filter created successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view': content_view['name'],
                'inclusion': 'false',
                'name': cvf_name,
                'organization': module_org.name,
                'type': 'erratum',
            },
        )
        ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})

    @pytest.mark.tier1
    def test_positive_create_by_org_label(self, module_org, content_view):
        """Create new content view filter and assign it to existing content
        view by name. Use organization label for reference

        :id: f233e223-c08c-4ce1-b87a-9e055fdd7b83

        :expectedresults: Content view filter created successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view': content_view['name'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-label': module_org.label,
                'type': 'erratum',
            },
        )
        ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})

    @pytest.mark.tier1
    def test_positive_create_with_repo_by_id(self, module_org, sync_repo, content_view):
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
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        # Check that only one, specified above, repository is displayed
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']

    @pytest.mark.tier1
    def test_positive_create_with_repo_by_name(
        self, module_org, module_product, sync_repo, content_view
    ):
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
                'content-view-id': content_view['id'],
                'inclusion': 'false',
                'name': cvf_name,
                'product': module_product.name,
                'repositories': sync_repo['name'],
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        # Check that only one, specified above, repository is displayed
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']

    @pytest.mark.tier1
    def test_positive_create_with_original_pkgs(self, sync_repo, content_view):
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
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'original-packages': 'true',
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert cvf['repositories'][0]['name'] == sync_repo['name']

    @pytest.mark.tier2
    def test_positive_create_with_repos_yum_and_docker(
        self, module_org, module_product, sync_repo, content_view
    ):
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
                'organization-id': module_org.id,
                'product-id': module_product.id,
                'url': CONTAINER_REGISTRY_HUB,
            },
        )

        ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': docker_repository['id']}
        )
        repos = [sync_repo['id'], docker_repository['id']]
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'repository-ids': repos,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert len(cvf['repositories']) == 2
        for repo in cvf['repositories']:
            assert repo['id'] in repos

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_invalid_name(self, name, module_org, content_view):
        """Try to create content view filter using invalid names only

        :id: f3497a23-6e34-4fee-9964-f95762fc737c

        :parametrized: yes

        :expectedresults: Content view filter is not created

        :CaseImportance: Low
        """
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': name,
                    'organization-id': module_org.id,
                    'type': 'rpm',
                },
            )

    @pytest.mark.tier1
    def test_negative_create_with_same_name(self, module_org, content_view):
        """Try to create content view filter using same name twice

        :id: 7e7444f4-e2b5-406d-a210-49b4008c88d9

        :expectedresults: Second content view filter is not created

        :CaseImportance: Low
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'organization-id': module_org.id,
                    'type': 'rpm',
                },
            )

    @pytest.mark.tier1
    def test_negative_create_without_type(self, module_org, content_view):
        """Try to create content view filter without providing required
        parameter 'type'

        :id: 8af65427-d0f0-4661-b062-93e054079f44

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': gen_string('utf8'),
                    'organization-id': module_org.id,
                },
            )

    @pytest.mark.tier1
    def test_negative_create_without_cv(self):
        """Try to create content view filter without providing content
        view information which should be used as basis for filter

        :id: 4ed3828e-52e8-457c-a2af-bb03b00467e8

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.create({'name': gen_string('utf8'), 'type': 'rpm'})

    @pytest.mark.tier1
    def test_negative_create_with_invalid_repo_id(self, module_org, content_view):
        """Try to create content view filter using incorrect repository

        :id: 21fdbeca-ad0a-4e29-93dc-f850b5639f4f

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': gen_string('utf8'),
                    'repository-ids': gen_string('numeric', 6),
                    'organization-id': module_org.id,
                    'type': 'rpm',
                },
            )

    @pytest.mark.tier2
    @pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
    def test_positive_update_name(self, new_name, module_org, content_view):
        """Create new content view filter and assign it to existing content
        view by id. Try to update that filter using different value types as a
        name

        :id: 70ba8916-5898-4911-9de8-21d2e0fb3df9

        :parametrized: yes

        :expectedresults: Content view filter updated successfully and has
            proper and expected name

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        cvf = ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'id': cvf['filter-id'],
                'new-name': new_name,
            }
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': new_name})
        assert cvf['name'] == new_name

    @pytest.mark.tier2
    def test_positive_update_repo_with_same_type(
        self, module_org, module_product, sync_repo, content_view
    ):
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
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']

        new_repo = make_repository(
            {'organization-id': module_org.id, 'product-id': module_product.id},
        )
        ContentView.add_repository({'id': content_view['id'], 'repository-id': new_repo['id']})

        ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': new_repo['id'],
            }
        )

        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] != sync_repo['name']
        assert cvf['repositories'][0]['name'] == new_repo['name']

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_repo_with_different_type(
        self, module_org, module_product, sync_repo, content_view
    ):
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
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']
        docker_repo = make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': 'busybox',
                'organization-id': module_org.id,
                'product-id': module_product.id,
                'url': CONTAINER_REGISTRY_HUB,
            },
        )
        ContentView.add_repository({'id': content_view['id'], 'repository-id': docker_repo['id']})
        ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': docker_repo['id'],
            }
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] != sync_repo['name']
        assert cvf['repositories'][0]['name'] == docker_repo['name']

    @pytest.mark.tier2
    def test_positive_update_inclusion(self, module_org, content_view):
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
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert cvf['inclusion'] == 'true'
        ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'inclusion': 'false',
            }
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert cvf['inclusion'] == 'false'

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_with_name(self, new_name, content_view):
        """Try to update content view filter using invalid names only

        :id: 6c40e452-f786-4e28-9f03-b1935b55b33a

        :parametrized: yes

        :expectedresults: Content view filter is not updated

        :BZ: 1328943

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {'content-view-id': content_view['id'], 'name': cvf_name, 'type': 'rpm'}
        )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'new-name': new_name,
                }
            )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.info({'content-view-id': content_view['id'], 'name': new_name})

    @pytest.mark.tier1
    def test_negative_update_with_same_name(self, module_org, content_view):
        """Try to update content view filter using name of already
        existing entity

        :id: 9c1b1c75-af57-4218-9e2d-e69d74f50e04

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        new_name = gen_string('alpha', 100)
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': new_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': new_name,
                    'new-name': cvf_name,
                }
            )

    @pytest.mark.tier1
    def test_negative_update_inclusion(self, module_org, content_view):
        """Try to update content view filter and assign incorrect inclusion
        value for it

        :id: 760400a8-49a5-4a31-924c-c232cb22ddad

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'inclusion': 'wrong_value',
                    'name': cvf_name,
                }
            )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        assert cvf['inclusion'] == 'true'

    @pytest.mark.tier1
    def test_negative_update_with_non_existent_repo_id(self, sync_repo, content_view):
        """Try to update content view filter using non-existing repository ID

        :id: 457af8c2-fb32-4164-9e19-98676f4ea063

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'repository-ids': gen_string('numeric', 6),
                }
            )

    @pytest.mark.tier1
    def test_negative_update_with_invalid_repo_id(
        self, module_org, module_product, sync_repo, content_view
    ):
        """Try to update filter and assign repository which does not belong to
        filter content view

        :id: aa550619-c436-4184-bb29-2becadf69e5b

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        new_repo = make_repository(
            {'organization-id': module_org.id, 'product-id': module_product.id},
        )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'repository-ids': new_repo['id'],
                }
            )

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_delete_by_name(self, name, module_org, content_view):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using different value types as a
        name

        :id: a01baf17-9c3c-4923-bfe0-865a4cbc4223

        :parametrized: yes

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        ContentView.filter.info({'content-view-id': content_view['id'], 'name': name})
        ContentView.filter.delete({'content-view-id': content_view['id'], 'name': name})
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.info({'content-view-id': content_view['id'], 'name': name})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_delete_by_id(self, module_org, content_view):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using its id as a parameter

        :id: e3865a11-1ba0-481a-bfe0-f9235901946d

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        ContentView.filter.delete({'id': cvf['filter-id']})
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})

    @pytest.mark.tier1
    def test_positive_delete_by_org_name(self, module_org, content_view):
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
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})
        ContentView.filter.delete(
            {
                'content-view': content_view['name'],
                'name': cvf_name,
                'organization': module_org.name,
            }
        )
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.info({'content-view-id': content_view['id'], 'name': cvf_name})

    @pytest.mark.tier1
    def test_negative_delete_by_name(self, content_view):
        """Try to delete non-existent filter using generated name

        :id: 84509061-6652-4594-b68a-4566c04bc289

        :expectedresults: System returned error

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            ContentView.filter.delete(
                {'content-view-id': content_view['id'], 'name': gen_string('utf8')}
            )
