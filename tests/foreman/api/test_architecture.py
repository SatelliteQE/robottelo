"""Unit tests for the ``architectures`` paths."""
from fauxfactory import gen_utf8
from robottelo.api import client
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
# (too-many-public-methods) pylint:disable=R0904


class ArchitectureTestCase(TestCase):
    """Tests for architectures."""

    @skip_if_bug_open('bugzilla', 1151220)
    def test_post_hash(self):
        """@Test: Do not wrap API calls in an extra hash.

        @Assert: It is possible to associate an activation key with an
        organization.

        @Feature: Architecture

        """
        name = gen_utf8()
        os_id = entities.OperatingSystem().create()['id']
        response = client.post(
            entities.Architecture().path(),
            {u'name': name, u'operatingsystem_ids': [os_id]},
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        attrs = response.json()

        # The server will accept some POSTed attributes (name) and silently
        # ignore others (operatingsystem_ids).
        self.assertIn('name', attrs)
        self.assertEqual(name, attrs['name'])
        self.assertIn('operatingsystems', attrs)
        self.assertEqual([os_id], attrs['operatingsystems'])

    @skip_if_bug_open('bugzilla', 1151240)
    def test_get_hash(self):
        """@Test: Read the API and look for a list of IDs.

        @Assert: The architecture-OS foreign key relationship is described with
        a list of IDs.

        @Feature: Architecture

        """
        os_id = entities.OperatingSystem().create()['id']
        attrs = entities.Architecture(operatingsystem=[os_id]).create()
        self.assertIn('operatingsystem_ids', attrs)
        self.assertEqual(attrs['operatingsystem_ids'], [os_id])
