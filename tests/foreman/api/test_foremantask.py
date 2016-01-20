"""Unit tests for the ``foreman_tasks/api/v2/tasks`` paths."""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1
from robottelo.test import APITestCase


class ForemanTaskTestCase(APITestCase):
    """Tests for the ``foreman_tasks/api/v2/tasks/:id`` path."""

    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1131702)
    def test_negative_fetch_non_existent_task(self):
        """Fetch a non-existent task.

        @Assert: An HTTP 4XX or 5XX message is returned.

        @Feature: ForemanTask

        @bz: 1131702
        """
        with self.assertRaises(HTTPError):
            entities.ForemanTask(id='abc123').read()

    @tier1
    @run_only_on('sat')
    def test_positive_get_summary(self):
        """Get a summary of foreman tasks.

        @Assert: A list of dicts is returned.

        @Feature: ForemanTask
        """
        summary = entities.ForemanTask().summary()
        self.assertIsInstance(summary, list)
        for item in summary:
            self.assertIsInstance(item, dict)
