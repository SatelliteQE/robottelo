"""Unit tests for :mod:`robottelo.common.decorators`."""
from ddt import DATA_ATTR
from fauxfactory import FauxFactory
from mock import patch
from robottelo.common import conf, decorators
from unittest import SkipTest, TestCase
# (Too many public methods) pylint: disable=R0904


class DataTestCase(TestCase):
    """Tests for :func:`robottelo.common.decorators.data`."""
    def setUp(self):  # pylint:disable=C0103
        self.test_data = ('one', 'two', 'three')

        def function():
            """An empty function."""
        self.function = function

    def test_smoke(self):
        conf.properties['main.smoke'] = '1'
        decorated = decorators.data(*self.test_data)(self.function)
        data_attr = getattr(decorated, DATA_ATTR)

        self.assertEqual(len(data_attr), 1)
        self.assertIn(data_attr[0], self.test_data)

    def test_not_smoke(self):
        conf.properties['main.smoke'] = '0'
        decorated = decorators.data(*self.test_data)(self.function)
        data_attr = getattr(decorated, DATA_ATTR)

        self.assertEqual(len(data_attr), len(self.test_data))
        self.assertEqual(getattr(decorated, DATA_ATTR), self.test_data)


class BzBugIsOpenTestCase(TestCase):
    """Tests for :func:`robottelo.common.decorators.bz_bug_is_open`."""
    # (protected-access) pylint:disable=W0212
    def setUp(self):  # pylint:disable=C0103
        """Back up objects and generate common values."""
        self.backup = decorators._get_bugzilla_bug
        self.bug_id = FauxFactory.generate_integer()

    def tearDown(self):  # pylint:disable=C0103
        """Restore backed-up objects."""
        decorators._get_bugzilla_bug = self.backup

    def test_bug_is_open(self):
        """Assert ``True`` is returned if the bug is 'NEW' or 'ASSIGNED'."""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with an open status."""
            status = 'NEW'
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id))
        MockBug.status = 'ASSIGNED'
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id))

    def test_bug_is_closed(self):
        """Assert ``False`` is returned if the bug is not open."""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with a closed status."""
            status = 'CLOSED'
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id))
        MockBug.status = 'ON_QA'
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id))
        MockBug.status = 'SLOWLY DRIVING A DEV INSANE'
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id))

    def test_bug_lookup_fails(self):
        """Assert ``False`` is returned if the bug cannot be found."""
        def bomb(_):
            """A function that mocks a failure to fetch a bug."""
            raise decorators.BugFetchError
        decorators._get_bugzilla_bug = bomb
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id))


class RmBugIsOpenTestCase(TestCase):
    """Tests for :func:`robottelo.common.decorators.rm_bug_is_open`."""
    # (protected-access) pylint:disable=W0212
    def setUp(self):  # pylint:disable=C0103
        """Back up objects and generate common values."""
        self.rm_backup = decorators._get_redmine_bug_status_id
        self.stat_backup = decorators._redmine_closed_issue_statuses
        decorators._redmine_closed_issue_statuses = lambda: [1, 2]
        self.bug_id = FauxFactory.generate_integer()

    def tearDown(self):  # pylint:disable=C0103
        """Restore backed-up objects."""
        decorators._get_redmine_bug_status_id = self.rm_backup
        decorators._redmine_closed_issue_statuses = self.stat_backup

    def test_bug_is_open(self):
        """Assert ``True`` is returned if the bug is open."""
        decorators._get_redmine_bug_status_id = lambda bug_id: 0
        self.assertTrue(decorators.rm_bug_is_open(self.bug_id))
        decorators._get_redmine_bug_status_id = lambda bug_id: 3
        self.assertTrue(decorators.rm_bug_is_open(self.bug_id))

    def test_bug_is_closed(self):
        """Assert ``False`` is returned if the bug is closed."""
        decorators._get_redmine_bug_status_id = lambda bug_id: 1
        self.assertFalse(decorators.rm_bug_is_open(self.bug_id))
        decorators._get_redmine_bug_status_id = lambda bug_id: 2
        self.assertFalse(decorators.rm_bug_is_open(self.bug_id))

    def test_bug_lookup_fails(self):
        """Assert ``False`` is returned if the bug cannot be found."""
        def bomb(_):
            """A function that mocks a failure to fetch a bug."""
            raise decorators.BugFetchError
        decorators._get_redmine_bug_status_id = bomb
        self.assertFalse(decorators.rm_bug_is_open(self.bug_id))


class MaybeSkipTestTestCase(TestCase):
    """Tests for ``_maybe_skip_test``."""
    # (protected-access) pylint:disable=W0212
    def setUp(self):  # pylint:disable=C0103
        """Back up objects and generate common values."""
        self.bug_id = FauxFactory.generate_integer()

    @patch('robottelo.common.decorators.bz_bug_is_open', return_value=True)
    @patch('robottelo.common.decorators.rm_bug_is_open', return_value=True)
    def test_bug_is_open(self, dummy, dummy2):
        """Assert ``unittest.SkipTest`` is raised if a bug is open."""
        for bug_type in ('bugzilla', 'redmine'):
            with self.assertRaises(SkipTest):
                decorators._maybe_skip_test(bug_type, self.bug_id)

    @patch('robottelo.common.decorators.bz_bug_is_open', return_value=False)
    @patch('robottelo.common.decorators.rm_bug_is_open', return_value=False)
    def test_bug_is_closed(self, dummy, dummy2):
        """Assert ``None`` is returned if a bug is open."""
        for bug_type in ('bugzilla', 'redmine'):
            self.assertIsNone(
                decorators._maybe_skip_test(bug_type, self.bug_id)
            )

    def test_bad_bug_type(self):
        """Assert :class:`robottelo.common.decorators.BugTypeError` is raised
        if argument ``bug_type`` is invalid.

        """
        with self.assertRaises(decorators.BugTypeError):
            decorators._maybe_skip_test('not_bugzilla_or_redmine', self.bug_id)
