"""Test class for Host CLI

:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: LifecycleEnvironments

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from math import ceil

import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_org
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.constants import ENVIRONMENT


@pytest.fixture(scope='class')
def module_lce(module_org):
    return make_lifecycle_environment(
        {
            'name': module_org.name,
            'organization-id': module_org.id,
            'description': gen_string('alpha'),
        }
    )


# Issues validation
@pytest.mark.tier2
def test_positive_list_subcommand(module_org):
    """List subcommand returns standard output

    :id: cca249d0-fb77-422b-aae3-3361887269db

    :expectedresults: There should not be an error returned

    :BZ: 1077386

    :CaseImportance: High
    """

    # List available lifecycle environments using default Table
    # output
    cmd = 'lifecycle-environment list --organization-id="%s"'
    result = LifecycleEnvironment.execute(cmd % module_org.id, None, None, False)
    assert len(result) > 0


@pytest.mark.tier2
def test_positive_search_lce_via_UTF8(module_org):
    """Search lifecycle environment via its name containing UTF-8
    chars

    :id: d15001ed-5bbf-43cf-bdd3-1e129dff14ec

    :expectedresults: Can get info for lifecycle by its name

    :BZ: 1077333

    :CaseImportance: High
    """
    test_data = {'name': gen_string('utf8', 15), 'organization-id': module_org.id}
    # Can we find the new object
    result = LifecycleEnvironment.info(
        {'name': make_lifecycle_environment(test_data)['name'], 'organization-id': module_org.id}
    )
    assert result['name'] == test_data['name']


# CRUD
@pytest.mark.tier1
def test_positive_lce_crud(module_org):
    """CRUD test case for lifecycle environment for name, description, label, registry name pattern,
    and unauthenticated pull

    :id: 6b0fbf4f-528c-4983-bc3f-e81ccb7438fd

    :expectedresults: Lifecycle environment is created, read, updated, and deleted successfull

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    desc = gen_string('alpha')
    new_desc = gen_string('alpha')
    label = gen_string('alpha')
    org_name = module_org.name
    registry_name_pattern = (
        "{}-<%= organization.label %>/<%= repository.docker_upstream_name %>"
    ).format(gen_string('alpha', 5))

    # create
    lce = make_lifecycle_environment(
        {
            'organization': org_name,
            'organization-id': module_org.id,
            'name': name,
            'label': label,
            'description': desc,
        }
    )

    assert lce['prior-lifecycle-environment'] == ENVIRONMENT
    assert lce['name'] == name
    assert lce['description'] == desc
    assert lce['label'] == label
    assert lce['organization'] == org_name

    # update
    LifecycleEnvironment.update(
        {
            'id': lce['id'],
            'new-name': new_name,
            'description': new_desc,
            'registry-unauthenticated-pull': 'true',
            'registry-name-pattern': registry_name_pattern,
        }
    )
    lce = LifecycleEnvironment.info({'id': lce['id'], 'organization-id': module_org.id})
    assert lce['name'] == new_name
    assert lce['registry-name-pattern'] == registry_name_pattern
    assert lce['unauthenticated-pull'] == 'true'

    # delete
    LifecycleEnvironment.delete({'id': lce['id']})
    with pytest.raises(CLIReturnCodeError):
        LifecycleEnvironment.info({'id': lce['id'], 'organization-id': module_org.id})


@pytest.mark.tier1
def test_positive_create_with_organization_label(module_org):
    """Create lifecycle environment, specifying organization label

    :id: eb5cfc71-c83d-45ca-ba34-9ef79197691d

    :expectedresults: Lifecycle environment is created for correct
        organization


    :CaseImportance: Critical
    """
    new_lce = make_lifecycle_environment(
        {'name': gen_string('alpha'), 'organization-label': module_org.label}
    )
    assert new_lce['organization'] == module_org.label


@pytest.mark.tier1
def test_positve_list_paths(module_org):
    """List the environment paths under a given organization

    :id: 71600d6b-1ef4-4b88-8e9b-eb2481ee1fe2

    :expectedresults: Lifecycle environment paths listed


    :CaseImportance: Critical
    """
    lc_env = make_lifecycle_environment({'organization-id': module_org.id})
    # Add paths to lifecycle environments
    result = LifecycleEnvironment.paths(
        {'organization-id': module_org.id, 'permission-type': 'readable'}
    )
    assert f"Library >> {lc_env['name']}" in result


class LifeCycleEnvironmentPaginationTestCase:
    """Test class for LifeCycle Environment pagination tests"""

    @classmethod
    def setUpClass(cls):
        """Create organization and lifecycle environments to reuse in tests"""
        super().setUpClass()
        cls.lces_count = 25
        cls.org = make_org()
        env_base_name = gen_string('alpha')
        last_env_name = ENVIRONMENT
        cls.env_names = [last_env_name]
        for env_index in range(cls.lces_count):
            env_name = f'{env_base_name}-{env_index}'
            make_lifecycle_environment(
                {'name': env_name, 'organization-id': cls.org['id'], 'prior': last_env_name}
            )
            last_env_name = env_name
            cls.env_names.append(env_name)

        cls.lces_count += 1  # include default 'Library' lce

    @pytest.mark.tier2
    def test_positive_list_all_with_per_page(self):
        """Attempt to list more than 20 lifecycle environment with per-page
        option.

        :id: 6e10fb0e-5e2c-45e6-85a8-0c853450257b

        :BZ: 1420503

        :expectedresults: all the Lifecycle environments are listed

        """
        per_page_count = self.lces_count + 5

        lifecycle_environments = LifecycleEnvironment.list(
            {'organization-id': self.org['id'], 'per-page': per_page_count}
        )

        assert len(lifecycle_environments) == self.lces_count
        env_name_set = {env['name'] for env in lifecycle_environments}
        assert env_name_set == set(self.env_names)

    @pytest.mark.tier2
    def test_positive_list_with_pagination(self):
        """Make sure lces list can be displayed with different items per page
        value

        :id: 28ecbc1f-bb5c-49df-a586-8cfdc0dd57df

        :BZ: 1368590

        :expectedresults: `per-page` correctly sets amount of items displayed
            per page, different `per-page` values divide a list into correct
            number of pages

        """
        # Test different `per-page` values
        for per_page in (1, 5, 20):
            # Verify the first page contains exactly the same items count
            # as `per-page` value
            with self.subTest(per_page):
                lces = LifecycleEnvironment.list(
                    {'organization-id': self.org['id'], 'per-page': per_page}
                )
                assert len(lces) == per_page
                # Verify pagination and total amount of pages by checking the
                # items count on the last page
                last_page = ceil(self.lces_count / per_page)
                lces = LifecycleEnvironment.list(
                    {'organization-id': self.org['id'], 'page': last_page, 'per-page': per_page}
                )
                assert len(lces) == self.lces_count % per_page or per_page
