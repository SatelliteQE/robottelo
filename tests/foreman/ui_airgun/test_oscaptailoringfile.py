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
    skip_if_bug_open,
    tier2,
    tier4,
    stubbed,
    upgrade,
)


@fixture(scope='module')
def oscap_tailoring_path():
    return settings.oscap.tailoring_path


def test_positive_create(session, oscap_tailoring_path):
    name = gen_string('alpha')
    with session:
        session.oscaptailoringfile.create({
            'file_upload.name': name,
            'file_upload.scap_file': oscap_tailoring_path
        })
        assert session.oscaptailoringfile.search(name)[0]['Name'] == name
        oscap_tailor_val = session.oscaptailoringfile.read(name)
        assert oscap_tailoring_path.rsplit(
            '/', 1)[-1] == oscap_tailor_val['scap_file_name']


def test_positive_update(session, oscap_tailoring_path):
    name = gen_string('alpha')
    org = entities.Organization().create()
    with session:
        session.oscaptailoringfile.create({
            'file_upload.name': name,
            'file_upload.scap_file': oscap_tailoring_path
        })
        session.oscaptailoringfile.update(name, {
            'organizations.resources.assigned': [org.name]
        })
        tailor_val = session.oscaptailoringfile.read(name)
        assert org.name in tailor_val['organizations']['resources']['assigned']


# TODO content policy has to be done firstly.
@tier2
@upgrade
def test_positive_associate_tailoring_file_with_scap():
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


# TODO content policy has to be done firstly.
@skip_if_bug_open('bugzilla', 1482904)
@tier2
def test_negative_associate_tailoring_file_with_different_scap():
    """ Associate a tailoring file with different scap content

    :id: 5b166dd4-5e9c-4c35-b2fb-fd35d75d51f5

    :setup: scap content and tailoring file

    :steps:

        1. Create a valid scap content
        2. Upload a Mutually exclusive tailoring file
        3. Associate the scap content with tailoring file

    :expectedresults: Association should give some warning

    :CaseImportance: Critical
    """


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
