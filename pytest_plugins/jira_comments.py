from collections import defaultdict
import os

import pytest

from robottelo.config import settings
from robottelo.logging import logger
from robottelo.utils.issue_handlers.jira import add_comment_on_jira


def pytest_addoption(parser):
    """Add --jira-comments option to report test results on the Jira issue."""
    help_comment = (
        'Report/Comment test results on Jira issues. '
        'Test results marked with "Verifies" or "BlockedBy" doc fields will be commented on the corresponding Jira issues. '
        'Note: To prevent accidental use, users must set ENABLE_COMMENT to true in the jira.yaml configuration file.'
    )
    parser.addoption(
        '--jira-comments',
        action='store_true',
        default=False,
        help=help_comment,
    )


def pytest_configure(config):
    """Register jira_comments markers to avoid warnings."""
    config.addinivalue_line('markers', 'jira_comments: Add test result comment on Jira issue.')
    pytest.jira_comments = config.getoption('jira_comments')


def update_issue_to_tests_map(item, marker, test_result):
    """If the test has Verifies or BlockedBy doc field,
    an issue to tests mapping will be added/updated in config.issue_to_tests_map
    for each test run with outcome of the test.
    """
    if marker:
        for issue in marker.args[0]:
            item.config.issue_to_tests_map[issue].append(
                {'nodeid': item.nodeid, 'outcome': test_result}
            )


@pytest.hookimpl(trylast=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Create jira issue to test result mapping. Used for commenting result on Jira."""
    outcome = yield
    verifies_marker = item.get_closest_marker('verifies_issues')
    blocked_by_marker = item.get_closest_marker('blocked_by')
    enable_jira_comments = item.config.getoption('jira_comments')
    if (
        settings.jira.enable_comment
        and enable_jira_comments
        and (verifies_marker or blocked_by_marker)
    ):
        report = outcome.get_result()
        if report.when == 'teardown':
            test_result = (
                'passed'
                if (
                    item.report_setup.passed
                    and item.report_call.passed
                    and report.outcome == 'passed'
                )
                else 'failed'
            )
            if not hasattr(item.config, 'issue_to_tests_map'):
                item.config.issue_to_tests_map = defaultdict(list)
            # Update issue_to_tests_map for Verifies testimony marker
            update_issue_to_tests_map(item, verifies_marker, test_result)
            # Update issue_to_tests_map for BlockedBy testimony marker
            update_issue_to_tests_map(item, blocked_by_marker, test_result)


def pytest_sessionfinish(session, exitstatus):
    """Add test result comment to related Jira issues."""
    if hasattr(session.config, 'issue_to_tests_map'):
        user = os.environ.get('USER')
        build_url = os.environ.get('BUILD_URL')
        for issue in session.config.issue_to_tests_map:
            comment_body = (
                f'This is an automated comment from job/user: {build_url if build_url else user} for a Robottelo test run.\n'
                f'Satellite/Capsule: {settings.server.version.release} Snap: {settings.server.version.snap} \n'
                f'Result for tests linked with issue: {issue} \n'
            )
            for item in session.config.issue_to_tests_map[issue]:
                comment_body += f'{item["nodeid"]} : {item["outcome"]} \n'
            try:
                add_comment_on_jira(issue, comment_body)
            except Exception as e:
                # Handle any errors in adding comments to Jira
                logger.warning(f'Failed to add comment to Jira issue {issue}: {e}')
