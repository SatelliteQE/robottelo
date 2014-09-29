"""Test class for Puppet Classes UI"""

from ddt import ddt
from fauxfactory import gen_string
from nose.plugins.attrib import attr
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org, make_loc, make_puppetclasses
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class PuppetClasses(UITestCase):
    """Implements puppet classes tests in UI."""
    org_name = None
    loc_name = None

    def setUp(self):
        super(PuppetClasses, self).setUp()
        # Make sure to use the Class' org_name instance
        if (PuppetClasses.org_name is None and
           PuppetClasses.loc_name is None):
            PuppetClasses.org_name = gen_string("alpha", 8)
            PuppetClasses.loc_name = gen_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=PuppetClasses.org_name)
                make_loc(session, name=PuppetClasses.loc_name)

    @attr('ui', 'puppet-classes', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_create_positive_1(self, name):
        """@Test: Create new puppet-class

        @Feature: Puppet-Classes - Positive Create

        @Assert: Puppet-Classes is created

        """
        with Session(self.browser) as session:
            make_puppetclasses(session, name=name)
            search = self.puppetclasses.search(name)
            self.assertIsNotNone(search)

    @attr('ui', 'puppet-classes', 'implemented')
    @data(
        gen_string('alphanumeric', 255),
        gen_string('alpha', 255),
        gen_string('numeric', 255),
        gen_string('latin1', 255),
        gen_string('utf8', 255)
    )
    def test_create_positive_2(self, name):
        """@Test: Create new puppet-class with 255 chars

        @Feature: Puppet-Classes - Positive Create

        @Assert: Puppet-Classes is created with 255 chars

        """
        with Session(self.browser) as session:
            make_puppetclasses(session, name=name)
            search = self.puppetclasses.search(name)
            self.assertIsNotNone(search)

    @skip_if_bug_open('bugzilla', 1126496)
    @attr('ui', 'puppet-classes', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_create_negative_1(self, name):
        """@Test: Create new puppet-class with 256 chars

        @Feature: Puppet-Classes - Negative Create

        @Assert: Puppet-Classes is not created with 256 chars

        @BZ: 1126496

        """
        with Session(self.browser) as session:
            make_puppetclasses(session, name=name)
            search = self.puppetclasses.search(name)
            self.assertIsNone(search)

    def test_create_negative_2(self):
        """@Test: Create new puppet-class with blank name

        @Feature: Puppet-Classes - Negative Create

        @Assert: Puppet-Classes is not created with 256 chars

        """
        name = ""
        with Session(self.browser) as session:
            make_puppetclasses(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_create_negative_3(self):
        """@Test: Create new puppet-class with blank name

        @Feature: Puppet-Classes - Negative Create

        @Assert: Puppet-Classes is not created with 256 chars

        """
        name = "    "
        with Session(self.browser) as session:
            make_puppetclasses(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @attr('ui', 'puppet-classes', 'implemented')
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
    @attr('ui', 'puppet-classes', 'implemented')
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
