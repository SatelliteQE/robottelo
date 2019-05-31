# -*- encoding: utf-8 -*-
"""Test class for Puppet Classes UI

:Requirement: Puppetclass

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.session import Session


class PuppetClassTestCase(UITestCase):
    """Implements puppet classes tests in UI."""

    @tier1
    def test_positive_update_description(self):
        """Create new puppet-class and update its description to a valid
        one

        :id: 711fe4de-b62f-48b5-9845-2d8725eb3548

        :expectedresults: Puppet-Classes is updated successfully.

        :CaseImportance: Critical
        """
        class_name = 'foreman_scap_client'
        param_name = 'ca_file'
        with Session(self):
            for description in valid_data_list():
                with self.subTest(description):
                    # Importing puppet classes from puppet-foreman_scap_client
                    # module for update process
                    if self.puppetclasses.search(class_name) is None:
                        self.puppetclasses.import_scap_client_puppet_classes()
                    self.assertIsNotNone(self.puppetclasses.search(class_name))
                    self.puppetclasses.update_class_parameter(
                        class_name, param_name, description=description)
                    self.assertEqual(
                        description,
                        self.puppetclasses.fetch_class_parameter_description(
                            class_name, param_name)
                    )

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create new puppet-class and then delete it

        :id: 0d6e579e-8a7a-46a1-9932-5f345905671d

        :expectedresults: Puppet-Class is deleted successfully.

        :CaseImportance: Critical
        """
        with Session(self):
            for name in valid_data_list():
                with self.subTest(name):
                    entities.PuppetClass(name=name).create()
                    self.puppetclasses.delete(name)
