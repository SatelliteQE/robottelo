"""Unit tests for the ``content_view_filters`` paths.

A full API reference for content views can be found here:
http://theforeman.org/api/apidoc/v2/content_view_filters.html

"""
import httplib
from nailgun import client, entities
from robottelo.common.decorators import run_only_on
from robottelo.common.helpers import get_server_credentials
from robottelo.test import APITestCase


@run_only_on('sat')
class ContentViewFilterTestCase(APITestCase):
    """Tests for content view filters."""

    def test_get_with_no_args(self):
        """@Test: Issue an HTTP GET to the base content view filters path.

        @Feature: ContentViewFilter

        @Assert: An HTTP 400 or 422 response is received if a GET request is
        issued with no arguments specified.

        This test targets bugzilla bug #1102120.

        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertIn(
            response.status_code,
            (httplib.BAD_REQUEST, httplib.UNPROCESSABLE_ENTITY)
        )

    def test_get_with_bad_args(self):
        """@Test: Issue an HTTP GET to the base content view filters path.

        @Feature: ContentViewFilter

        @Assert: An HTTP 400 or 422 response is received if a GET request is
        issued with bad arguments specified.

        This test targets bugzilla bug #1102120.

        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=get_server_credentials(),
            verify=False,
            data={'foo': 'bar'},
        )
        self.assertIn(
            response.status_code,
            (httplib.BAD_REQUEST, httplib.UNPROCESSABLE_ENTITY)
        )
