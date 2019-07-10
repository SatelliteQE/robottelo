# -*- encoding: utf-8 -*-
"""
:Requirement: Report templates

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Reporting

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import (
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import CLITestCase


class ReportTemplateTestCase(CLITestCase):
    """Report Templates CLI tests."""

    @tier1
    @stubbed()
    def test_positive_report_help_base(self):
        """Base level hammer help includes report-templates

        :id: 92d577db-144e-4761-a42e-e83887464986

        :setup: Any satellite user

        :steps:

            1. hammer --help

        :expectedresults: report-templates command is included in help

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_report_help_command(self):
        """Command level hammer help contains usage details

        :id: 92a578db-144e-4761-a42e-e83887464986

        :setup: Any satellite user

        :steps:

            1. hammer report-template --help

        :expectedresults: report-templates command details are displayed

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_report_help_subcommand(self):
        """Subcommand level hammer help contains usage details

        :id: 92a587db-144e-4761-a42e-e83887464986

        :setup: Any satellite user

        :steps:

            1. hammer report-template create --help

        :expectedresults: report-templates create command details are displayed

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_create_report(self):
        """Create report template

        :id: 82a577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights

        :steps:

            1. hammer report-template create ...

        :expectedresults: Report is created

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_list_reports(self):
        """List report templates

        :id: 82a577db-184e-4761-a42e-e83887464986

        :setup: User with reporting access rights, at least two report templates

        :steps:

            1. hammer report-template list ...

        :expectedresults: All report templates accessible by user are listed

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_read_report(self):
        """Read report template

        :id: 82a577db-144e-4765-a42e-e83887464986

        :setup: User with reporting access rights, some report template

        :steps:

            1. hammer report-template info ...

        :expectedresults: Report template data is shown

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_update_report(self):
        """Update report template

        :id: 84a577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. hammer report-template update ... # change some value

        :expectedresults: Report is updated (value is changed)

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_delete_report(self):
        """Delete report template

        :id: 84b577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. hammer report-template delete ...

        :expectedresults: Report is deleted

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_generate_report_nofilter(self):
        """Generate Host Status report

        :id: 84b687db-144e-4761-a42e-e93887464986

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            1. hammer report-template generate --id ... # do not specify any filter

        :expectedresults: Report is generated for all hosts visible for user

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_generate_report_filter(self):
        """Generate Host Status report

        :id: 84b677cb-144e-4761-a42e-e93887464986

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            1. hammer report-template generate --id ...

        :expectedresults: Report is generated for the host specified by the filter

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_lock_report(self):
        """Lock report template

        :id: 84c577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. hammer report-template update ... --locked true

        :expectedresults: Report is locked

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_unlock_report(self):
        """Unlock report template

        :id: 87fc028b-9cda-4a45-972c-d3ae4a06e04d

        :setup: User with reporting and unlock access rights, some report template that is locked

        :steps:

            1. hammer report-template update ... --locked false

        :expectedresults: Report is unlocked

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_report_add_userinput(self):
        """Add user input to template

        :id: 84b577db-144e-4761-a46e-e83887464986

        :setup: User with reporting access rights

        :steps:

            1. hammer template-input create ...

        :expectedresults: User input is assigned to the report template

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_dump_report(self):
        """Export report template

        :id: 84b577db-144e-4761-a42e-a83887464986

        :setup: User with reporting access rights, some report template

        :steps:

            1. hammer report-template dump ...

        :expectedresults: Report script is shown

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_clone_locked_report(self):
        """Clone locked report template

        :id: cc843731-b9c2-4fc9-9e15-d1ee5d967cda

        :setup: User with reporting access rights, some report template that is locked

        :steps:

            1. hammer report-template clone ...

        :expectedresults: Report is cloned

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_generate_report_sanitized(self):
        """Generate report template where there are values in comma outputted which might brake CSV format

        :id: 84b577db-144e-4961-a42e-e93887464986

        :setup: User with reporting access rights, Host Statuses report,
                a host with OS that has comma in its name

        :steps:

            1. hammer report-template generate ...

        :expectedresults: Report is generated in proper CSV format (value with comma is quoted)

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_negative_create_report_without_name(self):
        """Try to create a report template with empty name

        :id: 84b577db-144e-4771-a42e-e93887464986

        :setup: User with reporting access rights

        :steps:

            1. hammer report-template create --name '' ...

        :expectedresults: Report is not created

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_negative_delete_locked_report(self):
        """Try to delete a locked report template

        :id: 84b577db-144e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some report template that is locked

        :steps:

            1. hammer report-template delete ...

        :expectedresults: Report is not deleted

        :CaseImportance: Medium
        """
