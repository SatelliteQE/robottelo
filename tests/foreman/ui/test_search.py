"""Test classes for Search component

:Requirement: Search

:CaseAutomation: Automated

:CaseComponent: Search

:Team: Endeavour

:CaseImportance: Medium
"""

from collections import namedtuple

from fauxfactory import gen_string
import pytest

from robottelo.config import settings

SearchData = namedtuple('SearchData', ['expected_items', 'not_expected_items'])


def menu_search_should_find(search_func: callable, values: list[str]):
    """Helper function that does a vertical menu search for each value in `values` list
    and makes sure it finds a corresponding match.
    """
    for search_string in values:
        results = search_func(search_string)
        assert results, f'No result found for search string {search_string}!'
        for result in results:
            assert (
                search_string.lower() in result.lower()
            ), f'Search string {search_string} does not match result {result}!'


def menu_search_should_not_find(search_func: callable, values: list[str]):
    """Helper function that does a vertical menu search for each value in `values` list
    and makes sure it does not find any match.
    """
    for search_string in values:
        results = search_func(search_string)
        assert not results, f'Search string {search_string} should not return any results!'


@pytest.fixture(scope='module')
def auditor_module_user(
    module_target_sat, module_org, module_location, default_org, default_location
):
    """User with Auditor role. This user has significantly limited menu access.
    Expected or not expected data for searching the menu are appended as `search_for` attribute.
    """
    auditor_role = module_target_sat.api.Role().search(query={'search': 'name="Auditor"'})[0]
    password = gen_string('alphanumeric')
    user = module_target_sat.api.User(
        admin=False,
        location=[module_location],
        organization=[module_org],
        role=[auditor_role],
        password=password,
    ).create()
    user.password = password
    user.search_for = SearchData(
        expected_items=[
            'audits',
            'job',
            'tasks',
            'bookmark',
            'about',
            module_org.name,
            module_location.name,
        ],
        not_expected_items=[
            '-',
            'dashboard',
            'facts',
            'subscriptions',
            'product',
            'content',
            'sync plan',
            'host',
            'role',
            'compute',
            'domain',
            'user',
            'settings',
            default_org.name,
            default_location.name,
        ],
    )

    yield user

    user.delete()


@pytest.fixture(scope='module')
def admin_user(module_target_sat, module_org, module_location, default_org, default_location):
    """Admin user.
    Expected or not expected data for searching the menu are appended as `search_for` attribute.
    """
    admin_user = module_target_sat.api.User().search(
        query={'search': f'login={settings.server.admin_username}'}
    )[0]
    admin_user.password = settings.server.admin_password
    admin_user.search_for = SearchData(
        expected_items=[
            '-',
            'dashboard',
            'facts',
            'subscriptions',
            'product',
            'content',
            'sync plan',
            'host',
            'role',
            'compute',
            'domain',
            'user',
            'settings',
            'audits',
            'job',
            'tasks',
            'bookmark',
            'about',
            module_org.name,
            module_location.name,
            default_org.name,
            default_location.name,
        ],
        not_expected_items=[],
    )

    return admin_user


@pytest.fixture(scope='module', params=['admin_user', 'auditor_module_user'])
def search_user(request):
    """Parametrized fixture returning defined users for the UI session."""
    return request.getfixturevalue(request.param)


@pytest.mark.tier2
def test_positive_vertical_navigation_search_end_to_end(
    search_user,
    module_target_sat,
    test_name,
):
    """Test the search function of the vertical navigation menu.

    :id: 87660a22-996b-11ee-b8a5-000c2989e153

    :Setup:
        Create a non-admin user with Auditor role.
        Create a custom organization and location.

    :Steps:
        1. Perform a search in the vertical navigation menu with following inputs:
            1a. valid characters
            1b. invalid characters
            1c. current user organization and location
            1d. custom organization and location not assigned to the user
            1e. non-existent menu items (admin user only)
            1f. maximal number of found results (admin user only)
            1g. same search string with various case (admin user only)
        2. Perform the actions as:
            - admin user
            - non-admin user with Auditor role

    :ExpectedResults:
        Admin user:
            1a. should find all matching results
            1b. should not find any results
            1c. should find both results
            1d. should find both results
            1e. should not find any results
            1f. maximal number of found results is 10
            1g. the search is case-insensitive
        User with Auditor role:
            1a. should find all matching results
            1b. should not find any results
            1c. should find both results
            1d. should not find any results

    :Parametrized: yes
    """
    max_search_results_limit = 10

    with module_target_sat.ui_session(
        test_name, search_user.login, search_user.password
    ) as session:
        valid_characters = list(' ')
        invalid_characters = list('.,+=/?!@#$%^&*()[]{}|\\\'"')
        non_existent_menu_items = ['unicorns', 'rainbows']

        search_user.search_for.expected_items.extend(valid_characters)
        search_user.search_for.not_expected_items.extend(
            invalid_characters + non_existent_menu_items
        )

        search = session.bookmark.search_menu
        menu_search_should_find(search, search_user.search_for.expected_items)
        menu_search_should_not_find(search, search_user.search_for.not_expected_items)

        if search_user.admin is True:
            max_results = search(' ')
            assert (
                len(max_results) == max_search_results_limit
            ), f'Maximum number of search results is {max_search_results_limit}, got {len(max_results)}!'

            case_string = 'sTAtUs'
            assert (
                search(case_string) == search(case_string.upper()) == search(case_string.lower())
            ), 'Results for case insensitive search do not match!'
