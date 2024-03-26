"""Test module for EOL tracking

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Dashboard

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime

import pytest
import requests
import yaml

from robottelo.config import settings
from robottelo.constants import LIFECYCLE_METADATA_FILE


@pytest.mark.tier2
def test_positive_check_eol_date(target_sat):
    """Check if the EOL date for the satellite version

    :id: 0ce6c11c-d969-4e7e-a934-cd1683de62a3

    :expectedresults: EOL date from satellite-lifecycle package is accurate
    """
    current_version = '.'.join(target_sat.version.split('.')[0:2])
    output = yaml.load(target_sat.execute(rf'cat {LIFECYCLE_METADATA_FILE}').stdout, yaml.Loader)
    eol_datetime = datetime.strptime(output['releases'][current_version]['end_of_life'], '%Y-%m-%y')
    result = requests.get(settings.subscription.lifecycle_api_url, verify=False)
    if result.status_code != 200:
        raise requests.HTTPError(f'{settings.subscription.lifecycle_api_url} is not accessible')
    versions = result.json()['data'][0]['versions']
    version = [v for v in versions if v['name'] == current_version]
    api_date = [
        (p['date_format'], p['date'])
        for p in version[0]['phases']
        if p['name'] == 'Maintenance support'
    ]
    if api_date[0][0] == 'string':
        assert eol_datetime.strftime("%B, %Y") in api_date[0][1]
    if api_date[0][0] == 'date':
        assert eol_datetime.strftime("%B, %Y") in api_date[0][1].strftime("%B, %Y")
