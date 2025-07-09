"""Test module for verifying Documentation links

:Requirement: Branding

:CaseAutomation: Automated

:CaseComponent: Branding

:Team: Endeavour

:CaseImportance: High

"""

from collections import defaultdict

import pytest
import requests

from robottelo.config import settings
from robottelo.logging import logger


@pytest.mark.e2e
def test_positive_documentation_links(target_sat):
    """Verify that Satellite documentation links are working.
        Note: At the moment, the test doesn't support verifying links hidden behind a button.
        Currently, the only such link is on RH Cloud > Inventory Upload page.

    :id: 5e6cba22-896a-4d86-95b4-87d0cc2f1cb6

    :Steps:

        1. Gather documentation links present on various Satellite pages.
        2. Verify the links are working (returns 200).

    :expectedresults: All the Documentation links present on Satellite are working
    """
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
    sat_version = ".".join(target_sat.version.split('.')[0:2])
    all_links = defaultdict(list)
    pages_with_broken_links = defaultdict(list)
    with target_sat.ui_session() as session:
        for page in pages:
            page_object = getattr(session, page)
            if page == "host":
                view = page_object.navigate_to(page_object, 'Register')
            elif page == "oscappolicy":
                view = page_object.navigate_to(page_object, 'New')
            else:
                view = page_object.navigate_to(page_object, 'All')
            # Get the doc links present on the page.
            all_links[page] = view.documentation_links()
            assert all_links[page], f"Couldn't find any documentation links on {page} page."
        logger.info(
            f"Following are the documentation links collected from Satellite: \n {all_links}"
        )
        for page in pages:
            for link in all_links[page]:
                # Test stage docs url for Non-GA'ed Satellite
                if float(sat_version) in settings.robottelo.sat_non_ga_versions:
                    # The internal satellite doc url redirects to prod doc that is not available for Non-GA versions.
                    # Get the end url first and then update it in later part of test.
                    if target_sat.hostname in link:
                        link = requests.get(link, verify=False).url
                    link = link.replace(
                        'https://docs.redhat.com', settings.robottelo.stage_docs_url
                    )
                    link = link.replace('html', 'html-single')
                if requests.get(link, verify=False).status_code != 200:
                    pages_with_broken_links[page].append(link)
                    logger.info(f"Following link on {page} page seems broken: \n {link}")
        assert not pages_with_broken_links, (
            f"There are Satellite pages with broken documentation links. \n {print(pages_with_broken_links)}"
        )


@pytest.mark.e2e
def test_positive_upgrade_links(target_sat):
    """Verify that Satellite Upgrade links are present and working.

    :id: 1535c21d-2b75-450d-af63-55d268f8479e

    :Steps:

        1. Gather documentation links present on Administer -> Satellite Upgrade page
        2. Verify the links are working (returns 200).

    :expectedresults: All the Upgrade links present on Satellite are working

    :Verifies: SAT-20700
    """
    with target_sat.ui_session() as session:
        links = session.upgrade.documentation_links()
        # in the future, this should link to a higher version than the current Satellite
        if settings.server.version.release == 'stream':
            x, y, _ = str(target_sat.version).split('.')
            version = f'{x}.{int(y) - 1}'
        else:
            version = '.'.join(str(settings.server.version.release).split('.')[0:2])
        assert (
            f"https://docs.redhat.com/en/documentation/red_hat_satellite/{version}#Upgrade" in links
        )
        assert (
            'https://access.redhat.com/login?redirectTo=https%3A%2F%2Faccess.redhat.com%2Flabs%2Fsatelliteupgradehelper%2F'
            in links
        )
        assert (
            'https://access.redhat.com/products/red-hat-satellite#get-support' in links
            or 'https://access.redhat.com/products/red-hat-satellite/#get-support' in links
        )
