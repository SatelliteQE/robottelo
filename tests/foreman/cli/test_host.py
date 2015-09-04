"""CLI tests for ``hammer host``."""
from nailgun import entities
from robottelo.cli.host import Host
from robottelo.cli.proxy import Proxy
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common import conf
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

    def test_bz_1177570(self):
        """@Test: Create a libvirt host and specify just a MAC address.

        @Feature: Hosts

        @Assert: No host is created, and an appropriately descriptive error
        message is returned.

        """
        compute_resource_id = entities.LibvirtComputeResource(
            url='qemu+tcp://{0}:16509/system'.format(
                conf.properties['main.server.hostname']
            ),
        ).create_json()['id']
        host = entities.Host()
        host.create_missing()
        result = Host.create({
            u'architecture-id': host.architecture.id,
            u'compute-resource-id': compute_resource_id,
            u'domain-id': host.domain.id,
            u'environment-id': host.environment.id,
            u'location-id': host.location.id,  # pylint:disable=no-member
            u'medium-id': host.medium.id,
            u'name': host.name,
            u'operatingsystem-id': host.operatingsystem.id,
            u'organization-id': host.organization.id,  # pylint:disable=E1101
            u'partition-table-id': host.ptable.id,
            u'puppet-proxy-id': self.puppet_proxy['id'],
            u'root-pass': host.root_pass,
            u'interface': 'type=network',
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotIn(u'mac value is blank', result.stderr)
        self.assertEqual(len(result.stderr), 0)
