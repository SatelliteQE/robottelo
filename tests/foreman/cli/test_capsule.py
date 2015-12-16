# -*- encoding: utf-8 -*-
"""Test class for the capsule CLI."""
import random

from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError, make_proxy
from robottelo.cli.proxy import Proxy, default_url_on_new_port
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_only_on, stubbed, tier1, tier2
from robottelo.test import CLITestCase


class CapsuleTestCase(CLITestCase):
    """Proxy cli tests"""

    def setUp(self):
        """Skipping tests until we can create ssh tunnels"""
        self.skipTest('Skipping tests until we can create ssh tunnels')

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_url(self):
        """@Test: Proxy creation with random URL

        @Feature: Smart Proxy

        @Assert: Proxy is not created
        """
        # Create a random proxy
        with self.assertRaises(CLIFactoryError):
            make_proxy({
                u'url': u'http://{0}:{1}'.format(
                    gen_string('alpha', 6),
                    gen_string('numeric', 4)),
            })

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """@Test: Proxy creation with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is created
        """
        for name in valid_data_list():
            with self.subTest(name):
                proxy = make_proxy({u'name': name})
                self.assertEquals(proxy['name'], name)

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_id(self):
        """@Test: Proxy deletion with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                proxy = make_proxy({u'name': name})
                Proxy.delete({u'id': proxy['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Proxy.info({u'id': proxy['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """@Test: Proxy name update with the home proxy

        @Feature: Smart Proxy

        @Assert: Proxy has the name updated
        """
        proxy = make_proxy({u'name': gen_alphanumeric()})
        newport = random.randint(9091, 49090)
        for new_name in valid_data_list():
            with self.subTest(new_name):
                with default_url_on_new_port(9090, newport) as url:
                    Proxy.update({
                        u'id': proxy['id'],
                        u'name': new_name,
                        u'url': url,
                    })
                    proxy = Proxy.info({u'id': proxy['id']})
                    self.assertEqual(proxy['name'], new_name)

    @run_only_on('sat')
    @tier2
    def test_positive_refresh_features_by_id(self):
        """@Test: Refresh smart proxy features, search for proxy by id

        @Feature: Smart Proxy

        @Assert: Proxy features are refreshed
        """
        proxy = make_proxy()
        Proxy.refresh_features({u'id': proxy['id']})

    @run_only_on('sat')
    @tier2
    def test_positive_refresh_features_by_name(self):
        """@Test: Refresh smart proxy features, search for proxy by name

        @Feature: Smart Proxy

        @Assert: Proxy features are refreshed
        """
        proxy = make_proxy()
        Proxy.refresh_features({u'name': proxy['name']})


class CapsuleIntegrationTestCase(CLITestCase):
    """Tests for capsule functionality."""

    @stubbed()
    def test_positive_provision(self):
        """@Test: User can provision through a capsule

        @Feature: Capsules

        @Setup: Some valid, functional compute resource (perhaps one variation
        of this case for each supported compute resource type). Also,
        functioning capsule with proxy is required.

        @Steps:

        1. Attempt to route provisioning content through capsule that is using
           a proxy
        2. Attempt to provision instance

        @Assert: Instance can be provisioned, with content coming through
        proxy-enabled capsule.

        @Status: Manual
        """

    @stubbed()
    def test_positive_register(self):
        """@Test: User can register system through proxy-enabled capsule

        @Feature: Capsules

        @Steps:

        1. attempt to register a system trhough a proxy-enabled capsule

        @Assert: system is successfully registered

        @Status: Manual
        """

    @stubbed()
    def test_positive_unregister(self):
        """@Test: User can unregister system through proxy-enabled capsule

        @Feature: Capsules

        @Steps:

        1. attempt to unregister a system through a proxy-enabled capsule

        @Assert: system is successfully unregistered

        @Status: Manual
        """

    @stubbed()
    def test_positive_subscribe(self):
        """@Test: User can subscribe system to content through proxy-enabled
        capsule

        @Feature: Capsules

        @Setup: Content source types configured/synced for [RH, Custom, Puppet,
        Docker] etc.

        @Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule

        @Assert: system is successfully subscribed to each content type

        @Status: Manual
        """

    @stubbed()
    def test_positive_consume_content(self):
        """@Test: User can consume content on system, from a content source,
        through proxy-enabled capsule

        @Feature: Capsules

        @Setup: Content source types configured/synced for [RH, Custom, Puppet,
        Docker] etc.

        @Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule
        2. Attempt to install content (RPMs, puppet modules) via proxy-enabled
           capsule

        @Assert: system successfully consume content

        @Status: Manual
        """

    @stubbed()
    def test_positive_unsubscribe(self):
        """@Test: User can unsubscribe system from content through
        proxy-enabled capsule

        @Feature: Capsules

        @Setup: Content source types configured/synced for [RH, Custom, Puppet]
        etc.

        @Steps:

        1. attempt to subscribe a system to a content type variation, via a
           proxy-enabled capsule
        2. attempt to unsubscribe a system from said content type(s) via a
           proxy-enabled capsule

        @Assert: system is successfully unsubscribed from each content type

        @Status: Manual
        """

    @stubbed()
    def test_positive_reregister_with_capsule_cert(self):
        """@Test: system can register via capsule using cert provided by
        the capsule itself.

        @Feature: Capsules

        @Setup: functional capsule and certs rpm installed on target client.

        @Steps:

        1. Attempt to register from parent satellite; unregister and remove
           cert rpm
        2. Attempt to reregister using same credentials and certs from a
           functional capsule.

        @Assert: Registration works , and certs RPM installed
        from capsule.

        @Status: Manual
        """

    @stubbed()
    def test_positive_ssl_capsule(self):
        """@Test: Assure SSL functionality for capsules

        @Feature: Capsules

        @Setup: A capsule installed with SSL enabled.

        @Steps:

        1. Execute basic steps from above (register, subscribe, consume,
           unsubscribe, unregister) while connected to a capsule that is
           SSL-enabled

        @Assert: No failures executing said test scenarios against SSL,
        baseline functionality identical to non-SSL

        @Status: Manual
        """

    @stubbed()
    def test_positive_enable_bmc(self):
        """@Test: Enable BMC feature on smart-proxy

        @Feature: Capsules

        @Setup: A capsule installed with SSL enabled.

        @Steps:

        1. Enable BMC feature on proxy by running installer with:
           ``katello-installer --foreman-proxy-bmc 'true'``
        2. Please make sure to check default values to other BMC options.
           Should be like below:
           ``--foreman-proxy-bmc-default-provider  BMC default provider.
           (default: "ipmitool")``
           ``--foreman-proxy-bmc-listen-on  BMC proxy to listen on https, http,
           or both (default: "https")``
        3. Check if BMC plugin is enabled with:
           ``#cat /etc/foreman-proxy/settings.d/bmc.yml | grep enabled``
        4. Restart foreman-proxy service

        @Assert: Katello installer should show the options to enable BMC

        @Status: Manual
        """
