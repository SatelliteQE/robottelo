# -*- encoding: utf-8 -*-
"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.config import settings
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    fixture,
    tier2,
    tier4,
    stubbed,
    upgrade,
)


@fixture(scope='module')
def oscap_content_path():
    return settings.oscap.content_path


@fixture(scope='module')
def oscap_tailoring_path():
    return settings.oscap.tailoring_path


@tier2
@upgrade
def test_positive_associate_tailoring_file_with_scap(
        session, oscap_content_path, oscap_tailoring_path):
    """ Associate a Tailoring file with it’s scap content

    :id: 33e7b8ca-2e5f-4886-91b7-1a8763059d14

    :setup: scap content and tailoring file

    :steps:

        1. Create a valid scap content
        2. Upload a vaild tailoring file
        3. Associate scap content with it’s tailoring file

    :expectedresults: Association should be successful

    :CaseImportance: Critical
    """
    content_name = gen_string('alpha')
    tailoring_name = gen_string('alpha')
    policy_name = gen_string('alpha')
    loc = entities.Location().create()
    org = entities.Organization().create()
    with session:
        session.oscapcontent.create({
            'file_upload.title': content_name,
            'file_upload.scap_file': oscap_content_path,
            'organizations.resources.assigned': [org.name]
        })
        session.organization.select(org_name=org.name)
        session.oscaptailoringfile.create({
            'file_upload.name': tailoring_name,
            'file_upload.scap_file': oscap_tailoring_path,
            'locations.resources.assigned': [loc.name]
        })
        assert session.oscaptailoringfile.search(
            tailoring_name)[0]['Name'] == tailoring_name
        assert session.oscapcontent.search(
            content_name)[0]['Title'] == content_name
        session.oscappolicy.create({
            'create_policy.name': policy_name,
            'scap_content.scap_content_resource': content_name,
            'scap_content.xccdf_profile':
                'Common Profile for General-Purpose Systems',
            'scap_content.tailoring_file': tailoring_name,
            'scap_content.xccdf_profile_tailoring_file':
                'Common Profile for General-Purpose Systems [CUSTOMIZED1]',
            'schedule.period': 'Weekly',
            'schedule.period_selection.weekday': 'Friday',
        })
        assert session.oscappolicy.search(
            policy_name)[0]['Name'] == policy_name


@tier2
@stubbed()
def test_positive_download_tailoring_file():
    """ Download the tailoring file from satellite

    :id: 906ab1f8-c02c-4197-9c98-01e8b9f2f075

    :setup: tailoring file

    :steps:

        1. Upload a tailoring file
        2. Download the uploaded tailoring file

    :expectedresults: The tailoring file should be downloaded

    :CaseImportance: Critical
    """


@tier2
@upgrade
def test_positive_delete_tailoring_file(session, oscap_tailoring_path):
    """ Delete tailoring file

    :id: 359bade3-fff1-4aac-b4de-491190407507

    :setup: tailoring file

    :steps:

        1. Upload a tailoring file
        2. Delete the created tailoring file

    :expectedresults: Tailoring file should be deleted

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.oscaptailoringfile.create({
            'file_upload.name': name,
            'file_upload.scap_file': oscap_tailoring_path
        })
        session.oscaptailoringfile.delete(name)
        assert not session.oscaptailoringfile.search(name)


@stubbed()
@tier4
def test_positive_oscap_run_with_tailoring_file_and_external_capsule():
    """ End-to-End Oscap run with tailoring files and external capsule

    :id: 5e6e87b1-5f7d-4bbb-9603-eb3a34521d31

    :setup: scap content, scap policy, tailoring file, host group

    :steps:
        1. Create a valid scap content
        2. Upload a valid tailoring file
        3. Create a scap policy
        4. Associate scap content with it’s tailoring file
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Puppet should configure and fetch the scap content
           and tailoring file from external capsule

    :CaseAutomation: notautomated

    :expectedresults: ARF report should be sent to satellite
                     reflecting the changes done via tailoring files

    :CaseImportance: Critical
    """


@stubbed()
@tier4
def test_positive_fetch_tailoring_file_information_from_arfreports():
    """ Fetch Tailoring file Information from Arf-reports

    :id: 7412cf34-8271-4c8b-b369-304529e8ee28

    :setup: scap content, scap policy, tailoring file, host group

    :steps:

        1. Create a valid scap content
        2. Upload a valid tailoring file
        3. Create a scap policy
        4. Associate scap content with it’s tailoring file
        5. Associate the policy with a hostgroup
        6. Provision a host using the hostgroup
        7. Puppet should configure and fetch the scap content
           and send arf-report to satellite

    :CaseAutomation: notautomated

    :expectedresults: ARF report should have information
                      about the tailoring file used, if any

    :CaseImportance: Critical
    """
