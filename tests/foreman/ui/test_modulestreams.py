"""Test class for module_streams UI

:Requirement: Repositories

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Artemis

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings


@pytest.fixture(scope='module')
def module_org(module_target_sat):
    return module_target_sat.api.Organization().create()


@pytest.fixture(scope='module')
def module_product(module_org, module_target_sat):
    return module_target_sat.api.Product(organization=module_org).create()


@pytest.fixture(scope='module')
def module_yum_repo(module_product, module_target_sat):
    yum_repo = module_target_sat.api.Repository(
        name=gen_string('alpha'),
        product=module_product,
        content_type='yum',
        url=settings.repos.module_stream_1.url,
    ).create()
    yum_repo.sync()
    return yum_repo


def test_positive_module_stream_details_search_in_repo(
    module_target_sat, module_org, module_yum_repo
):
    """Create product with yum repository assigned to it. Search for
    module_streams inside of it

    :id: 2ad7021a-25ee-42de-97d9-21fd928591d3

    :expectedresults: Content search functionality works as intended and
        expected module_streams are present inside of repository

    :BZ: 1948758
    """
    ducks_count = len(
        module_target_sat.api.ModuleStream().search(
            query={'search': f'name~"duck" and repository="{module_yum_repo.name}"'}
        )
    )
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        duck_results = session.modulestream.search(
            f'name~"duck" and repository="{module_yum_repo.name}"'
        )
        assert len(duck_results) == ducks_count
        assert all(item['Name'].startswith('duck') for item in duck_results)
        walrus_details = session.modulestream.read('walrus', '5.21')
        expected_module_details = {
            'Context': 'deadbeef',
            'Name': 'walrus',
            'Stream': '5.21',
            'Arch': 'x86_64',
            'Description': 'A module for the walrus 5.21 package',
        }
        module_stream_details = {
            key: value
            for key, value in walrus_details['details_table'].items()
            if key in expected_module_details
        }
        assert expected_module_details == module_stream_details


def test_positive_module_stream_all_tabs(module_target_sat, module_org):
    """Verify all 4 tabs render correctly on Module Stream details page.

    :id: 7c5f4e8a-3b2d-4a1f-9e6c-8d7b5a4c3e2f

    :steps:
        1. Navigate to Content -> Content Types -> Module Streams
        2. Click on a module stream name
        3. Verify all 4 tabs render (Details, Repositories, Profiles, Artifacts)
        4. Verify tab content can be read

    :expectedresults: All tabs are present and accessible

    :CaseImportance: High

    :Verifies: SAT-39267
    """
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        module_data = session.modulestream.read('walrus', '5.21')

        assert 'details_table' in module_data, 'Details table not found'
        assert module_data['details_table']['Name'] == 'walrus'
        assert module_data['details_table']['Stream'] == '5.21'
        assert 'repositories_tab' in module_data, 'Repositories tab not found'
        assert 'profiles_tab' in module_data, 'Profiles tab not found'
        assert 'artifacts_tab' in module_data, 'Artifacts tab not found'
