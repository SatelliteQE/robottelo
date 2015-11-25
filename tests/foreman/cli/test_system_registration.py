"""Test module for System Registration CLI"""
from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class SystemRegistrationTestCase(CLITestCase):
    """Tests for System Registration CLI"""

    @stubbed()
    def test_rpm_install(self):
        """@test: rpm can be retrieved

        @feature: system registration

        @assert: rpm required for modifying rhsm.conf can be installed from sat
        host

        @assert: rhsm.conf has been updated appropriately.

        @status: Manual
        """

    @stubbed()
    def test_register_no_ak(self):
        """@test: register system to sat without activation key

        @feature: system registration

        @assert: system successfully registered to appropriate org

        @status: Manual
        """

    @stubbed()
    def test_register_with_ak(self):
        """@test: register system with activation key

        @feature: system registration

        @assert: system successfully registered to appropriate org and
        subscribed to content as listed in key

        @status: Manual
        """

    @stubbed()
    def test_cannot_register_twice_negative(self):
        """@test: Attempt to register a system twice to an instance

        @feature: system registration

        @assert: system cannot be registered twice via RHSM

        @status: Manual
        """

    @stubbed()
    def test_registered_systems_pull_content(self):
        # variations:  RH rpms/errata; custom content repos
        """@test: assure RH RPM content can be installed

        @feature: system registration

        @assert: RH RPM/errata content can be retrieved/installed via sat

        @status: Manual
        """

    @stubbed()
    def test_registered_system_can_be_listed_cli(self):
        """@test: perform a system list for a given org

        @feature: system registration

        @assert: newly registered system appears in system list

        @status: Manual
        """

    @stubbed()
    def test_system_deregister_cli(self):
        """@test: deregister/delete system via RHSM

        @feature: system registration

        @assert: after deregistering, performing a system list via CLI
        assures system no longer appears in CLI

        @status: Manual
        """

    @stubbed()
    def test_deregistered_system_cannot_pull_content(self):
        """@test: try and retrieve content (via yum, etc.) after system has
        been removed from sat

        @feature: system registration

        @assert: system can no longer retrieve content from satellite

        @status: Manual
        """
