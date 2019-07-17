# -*- encoding: utf-8 -*-
"""
:Requirement: Report templates

:CaseAutomation: Automated

:CaseLevel: Component

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

    @tier2
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

    @tier2
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

    @tier2
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

        :CaseImportance: Critical
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

        :CaseImportance: Critical
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

        :CaseImportance: Critical
        """

    @tier2
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

    @tier2
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

        :CaseImportance: Critical
        """

    @tier2
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

        :CaseImportance: High
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

    @tier2
    @stubbed()
    def test_positive_applied_errata(self):
        """Generate an Applied Errata report

        :id: a4b677db-141e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template generate ...

        :expectedresults: A report is generated with all applied errata listed

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_generate_nonblocking_wait(self):
        """Generate an Applied Errata report using schedule --wait

        :id: a4b777db-143c-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template schedule --wait ...

        :expectedresults: A report is generated asynchronously

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_generate_nonblocking_download(self):
        """Generate an Applied Errata report

        :id: a4b777db-143d-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template schedule ...
            2. hammer report-template report-data --job-id= ...

        :expectedresults: A report is generated asynchronously

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_generate_email_compressed(self):
        """Generate an Applied Errata report, get it by e-mail, compressed

        :id: a4b877db-143e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template schedule ...

        :expectedresults: A report is generated asynchronously, the result
                          is compressed and mailed to the specified address

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_positive_generate_email_uncompressed(self):
        """Generate an Applied Errata report, get it by e-mail, uncompressed

        :id: a4b977db-143f-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template schedule ...

        :expectedresults: A report is generated asynchronously, the result
                          is not compressed and is mailed
                          to the specified address

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_negative_bad_email(self):
        """ Report can't be generated when incorrectly formed mail specified

        :id: a4ba77db-144e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some host with applied errata

        :steps:

            1. hammer report-template schedule ...

        :expectedresults: Error message about wrong e-mail address, no task is triggered

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_negative_nonauthor_of_report_cant_download_it(self):
        """The resulting report should only be downloadable by
           the user that generated it or admin. Check.

        :id: a4bc77db-146e-4871-a42e-e93887464986

        :setup: Installed Satellite, user that can list running tasks

        :steps:

            1. hammer -u u1 -p p1 report-template schedule
            2. hammer -u u2 -p p2 report-template report-data

        :expectedresults: Report can't be downloaded. Error.

        :CaseImportance: High
        """
