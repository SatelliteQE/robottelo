"""DEPRECATED UI FUNCTIONALITY"""
# import time
# from fauxfactory import gen_string
# from nailgun import entities
# from robottelo import ssh
# from robottelo.constants import (
#     CHECKSUM_TYPE,
#     DOWNLOAD_POLICIES,
#     FAKE_0_PUPPET_REPO,
#     FAKE_1_PUPPET_REPO,
#     FAKE_1_YUM_REPO,
#     FAKE_2_YUM_REPO,
#     FAKE_YUM_DRPM_REPO,
#     FAKE_YUM_SRPM_REPO,
#     FEDORA26_OSTREE_REPO,
#     FEDORA27_OSTREE_REPO,
#     PUPPET_MODULE_NTP_PUPPETLABS,
#     REPO_TYPE,
#     RPM_TO_UPLOAD,
#     VALID_GPG_KEY_BETA_FILE,
#     VALID_GPG_KEY_FILE,
# )
# from robottelo.datafactory import (
#     generate_strings_list,
#     invalid_values_list,
# )
# from robottelo.decorators import (
#     bz_bug_is_open,
#     skip_if_bug_open,
#     stubbed,
#     tier1,
#     tier2,
#     tier4,
#     upgrade,
# )
# from robottelo.decorators.host import skip_if_os
# from robottelo.helpers import get_data_file, read_data_file
# from robottelo.host_info import get_host_os_version
# from robottelo.test import UITestCase
# from robottelo.ui.factory import make_contentview, make_repository, set_context
# from robottelo.ui.locators import (
#     common_locators,
#     locators,
#     tab_locators,
# )
# from robottelo.ui.session import Session
# from selenium.common.exceptions import NoSuchElementException
# class RepositoryTestCase(UITestCase):
#     """Implements Repos tests in UI"""
#     @classmethod
#     def setUpClass(cls):
#         super(RepositoryTestCase, cls).setUpClass()
#         # create instances to be shared across the sessions
#         cls.session_loc = entities.Location().create()
#         cls.session_prod = entities.Product(
#             organization=cls.session_org).create()
#     @classmethod
#     def set_session_org(cls):
#         """Creates new organization to be used for current session the
#         session_user will login automatically with this org in context
#         """
#         cls.session_org = entities.Organization().create()
#     def setup_navigate_syncnow(self, session, prd_name, repo_name):
#         """Helps with Navigation for syncing via the repos page."""
#         session.nav.go_to_select_org(self.session_org.name, force=False)
#         session.nav.go_to_products()
#         session.nav.click(locators['repo.select'] % prd_name)
#         session.nav.click(locators['repo.select_checkbox'] % repo_name)
#         session.nav.click(locators['repo.sync_now'])
#     def prd_sync_is_ok(self, repo_name):
#         """Asserts whether the sync Result is successful."""
#         self.repository.click(tab_locators['prd.tab_tasks'])
#         self.repository.click(locators['repo.select_event'] % repo_name)
#         timeout = time.time() + 60 * 10
#         spinner = self.repository.wait_until_element(
#             locators['repo.result_spinner'], 20)
#         # Waits until result spinner is visible on the UI or times out
#         # after 10mins
#         while spinner:
#             if time.time() > timeout:
#                 break
#             spinner = self.repository.wait_until_element(
#                 locators['repo.result_spinner'], 3)
#         result = self.repository.wait_until_element(
#             locators['repo.result_event']).text
#         return result == 'success'
#     @skip_if_os('RHEL6')
#     @tier1
#     def test_positive_create_custom_ostree_repo(self):
#         """Create Custom ostree repository.
#         :id: 852cccdc-7289-4d2f-b23a-7caad2dfa195
#         :expectedresults: Create custom ostree repository should be successful
#         :CaseImportance: Critical
#         """
#         prod = entities.Product(organization=self.session_org).create()
#         with Session(self) as session:
#             for repo_name in generate_strings_list(
#                     exclude_types=['numeric'], bug_id=1467722):
#                 with self.subTest(repo_name):
#                     session.nav.go_to_select_org(
#                         self.session_org.name, force=False)
#                     self.products.search_and_click(prod.name)
#                     make_repository(
#                         session,
#                         name=repo_name,
#                         repo_type=REPO_TYPE['ostree'],
#                         url=FEDORA27_OSTREE_REPO,
#                     )
#                     self.assertIsNotNone(self.repository.search(repo_name))
#     @skip_if_os('RHEL6')
#     @tier1
#     @upgrade
#     def test_positive_delete_custom_ostree_repo(self):
#         """Delete custom ostree repository.
#         :id: 87dcb236-4eb4-4897-9c2a-be1d0f4bc3e7
#         :expectedresults: Delete custom ostree repository should be successful
#         :CaseImportance: Critical
#         """
#         prod = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         # Creates new ostree repository using api
#         entities.Repository(
#             name=repo_name,
#             content_type='ostree',
#             url=FEDORA26_OSTREE_REPO,
#             product=prod,
#             unprotected=False,
#         ).create()
#         with Session(self) as session:
#             session.nav.go_to_select_org(self.session_org.name, force=False)
#             self.products.click(self.products.search(prod.name))
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.repository.delete(repo_name)
#     @skip_if_os('RHEL6')
#     @tier1
#     def test_positive_update_custom_ostree_repo_name(self):
#         """Update custom ostree repository name.
#         :id: 098ee88f-6cdb-45e0-850a-e1b71662f7ab
#         :Steps: Update repo name
#         :expectedresults: ostree repo name should be updated successfully
#         :CaseImportance: Critical
#         """
#         prod = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         new_repo_name_length = None
#         if bz_bug_is_open(1467722):
#             new_repo_name_length = 9
#         new_repo_name = gen_string('numeric', length=new_repo_name_length)
#         # Creates new ostree repository using api
#         entities.Repository(
#             name=repo_name,
#             content_type='ostree',
#             url=FEDORA26_OSTREE_REPO,
#             product=prod,
#             unprotected=False,
#         ).create()
#         with Session(self) as session:
#             session.nav.go_to_select_org(self.session_org.name, force=False)
#             self.products.click(self.products.search(prod.name))
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.repository.update(
#                 repo_name, new_name=new_repo_name)
#             self.products.search_and_click(prod.name)
#             self.assertIsNotNone(self.repository.search(new_repo_name))
#     @skip_if_os('RHEL6')
#     @tier1
#     def test_positive_update_custom_ostree_repo_url(self):
#         """Update custom ostree repository url.
#         :id: dfd392f9-6f1d-4d87-a43b-ced40606b8c2
#         :Steps: Update ostree repo URL
#         :expectedresults: ostree repo URL should be updated successfully
#         :CaseImportance: Critical
#         """
#         prod = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         # Creates new ostree repository using api
#         entities.Repository(
#             name=repo_name,
#             content_type='ostree',
#             url=FEDORA26_OSTREE_REPO,
#             product=prod,
#             unprotected=False,
#         ).create()
#         with Session(self) as session:
#             session.nav.go_to_select_org(self.session_org.name, force=False)
#             self.products.search_and_click(prod.name)
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.repository.update(
#                 repo_name,
#                 new_url=FEDORA27_OSTREE_REPO
#             )
#             self.products.search_and_click(prod.name)
#             # Validate the new repo URL
#             self.assertTrue(
#                 self.repository.validate_field(
#                     repo_name, 'url', FEDORA27_OSTREE_REPO
#                 )
#             )
#     @tier1
#     def test_positive_download_policy_displayed_for_yum_repos(self):
#         """Verify that YUM repositories can be created with download policy
#         :id: 8037a68b-66b8-4b42-a80b-fb08495f948d
#         :expectedresults: Dropdown for download policy is displayed for yum
#             repo
#         :CaseImportance: Critical
#         """
#         with Session(self) as session:
#             session.nav.go_to_select_org(self.session_org.name, force=False)
#             self.products.search_and_click(self.session_prod.name)
#             self.repository.navigate_to_entity()
#             self.repository.click(locators['repo.new'])
#             self.repository.assign_value(
#                 common_locators['name'], gen_string('alphanumeric'))
#             self.repository.assign_value(locators['repo.type'], 'yum')
#             self.assertIsNotNone(
#                 self.repository.find_element(locators['repo.download_policy'])
#             )
#     @skip_if_bug_open('bugzilla', 1378442)
#     @tier2
#     def test_positive_srpm_sync(self):
#         """Synchronize repository with SRPMs
#         :id: 1967a540-a265-4046-b87b-627524b63688
#         :expectedresults: srpms can be listed in repository
#         :CaseLevel: Integration
#         """
#         product = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         with Session(self) as session:
#             self.products.search_and_click(product.name)
#             make_repository(
#                 session,
#                 name=repo_name,
#                 url=FAKE_YUM_SRPM_REPO,
#             )
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.setup_navigate_syncnow(
#                 session,
#                 product.name,
#                 repo_name,
#             )
#             self.assertTrue(self.prd_sync_is_ok(repo_name))
#         result = ssh.command(
#             'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
#             '/custom/{}/{}/ | grep .src.rpm'
#             .format(
#                 self.session_org.label,
#                 product.label,
#                 repo_name,
#             )
#         )
#         self.assertEqual(result.return_code, 0)
#         self.assertGreaterEqual(len(result.stdout), 1)
#     @skip_if_bug_open('bugzilla', 1378442)
#     @tier2
#     def test_positive_srpm_sync_publish_cv(self):
#         """Synchronize repository with SRPMs, add repository to content view
#         and publish content view
#         :id: 2a57cbde-c616-440d-8bcb-6e18bd2d5c5f
#         :expectedresults: srpms can be listed in content view
#         :CaseLevel: Integration
#         """
#         product = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         cv_name = gen_string('alphanumeric')
#         with Session(self) as session:
#             self.products.search_and_click(product.name)
#             make_repository(
#                 session,
#                 name=repo_name,
#                 url=FAKE_YUM_SRPM_REPO,
#             )
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.setup_navigate_syncnow(
#                 session,
#                 product.name,
#                 repo_name,
#             )
#             self.assertTrue(self.prd_sync_is_ok(repo_name))
#             make_contentview(session, org=self.session_org.name, name=cv_name)
#             self.assertIsNotNone(self.content_views.search(cv_name))
#             self.content_views.add_remove_repos(cv_name, [repo_name])
#             self.assertIsNotNone(self.content_views.wait_until_element(
#                 common_locators['alert.success_sub_form']))
#             self.content_views.publish(cv_name)
#             self.assertIsNotNone(
#                 self.content_views.version_search(cv_name, 'Version 1.0'))
#         result = ssh.command(
#             'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
#             '/1.0/custom/{}/{}/ | grep .src.rpm'
#             .format(
#                 self.session_org.label,
#                 cv_name,
#                 product.label,
#                 repo_name,
#             )
#         )
#         self.assertEqual(result.return_code, 0)
#         self.assertGreaterEqual(len(result.stdout), 1)
#     @skip_if_bug_open('bugzilla', 1378442)
#     @tier2
#     @upgrade
#     def test_positive_srpm_sync_publish_promote_cv(self):
#         """Synchronize repository with SRPMs, add repository to content view,
#         publish and promote content view to lifecycle environment
#         :id: 4563d1c1-cdce-4838-a67f-c0a5d4e996a6
#         :expectedresults: srpms can be listed in content view in proper
#             lifecycle environment
#         :CaseLevel: Integration
#         """
#         lce = entities.LifecycleEnvironment(
#             organization=self.session_org).create()
#         product = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         cv_name = gen_string('alphanumeric')
#         with Session(self) as session:
#             self.products.search_and_click(product.name)
#             make_repository(
#                 session,
#                 name=repo_name,
#                 url=FAKE_YUM_SRPM_REPO,
#             )
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.setup_navigate_syncnow(
#                 session,
#                 product.name,
#                 repo_name,
#             )
#             self.assertTrue(self.prd_sync_is_ok(repo_name))
#             make_contentview(session, org=self.session_org.name, name=cv_name)
#             self.assertIsNotNone(self.content_views.search(cv_name))
#             self.content_views.add_remove_repos(cv_name, [repo_name])
#             self.assertIsNotNone(self.content_views.wait_until_element(
#                 common_locators['alert.success_sub_form']))
#             self.content_views.publish(cv_name)
#             self.assertIsNotNone(
#                 self.content_views.version_search(cv_name, 'Version 1.0'))
#             status = self.content_views.promote(cv_name, 'Version 1', lce.name)
#             self.assertIn('Promoted to {}'.format(lce.name), status)
#         result = ssh.command(
#             'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
#             ' | grep .src.rpm'
#             .format(
#                 self.session_org.label,
#                 lce.name,
#                 cv_name,
#                 product.label,
#                 repo_name,
#             )
#         )
#         self.assertEqual(result.return_code, 0)
#         self.assertGreaterEqual(len(result.stdout), 1)
#     @skip_if_bug_open('bugzilla', 1378442)
#     @tier2
#     def test_positive_drpm_sync(self):
#         """Synchronize repository with DRPMs
#         :id: 5e703d9a-ea26-4062-9d5c-d31bfbe87417
#         :expectedresults: drpms can be listed in repository
#         :CaseLevel: Integration
#         """
#         product = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         with Session(self) as session:
#             self.products.search_and_click(product.name)
#             make_repository(
#                 session,
#                 name=repo_name,
#                 url=FAKE_YUM_DRPM_REPO,
#             )
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.setup_navigate_syncnow(
#                 session,
#                 product.name,
#                 repo_name,
#             )
#             self.assertTrue(self.prd_sync_is_ok(repo_name))
#         result = ssh.command(
#             'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
#             '/custom/{}/{}/drpms/ | grep .drpm'
#             .format(
#                 self.session_org.label,
#                 product.label,
#                 repo_name,
#             )
#         )
#         self.assertEqual(result.return_code, 0)
#         self.assertGreaterEqual(len(result.stdout), 1)
#     @skip_if_bug_open('bugzilla', 1378442)
#     @tier2
#     def test_positive_drpm_sync_publish_cv(self):
#         """Synchronize repository with DRPMs, add repository to content view
#         and publish content view
#         :id: cffa862c-f972-4aa4-96b2-5a4513cb3eef
#         :expectedresults: drpms can be listed in content view
#         :CaseLevel: Integration
#         """
#         product = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         cv_name = gen_string('alphanumeric')
#         with Session(self) as session:
#             self.products.search_and_click(product.name)
#             make_repository(
#                 session,
#                 name=repo_name,
#                 url=FAKE_YUM_DRPM_REPO,
#             )
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.setup_navigate_syncnow(
#                 session,
#                 product.name,
#                 repo_name,
#             )
#             self.assertTrue(self.prd_sync_is_ok(repo_name))
#             make_contentview(session, org=self.session_org.name, name=cv_name)
#             self.assertIsNotNone(self.content_views.search(cv_name))
#             self.content_views.add_remove_repos(cv_name, [repo_name])
#             self.assertIsNotNone(self.content_views.wait_until_element(
#                 common_locators['alert.success_sub_form']))
#             self.content_views.publish(cv_name)
#             self.assertIsNotNone(
#                 self.content_views.version_search(cv_name, 'Version 1.0'))
#         result = ssh.command(
#             'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
#             '/1.0/custom/{}/{}/drpms/ | grep .drpm'
#             .format(
#                 self.session_org.label,
#                 cv_name,
#                 product.label,
#                 repo_name,
#             )
#         )
#         self.assertEqual(result.return_code, 0)
#         self.assertGreaterEqual(len(result.stdout), 1)
#     @skip_if_bug_open('bugzilla', 1378442)
#     @tier2
#     @upgrade
#     def test_positive_drpm_sync_publish_promote_cv(self):
#         """Synchronize repository with DRPMs, add repository to content view,
#         publish and promote content view to lifecycle environment
#         :id: e33ee07c-4677-4be8-bd53-73689edfda34
#         :expectedresults: drpms can be listed in content view in proper
#             lifecycle environment
#         :CaseLevel: Integration
#         """
#         lce = entities.LifecycleEnvironment(
#             organization=self.session_org).create()
#         product = entities.Product(organization=self.session_org).create()
#         repo_name = gen_string('alphanumeric')
#         cv_name = gen_string('alphanumeric')
#         with Session(self) as session:
#             self.products.search_and_click(product.name)
#             make_repository(
#                 session,
#                 name=repo_name,
#                 url=FAKE_YUM_DRPM_REPO,
#             )
#             self.assertIsNotNone(self.repository.search(repo_name))
#             self.setup_navigate_syncnow(
#                 session,
#                 product.name,
#                 repo_name,
#             )
#             self.assertTrue(self.prd_sync_is_ok(repo_name))
#             make_contentview(session, org=self.session_org.name, name=cv_name)
#             self.assertIsNotNone(self.content_views.search(cv_name))
#             self.content_views.add_remove_repos(cv_name, [repo_name])
#             self.assertIsNotNone(self.content_views.wait_until_element(
#                 common_locators['alert.success_sub_form']))
#             self.content_views.publish(cv_name)
#             self.assertIsNotNone(
#                 self.content_views.version_search(cv_name, 'Version 1.0'))
#             status = self.content_views.promote(cv_name, 'Version 1', lce.name)
#             self.assertIn('Promoted to {}'.format(lce.name), status)
#         result = ssh.command(
#             'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}'
#             '/drpms/ | grep .drpm'
#             .format(
#                 self.session_org.label,
#                 lce.name,
#                 cv_name,
#                 product.label,
#                 repo_name,
#             )
#         )
#         self.assertEqual(result.return_code, 0)
#         self.assertGreaterEqual(len(result.stdout), 1)
