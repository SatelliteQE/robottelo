"""Unit tests for the ``foreman_tasks/api/v2/tasks`` paths."""
from requests.exceptions import HTTPError
from robottelo.common.decorators import run_only_on, skip_if_bug_open
from robottelo import entities
from unittest import TestCase
# (too-many-public-methods) pylint:disable=R0904


@run_only_on('sat')
class ForemanTasksIdTestCase(TestCase):
    """Tests for the ``foreman_tasks/api/v2/tasks/:id`` path."""
    _multiprocess_can_split_ = True

    @skip_if_bug_open('bugzilla', 1131702)
    def test_no_such_task(self):
        """@Test: Fetch a non-existent task.

        @Assert: An HTTP 4XX or 5XX message is returned.

        @Feature: ForemanTask

        @bz: 1131702

        """
        with self.assertRaises(HTTPError):
            entities.ForemanTask(id='abc123').read_json()
