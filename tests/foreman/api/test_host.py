# -*- encoding: utf-8 -*-
"""Unit tests for the ``hosts`` paths.

An API reference can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html

"""
import httplib
from ddt import ddt
from fauxfactory import gen_integer, gen_string
from nailgun import client
from robottelo import entities
from robottelo.common.decorators import (
    bz_bug_is_open,
    data,
    run_only_on,
    skip_if_bug_open,
)
from robottelo.common.helpers import get_server_credentials
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


@run_only_on('sat')
@ddt
class HostsTestCase(APITestCase):
    """Tests for ``entities.Host().path()``."""

    def test_get_search(self):
        """@Test: GET ``api/v2/hosts`` and specify the ``search`` parameter.

        @Feature: Host

        @Assert: HTTP 200 is returned, along with ``search`` term.

        """
        query = gen_string('utf8', gen_integer(1, 100))
        response = client.get(
            entities.Host().path(),
            auth=get_server_credentials(),
            data={u'search': query},
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['search'], query)

    def test_get_per_page(self):
        """@Test: GET ``api/v2/hosts`` and specify the ``per_page`` parameter.

        @Feature: Host

        @Assert: HTTP 200 is returned, along with per ``per_page`` value.

        """
        per_page = gen_integer(1, 1000)
        response = client.get(
            entities.Host().path(),
            auth=get_server_credentials(),
            data={u'per_page': per_page},
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(response.json()['per_page'], per_page)

    @skip_if_bug_open('bugzilla', 1120800)
    def test_bz_1120800(self):
        """@Test: Create a host with the ``name`` parameter in the outer hash.

        @Feature: Host

        @Assert: A host is created.

        """
        host = entities.Host()
        host.create_missing()
        payload = host.create_payload()
        payload['name'] = payload['host'].pop('name')
        response = client.post(
            host.path(),
            payload,
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        self.assertTrue('id' in response.json())

    @data('User', 'Usergroup')
    def test_create_owner_type(self, owner_type):
        """@Test: Create a host and specify an ``owner_type``.

        @Feature: Host

        @Assert: The host can be read back, and the ``owner_type`` attribute is
        correct.

        """
        if owner_type == 'Usergroup' and bz_bug_is_open(1203865):
            self.skipTest('BZ 1203865: owner_type ignored when creating host')
        host = entities.Host()
        host.create_missing()
        host.owner_type = owner_type
        host_id = host.create_json(create_missing=False)['id']
        self.assertEqual(
            entities.Host(id=host_id).read_json()['owner_type'],
            owner_type,
        )

    @data('User', 'Usergroup')
    def test_update_owner_type(self, owner_type):
        """@Test: Update a host and specify an ``owner_type``.

        @Feature: Host

        @Assert: The host can be read back, and the ``owner_type`` attribute is
        correct.

        """
        if owner_type == 'Usergroup' and bz_bug_is_open(1210001):
            self.skipTest('BZ 1210001: host update should block or yield task')
        host_id = entities.Host().create_json()['id']
        response = client.put(
            entities.Host(id=host_id).path(),
            {'host': {'owner_type': owner_type}},
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        self.assertEqual(
            entities.Host(id=host_id).read_json()['owner_type'],
            owner_type,
        )
