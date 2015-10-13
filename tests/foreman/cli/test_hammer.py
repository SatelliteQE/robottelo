"""Tests related to hammer command and its options and subcommands."""
import json

from robottelo import ssh
from robottelo.cli import hammer
from robottelo.decorators import bz_bug_is_open
from robottelo.helpers import read_data_file
from robottelo.test import CLITestCase

HAMMER_COMMANDS = json.loads(read_data_file('hammer_commands.json'))


class HammerCommandsTestCase(CLITestCase):
    """Tests for ensuring that  all expected hammer subcommands and its options
    are present.

    """
    def __init__(self, *args, **kwargs):
        super(HammerCommandsTestCase, self).__init__(*args, **kwargs)
        self.differences = {}

    # pylint: disable=no-self-use
    def _fetch_command_info(self, command):
        """Fetch command info from expected commands info dictionary."""
        info = HAMMER_COMMANDS
        if command != 'hammer':
            found = False
            parts = command.split(' ')[1:]  # exclude hammer
            for part in parts:
                for command in info['subcommands']:
                    if command['name'] == part:
                        info = command
                        found = True
                        break
            if not found:
                return None
        return info

    def _traverse_command_tree(self, command):
        """Recursively walk through the hammer commands tree and assert that
        the expected options are present.

        """
        output = hammer.parse_help(
            ssh.command('{0} --help'.format(command)).stdout
        )
        command_options = set([option['name'] for option in output['options']])
        command_subcommands = set(
            [subcommand['name'] for subcommand in output['subcommands']]
        )
        if 'discovery_rule' in command and bz_bug_is_open(1219610):
            # Adjust the discovery_rule subcommand name. The expected data is
            # already with the naming convetion name
            expected = self._fetch_command_info(
                command.replace('discovery_rule', 'discovery-rule'))
        else:
            expected = self._fetch_command_info(command)
        expected_options = set()
        expected_subcommands = set()

        if expected is not None:
            expected_options = set(
                [option['name'] for option in expected['options']]
            )
            expected_subcommands = set(
                [subcommand['name'] for subcommand in expected['subcommands']]
            )

        if command == 'hammer' and bz_bug_is_open(1219610):
            # Adjust the discovery_rule subcommand name
            command_subcommands.discard('discovery_rule')
            command_subcommands.add('discovery-rule')

        added_options = tuple(command_options - expected_options)
        removed_options = tuple(expected_options - command_options)
        added_subcommands = tuple(command_subcommands - expected_subcommands)
        removed_subcommands = tuple(expected_subcommands - command_subcommands)

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

        if len(output['subcommands']) > 0:
            for subcommand in output['subcommands']:
                self._traverse_command_tree(
                    '{0} {1}'.format(command, subcommand['name'])
                )

    def test_hammer_options(self):
        """@Test: check all provided options for every hammer command

        @Feature: Hammer

        @Assert: All expected options are present

        """
        self.maxDiff = None
        self._traverse_command_tree('hammer')
        if self.differences:
            self.fail(
                json.dumps(self.differences, indent=True, sort_keys=True)
            )
