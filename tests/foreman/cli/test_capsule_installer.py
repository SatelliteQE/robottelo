# -*- encoding: utf-8 -*-
"""Test for capsule installer CLI"""
from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class CapsuleInstallerTestCase(CLITestCase):
    """Test class for capsule installer CLI"""

    @stubbed()
    def test_positive_basic(self):
        """perform a basic install of capsule.

        @Feature: Capsule Installer

        @Steps:

        1. Assure your target capsule has ONLY the Capsule repo enabled. In
           other words, the Satellite repo itself is not enabled by default.
        2. attempt to perform a basic, functional install the capsule using
           `capsule-installer`.

        @Assert: product is installed

        @Status: Manual

        """

    @stubbed()
    def test_positive_option_qpid_router(self):
        """assure the --qpid-router flag can be used in
        capsule-installer to enable katello-agent functionality via
        remote clients

        @Feature: capsule Installer

        @Steps:

        1. Install capsule-installer with the '--qpid-router=true` flag

        @Assert: Capsule installs correctly and qpid functionality is
        enabled.

        @Status: Manual

        """

    @stubbed()
    def test_positive_option_reverse_proxy(self):
        """ assure the --reverse-proxy flag can be used in
        capsule-installer to enable katello-agent functionality via
        remote clients

        @Feature: capsule Installer

        @Steps:

        1. Install using the '--reverse-proxy=true' flag

        @Assert: Capsule installs correctly and functionality is
        enabled.

        @Status: Manual

        """

    @stubbed()
    def test_negative_invalid_parameters(self):
        """invalid (non-boolean) parameters cannot be passed to flag

        @Feature: Capsule Installer

        @Steps:

        1. attempt to provide a variety of invalid parameters
           to installer (strings, numerics, whitespace, etc.)

        @Assert: user is told that such parameters are invalid and install
        aborts.

        @Status: Manual

        """

    @stubbed()
    def test_negative_option_parent_reverse_proxy_port(self):
        """invalid (non-integer) parameters cannot be passed to flag

        @Feature: Capsule Installer

        @Setup: na

        @Steps:

        1. attempt to provide a variety of invalid parameters to
           --parent-reverse-proxy-port flag (strings, numerics, whitespace,
           etc.)

        @Assert: user told parameters are invalid; install aborts.

        @Status: Manual

        """

    @stubbed()
    def test_positive_option_parent_reverse_proxy(self):
        """ valid parameters can be passed to --parent-reverse-proxy
        (true)

        @Feature: Capsule Installer

        @Setup: note that this requires an accompanying, valid port value

        @Steps:

        1. Attempt to provide a value of "true" to --parent-reverse-proxy

        @Assert: Install commences/completes with proxy installed correctly.

        @Status: Manual

        """

    @stubbed()
    def test_positive_option_parent_reverse_proxy_port(self):
        """valid parameters can be passed to
        --parent-reverse-proxy-port (integer)

        @Feature: Capsule Installer

        @Setup: note that this requires an accompanying, valid host for
        proxy parameter

        @Steps:

        1. Attempt to provide a valid proxy port # to flag

        @Assert: Install commences and completes with proxy installed
        correctly.

        @Status: Manual

        """
