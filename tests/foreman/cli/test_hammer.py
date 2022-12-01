"""Tests related to hammer command and its options and subcommands.

:Requirement: Hammer

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hammer

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import io
import json
import re
import time

import pytest

from robottelo.cli import hammer
from robottelo.constants import DataFile
from robottelo.logging import logger


HAMMER_COMMANDS = json.loads(DataFile.HAMMER_COMMANDS_JSON.read_text())

pytestmark = [pytest.mark.tier1, pytest.mark.upgrade, pytest.mark.e2e]


def fetch_command_info(command):
    """Fetch command info from expected commands info dictionary."""
    info = HAMMER_COMMANDS
    if command != 'hammer':
        found = []
        parts = command.split(' ')[1:]  # exclude hammer
        for part in parts:
            for command in info['subcommands']:
                if command['name'] == part:
                    found.append(part)
                    info = command
                    break
        if found != parts:
            return None
    return info


def format_commands_diff(commands_diff):
    """Format the commands differences into a human readable format."""
    output = io.StringIO()
    for key, value in sorted(commands_diff.items()):
        if key == 'hammer':
            continue
        output.write('{}{}\n'.format(key, ' (new command)' if value['added_command'] else ''))
        if value.get('added_subcommands'):
            output.write('  Added subcommands:\n')
            for subcommand in value.get('added_subcommands'):
                output.write(f'    * {subcommand}\n')
        if value.get('added_options'):
            output.write('  Added options:\n')
            for option in value.get('added_options'):
                output.write(f'    * {option}\n')
        if value.get('removed_subcommands'):
            output.write('  Removed subcommands:')
            for subcommand in value.get('removed_subcommands'):
                output.write(f'    * {subcommand}')
        if value.get('removed_options'):
            output.write('  Removed options:\n')
            for option in value.get('removed_options'):
                output.write(f'    * {option}\n')
        output.write('\n')
    output_value = output.getvalue()
    output.close()
    return output_value


def test_positive_all_options(target_sat):
    """check all provided options for every hammer command

    :id: 1203ab9f-896d-4039-a166-9e2d36925b5b

    :expectedresults: All expected options are present
    """
    differences = {}
    raw_output = target_sat.execute('hammer full-help').stdout
    commands = re.split(r'.*\n(?=hammer.*\n^[-]+)', raw_output, flags=re.M)
    commands.pop(0)  # remove "Hammer CLI help" line
    for raw_command in commands:
        command = raw_command.splitlines().pop(0).replace(' >', '')
        output = hammer.parse_help(raw_command)
        command_options = {option['name'] for option in output['options']}
        command_subcommands = {subcommand['name'] for subcommand in output['subcommands']}
        expected = fetch_command_info(command)
        expected_options = set()
        expected_subcommands = set()

        if expected is not None:
            expected_options = {option['name'] for option in expected['options']}
            expected_subcommands = {subcommand['name'] for subcommand in expected['subcommands']}
        added_options = tuple(command_options - expected_options)
        removed_options = tuple(expected_options - command_options)
        added_subcommands = tuple(command_subcommands - expected_subcommands)
        removed_subcommands = tuple(expected_subcommands - command_subcommands)

        if added_options or added_subcommands or removed_options or removed_subcommands:
            diff = {'added_command': expected is None}
            if added_options:
                diff['added_options'] = added_options
            if removed_options:
                diff['removed_options'] = removed_options
            if added_subcommands:
                diff['added_subcommands'] = added_subcommands
            if removed_subcommands:
                diff['removed_subcommands'] = removed_subcommands
            differences[command] = diff

    if differences:
        pytest.fail(format_commands_diff(differences))


def test_positive_disable_hammer_defaults(request, function_product, target_sat):
    """Verify hammer disable defaults command.

    :id: d0b65f36-b91f-4f2f-aaf8-8afda3e23708

    :steps:
        1. Add hammer defaults as organization-id.
        2. Verify hammer product list successful.
        3. Run hammer --no-use-defaults product list.

    :expectedresults: Hammer --no-use-defaults product list should fail.

    :BZ: 1640644, 1368173
    """
    target_sat.cli.Defaults.add(
        {'param-name': 'organization_id', 'param-value': function_product.organization.id}
    )
    # list templates for BZ#1368173
    result = target_sat.execute('hammer job-template list')
    assert result.status == 0
    # Verify --organization-id is not required to pass if defaults are set
    result = target_sat.execute('hammer product list')
    assert result.status == 0
    # Verify product list fail without using defaults
    result = target_sat.execute('hammer --no-use-defaults product list')
    assert result.status != 0
    assert function_product.name not in result.stdout
    # Verify --organization-id is not required to pass if defaults are set
    result = target_sat.execute('hammer --use-defaults product list')
    assert result.status == 0
    assert function_product.name in result.stdout

    @request.addfinalizer
    def _finalize():
        target_sat.cli.Defaults.delete({'param-name': 'organization_id'})
        result = target_sat.execute('hammer defaults list')
        assert str(function_product.organization.id) not in result.stdout


def test_positive_check_debug_log_levels(target_sat):
    """Enabling debug log level in candlepin via hammer logging

    :id: 029c80f1-2bc5-494e-a04a-7d6beb0f769a

    :expectedresults: Verify enabled debug log level

    :customerscenario: true

    :CaseImportance: Medium

    :BZ: 1760773
    """
    target_sat.cli.Admin.logging({'all': True, 'level-debug': True})
    # Verify value of `log4j.logger.org.candlepin` as `DEBUG`
    result = target_sat.execute('grep DEBUG /etc/candlepin/candlepin.conf')
    assert result.status == 0
    assert 'log4j.logger.org.candlepin = DEBUG' in result.stdout

    target_sat.cli.Admin.logging({"all": True, "level-production": True})
    # Verify value of `log4j.logger.org.candlepin` as `WARN`
    result = target_sat.execute('grep WARN /etc/candlepin/candlepin.conf')
    assert result.status == 0
    assert 'log4j.logger.org.candlepin = WARN' in result.stdout


def test_positive_hammer_shell(target_sat):
    """Verify that hammer shell runs a command when input is provided via interactive/bash

    :id: 4e5db106-65ca-11ed-9054-07f7387bd580

    :steps:
        1. Run any command in hammer shell

    :expectedresults: hammer shell should run a command

    :BZ: 2053843
    """
    command = 'user list --organization-id 1 --fields login'
    # Verify hammer shell runs a command with interactive input
    with target_sat.session.shell() as sh:
        sh.send('hammer shell')
        time.sleep(5)
        sh.send(command)
        time.sleep(5)
    logger.info(sh.result)
    assert 'admin' in sh.result.stdout

    # Verify hammer shell runs a command with bash input
    result = target_sat.execute(f'echo "{command}" | hammer shell')
    assert 'admin' in result.stdout
    assert 'stty: invalid argument' not in result.stdout
