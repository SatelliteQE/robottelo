"""Tests related to hammer command and its options and subcommands.

:Requirement: Hammer

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hammer

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import io
import json
import re

import pytest
from fauxfactory import gen_string

from robottelo import ssh
from robottelo.cli import hammer
from robottelo.cli.admin import Admin
from robottelo.cli.defaults import Defaults
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.helpers import read_data_file
from robottelo.test import CLITestCase
from robottelo.utils.issue_handlers import is_open


HAMMER_COMMANDS = json.loads(read_data_file('hammer_commands.json'))


def _fetch_command_info(command):
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


def _format_commands_diff(commands_diff):
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


class HammerCommandsTestCase(CLITestCase):
    """Tests for ensuring that  all expected hammer subcommands and its options
    are present.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.differences = {}

    def _traverse_command_tree(self):
        """Walk through the hammer commands tree and assert that the expected
        options are present.

        """
        raw_output = ssh.command('hammer full-help', output_format='plain').stdout
        commands = re.split('.*\n(?=hammer.*\n^[-]+)', raw_output, flags=re.M)
        commands.pop(0)  # remove "Hammer CLI help" line
        for raw_command in commands:
            raw_command = raw_command.splitlines()
            command = raw_command.pop(0).replace(' >', '')
            output = hammer.parse_help(raw_command)
            command_options = {option['name'] for option in output['options']}
            command_subcommands = {subcommand['name'] for subcommand in output['subcommands']}
            expected = _fetch_command_info(command)
            expected_options = set()
            expected_subcommands = set()

            if expected is not None:
                expected_options = {option['name'] for option in expected['options']}
                expected_subcommands = {
                    subcommand['name'] for subcommand in expected['subcommands']
                }
            if is_open('BZ:1666687'):
                cmds = ['hammer report-template create', 'hammer report-template update']
                if command in cmds:
                    command_options.add('interactive')
                if 'hammer virt-who-config fetch' in command:
                    command_options.add('output')
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
                self.differences[command] = diff

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_all_options(self):
        """check all provided options for every hammer command

        :id: 1203ab9f-896d-4039-a166-9e2d36925b5b

        :expectedresults: All expected options are present

        :CaseImportance: Critical
        """
        self.maxDiff = None
        self._traverse_command_tree()
        if self.differences:
            self.fail('\n' + _format_commands_diff(self.differences))


class HammerTestCase(CLITestCase):
    """Tests related to hammer sub options. """

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.run_in_one_thread
    def test_positive_disable_hammer_defaults(self):
        """Verify hammer disable defaults command.

        :id: d0b65f36-b91f-4f2f-aaf8-8afda3e23708

        :steps:
            1. Add hammer defaults as organization-id.
            2. Verify hammer product list successful.
            3. Run hammer --no-use-defaults product list.

        :expectedresults: Hammer --no-use-defaults product list should fail.

        :CaseImportance: Critical

        :BZ: 1640644, 1368173
        """
        default_org = make_org()
        default_product_name = gen_string('alpha')
        make_product({'name': default_product_name, 'organization-id': default_org['id']})
        try:
            Defaults.add({'param-name': 'organization_id', 'param-value': default_org['id']})
            # list templates for BZ#1368173
            result = ssh.command('hammer job-template list')
            assert result.return_code == 0
            # Verify --organization-id is not required to pass if defaults are set
            result = ssh.command('hammer product list')
            assert result.return_code == 0
            # Verify product list fail without using defaults
            result = ssh.command('hammer --no-use-defaults product list')
            assert result.return_code != 0
            assert default_product_name not in "".join(result.stdout)
            # Verify --organization-id is not required to pass if defaults are set
            result = ssh.command('hammer --use-defaults product list')
            assert result.return_code == 0
            assert default_product_name in "".join(result.stdout)
        finally:
            Defaults.delete({'param-name': 'organization_id'})
            result = ssh.command('hammer defaults list')
            assert default_org['id'] not in "".join(result.stdout)

    @pytest.mark.tier1
    def test_positive_check_debug_log_levels(self):
        """Enabling debug log level in candlepin via hammer logging

        :id: 029c80f1-2bc5-494e-a04a-7d6beb0f769a

        :expectedresults: Verify enabled debug log level

        :CaseImportance: Medium

        :BZ: 1760773
        """
        Admin.logging({"all": True, "level-debug": True})
        # Verify value of `log4j.logger.org.candlepin` as `DEBUG`
        result = ssh.command("grep DEBUG /etc/candlepin/candlepin.conf")
        assert result.return_code == 0
        assert 'log4j.logger.org.candlepin = DEBUG' in result.stdout

        Admin.logging({"all": True, "level-production": True})
        # Verify value of `log4j.logger.org.candlepin` as `WARN`
        result = ssh.command("grep WARN /etc/candlepin/candlepin.conf")
        assert result.return_code == 0
        assert 'log4j.logger.org.candlepin = WARN' in result.stdout
