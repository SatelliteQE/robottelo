# -*- encoding: utf-8 -*-
from nailgun import entities
from robottelo.constants import ENVIRONMENT
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
class Host(UITestCase):

    def test_create_host(self):
        """@Test: Create a new Host

        @Feature: Host - Positive create

        @Assert: Host is created

        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(host.organization.name)
            self.navigator.go_to_hosts()
            self.hosts.create(
                arch=host.architecture.name,
                domain=host.domain.name,
                env=host.environment.name,
                loc=host.location.name,
                lifecycle_env=ENVIRONMENT,
                mac=host.mac,
                media=host.medium.name,
                name=host.name,
                org=host.organization.name,
                os=os_name,
                ptable=host.ptable.name,
                root_pwd=host.root_pass,
            )
            self.navigator.go_to_dashboard()
            self.navigator.go_to_hosts()
            # confirm the Host appears in the UI
            search = self.hosts.search(
                u'{0}.{1}'.format(host.name, host.domain.name)
            )
            self.assertIsNotNone(search)

    def test_delete_host(self):
        """@Test: Delete a Host

        @Feature: Host - Positive Delete

        @Assert: Host is deleted

        """
        host = entities.Host()
        host.create_missing()
        os_name = u'{0} {1}'.format(
            host.operatingsystem.name, host.operatingsystem.major)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(host.organization.name)
            self.navigator.go_to_hosts()
            self.hosts.create(
                arch=host.architecture.name,
                domain=host.domain.name,
                env=host.environment.name,
                loc=host.location.name,
                lifecycle_env=ENVIRONMENT,
                mac=host.mac,
                media=host.medium.name,
                name=host.name,
                org=host.organization.name,
                os=os_name,
                ptable=host.ptable.name,
                root_pwd=host.root_pass,
            )
            self.navigator.go_to_dashboard()
            self.navigator.go_to_hosts()
            # Delete host
            self.hosts.delete(
                u'{0}.{1}'.format(host.name, host.domain.name))
            self.assertIsNotNone(
                self.user.wait_until_element(common_locators['notif.success']))
            # confirm the Host disappeared from the UI
            search = self.hosts.search(
                u'{0}.{1}'.format(host.name, host.domain.name)
            )
            self.assertIsNone(search)
