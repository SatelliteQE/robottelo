"""Unit tests for the ``content_view_versions`` paths."""
from requests.exceptions import HTTPError
from robottelo import entities
from unittest import TestCase
# (too-many-public-methods) pylint:disable=R0904


class CVVersionTestCase(TestCase):
    """Tests for content view versions."""

    def test_negative_promote_1(self):
        """@Test: Promote the default content view version.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        env_id = entities.Environment().create()['id']
        with self.assertRaises(HTTPError):
            entities.ContentViewVersion(id=1).promote(env_id)

    def test_negative_promote_2(self):
        """@Test: Promote a content view version using an invalid environment.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        with self.assertRaises(HTTPError):
            entities.ContentViewVersion(id=1).promote(-1)
