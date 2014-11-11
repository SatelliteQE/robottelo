"""Unit tests for the ``hosts`` paths.

An API reference can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html

"""
from fauxfactory import gen_integer, gen_string
from robottelo.api import client
from robottelo.common.decorators import run_only_on
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
# (too-many-public-methods) pylint:disable=R0904


@run_only_on('sat')
class HostsTestCase(TestCase):
    """Tests for ``entities.Host().path()``."""
    _multiprocess_can_split_ = True

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
