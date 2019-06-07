"""DEPRECATED UI FUNCTIONALITY"""

# """
# from six.moves.urllib.parse import urljoin
# from nailgun import entities

# from robottelo.cleanup import vm_cleanup
# from robottelo.cli.factory import (
#     setup_org_for_a_custom_repo,
#     setup_org_for_a_rh_repo,
# )
# from robottelo.config import settings
# from robottelo.constants import (
#     DISTRO_RHEL7,
#     FAKE_1_YUM_REPO,
#     FAKE_6_YUM_REPO,
#     PRDS,
#     REPOS,
#     REPOSET,
# )
# from robottelo.decorators import (
#     bz_bug_is_open,
#     run_in_one_thread,
#     skip_if_bug_open,
#     skip_if_not_set,
#     stubbed,
#     tier3,
#     upgrade
# )
# from robottelo.test import UITestCase
# from robottelo.ui.locators import common_locators, tab_locators
# from robottelo.ui.session import Session
# from robottelo.vm import VirtualMachine


# @run_in_one_thread
# class ContentHostTestCase(UITestCase):
#     """Implements Content Host tests in UI"""

#     @classmethod
#     def set_session_org(cls):
#         """Create an organization for tests, which will be selected
#         automatically"""
#         cls.session_org = entities.Organization().create()

#     @classmethod
#     @skip_if_not_set('clients', 'fake_manifest')
#     def setUpClass(cls):
#         """Create Lifecycle Environment, Content View and Activation key
#         """
#         super(ContentHostTestCase, cls).setUpClass()
#         cls.env = entities.LifecycleEnvironment(
#             organization=cls.session_org).create()
#         cls.content_view = entities.ContentView(
#             organization=cls.session_org).create()
#         cls.activation_key = entities.ActivationKey(
#             environment=cls.env,
#             organization=cls.session_org,
#         ).create()
#         setup_org_for_a_rh_repo({
#             'product': PRDS['rhel'],
#             'repository-set': REPOSET['rhst7'],
#             'repository': REPOS['rhst7']['name'],
#             'organization-id': cls.session_org.id,
#             'content-view-id': cls.content_view.id,
#             'lifecycle-environment-id': cls.env.id,
#             'activationkey-id': cls.activation_key.id,
#         }, force_manifest_upload=True)
#         setup_org_for_a_custom_repo({
#             'url': FAKE_1_YUM_REPO,
#             'organization-id': cls.session_org.id,
#             'content-view-id': cls.content_view.id,
#             'lifecycle-environment-id': cls.env.id,
#             'activationkey-id': cls.activation_key.id,
#         })
#         setup_org_for_a_custom_repo({
#             'url': FAKE_6_YUM_REPO,
#             'organization-id': cls.session_org.id,
#             'content-view-id': cls.content_view.id,
#             'lifecycle-environment-id': cls.env.id,
#             'activationkey-id': cls.activation_key.id,
#         })

#     def setUp(self):
#         """Create a VM, subscribe it to satellite-tools repo, install
#         katello-ca and katello-agent packages"""
#         super(ContentHostTestCase, self).setUp()
#         self.client = VirtualMachine(distro=DISTRO_RHEL7)
#         self.addCleanup(vm_cleanup, self.client)
#         self.client.create()
#         self.client.install_katello_ca()
#         self.client.register_contenthost(
#             self.session_org.label, self.activation_key.name)
#         self.assertTrue(self.client.subscribed)
#         self.client.enable_repo(REPOS['rhst7']['id'])
#         self.client.install_katello_agent()

#     @tier3
#     def test_positive_sort_by_last_checkin(self):
#         """Register two content hosts and then sort them by last checkin date

#         :id: c42c1347-8b3a-4ba7-95d1-609e2e9ec40e

#         :customerscenario: true

#         :expectedresults: Validate that content hosts are sorted properly

#         :BZ: 1281251

#         :CaseLevel: System
#         """
#         with VirtualMachine(distro=DISTRO_RHEL7) as vm:
#             vm.install_katello_ca()
#             vm.register_contenthost(
#                 self.session_org.label, self.activation_key.name)
#             self.assertTrue(vm.subscribed)
#             vm.enable_repo(REPOS['rhst7']['id'])
#             vm.install_katello_agent()
#             with Session(self):
#                 self.assertIsNotNone(
#                     self.contenthost.search(self.client.hostname))
#                 if bz_bug_is_open(1495271):
#                     self.dashboard.navigate_to_entity()
#                 self.assertIsNotNone(self.contenthost.search(vm.hostname))
#                 self.contenthost.click(common_locators['kt_clear_search'])
#                 if bz_bug_is_open(1495271):
#                     self.dashboard.navigate_to_entity()
#                     self.contenthost.navigate_to_entity()
#                 # In case we have a lot of unregistered hosts
#                 # fixme: Should be replaced with loop across all pages
#                 self.contenthost.assign_value(
#                     common_locators['table_per_page'], '100')
#                 # prevent any issues in case some default sorting was set
#                 self.contenthost.sort_table_by_column('Name')
#                 dates = self.contenthost.sort_table_by_column('Last Checkin')
#                 checked_in_dates = [date for date in dates
#                                     if date != 'Never checked in']
#                 self.assertGreater(checked_in_dates[1], checked_in_dates[0])
#                 dates = self.contenthost.sort_table_by_column('Last Checkin')
#                 self.assertGreater(dates[0], dates[1])

#     @skip_if_bug_open('bugzilla', 1351464)
#     @skip_if_bug_open('bugzilla', 1387892)
#     @tier3
#     def test_positive_provisioning_host_link(self):
#         """Check that the host link in provisioning tab of content host page
#         point to the host details page.

#         :id: 28f5fb0e-007b-4ee6-876e-9693fb7f5841

#         :expectedresults: The Provisioning host details name link at
#             content_hosts/provisioning point to host detail page eg:
#             hosts/hostname

#         :BZ: 1387892

#         :CaseLevel: System
#         """
#         with Session(self):
#             # open the content host
#             self.contenthost.search_and_click(self.client.hostname)
#             # open the provisioning tab of the content host
#             self.contenthost.click(
#                 tab_locators['contenthost.tab_provisioning_details'])
#             # click the name field value that contain the hostname
#             self.contenthost.click(
#                 tab_locators['contenthost.tab_provisioning_details_host_link'])
#             # assert that the current url is equal to:
#             # server_host_url/hosts/hostname
#             host_url = urljoin(settings.server.get_url(),
#                                'hosts/{0}'.format(self.client.hostname))
#             self.assertEqual(self.browser.current_url, host_url)

#     @tier3
#     @upgrade
#     @stubbed()
#     def test_positive_bulk_add_subscriptions(self):
#         """Add a subscription to more than one content host, using bulk actions.

#         :id: a427c77f-100d-4af5-9248-6f806db364ef

#         :steps:

#             1. Upload a manifest with, or use an existing, subscription
#             2. Register multiple hosts to the current organization
#             3. Select all of those hosts
#             4. Navigate to the bulk subscriptions page
#             5. Select and add a subscription to the hosts

#         :expectedresults: The subscriptions are successfully attached to the
#             hosts

#         :CaseLevel: System
#         """

#     @tier3
#     @stubbed()
#     def test_positive_bulk_remove_subscriptions(self):
#         """Remove a subscription to more than one content host, using bulk
#         actions.

#         :id: f74b829e-d888-4caf-a25e-ca64b073a3fc

#         :steps:

#             1. Upload a manifest with, or use an existing, subscription
#             2. Register multiple hosts to the current organization
#             3. Select all of those hosts
#             4. Navigate to the bulk subscriptions page
#             5. Select and add a subscription to the hosts
#             6. Verify that the subscriptions were added
#             7. Reselect all the hosts from step 3
#             8. Navigate to the bulk subscriptions page
#             9. Select the subscription added in step 5 and remove it

#         :expectedresults: The subscriptions are successfully removed from the
#             hosts

#         :CaseLevel: System
#         """
