"""Unit tests for :mod:`robottelo.decorators`."""
from itertools import product, chain

import six
from fauxfactory import gen_integer
from unittest2 import SkipTest, TestCase

from robottelo import decorators
from robozilla import decorators as robozilla_decorators
from robottelo.config.base import BugzillaSettings
from robottelo.constants import BZ_CLOSED_STATUSES, BZ_OPEN_STATUSES

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
        self.backup = robozilla_decorators._get_bugzilla_bug
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
        robozilla_decorators._get_bugzilla_bug = self.backup
        self._get_host_sat_version_patcher.stop()

    def test_bug_is_open(self):
        """Assert ``True`` is returned if the bug is 'NEW' or 'ASSIGNED'."""

        original_bug = {
            'id': 1,
            'status': 'NEW',
            'whiteboard': ''
        }

        robozilla_decorators._get_bugzilla_bug = (
            lambda bug_id, **_: original_bug
        )
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id,
                                                  sat_version_picker=None))
        original_bug['status'] = 'ASSIGNED'
        self.assertTrue(decorators.bz_bug_is_open(self.bug_id,
                                                  sat_version_picker=None))

    def test_bug_is_closed(self):
        """Assert ``False`` is returned if the bug is not open."""
        original_bug = {
            'id': 1,
            'status': 'CLOSED',
            'whiteboard': '',
            'target_milestone': 'Unspecified',
            'flags': {'sat-6.2.z': '', 'sat-6.3.0': '+'}
        }

        robozilla_decorators._get_bugzilla_bug = (
            lambda bug_id, **_: original_bug
        )
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id,
                                                   sat_version_picker=None))
        original_bug['status'] = 'ON_QA'
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id,
                                                   sat_version_picker=None))
        original_bug['status'] = 'SLOWLY DRIVING A DEV INSANE'
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id,
                                                   sat_version_picker=None))

    def test_bug_lookup_fails(self):
        """Assert ``False`` is returned if the bug cannot be found."""
        robozilla_decorators._get_bugzilla_bug = lambda _, **__: None
        self.assertFalse(decorators.bz_bug_is_open(self.bug_id,
                                                   sat_version_picker=None))

    @mock.patch('robottelo.decorators.settings')
    def test_upstream_with_whiteboard(self, dec_settings):
        """Assert that upstream bug is not affected by whiteboard texts"""

        original_bug = {
            'id': 1,
            'status': 'NEW',
            'whiteboard': '',
        }

        dec_settings.upstream = True
        robozilla_decorators._get_bugzilla_bug = (
            lambda bug_id, **_: original_bug
        )
        # Assert bug is really closed with valid/invalid whiteboard texts
        white_board_data = (
            self.valid_whiteboard_data + self.invalid_whiteboard_data)
        for original_bug['status'], original_bug['whiteboard'] in \
                product(BZ_CLOSED_STATUSES, white_board_data):
            self.assertFalse(decorators.bz_bug_is_open(
                self.bug_id, sat_version_picker=None))

        # Assert bug is really open with valid/invalid whiteboard texts
        for original_bug['status'], original_bug['whiteboard'] in \
                product(BZ_OPEN_STATUSES, white_board_data):
            self.assertTrue(decorators.bz_bug_is_open(
                self.bug_id, sat_version_picker=None))

    @mock.patch('robottelo.decorators.settings')
    def test_downstream_valid_whiteboard(self, dec_settings):
        """Assert ``True`` is returned if
        - bug is in any status
        - bug has a valid Whiteboard text
        - robottelo in downstream mode
        """

        original_bug = {
            'id': 1,
            'status': 'CLOSED',
            'whiteboard': '',
            'target_milestone': 'Unspecified',
            'flags': {'sat-6.2.z': '', 'sat-6.3.0': '+'}
        }

        dec_settings.upstream = False
        robozilla_decorators._get_bugzilla_bug = (
            lambda bug_id, **_: original_bug
        )
        all_statuses = chain(BZ_OPEN_STATUSES, BZ_CLOSED_STATUSES)
        for original_bug['status'], original_bug['whiteboard'] in \
                product(all_statuses, self.valid_whiteboard_data):
            if original_bug['status'] == 'CLOSED':
                self.assertFalse(decorators.bz_bug_is_open(
                    self.bug_id, sat_version_picker=None))
            else:
                self.assertTrue(decorators.bz_bug_is_open(
                    self.bug_id, sat_version_picker=None))

    @mock.patch('robottelo.decorators.settings')
    def test_downstream_closedbug_invalid_whiteboard(self, dec_settings):
        """Assert ``False`` is returned if
        - bug is in closed status
        - bug has an invalid Whiteboard text
        - robottelo in downstream mode

        """

        original_bug = {
            'id': 1,
            'status': 'CLOSED',
            'whiteboard': '',
            'target_milestone': 'Unspecified',
            'flags': {'sat-6.2.z': '', 'sat-6.3.0': '+'}
        }

        dec_settings.upstream = False
        robozilla_decorators._get_bugzilla_bug = (
            lambda bug_id, **_: original_bug
        )
        for original_bug['status'], original_bug['whiteboard'] in \
                product(BZ_CLOSED_STATUSES, self.invalid_whiteboard_data):
            self.assertFalse(decorators.bz_bug_is_open(
                self.bug_id, sat_version_picker=None))

    @mock.patch('robottelo.decorators.settings')
    def test_downstream_openbug_whiteboard(self, dec_settings):
        """Assert ``True`` is returned if
        - bug is in open status
        - bug has a valid/invalid Whiteboard text
        - robottelo in downstream mode

        """

        original_bug = {
            'id': 1,
            'status': '',
            'whiteboard': ''
        }

        dec_settings.upstream = False
        robozilla_decorators._get_bugzilla_bug = (
            lambda bug_id, **_: original_bug
        )
        all_whiteboard_data = chain(
            self.valid_whiteboard_data, self.invalid_whiteboard_data)
        for original_bug['status'], original_bug['whiteboard'] in \
                product(BZ_OPEN_STATUSES, all_whiteboard_data):
            self.assertTrue(decorators.bz_bug_is_open(
                self.bug_id, sat_version_picker=None)
            )

    @mock.patch('robozilla.decorators.BZReader')
    @mock.patch('robottelo.decorators.settings')
    def test_unauthenticated_bz_call(self, dec_settings, BZReader):
        """Assert flags are not taken into account if bz credentials section is
        not present on robottelo.properties

        """
        dec_settings.upstream = False
        # Missing password
        bz_credentials = {'user': 'foo', 'password': None}
        dec_settings.bugzilla.get_credentials.return_value = bz_credentials

        original_bug = {
            'id': 1,
            'status': 'VERIFIED',
            'target_milestone': 'Unspecified',
            'whiteboard': ''
        }

        bz_reader = mock.Mock()
        BZReader.return_value = bz_reader
        bz_reader.get_bug_data.return_value = original_bug

        self.assertFalse(decorators.bz_bug_is_open(
            original_bug['id'], sat_version_picker=None))
        BZReader.assert_called_once_with(
            {},
            include_fields=[
                'id', 'status', 'whiteboard', 'flags', 'resolution',
                'target_milestone'
            ],
            follow_clones=True,
            follow_duplicates=True
        )
        bz_reader.get_bug_data.assert_called_once_with(original_bug['id'])
        original_bug['status'] = 'ASSIGNED'
        # Missing user
        bz_credentials.update({'user': None, 'password': 'foo'})
        # avoiding cache adding 1 to id
        self.assertTrue(decorators.bz_bug_is_open(
            original_bug['id'] + 1, sat_version_picker=None))

    @mock.patch('robottelo.decorators.settings')
    def test_complete_bug_workflow(self, dec_settings):
        """Assert ``True`` is returned if host version is minor than 6.3,
        the minor version version with positive status
        """

        def set_downstream_flag(bug, value):
            bug['flags']['sat-6.3.0'] = value

        def set_zstream_flag(bug, value):
            bug['flags']['sat-6.2.z'] = value

        # Downstream
        dec_settings.upstream = False
        original_bug = {
            'id': 1,
            'status': 'NEW',
            'whiteboard': '',
            'flags': {'sat-6.2.z': '?', 'sat-6.3.0': '?'},
            'target_milestone': 'Unspecified'
        }

        bugzilla_server = {}

        def add_bug_on_server(bug):
            bugzilla_server[bug['id']] = bug

        robozilla_decorators._get_bugzilla_bug = (
            lambda bug_id, **_: bugzilla_server[bug_id]
        )

        add_bug_on_server(original_bug)

        for v in ['6.1', '6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(
                    original_bug['id'], sat_version_picker=lambda: v),
                'Should be open for all version because of status NEW'
            )

        # Upstream

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertTrue(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=lambda: v,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be open because of status NEW'
        )

        # ------------ Bug is fixed and verified on upstream
        original_bug['status'] = 'VERIFIED'
        original_bug['whiteboard'] = 'verified in upstream'
        set_downstream_flag(original_bug, '+')

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=lambda: v,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.1', '6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(
                    original_bug['id'], sat_version_picker=lambda: v
                ),
                'Should be open for all versions because it is not on '
                'downstream'
            )

        # ------------ Bug landed downstream snap
        original_bug['whiteboard'] = ''

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(
                    original_bug['id'], sat_version_picker=lambda: v),
                'Should be closed for all versions greater or equals to 6.3, '
                'version present on flags'
            )

        # ------------ Bug has 2 positive flags and target_milestone
        # Unspecified
        set_downstream_flag(original_bug, '+')
        set_zstream_flag(original_bug, '+')

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.1', '6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(
                    original_bug['id'], sat_version_picker=lambda: v),
                'Should be open for all versions because bug has 2 '
                'positive sat version flags and no defined target milestone'
            )

        # ------------ Bug has 2 positive flags and target_milestone GA
        original_bug['target_milestone'] = 'GA'
        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(
                    original_bug['id'],
                    sat_version_picker=lambda: v
                ),
                'Should be False for all versions greater than 6.3'
                'because target_milestone is GA and non zstream flag is 6.3'
            )

        for v in ['6.1', '6.2']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be True for all versions less than 6.3'
            )

        # ------------ Bug has 2 positive flags and target_milestone 6.3.0
        original_bug['target_milestone'] = '6.3.0'
        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(
                    original_bug['id'],
                    sat_version_picker=lambda: v
                ),
                'Should be False for all versions greater than 6.3'
                'because target_milestone is GA and non zstrem flag '
                'is 6.3'
            )

        for v in ['6.1', '6.2']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be True for all versions less than 6.3'
            )

        # ------------ Bug has 2 positive flags and target_milestone 6.2.9
        original_bug['target_milestone'] = '6.2.9'
        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(
                    original_bug['id'], sat_version_picker=lambda: v
                ),
                'Should be False for all versions greater than 6.2'
            )

        for v in ['6.1']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be True for all versions less than 6.2'
            )

        # ------------ Bug has 2 positive flags and target_milestone 6.3.0
        original_bug['target_milestone'] = '6.3.0'
        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(
                    original_bug['id'], sat_version_picker=lambda: v
                ),
                'Should be False for all versions greater than 6.3'
            )

        for v in ['6.2', '6.1']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be True for all versions less than 6.3'
            )

        # ------------ Decided to cherry pick fix to z stream

        # clone
        cloned_bug = {
            'id': 2,
            'status': 'NEW',
            'whiteboard': '',
            'target_milestone': 'Unspecified',
            'flags': {'sat-6.2.z': '+', 'sat-6.3.0': '?'}
        }

        add_bug_on_server(cloned_bug)
        original_bug['other_clones'] = {cloned_bug['id']: cloned_bug}

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.1', '6.2']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be open for all versions less or equals to 6.3, '
                'version present on flags'
            )

        for v in ['6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be closed for all versions greater or equals to 6.3, '
                'version present on flags'
            )

        # ------------ Cherry pick landed z stream
        cloned_bug['status'] = 'ON_QA'

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.0', '6.1']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be open for all versions less or equals to 6.2, minor'
                ' version present on flags for orignal_bug + clones'
            )

        for v in ['6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be closed for all versions greater or equals to '
                '6.2, minor version present on flags for orignal_bug + clones'
            )

        # ------------ Bug is closed
        cloned_bug['status'] = 'CLOSED'

        # Test running against upstream
        dec_settings.upstream = True
        self.get_sat_versions_mock.return_value = 'Does not apply'

        self.assertFalse(
            decorators.bz_bug_is_open(
                original_bug['id'],
                sat_version_picker=None,
                config_picker=lambda: {'upstream': True}
            ),
            'Should be closed for testing on upstream'
        )

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.2', '6.3', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be closed for all versions greater or equals to to '
                '6.2, minor version present on flags for orignal_bug + clones'
            )

        self.get_sat_versions_mock.return_value = '6.1'
        self.assertTrue(
            decorators.bz_bug_is_open(original_bug['id'],
                                      sat_version_picker=lambda: '6.1'),
            'Should be open because 6.1 is less than 6.2, the minor version '
            'on flags with +'
        )

        # Had original bug for 6.2.z, decided to port to 6.3 and haven't
        # finished porting yet
        original_bug = {
            'id': 1,
            'status': 'VERIFIED',
            'whiteboard': '',
            'flags': {'sat-6.2.z': '+'},
            'target_milestone': 'Unspecified'
        }
        cloned_bug = {
            'id': 2,
            'status': 'NEW',
            'whiteboard': '',
            'target_milestone': 'Unspecified',
            'flags': {'sat-6.3.0': '+'}
        }

        add_bug_on_server(original_bug)
        add_bug_on_server(cloned_bug)
        original_bug['other_clones'] = {cloned_bug['id']: cloned_bug}

        # Test running against downstream
        dec_settings.upstream = False

        for v in ['6.1', '6.3']:
            self.get_sat_versions_mock.return_value = v
            self.assertTrue(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be open for previous versions and versions which have '
                'a separate clone in opened state'
            )

        for v in ['6.2', '6.4', '6.5']:
            self.get_sat_versions_mock.return_value = v
            self.assertFalse(
                decorators.bz_bug_is_open(original_bug['id'],
                                          sat_version_picker=lambda: v),
                'Should be closed for 6.2 as original bug is closed in 6.2.z '
                'and all the next versions which do not have a separate clone'
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
        self.rm_backup = robozilla_decorators._get_redmine_bug_status_id
        self.stat_backup = robozilla_decorators._redmine_closed_issue_statuses
        robozilla_decorators._redmine_closed_issue_statuses = lambda: [1, 2]
        self.bug_id = gen_integer()

    def tearDown(self):  # noqa pylint:disable=C0103
        """Restore backed-up objects."""
        robozilla_decorators._get_redmine_bug_status_id = self.rm_backup
        robozilla_decorators._redmine_closed_issue_statuses = self.stat_backup

    def test_bug_is_open(self):
        """Assert ``True`` is returned if the bug is open."""
        robozilla_decorators._get_redmine_bug_status_id = lambda bug_id: 0
        self.assertTrue(decorators.rm_bug_is_open(self.bug_id))
        robozilla_decorators._get_redmine_bug_status_id = lambda bug_id: 3
        self.assertTrue(decorators.rm_bug_is_open(self.bug_id))

    def test_bug_is_closed(self):
        """Assert ``False`` is returned if the bug is closed."""
        robozilla_decorators._get_redmine_bug_status_id = lambda bug_id: 1
        self.assertFalse(decorators.rm_bug_is_open(self.bug_id))
        robozilla_decorators._get_redmine_bug_status_id = lambda bug_id: 2
        self.assertFalse(decorators.rm_bug_is_open(self.bug_id))

    def test_bug_lookup_fails(self):
        """Assert ``False`` is returned if the bug cannot be found."""

        def bomb(_):
            """A function that mocks a failure to fetch a bug."""
            raise robozilla_decorators.BugFetchError

        robozilla_decorators._get_redmine_bug_status_id = bomb
        self.assertFalse(decorators.rm_bug_is_open(self.bug_id))


class GetBugzillaBugStatusIdTestCase(TestCase):
    """Tests for ``robottelo.robozilla_decorators._get_bugzilla_bug``."""

    def setUp(self):
        self.robozilla_patcher = mock.patch('robozilla.decorators.BZReader')
        self.settings_patcher = mock.patch(
            'robottelo.decorators.settings')
        self.settings = BugzillaSettings()
        self.settings.username = 'admin'
        self.settings.password = 'changeme'
        settings_mock = self.settings_patcher.start()
        settings_mock.bugzilla = self.settings
        self.BZReader = self.robozilla_patcher.start()

    def tearDown(self):
        self.robozilla_patcher.stop()
        self.settings_patcher.stop()

    def test_cached(self):
        """Return bug information from the cache."""
        with mock.patch.dict('robozilla.decorators._bugzilla', {'4242': 42}):
            self.assertEqual(
                robozilla_decorators._get_bugzilla_bug('4242'), 42)

    def test_not_cached_bug(self):
        """Fetch bug information and cache it."""
        bug = {'id': 4242}
        get_bug_data = self.BZReader.return_value.get_bug_data
        get_bug_data.return_value = bug

        credentials = {
            'user': self.settings.username, 'password': self.settings.password}

        with mock.patch.dict('robozilla.decorators._bugzilla', {}):
            self.assertIs(
                robozilla_decorators._get_bugzilla_bug(
                    bug['id'],
                    bz_credentials=credentials
                ),
                bug
            )

        self.BZReader.assert_called_once_with(
            credentials,
            include_fields=[
                'id', 'status', 'whiteboard', 'flags', 'resolution',
                'target_milestone'
            ],
            follow_clones=True,
            follow_duplicates=True
        )

        get_bug_data.assert_called_once_with(bug['id'])


class GetRedmineBugStatusIdTestCase(TestCase):
    """Tests for ``robottelo.robozilla_decorators._get_redmine_bug_status_id``.
    """

    def test_cached_bug(self):
        """Return bug status from the cache."""
        with mock.patch.dict('robozilla.decorators._redmine',
                             issues={'4242': 42}):
            self.assertEqual(
                robozilla_decorators._get_redmine_bug_status_id('4242'), 42)

    @mock.patch('robozilla.decorators.requests')
    def test_not_cached_bug(self, requests):
        """Return bug status."""
        bug_id = '4242'
        result = mock.MagicMock()
        result.json.side_effect = [{'issue': {'status': {'id': 42}}}]
        result.status_code = 200
        requests.get.side_effect = [result]
        with mock.patch.dict('robozilla.decorators._redmine', issues={}):
            self.assertEqual(
                robozilla_decorators._get_redmine_bug_status_id('4242'), 42)
            requests.get.assert_called_once_with(
                '{0}/issues/{1}.json'.format(
                    robozilla_decorators.REDMINE_URL, bug_id))

    @mock.patch('robozilla.decorators.requests')
    def test_raise_bug_fetch_error_status_code(self, requests):
        """Return bug status."""
        result = mock.MagicMock()
        result.status_code = 404
        requests.get.side_effect = [result]
        with mock.patch.dict('robozilla.decorators._redmine', issues={}):
            with self.assertRaises(robozilla_decorators.BugFetchError):
                robozilla_decorators._get_redmine_bug_status_id('4242')

    @mock.patch('robozilla.decorators.requests')
    def test_raise_bug_fetch_error_key_error(self, requests):
        """Return bug status."""
        bug_id = '4242'
        result = mock.MagicMock()
        result.json.side_effect = [{'issue': {'status': {}}}]
        result.status_code = 200
        requests.get.side_effect = [result]
        with mock.patch.dict('robozilla.decorators._redmine', issues={}):
            with self.assertRaises(robozilla_decorators.BugFetchError):
                robozilla_decorators._get_redmine_bug_status_id('4242')
        requests.get.assert_called_once_with(
            '{0}/issues/{1}.json'.format(
                robozilla_decorators.REDMINE_URL, bug_id))


class RedmineClosedIssueStatusesTestCase(TestCase):
    """Tests for
    ``robottelo.decorators._redmine_closed_issue_statuses``."""

    @mock.patch('robozilla.decorators.requests')
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
                'robozilla.decorators._redmine', closed_statuses=None):
            self.assertEqual(
                robozilla_decorators._redmine_closed_issue_statuses(),
                [42]
            )
        requests.get.assert_called_once_with(
            '{0}/issue_statuses.json'.format(robozilla_decorators.REDMINE_URL))

    @mock.patch('robozilla.decorators.requests')
    def test_return_cache(self, requests):
        """Return the cache if already built."""
        with mock.patch.dict(
                'robozilla.decorators._redmine', closed_statuses=[42]):
            self.assertEqual(
                robozilla_decorators._redmine_closed_issue_statuses(),
                [42]
            )
        requests.get.assert_not_called()


class RunOnlyOnTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.run_only_on`."""

    @mock.patch('robottelo.decorators.settings')
    def test_project_mode_different_cases(self, settings):
        """Assert ``True`` for different cases of accepted input values
           for project / robottelo modes."""
        accepted_values = (
            'SAT', 'SAt', 'SaT', 'Sat', 'sat', 'sAt',
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


class SkipIfTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.skip_if`."""

    def test_raise_skip_test(self):
        """Skip a test method on True condition"""
        @decorators.skip_if(True)
        def dummy():
            pass

        with self.assertRaises(SkipTest):
            dummy()

    def test_execute_test_with_false(self):
        """Execute a test method on False condition"""
        @decorators.skip_if(False)
        def dummy():
            pass

        dummy()

    def test_raise_type_error(self):
        """Type error is raised with no condition (None) provided"""
        with self.assertRaises(TypeError):
            @decorators.skip_if()
            def dummy():
                pass

            dummy()

    def test_raise_default_message(self):
        """Test is skipped with a default message"""
        @decorators.skip_if(True)
        def dummy():
            pass

        try:
            dummy()
        except SkipTest as err:
            self.assertIn(
                'Skipping due expected condition is true',
                err.args
            )

    def test_raise_custom_message(self):
        """Test is skipped with a custom message"""
        @decorators.skip_if(True, 'foo')
        def dummy():
            pass

        try:
            dummy()
        except SkipTest as err:
            self.assertIn('foo', err.args)


class SkipIfBugOpen(TestCase):
    """Tests for :func:`robottelo.decorators.skip_if_bug_open`."""

    def test_raise_bug_type_error(self):
        with self.assertRaises(robozilla_decorators.BugTypeError):
            @decorators.skip_if_bug_open('notvalid', 123456)
            def foo():
                pass

    @mock.patch('robozilla.decorators.bz_bug_is_open')
    def test_skip_bugzilla_bug(self, bz_bug_is_open):
        bz_bug_is_open.side_effect = [True]

        @decorators.skip_if_bug_open('bugzilla', 123456)
        def foo():
            pass

        with self.assertRaises(SkipTest):
            foo()

    @mock.patch('robozilla.decorators.bz_bug_is_open')
    def test_not_skip_bugzilla_bug(self, bz_bug_is_open):
        bz_bug_is_open.side_effect = [False]

        @decorators.skip_if_bug_open('bugzilla', 123456)
        def foo():
            return 42

        self.assertEqual(foo(), 42)

    @mock.patch('robozilla.decorators.rm_bug_is_open')
    def test_skip_redmine_bug(self, rm_bug_is_open):
        rm_bug_is_open.side_effect = [True]

        @decorators.skip_if_bug_open('redmine', 123456)
        def foo():
            pass

        with self.assertRaises(SkipTest):
            foo()

    @mock.patch('robozilla.decorators.rm_bug_is_open')
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
