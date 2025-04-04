from urllib.parse import urlparse

from box import Box
from broker.hosts import Host
import pytest

from robottelo.config import settings
from robottelo.logging import logger

test_results = {}
test_directories = [
    'tests/foreman/destructive',
    'tests/foreman/ui',
    'tests/foreman/sanity',
    'tests/foreman/virtwho',
]


def _clean_video(session_id, test):
    if settings.ui.record_video:
        logger.info(f"cleaning up video files for session: {session_id} and test: {test}")

        if settings.ui.grid_url and session_id:
            grid = urlparse(url=settings.ui.grid_url)
            infra_grid = Host(hostname=grid.hostname)
            infra_grid.execute(command=f'rm -rf /var/www/html/videos/{session_id}')
            logger.info(f"video cleanup for session {session_id} is complete")
        else:
            logger.warning("missing grid_url or session_id. unable to clean video files.")


def pytest_addoption(parser):
    """Custom pytest option to skip video cleanup on test success.
    Args:
        parser (object): The pytest command-line option parser.
    Options:
        --skip-video-cleanup: Skip video cleaning on test success (default: False).
    """
    parser.addoption(
        "--skip-video-cleanup",
        action="store_true",
        default=False,
        help="Skip video cleaning on test success",
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Custom pytest hook to capture test outcomes and perform video cleanup.
    Note:
        This hook captures test results during 'call' and performs video cleanup
        during 'teardown' if the test passed and the '--skip-video-cleanup' option is not set.
    """
    outcome = yield
    report = outcome.get_result()
    skip_video_cleanup = item.config.getoption("--skip-video-cleanup", False)

    if not skip_video_cleanup and any(directory in report.fspath for directory in test_directories):
        if report.when == "call":
            test_results[item.nodeid] = Box(
                {
                    'outcome': report.outcome,
                    'duration': report.duration,
                    'longrepr': str(report.longrepr),
                }
            )
        if report.when == "teardown" and item.nodeid in test_results:
            result_info = test_results[item.nodeid]
            if result_info.outcome == 'passed':
                report.user_properties = [
                    (key, value) for key, value in report.user_properties if key != 'video_url'
                ]
                session_id_tuple = next(
                    (t for t in report.user_properties if t[0] == 'session_id'), None
                )
                session_id = session_id_tuple[1] if session_id_tuple else None
                _clean_video(session_id, item.nodeid)
