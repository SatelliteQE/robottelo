# -*- encoding: utf-8 -*-
"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.config import settings
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier4
from robottelo.decorators import upgrade
from robottelo.helpers import file_downloader


@fixture(scope='module')
def oscap_tailoring_path():
    return file_downloader(settings.oscap.tailoring_path)[0]


@tier1
@upgrade
def test_positive_end_to_end(session, oscap_tailoring_path):
    """Perform end to end testing for tailoring file component

    :id: 9aebccb8-6837-4583-8a8a-8883480ab688

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    org = entities.Organization().create()
    loc = entities.Location().create()
    with session:
        session.oscaptailoringfile.create(
            {
                'file_upload.name': name,
                'file_upload.scap_file': oscap_tailoring_path,
                'organizations.resources.assigned': [org.name],
                'locations.resources.assigned': [loc.name],
            }
        )
        assert session.oscaptailoringfile.search(name)[0]['Name'] == name
        tailroingfile_values = session.oscaptailoringfile.read(name)
        assert tailroingfile_values['file_upload']['name'] == name
        assert (
            tailroingfile_values['file_upload']['uploaded_scap_file']
            == oscap_tailoring_path.rsplit('/', 1)[-1]
        )
        assert org.name in tailroingfile_values['organizations']['resources']['assigned']
        assert loc.name in tailroingfile_values['locations']['resources']['assigned']
        session.oscaptailoringfile.update(name, {'file_upload.name': new_name})
        assert session.oscaptailoringfile.search(new_name)[0]['Name'] == new_name
        assert not session.oscaptailoringfile.search(name)
        # Skip delete operation till https://github.com/SatelliteQE/airgun/issues/473 is fixed.
        # session.oscaptailoringfile.delete(new_name)
        # assert not session.oscaptailoringfile.search(new_name)


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
