import logging

import pytest

from robottelo.config import settings
from robottelo.report_portal.portal import ReportPortal

LOGGER = logging.getLogger(__name__)


def _get_launch(rp):
    """Returns the latest launch of satellite"""
    _version = settings.server.version
    sat_version = f'{_version.base_version}.{_version.epoch}'
    launch = next(iter(rp.launches(sat_version=sat_version).values()))
    # Stop session based on RP Launch statistics and info
    pass_percent = round(
        100 * (int(launch.statistics['passed']) / int(launch.statistics['total']))
    )
    if launch.info['isProcessing']:
        pytest.skip(f'The latest launch of satellite version {sat_version} is not Finished yet.')
    if pass_percent < 80:
        pytest.skip(
            f'The latest Satellite launch has only {pass_percent}% tests passed. '
            'Which is lesser than the threshold of 80%. '
            'Examine the failures thoroughly and check for any major issue.'
        )
    return launch


def _get_failed_tests(launch, fail_args):
    """Returns failed test names from Report Portal Launch based on arguments"""
    tests = []
    if fail_args == ['all']:
        test_names = [*launch.tests(status='failed').keys()]
        tests.extend(test_names)
    else:
        for dtype in fail_args:
            test_names = [*launch.tests(defect_type=dtype).keys()]
            tests.extend(test_names)
    # Formating test names for 'member of items' operation
    tests = [str(test).replace('::', '.') for test in tests]
    return tests


def _get_test_collection(rp_failed_tests, items):
    """Returns the selected and deselected items"""
    # Select test item if its in failed tests else deselect
    LOGGER.debug('Selecting/Deselecting tests based on latest launch test results..')
    selected = []
    deselected = []
    for item in items:
        test_item = f"{item.location[0]}.{item.location[2]}"
        if test_item in rp_failed_tests:
            selected.append(item)
        else:
            deselected.append(item)
    return selected, deselected


def pytest_addoption(parser):
    """Add options for pytest to collect only failed tests"""
    help_script = '''
        Collects only failed tests in Report Portal to run only failed tests.

        Usage: --only-failed [options]

        Options: [ specific_defect_type | comma_sparated_list_of defect_types ]

        Defect_types:
        product_bug: Rerun failed tests marked with product_bug on RP
        rhel_bug: Rerun failed tests marked with rhel_bug on RP
        satellite_bug: Rerun failed tests marked with rhel_bug on RP
        automation_bug': Rerun failed tests marked with automation_bug on RP
        robottelo_bug': Rerun failed tests marked with robottelo_bug on RP
        nailgun_bug': Rerun failed tests marked with nailgun_bug on RP
        airgun_bug': Rerun failed tests marked with airgun_bug on RP
        system_issue': Rerun failed tests marked with system_issue on RP
        saucelabs_issue': Rerun failed tests marked with saucelabs_issue on RP
        to_investigate': Rerun failed tests marked with to_investigate on RP
        no_defect': Rerun failed tests marked with no_defect on RP
        '''
    parser.addoption("--only-failed", const='all', nargs='?', help=help_script)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items, config):
    """
    Collects tests based on pytest option to select tests marked as failed on Report Portal
    """
    fail_args = config.getvalue('only_failed')
    if not fail_args:
        return
    rp = ReportPortal()
    fail_args = fail_args.split(',') if ',' in fail_args else [fail_args]
    allowed_args = [*rp.defect_types.keys()]
    if not fail_args == ['all']:
        if not set(fail_args).issubset(set(allowed_args)):
            pytest.skip(
                f'Incorrect values to pytest option \'--only-failed\' are provided'
                f'\'{fail_args}\' but should be one/mix of {allowed_args}'
            )
    launch = _get_launch(rp)
    rp_tests = _get_failed_tests(launch, fail_args)
    selected, deselected = _get_test_collection(rp_tests, items)
    LOGGER.debug(
        f'Selected {len(selected)} failed and deselected {len(deselected)} passed tests '
        f'based on latest launch test results.'
    )
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
