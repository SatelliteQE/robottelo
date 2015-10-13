# -*- encoding: utf-8 -*-
"""Test class for Puppet Classes UI"""

from nailgun import entities
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.session import Session


class PuppetClasses(UITestCase):
    """Implements puppet classes tests in UI."""

    @run_only_on('sat')
    def test_update_positive(self):
        """@Test: Create new puppet-class

        @Feature: Puppet-Classes - Positive Update

        @Assert: Puppet-Classes is updated.

        """
        class_name = 'foreman_scap_client'
        param_name = 'ca file'
        with Session(self.browser):
            for description in generate_strings_list(len1=8):
                with self.subTest(description):
                    # Importing puppet classes from puppet-foreman_scap_client
                    # module for update process
                    if self.puppetclasses.search(class_name) is None:
                        self.puppetclasses.import_scap_client_puppet_classes()
                    self.assertIsNotNone(self.puppetclasses.search(class_name))
                    self.puppetclasses.update_class_parameter_description(
                        class_name, param_name, description)
                    self.assertEqual(
                        description,
                        self.puppetclasses.fetch_class_parameter_description(
                            class_name, param_name)
                    )

    @run_only_on('sat')
    def test_delete_positive(self):
        """@Test: Create new puppet-class

        @Feature: Puppet-Classes - Positive delete

        @Assert: Puppet-Class is deleted

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(len1=8):
                with self.subTest(name):
                    entities.PuppetClass(name=name).create()
                    session.nav.go_to_puppet_classes()
                    self.puppetclasses.delete(name)
