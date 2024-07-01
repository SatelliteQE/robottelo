"""Test class for Content View Filters

:Requirement: Contentviewfilter

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""

import random

from fauxfactory import gen_string
import pytest

from robottelo.cli.defaults import Defaults
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
)


@pytest.fixture(scope='module')
def sync_repo(module_org, module_product, module_target_sat):
    repo = module_target_sat.cli_factory.make_repository(
        {'organization-id': module_org.id, 'product-id': module_product.id}
    )
    module_target_sat.cli.Repository.synchronize({'id': repo['id']})
    return repo


@pytest.fixture
def content_view(module_org, sync_repo, module_target_sat):
    return module_target_sat.cli_factory.make_content_view(
        {'organization-id': module_org.id, 'repository-ids': [sync_repo['id']]}
    )


class TestContentViewFilter:
    """Content View Filter CLI tests"""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    @pytest.mark.parametrize('filter_content_type', ['rpm', 'package_group', 'erratum', 'modulemd'])
    def test_positive_create_with_name_by_cv_id(
        self, name, filter_content_type, module_org, content_view, module_target_sat
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
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': name,
                'organization-id': module_org.id,
                'type': filter_content_type,
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': name}
        )
        assert cvf['name'] == name
        assert cvf['type'] == filter_content_type

    @pytest.mark.tier1
    @pytest.mark.parametrize('filter_content_type', ['rpm', 'package_group', 'erratum', 'modulemd'])
    def test_positive_create_with_content_type_by_cv_id(
        self, filter_content_type, module_org, content_view, module_target_sat
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
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': filter_content_type,
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert cvf['type'] == filter_content_type

    @pytest.mark.tier1
    @pytest.mark.parametrize('inclusion', ['true', 'false'])
    def test_positive_create_with_inclusion_by_cv_id(
        self, inclusion, module_org, content_view, module_target_sat
    ):
        """Create new content view filter and assign it to existing content
        view by id. Use different inclusions as a parameter

        :id: 4a18ee71-3f0d-4e8b-909e-999d722ebc0a

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct and expected parameters

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': inclusion,
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert cvf['inclusion'] == inclusion

    @pytest.mark.tier1
    def test_positive_create_with_description_by_cv_id(
        self, module_org, content_view, module_target_sat
    ):
        """Create new content view filter with description and assign it to
        existing content view.

        :id: e283a42a-122b-467c-8d00-d6487f657692

        :expectedresults: Content view filter created successfully and has
            proper description

        :CaseImportance: Low
        """
        description = gen_string('utf8')
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'description': description,
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'package_group',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert cvf['description'] == description

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier1
    def test_positive_create_with_default_taxonomies(
        self, module_org, module_location, content_view, module_target_sat
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
            module_target_sat.cli.ContentView.filter.create(
                {
                    'content-view': content_view['name'],
                    'name': name,
                    'type': 'erratum',
                    'inclusion': 'true',
                },
            )
            cvf = module_target_sat.cli.ContentView.filter.info(
                {'content-view': content_view['name'], 'name': name}
            )
            assert cvf['name'] == name
        finally:
            Defaults.delete({'param-name': 'organization_id'})
            Defaults.delete({'param-name': 'location_id'})

    @pytest.mark.tier1
    def test_positive_list_by_name_and_org(self, module_org, content_view, module_target_sat):
        """Create new content view filter and try to list it by its name and
        organization it belongs

        :id: e685892d-9dc3-48f2-8a09-8f861dceaf4e

        :expectedresults: Content view filter created and listed successfully

        :BZ: 1378018

        :customerscenario: true

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'package_group',
            },
        )
        cv_filters = module_target_sat.cli.ContentView.filter.list(
            {'content-view': content_view['name'], 'organization': module_org.name}
        )
        assert len(cv_filters) >= 1
        assert cvf_name in [cvf['name'] for cvf in cv_filters]

    @pytest.mark.tier1
    def test_positive_create_by_cv_name(self, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by name. Use organization id for reference

        :id: 0fb2fbc2-0d81-451e-9b20-9e996e14c977

        :expectedresults: Content view filter created successfully

        :BZ: 1356906

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view': content_view['name'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'package_group',
            },
        )
        module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )

    @pytest.mark.tier1
    def test_positive_create_by_org_name(self, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by name. Use organization name for reference

        :id: 295847fe-51e4-483d-af2f-b972c8b5064c

        :expectedresults: Content view filter created successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view': content_view['name'],
                'inclusion': 'false',
                'name': cvf_name,
                'organization': module_org.name,
                'type': 'erratum',
            },
        )
        module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )

    @pytest.mark.tier1
    def test_positive_create_by_org_label(self, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by name. Use organization label for reference

        :id: f233e223-c08c-4ce1-b87a-9e055fdd7b83

        :expectedresults: Content view filter created successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view': content_view['name'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-label': module_org.label,
                'type': 'erratum',
            },
        )
        module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )

    @pytest.mark.tier1
    def test_positive_create_with_repo_by_id(
        self, module_org, sync_repo, content_view, module_target_sat
    ):
        """Create new content view filter and assign it to existing content
        view that has repository assigned to it. Use that repository id for
        proper filter assignment.

        :id: 6d517e09-6a6a-4eed-91fe-9459610c0062

        :expectedresults: Content view filter created successfully and has
            proper repository affected

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        # Check that only one, specified above, repository is displayed
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']

    @pytest.mark.tier1
    def test_positive_create_with_repo_by_name(
        self, module_org, module_product, sync_repo, content_view, module_target_sat
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
        module_target_sat.cli.ContentView.filter.create(
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
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        # Check that only one, specified above, repository is displayed
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']

    @pytest.mark.tier1
    def test_positive_create_with_original_pkgs(self, sync_repo, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view that has repository assigned to it. Enable 'original packages'
        option for that filter

        :id: 5491233a-9361-435f-87ad-dca97e6d5d2f

        :expectedresults: Content view filter created successfully and has
            proper repository affected

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'original-packages': 'true',
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert cvf['repositories'][0]['name'] == sync_repo['name']

    @pytest.mark.tier2
    def test_positive_create_with_repos_yum_and_docker(
        self, module_org, module_product, sync_repo, content_view, module_target_sat
    ):
        """Create new docker repository and add to content view that has yum
        repo already assigned to it. Create new content view filter and assign
        it to mentioned content view. Use these repositories id for proper
        filter assignment.

        :id: 8419a5fa-0530-42a7-964c-7c513443c5c8

        :expectedresults: Content view filter created successfully and has both
            repositories affected (yum and docker)
        """
        docker_repository = module_target_sat.cli_factory.make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': 'busybox',
                'organization-id': module_org.id,
                'product-id': module_product.id,
                'url': CONTAINER_REGISTRY_HUB,
            },
        )

        module_target_sat.cli.ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': docker_repository['id']}
        )
        repos = [sync_repo['id'], docker_repository['id']]
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'repository-ids': repos,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert len(cvf['repositories']) == 2
        for repo in cvf['repositories']:
            assert repo['id'] in repos

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_invalid_name(
        self, name, module_org, content_view, module_target_sat
    ):
        """Try to create content view filter using invalid names only

        :id: f3497a23-6e34-4fee-9964-f95762fc737c

        :parametrized: yes

        :expectedresults: Content view filter is not created

        :CaseImportance: Low
        """
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': name,
                    'organization-id': module_org.id,
                    'type': 'rpm',
                },
            )

    @pytest.mark.tier1
    def test_negative_create_with_same_name(self, module_org, content_view, module_target_sat):
        """Try to create content view filter using same name twice

        :id: 7e7444f4-e2b5-406d-a210-49b4008c88d9

        :expectedresults: Second content view filter is not created

        :CaseImportance: Low
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'organization-id': module_org.id,
                    'type': 'rpm',
                },
            )

    @pytest.mark.tier1
    def test_negative_create_without_type(self, module_org, content_view, module_target_sat):
        """Try to create content view filter without providing required
        parameter 'type'

        :id: 8af65427-d0f0-4661-b062-93e054079f44

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': gen_string('utf8'),
                    'organization-id': module_org.id,
                },
            )

    @pytest.mark.tier1
    def test_negative_create_without_cv(self, module_target_sat):
        """Try to create content view filter without providing content
        view information which should be used as basis for filter

        :id: 4ed3828e-52e8-457c-a2af-bb03b00467e8

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.create(
                {'name': gen_string('utf8'), 'type': 'rpm'}
            )

    @pytest.mark.tier1
    def test_negative_create_with_invalid_repo_id(
        self, module_org, content_view, module_target_sat
    ):
        """Try to create content view filter using incorrect repository

        :id: 21fdbeca-ad0a-4e29-93dc-f850b5639f4f

        :expectedresults: Content view filter is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.create(
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
    def test_positive_update_name(self, new_name, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by id. Try to update that filter using different value types as a
        name

        :id: 70ba8916-5898-4911-9de8-21d2e0fb3df9

        :parametrized: yes

        :expectedresults: Content view filter updated successfully and has
            proper and expected name

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        cvf = module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        module_target_sat.cli.ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'id': cvf['filter-id'],
                'new-name': new_name,
            }
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': new_name}
        )
        assert cvf['name'] == new_name

    @pytest.mark.tier2
    def test_positive_update_repo_with_same_type(
        self, module_org, module_product, sync_repo, content_view, module_target_sat
    ):
        """Create new content view filter and apply it to existing content view
        that has repository assigned to it. Try to update that filter and
        change affected repository on another one.

        :id: b2f444fd-e65e-41ba-9941-620d3cdb260f

        :expectedresults: Content view filter updated successfully and has new
            repository affected

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']

        new_repo = module_target_sat.cli_factory.make_repository(
            {'organization-id': module_org.id, 'product-id': module_product.id},
        )
        module_target_sat.cli.ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': new_repo['id']}
        )

        module_target_sat.cli.ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': new_repo['id'],
            }
        )

        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] != sync_repo['name']
        assert cvf['repositories'][0]['name'] == new_repo['name']

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_repo_with_different_type(
        self, module_org, module_product, sync_repo, content_view, module_target_sat
    ):
        """Create new content view filter and apply it to existing content view
        that has repository assigned to it. Try to update that filter and
        change affected repository on another one. That new repository should
        have another type from initial one (e.g. yum->docker)

        :id: cf3daa0d-e918-4330-95ad-f88933579829

        :expectedresults: Content view filter updated successfully and has new
            repository affected

        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] == sync_repo['name']
        docker_repo = module_target_sat.cli_factory.make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': 'busybox',
                'organization-id': module_org.id,
                'product-id': module_product.id,
                'url': CONTAINER_REGISTRY_HUB,
            },
        )
        module_target_sat.cli.ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': docker_repo['id']}
        )
        module_target_sat.cli.ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': docker_repo['id'],
            }
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert len(cvf['repositories']) == 1
        assert cvf['repositories'][0]['name'] != sync_repo['name']
        assert cvf['repositories'][0]['name'] == docker_repo['name']

    @pytest.mark.tier2
    def test_positive_update_inclusion(self, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by id. Try to update that filter and assign opposite inclusion
        value for it

        :id: 76b3c66d-8200-4cf0-8cd0-b57de4ff12b0

        :expectedresults: Content view filter updated successfully and has
            correct and expected value for inclusion parameter

        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert cvf['inclusion'] == 'true'
        module_target_sat.cli.ContentView.filter.update(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'inclusion': 'false',
            }
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert cvf['inclusion'] == 'false'

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_with_name(self, new_name, content_view, module_target_sat):
        """Try to update content view filter using invalid names only

        :id: 6c40e452-f786-4e28-9f03-b1935b55b33a

        :parametrized: yes

        :expectedresults: Content view filter is not updated

        :BZ: 1328943

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {'content-view-id': content_view['id'], 'name': cvf_name, 'type': 'rpm'}
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'new-name': new_name,
                }
            )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.info(
                {'content-view-id': content_view['id'], 'name': new_name}
            )

    @pytest.mark.tier1
    def test_negative_update_with_same_name(self, module_org, content_view, module_target_sat):
        """Try to update content view filter using name of already
        existing entity

        :id: 9c1b1c75-af57-4218-9e2d-e69d74f50e04

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        new_name = gen_string('alpha', 100)
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': new_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': new_name,
                    'new-name': cvf_name,
                }
            )

    @pytest.mark.tier1
    def test_negative_update_inclusion(self, module_org, content_view, module_target_sat):
        """Try to update content view filter and assign incorrect inclusion
        value for it

        :id: 760400a8-49a5-4a31-924c-c232cb22ddad

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'inclusion': 'wrong_value',
                    'name': cvf_name,
                }
            )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        assert cvf['inclusion'] == 'true'

    @pytest.mark.tier1
    def test_negative_update_with_non_existent_repo_id(
        self, sync_repo, content_view, module_target_sat
    ):
        """Try to update content view filter using non-existing repository ID

        :id: 457af8c2-fb32-4164-9e19-98676f4ea063

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'repository-ids': gen_string('numeric', 6),
                }
            )

    @pytest.mark.tier1
    def test_negative_update_with_invalid_repo_id(
        self, module_org, module_product, sync_repo, content_view, module_target_sat
    ):
        """Try to update filter and assign repository which does not belong to
        filter content view

        :id: aa550619-c436-4184-bb29-2becadf69e5b

        :expectedresults: Content view filter is not updated

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'repository-ids': sync_repo['id'],
                'type': 'rpm',
            },
        )
        new_repo = module_target_sat.cli_factory.make_repository(
            {'organization-id': module_org.id, 'product-id': module_product.id},
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.update(
                {
                    'content-view-id': content_view['id'],
                    'name': cvf_name,
                    'repository-ids': new_repo['id'],
                }
            )

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_delete_by_name(self, name, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using different value types as a
        name

        :id: a01baf17-9c3c-4923-bfe0-865a4cbc4223

        :parametrized: yes

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': name}
        )
        module_target_sat.cli.ContentView.filter.delete(
            {'content-view-id': content_view['id'], 'name': name}
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.info(
                {'content-view-id': content_view['id'], 'name': name}
            )

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_delete_by_id(self, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using its id as a parameter

        :id: e3865a11-1ba0-481a-bfe0-f9235901946d

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        cvf = module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        module_target_sat.cli.ContentView.filter.delete({'id': cvf['filter-id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.info(
                {'content-view-id': content_view['id'], 'name': cvf_name}
            )

    @pytest.mark.tier1
    def test_positive_delete_by_org_name(self, module_org, content_view, module_target_sat):
        """Create new content view filter and assign it to existing content
        view by id. Try to delete that filter using organization and content
        view names where that filter was applied

        :id: 61b25ae5-98d5-4b7d-9197-2b1935054a92

        :expectedresults: Content view filter deleted successfully

        :CaseImportance: Critical
        """
        cvf_name = gen_string('utf8')
        module_target_sat.cli.ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'name': cvf_name,
                'organization-id': module_org.id,
                'type': 'rpm',
            },
        )
        module_target_sat.cli.ContentView.filter.info(
            {'content-view-id': content_view['id'], 'name': cvf_name}
        )
        module_target_sat.cli.ContentView.filter.delete(
            {
                'content-view': content_view['name'],
                'name': cvf_name,
                'organization': module_org.name,
            }
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.info(
                {'content-view-id': content_view['id'], 'name': cvf_name}
            )

    @pytest.mark.tier1
    def test_negative_delete_by_name(self, content_view, module_target_sat):
        """Try to delete non-existent filter using generated name

        :id: 84509061-6652-4594-b68a-4566c04bc289

        :expectedresults: System returned error

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.filter.delete(
                {'content-view-id': content_view['id'], 'name': gen_string('utf8')}
            )

    @pytest.mark.tier2
    def test_positive_check_filters_applied(self, target_sat, module_org, content_view):
        """Ensure the applied filters are indicated and listed correctly in the CVV info.

        :id: ab72af3f-6bee-4aa8-a74a-637fe9b7e34a

        :steps:
            1. Publish first CVV with no filters applied, assert no applied filters are indicated
               nor listed.
            2. Randomly add filters to the CV, publish new CVVs and assert that the applied filters
               are indicated and the correct filters are listed.
            3. Randomly remove filters from the CV, publish new CVVs and assert that the applied
               filters are indicated when at least one filter exists and the correct filters were
               removed.

        :expectedresults:
            1. Hammer shows correctly if a CVV has filter(s) applied, no matter the filter type,
               count, nor order.
            2. Hammer lists correctly the applied filter(s), no matter the filter type, count
               nor order.
        """
        f_types = ['rpm', 'package_group', 'erratum', 'modulemd', 'docker']
        filters_applied = []

        # Publish first CVV with no filters applied
        target_sat.cli.ContentView.publish({'id': content_view['id']})
        cvv = target_sat.cli.ContentView.info({'id': content_view['id']})['versions'][0]
        cvv_info = target_sat.cli.ContentView.version_info(
            {'id': cvv['id'], 'include-applied-filters': 'true'}
        )
        assert cvv_info['has-applied-filters'] == 'no'
        assert 'applied-filters' not in cvv_info

        # Randomly add filters to the CV, assert correct CVV info values
        for f_type in random.choices(f_types, k=random.randint(1, 5)):
            cvf = target_sat.cli.ContentView.filter.create(
                {
                    'content-view-id': content_view['id'],
                    'name': gen_string('alpha'),
                    'organization-id': module_org.id,
                    'type': f_type,
                    'inclusion': random.choice(['true', 'false']),
                },
            )
            filters_applied.append(cvf)

            target_sat.cli.ContentView.publish({'id': content_view['id']})
            cvv = max(
                target_sat.cli.ContentView.info({'id': content_view['id']})['versions'],
                key=lambda x: int(x['id']),
            )
            cvv_info = target_sat.cli.ContentView.version_info(
                {'id': cvv['id'], 'include-applied-filters': 'true'}
            )
            assert cvv_info['has-applied-filters'] == 'yes'
            assert len(cvv_info['applied-filters']) == len(filters_applied)
            f_listed = [f for f in cvv_info['applied-filters'] if f['id'] == cvf['filter-id']]
            assert len(f_listed) == 1
            assert f_listed[0]['name'] == cvf['name']

        # Randomly remove filters from the CV, assert correct CVV info values
        random.shuffle(filters_applied)
        for _ in range(len(filters_applied)):
            cvf = filters_applied.pop()
            target_sat.cli.ContentView.filter.delete({'id': cvf['filter-id']})

            target_sat.cli.ContentView.publish({'id': content_view['id']})
            cvv = max(
                target_sat.cli.ContentView.info({'id': content_view['id']})['versions'],
                key=lambda x: int(x['id']),
            )
            cvv_info = target_sat.cli.ContentView.version_info(
                {'id': cvv['id'], 'include-applied-filters': 'true'}
            )
            if len(filters_applied) > 0:
                assert cvv_info['has-applied-filters'] == 'yes'
                assert len(cvv_info['applied-filters']) == len(filters_applied)
                assert cvf['filter-id'] not in [f['id'] for f in cvv_info['applied-filters']]
                assert cvf['name'] not in [f['name'] for f in cvv_info['applied-filters']]
            else:
                assert cvv_info['has-applied-filters'] == 'no'
                assert 'applied-filters' not in cvv_info
