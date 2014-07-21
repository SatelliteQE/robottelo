"""Unit tests for the ``organizations`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/organizations

"""
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.decorators import skip_if_bz_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


class OrganizationsTestCase(TestCase):
    """Tests for the ``organizations`` path."""
    @skip_if_bz_bug_open(1116043)
    def test_create(self):
        """@Test Create an organization.

        @Assert: HTTP 201 is returned.
        @Feature: Organization

        """
        path = entities.Organization().path()
        attrs = entities.Organization().build()
        response = client.post(
            path,
            attrs,
            auth=get_server_credentials(),
            headers={'content-type': 'text/plain'},
            verify=False,
        )
        status_code = httplib.CREATED
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
