# -*- encoding: utf-8 -*-
"""Test class for Navigation UI

:Requirement: Navigation

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import skip_if_bug_open, tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, menu_locators
from robottelo.ui.session import Session


class NavigationTestCase(UITestCase):
    """Implements the navigation tests from UI"""

    def page_objects(self):
        return {
            'Activation Key': self.activationkey,
            'Architecture': self.architecture,
            'Bookmark': self.bookmark,
            'Container': self.container,
            'Compute Profile': self.compute_profile,
            'Compute Resource': self.compute_resource,
            'Content Hosts': self.contenthost,
            'Config Groups': self.configgroups,
            'Content Views': self.content_views,
            'Docker Tag': self.dockertag,
            'Domain': self.domain,
            'Discovered Hosts': self.discoveredhosts,
            'Discovery Rules': self.discoveryrules,
            'Environment': self.environment,
            'Gpgkey': self.gpgkey,
            'Hardware Model': self.hardwaremodel,
            'Host Collection': self.hostcollection,
            'Host Group': self.hostgroup,
            'Hosts': self.hosts,
            'Jobs': self.job,
            'Job Template': self.jobtemplate,
            'LDAP Authsource': self.ldapauthsource,
            'LifecycleEnvironment': self.lifecycleenvironment,
            'Location': self.location,
            'Medium': self.medium,
            'Operating Systems': self.operatingsys,
            'Organization': self.org,
            'SCAP Contents': self.oscapcontent,
            'Policies': self.oscappolicy,
            'Reports': self.oscapreports,
            'Packages': self.package,
            'Partition Table': self.partitiontable,
            'Puppet Classes': self.puppetclasses,
            'Product': self.products,
            'Registry': self.registry,
            'Role': self.role,
            'Settings': self.settings,
            'Subnet': self.subnet,
            'Subscriptions': self.subscriptions,
            'Sync Plan': self.syncplan,
            'Template': self.template,
            'Trend': self.trend,
            'User': self.user,
            'User Group': self.usergroup,
        }

    @skip_if_bug_open('bugzilla', 1426382)
    @tier1
    @upgrade
    def test_positive_navigate(self):
        """Navigate through application pages

        :id: da8b1242-364e-44ec-8a17-dd5d8047a386

        :expectedresults: Page is opened without errors

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for page in self.page_objects().values():
                page.navigate_to_entity()
                self.assertIsNotNone(session.nav.wait_until_element(
                    menu_locators['menu.current_text']))
                self.assertIsNone(session.nav.wait_until_element(
                    common_locators['alert.error'], timeout=1))
                self.assertIsNone(session.nav.wait_until_element(
                    common_locators['notif.error'], timeout=1))

    @tier1
    def test_positive_navigate_katello_foreman(self):
        """Navigate from katello application page to foreman one

        :id: dd4d5d3d-4902-4f85-968d-a9c46fce0b32

        :BZ: 1351464

        :expectedresults: Page is opened without errors
        """
        with Session(self) as session:
            self.products.navigate_to_entity()
            self.environment.navigate_to_entity()
            self.assertIsNotNone(session.nav.wait_until_element(
                menu_locators['menu.current_text']))
            self.assertIsNone(session.nav.wait_until_element(
                common_locators['alert.error'], timeout=1))
            self.assertIsNone(session.nav.wait_until_element(
                common_locators['notif.error'], timeout=1))
            self.assertIn('environments', self.browser.current_url)

    @tier1
    def test_positive_navigate_foreman_katello(self):
        """Navigate from foreman application page to katello one

        :id: b78a1fd3-47be-4956-99c0-e1b5d2d2c66a

        :expectedresults: Page is opened without errors
        """
        with Session(self) as session:
            self.architecture.navigate_to_entity()
            self.content_views.navigate_to_entity()
            self.assertIsNotNone(session.nav.wait_until_element(
                menu_locators['menu.current_text']))
            self.assertIsNone(session.nav.wait_until_element(
                common_locators['alert.error'], timeout=1))
            self.assertIsNone(session.nav.wait_until_element(
                common_locators['notif.error'], timeout=1))
            self.assertIn('content_views', self.browser.current_url)

    @tier1
    def test_positive_sat_logo_redirection(self):
        """Check that we can be redirected from current page using application
        logo in the top left section of the screen

        :id: 9f05ac85-3b0f-4220-b2b4-a9fd050f3dc0

        :BZ: 1394974

        :expectedresults: No error is raised after redirection and logo is
            still present on the page

        :CaseImportance: Critical
        """
        with Session(self) as session:
            pages = self.page_objects()
            for page_name in (
                    'Activation Key', 'Product', 'Domain', 'Location'):
                pages[page_name].navigate_to_entity()
                session.nav.click(common_locators['application_logo'])
                self.assertIsNotNone(session.nav.wait_until_element(
                    common_locators['application_logo']))
                self.assertIsNone(session.nav.wait_until_element(
                    common_locators['alert.error'], timeout=1))
