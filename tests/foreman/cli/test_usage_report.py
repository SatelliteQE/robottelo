"""Tests related to the satellite usage report

:Requirement: Hammer

:CaseAutomation: Automated

:CaseComponent: Reporting

:Team: Endeavour

:CaseImportance: Critical

"""

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
