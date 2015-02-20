# -*- encoding: utf-8 -*-
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

    def register_via_capsule_with_parent_cert(self):
        """@Test: system can register via capsule using same cert as parent
        sat. Note: it is possible that some changes may have to be made to
        rhsm.conf to point to satellite. How this will be impl. has not yet
        been determined. It will need its own case eventually.

        @Feature: Capsules

        @Setup: functional capsule and certs rpm installed on target client.

        @Steps:

        1. Attempt to register system to parent satellite; unregister
        2. Attempt to reregister using same credentials and certs against a
           functional capsule.

        @Assert: Registration works with no changes, and certs RPM installed
        from parent satellite.

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
