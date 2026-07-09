"""Test Class for hammer ping

:Requirement: Ping

:CaseAutomation: Automated

:CaseComponent: Hammer

:Team: Rocket

:CaseImportance: Critical

"""

import pytest

from robottelo.config import settings
from robottelo.enums import InstallMethod

pytestmark = pytest.mark.destructive


@pytest.fixture(scope='module')
def tomcat_service_teardown(request, module_target_sat):
    service_name = (
        'tomcat.service'
        if settings.server.install_method == InstallMethod.INSTALLER
        else 'candlepin.service'
    )
    assert module_target_sat.execute(f'systemctl stop {service_name}').status == 0

    @request.addfinalizer
    def _finalize():
        assert module_target_sat.execute(f'systemctl start {service_name}').status == 0

    return module_target_sat


def test_negative_cli_ping_fail_status(tomcat_service_teardown):
    """Negative test to verify non-zero status code of CLI ping fail

    :id: 8f8675aa-df52-11eb-9353-b0a460e02491

    :customerscenario: true

    :BZ: 1941240

    :expectedresults: Hammer ping fails and returns non-zero(1) status code.
    """
    result = tomcat_service_teardown.execute('hammer ping')
    assert result.status == 1


def test_negative_api_ping_fail_status(tomcat_service_teardown):
    """Negative test to verify FAIL status when API ping fail

    :id: 6bd2c552-29d7-4f49-81dd-f8d5ff0e7c39

    :customerscenario: true

    :BZ: 1835122

    :CaseComponent: API

    :expectedresults: API ping fails and shows FAIL status.
    """
    response = tomcat_service_teardown.api.Ping().search_json()
    assert response['results']['katello']['status'] == 'FAIL'
