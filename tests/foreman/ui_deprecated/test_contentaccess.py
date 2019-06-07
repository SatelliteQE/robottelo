"""DEPRECATED UI FUNCTIONALITY"""

# """
# from nailgun import entities

# from robottelo import manifests
# from robottelo.api.utils import call_entity_method_with_timeout
# from robottelo.config import settings
# from robottelo.constants import (
#     DISTRO_RHEL7,
#     ENVIRONMENT,
#     REAL_RHEL7_0_0_PACKAGE,
#     REAL_RHEL7_0_1_PACKAGE,
#     REAL_RHEL7_0_ERRATA_ID,
#     REPOS,
#     REPOSET,
#     PRDS,
# )
# from robottelo.cli.factory import (
#     setup_cdn_and_custom_repositories,
#     setup_virtual_machine,
# )
# from robottelo.decorators import (
#     run_in_one_thread,
#     skip_if_not_set,
#     stubbed,
#     tier1,
#     tier2,
# )
# from robottelo.test import UITestCase
# from robottelo.ui.factory import set_context
# from robottelo.ui.locators import common_locators, locators, tab_locators
# from robottelo.ui.session import Session
# from robottelo.vm import VirtualMachine


# org_environment_full_message = (
#     'Access to repositories is unrestricted in this organization. Hosts can'
#     ' consume all repositories available in the Content View they are '
#     'registered to, regardless of subscription status.'
# )


# @run_in_one_thread
# class ContentAccessTestCase(UITestCase):
#     """Implements Content Access (Golden Ticket) tests in UI"""

#     @classmethod
#     def set_session_org(cls):
#         """Create an organization for tests, which will be selected
#         automatically

#         This method should set `session_org` to a new Org or reuse existing
#         org that has Golden ticket enabled
#         """
#         cls.session_org = entities.Organization().create()

#     @classmethod
#     @skip_if_not_set('clients', 'fake_manifest')
#     def setUpClass(cls):
#         """Setup must ensure the current `session_org`  has Golden Ticket
#         enabled.

#         Option 1) SQL::

#             UPDATE
#                  cp_owner
#             SET
#                  content_access_mode = 'org_environment',
#                  content_access_mode_list='entitlement,org_environment'
#             WHERE account='{org.label}';

#         Option 2) manifest::

#             Change manifest file as it looks like:

#                 Consumer:
#                     Name: ExampleCorp
#                     UUID: c319a1d8-4b30-44cd-b2cf-2ccba4b9a8db
#                     Content Access Mode: org_environment
#                     Type: satellite

#         :steps:

#             1. Create a Product and CV for current session_org.
#             2. Use either option 1 or option 2 (described above) to activate
#                the Golden Ticket.
#             3. Add a repository pointing to a real repo which requires a
#                RedHat subscription to access.
#             4. Create Content Host and assign that gated repos to it.
#             5. Sync the gated repository.

#         """
#         super(ContentAccessTestCase, cls).setUpClass()
#         # upload organization manifest with org environment access enabled
#         manifests.upload_manifest_locked(
#             cls.session_org.id,
#             manifests.clone(org_environment_access=True)
#         )
#         # Create repositories
#         cls.repos = [
#             # Red Hat Enterprise Linux 7
#             {
#                 'product': PRDS['rhel'],
#                 'repository-set': REPOSET['rhel7'],
#                 'repository': REPOS['rhel7']['name'],
#                 'repository-id': REPOS['rhel7']['id'],
#                 'releasever': REPOS['rhel7']['releasever'],
#                 'arch': REPOS['rhel7']['arch'],
#                 'cdn': True,
#             },
#             # Red Hat Satellite Tools
#             {
#                 'product': PRDS['rhel'],
#                 'repository-set': REPOSET['rhst7'],
#                 'repository': REPOS['rhst7']['name'],
#                 'repository-id': REPOS['rhst7']['id'],
#                 'url': settings.sattools_repo['rhel7'],
#                 'cdn': bool(
#                     settings.cdn or not settings.sattools_repo['rhel7']),
#             },
#         ]
#         cls.custom_product, cls.repos_info = setup_cdn_and_custom_repositories(
#             cls.session_org.id, cls.repos)
#         # Create a content view
#         content_view = entities.ContentView(
#             organization=cls.session_org,
#             repository=[entities.Repository(id=repo_info['id'])
#                         for repo_info in cls.repos_info],
#         ).create()
#         # Publish the content view
#         call_entity_method_with_timeout(content_view.publish, timeout=1500)
#         cls.content_view = content_view.read()
#         # create an activation only for testing org environment info message
#         # displayed tests
#         cls.activation_key = entities.ActivationKey(
#             organization=cls.session_org).create()

#     def _setup_virtual_machine(self, vm):
#         """Make the initial virtual machine setup

#         :param VirtualMachine vm: The virtual machine setup
#         """
#         setup_virtual_machine(
#             vm,
#             self.session_org.label,
#             rh_repos_id=[
#                 repo['repository-id'] for repo in self.repos if repo['cdn']
#             ],
#             product_label=self.custom_product['label'],
#             repos_label=[
#                 repo['label'] for repo in self.repos_info
#                 if repo['red-hat-repository'] == 'no'
#             ],
#             lce=ENVIRONMENT,
#             patch_os_release_distro=DISTRO_RHEL7,
#             install_katello_agent=True,
#         )

#     @tier2
#     def test_positive_list_installable_updates(self):
#         """Access content hosts and assert all updates are listed on
#         packages tab updates and not only those for attached subscriptions.

#         :id: 30783c91-c665-4c39-8b3b-b7456bde76f2

#         :steps:

#             1. Access Content-Host listing page.

#         :CaseAutomation: notautomated

#         :expectedresults:
#             1. All updates are available independent of subscription because
#                Golden Ticket is enabled.
#         """
#         with VirtualMachine(distro=DISTRO_RHEL7) as vm:
#             self._setup_virtual_machine(vm)
#             # install a the packages that has updates with errata
#             result = vm.run(
#                 'yum install -y {0}'.format(REAL_RHEL7_0_0_PACKAGE))
#             self.assertEqual(result.return_code, 0)
#             result = vm.run('rpm -q {0}'.format(REAL_RHEL7_0_0_PACKAGE))
#             self.assertEqual(result.return_code, 0)
#             # check that package errata is applicable
#             with Session(self) as session:
#                 set_context(session, org=self.session_org.name)
#                 self.assertIsNotNone(
#                     session.contenthost.errata_search(
#                         vm.hostname, REAL_RHEL7_0_ERRATA_ID)
#                 )

#     @tier2
#     def test_positive_list_available_packages(self):
#         """Access content hosts and assert all packages are listed on
#         installable updates and not only those for attached subscriptions.

#         :id: 37383e25-7b1d-433e-9e05-faaa8ec70ee8

#         :steps:

#             1. Access Content-Host Packages tab.

#         :CaseAutomation: notautomated

#         :expectedresults:
#             1. All packages are available independent
#                of subscription because Golden Ticket is enabled.
#         """
#         with VirtualMachine(distro=DISTRO_RHEL7) as vm:
#             self._setup_virtual_machine(vm)
#             # install a the packages that has updates with errata
#             result = vm.run(
#                 'yum install -y {0}'.format(REAL_RHEL7_0_0_PACKAGE))
#             self.assertEqual(result.return_code, 0)
#             result = vm.run('rpm -q {0}'.format(REAL_RHEL7_0_0_PACKAGE))
#             self.assertEqual(result.return_code, 0)
#             # force host to generate/refresh errata applicability
#             host = entities.Host(
#                 name=vm.hostname,
#                 organization=self.session_org
#             ).search()[0].read()
#             call_entity_method_with_timeout(
#                 host.errata_applicability, timeout=600)
#             # check that package errata is applicable
#             with Session(self) as session:
#                 set_context(session, org=self.session_org.name)
#                 self.assertIsNotNone(
#                     session.contenthost.package_search(
#                         vm.hostname,
#                         REAL_RHEL7_0_1_PACKAGE,
#                         package_tab='applicable'
#                     )
#                 )

#     @tier1
#     def test_positive_visual_indicator_on_hosts_subscription(self):
#         """Access content hosts subscription tab and assert a visual indicator
#         is present highlighting that organization hosts have unrestricted
#         access to repository content.

#         :id: f8fc0bd2-c92f-4706-9921-4e331762170d

#         :steps:

#             1. Access Content-Host Subscription tab.

#         :CaseAutomation: automated

#         :expectedresults:
#             1. A visual alert is present at the top of the subscription tab
#                saying: "Access to repositories is unrestricted in
#                this organization. Hosts can consume all repositories available
#                in the Content View they are registered to, regardless of
#                subscription status".

#         :CaseImportance: Critical
#         """
#         with VirtualMachine(distro=DISTRO_RHEL7) as client:
#             client.install_katello_ca()
#             client.register_contenthost(
#                 self.session_org.label, lce=ENVIRONMENT)
#             self.assertTrue(client.subscribed)
#             with Session(self) as session:
#                 set_context(session, org=self.session_org.name)
#                 session.contenthost.search_and_click(client.hostname)
#                 session.contenthost.click(
#                     tab_locators['contenthost.tab_subscriptions'])
#                 session.contenthost.click(
#                     tab_locators[
#                         'contenthost.tab_subscriptions_subscriptions'])
#                 info_element = session.subscriptions.wait_until_element(
#                     common_locators['org_environment_info'])
#                 self.assertIsNotNone(info_element)
#                 self.assertIn(
#                     org_environment_full_message,
#                     info_element.text
#                 )

#     @tier1
#     def test_positive_visual_indicator_on_activation_key_details(self):
#         """Access AK details subscription tab and assert a visual indicator
#         is present highlighting that organization hosts have unrestricted
#         access to repository content.

#         :id: 94ba1113-11cb-43b2-882e-bf45b5355d9b

#         :steps:

#             1. Access Ak details Subscription tab.

#         :CaseAutomation: automated

#         :expectedresults:
#             1. A visual alert is present at the top of the subscription tab
#                saying: "Access to repositories is unrestricted in this
#                organization. Hosts can consume all repositories available in
#                the Content View they are registered to, regardless of
#                subscription status".

#         :CaseImportance: Critical
#         """
#         with Session(self) as session:
#             set_context(session, org=self.session_org.name)
#             session.activationkey.search_and_click(self.activation_key.name)
#             session.activationkey.click(tab_locators['ak.subscriptions'])
#             info_element = session.subscriptions.wait_until_element(
#                 common_locators['org_environment_info'])
#             self.assertIsNotNone(info_element)
#             self.assertIn(
#                 org_environment_full_message,
#                 info_element.text
#             )

#     @tier1
#     def test_positive_visual_indicator_on_manifest(self):
#         """Access org manifest page and assert a visual indicator
#         is present highlighting that organization hosts have unrestricted
#         access to repository content.

#         :id: a9c2d2b7-17ab-441b-978d-24dc80f35a4b

#         :steps:

#             1. Access org manifest page.

#         :CaseAutomation: automated

#         :expectedresults:
#             1. A visual alert is present at the top of the
#                subscription tab saying: "Access to repositories is unrestricted
#                in this organization. Hosts can consume all repositories
#                available in the Content View they are registered to, regardless
#                of subscription status".

#         :CaseImportance: Critical
#         """
#         with Session(self) as session:
#             set_context(session, org=self.session_org.name)
#             session.subscriptions.navigate_to_entity()
#             if not session.subscriptions.wait_until_element(
#                     locators.subs.upload, timeout=1):
#                 session.subscriptions.click(locators.subs.manage_manifest)
#             info_element = session.subscriptions.wait_until_element(
#                 common_locators['org_environment_info'])
#             self.assertIsNotNone(info_element)
#             self.assertIn(
#                 org_environment_full_message,
#                 info_element.text
#             )

#     @tier1
#     def test_negative_visual_indicator_with_restricted_subscription(self):
#         """Access AK details subscription tab and assert a visual indicator
#         is NOT present if organization has no Golden Ticket Enabled.

#         :id: ce5f3017-a449-45e6-8709-7d4f7b5f7a4d

#         :steps:

#             1. Change to a restricted organization (with no GT enabled).
#             2. Access Ak details Subscription tab.

#         :CaseAutomation: automated

#         :expectedresults:
#             1. Assert GoldenTicket  visual alert is NOT present.

#         :CaseImportance: Critical
#         """
#         org = entities.Organization().create()
#         self.upload_manifest(org.id, manifests.clone())
#         activation_key = entities.ActivationKey(organization=org).create()
#         with Session(self) as session:
#             set_context(session, org=org.name, force_context=True)
#             session.activationkey.search_and_click(activation_key.name)
#             session.activationkey.click(tab_locators['ak.subscriptions'])
#             self.assertIsNone(
#                 session.subscriptions.wait_until_element(
#                     common_locators['org_environment_info'])
#             )

#     @tier2
#     @stubbed()
#     def test_negative_list_available_packages(self):
#         """Access content hosts and assert restricted packages are not listed
#         on installable updates but only those for attached subscriptions.

#         :id: 87a502ff-bb3c-4da4-ab88-b49a4fcdf3fb

#         :steps:

#             1. Change to a restricted organization (with no GT enabled).
#             2. Access Content-Host Packages tab.

#         :CaseAutomation: notautomated

#         :expectedresults:
#             1. Restricted packages are NOT available but only
#                those for atached subscriptions because Golden Ticket is NOT
#                enabled.
#         """
