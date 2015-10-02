# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for the capsule CLI."""
from robottelo.test import CLITestCase


class CapsuleTestCase(CLITestCase):
    """Tests for capsule functionality."""

    def provision_through_capsule(self):
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

    def register_through_capsule(self):
        """@Test: User can register system through proxy-enabled capsule

        @Feature: Capsules

        @Steps:

        1. attempt to register a system trhough a proxy-enabled capsule

        @Assert: system is successfully registered

        @Status: Manual

        """

    def deregister_through_capsule(self):
        """@Test: User can unregister system through proxy-enabled capsule

        @Feature: Capsules

        @Steps:

        1. attempt to unregister a system through a proxy-enabled capsule

        @Assert: system is successfully unregistered

        @Status: Manual

        """

    def subscribe_content_through_capsule(self):
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

    def consume_content_through_capsule(self):
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

    def unsusbscribe_content_through_capsule(self):
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

    def reregister_with_capsule_cert(self):
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

    def test_ssl_capsule(self):
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

    def test_enable_bmc(self):
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
