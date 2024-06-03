"""Test module for EOL tracking

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseComponent: Dashboard

:Team: Endeavour

:CaseImportance: High
"""

from datetime import datetime

import pytest
import requests
import yaml

from robottelo.config import settings
from robottelo.constants import LIFECYCLE_METADATA_FILE
from robottelo.logging import logger


@pytest.mark.tier2
def test_positive_check_eol_date(target_sat):
    """Check if the EOL date for the satellite version

    :id: 1c2f0d19-a357-4461-9ace-edb468f9ca5c

    :expectedresults: EOL date from satellite-lifecycle package is accurate
    """
    current_version = '.'.join(target_sat.version.split('.')[0:2])
    output = yaml.load(target_sat.execute(rf'cat {LIFECYCLE_METADATA_FILE}').stdout, yaml.Loader)
    logger.debug(f'contents of {LIFECYCLE_METADATA_FILE} :{output}')
    eol_datetime = datetime.strptime(output['releases'][current_version]['end_of_life'], '%Y-%m-%d')
    result = requests.get(settings.subscription.lifecycle_api_url, verify=False)
    if result.status_code != 200:
        result.raise_for_status()
    versions = result.json()['data'][0]['versions']
    version = [v for v in versions if v['name'] == current_version]
    if len(version) > 0:
        api_date = [
            (p['date_format'], p['date'])
            for p in version[0]['phases']
            if p['name'] == 'Maintenance support'
        ]
        if api_date[0][0] == 'string':
            assert eol_datetime.strftime("%B, %Y") in api_date[0][1]
        elif api_date[0][0] == 'date':
            assert eol_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z' == api_date[0][1]
        else:
            pytest.fail("Unexpcted date format returned")
    else:
        pytest.skip("The Satellite version is not GA yet")
