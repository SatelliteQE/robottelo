"""Tests related to the satellite usage report

:Requirement: Hammer

:CaseAutomation: Automated

:CaseComponent: Hammer

:Team: Endeavour

:CaseImportance: Critical

"""

import filecmp

from fauxfactory import gen_string
import pytest


def test_positive_usage_report_items(module_target_sat, module_report_keys, module_expected_keys):
    """check all expected entries are present in usage report

    :id: fe03c15f-4cd3-4282-988f-28112e60a909

    :expectedresults: All expected top-level entries are present

    """
    if module_report_keys != module_expected_keys:
        added_items = module_report_keys - module_expected_keys
        removed_items = module_expected_keys - module_report_keys
        pytest.fail(
            f'Report field mismatch: added items: {added_items}, removed items: {removed_items}'
        )


def test_positive_condensed_report(
    module_target_sat, module_generated_report, module_expected_keys_condensed
):
    """Check condensed usage report is created both from scratch and from full report

    :id: f11e5392-0a93-43a6-bda2-dc7cf62ba5f6

    :verifies: SAT-30439

    :expectedresults: Condensed report is created correctly and contains expected keys

    """
    cond_report_from_scratch = f'cr_new-{gen_string("alphanumeric")}.yml'
    cond_report_from_full_report = f'cr_cond-{gen_string("alphanumeric")}.yml'
    result = module_target_sat.execute(
        f'satellite-maintain report condense --output {cond_report_from_scratch}'
    )
    assert result.status == 0, 'failed to generate condensed report from scratch'
    result = module_target_sat.execute(
        f'satellite-maintain report condense --input {module_generated_report} --output {cond_report_from_full_report}'
    )
    assert result.status == 0, 'failed to generate condensed report from the full report'
    assert filecmp.cmp(cond_report_from_full_report, cond_report_from_scratch), (
        'condensed report mismatch'
    )
    assert (
        module_target_sat.load_remote_yaml_file(cond_report_from_scratch).keys()
        == module_expected_keys_condensed
    )


# TODO something for --max-age
def test_positive_condense_service(module_target_sat):
    """satellite-usage-metrics-condense

    :id: 83899ae2-19df-4d68-a4d9-be49ddc24fde

    :expectedresults:

    """
    result = module_target_sat.execute('systemctl status satellite-usage-metrics-condense')
    assert result.status == 0, ''
