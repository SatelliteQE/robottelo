"""Unit tests for :mod:`robottelo.decorators`."""
from ddt import DATA_ATTR
from fauxfactory import gen_integer
from robottelo import decorators
from robottelo.config import conf
from robottelo.constants import BZ_CLOSED_STATUSES, BZ_OPEN_STATUSES
from unittest import TestCase
# (Too many public methods) pylint: disable=R0904


class DataTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.data`."""
    def setUp(self):  # noqa pylint:disable=C0103
        self.test_data = ('one', 'two', 'three')

        def function():
            """An empty function."""
        self.function = function

    def test_smoke(self):
        """Test for smoke attribute on"""
        conf.properties['main.smoke'] = '1'
        decorated = decorators.data(*self.test_data)(self.function)
        data_attr = getattr(decorated, DATA_ATTR)

        self.assertEqual(len(data_attr), 1)
        self.assertIn(data_attr[0], self.test_data)

    def test_not_smoke(self):
        """Test for smoke attribute off"""
        conf.properties['main.smoke'] = '0'
        decorated = decorators.data(*self.test_data)(self.function)
        data_attr = getattr(decorated, DATA_ATTR)

        self.assertEqual(len(data_attr), len(self.test_data))
        self.assertEqual(getattr(decorated, DATA_ATTR), self.test_data)


class BzBugIsOpenTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.bz_bug_is_open`."""
    # (protected-access) pylint:disable=W0212
    # (test names are long to make it readable) pylint:disable=C0103
    def setUp(self):
        """Back up objects and generate common values."""
        self.backup = decorators._get_bugzilla_bug
        self.bug_id = gen_integer()
        self.upstream_backup = conf.properties.get('main.upstream')

        self.valid_whiteboard_data = [
            'VERIFIED IN UPSTREAM',
            'VeRiFiEd In UpStReAm',
            'verified in upstream'
        ]
        self.invalid_whiteboard_data = [
            'VERIED IN UPSTREAM',
            'VeRiFiEd I UpStReAm',
            'verified in uppstream',
            'None',
            ''
        ]

    def tearDown(self):
        """Restore backed-up objects."""
        decorators._get_bugzilla_bug = self.backup
        conf.properties['main.upstream'] = self.upstream_backup

    def test_bug_is_open(self):
        """Assert ``True`` is returned if the bug is 'NEW' or 'ASSIGNED'."""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with an open status."""
            status = 'NEW'
            whiteboard = None
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id))
        MockBug.status = 'ASSIGNED'
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id))

    def test_bug_is_closed(self):
        """Assert ``False`` is returned if the bug is not open."""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with a closed status."""
            status = 'CLOSED'
            whiteboard = None
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

    def test_upstream_with_whiteboard(self):
        """Assert that upstream bug is not affected by whiteboard texts"""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug"""
            status = None
            whiteboard = None
        conf.properties['main.upstream'] = '1'  # upstream mode
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        # Assert bug is really closed with valid/invalid whiteboard texts
        for MockBug.status in BZ_CLOSED_STATUSES:
            for MockBug.whiteboard in (self.valid_whiteboard_data +
                                       self.invalid_whiteboard_data):
                self.assertFalse(decorators.bz_bug_is_open(self.bug_id))

        # Assert bug is really open with valid/invalid whiteboard texts
        for MockBug.status in BZ_OPEN_STATUSES:
            for MockBug.whiteboard in (self.valid_whiteboard_data +
                                       self.invalid_whiteboard_data):
                self.assertTrue(decorators.bz_bug_is_open(self.bug_id))

    def test_downstream_valid_whiteboard(self):
        """Assert ``True`` is returned if
        - bug is in any status
        - bug has a valid Whiteboard text
        - robottelo in downstream mode

        """
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with a closed status."""
            status = None
            whiteboard = None
        conf.properties['main.upstream'] = '0'  # downstream mode
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        for MockBug.status in BZ_OPEN_STATUSES + BZ_CLOSED_STATUSES:
            for MockBug.whiteboard in self.valid_whiteboard_data:
                self.assertTrue(decorators.bz_bug_is_open(self.bug_id))

    def test_downstream_closedbug_invalid_whiteboard(self):
        """Assert ``False`` is returned if
        - bug is in closed status
        - bug has an invalid Whiteboard text
        - robottelo in downstream mode

        """
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with a closed status."""
            status = None
            whiteboard = None
        conf.properties['main.upstream'] = '0'  # downstream mode
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        for MockBug.status in BZ_CLOSED_STATUSES:
            for MockBug.whiteboard in self.invalid_whiteboard_data:
                self.assertFalse(decorators.bz_bug_is_open(self.bug_id))

    def test_downstream_openbug_whiteboard(self):
        """Assert ``True`` is returned if
        - bug is in open status
        - bug has a valid/invalid Whiteboard text
        - robottelo in downstream mode

        """
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug"""
            status = None
            whiteboard = None
        conf.properties['main.upstream'] = '0'  # downstream mode
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        for MockBug.status in BZ_OPEN_STATUSES:
            for MockBug.whiteboard in (self.valid_whiteboard_data +
                                       self.invalid_whiteboard_data):
                self.assertTrue(decorators.bz_bug_is_open(self.bug_id))


class RmBugIsOpenTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.rm_bug_is_open`."""
    # (protected-access) pylint:disable=W0212
    def setUp(self):  # noqa pylint:disable=C0103
        """Back up objects and generate common values."""
        self.rm_backup = decorators._get_redmine_bug_status_id
        self.stat_backup = decorators._redmine_closed_issue_statuses
        decorators._redmine_closed_issue_statuses = lambda: [1, 2]
        self.bug_id = gen_integer()

    def tearDown(self):  # noqa pylint:disable=C0103
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


class RunOnlyOnTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.run_only_on`."""
    def setUp(self):  # noqa
        """Backup object."""
        self.project_backup = conf.properties.get('main.project')

    def tearDown(self):  # noqa
        """Restore backed-up object."""
        conf.properties['main.project'] = self.project_backup

    def test_project_mode_different_cases(self):  # pylint:disable=C0103
        """Assert ``True`` for different cases of accepted input values
           for project / robottelo modes."""
        accepted_values = ('SAT', 'SAt', 'SaT', 'Sat', 'sat', 'sAt',
                           'SAM', 'SAm', 'SaM', 'Sam', 'sam', 'sAm')

        # Test different project values
        conf.properties['main.project'] = 'sam'
        for project in accepted_values:
            self.assertTrue(decorators.run_only_on(project))

        # Test different mode values
        for mode in accepted_values:
            conf.properties['main.project'] = mode
            self.assertTrue(decorators.run_only_on('SAT'))

    def test_invalid_project(self):
        """Assert error is thrown when project has invalid value."""
        conf.properties['main.project'] = 'sam'
        with self.assertRaises(decorators.ProjectModeError):
            decorators.run_only_on('satddfddffdf')

    def test_invalid_mode(self):
        """Assert error is thrown when mode has invalid value."""
        # Invalid value for robottelo mode
        conf.properties['main.project'] = 'samtdd'
        with self.assertRaises(decorators.ProjectModeError):
            decorators.run_only_on('sat')
