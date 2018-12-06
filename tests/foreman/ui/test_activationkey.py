# -*- encoding: utf-8 -*-
"""Test class for Activation key UI

:Requirement: Activationkey

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import re
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import DISTRO_RHEL6, ENVIRONMENT
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier3,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_activationkey, set_context
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


class ActivationKeyTestCase(UITestCase):
    """Implements Activation key tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(ActivationKeyTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.base_key_name = entities.ActivationKey(
            organization=cls.organization
        ).create().name
        cls.vm_distro = DISTRO_RHEL6

    @tier1
    def test_positive_create_with_name(self):
        """Create Activation key for all variations of Activation key
        name

        :id: 091f1034-9850-4004-a0ca-d398d1626a5e

        :expectedresults: Activation key is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                    )
                    self.assertIsNotNone(self.activationkey.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Activation key with description

        :id: 4c8f4dca-723f-4dae-a8df-4e00a7fc7d95

        :expectedresults: Activation key is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                description=gen_string('utf8'),
            )
            self.assertIsNotNone(self.activationkey.search(name))

    @tier1
    def test_positive_create_with_usage_limit(self):
        """Create Activation key with finite Usage limit

        :id: cd45363e-8a79-4aa4-be97-885aea9434c9

        :expectedresults: Activation key is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                limit='6',
            )
            self.assertIsNotNone(self.activationkey.search(name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Activation key with invalid Name

        :id: 143ca57d-89ff-45e0-99cf-4d4033ea3690

        :expectedresults: Activation key is not created. Appropriate error
            shown.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                    )
                    self.assertIsNotNone(self.activationkey.wait_until_element(
                        common_locators['common_invalid']))
                    self.assertIsNone(self.activationkey.search(name))

    @tier1
    def test_negative_create_with_invalid_limit(self):
        """Create Activation key with invalid Usage Limit. Both with too
        long numbers and using letters.

        :id: 71ecf5b2-ce4f-41b0-b30d-45f89713f8c1

        :expectedresults: Activation key is not created. Appropriate error
            shown.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            for limit in invalid_names_list():
                with self.subTest(limit):
                    name = gen_string('alpha')
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                        limit=limit,
                    )
                    self.assertIsNotNone(self.activationkey.wait_until_element(
                        common_locators['invalid_limit']))
                    self.assertIsNone(self.activationkey.search(name))

    @tier1
    def test_positive_delete(self):
        """Create Activation key and delete it for all variations of
        Activation key name

        :id: 113e4c1e-cf4d-4c6a-88c9-766db8271933

        :expectedresults: Activation key is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_activationkey(
                        session,
                        org=self.organization.name,
                        name=name,
                        env=ENVIRONMENT,
                        description=gen_string('utf8'),
                    )
                    self.assertIsNotNone(self.activationkey.search(name))
                    self.activationkey.delete(name)

    @tier1
    def test_negative_delete(self):
        """[UI ONLY] Attempt to delete an Activation Key and cancel it

        :id: 07a17b98-b756-405c-b0c2-516f2a16aff1

        :Steps:
            1. Create an Activation key
            2. Attempt to remove an Activation Key
            3. Click Cancel in the confirmation dialog box

        :expectedresults: Activation key is not deleted

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.delete(name, really=False)

    @tier1
    def test_positive_update_name(self):
        """Update Activation Key Name in an Activation key

        :id: 81d74424-893d-46c4-a20c-c20c85d4e898

        :expectedresults: Activation key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 10)
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.activationkey.update(name, new_name)
                    self.assertIsNotNone(
                        self.activationkey.search(new_name))
                    name = new_name

    @tier1
    def test_positive_update_description(self):
        """Update Description in an Activation key

        :id: 24988466-af1d-4dcd-80b7-9c7d317fb805

        :expectedresults: Activation key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        description = gen_string('alpha')
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                description=description,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    self.activationkey.update(name, description=new_desc)
                    selected_desc = self.activationkey.get_attribute(
                        name, locators['ak.fetch_description'])
                    self.assertEqual(selected_desc, new_desc)

    @tier1
    def test_positive_update_limit(self):
        """Update Usage limit from Unlimited to a finite number

        :id: e6ef8dbe-dfb6-4226-8253-ff2e24cabe12

        :expectedresults: Activation key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        limit = '8'
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.update(name, limit=limit)
            selected_limit = self.activationkey.get_attribute(
                name, locators['ak.fetch_limit'])
            self.assertEqual(selected_limit, limit)

    @tier1
    def test_positive_update_limit_to_unlimited(self):
        """Update Usage limit from definite number to Unlimited

        :id: 2585ac91-baf0-43de-ba6e-862415402e62

        :expectedresults: Activation key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
                limit='6',
            )
            self.assertIsNotNone(self.activationkey.search(name))
            self.activationkey.update(name, limit='Unlimited')
            selected_limit = self.activationkey.get_attribute(
                name, locators['ak.fetch_limit'])
            self.assertEqual(selected_limit, 'Unlimited')

    @tier1
    def test_negative_update_name(self):
        """Update invalid name in an activation key

        :id: 6eb0f747-cd4d-421d-b11e-b8917bb0cec6

        :expectedresults: Activation key is not updated.  Appropriate error
            shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 10)
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.activationkey.update(name, new_name)
                    self.assertIsNotNone(self.activationkey.wait_until_element(
                        common_locators['alert.error_sub_form']))
                    self.assertIsNone(self.activationkey.search(new_name))

    @tier1
    def test_negative_update_limit(self):
        """Update invalid Usage Limit in an activation key

        :id: d42d8b6a-d3f4-4baa-be20-127f52f2313e

        :expectedresults: Activation key is not updated.  Appropriate error
            shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=name,
                env=ENVIRONMENT,
            )
            self.assertIsNotNone(self.activationkey.search(name))
            for limit in ' ', -1, 'text', '0':
                with self.subTest(limit):
                    with self.assertRaises(ValueError) as context:
                        self.activationkey.update(name, limit=limit)
                    self.assertEqual(
                        str(context.exception),
                        'Please update content host limit with valid ' +
                        'integer value'
                    )

    @skip_if_not_set('clients')
    @tier3
    @upgrade
    def test_positive_open_associated_host(self):
        """Associate content host with activation key, open activation key's
        associated hosts, click on content host link

        :id: 3dbe8370-f85b-416f-847f-7b7d81585bfc

        :expectedresults: Redirected to specific content host page

        :BZ: 1405166

        :CaseLevel: System
        """
        ak = entities.ActivationKey(
            environment=entities.LifecycleEnvironment(
                name=ENVIRONMENT,
                organization=self.organization,
            ).search()[0],
            organization=self.organization,
        ).create()
        with VirtualMachine(distro=self.vm_distro) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(self.organization.label, ak.name)
            self.assertTrue(vm.subscribed)
            with Session(self) as session:
                session.nav.go_to_select_org(self.organization.name)
                host = self.activationkey.search_content_host(
                    ak.name, vm.hostname)
                self.activationkey.click(host)
                chost_name = self.activationkey.wait_until_element(
                    locators['contenthost.details_page.name'])
                self.assertIsNotNone(chost_name)
                self.assertEqual(chost_name.text, vm.hostname)
                # Ensure content host id is present in URL
                chost_id = entities.Host().search(query={
                    'search': 'name={}'.format(vm.hostname)})[0].id
                chost_url_id = re.search(
                    '(?<=content_hosts/)([0-9])+', self.browser.current_url)
                self.assertIsNotNone(chost_url_id)
                self.assertEqual(int(chost_url_id.group(0)), chost_id)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_end_to_end(self):
        """Create Activation key and provision content-host with it

        Associate activation-key with host-group to auto-register the
        content-host during provisioning itself.

        :id: 1dc0079d-f41f-454b-9554-1235cabd1a4c

        :Steps:
            1. Create Activation key
            2. Associate it to host-group
            3. Provision content-host with same Activation key

        :expectedresults: Content-host should be successfully provisioned and
            registered with Activation key

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_copy(self):
        """Create Activation key and copy it

        :id: f43d9ecf-f8ec-49cc-bd12-be7cdb3bf07c

        :expectedresults: Activation Key copy exists

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    set_context(session, org=self.organization.name)
                    self.assertIsNotNone(
                        self.activationkey.search(self.base_key_name))
                    self.activationkey.copy(self.base_key_name, new_name)
                    self.assertIsNotNone(
                        self.activationkey.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_negative_copy(self):
        """Create Activation key and fail copying it

        :id: 117af9a8-e669-46cb-8a54-071087d0d082

        :expectedresults: Activation Key copy does not exist

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    set_context(session, org=self.organization.name)
                    self.assertIsNotNone(
                        self.activationkey.search(self.base_key_name))
                    self.activationkey.copy(self.base_key_name, new_name)
                    self.assertIsNone(self.activationkey.search(new_name))
