from collections import defaultdict
import os

import pytest

from robottelo.config import settings
from robottelo.constants import JIRA_TESTS_FAILED_LABEL, JIRA_TESTS_PASSED_LABEL
from robottelo.logging import logger
from robottelo.utils import parse_comma_separated_list
from robottelo.utils.issue_handlers.jira import add_comment_on_jira, get_single_jira


def pytest_addoption(parser):
    """Add --jira-comments option to report test results on the Jira issue."""
    help_comment = (
        'Report/Comment test results on Jira issues.\n'
        'Results for tests marked with "Verifies" or "BlockedBy" doc fields will be commented on the corresponding Jira issues. '
        'This behaviour can be overriden by providing a comma separated list of jira issue ids.\n'
        'Note: To prevent accidental use, users must set ENABLE_COMMENT to true in the jira.yaml configuration file.'
    )
    parser.addoption(
        '--jira-comments',
        type=parse_comma_separated_list,
        nargs='?',
        const=True,
        default=False,
        help=help_comment,
    )


def pytest_configure(config):
    """Register jira_comments markers to avoid warnings."""
    config.addinivalue_line('markers', 'jira_comments: Add test result comment on Jira issue.')
    pytest.jira_comments = config.getoption('jira_comments')


def update_issue_to_tests_map(item, issues, test_result):
    """If the test has Verifies or BlockedBy doc field,
    an issue to tests mapping will be added/updated in config.issue_to_tests_map
    for each test run with outcome of the test.
    """
    for issue in issues:
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
    verifies_issues = verifies_marker.args[0] if verifies_marker else []
    blocked_by_issues = blocked_by_marker.args[0] if blocked_by_marker else []
    # Override jira issues to report/comment on.
    if isinstance(enable_jira_comments, list):
        verifies_issues = enable_jira_comments
        blocked_by_issues = []
    if (
        settings.jira.enable_comment
        and enable_jira_comments
        and (verifies_issues or blocked_by_issues)
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
            update_issue_to_tests_map(item, verifies_issues, test_result)
            # Update issue_to_tests_map for BlockedBy testimony marker
            update_issue_to_tests_map(item, blocked_by_issues, test_result)


def escape_special_characters(text):
    special_chars = '[]'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def pytest_sessionfinish(session, exitstatus):
    """Add test result comment to related Jira issues."""
    if hasattr(session.config, 'issue_to_tests_map'):
        user = os.environ.get('USER')
        build_url = os.environ.get('BUILD_URL')
        for issue in session.config.issue_to_tests_map:
            # Sort test result based on the outcome.
            session.config.issue_to_tests_map[issue].sort(key=lambda x: x['outcome'])
            all_tests_passed = True
            comment_body = (
                f'This is an automated comment from job/user: {build_url if build_url else user} for a Robottelo test run.\n'
                f'Satellite/Capsule: {settings.server.version.release} Snap: {settings.server.version.snap} \n'
                f'Result for tests linked with issue: {issue} \n'
            )
            for item in session.config.issue_to_tests_map[issue]:
                color_code = '{color:green}'
                if item['outcome'] == 'failed':
                    all_tests_passed = False
                    color_code = '{color:red}'
                # Color code test outcome
                color_coded_result = f'{color_code}{item["outcome"]}{{color}}'
                # Escape special characters in the node_id.
                escaped_node_id = escape_special_characters(item['nodeid'])
                comment_body += f'{escaped_node_id} : {color_coded_result} \n'
            try:
                labels = (
                    [{'add': JIRA_TESTS_PASSED_LABEL}, {'remove': JIRA_TESTS_FAILED_LABEL}]
                    if all_tests_passed
                    else [{'add': JIRA_TESTS_FAILED_LABEL}, {'remove': JIRA_TESTS_PASSED_LABEL}]
                )
                data = get_single_jira(issue)
                # Initially set a Pass/Fail label based on the test result
                # If the state changes add a comment
                # If the state is already failing, and test is failing, still add a comment
                # If the state is already passing, and the test passes, don’t add a comment
                if (data['status'] in settings.jira.issue_status) and (
                    not all_tests_passed or JIRA_TESTS_PASSED_LABEL not in data['labels']
                ):
                    add_comment_on_jira(issue, comment_body, labels=labels)
                else:
                    logger.warning(
                        f'Jira comments are currently disabled for {issue} issue. '
                        f'It could be because jira is in {data["status"]} state or that there are no failing tests. \n'
                        'Please update issue_status in jira.conf to override this behaviour.'
                    )
            except Exception as e:
                # Handle any errors in adding comments to Jira
                logger.warning(f'Failed to add comment to Jira issue {issue}: {e}')
