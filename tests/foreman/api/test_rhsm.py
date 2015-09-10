"""Unit tests for the ``rhsm`` paths.

No API doc exists for the subscription manager path(s). However, bugzilla bug
1112802 provides some relevant information.

"""
import httplib

from nailgun import client
from robottelo.helpers import get_server_credentials, get_server_url
from robottelo.test import APITestCase


class RHSMTestCase(APITestCase):
    """Tests for the ``/rhsm`` path."""

    def test_path_exists(self):
        """@Test: Check whether the path exists.

        @Feature: Red Hat Subscription Manager

        @Assert: Issuing an HTTP GET produces an HTTP 200 response with an
        ``application/json`` content-type, and the response is a list.

        This test targets bugzilla bug 1112802.

        """
        path = '{0}/rhsm'.format(get_server_url())
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('application/json', response.headers['content-type'])
        self.assertIsInstance(response.json(), list)
