"""Unit tests for :mod:`robottelo.decorators`."""
import six

from fauxfactory import gen_integer
from robottelo import decorators
from robottelo.config.base import BugzillaSettings
from robottelo.constants import (
    BUGZILLA_URL,
    BZ_CLOSED_STATUSES,
    BZ_OPEN_STATUSES
)
from unittest2 import SkipTest, TestCase
# (Too many public methods) pylint: disable=R0904

if six.PY2:
    import mock
else:
    from unittest import mock


class BzBugIsOpenTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.bz_bug_is_open`."""
    # (protected-access) pylint:disable=W0212
    # (test names are long to make it readable) pylint:disable=C0103
    def setUp(self):
        """Back up objects and generate common values."""
        self.backup = decorators._get_bugzilla_bug
        self.bug_id = gen_integer()
        self._get_host_sat_version_patcher = mock.patch(
            'robottelo.decorators.get_host_sat_version')
        self.get_sat_versions_mock = self._get_host_sat_version_patcher.start()
        self.get_sat_versions_mock.return_value = '6.3'

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
        self._get_host_sat_version_patcher.stop()

    def test_bug_is_open(self):
        """Assert ``True`` is returned if the bug is 'NEW' or 'ASSIGNED'."""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with an open status."""
            status = 'NEW'
            whiteboard = None
        decorators._get_bugzilla_bug = lambda bug_id: MockBug
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id))
        MockBug.status = 'ASSIGNED'
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id))

    def test_bug_is_closed(self):
        """Assert ``False`` is returned if the bug is not open."""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with a closed status."""
            status = 'CLOSED'
            whiteboard = None
            flags = [
                {'status': '', 'name': 'sat-6.2.z'},
                {'status': '+', 'name': 'sat-6.3.0'},
            ]
        decorators._get_bugzilla_bug = lambda bug_id: MockBug
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

    @mock.patch('robottelo.decorators.settings')
    def test_upstream_with_whiteboard(self, dec_settings):
        """Assert that upstream bug is not affected by whiteboard texts"""
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug"""
            status = None
            whiteboard = None
            flags = []
        dec_settings.upstream = True
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

    @mock.patch('robottelo.decorators.settings')
    def test_downstream_valid_whiteboard(self, dec_settings):
        """Assert ``True`` is returned if
        - bug is in any status
        - bug has a valid Whiteboard text
        - robottelo in downstream mode

        """
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with a closed status."""
            status = None
            whiteboard = None
            flags = [
                {'status': '', 'name': 'sat-6.2.z'},
                {'status': '+', 'name': 'sat-6.3.0'},
            ]
        dec_settings.upstream = False
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        for MockBug.status in BZ_OPEN_STATUSES + BZ_CLOSED_STATUSES:
            for MockBug.whiteboard in self.valid_whiteboard_data:
                # 'CLOSED' state overides whiteboard 'verified in upstream'
                if MockBug.status == 'CLOSED':
                    self.assertFalse(decorators.bz_bug_is_open(self.bug_id))
                else:
                    self.assertTrue(decorators.bz_bug_is_open(self.bug_id))

    @mock.patch('robottelo.decorators.settings')
    def test_downstream_closedbug_invalid_whiteboard(self, dec_settings):
        """Assert ``False`` is returned if
        - bug is in closed status
        - bug has an invalid Whiteboard text
        - robottelo in downstream mode

        """
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug with a closed status."""
            status = None
            whiteboard = None
            flags = [
                {'status': '', 'name': 'sat-6.2.z'},
                {'status': '+', 'name': 'sat-6.3.0'},
            ]
        dec_settings.upstream = False
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        for MockBug.status in BZ_CLOSED_STATUSES:
            for MockBug.whiteboard in self.invalid_whiteboard_data:
                self.assertFalse(decorators.bz_bug_is_open(self.bug_id))

    @mock.patch('robottelo.decorators.settings')
    def test_downstream_openbug_whiteboard(self, dec_settings):
        """Assert ``True`` is returned if
        - bug is in open status
        - bug has a valid/invalid Whiteboard text
        - robottelo in downstream mode

        """
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug"""
            status = None
            whiteboard = None
            flags = []
        dec_settings.upstream = False
        decorators._get_bugzilla_bug = lambda bug_id: MockBug()
        for MockBug.status in BZ_OPEN_STATUSES:
            for MockBug.whiteboard in (self.valid_whiteboard_data +
                                       self.invalid_whiteboard_data):
                self.assertTrue(decorators.bz_bug_is_open(self.bug_id))

    @mock.patch('robottelo.decorators.bugzilla.RHBugzilla')
    @mock.patch('robottelo.decorators.settings')
    def test_unauthenticated_bz_call(self, dec_settings, RHBugzilla):
        """Assert flags are not taken into account if bz credentials section is
        not present on robottelo.properties

        """
        dec_settings.upstream = False
        # Missing password
        bz_credentials = {'user': 'foo', 'password': None}
        dec_settings.bugzilla.get_credentials.return_value = bz_credentials

        class MockBug(object):  # pylint:disable=R0903
            """A mock bug if empty flags"""
            status = 'VERIFIED'
            whiteboard = None
            flags = []

        bz_conn_mock = mock.Mock()
        RHBugzilla.return_value = bz_conn_mock
        bz_conn_mock.getbug.return_value = MockBug

        self.assertFalse(decorators.bz_bug_is_open(self.bug_id))
        RHBugzilla.assert_called_once_with(url=BUGZILLA_URL)
        bz_conn_mock.getbug.assert_called_once_with(
            self.bug_id,
            include_fields=['id', 'status', 'whiteboard', 'flags']
        )
        MockBug.status = 'NEW'
        # Missing user
        bz_credentials.update({'user': None, 'password': 'foo'})
        # avoiding cache adding 1 to id
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id + 1))

    @mock.patch('robottelo.decorators.settings')
    def test_complete_bug_workflow(self, dec_settings):
        """Assert ``True`` is returned if host version is minor then 6.3,
        the minor version version with positive status
        """

        # ------------- Bug found on Satellite 6.2.3, 6.3 is GA version
        class MockBug(object):  # pylint:disable=R0903
            """A mock bug"""
            status = 'NEW'
            whiteboard = ''
            flags = [
                {'status': '?', 'name': 'sat-6.2.z'},
                {'status': '?', 'name': 'sat-6.3.0'},
            ]

        # Downstream
        dec_settings.upstream = False
        decorators._get_bugzilla_bug = lambda bug_id: MockBug

        for v in ['6.1', '6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(self.bug_id),
                'Should be open for all version because of status NEW'
            )

        # Upstream

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertTrue(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be open because of status NEW'
        )

        # ------------ Bug is fixed and verified on upstream
        MockBug.status = 'VERIFIED'
        MockBug.whiteboard = 'verified in upstream'
        MockBug.flags = [
            {'status': '?', 'name': 'sat-6.2.z'},
            {'status': '+', 'name': 'sat-6.3.0'},
        ]

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.1', '6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(self.bug_id),
                'Should be open for all versions because it is not on '
                'downstream'
            )

        # ------------ Bug landed z stream and we forget to remove verified
        # on upstream msg
        MockBug.status = 'VERIFIED'
        MockBug.whiteboard = 'verified in upstream'
        MockBug.flags = [
            {'status': '+', 'name': 'sat-6.2.z'},
            {'status': '+', 'name': 'sat-6.3.0'},
        ]

        # Test running against upstream
        dec_settings.upstream = False
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(self.bug_id),
                'Should be closed for all versions because it landed z stream'
            )

        self.get_sat_versions_mock.return_value = '6.1'
        self.assertTrue(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be open because 6.1 < 6.2 on flags '
        )

        # ------------ Bug landed downstream snap
        MockBug.status = 'VERIFIED'
        MockBug.whiteboard = ''
        MockBug.flags = [
            {'status': '?', 'name': 'sat-6.2.z'},
            {'status': '+', 'name': 'sat-6.3.0'},
        ]

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(self.bug_id),
                'Should be closed for all versions greater or equals to 6.3, '
                'version present on flags'
            )

        # ------------ Bug landed z stream
        MockBug.status = 'VERIFIED'
        MockBug.whiteboard = ''
        MockBug.flags = [
            {'status': '+', 'name': 'sat-6.2.z'},
            {'status': '+', 'name': 'sat-6.3.0'},
        ]

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(self.bug_id),
                'Should be closed for all versions greater or equals to 6.3, '
                'version present on flags'
            )

        self.get_sat_versions_mock.return_value = '6.1'
        self.assertTrue(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be open because 6.1 is less then 6.2, the minor version '
            'on flags with +'
        )

        # ------------ Bug is closed
        MockBug.status = 'CLOSED'

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(self.bug_id),
                'Should be closed for all versions greater or equals to 6.3, '
                'version present on flags'
            )

        self.get_sat_versions_mock.return_value = '6.1'
        self.assertTrue(
            decorators.bz_bug_is_open(self.bug_id),
            'Should be open because 6.1 is less then 6.2, the minor version '
            'on flags with +'
        )


class CacheableTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.cacheable`."""
    def setUp(self):
        self.object_cache_patcher = mock.patch.dict(
            'robottelo.decorators.OBJECT_CACHE')
        self.object_cache = self.object_cache_patcher.start()

        def make_foo(options):
            return {'id': 42}

        self.make_foo = decorators.cacheable(make_foo)

    def tearDown(self):
        self.object_cache_patcher.stop()

    def test_build_cache(self):
        """Create a new object and add it to the cache."""
        obj = self.make_foo(cached=True)
        self.assertEqual(decorators.OBJECT_CACHE, {'foo': {'id': 42}})
        self.assertEqual(id(decorators.OBJECT_CACHE['foo']), id(obj))

    def test_return_from_cache(self):
        """Return an already cached object."""
        cache_obj = {'id': 42}
        decorators.OBJECT_CACHE['foo'] = cache_obj
        obj = self.make_foo(cached=True)
        self.assertEqual(id(cache_obj), id(obj))

    def test_create_and_not_add_to_cache(self):
        """Create a new object and not add it to the cache."""
        self.make_foo(cached=False)
        self.assertNotIn('foo', decorators.OBJECT_CACHE)
        self.assertEqual(decorators.OBJECT_CACHE, {})


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


class GetBugzillaBugStatusIdTestCase(TestCase):
    """Tests for ``robottelo.decorators._get_bugzilla_bug``."""
    def setUp(self):
        self.bugzilla_patcher = mock.patch('robottelo.decorators.bugzilla')
        self.settings_patcher = mock.patch(
            'robottelo.decorators.settings')
        self.settings = BugzillaSettings()
        self.settings.username = 'admin'
        self.settings.password = 'changeme'
        settings_mock = self.settings_patcher.start()
        settings_mock.bugzilla = self.settings
        self.bugzilla = self.bugzilla_patcher.start()

    def tearDown(self):
        self.bugzilla_patcher.stop()
        self.settings_patcher.stop()

    def test_cached_bug(self):
        """Return bug information from the cache."""
        with mock.patch.dict(
                'robottelo.decorators._bugzilla', {'4242': 42}):
            self.assertEqual(decorators._get_bugzilla_bug('4242'), 42)

    def test_not_cached_bug(self):
        """Fetch bug information and cache it."""
        bug = {'id': 42}
        connection = mock.MagicMock()
        connection.getbug.return_value = bug
        self.bugzilla.RHBugzilla.return_value = connection

        with mock.patch.dict(
                'robottelo.decorators._bugzilla', {}):
            self.assertEqual(id(decorators._get_bugzilla_bug('4242')), id(bug))
        self.bugzilla.RHBugzilla.assert_called_once_with(
            url=BUGZILLA_URL,
            user=self.settings.username,
            password=self.settings.password
        )

    def test_raise_bug_fetch_error_getbug_fault(self):
        """Raise BugFetchError due to Fault exception on getbugsimple."""
        connection = mock.MagicMock()
        connection.getbug.side_effect = [
            decorators.Fault(42, 'What is the answer?')]
        self.bugzilla.RHBugzilla.return_value = connection

        with mock.patch.dict(
                'robottelo.decorators._redmine', {}):
            with self.assertRaises(decorators.BugFetchError):
                decorators._get_bugzilla_bug('4242')

    def test_raise_bug_fetch_error_getbug_expaterror(self):
        """Raise BugFetchError due to an ExpatError exception on
        getbugsimple.
        """
        expaterror = decorators.ExpatError()
        expaterror.code = 12
        connection = mock.MagicMock()
        connection.getbug.side_effect = [expaterror]
        self.bugzilla.RHBugzilla.return_value = connection

        with mock.patch.dict(
                'robottelo.decorators._redmine', {}):
            with self.assertRaises(decorators.BugFetchError):
                decorators._get_bugzilla_bug('4242')


class GetRedmineBugStatusIdTestCase(TestCase):
    """Tests for ``robottelo.decorators._get_redmine_bug_status_id``."""
    def test_cached_bug(self):
        """Return bug status from the cache."""
        with mock.patch.dict(
                'robottelo.decorators._redmine', issues={'4242': 42}):
            self.assertEqual(decorators._get_redmine_bug_status_id('4242'), 42)

    @mock.patch('robottelo.decorators.requests')
    def test_not_cached_bug(self, requests):
        """Return bug status."""
        bug_id = '4242'
        result = mock.MagicMock()
        result.json.side_effect = [{'issue': {'status': {'id': 42}}}]
        result.status_code = 200
        requests.get.side_effect = [result]
        with mock.patch.dict(
                'robottelo.decorators._redmine', issues={}):
            self.assertEqual(decorators._get_redmine_bug_status_id('4242'), 42)
            requests.get.assert_called_once_with(
                '{0}/issues/{1}.json'.format(decorators.REDMINE_URL, bug_id))

    @mock.patch('robottelo.decorators.requests')
    def test_raise_bug_fetch_error_status_code(self, requests):
        """Return bug status."""
        result = mock.MagicMock()
        result.status_code = 404
        requests.get.side_effect = [result]
        with mock.patch.dict(
                'robottelo.decorators._redmine', issues={}):
            with self.assertRaises(decorators.BugFetchError):
                decorators._get_redmine_bug_status_id('4242')

    @mock.patch('robottelo.decorators.requests')
    def test_raise_bug_fetch_error_key_error(self, requests):
        """Return bug status."""
        bug_id = '4242'
        result = mock.MagicMock()
        result.json.side_effect = [{'issue': {'status': {}}}]
        result.status_code = 200
        requests.get.side_effect = [result]
        with mock.patch.dict(
                'robottelo.decorators._redmine', issues={}):
            with self.assertRaises(decorators.BugFetchError):
                decorators._get_redmine_bug_status_id('4242')
        requests.get.assert_called_once_with(
            '{0}/issues/{1}.json'.format(decorators.REDMINE_URL, bug_id))


class RedmineClosedIssueStatusesTestCase(TestCase):
    """Tests for ``robottelo.decorators._redmine_closed_issue_statuses``."""
    @mock.patch('robottelo.decorators.requests')
    def test_build_cache(self, requests):
        """Build closed issue statuses cache."""
        result = mock.MagicMock()
        result.json.side_effect = [{
            'issue_statuses': [{
                'id': 42,
                'is_closed': True,
            }, {
                'id': 12,
                'is_closed': False,
            }]
        }]
        result.status_code = 200
        requests.get.side_effect = [result]
        with mock.patch.dict(
                'robottelo.decorators._redmine', closed_statuses=None):
            self.assertEqual(
                decorators._redmine_closed_issue_statuses(),
                [42]
            )
        requests.get.assert_called_once_with(
            '{0}/issue_statuses.json'.format(decorators.REDMINE_URL))

    @mock.patch('robottelo.decorators.requests')
    def test_return_cache(self, requests):
        """Return the cache if already built."""
        with mock.patch.dict(
                'robottelo.decorators._redmine', closed_statuses=[42]):
            self.assertEqual(
                decorators._redmine_closed_issue_statuses(),
                [42]
            )
        requests.get.assert_not_called()


class RunOnlyOnTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.run_only_on`."""
    @mock.patch('robottelo.decorators.settings')
    def test_project_mode_different_cases(self, settings):
        """Assert ``True`` for different cases of accepted input values
           for project / robottelo modes."""
        accepted_values = ('SAT', 'SAt', 'SaT', 'Sat', 'sat', 'sAt',
                           'SAM', 'SAm', 'SaM', 'Sam', 'sam', 'sAm')

        # Test different project values
        settings.project = 'sam'
        for project in accepted_values:
            self.assertTrue(decorators.run_only_on(project))

        # Test different mode values
        for mode in accepted_values:
            settings.project = mode
            self.assertTrue(decorators.run_only_on('SAT'))

    @mock.patch('robottelo.decorators.settings')
    def test_invalid_project(self, dec_settings):
        """Assert error is thrown when project has invalid value."""
        dec_settings.project = 'sam'

        @decorators.run_only_on('satddfddffdf')
        def dummy():
            pass

        with self.assertRaises(decorators.ProjectModeError):
            dummy()

    @mock.patch('robottelo.decorators.settings')
    def test_invalid_mode(self, dec_settings):
        """Assert error is thrown when mode has invalid value."""
        # Invalid value for robottelo mode
        dec_settings.project = 'samtdd'

        @decorators.run_only_on('sat')
        def dummy():
            pass

        with self.assertRaises(decorators.ProjectModeError):
            dummy()

    @mock.patch('robottelo.decorators.settings')
    def test_default_project_value(self, settings):
        settings.project = None

        @decorators.run_only_on('sat')
        def dummy():
            return 42

        self.assertEqual(dummy(), 42)

    @mock.patch('robottelo.decorators.settings')
    def test_raise_skip_test(self, settings):
        settings.project = 'sam'

        @decorators.run_only_on('sat')
        def dummy():
            return 42

        with self.assertRaises(SkipTest):
            dummy()


class SkipIfBugOpen(TestCase):
    """Tests for :func:`robottelo.decorators.skip_if_bug_open`."""
    def test_raise_bug_type_error(self):
        with self.assertRaises(decorators.BugTypeError):
            @decorators.skip_if_bug_open('notvalid', 123456)
            def foo():
                pass

    @mock.patch('robottelo.decorators.bz_bug_is_open')
    def test_skip_bugzilla_bug(self, bz_bug_is_open):
        bz_bug_is_open.side_effect = [True]

        @decorators.skip_if_bug_open('bugzilla', 123456)
        def foo():
            pass

        with self.assertRaises(SkipTest):
            foo()

    @mock.patch('robottelo.decorators.bz_bug_is_open')
    def test_not_skip_bugzilla_bug(self, bz_bug_is_open):
        bz_bug_is_open.side_effect = [False]

        @decorators.skip_if_bug_open('bugzilla', 123456)
        def foo():
            return 42

        self.assertEqual(foo(), 42)

    @mock.patch('robottelo.decorators.rm_bug_is_open')
    def test_skip_redmine_bug(self, rm_bug_is_open):
        rm_bug_is_open.side_effect = [True]

        @decorators.skip_if_bug_open('redmine', 123456)
        def foo():
            pass

        with self.assertRaises(SkipTest):
            foo()

    @mock.patch('robottelo.decorators.rm_bug_is_open')
    def test_not_skip_redmine_bug(self, rm_bug_is_open):
        rm_bug_is_open.side_effect = [False]

        @decorators.skip_if_bug_open('redmine', 123456)
        def foo():
            return 42

        self.assertEqual(foo(), 42)


class SkipIfNotSetTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.skip_if_not_set`."""
    def setUp(self):
        self.settings_patcher = mock.patch('robottelo.decorators.settings')
        self.settings = self.settings_patcher.start()
        self.settings.all_features = ['clients']

    def tearDown(self):
        self.settings_patcher.stop()

    def test_raise_skip_if_method(self):
        """Skip a test method if configuration is missing."""
        self.settings.clients.validate.side_effect = ['Validation error']

        @decorators.skip_if_not_set('clients')
        def dummy():
            pass

        with self.assertRaises(SkipTest):
            dummy()

    def test_raise_skip_if_setup(self):
        """Skip setUp method if configuration is missing."""
        self.settings.clients.validate.side_effect = ['Validation error']

        class MyTestCase(object):
            @decorators.skip_if_not_set('clients')
            def setUp(self):
                pass

        test_case = MyTestCase()
        with self.assertRaises(SkipTest):
            test_case.setUp()

    def test_raise_skip_if_setupclass(self):
        """Skip setUpClass method if configuration is missing."""
        self.settings.clients.validate.side_effect = ['Validation error']

        class MyTestCase(object):
            @classmethod
            @decorators.skip_if_not_set('clients')
            def setUpClass(cls):
                pass

        with self.assertRaises(SkipTest):
            MyTestCase.setUpClass()

    def test_not_raise_skip_if(self):
        """Don't skip if configuration is available."""
        self.settings.clients.validate.side_effect = [[]]

        @decorators.skip_if_not_set('clients')
        def dummy():
            return 'ok'

        self.assertEqual(dummy(), 'ok')

    def test_raise_value_error(self):
        """ValueError is raised when a misspelled feature is passed."""
        with self.assertRaises(ValueError):
            @decorators.skip_if_not_set('client')
            def dummy():
                pass

    def test_configure_settings(self):
        """Call settings.configure() if settings is not configured."""
        self.settings.clients.validate.side_effect = [[]]
        self.settings.configured = False

        @decorators.skip_if_not_set('clients')
        def dummy():
            return 'ok'

        self.assertEqual(dummy(), 'ok')
        self.settings.configure.called_once_with()


class StubbedTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.stubbed`."""
    @mock.patch('robottelo.decorators.unittest2.skip')
    def test_default_reason(self, skip):

        @decorators.stubbed()
        def foo():
            pass

        skip.assert_called_once_with(decorators.NOT_IMPLEMENTED)

    @mock.patch('robottelo.decorators.unittest2.skip')
    def test_reason(self, skip):

        @decorators.stubbed('42 is the answer')
        def foo():
            pass

        skip.assert_called_once_with('42 is the answer')
