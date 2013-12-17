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
from robottelo.cli.report import Report
from robottelo.common.helpers import generate_id, sleep_for_seconds
from tests.cli.basecli import BaseCLI


class TestReport(BaseCLI):

    def test_info(self):
        id = generate_id() 
        result = Report().info({'id': id})
        self.assertEquals(
            len(result.stdout), 1, "Report info - return count"
        )
        self.assertEquals(result.stdout[0]['ID'], name,
                          "Report info - stdout contains 'ID'")
        
    def test_delete(self):
        id = generate_id()
        result = Report().delete({'id': id})
        self.assertTrue(result.return_code == 0,
                        "Report delete - retcode")
        sleep_for_seconds(5)  # sleep for about 5 sec.
        result = Report().list({'search': id})
        self.assertTrue(len(result.stdout) == 0,
                        "Report list - does not have deleted id")
        
    def test_list(self):
        id = generate_id()
        result = Report().list({'search': id})
        self.assertTrue(len(result.stdout) == 1,
                        "Report list - stdout contains 'ID'")
        result = Report().list({'order': id})
        self.assertTrue(len(result.stdout) == 1,
                        "Report list - stdout contains 'ID'")
        result = Report().list({'page': id})
        self.assertTrue(len(result.stdout) == 1,
                        "Report list - stdout contains 'ID'")
        result = Report().list({'per-page': id})
        self.assertTrue(len(result.stdout) == 1,
                        "Report list - stdout contains 'ID'")