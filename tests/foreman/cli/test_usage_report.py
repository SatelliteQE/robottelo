"""Tests related to the satellite usage report

:Requirement: Hammer

:CaseAutomation: Automated

:CaseComponent: Reporting

:Team: Endeavour

:CaseImportance: Critical

"""

from datetime import datetime

from fauxfactory import gen_string
import pytest

from pytest_fixtures.component.usage_report import process_keys

pytestmark = pytest.mark.destructive


def compare_report_keys(report_keys, expected_keys):
    if report_keys != expected_keys:
        added_items = report_keys - expected_keys
        removed_items = expected_keys - report_keys
        pytest.fail(
            f'Report field mismatch: added items: {added_items}, removed items: {removed_items}'
        )


def test_positive_usage_report_items(module_target_sat, module_report_keys, module_expected_keys):
    """check all expected entries are present in usage report

    :id: fe03c15f-4cd3-4282-988f-28112e60a909

    :expectedresults: All expected top-level entries are present

    """
    compare_report_keys(module_report_keys, module_expected_keys)


def test_positive_condensed_report(
    module_target_sat, module_generated_report, module_expected_keys_condensed
):
    """Check condensed usage report is created both from scratch and from full report

    :id: f11e5392-0a93-43a6-bda2-dc7cf62ba5f6

    :verifies: SAT-30439

    :expectedresults: Condensed report is created correctly and contains expected keys

    """
    cond_report_from_scratch = (
        f'cr_new-{datetime.timestamp(datetime.now())}-{gen_string("alphanumeric")}.yml'
    )
    cond_report_from_full_report = (
        f'cr_cond-{datetime.timestamp(datetime.now())}-{gen_string("alphanumeric")}.yml'
    )
    result = module_target_sat.cli.SatelliteMaintainReport.condense(
        {'output': cond_report_from_scratch}
    )
    assert result.status == 0, 'failed to generate condensed report from scratch'
    result = module_target_sat.cli.SatelliteMaintainReport.condense(
        {'input': module_generated_report, 'output': cond_report_from_full_report}
    )
    assert result.status == 0, 'failed to generate condensed report from the full report'
    cond_report = module_target_sat.load_remote_yaml_file(cond_report_from_scratch)
    assert cond_report == module_target_sat.load_remote_yaml_file(cond_report_from_full_report)
    cond_report_keys = process_keys(cond_report)
    compare_report_keys(cond_report_keys, module_expected_keys_condensed)


def test_positive_max_age(module_target_sat):
    """Check that max age setting is respected when generating condensed report

    :id: 83899ae2-19df-4d68-a4d9-be49ddc24fde

    :expectedresults: Max age setting takes effect

    """
    key = 'advisor_on_prem_remediations_count'
    key_cond = f'foreman.{key}'
    server_value = int(module_target_sat.get_reported_condensed_value(key_cond))
    test_value = (server_value + 1) * 2
    test_report = f'test_report-{datetime.timestamp(datetime.now())}-{gen_string("alphanumeric")}'
    test_report_cond = (
        f'test_report_cond-{datetime.timestamp(datetime.now())}-{gen_string("alphanumeric")}'
    )
    module_target_sat.execute(f"echo '{key}: {test_value}' > {test_report}")

    result = module_target_sat.cli.SatelliteMaintainReport.condense(
        {'input': test_report, 'output': test_report_cond}
    )
    assert result.status == 0, 'failed to create condensed report'
    report = module_target_sat.load_remote_yaml_file(test_report_cond)
    assert report.get(key_cond) == test_value, (
        'condensed test report does not contain expected value'
    )

    result = module_target_sat.cli.SatelliteMaintainReport.condense(
        {'input': test_report, 'output': test_report_cond, 'max-age': 0}
    )
    assert result.status == 0, 'failed to create condensed report'
    report = module_target_sat.load_remote_yaml_file(test_report_cond)
    assert report.get(key_cond) == server_value, 'test report does not contain expected value'


def test_positive_report_services(
    module_target_sat, module_expected_keys, module_expected_keys_condensed
):
    """Check condense and generate systemd timers and services

    :id: 2e4757a4-2815-4665-9012-c0a5daa396fd

    :expectedresults: Condense and generate timers are enabled and listed in the timers list,
        condense and generate services create expected files when run

    """
    generate_unit_name = 'satellite-usage-metrics-generate'
    condense_unit_name = 'satellite-usage-metrics-condense'
    generate_output_file = '/var/lib/foreman-maintain/satellite_metrics.yml'
    condense_output_file = '/etc/rhsm/facts/foreman.facts'

    # check that timers are enabled and listed in the timers list
    result = module_target_sat.execute(f'systemctl status {generate_unit_name}.timer')
    assert result.status == 0, f'{generate_unit_name}.timer is not enabled'
    result = module_target_sat.execute(f'systemctl status {condense_unit_name}.timer')
    assert result.status == 0, f'{condense_unit_name}.timer is not enabled'
    result = module_target_sat.execute('systemctl list-timers')
    assert f'{generate_unit_name}.timer' in result.stdout, f'{generate_unit_name}.timer not found'
    assert f'{condense_unit_name}.timer' in result.stdout, f'{condense_unit_name}.timer not found'

    # check that generate service creates expected file
    result = module_target_sat.execute(f'systemctl start {generate_unit_name}.service')
    assert result.status == 0, f'{generate_unit_name}.service did not run'
    report = module_target_sat.load_remote_yaml_file(generate_output_file)
    report_keys = process_keys(report)
    compare_report_keys(report_keys, module_expected_keys)

    # check that condense service creates expected file
    result = module_target_sat.execute(f'systemctl start {condense_unit_name}.service')
    assert result.status == 0, f'{condense_unit_name}.service did not run'
    cond_report = module_target_sat.load_remote_yaml_file(condense_output_file)
    cond_report_keys = process_keys(cond_report)
    compare_report_keys(cond_report_keys, module_expected_keys_condensed)
