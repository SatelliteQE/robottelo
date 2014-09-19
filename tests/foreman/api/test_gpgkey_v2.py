"""Unit tests for the ``gpgkeys`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/gpgkeys.html

"""
from robottelo.api import client
from robottelo.common.decorators import run_only_on
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


@run_only_on('sat')
class GPGKeyTestCase(TestCase):
    """Tests for ``katello/api/v2/gpg_keys``."""
    def test_get_all(self):
        """@Test: Get ``katello/api/v2/gpg_keys`` and specify just an
        organization ID.

        @Feature: GPGKey

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        org_attrs = entities.Organization().create()
        response = client.get(
            entities.GPGKey().path(),
            auth=get_server_credentials(),
            data={u'organization_id': org_attrs['id']},
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('application/json', response.headers['content-type'])
