# -*- encoding: utf-8 -*-
"""Test for capsule installer CLI

@Requirement: Capsule installer

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from robottelo.decorators import stubbed, upgrade
from robottelo.test import CLITestCase


class CapsuleInstallerTestCase(CLITestCase):
    """Test class for capsule installer CLI"""

    @stubbed()
    @upgrade
    def test_positive_basic(self):
        """perform a basic install of capsule.

        @id: 47445685-5924-4980-89d0-bbb2fb608f4d

        @Steps:

        1. Assure your target capsule has ONLY the Capsule repo enabled. In
           other words, the Satellite repo itself is not enabled by default.
        2. attempt to perform a basic, functional install the capsule using
           `capsule-installer`.

        @expectedresults: product is installed

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_qpid_router(self):
        """assure the --qpid-router flag can be used in
        capsule-installer to enable katello-agent functionality via
        remote clients

        @id: d040a72d-72b2-41cf-b14e-a8e37e80200d

        @Steps:

        1. Install capsule-installer with the '--qpid-router=true` flag

        @expectedresults: Capsule installs correctly and qpid functionality is
        enabled.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_reverse_proxy(self):
        """ assure the --reverse-proxy flag can be used in
        capsule-installer to enable katello-agent functionality via
        remote clients

        @id: 756fd76a-0183-4637-93c8-fe7c375be751

        @Steps:

        1. Install using the '--reverse-proxy=true' flag

        @expectedresults: Capsule installs correctly and functionality is
        enabled.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_negative_invalid_parameters(self):
        """invalid (non-boolean) parameters cannot be passed to flag

        @id: f4366c87-e436-42b4-ada4-55f0e66a481e

        @Steps:

        1. attempt to provide a variety of invalid parameters
           to installer (strings, numerics, whitespace, etc.)

        @expectedresults: user is told that such parameters are invalid and
        install aborts.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_negative_option_parent_reverse_proxy_port(self):
        """invalid (non-integer) parameters cannot be passed to flag

        @id: a1af16d3-84da-4e94-818e-90bc82cc5698

        @Setup: na

        @Steps:

        1. attempt to provide a variety of invalid parameters to
           --parent-reverse-proxy-port flag (strings, numerics, whitespace,
           etc.)

        @expectedresults: user told parameters are invalid; install aborts.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_parent_reverse_proxy(self):
        """ valid parameters can be passed to --parent-reverse-proxy
        (true)

        @id: a905f4ca-a729-4efb-84fc-43923737f75b

        @Setup: note that this requires an accompanying, valid port value

        @Steps:

        1. Attempt to provide a value of "true" to --parent-reverse-proxy

        @expectedresults: Install commences/completes with proxy installed
        correctly.

        @caseautomation: notautomated

        """

    @stubbed()
    def test_positive_option_parent_reverse_proxy_port(self):
        """valid parameters can be passed to
        --parent-reverse-proxy-port (integer)

        @id: 32238045-53e2-4ed4-ac86-57917e7aedcd

        @Setup: note that this requires an accompanying, valid host for
        proxy parameter

        @Steps:

        1. Attempt to provide a valid proxy port # to flag

        @expectedresults: Install commences and completes with proxy installed
        correctly.

        @caseautomation: notautomated

        """
