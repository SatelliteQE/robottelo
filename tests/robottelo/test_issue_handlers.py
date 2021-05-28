import os
import subprocess
import sys
from collections import defaultdict

import pytest
from packaging.version import Version

from pytest_plugins.issue_handlers import DEFAULT_BZ_CACHE_FILE
from robottelo.constants import CLOSED_STATUSES
from robottelo.constants import OPEN_STATUSES
from robottelo.constants import WONTFIX_RESOLUTIONS
from robottelo.utils.issue_handlers import add_workaround
from robottelo.utils.issue_handlers import is_open
from robottelo.utils.issue_handlers import should_deselect


class TestBugzillaIssueHandler:
    @pytest.fixture(autouse=True)
    def set_env_version(self, mocker):
        """Mock the return of get_sat_version to avoid ssh attempts"""
        mocker.patch('robottelo.host_info.get_sat_version', return_value=Version('6.6'))
        mocker.patch(
            'robottelo.utils.issue_handlers.bugzilla.get_sat_version', return_value=Version('6.6')
        )

    def test_bz_is_open_pre_processed(self):
        """Assert a pre-processed BZ is considered open"""
        data = {"is_open": True}
        assert is_open("BZ:123456", data)

    def test_bz_is_not_open_pre_processed(self):
        """Assert a pre-processed BZ is considered not open"""
        data = {"is_open": False}
        assert not is_open("BZ:123456", data)

    def test_bz_is_deselected_pre_processed(self):
        """Assert a pre-processed BZ is considered deselected"""
        data = {"is_deselected": True}
        assert should_deselect("BZ:123456", data)

    def test_bz_is_not_deselected_pre_processed(self):
        """Assert a pre-processed BZ is considered not deselected"""
        data = {"is_deselected": False}
        assert not should_deselect("BZ:123456", data)

    @pytest.mark.parametrize('status', OPEN_STATUSES)
    def test_bz_is_open_by_status(self, status):
        """Assert status in NEW, ASSIGNED, POST, MODIFIED is open"""
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": status,
                "resolution": "",
                "target_milestone": "Unspecified",
                "flags": [],
            },
        )

    @pytest.mark.parametrize('resolution', WONTFIX_RESOLUTIONS)
    def test_bz_is_open_by_resolution(self, resolution):
        """Assert a closed BZ in WONTFIX resolution is considered open"""
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": resolution,
                "target_milestone": "Unspecified",
                "flags": [],
            },
        )

    def test_bz_is_open_if_server_version_is_lower(self):
        """Assert bug is considered open if TM is set for a future version
        and there are no clones backporting the solution to server version.
        """
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": "ERRATA",
                "target_milestone": "7.0.1",
                "flags": [],
                "clones": [],
            },
        )

    @pytest.mark.parametrize('status', CLOSED_STATUSES)
    def test_bz_is_not_open_if_server_version_is_higher_or_equal_tm(self, status):
        """Assert bug is considered not open if closed status and
        TM is higher or matches the running server version.
        """
        assert not is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": status,
                "resolution": "",
                "target_milestone": "6.6.1",
                "flags": [],
                "clones": [],
            },
        )

    def test_bz_is_open_if_server_version_is_lower_using_flags(self):
        """Assert bug is considered open if flag version is set for a future
        version and there are no clones backporting the solution.
        """
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": "ERRATA",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-7.0.1"}],
                "clones": [],
            },
        )

    @pytest.mark.parametrize('status', CLOSED_STATUSES)
    def test_bz_is_not_open_if_server_version_is_higher_or_equal_flags(self, status):
        """Assert bug is considered not open if closed status and
        min(flags) version is higher or matches the running server version.
        """
        assert not is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": status,
                "resolution": "",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.6.0"}],
                "clones": [],
            },
        )

    def test_bz_is_open_using_dupe_data_higher_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA but on a future version, no clones for
        backport the solution."""
        assert is_open(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "flags": [],
                "dupe_data": {
                    "id": 999999,
                    "status": "CLOSED",
                    "resolution": "ERRATA",
                    "target_milestone": "Unspecified",
                    "flags": [{"status": "+", "name": "sat-6.7.0"}],
                },
            },
        )

    def test_bz_is_not_open_using_dupe_data_lower_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA in a previous version."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "ERRATA",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.3.z"}],
            },
        }
        assert not is_open("BZ:123456", data)

    def test_bz_is_open_using_dupe_of_dupe_data_higher_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA but on a future version, no clones for
        backport the solution."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.7.z"}],
                "dupe_data": {
                    "id": 888888,
                    "status": "CLOSED",
                    "resolution": "ERRATA",
                    "target_milestone": "Unspecified",
                    "flags": [{"status": "+", "name": "sat-6.7.z"}],
                },
            },
        }
        assert is_open("BZ:123456", data)

    def test_bz_is_not_open_using_dupe_of_dupe_data_lower_version(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA in a previous version."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "flags": [{"status": "+", "name": "sat-6.3.z"}],
                "dupe_data": {
                    "id": 888888,
                    "status": "CLOSED",
                    "resolution": "ERRATA",
                    "target_milestone": "Unspecified",
                    "flags": [{"status": "+", "name": "sat-6.3.z"}],
                },
            },
        }
        assert not is_open("BZ:123456", data)

    def test_bz_is_open_using_dupe_of_dupe_data_by_status(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA but on a future version, no clones for
        backport the solution."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "flags": [],
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "dupe_data": {
                    "id": 888888,
                    "status": "NEW",
                    "resolution": "",
                    "target_milestone": "Unspecified",
                },
            },
        }
        assert is_open("BZ:123456", data)

    def test_bz_is_not_open_using_dupe_of_dupe_data_by_status(self):
        """Assert that if BZ has a dupe, the dupe data is considered.
        The dupe is CLOSED/ERRATA in a previous version."""
        data = {
            "id": 123456,
            "status": "CLOSED",
            "resolution": "DUPLICATE",
            "target_milestone": "Unspecified",
            "dupe_data": {
                "id": 999999,
                "status": "CLOSED",
                "resolution": "DUPLICATE",
                "target_milestone": "Unspecified",
                "dupe_data": {
                    "id": 999999,
                    "status": "CLOSED",
                    "resolution": "ERRATA",
                    "target_milestone": "Unspecified",
                    "flags": [],
                },
            },
        }
        assert not is_open("BZ:123456", data)

    @pytest.mark.parametrize('resolution', WONTFIX_RESOLUTIONS)
    def test_bzshould_deselect(self, resolution):
        """Ensure a BZ in resolution WONTFIX,CANTIFX,DEFERRED is deselected"""
        assert should_deselect(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": resolution,
                "target_milestone": "Unspecified",
                "flags": [],
            },
        )

    @pytest.mark.parametrize('resolution', WONTFIX_RESOLUTIONS)
    def test_bzshould_deselect_if_dupe_is_wontfix(self, resolution):
        """Ensure a BZ in resolution WONTFIX,CANTIFX,DEFERRED is deselected"""
        assert should_deselect(
            "BZ:123456",
            {
                "id": 123456,
                "status": "CLOSED",
                "resolution": 'DUPLICATE',
                "target_milestone": "Unspecified",
                "flags": [],
                "dupe_data": {
                    "id": 999999,
                    "status": "CLOSED",
                    "resolution": resolution,
                    "target_milestone": "Unspecified",
                    "flags": [],
                },
            },
        )

    def test_bz_should_not_deselect(self):
        """Ensure a BZ is not deselected if not in WONTFIX_RESOLUTIONS."""
        for status in OPEN_STATUSES:
            assert not should_deselect(
                "BZ:123456",
                {
                    "id": 123456,
                    "status": status,
                    "resolution": "",
                    "target_milestone": "Unspecified",
                    "flags": [],
                },
            )

        for status in CLOSED_STATUSES:
            for resolution in ('ERRATA', 'CURRENT_RELEASE', 'WORKSFORME'):
                assert not should_deselect(
                    "BZ:123456",
                    {
                        "id": 123456,
                        "status": status,
                        "resolution": resolution,
                        "target_milestone": "Unspecified",
                        "flags": [],
                    },
                )

    @pytest.mark.parametrize('issue', ["BZ123456", "XX:123456", "KK:89456", "123456", 999999])
    def test_invalid_handler(self, issue):
        """Assert is_open w/ invalid handlers raise AttributeError"""
        with pytest.raises(AttributeError):
            issue_deselect = should_deselect(issue)
            is_open(issue)
        assert issue_deselect is None

    def test_bz_cache(self, request):
        """Assert basic behavior of the --bz-cache pytest option"""

        if os.path.exists(DEFAULT_BZ_CACHE_FILE):
            pytest.skip('BZ cache file exists, skipping')

        @request.addfinalizer
        def _remove_file():
            if os.path.exists(DEFAULT_BZ_CACHE_FILE):
                os.remove(DEFAULT_BZ_CACHE_FILE)

        try:

            subprocess.run(
                [sys.executable, '-m', 'pytest', '--collect-only', 'tests/robottelo'], check=True
            )
        except subprocess.CalledProcessError as exc:
            pytest.fail(
                'Process error running pytest collect:\n'
                f'Process output: {exc.output}\n'
                f'Process stderr: {exc.stderr}\n'
                f'Process RC: {exc.returncode}\n'
            )
        assert not os.path.exists(DEFAULT_BZ_CACHE_FILE)

        try:
            subprocess.run(
                [
                    sys.executable,
                    '-m',
                    'pytest',
                    '--bz-cache',
                    '--collect-only',
                    'tests/robottelo',
                ],
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            pytest.fail(
                'Process error running pytest collect:\n'
                f'Process output: {exc.output}\n'
                f'Process stderr: {exc.stderr}\n'
                f'Process RC: {exc.returncode}\n'
            )
        assert os.path.exists(DEFAULT_BZ_CACHE_FILE)


def test_add_workaround():
    """Assert helper function adds current items to given data"""
    data = defaultdict(lambda: {"data": {}, "used_in": []})
    matches = [('BZ', '123456'), ('BZ', '789456')]

    add_workaround(data, matches, 'test', foo='bar')

    add_workaround(
        data, matches, 'test', validation=lambda *a, **k: False, zaz='traz'  # Should not be added
    )

    for match in matches:
        issue = f"{match[0]}:{match[1]}"
        used_in = data[issue.strip()]['used_in']
        assert {'usage': 'test', 'foo': 'bar'} in used_in
        assert {'usage': 'test', 'zaz': 'traz'} not in used_in
