#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
# hammer report --help
Usage:
    hammer report [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    info                          Show a report.
    list                          List all reports.
    delete                        Delete a report.

Options:
    -h, --help                    print help
"""

from tests.cli.basecli import BaseCLI
from robottelo.common.decorators import bzbug
from robottelo.common import ssh


class TestReport(BaseCLI):

    def test_list(self):
        """
        Displays list for puppet report.
        """

        result = ssh.command('puppet agent -t')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = ssh.command('hammer report list --search')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = ssh.command('hammer report list --order')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = ssh.command('hammer report list --page')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = ssh.command('hammer report list --per-page')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)

    def test_info(self):
        """
        Displays info for puppet report.
        """

        result = ssh.command('puppet agent -t')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = ssh.command('hammer report list')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        output = result.stdout
        index = [c.strip() for c in output[1].split('|')].index('ID')
        ids = [line.split('|')[index].strip() for line in output[3:-1]]
        result = ssh.command('hammer report info --id ' + ids[0])
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)

    @bzbug(1044408)
    def test_delete(self):
        """
        Delete a puppet report.
        """

        result = ssh.command('puppet agent -t')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = ssh.command('hammer report list')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        output = result.stdout
        index = [c.strip() for c in output[1].split('|')].index('ID')
        ids = [line.split('|')[index].strip() for line in output[3:-1]]
        result = ssh.command('hammer report delete --id ' + ids[0])
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
