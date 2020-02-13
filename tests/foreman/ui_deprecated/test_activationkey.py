"""DEPRECATED UI FUNCTIONALITY"""
# import re
# from nailgun import entities
# from robottelo.constants import DISTRO_RHEL6, ENVIRONMENT
# from robottelo.decorators import skip_if_not_set, tier3, upgrade
# from robottelo.test import UITestCase
# from robottelo.ui.locators import locators
# from robottelo.ui.session import Session
# from robottelo.vm import VirtualMachine
# class ActivationKeyTestCase(UITestCase):
#     """Implements Activation key tests in UI"""
#     @classmethod
#     def setUpClass(cls):  # noqa
#         super(ActivationKeyTestCase, cls).setUpClass()
#         cls.organization = entities.Organization().create()
#         cls.base_key_name = entities.ActivationKey(
#             organization=cls.organization
#         ).create().name
#         cls.vm_distro = DISTRO_RHEL6
#
#     @skip_if_not_set('clients')
#     @tier3
#     @upgrade
#     def test_positive_open_associated_host(self):
#         """Associate content host with activation key, open activation key's
#         associated hosts, click on content host link
#         :id: 3dbe8370-f85b-416f-847f-7b7d81585bfc
#         :expectedresults: Redirected to specific content host page
#         :BZ: 1405166
#         :CaseLevel: System
#         """
#         ak = entities.ActivationKey(
#             environment=entities.LifecycleEnvironment(
#                 name=ENVIRONMENT,
#                 organization=self.organization,
#             ).search()[0],
#             organization=self.organization,
#         ).create()
#         with VirtualMachine(distro=self.vm_distro) as vm:
#             vm.install_katello_ca()
#             vm.register_contenthost(self.organization.label, ak.name)
#             self.assertTrue(vm.subscribed)
#             with Session(self) as session:
#                 session.nav.go_to_select_org(self.organization.name)
#                 host = self.activationkey.search_content_host(
#                     ak.name, vm.hostname)
#                 self.activationkey.click(host)
#                 chost_name = self.activationkey.wait_until_element(
#                     locators['contenthost.details_page.name'])
#                 self.assertIsNotNone(chost_name)
#                 self.assertEqual(chost_name.text, vm.hostname)
#                 # Ensure content host id is present in URL
#                 chost_id = entities.Host().search(query={
#                     'search': 'name={}'.format(vm.hostname)})[0].id
#                 chost_url_id = re.search(
#                     '(?<=content_hosts/)([0-9])+', self.browser.current_url)
#                 self.assertIsNotNone(chost_url_id)
#                 self.assertEqual(int(chost_url_id.group(0)), chost_id)
