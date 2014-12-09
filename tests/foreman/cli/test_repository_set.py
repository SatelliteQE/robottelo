from robottelo.common.decorators import skip_if_bug_open
from robottelo.test import CLITestCase


class TestRepositorySet(CLITestCase):
    """Repository Set CLI tests."""

    @skip_if_bug_open('bugzilla', 1172171)
    def test_available_repository_1(self):
        """@Test: Check if repositories are available

        @Feature: Repository-set

        @Assert: List of available repositories is displayed

        @BZ: 1172171

        """
        self.fail('This stubbed test should be fleshed out')
