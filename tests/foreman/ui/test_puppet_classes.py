"""Test class for Puppet Classes UI"""

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest
from ddt import ddt
from fauxfactory import gen_string
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_puppetclasses
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@unittest.skip("Now Puppet Classes can only be created via API's")
@run_only_on('sat')
@ddt
class PuppetClasses(UITestCase):
    """Implements puppet classes tests in UI."""

    @data({'name': gen_string('alpha', 10),
           'new_name': gen_string('alpha', 10)},
          {'name': gen_string('numeric', 10),
           'new_name': gen_string('numeric', 10)},
          {'name': gen_string('alphanumeric', 10),
           'new_name': gen_string('alphanumeric', 10)},
          {'name': gen_string('utf8', 10),
           'new_name': gen_string('utf8', 10)},
          {'name': gen_string('latin1', 20),
           'new_name': gen_string('latin1', 10)})
    def test_update_positive_1(self, testdata):
        """@Test: Create new puppet-class

        @Feature: Puppet-Classes - Positive Update

        @Assert: Puppet-Classes is updated.

        """
        name = testdata['name']
        new_name = testdata['new_name']
        with Session(self.browser) as session:
            make_puppetclasses(session, name=name)
            search = self.puppetclasses.search(name)
            self.assertIsNotNone(search)
            self.puppetclasses.update(name, new_name)

    @skip_if_bug_open('bugzilla', 1126473)
    @data(*generate_strings_list(len1=8))
    def test_delete_positive_1(self, name):
        """@Test: Create new puppet-class

        @Feature: Puppet-Classes - Positive delete

        @Assert: Puppet-Class is deleted

        @BZ: 1126473

        """
        with Session(self.browser) as session:
            make_puppetclasses(session, name=name)
            search = self.puppetclasses.search(name)
            self.assertIsNotNone(search)
            self.puppetclasses.delete(name, True)
            self.assertIsNotNone(session.nav.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.puppetclasses.search(name))
