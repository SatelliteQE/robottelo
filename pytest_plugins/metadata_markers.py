import datetime
import inspect
import re

import pytest

from robottelo.config import settings
from robottelo.hosts import get_sat_rhel_version
from robottelo.logging import collection_logger as logger
from robottelo.utils.issue_handlers.jira import are_any_jira_open

FMT_XUNIT_TIME = '%Y-%m-%dT%H:%M:%S'
IMPORTANCE_LEVELS = []
selected = []
deselected = []


def parse_comma_separated_list(option_value):
    if isinstance(option_value, str):
        if option_value.lower() == 'true':
            return True
        if option_value.lower() == 'false':
            return False
        return [item.strip() for item in option_value.split(',')]
    return None


def pytest_addoption(parser):
    """Add CLI options related to Testimony token based mark collection"""
    parser.addoption(
        '--importance',
        help='Comma separated list of importance levels to include in test collection',
    )
    parser.addoption(
        '--component',
        help='Comma separated list of component names to include in test collection',
    )
    parser.addoption(
        '--team',
        help='Comma separated list of teams to include in test collection',
    )
    parser.addoption(
        '--blocked-by',
        type=parse_comma_separated_list,
        nargs='?',
        const=True,
        default=True,
        help='Comma separated list of Jiras to collect tests matching BlockedBy testimony marker. '
        'If no issue is provided all the tests with BlockedBy testimony marker will be processed '
        'and deselected if any issue is open.',
    )
    parser.addoption(
        '--verifies-issues',
        type=parse_comma_separated_list,
        nargs='?',
        const=True,
        default=False,
        help='Comma separated list of Jiras to collect tests matching Verifies testimony marker. '
        'If no issue is provided all the tests with Verifies testimony marker will be selected.',
    )


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    for marker in [
        'importance: CaseImportance testimony token, use --importance to filter',
        'component: Component testimony token, use --component to filter',
        'team: Team testimony token, use --team to filter',
        'blocked_by: BlockedBy testimony token, use --blocked-by to filter',
        'verifies_issues: Verifies testimony token, use --verifies_issues to filter',
    ]:
        config.addinivalue_line("markers", marker)


component_regex = re.compile(
    # To match :CaseComponent: FooBar
    r'\s*:CaseComponent:\s*(?P<component>\S*)',
    re.IGNORECASE,
)

importance_regex = re.compile(
    # To match :CaseImportance: Critical
    r'\s*:CaseImportance:\s*(?P<importance>\S*)',
    re.IGNORECASE,
)

team_regex = re.compile(
    # To match :Team: Rocket
    r'\s*:Team:\s*(?P<team>\S*)',
    re.IGNORECASE,
)

blocked_by_regex = re.compile(
    # To match :BlockedBy: SAT-32932
    r'\s*:BlockedBy:\s*(?P<blocked_by>.*\S*)',
    re.IGNORECASE,
)

verifies_regex = re.compile(
    # To match :Verifies: SAT-32932
    r'\s*:Verifies:\s*(?P<verifies>.*\S*)',
    re.IGNORECASE,
)


def handle_verification_issues(item, verifies_marker, verifies_issues):
    """Handles the logic for deselecting tests based on Verifies testimony token
    and --verifies-issues pytest option.
    """
    if verifies_issues:
        if not verifies_marker:
            log_and_deselect(item, '--verifies-issues')
            return False
        if isinstance(verifies_issues, list):
            verifies_args = verifies_marker.args[0]
            if all(issue not in verifies_issues for issue in verifies_args):
                log_and_deselect(item, '--verifies-issues')
            return False
    return True


def handle_blocked_by(item, blocked_by_marker, blocked_by):
    """Handles the logic for deselecting tests based on BlockedBy testimony token
    and --blocked-by pytest option.
    """
    if isinstance(blocked_by, list):
        if not blocked_by_marker:
            log_and_deselect(item, '--blocked-by')
            return False
        if all(issue not in blocked_by for issue in blocked_by_marker.args[0]):
            log_and_deselect(item, '--blocked-by')
            return False
    elif isinstance(blocked_by, bool) and blocked_by_marker:
        if blocked_by and are_any_jira_open(blocked_by_marker.args[0]):
            log_and_deselect(item, '--blocked-by')
            return False
    return True


def log_and_deselect(item, option):
    logger.debug(f'Deselected test {item.nodeid} due to "{option}" pytest option.')
    deselected.append(item)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items, config):
    """Add markers and user_properties for testimony token metadata

    user_properties is used by the junit plugin, and thus by many test report systems
    Handle test function/class/module/session scope metadata coming from test docblocks
    Apply user_properties, ibutsu metadata, and pytest markers

    Markers for metadata use the testimony token name as the mark name
    The value of the token for the mark is the first mark arg

    Control test collection for custom options related to testimony metadata

    """
    # get RHEL version of the satellite
    rhel_version = get_sat_rhel_version().base_version
    sat_version = settings.server.version.get('release')
    snap_version = settings.server.version.get('snap', '')

    # split the option string and handle no option, single option, multiple
    # config.getoption(default) doesn't work like you think it does, hence or ''
    importance = [i for i in (config.getoption('importance') or '').split(',') if i != '']
    component = [c for c in (config.getoption('component') or '').split(',') if c != '']
    team = [a.lower() for a in (config.getoption('team') or '').split(',') if a != '']
    verifies_issues = config.getoption('verifies_issues')
    blocked_by = config.getoption('blocked_by')
    logger.info('Processing test items to add testimony token markers')
    for item in items:
        item.user_properties.append(
            ("start_time", datetime.datetime.utcnow().strftime(FMT_XUNIT_TIME))
        )
        if item.nodeid.startswith('tests/robottelo/') and 'test_junit' not in item.nodeid:
            # Unit test, no testimony markers
            continue

        # apply the marks for importance, component, and team
        # Find matches from docstrings starting at smallest scope
        item_docstrings = [
            d
            for d in map(inspect.getdoc, (item.function, getattr(item, 'cls', None), item.module))
            if d is not None
        ]
        blocked_by_marks_to_add = []
        verifies_marks_to_add = []
        for docstring in item_docstrings:
            item_mark_names = [m.name for m in item.iter_markers()]
            # Add marker starting at smallest docstring scope
            # only add the mark if it hasn't already been applied at a lower scope
            doc_component = component_regex.findall(docstring)
            if doc_component and 'component' not in item_mark_names:
                item.add_marker(pytest.mark.component(doc_component[0]))
            doc_importance = importance_regex.findall(docstring)
            if doc_importance and 'importance' not in item_mark_names:
                item.add_marker(pytest.mark.importance(doc_importance[0]))
            doc_team = team_regex.findall(docstring)
            if doc_team and 'team' not in item_mark_names:
                item.add_marker(pytest.mark.team(doc_team[0].lower()))
            doc_verifies = verifies_regex.findall(docstring)
            if doc_verifies and 'verifies_issues' not in item_mark_names:
                verifies_marks_to_add.extend(str(b.strip()) for b in doc_verifies[-1].split(','))
            doc_blocked_by = blocked_by_regex.findall(docstring)
            if doc_blocked_by and 'blocked_by' not in item_mark_names:
                blocked_by_marks_to_add.extend(
                    str(b.strip()) for b in doc_blocked_by[-1].split(',')
                )
        if blocked_by_marks_to_add:
            item.add_marker(pytest.mark.blocked_by(blocked_by_marks_to_add))
        if verifies_marks_to_add:
            item.add_marker(pytest.mark.verifies_issues(verifies_marks_to_add))

        # add markers as user_properties so they are recorded in XML properties of the report
        # pytest-ibutsu will include user_properties dict in testresult metadata
        markers_prop_data = []
        exclude_markers = ['parametrize', 'skipif', 'usefixtures', 'skip_if_not_set']
        for marker in item.iter_markers():
            proprty = marker.name
            if proprty in exclude_markers:
                continue
            if marker_val := next(iter(marker.args), None):
                proprty = '='.join([proprty, str(marker_val)])
            markers_prop_data.append(proprty)
            # Adding independent marker as a property
            item.user_properties.append((marker.name, marker_val))
        # Adding all markers as a single property
        item.user_properties.append(("markers", ", ".join(markers_prop_data)))

        # Version specific user properties
        item.user_properties.append(("BaseOS", rhel_version))
        item.user_properties.append(("SatelliteVersion", sat_version))
        item.user_properties.append(("SnapVersion", snap_version))

        # exit early if no filters were passed
        if importance or component or team:
            # Filter test collection based on CLI options for filtering
            # filters should be applied together
            # such that --component Repository --importance Critical --team rocket
            # only collects tests which have all three of these marks

            # https://github.com/pytest-dev/pytest/issues/1373  Will make this way easier
            # testimony requires both importance and component, this will blow up if its forgotten
            importance_marker = item.get_closest_marker('importance').args[0]
            if importance and importance_marker not in importance:
                logger.debug(
                    f'Deselected test {item.nodeid} due to "--importance {importance}",'
                    f'test has importance mark: {importance_marker}'
                )
                deselected.append(item)
                continue
            component_marker = item.get_closest_marker('component').args[0]
            if component and component_marker not in component:
                logger.debug(
                    f'Deselected test {item.nodeid} due to "--component {component}",'
                    f'test has component mark: {component_marker}'
                )
                deselected.append(item)
                continue
            team_marker = item.get_closest_marker('team').args[0]
            if team and team_marker not in team:
                logger.debug(
                    f'Deselected test {item.nodeid} due to "--team {team}",'
                    f'test has team mark: {team_marker}'
                )
                deselected.append(item)
                continue

        if verifies_issues or blocked_by:
            # Filter tests based on --verifies-issues and --blocked-by pytest options
            # and Verifies and BlockedBy testimony tokens.
            verifies_marker = item.get_closest_marker('verifies_issues', False)
            blocked_by_marker = item.get_closest_marker('blocked_by', False)
            if not handle_verification_issues(item, verifies_marker, verifies_issues):
                continue
            if not handle_blocked_by(item, blocked_by_marker, blocked_by):
                continue
        selected.append(item)

    # selected will be empty if no filter option was passed, defaulting to full items list
    items[:] = selected if deselected else items
    config.hook.pytest_deselected(items=deselected)
