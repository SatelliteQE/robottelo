"""Tests related to hammer command and its options and subcommands."""
import json

from robottelo.cli import hammer
from robottelo.common import ssh
from robottelo.common.helpers import read_data_file
from robottelo.test import CLITestCase

HAMMER_COMMANDS = json.loads(read_data_file('hammer_commands.json'))


class HammerCommandsTestCase(CLITestCase):
    """Tests for ensuring that  all expected hammer subcommands and its options
    are present.

    """
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
                self.fail(
                    'Was not possible to fetch information for "{0}" command.'
                    .format(command)
                )
        return info

    def _traverse_command_tree(self, command):
        """Recursively walk through the hammer commands tree and assert that
        the expected options are present.

        """
        output = hammer.parse_help(
            ssh.command('{0} --help'.format(command)).stdout
        )
        info = self._fetch_command_info(command)
        for option in output['options']:
            if (command == 'hammer sync-plan create' and
                    option['name'] == 'sync-date'):
                # sync-date option use the current server time as the default
                # value in help text. As we use a previous created json file
                # with the commands information we need a special treatment for
                # this option.
                info_option = None
                for opt in info['options']:
                    if opt['name'] == 'sync-date':
                        info_option = opt
                        break
                self.assertIsNotNone(info_option)
                self.assertEqual(option['name'], opt['name'])
                self.assertEqual(option['shortname'], opt['shortname'])
                self.assertEqual(option['value'], opt['value'])
                # Drop the default value, and assert if the remaining string is
                # present on the help text.
                help = option['help'][:option['help'].find('Default: "')]
                self.assertIn(help, opt['help'])
            else:
                self.assertIn(option, info['options'])
        if len(info['subcommands']) > 0:
            for subcommand in info['subcommands']:
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
