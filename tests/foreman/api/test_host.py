# -*- encoding: utf-8 -*-
"""Unit tests for the ``hosts`` paths.

An API reference can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html

"""
from fauxfactory import gen_integer, gen_string
from nailgun import client, entities
from robottelo.config import settings
from robottelo.decorators import bz_bug_is_open, run_only_on, tier1
from robottelo.test import APITestCase
from six.moves import http_client


class HostsTestCase(APITestCase):
    """Tests for ``entities.Host().path()``."""

    @tier1
    @run_only_on('sat')
    def test_get_search(self):
        """@Test: GET ``api/v2/hosts`` and specify the ``search`` parameter.

        @Feature: Host

        @Assert: HTTP 200 is returned, along with ``search`` term.

        """
        query = gen_string('utf8', gen_integer(1, 100))
        response = client.get(
            entities.Host().path(),
            auth=settings.server.get_credentials(),
            data={u'search': query},
            verify=False,
        )
        self.assertEqual(response.status_code, http_client.OK)
        self.assertEqual(response.json()['search'], query)

    @tier1
    @run_only_on('sat')
    def test_get_per_page(self):
        """@Test: GET ``api/v2/hosts`` and specify the ``per_page`` parameter.

        @Feature: Host

        @Assert: HTTP 200 is returned, along with per ``per_page`` value.

        """
        per_page = gen_integer(1, 1000)
        response = client.get(
            entities.Host().path(),
            auth=settings.server.get_credentials(),
            data={u'per_page': per_page},
            verify=False,
        )
        self.assertEqual(response.status_code, http_client.OK)
        self.assertEqual(response.json()['per_page'], per_page)

    @tier1
    @run_only_on('sat')
    def test_create_owner_type(self):
        """@Test: Create a host and specify an ``owner_type``.

        @Feature: Host

        @Assert: The host can be read back, and the ``owner_type`` attribute is
        correct.

        """
        for owner_type in ('User', 'Usergroup'):
            with self.subTest(owner_type):
                if owner_type == 'Usergroup' and bz_bug_is_open(1203865):
                    continue  # instead of skip for compatibility with nose
                host = entities.Host()
                host.create_missing()
                host.owner_type = owner_type
                host = host.create(create_missing=False)
                self.assertEqual(host.owner_type, owner_type)

    @tier1
    @run_only_on('sat')
    def test_update_owner_type(self):
        """@Test: Update a host's ``owner_type``.

        @Feature: Host

        @Assert: The host's ``owner_type`` attribute is updated as requested.

        """
        host = entities.Host().create()
        for owner_type in ('User', 'Usergroup'):
            with self.subTest(owner_type):
                if owner_type == 'Usergroup' and bz_bug_is_open(1210001):
                    continue  # instead of skip for compatibility with nose
                host.owner_type = owner_type
                host = host.update(['owner_type'])
                self.assertEqual(host.owner_type, owner_type)
