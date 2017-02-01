# -*- encoding: utf-8 -*-
"""Test class for Login UI

@Requirement: Navigation

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import skip_if_bug_open, tier1
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

    @tier1
    def test_positive_navigate(self):
        """Navigate through application pages

        @id: da8b1242-364e-44ec-8a17-dd5d8047a386

        @Assert: Page is opened without errors
        """
        with Session(self.browser) as session:
            for name, page in self.page_objects().items():
                    page.navigate_to_entity()
                    self.assertIsNotNone(session.nav.wait_until_element(
                        menu_locators['menu.current_text']))
                    self.assertIsNone(session.nav.wait_until_element(
                        common_locators['alert.error'], timeout=1))
                    self.assertIsNone(session.nav.wait_until_element(
                        common_locators['notif.error'], timeout=1))

    @skip_if_bug_open('bugzilla', 1394974)
    @tier1
    def test_positive_sat_logo_redirection(self):
        """Check that we can be redirected from current page using application
        logo in the top left section of the screen

        @id: 9f05ac85-3b0f-4220-b2b4-a9fd050f3dc0

        @BZ: 1394974

        @Assert: No error is raised after redirection and logo is still present
        on the page
        """
        with Session(self.browser) as session:
            for name, page in self.page_objects().items():
                if name in ['Activation Key', 'Product', 'Domain', 'Location']:
                    page.navigate_to_entity()
                    session.nav.click(common_locators['application_logo'])
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['application_logo']))
                    self.assertIsNone(session.nav.wait_until_element(
                        common_locators['alert.error'], timeout=1))
