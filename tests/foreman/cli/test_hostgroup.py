# -*- encoding: utf-8 -*-
"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI."""
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.proxy import Proxy
from robottelo.cli.factory import (
    make_domain,
    make_environment,
    make_hostgroup,
    make_location,
    make_org,
    make_os,
)
from robottelo.config import settings
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_hostgroups_list,
)
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


class HostGroupTestCase(CLITestCase):
    """Test class for Host Group CLI"""

    @tier1
    def test_positive_create_with_name(self):
        """Successfully creates an HostGroup.

        @Feature: HostGroup

        @Assert: HostGroup is created.
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                self.assertEqual(hostgroup['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an HostGroup with invalid data.

        @Feature: HostGroup

        @Assert: HostGroup is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.create({'name': name})

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_env(self):
        """Check if hostgroup with environment can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new environment assigned

        """
        environment = make_environment()
        hostgroup = make_hostgroup({'environment-id': environment['id']})
        self.assertEqual(environment['name'], hostgroup['environment'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_loc(self):
        """Check if hostgroup with location can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new location assigned

        """
        location = make_location()
        hostgroup = make_hostgroup({'location-ids': location['id']})
        self.assertIn(location['name'], hostgroup['locations'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_os(self):
        """Check if hostgroup with operating system can be created

        @Feature: Hostgroup - Create

        @Assert: Hostgroup is created and has operating system assigned

        """
        os = make_os()
        hostgroup = make_hostgroup({'operatingsystem-id': os['id']})
        self.assertEqual(hostgroup['operating-system'], os['title'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_org(self):
        """Check if hostgroup with organization can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new organization assigned

        """
        org = make_org()
        hostgroup = make_hostgroup({'organization-ids': org['id']})
        self.assertIn(org['name'], hostgroup['organizations'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_ca_proxy(self):
        """Check if hostgroup with puppet CA proxy server can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has puppet CA proxy server assigned

        """
        puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({'puppet-ca-proxy': puppet_proxy['name']})
        self.assertEqual(puppet_proxy['id'], hostgroup['puppet-ca-proxy-id'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_proxy(self):
        """Check if hostgroup with puppet proxy server can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has puppet proxy server assigned

        """
        puppet_proxy = Proxy.list({
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = make_hostgroup({'puppet-proxy': puppet_proxy['name']})
        self.assertEqual(
            puppet_proxy['id'],
            hostgroup['puppet-master-proxy-id'],
        )

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_architecture(self):
        """Check if hostgroup with architecture can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup should be created and has architecture assigned
        """
        arch = 'x86_64'
        hostgroup = make_hostgroup({'architecture': arch})
        self.assertEqual(arch, hostgroup['architecture'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_domain(self):
        """Check if hostgroup with domain can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup should be created and has domain assigned
        """
        domain = make_domain()
        hostgroup = make_hostgroup({'domain-id': domain['id']})
        self.assertEqual(domain['name'], hostgroup['domain'])

    @tier1
    def test_positive_update_name(self):
        """Successfully update an HostGroup.

        @Feature: HostGroup

        @Assert: HostGroup is updated.
        """
        hostgroup = make_hostgroup()
        for new_name in valid_hostgroups_list():
            with self.subTest(new_name):
                HostGroup.update({
                    'id': hostgroup['id'],
                    'new-name': new_name,
                })
                hostgroup = HostGroup.info({'id': hostgroup['id']})
                self.assertEqual(hostgroup['name'], new_name)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Create HostGroup then fail to update its name

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
    @tier1
    def test_positive_delete_by_id(self):
        """Create HostGroup with valid values then delete it
        by ID

        @feature: HostGroup

        @assert: HostGroup is deleted
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                HostGroup.delete({'id': hostgroup['id']})
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.info({'id': hostgroup['id']})

    @run_only_on('sat')
    @tier1
    def test_negative_delete_by_id(self):
        """Create HostGroup then delete it by wrong ID

        @feature: HostGroup

        @assert: HostGroup is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.delete({'id': entity_id})
