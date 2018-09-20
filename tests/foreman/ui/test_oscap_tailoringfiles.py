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
from fauxfactory import gen_string
from nailgun import entities
from robottelo.cli.scapcontent import Scapcontent
from robottelo.config import settings
from robottelo.constants import (
    SNIPPET_DATA_FILE,
    OSCAP_PERIOD,
    OSCAP_PROFILE,
    OSCAP_WEEKDAY,
    OSCAP_DEFAULT_CONTENT
)
from robottelo.datafactory import valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade,
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_oscap_tailoringfile, make_oscappolicy
from robottelo.ui.session import Session
from unittest import skipIf


@skipIf(not(settings.oscap.tailoring_path or settings.oscap.content_path),
        "OSCAP-settings must have tailoring_path and content_path set")
class TailoringFilesTestCase(UITestCase):
    """Implements Tailoring Files tests in UI."""

    @classmethod
    def setUpClass(cls):
        super(TailoringFilesTestCase, cls).setUpClass()
        cls.tailoring_path = get_data_file(settings.oscap.tailoring_path)
        proxy = entities.SmartProxy().search(
            query={
                u'search': u'name={0}'.format(
                    settings.server.hostname)
            }
        )[0]
        loc = entities.Location(name=gen_string('alpha')).create()
        cls.loc_name = loc.name
        org = entities.Organization(name=gen_string('alpha'),
                                    smart_proxy=[proxy]).create()
        cls.org_name = org.name
        cls.content_path = get_data_file(settings.oscap.content_path)

    @run_only_on('sat')
    @tier1
    def test_positive_create(self):
        """Create new Tailoring Files using different values types as name

        :id: d6ae6b33-5af3-4b55-8ad4-6fa8e67e40f5

        :setup: Oscap enabled on capsule and scap tailoring file

        :steps:

            1. Navigate to Tailoring files menu
            2. Upload a valid tailoring file
            3. Give it a valid name

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for tailoring_file_name in valid_data_list():
                with self.subTest(tailoring_file_name):
                    make_oscap_tailoringfile(
                        session,
                        name=tailoring_file_name,
                        tailoring_path=self.tailoring_path,
                        tailoring_loc=self.loc_name,
                        tailoring_org=self.org_name,
                    )
                    self.assertIsNotNone(
                        self.oscaptailoringfile.search(tailoring_file_name),
                        msg="Tailoring file name element not found")

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_space(self):
        """Create tailoring files with space in name

        :id: 4b6a608b-b032-4d03-b67a-a9dce194e1ce

        :setup: tailoring file

        :steps:

            1. Navigate to Tailoring files menu
            2. Upload a valid tailoring file
            3. Give it a name with space

        :expectedresults: Tailoring file will be added to satellite

        :CaseImportance: Critical
        """
        with Session(self) as session:
            tailoring_name = gen_string('alpha') + ' ' + gen_string('alpha')
            make_oscap_tailoringfile(
                session,
                name=tailoring_name,
                tailoring_path=self.tailoring_path,
                tailoring_loc=self.loc_name,
                tailoring_org=self.org_name,
            )
            self.assertIsNotNone(
                self.oscaptailoringfile.search(tailoring_name),
                msg="Tailoring file name element not found")

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_file(self):
        """Create Tailoring files with invalid file

        :id: 310200e6-b5d9-460e-866a-a7864c134d76

        :setup: invalid tailoring file

        :steps:

            1. Navigate to Tailoring files menu
            2. With valid name ,upload  invalid tailoring file

        :expectedresults: Tailoring file will not be added to satellite

        :CaseImportance: Critical
        """
        invalid_file = SNIPPET_DATA_FILE
        tailoring_name = gen_string('alpha')
        with Session(self) as session:
            make_oscap_tailoringfile(
                session,
                name=tailoring_name,
                tailoring_path=invalid_file,
                tailoring_loc=self.loc_name,
                tailoring_org=self.org_name,
            )
            self.assertIsNone(
                self.oscaptailoringfile.search(tailoring_name),
                msg="Tailoring file name element is found")

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_associate_tailoring_file_with_scap(self):
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
        tailoring_name = gen_string('alpha')
        content_name = OSCAP_DEFAULT_CONTENT['rhel7_content']
        Scapcontent.update({
            'title': content_name,
            'organizations': self.org_name})
        policy_name = gen_string('alpha')
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            make_oscap_tailoringfile(
                session,
                name=tailoring_name,
                tailoring_path=self.tailoring_path,
                tailoring_loc=self.loc_name,
            )
            self.assertIsNotNone(
                self.oscaptailoringfile.search(tailoring_name),
                msg="Tailoring file name element not found")
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            make_oscappolicy(
                session,
                content=content_name,
                name=policy_name,
                period=OSCAP_PERIOD['weekly'],
                profile=OSCAP_PROFILE['common'],
                tailoring=tailoring_name,
                tailoring_profile=OSCAP_PROFILE['tailoring_rhel7'],
                period_value=OSCAP_WEEKDAY['friday'],
            )
            self.assertIsNotNone(
                self.oscappolicy.search(policy_name),
                msg="scap policy name element not found")

    @skip_if_bug_open('bugzilla', 1482904)
    @run_only_on('sat')
    @tier2
    def test_negative_associate_tailoring_file_with_different_scap(self):
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
        tailoring_name = gen_string('alpha')
        content_name = OSCAP_DEFAULT_CONTENT['rhel_firefox']
        policy_name = gen_string('alpha')
        with Session(self) as session:
            make_oscap_tailoringfile(
                session,
                name=tailoring_name,
                tailoring_path=self.tailoring_path,
                tailoring_loc=self.loc_name,
                tailoring_org=self.org_name,
            )
            self.assertIsNotNone(
                self.oscaptailoringfile.search(tailoring_name),
                msg="Tailoring file name element not found")
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))
            make_oscappolicy(
                session,
                content=content_name,
                name=policy_name,
                period=OSCAP_PERIOD['weekly'],
                profile=OSCAP_PROFILE['common'],
                tailoring=tailoring_name,
                tailoring_profile=OSCAP_PROFILE['tailoring_rhel7'],
                period_value=OSCAP_WEEKDAY['friday'],
            )
            self.assertIsNone(
                self.oscappolicy.search(policy_name),
                msg="scap policy name element found")

    @run_only_on('sat')
    @tier2
    @stubbed()
    def test_positive_download_tailoring_file(self):
        """ Download the tailoring file from satellite

        :id: 906ab1f8-c02c-4197-9c98-01e8b9f2f075

        :setup: tailoring file

        :steps:

            1. Upload a tailoring file
            2. Download the uploaded tailoring file

        :expectedresults: The tailoring file should be downloaded

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_delete_tailoring_file(self):
        """ Delete tailoring file

        :id: 359bade3-fff1-4aac-b4de-491190407507

        :setup: tailoring file

        :steps:

            1. Upload a tailoring file
            2. Delete the created tailoring file

        :expectedresults: Tailoring file should be deleted

        :CaseImportance: Critical
        """
        tailoring_name = gen_string('alpha')
        with Session(self) as session:
            make_oscap_tailoringfile(
                session,
                name=tailoring_name,
                tailoring_path=self.tailoring_path,
                tailoring_loc=self.loc_name,
                tailoring_org=self.org_name,
            )
            self.assertIsNotNone(
                self.oscaptailoringfile.search(tailoring_name),
                msg="Tailoring file name element not found")
            self.oscaptailoringfile.delete(
                tailoring_name, dropdown_present=True)
            self.assertIsNone(
                self.oscaptailoringfile.search(tailoring_name),
                msg="Tailoring file name element found")

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_oscap_run_with_tailoring_file_and_external_capsule(self):
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

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_positive_fetch_tailoring_file_information_from_arfreports(self):
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

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_tailoring_file_options_with_no_capsule_support(self):
        """ Tailoring Files Options with no capsule support(Eg. 6.2 cap)

        :id: ecfd2f5f-a8b1-4491-a081-33ac013f5e9f

        :CaseAutomation: notautomated

        :expectedresults:  Display a message about no supported capsule

        :CaseImportance: Critical
        """
