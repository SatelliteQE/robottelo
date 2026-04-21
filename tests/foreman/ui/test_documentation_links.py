"""Test module for verifying Documentation links

:Requirement: Branding

:CaseAutomation: Automated

:CaseComponent: Branding

:Team: Endeavour

:CaseImportance: High

"""

import pytest
import requests

from robottelo.config import settings
from robottelo.logging import logger

pages = [
    'about',
    'settings',
    'bookmark',
    'role',
    'ldapauthentication',
    'cloudinventory',
    'ansiblevariables',
    'ansibleroles',
    'discoveryrule',
    'global_parameter',
    'oscapreport',
    'oscappolicy',
    'oscapcontent',
    'jobtemplate',
    'provisioningtemplate',
    'partitiontable',
    'operatingsystem',
    'host',
    'discoveredhosts',
    'reporttemplate',
    'configreport',
    'jobinvocation',
    'audit',
    'factvalue',
    'dashboard',
]

exceptions = {
    'about': [
        'https://access.redhat.com/',
        'https://www.redhat.com/en/blog/channel/red-hat-satellite',
    ],
    'cloudinventory': ['https://www.redhat.com/en/topics/management/data-application-security'],
}


@pytest.fixture(scope='module')
def session(module_target_sat):
    """Helper function to create a session for testing documentation links."""
    with module_target_sat.ui_session() as session:
        yield session


@pytest.fixture(scope='module')
def custom_docs_url_setting(request, module_target_sat):
    """Optionally set a custom satellite_documentation_url Satellite setting.

    When parametrized with ``True``, reads the custom URL from
    ``robottelo.custom_docs_url`` in robottelo.yaml, applies it to
    the Satellite setting, and reverts the setting to its original value after
    all tests in the module finish.

    When parametrized with ``False`` the setting is left unchanged (default).
    """
    if not request.param:
        yield None
        return
    if not settings.robottelo.custom_docs_url:
        pytest.skip('robottelo.custom_docs_url is not set in robottelo.yaml')
    setting_obj = module_target_sat.api.Setting().search(
        query={'search': 'name=satellite_documentation_url'}
    )[0]
    original_value = setting_obj.value or ''
    setting_obj.value = settings.robottelo.custom_docs_url
    setting_obj.update({'value'})
    yield settings.robottelo.custom_docs_url
    setting_obj.value = original_value
    setting_obj.update({'value'})


@pytest.mark.parametrize('page', pages)
@pytest.mark.parametrize(
    'custom_docs_url_setting',
    [
        pytest.param(False, id='default_url'),
        pytest.param(True, id='custom_url'),
    ],
    indirect=True,
)
@pytest.mark.e2e
def test_positive_documentation_links(module_target_sat, session, custom_docs_url_setting, page):
    """Verify that Satellite documentation links are working.
        Note: At the moment, the test doesn't support verifying links hidden behind a button.
        Currently, the only such link is on RH Cloud > Inventory Upload page.

    :id: 5e6cba22-896a-4d86-95b4-87d0cc2f1cb6

    :Steps:

        1. Gather documentation links present on various Satellite pages.
        2. Verify the links are working (returns 200). If Custom URL is set also check that it was applied

    :expectedresults: All the Documentation links present on Satellite are working
    """
    sat_version = ".".join(module_target_sat.version.split('.')[0:2])
    all_links = []
    broken_links = []
    page_object = getattr(session, page)
    if page == "host":
        view = page_object.navigate_to(page_object, 'Register')
    elif page == "oscappolicy":
        view = page_object.navigate_to(page_object, 'New')
    else:
        view = page_object.navigate_to(page_object, 'All')
    # Get the doc links present on the page.
    all_links = view.documentation_links()
    assert all_links, f"Couldn't find any documentation links on {page} page."
    logger.info(f"Following are the documentation links collected from Satellite: \n {all_links}")
    for link in all_links:
        # Test stage docs url for Non-GA'ed Satellite
        if (
            float(sat_version) in settings.robottelo.sat_non_ga_versions
            and not custom_docs_url_setting
        ):
            # The internal satellite doc url redirects to prod doc that is not available for Non-GA versions.
            # Get the end url first and then update it in later part of test.
            # This does not apply when custom URL is set
            if module_target_sat.hostname in link:
                link = requests.get(link, verify=False).url
            link = link.replace('https://docs.redhat.com', settings.robottelo.stage_docs_url)
        if requests.get(link, verify=False).status_code != 200:
            broken_links.append(link)
            logger.info(f"Following link on {page} page seems broken: \n {link}")
        # If Custom URL is configured, check if it is applied, allow pre-defined exceptions
        if (
            custom_docs_url_setting
            and custom_docs_url_setting not in link
            and not (page in exceptions and link in exceptions[page])
        ):
            broken_links.append(link)
            logger.info(
                f"Following link on {page} does not comply with custom url setting: \n {link}"
            )
    assert not broken_links, (
        f"There are broken documentation links on page \"{page}\": \n {broken_links}"
    )


@pytest.mark.e2e
def test_positive_upgrade_links(target_sat):
    """Verify that Satellite Upgrade links are present and working.

    :id: 1535c21d-2b75-450d-af63-55d268f8479e

    :Steps:

        1. Gather documentation links present on Administer -> Satellite Upgrade page
        2. Verify the links are working (returns 200).

    :expectedresults: All the Upgrade links present on Satellite are working

    :Verifies: SAT-20700, SAT-35235
    """
    with target_sat.ui_session() as session:
        links = session.upgrade.documentation_links()
        assert (
            'https://access.redhat.com/login?redirectTo=https%3A%2F%2Faccess.redhat.com%2Flabs%2Fsatelliteupgradehelper%2F'
            in links
        )
        assert (
            'https://access.redhat.com/products/red-hat-satellite#get-support' in links
            or 'https://access.redhat.com/products/red-hat-satellite/#get-support' in links
        )
