"""Test class for Puppet Classes UI"""

from ddt import ddt, data
from nailgun import entities
from robottelo.decorators import run_only_on
from robottelo.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class PuppetClasses(UITestCase):
    """Implements puppet classes tests in UI."""

    @data(*generate_strings_list(len1=8))
    def test_update_positive(self, description):
        """@Test: Create new puppet-class

        @Feature: Puppet-Classes - Positive Update

        @Assert: Puppet-Classes is updated.

        """
        class_name = 'foreman_scap_client'
        param_name = 'ca file'
        with Session(self.browser):
            # Importing puppet classes from puppet-foreman_scap_client
            # module for update process
            if self.puppetclasses.search(class_name) is None:
                self.puppetclasses.import_scap_client_puppet_classes()
            self.assertIsNotNone(self.puppetclasses.search(class_name))
            self.puppetclasses.update_class_parameter_description(
                class_name,
                param_name,
                description
            )
            self.assertEqual(
                description,
                self.puppetclasses.fetch_class_parameter_description(
                    class_name,
                    param_name)
            )

    @data(*generate_strings_list(len1=8))
    def test_delete_positive(self, name):
        """@Test: Create new puppet-class

        @Feature: Puppet-Classes - Positive delete

        @Assert: Puppet-Class is deleted

        """
        entities.PuppetClass(name=name).create()
        with Session(self.browser) as session:
            session.nav.go_to_puppet_classes()
            self.puppetclasses.delete(name)
