import pytest

from robottelo.config import settings
from robottelo.logging import logger
from robottelo.report_portal.portal import ReportPortal


class LaunchError(Exception):
    """To be raised in case of skipping the session due to Launch issues/info"""

    pass


def _transform_rp_tests_to_pytest(tests):
    """Formating test names toc check 'member of pytest test items' operation

    :param list tests: The list of tests those name to be changed
    :return list: The transformed list of tests
    """
    tests = [str(test).replace('::', '.') for test in tests]
    return tests


def _get_tests(launch, **kwargs):
    """The helper function that actually connects to Report Portal and fetch tests of a launch

    :param rp.launch launch: The launch object from where the tests will be read
    :param dict kwargs: The params to `launch.tests` function
        i.e status, user, defect_types
    :return list: The list of test names retrieved from RP launch
    """
    tests = []
    if 'status' in kwargs:
        all_status = kwargs.pop('status')
        for status in all_status:
            if status == 'failed' and 'defect_types' in kwargs:
                defect_types = kwargs.pop('defect_types')
                for dtype in defect_types:
                    tests.extend(launch.tests(**kwargs, status=status, defect_type=dtype).keys())
            else:
                tests.extend(launch.tests(**kwargs, status=status).keys())
    else:
        tests.extend(launch.tests(**kwargs).keys())
    transformed_tests = _transform_rp_tests_to_pytest(tests)
    return transformed_tests


def _get_test_collection(selectable_tests, items):
    """Returns the selected and deselected items"""
    # Select test item if its in failed tests else deselect
    logger.debug('Selecting/Deselecting tests based on latest launch test results.')
    selected = []
    deselected = []
    for item in items:
        test_item = f"{item.location[0]}.{item.location[2]}"
        if test_item in selectable_tests:
            selected.append(item)
        else:
            deselected.append(item)
    return selected, deselected


def _validate_launch(launch, sat_version):
    """Stop session based on RP Launch statistics and info"""
    fail_percent = round(int(launch.statistics['failed']) / int(launch.statistics['total']) * 100)
    fail_threshold = settings.report_portal.fail_threshold
    if fail_percent > fail_threshold:
        raise LaunchError(
            f'The latest launch of Satellite verson {sat_version} has {fail_percent}% tests '
            f'failed. Which is higher than the threshold of {fail_threshold}%. '
            'Examine the failures thoroughly and check for any major issue.'
        )


def pytest_addoption(parser):
    """Add options for pytest to collect only failed/skipped and user tests"""
    help_text = f'''
        Collects tests in Report Portal to run only failed status tests.

        Usage: --only-failed [options]

        Options: [ specific_defect_type | comma_sparated_list_of defect_types ]

        Defect_types:
            Collect failed tests marked with defect types: {[*ReportPortal.defect_types.keys()]}
    '''
    parser.addoption("--only-failed", const='all', nargs='?', help=help_text)
    help_text = '''
        Collects only skipped tests in Report Portal to run only skipped tests.

        Usage: --only-skipped
    '''
    parser.addoption("--only-skipped", action='store_true', default=False, help=help_text)
    help_text = '''
        Collects user tests from report portal.

        Usage: --user [value]

        Value: [ Report_portal_username ]
    '''
    parser.addoption("--user", nargs='?', help=help_text)
    help_text = '''
        Rerun Upgrade launch tests instead of Regular Tier launch from Report Portal,

        Usage: --upgrades-rerun
    '''
    parser.addoption("--upgrades-rerun", action='store_true', default=False, help=help_text)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items, config):
    """
    Collects and modifies tests collection based on pytest options to select tests marked as
    failed/skipped and user specific tests in Report Portal
    """
    fail_args = config.getoption('only_failed', False)
    skip_arg = config.getoption('only_skipped', False)
    user_arg = config.getoption('user', False)
    upgrades_rerun = config.getoption('upgrades_rerun', False)
    if not any([fail_args, skip_arg, user_arg, upgrades_rerun]):
        return
    rp = ReportPortal()
    version = settings.server.version
    sat_version = f'{version.base_version}.{version.epoch}'
    logger.info(f'Fetching Report Portal launches for target Satellite version: {sat_version}')
    launch = next(
        iter(
            rp.launches(
                sat_version=sat_version, launch_type='upgrades' if upgrades_rerun else 'satellite6'
            ).values()
        )
    )
    _validate_launch(launch, sat_version)
    test_args = {}
    test_args.setdefault('status', list())
    if fail_args:
        test_args['status'].append('failed')
        if not fail_args == 'all':
            defect_types = fail_args.split(',') if ',' in fail_args else [fail_args]
            allowed_args = [*rp.defect_types.keys()]
            if not set(defect_types).issubset(set(allowed_args)):
                raise pytest.UsageError(
                    'Incorrect values to pytest option \'--only-failed\' are provided as '
                    f'\'{fail_args}\'. It should be none/one/mix of {allowed_args}'
                )
            test_args['defect_types'] = defect_types
    if skip_arg:
        test_args['status'].append('skipped')
    if user_arg:
        test_args['user'] = user_arg
    rp_tests = _get_tests(launch, **test_args)
    selected, deselected = _get_test_collection(rp_tests, items)
    logger.debug(
        f'Selected {len(selected)} and deselected {len(deselected)} tests based on latest '
        'launch test results.'
    )
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
