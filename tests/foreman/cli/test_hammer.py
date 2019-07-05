"""Tests related to hammer command and its options and subcommands.

:Requirement: Hammer

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hammer

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json
import re

from robottelo import ssh
from robottelo.cli import hammer
from robottelo.decorators import bz_bug_is_open, tier1, upgrade
from robottelo.helpers import read_data_file
from robottelo.test import CLITestCase
from six import StringIO

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
    output = StringIO()
    for key, value in sorted(commands_diff.items()):
        if key == 'hammer':
            continue
        output.write('{}{}\n'.format(
            key,
            ' (new command)' if value['added_command'] else ''
        ))
        if value.get('added_subcommands'):
            output.write('  Added subcommands:\n')
            for subcommand in value.get('added_subcommands'):
                output.write('    * {}\n'.format(subcommand))
        if value.get('added_options'):
            output.write('  Added options:\n')
            for option in value.get('added_options'):
                output.write('    * {}\n'.format(option))
        if value.get('removed_subcommands'):
            output.write('  Removed subcommands:')
            for subcommand in value.get('removed_subcommands'):
                output.write('    * {}'.format(subcommand))
        if value.get('removed_options'):
            output.write('  Removed options:\n')
            for option in value.get('removed_options'):
                output.write('    * {}\n'.format(option))
        output.write('\n')
    output_value = output.getvalue()
    output.close()
    return output_value


class HammerCommandsTestCase(CLITestCase):
    """Tests for ensuring that  all expected hammer subcommands and its options
    are present.

    """
    def __init__(self, *args, **kwargs):
        super(HammerCommandsTestCase, self).__init__(*args, **kwargs)
        self.differences = {}

    def _traverse_command_tree(self):
        """Walk through the hammer commands tree and assert that the expected
        options are present.

        """
        raw_output = ssh.command(
            'hammer full-help', output_format='plain').stdout
        commands = re.split('.*\n(?=hammer.*\n^[-]+)', raw_output, flags=re.M)
        commands.pop(0)  # remove "Hammer CLI help" line
        for raw_command in commands:
            raw_command = raw_command.splitlines()
            command = raw_command.pop(0).replace(' >', '')
            output = hammer.parse_help(raw_command)
            command_options = set([
                option['name'] for option in output['options']])
            command_subcommands = set(
                [subcommand['name'] for subcommand in output['subcommands']]
            )
            expected = _fetch_command_info(command)
            expected_options = set()
            expected_subcommands = set()

            if expected is not None:
                expected_options = set(
                    [option['name'] for option in expected['options']]
                )
                expected_subcommands = set([
                    subcommand['name']
                    for subcommand in expected['subcommands']
                ])
            # Below code is added as workaround for Bug 1666687
            if bz_bug_is_open(1666687):
                cmds = ['hammer report-template create', 'hammer report-template update']
                if command in cmds:
                    command_options.add('interactive')
                if 'hammer virt-who-config fetch' in command:
                    command_options.add('output')
            # Below code is added as workaround for Bug 1655513 on Sat 6.4 release
            # This will neglect null entry added for hammer ansible roles command
            if bz_bug_is_open(1655513) and 'hammer ansible roles ' in command and 'help' in (
                    command_options - expected_options):
                expected_options.add("help")
            added_options = tuple(command_options - expected_options)
            removed_options = tuple(expected_options - command_options)
            added_subcommands = tuple(
                command_subcommands - expected_subcommands)
            removed_subcommands = tuple(
                expected_subcommands - command_subcommands)

            if (added_options or added_subcommands or removed_options or
                    removed_subcommands):
                diff = {
                    'added_command': expected is None,
                }
                if added_options:
                    diff['added_options'] = added_options
                if removed_options:
                    diff['removed_options'] = removed_options
                if added_subcommands:
                    diff['added_subcommands'] = added_subcommands
                if removed_subcommands:
                    diff['removed_subcommands'] = removed_subcommands
                self.differences[command] = diff

    @tier1
    @upgrade
    def test_positive_all_options(self):
        """check all provided options for every hammer command

        :id: 1203ab9f-896d-4039-a166-9e2d36925b5b

        :expectedresults: All expected options are present

        :CaseImportance: Critical
        """
        self.maxDiff = None
        self._traverse_command_tree()
        if self.differences:
            self.fail(
                '\n' + _format_commands_diff(self.differences)
            )
