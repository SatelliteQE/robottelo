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
from robottelo.config import settings
from robottelo.constants import (
    SNIPPET_DATA_FILE,
)
from robottelo.datafactory import valid_data_list
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_oscap_tailoringfile
from robottelo.ui.session import Session


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
    @stubbed()
    @tier1
    def test_negative_tailoring_file_options_with_no_capsule_support(self):
        """ Tailoring Files Options with no capsule support(Eg. 6.2 cap)

        :id: ecfd2f5f-a8b1-4491-a081-33ac013f5e9f

        :CaseAutomation: notautomated

        :expectedresults:  Display a message about no supported capsule

        :CaseImportance: Critical
        """
