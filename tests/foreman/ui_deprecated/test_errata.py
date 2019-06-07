"""DEPRECATED UI FUNCTIONALITY"""

# from nailgun import entities
# from robottelo.api.utils import enable_rhrepo_and_fetchid
# from robottelo.cli.factory import (
#     setup_org_for_a_custom_repo,
#     setup_org_for_a_rh_repo,
# )
# from robottelo.constants import (
#     DEFAULT_ARCHITECTURE,
#     DEFAULT_RELEASE_VERSION,
#     DISTRO_RHEL7,
#     FAKE_1_CUSTOM_PACKAGE,
#     FAKE_2_CUSTOM_PACKAGE,
#     FAKE_2_ERRATA_ID,
#     FAKE_6_YUM_REPO,
#     PRDS,
#     REAL_0_ERRATA_ID,
#     REAL_4_ERRATA_ID,
#     REAL_4_ERRATA_CVES,
#     REAL_4_ERRATA_DETAILS,
#     REPOS,
#     REPOSET,
#     TOOLS_ERRATA_TABLE_DETAILS,
# )
# from robottelo.decorators import (
#     run_in_one_thread,
#     skip_if_not_set,
#     stubbed,
#     tier2,
#     tier3,
# )
# from robottelo.test import UITestCase
# from robottelo.ui.session import Session
# from robottelo.vm import VirtualMachine


# CUSTOM_REPO_URL = FAKE_6_YUM_REPO
# CUSTOM_REPO_ERRATA_ID = FAKE_2_ERRATA_ID


# @run_in_one_thread
# class ErrataTestCase(UITestCase):
#     """UI Tests for the errata management feature"""

#     @classmethod
#     def set_session_org(cls):
#         """Create an organization for tests, which will be selected
#         automatically"""
#         cls.session_org = entities.Organization().create()

#     @classmethod
#     @skip_if_not_set('clients', 'fake_manifest')
#     def setUpClass(cls):
#         """Set up single org with subscription to 1 RH and 1 custom products to
#         reuse in tests
#         """
#         super(ErrataTestCase, cls).setUpClass()
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
#         cls.custom_entitites = setup_org_for_a_custom_repo({
#             'url': CUSTOM_REPO_URL,
#             'organization-id': cls.session_org.id,
#             'content-view-id': cls.content_view.id,
#             'lifecycle-environment-id': cls.env.id,
#             'activationkey-id': cls.activation_key.id,
#         })
#         rhva_repo = enable_rhrepo_and_fetchid(
#             basearch=DEFAULT_ARCHITECTURE,
#             org_id=cls.session_org.id,
#             product=PRDS['rhel'],
#             repo=REPOS['rhva6']['name'],
#             reposet=REPOSET['rhva6'],
#             releasever=DEFAULT_RELEASE_VERSION,
#         )
#         assert entities.Repository(id=rhva_repo).sync()['result'] == 'success'
#         cls.rhva_errata_id = REAL_4_ERRATA_ID
#         cls.rhva_errata_cves = REAL_4_ERRATA_CVES

#     @stubbed()
#     @tier2
#     def test_positive_sort(self):
#         """Sort the columns of Errata page

#         :id: 213b8592-ccb5-485d-b5fa-e445b853b20c

#         :Setup: Errata synced on satellite server.

#         :Steps:

#             1. Go to Content -> Errata.
#             2. Sort by Errata Id, Title, Type, Affected Content Hosts, Updated.

#         :expectedresults: Errata is sorted by selected column.

#         :CaseAutomation: notautomated

#         :CaseLevel: Integration
#         """

#     @tier3
#     def test_positive_apply_for_host(self):
#         """Apply an erratum for selected content hosts

#         :id: 442d1c20-bf7e-4e4c-9a48-ab3f4809fa61

#         :customerscenario: true

#         :Setup: Errata synced on satellite server.

#         :Steps:

#             1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
#             2. Select few Content Hosts and apply the erratum.

#         :expectedresults: Check that the erratum is applied in the selected
#             content hosts.

#         :CaseLevel: System
#         """
#         with VirtualMachine(distro=DISTRO_RHEL7) as client:
#             client.install_katello_ca()
#             client.register_contenthost(
#                 self.session_org.label,
#                 self.activation_key.name,
#             )
#             self.assertTrue(client.subscribed)
#             client.enable_repo(REPOS['rhst7']['id'])
#             client.install_katello_agent()
#             client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
#             with Session(self):
#                 result = self.errata.install(
#                     CUSTOM_REPO_ERRATA_ID, client.hostname)
#                 self.assertEqual(result, 'success')
#                 self.assertIsNotNone(self.contenthost.package_search(
#                     client.hostname, FAKE_2_CUSTOM_PACKAGE))

#     @tier2
#     def test_positive_view(self):
#         """View erratum similar to RH Customer portal

#         :id: 7d0814fd-70e8-4451-ac96-c632cae55731

#         :Setup: Errata synced on satellite server.

#         :Steps: Go to Content -> Errata. Review the Errata page.

#         :expectedresults: The following fields: Errata Id, Title, Type,
#             Affected Content Hosts, Updated has expected values for errata
#             table.

#         :CaseLevel: Integration
#         """
#         with Session(self):
#             self.errata.validate_table_fields(
#                 REAL_0_ERRATA_ID,
#                 only_applicable=False,
#                 values_list=TOOLS_ERRATA_TABLE_DETAILS
#             )

#     @tier2
#     def test_positive_view_details(self):
#         """View erratum details similar to RH Customer portal

#         :id: c00aeacc-eefb-4371-a0ee-5a68041a16a2

#         :Setup: Errata synced on satellite server.

#         :Steps: Go to Content -> Errata.  Select an Errata -> Details tab.

#         :expectedresults: The following fields are displayed: : Advisory, CVEs,
#             Type, Severity, Issued, Last Update on, Reboot Suggested, Topic,
#             Description, Solution, Affected Packages.

#         :CaseLevel: Integration
#         """
#         with Session(self):
#             self.errata.check_errata_details(
#                 REAL_4_ERRATA_ID,
#                 REAL_4_ERRATA_DETAILS,
#                 only_applicable=False,
#             )

#     @tier2
#     def test_positive_view_products_and_repos(self):
#         """View a list of products/repositories for an erratum

#         :id: 3023006d-514f-436a-b12b-dc08d9609fa6

#         :Setup: Errata synced on satellite server.

#         :Steps: Go to Content -> Errata.  Select an Errata -> Repositories tab.

#         :expectedresults: The Repositories tab lists affected Products and
#             Repositories.

#         :CaseLevel: Integration
#         """
#         product = entities.Product(
#             id=self.custom_entitites['product-id']).read()
#         repo = entities.Repository(
#             id=self.custom_entitites['repository-id']).read()
#         with Session(self):
#             self.assertIsNotNone(
#                 self.errata.repository_search(
#                     CUSTOM_REPO_ERRATA_ID,
#                     repo.name,
#                     product.name,
#                     only_applicable=False,
#                 )
#             )

#     @tier2
#     def test_positive_search_autocomplete(self):
#         """Check if autocomplete works in search field of Errata page

#         :id: d93941d9-faad-4a31-9815-87dff9132082

#         :Setup: Errata synced on satellite server.

#         :Steps: Go to Content -> Errata.

#         :expectedresults: Check if autocomplete works in search field of Errata
#             page.

#         :CaseLevel: Integration
#         """
#         with Session(self):
#             self.assertIsNotNone(
#                 self.errata.auto_complete_search(
#                     CUSTOM_REPO_ERRATA_ID, only_applicable=False)
#             )

#     @stubbed()
#     @tier2
#     def test_positive_search_redirect(self):
#         """Check if all the errata searches are redirected to the new
#         errata page

#         :id: 3de38510-d0d9-447e-8dee-a3aadba1f3c7

#         :Setup: Errata synced on satellite server.

#         :Steps:

#             1. Go to Content -> Products -> Repositories -> Click on any of the
#                 errata hyperlink.
#             2. Go to Content -> Products -> Repositories -> Click on a
#                 repository-> Click on any of the errata hyperlink.
#             3. Go to Content -> Content Views -> Select a Content View -> Yum
#                 Content -> Click on any of the errata hyperlink.
#             4. Go to Content -> Content Views -> Select a Content View -> Yum
#                 Content -> Filters -> Select a Filter -> Click on any of the
#                 errata hyperlink.

#         :expectedresults: Check if all the above mentioned scenarios redirect
#             to the new errata page.

#         :CaseAutomation: notautomated

#         :CaseLevel: Integration
#         """

#     @stubbed()
#     @tier3
#     def test_positive_incremental_update(self):
#         """Update composite content views and environments with new
#         point releases

#         :id: d30bae6f-e45f-4ba9-9151-32dfa14ed2b8

#         :Setup:

#             1. Errata synced on satellite server.
#             2. Composite content views present.

#         :Steps: As a user, I would expect updated point releases to update
#             composites with a new point release as well in the respective
#             environments (i.e. if ComponentA gets updated from 1.0 to 1.1, any
#             composite that is using 1.0 will have a new point release bumped
#             and published with the new 1.1 ComponentA and pushed to the
#             environment it was in.

#         :expectedresults: Composite content views updated with point releases.

#         :CaseAutomation: notautomated

#         :CaseLevel: System
#         """
