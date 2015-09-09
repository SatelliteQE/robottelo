"""Unit tests for the ``foreman_tasks/api/v2/tasks`` paths."""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.common.decorators import run_only_on, skip_if_bug_open
from robottelo.test import APITestCase


@run_only_on('sat')
class ForemanTasksIdTestCase(APITestCase):
    """Tests for the ``foreman_tasks/api/v2/tasks/:id`` path."""

    @skip_if_bug_open('bugzilla', 1131702)
    def test_no_such_task(self):
        """@Test: Fetch a non-existent task.

        @Assert: An HTTP 4XX or 5XX message is returned.

        @Feature: ForemanTask

        @bz: 1131702

        """
        with self.assertRaises(HTTPError):
            entities.ForemanTask(id='abc123').read()

    def test_summary(self):
        """@Test: Get a summary of foreman tasks.

        @Assert: A list of dicts is returned.

        @Feature: ForemanTask

        """
        summary = entities.ForemanTask().summary()
        self.assertIsInstance(summary, list)
        for item in summary:
            self.assertIsInstance(item, dict)
