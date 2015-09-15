"""CLI tests for ``hammer host``."""
from nailgun import entities
from robottelo.cli.host import Host
from robottelo.cli.proxy import Proxy
from robottelo.config import conf
from robottelo.test import CLITestCase


class HostTestCase(CLITestCase):
    """Host CLI tests."""

    def setUp(self):
        """Find an existing puppet proxy.

        Record information about this puppet proxy as ``self.puppet_proxy``.

        """
        # Use the default installation smart proxy
        result = Proxy.list()
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertGreater(len(result.stdout), 0)
        self.puppet_proxy = result.stdout[0]

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
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            '{0}.{1}'.format(host.name, host.domain.read().name).lower(),
            result.stdout['name'],
        )

    def test_create_libvirt_without_mac(self):
        """@Test: Create a libvirt host and not specify a MAC address.

        @Feature: Hosts

        @Assert: Host is created

        """
        compute_resource = entities.LibvirtComputeResource(
            url='qemu+tcp://{0}:16509/system'.format(
                conf.properties['main.server.hostname']
            ),
        ).create()
        host = entities.Host()
        host.create_missing()
        result = Host.create({
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
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
