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
from robottelo.common.decorators import bzbug


class TestReport(BaseCLI):

    @bzbug('1043830')
    def test_info(self):
        """
        Displays info for puppet report.
        """
        id = generate_id() 
        result = Report().info({'id': id})
        self.assertEquals(
            len(result.stdout), 1, "Report info - return count"
        )
        self.assertEquals(result.stdout['ID'], name,
                          "Report info - stdout contains 'ID'")
        
    @bzbug('1043830')   
    def test_delete(self):
        """
        Deletes the report generated for puppet.
        """
        id = generate_id()
        result = Report().delete({'id': id})
        self.assertTrue(result.return_code == 0,
                        "Report delete - retcode")
        sleep_for_seconds(5)  # sleep for about 5 sec.
        result = Report().list({'search': id})
        self.assertTrue(len(result.stdout) == 0,
                        "Report list - does not have deleted id")
        
    @bzbug('1043830')    
    def test_list(self):
        """
        List the report for puppet.
        """
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
           