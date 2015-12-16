"""Test module for System Registration CLI"""
from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class SystemRegistrationTestCase(CLITestCase):
    """Tests for System Registration CLI"""

    @stubbed()
    def test_positive_register_with_no_ak(self):
        """@test: Register Content host to satellite without activation key

        @feature: Content host

        @assert: Content host successfully registered to appropriate org

        @status: Manual
        """

    @stubbed()
    def test_negative_register_twice(self):
        """@test: Attempt to register a Content host twice to Satellite

        @feature: Content host

        @assert: Content host cannot be registered twice

        @status: Manual
        """

    @stubbed()
    def test_positive_list(self):
        """@test: List Content hosts for a given org

        @feature: Content host

        @assert: Content hosts are listed for the given org

        @status: Manual
        """

    @stubbed()
    def test_positive_unregister(self):
        """@test: Unregister Content host

        @feature: Content host

        @assert: After unregistering, Content hosts list for the org does not
        show the Content host

        @status: Manual
        """

    @stubbed()
    def test_negative_unregistered_chost_pull_content(self):
        """@test: Attempt to retrieve content after Content host has been
        unregistered from Satellite

        @feature: Content host

        @assert: Content host can no longer retrieve content from satellite

        @status: Manual
        """
