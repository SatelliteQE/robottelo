"""Unit tests for the ``foreman_tasks/api/v2/tasks`` paths.

:Requirement: Foremantask

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: TasksPlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.test import APITestCase


class ForemanTaskTestCase(APITestCase):
    """Tests for the ``foreman_tasks/api/v2/tasks/:id`` path."""

    @pytest.mark.tier1
    def test_negative_fetch_non_existent_task(self):
        """Fetch a non-existent task.

        :id: a2a81ca2-63c4-47f5-9314-5852f5e2617f

        :expectedresults: An HTTP 4XX or 5XX message is returned.

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.ForemanTask(id='abc123').read()

    @pytest.mark.tier1
    @pytest.mark.upgrade
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
