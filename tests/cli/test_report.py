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
from robottelo.cli.report import Report
from robottelo.common.decorators import bzbug
from robottelo.common import ssh


class TestReport(BaseCLI):

    @bzbug(1044408)
    def test_list(self):
        """
        Displays list for puppet report.
        """

        result = ssh.command('puppet agent -t')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = Report().list({'search': 'search'})
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = Report().list({'order': 'order'})
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = Report().list({'page': 'page'})
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = Report().list({'per-page': 'per-page'})
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)

    def test_info(self):
        """
        Displays info for puppet report.
        """

        result = ssh.command('puppet agent -t')
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        result = Report().list()
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        output = result.stdout
        keys_id = []
        for i in range(0, len(output)):
            for key in output[i].keys():
                if key == 'Id':
                    keys_id.append(output[i][key])
        result = Report().info({'id': keys_id[0]})
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
        result = Report().list()
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
        output = result.stdout
        index = [c.strip() for c in output[1].split('|')].index('ID')
        ids = [line.split('|')[index].strip() for line in output[3:-1]]
        result = Report().delete({'id': ids[0]})
        self.assertEqual(result.return_code, 0)
        self.assertFalse(result.stderr)
