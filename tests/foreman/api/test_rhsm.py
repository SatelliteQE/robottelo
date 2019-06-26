"""Unit tests for the ``rhsm`` paths.

No API doc exists for the subscription manager path(s). However, bugzilla bug
1112802 provides some relevant information.


:Requirement: Rhsm

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Candlepin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import client
from robottelo.config import settings
from robottelo.decorators import tier1
from robottelo.test import APITestCase
from six.moves import http_client


class RedHatSubscriptionManagerTestCase(APITestCase):
    """Tests for the ``/rhsm`` path."""

    @tier1
    def test_positive_path(self):
        """Check whether the path exists.

        :id: a8706cb7-549b-4426-9bd9-4beecc33c797

        :expectedresults: Issuing an HTTP GET produces an HTTP 200 response
            with an ``application/json`` content-type, and the response is a
            list.

        :BZ: 1112802

        :CaseImportance: Critical
        """
        path = '{0}/rhsm'.format(settings.server.get_url())
        response = client.get(
            path,
            auth=settings.server.get_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, http_client.OK)
        self.assertIn('application/json', response.headers['content-type'])
        self.assertIsInstance(response.json(), list)
