"""Test for Report Templates

:Requirement: Reports

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""


from robottelo.decorators import (
    tier2,
    tier3,
    stubbed,
)


@tier2
@stubbed()
def test_positive_create_report(session):
    """ Create a report template

    :id: 906ac1f8-c02c-4197-9c98-01e8b9f2f075

    :setup: User with reporting access rights

    :steps:

        1. Monitor -> Report Templates -> Create Template
        2. Insert any content
        3. Submit

    :expectedresults: The report template should be created

    :CaseImportance: High
    """


@tier2
@stubbed()
def test_positive_read_report(session):
    """ Create a report template

    :id: 906ac1f8-c02c-4197-9c97-01e8b9f2f075

    :setup: User with reporting access rights, some existing report template

    :steps:

        1. Monitor -> Report Templates
        2. Select template

    :expectedresults: The report template's content is shown

    :CaseImportance: High
    """


@tier2
@stubbed()
def test_positive_update_report(session):
    """ Edit a report template

    :id: 906ac1f8-c02c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights, some existing report template that is not locked

    :steps:

        1. Monitor -> Report Templates
        2. Select template
        3. Change template content
        4. Submit

    :expectedresults: The report template should be updated

    :CaseImportance: High
    """


@tier2
@stubbed()
def test_positive_delete_report(session):
    """ Edit a report template

    :id: 906ac1f8-c02c-4297-9c98-01f8b9f2f075

    :setup: User with reporting access rights, some existing report template that is not locked

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Delete

    :expectedresults: The report template should be deleted

    :CaseImportance: High
    """


@tier2
@stubbed()
def test_positive_lock_report(session):
    """ Edit a report template

    :id: 903ac1f8-c02c-4297-9c98-01e8f9f2f075

    :setup: User with reporting access rights, some existing report template that is not locked

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Lock

    :expectedresults: The report template should be locked

    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_positive_unlock_report(session):
    """ Edit a report template

    :id: 976ac1f8-c02c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights, some existing report template that is locked

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Unlock

    :expectedresults: The report template should be unlocked

    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_positive_export_report(session):
    """ Edit a report template

    :id: 916ac1f8-c02c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights, some existing report template

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Export

    :expectedresults: A file should be downloaded with the report's script

    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_positive_generate_report_hoststatus(session):
    """ Edit a report template

    :id: 916fc1f8-c02c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights, existing Hosts Status report template,
            at least two hosts

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Generate
        3. Submit

    :expectedresults: A report should be generated with a list of hosts and their statuses

    :CaseImportance: High
    """


@tier2
@stubbed()
def test_positive_generate_report_hoststatus_filter(session):
    """ Edit a report template

    :id: 916ec1f8-c02c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights, existing Hosts Status report template,
            at least two hosts

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Generate
        3. Fill in such a filter that it only matches 1 host
        4. Submit

    :expectedresults: A report should be generated with a filtered hosts and its status

    :CaseImportance: High
    """


@tier2
@stubbed()
def test_positive_generate_report_hoststatus_sanitized(session):
    """ Edit a report template

    :id: 916ed1f8-c02c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights, existing Hosts Status report template,
            OS with comma in its label, at least two hosts with this OS

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions column, click Generate
        3. Submit

    :expectedresults: A report should be generated with a list of hosts and their statuses

    :CaseImportance: High
    """


@tier2
@stubbed()
def test_negative_create_report_without_name(session):
    """ Edit a report template

    :id: 916ec1f8-c42c-4297-9c98-01e8b9f2f075

    :setup: User with reporting access rights

    :steps:

        1. Monitor -> Report Templates -> Create Template
        2. Insert any content but empty name
        3. Submit

    :expectedresults: A report should not be created and a warning should be displayed

    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_negative_cannont_delete_locked_report(session):
    """ Edit a report template

    :id: cd19b90d-830f-4efd-8cbc-d5e09a909a67

    :setup: User with reporting access rights, some report template that is locked

    :steps:

        1. Monitor -> Report Templates
        2. In the reports row, in Actions Column, try to click Delete

    :expectedresults: A report should not be deleted and the button should not even be clickable

    :CaseImportance: Medium
    """


@tier2
@stubbed()
def test_positive_preview_report(session):
    """ Preview a report

    :id: cd19b90d-836f-4efd-8cbc-d5e09a909a67

    :setup: User with reporting access rights, some report template

    :steps:

        1. Monitor -> Report Templates
        2. Open the report template
        3. Go to Preview tab

    :expectedresults: A report preview should be shown, with correct but
                      limited data (load_hosts macro should only list 10 records)

    :CaseImportance: Medium
    """


@tier3
@stubbed()
def test_positive_report_e2e(session):
    """ Report templates end-to-end scenario

    :id: cd19b90d-836f-4efd-8cbc-d5e09a908e67

    :setup: Admin user, more than one host registered

    :steps:

        1. Admin creates a user with appropriate permissions, that user logs in
        2. Creates new report template with host_search input that would e.g. print just host names
        3. Generate the report out of it by specifying the valid host search syntax
        4. The report contains expected data
        5. User deletes the report template

    :expectedresults: All steps succeeded. Generated report contains correct data.
                      User can see this activity logged in audit
                      page (besides generating report as it doesn't change DB state)

    :CaseImportance: Medium
    """
