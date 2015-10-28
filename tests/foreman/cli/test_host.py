# pylint: disable=invalid-name
"""CLI tests for ``hammer host``."""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.host import Host
from robottelo.cli.proxy import Proxy
from robottelo.config import settings
from robottelo.helpers import invalid_values_list, valid_data_list
from robottelo.test import CLITestCase


class HostTestCase(CLITestCase):
    """Host CLI tests."""

    def setUp(self):
        """Find an existing puppet proxy.

        Record information about this puppet proxy as ``self.puppet_proxy``.

        """
        # Use the default installation smart proxy
        result = Proxy.list()
        self.assertGreater(len(result), 0)
        self.puppet_proxy = result[0]

    def test_positive_create_1(self):
        """@test: A host can be created with a random name

        @feature: Hosts

        @assert: A host is created and the name matches

        """
        host = entities.Host()
        host.create_missing()
        result = Host.create({
            u'architecture-id': host.architecture.id,
            u'domain-id': host.domain.id,
            u'environment-id': host.environment.id,
            u'location-id': host.location.id,  # pylint:disable=no-member
            u'mac': host.mac,
            u'medium-id': host.medium.id,
            u'name': host.name,
            u'operatingsystem-id': host.operatingsystem.id,
            u'organization-id': host.organization.id,  # pylint:disable=E1101
            u'partition-table-id': host.ptable.id,
            u'puppet-proxy-id': self.puppet_proxy['id'],
            u'root-pass': host.root_pass,
        })
        self.assertEqual(
            '{0}.{1}'.format(host.name, host.domain.read().name).lower(),
            result['name'],
        )

    def test_create_libvirt_without_mac(self):
        """@Test: Create a libvirt host and not specify a MAC address.

        @Feature: Hosts

        @Assert: Host is created

        """
        compute_resource = entities.LibvirtComputeResource(
            url='qemu+tcp://{0}:16509/system'.format(
                settings.server.hostname
            ),
        ).create()
        host = entities.Host()
        host.create_missing()
        Host.create({
            u'architecture-id': host.architecture.id,
            u'compute-resource-id': compute_resource.id,
            u'domain-id': host.domain.id,
            u'environment-id': host.environment.id,
            u'interface': 'type=network',
            u'location-id': host.location.id,  # pylint:disable=no-member
            u'medium-id': host.medium.id,
            u'name': host.name,
            u'operatingsystem-id': host.operatingsystem.id,
            u'organization-id': host.organization.id,  # pylint:disable=E1101
            u'partition-table-id': host.ptable.id,
            u'puppet-proxy-id': self.puppet_proxy['id'],
            u'root-pass': host.root_pass,
        })


class HostParameterTests(CLITestCase):
    """Tests targeting host parameters"""

    @classmethod
    def setUpClass(cls):
        """Create host to tests parameters for"""
        super(HostParameterTests, cls).setUpClass()
        cls.proxies = Proxy.list()
        assert len(cls.proxies) > 0
        cls.puppet_proxy = cls.proxies[0]
        # using nailgun to create dependencies
        cls.host = entities.Host()
        cls.host.create_missing()
        # using CLI to create host
        cls.host = Host.create({
            u'architecture-id': cls.host.architecture.id,
            u'domain-id': cls.host.domain.id,
            u'environment-id': cls.host.environment.id,
            u'location-id': cls.host.location.id,  # pylint:disable=no-member
            u'mac': cls.host.mac,
            u'medium-id': cls.host.medium.id,
            u'name': cls.host.name,
            u'operatingsystem-id': cls.host.operatingsystem.id,
            # pylint:disable=no-member
            u'organization-id': cls.host.organization.id,
            u'partition-table-id': cls.host.ptable.id,
            u'puppet-proxy-id': cls.puppet_proxy['id'],
            u'root-pass': cls.host.root_pass,
        })

    def test_add_parameter_diff_names(self):
        """@Test: Add host parameter with different valid names.

        @Feature: Hosts

        @Assert: Host parameter was successfully added with correct name.

        """
        for name in valid_data_list():
            with self.subTest(name):
                name = name.lower()
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': gen_string('alphanumeric'),
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())

    def test_add_parameter_diff_values(self):
        """@Test: Add host parameter with different valid values.

        @Feature: Hosts

        @Assert: Host parameter was successfully added with value.

        """
        for value in valid_data_list():
            with self.subTest(value):
                name = gen_string('alphanumeric').lower()
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': value,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())
                self.assertEqual(value, self.host['parameters'][name])

    def test_add_parameter_by_host_name(self):
        """@Test: Add host parameter by specifying host name.

        @Feature: Hosts

        @Assert: Host parameter was successfully added with correct name and
        value.

        """
        name = gen_string('alphanumeric').lower()
        value = gen_string('alphanumeric')
        Host.set_parameter({
            'host': self.host['name'],
            'name': name,
            'value': value,
        })
        self.host = Host.info({'id': self.host['id']})
        self.assertIn(name, self.host['parameters'].keys())
        self.assertEqual(value, self.host['parameters'][name])

    def test_update_parameter_by_host_id(self):
        """@Test: Update existing host parameter by specifying host ID.

        @Feature: Hosts

        @Assert: Host parameter was successfully updated with new value.

        """
        name = gen_string('alphanumeric').lower()
        old_value = gen_string('alphanumeric')
        Host.set_parameter({
            'host-id': self.host['id'],
            'name': name,
            'value': old_value,
        })
        for new_value in valid_data_list():
            with self.subTest(new_value):
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': new_value,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())
                self.assertEqual(new_value, self.host['parameters'][name])

    def test_update_parameter_by_host_name(self):
        """@Test: Update existing host parameter by specifying host name.

        @Feature: Hosts

        @Assert: Host parameter was successfully updated with new value.

        """
        name = gen_string('alphanumeric').lower()
        old_value = gen_string('alphanumeric')
        Host.set_parameter({
            'host': self.host['name'],
            'name': name,
            'value': old_value,
        })
        for new_value in valid_data_list():
            with self.subTest(new_value):
                Host.set_parameter({
                    'host': self.host['name'],
                    'name': name,
                    'value': new_value,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertIn(name, self.host['parameters'].keys())
                self.assertEqual(new_value, self.host['parameters'][name])

    def test_delete_parameter_by_host_id(self):
        """@Test: Delete existing host parameter by specifying host ID.

        @Feature: Hosts

        @Assert: Host parameter was successfully deleted.

        """
        for name in valid_data_list():
            with self.subTest(name):
                name = name.lower()
                Host.set_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                    'value': gen_string('alphanumeric'),
                })
                Host.delete_parameter({
                    'host-id': self.host['id'],
                    'name': name,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertNotIn(name, self.host['parameters'].keys())

    def test_delete_parameter_by_host_name(self):
        """@Test: Delete existing host parameter by specifying host name.

        @Feature: Hosts

        @Assert: Host parameter was successfully deleted.

        """
        for name in valid_data_list():
            with self.subTest(name):
                name = name.lower()
                Host.set_parameter({
                    'host': self.host['name'],
                    'name': name,
                    'value': gen_string('alphanumeric'),
                })
                Host.delete_parameter({
                    'host': self.host['name'],
                    'name': name,
                })
                self.host = Host.info({'id': self.host['id']})
                self.assertNotIn(name, self.host['parameters'].keys())

    def test_add_parameter_negative(self):
        """@Test: Try to add host parameter with different invalid names.

        @Feature: Hosts

        @Assert: Host parameter was not added.

        """
        for name in invalid_values_list():
            with self.subTest(name):
                name = name.lower()
                with self.assertRaises(CLIReturnCodeError):
                    Host.set_parameter({
                        'host-id': self.host['id'],
                        'name': name,
                        'value': gen_string('alphanumeric'),
                    })
                self.host = Host.info({'id': self.host['id']})
                self.assertNotIn(name, self.host['parameters'].keys())
