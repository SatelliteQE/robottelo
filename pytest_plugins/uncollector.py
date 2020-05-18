import logging

import pytest

from robottelo.config import settings
from robottelo.report_portal.portal import ReportPortal

LOGGER = logging.getLogger(__name__)


class LaunchError(Exception):
    """To be raised in case of skipping the session due to Launch issues/info"""

    pass


def _get_failed_tests(launch, fail_args):
    """Returns failed test names from Report Portal Launch based on arguments"""
    test_args = (
        [dict(status='failed')]
        if fail_args == ['all']
        else [dict(defect_type=dtype) for dtype in fail_args]
    )
    tests = []
    for t_args in test_args:
        tests.extend([*launch.tests(**t_args).keys()])
    # Formating test names for 'member of pytest test items' operation
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
    help_script = f'''
        Collects only failed tests in Report Portal to run only failed tests.

        Usage: --only-failed [options]

        Options: [ specific_defect_type | comma_sparated_list_of defect_types ]

        Defect_types:
            Collect failed tests marked with defect types: {[*ReportPortal.defect_types.keys()]}
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
    # Stop Session based on Arguments to pytest
    if not fail_args == ['all']:
        if not set(fail_args).issubset(set(allowed_args)):
            raise pytest.UsageError(
                f'Incorrect values to pytest option \'--only-failed\' are provided as '
                f'{fail_args} but should be none/one/mix of {allowed_args}'
            )
    # Fetch the latest launch
    version = settings.server.version
    sat_version = f'{version.base_version}.{version.epoch}'
    launch = next(iter(rp.launches(sat_version=sat_version).values()))
    # Stop session based on RP Launch statistics and info
    if launch.info['isProcessing']:
        raise LaunchError(f'The launch of satellite version {sat_version} is not Finished yet')
    fail_percent = round(
        (int(launch.statistics['failed']) / int(launch.statistics['total']) * 100)
    )
    if fail_percent > 20:
        raise LaunchError(
            f'The latest launch of Satellite verson {sat_version} has {fail_percent}% tests '
            'failed. Which is higher than the threshold of 20%. '
            'Examine the failures thoroughly and check for any major issue.'
        )
    rp_tests = _get_failed_tests(launch, fail_args)
    selected, deselected = _get_test_collection(rp_tests, items)
    LOGGER.debug(
        f'Selected {len(selected)} failed and deselected {len(deselected)} passed tests '
        f'based on latest launch test results.'
    )
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
