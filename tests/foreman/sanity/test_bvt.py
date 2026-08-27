"""Build Validation tests

:Requirement: Sanity

:CaseAutomation: Automated

:CaseComponent: BVT

:Team: JPL

:CaseImportance: Critical

"""

import re

import pytest

from robottelo.config import settings
from robottelo.utils.ohsnap import ohsnap_snap_rpms

pytestmark = [pytest.mark.build_sanity]

def test_all_interfaces_are_accessible(target_sat):
    """API, CLI and UI interfaces are accessible

    :id: 0a212120-8e49-4489-a1a4-4272004e16dc

    :expectedresults: All three satellite interfaces are accessible
    """
    errors = {}
    # API Interface
    try:
        api_org = target_sat.api.Organization(id=1).read()
        assert api_org
        assert api_org.name == 'Default Organization'
    except Exception as api_exc:
        errors['api'] = api_exc

    # CLI Interface
    try:
        cli_org = target_sat.cli.Org.info({'id': 1})
        assert cli_org
        assert cli_org['name'] == 'Default Organization'
    except Exception as cli_exc:
        errors['cli'] = cli_exc

    # UI Interface
    try:
        with target_sat.ui_session() as session:
            ui_org = session.organization.read('Default Organization', widget_names='primary')
            assert ui_org
            assert ui_org['primary']['name'] == 'Default Organization'
    except Exception as ui_exc:
        errors['ui'] = ui_exc

    # Final Exception
    if errors:
        pytest.fail(
            '\n'.join(
                [
                    f'Interface {interface} interaction failed with error {err}'
                    for interface, err in errors.items()
                ]
            )
        )
    assert True
