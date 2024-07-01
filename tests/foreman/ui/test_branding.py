"""Tests for branding

:Requirement: Branding

:CaseAutomation: Automated

:CaseComponent: Branding

:Team: Platform

:CaseImportance: High

"""

import pytest


@pytest.mark.e2e
@pytest.mark.skip_if_open("BZ:2105949")
def test_verify_satellite_login_screen_info(target_sat):
    """Verify Satellite version on the login screen

    :id: f48110ad-29b4-49b1-972a-a70075a05732

    :steps: Get the info from the login screen

    :expectedresults:
        1. Correct Satellite version
        2. If 'Beta' is present, should fail until a GA snap is received

    :BZ: 1315849, 1367495, 1372436, 1502098, 1540710, 1582476, 1724738,
         1959135, 2076979, 1687250, 1686540, 1742872, 1805642, 2105949
    """
    with target_sat.ui_session(login=False) as session:
        version = session.login.read_sat_version()
    assert f'Version {target_sat.version}' == version['login_text']
    assert 'Beta' not in version['login_text'], '"Beta" should not be there'
