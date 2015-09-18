"""Unit tests for the ``architectures`` paths."""
from fauxfactory import gen_utf8
from nailgun import client, entities
from robottelo.decorators import skip_if_bug_open
from robottelo.helpers import get_server_credentials
from robottelo.test import APITestCase


class ArchitectureTestCase(APITestCase):
    """Tests for architectures."""

    @skip_if_bug_open('bugzilla', 1151220)
    def test_post_hash(self):
        """@Test: Do not wrap API calls in an extra hash.

        @Assert: It is possible to associate an activation key with an
        organization.

        @Feature: Architecture

        """
        name = gen_utf8()
        os_id = entities.OperatingSystem().create_json()['id']
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

    def test_associate_with_os(self):
        """@Test: Create an architecture and associate it with an OS.

        @Assert: The architecture can be created, and the association can be
        read back from the server.

        @Feature: Architecture

        """
        operating_sys = entities.OperatingSystem().create()
        arch = entities.Architecture(operatingsystem=[operating_sys]).create()
        self.assertEqual(
            {operating_sys.id},
            {os.id for os in arch.operatingsystem},
        )
