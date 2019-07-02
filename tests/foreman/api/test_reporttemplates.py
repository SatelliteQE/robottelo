# -*- encoding: utf-8 -*-
"""Unit tests for the ``report_templates`` paths.

:Requirement: Report templates

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import tier1, tier2, stubbed
from robottelo.test import APITestCase


class ComputeResourceTestCase(APITestCase):
    """Tests for ``katello/api/v2/report_templates``."""

    @tier1
    @stubbed()
    def test_positive_create_report(self):
        """Create report template

        :id: a2a577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights

        :steps:

            1. POST /api/report_templates

        :expectedresults: Report is created

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_positive_list_reports(self):
        """List report templates

        :id: a2a577db-184e-4761-a42e-e83887464986

        :setup: User with reporting access rights, at least two report templates

        :steps:

            1. GET /api/report_templates

        :expectedresults: All report templates accessible by user are listed

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_positive_read_report(self):
        """Read report template

        :id: a2a577db-144e-4765-a42e-e83887464986

        :setup: User with reporting access rights, some report template

        :steps:

            1. GET /api/report_templates/:id

        :expectedresults: Report template data is shown

        :CaseImportance: Critical
        """

    @tier2
    @stubbed()
    def test_positive_update_report(self):
        """Update report template

        :id: a4a577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. PUT /api/report_templates/:id

        :expectedresults: Report is updated (value is changed)

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_delete_report(self):
        """Delete report template

        :id: a4b577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. DELETE /api/report_templates/:id

        :expectedresults: Report is deleted

        :CaseImportance: High
        """

    @tier1
    @stubbed()
    def test_positive_generate_report_nofilter(self):
        """Generate Host Status report

        :id: a4b687db-144e-4761-a42e-e93887464986

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            1. POST /api/report_templates/:id/generate

        :expectedresults: Report is generated for all hosts visible for user

        :CaseImportance: Critical
        """

    @tier2
    @stubbed()
    def test_positive_generate_report_filter(self):
        """Generate Host Status report

        :id: a4b677cb-144e-4761-a42e-e93887464986

        :setup: User with reporting access rights, some report template, at least two hosts

        :steps:

            1. POST /api/report_templates/:id/generate ... # define input_values

        :expectedresults: Report is generated for the host specified by the filter

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_report_add_userinput(self):
        """Add user input to template

        :id: a4a577db-144e-4761-a42e-e86887464986

        :setup: User with reporting access rights

        :steps:

            1. PUT /api/templates/:template_id/template_inputs/:id ... # add user input

        :expectedresults: User input is assigned to the report template

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_lock_report(self):
        """Lock report template

        :id: a4c577db-144e-4761-a42e-e83887464986

        :setup: User with reporting access rights, some report template that is not locked

        :steps:

            1. PUT /api/report_templates/:id ... # report_template[locked] = true

        :expectedresults: Report is locked

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_unlock_report(self):
        """Unlock report template

        :id: dae2bff8-340c-4d4c-8349-a2155507a3ab

        :setup: User with reporting and unlock access rights, some report template that is locked

        :steps:

            1. PUT /api/report_templates/:id ... # report_template[locked] = false

        :expectedresults: Report is unlocked

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_export_report(self):
        """Export report template

        :id: a4b577db-144e-4761-a42e-a83887464986

        :setup: User with reporting access rights, some report template

        :steps:

            1. /api/report_templates/:id/export

        :expectedresults: Report script is shown

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_clone_locked_report(self):
        """Clone locked report template

        :id: 9b77242d-31e4-4930-83dd-8bffa1d6b1df

        :setup: User with reporting access rights, some report template that is locked

        :steps:

            1. POST /api/report_templates/:id/clone

        :expectedresults: Report is cloned

        :CaseImportance: High
        """

    @tier2
    @stubbed()
    def test_positive_generate_report_sanitized(self):
        """Generate report template where there are values in comma outputted which might brake CSV format

        :id: a4b577db-144e-4961-a42e-e93887464986

        :setup: User with reporting access rights, Host Statuses report,
                a host with OS that has comma in its name

        :steps:

            1. POST /api/report_templates/:id/generate

        :expectedresults: Report is generated in proper CSV format (value with comma is quoted)

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_negative_create_report_without_name(self):
        """Try to create a report template with empty name

        :id: a4b577db-144e-4771-a42e-e93887464986

        :setup: User with reporting access rights

        :steps:

            1. POST /api/report_templates

        :expectedresults: Report is not created

        :CaseImportance: Medium
        """

    @tier2
    @stubbed()
    def test_negative_delete_locked_report(self):
        """Try to delete a locked report template

        :id: a4b577db-144e-4871-a42e-e93887464986

        :setup: User with reporting access rights, some report template that is locked

        :steps:

            1. DELETE /api/report_templates/:id

        :expectedresults: Report is not deleted

        :CaseImportance: Medium
        """
