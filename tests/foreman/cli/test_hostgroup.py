# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI."""

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.proxy import Proxy
from robottelo.cli.factory import (
    make_environment,
    make_hostgroup,
    make_location,
    make_org,
    make_os,
)
from robottelo.decorators import run_only_on
from robottelo.helpers import (
    invalid_id_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.test import CLITestCase


class TestHostGroup(CLITestCase):
    """Test class for Host Group CLI"""
    def test_positive_create(self):
        """@Test: Successfully creates an HostGroup.

        @Feature: HostGroup

        @Assert: HostGroup is created.
        """
        for name in valid_data_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                self.assertEqual(hostgroup['name'], name)

    def test_negative_create(self):
        """@Test: Don't create an HostGroup with invalid data.

        @Feature: HostGroup

        @Assert: HostGroup is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.create({'name': name})

    @run_only_on('sat')
    def test_create_hostgroup_with_environment(self):
        """@Test: Check if hostgroup with environment can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new environment assigned

        """
        environment = make_environment()
        hostgroup = make_hostgroup({'environment-id': environment['id']})
        self.assertEqual(environment['name'], hostgroup['environment'])

    @run_only_on('sat')
    def test_create_hostgroup_with_location(self):
        """@Test: Check if hostgroup with location can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new location assigned

        """
        location = make_location()
        hostgroup = make_hostgroup({'location-ids': location['id']})
        self.assertIn(location['name'], hostgroup['locations'])

    @run_only_on('sat')
    def test_create_hostgroup_with_operating_system(self):
        """@Test: Check if hostgroup with operating system can be created

        @Feature: Hostgroup - Create

        @Assert: Hostgroup is created and has operating system assigned

        """
        os = make_os()
        hostgroup = make_hostgroup({'operatingsystem-id': os['id']})
        self.assertEqual(hostgroup['operating-system'], os['title'])

    @run_only_on('sat')
    def test_create_hostgroup_with_organization(self):
        """@Test: Check if hostgroup with organization can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new organization assigned

        """
        org = make_org()
        hostgroup = make_hostgroup({'organization-ids': org['id']})
        self.assertIn(org['name'], hostgroup['organizations'])

    @run_only_on('sat')
    def test_create_hostgroup_with_puppet_ca_proxy(self):
        """@Test: Check if hostgroup with puppet CA proxy server can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has puppet CA proxy server assigned

        """
        puppet_proxy = Proxy.list()[0]
        hostgroup = make_hostgroup({'puppet-ca-proxy': puppet_proxy['name']})
        self.assertEqual(puppet_proxy['id'], hostgroup['puppet-ca-proxy-id'])

    @run_only_on('sat')
    def test_create_hostgroup_with_puppet_proxy(self):
        """@Test: Check if hostgroup with puppet proxy server can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has puppet proxy server assigned

        """
        puppet_proxy = Proxy.list()[0]
        hostgroup = make_hostgroup({'puppet-proxy': puppet_proxy['name']})
        self.assertEqual(
            puppet_proxy['id'],
            hostgroup['puppet-master-proxy-id'],
        )

    def test_positive_update_name(self):
        """@Test: Successfully update an HostGroup.

        @Feature: HostGroup

        @Assert: HostGroup is updated.
        """
        hostgroup = make_hostgroup()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                HostGroup.update({
                    'id': hostgroup['id'],
                    'new-name': new_name,
                })
                hostgroup = HostGroup.info({'id': hostgroup['id']})
                self.assertEqual(hostgroup['name'], new_name)

    @run_only_on('sat')
    def test_negative_update(self):
        """@test: Create HostGroup then fail to update its name

        @feature: HostGroup

        @assert: HostGroup name is not updated
        """
        hostgroup = make_hostgroup()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.update({
                        'id': hostgroup['id'],
                        'new-name': new_name,
                    })
                result = HostGroup.info({'id': hostgroup['id']})
                self.assertEqual(hostgroup['name'], result['name'])

    @run_only_on('sat')
    def test_positive_delete(self):
        """@test: Create HostGroup with valid values then delete it
        by ID

        @feature: HostGroup

        @assert: HostGroup is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                HostGroup.delete({'id': hostgroup['id']})
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.info({'id': hostgroup['id']})

    @run_only_on('sat')
    def test_negative_delete(self):
        """@test: Create HostGroup then delete it by wrong ID

        @feature: HostGroup

        @assert: HostGroup is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.delete(entity_id)
