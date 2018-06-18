"""Unit tests for the ``foreman_tasks/api/v2/tasks`` paths.

:Requirement: Foremantask

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.decorators import run_only_on, tier1, upgrade
from robottelo.test import APITestCase


class ForemanTaskTestCase(APITestCase):
    """Tests for the ``foreman_tasks/api/v2/tasks/:id`` path."""

    @tier1
    @run_only_on('sat')
    def test_negative_fetch_non_existent_task(self):
        """Fetch a non-existent task.

        :id: a2a81ca2-63c4-47f5-9314-5852f5e2617f

        :expectedresults: An HTTP 4XX or 5XX message is returned.

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.ForemanTask(id='abc123').read()

    @tier1
    @upgrade
    @run_only_on('sat')
    def test_positive_get_summary(self):
        """Get a summary of foreman tasks.

        :id: bdcab413-a25d-4fe1-9db4-b50b5c31ebce

        :expectedresults: A list of dicts is returned.

        :CaseImportance: Critical
        """
        summary = entities.ForemanTask().summary()
        self.assertIsInstance(summary, list)
        for item in summary:
            self.assertIsInstance(item, dict)
