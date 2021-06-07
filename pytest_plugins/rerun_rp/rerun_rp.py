import pytest

from robottelo.config import settings
from robottelo.hosts import get_sat_version
from robottelo.logging import logger
from robottelo.report_portal.portal import ReportPortal


class LaunchError(Exception):
    """To be raised in case of skipping the session due to Launch issues/info"""

    pass


def _validate_launch(launch):
    """Stops the pytest session based on RP Launch statistics and info"""
    fail_percent = round(
        int(launch['statistics']['executions'].get('failed', 0))
        / int(launch['statistics']['executions'].get('total'))
        * 100
    )
    fail_threshold = settings.report_portal.fail_threshold
    if fail_percent > fail_threshold:
        raise LaunchError(
            f'The reference launch {launch["name"]} (id: {launch["id"]}) has {fail_percent}% '
            f'of failed tests. It is higher than the threshold of {fail_threshold}%. '
            'Examine the failures thoroughly and check for any major issue.'
        )


def pytest_addoption(parser):
    """Add options for pytest to collect only failed/skipped and user tests"""
    help_text = f'''
        Collects tests from Report Portal to run only failed status tests.

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
        Uses given launch as a reference for parsing RP tests to be used with
        --only-failed, --only-skipped or --user

        Usage: --rp-reference-launch-uuid [value]

        Value: report_portal_launch_uuid
    '''
    parser.addoption("--rp-reference-launch-uuid", nargs='?', help=help_text)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items, config):
    """
    Collects and modifies test collection based on the pytest options to select the tests marked as
    failed/skipped and user-specific tests in Report Portal
    """
    rp_url = settings.report_portal.portal_url or config.getini('rp_endpoint')
    rp_uuid = config.getini('rp_uuid') or settings.report_portal.api_key
    # prefer dynaconf setting before ini config as pytest-reportportal plugin uses default value
    # for `rp_launch` if none is set there
    rp_launch_name = settings.report_portal.launch_name or config.getini('rp_launch')
    rp_project = config.getini('rp_project') or settings.report_portal.project
    fail_args = config.getoption('only_failed', False)
    skip_arg = config.getoption('only_skipped', False)
    user_arg = config.getoption('user', False)
    ref_launch_uuid = config.getoption('rp_reference_launch_uuid', None) or config.getoption(
        'rp_rerun_of', None
    )
    tests = []
    if not any([fail_args, skip_arg, user_arg]):
        return
    rp = ReportPortal(rp_url=rp_url, rp_api_key=rp_uuid, rp_project=rp_project)

    if ref_launch_uuid:
        logger.info(f'Fetching A reference Report Portal launch {ref_launch_uuid}')
        ref_launches = rp.get_launches(uuid=ref_launch_uuid)
        if not ref_launches:
            raise LaunchError(
                f'Provided reference launch {ref_launch_uuid} was not found or is not finished'
            )
    else:
        sat_release = get_sat_version().base_version
        sat_snap = settings.server.version.get('snap', '')
        if not all([sat_release, sat_snap, (len(sat_release.split('.')) == 3)]):
            raise pytest.UsageError(
                '--failed|skipped-only requires a reference launch id or'
                ' a full satellite version (x.y.z-a.b) to be provided.'
                f' sat_release: {sat_release}, sat_snap: {sat_snap} were provided instead'
            )
        sat_version = f'{sat_release}-{sat_snap}'
        logger.info(
            f'Fetching A reference Report Portal launch by Satellite version: {sat_version}'
        )

        ref_launches = rp.get_launches(name=rp_launch_name, sat_version=sat_version)
        if not ref_launches:
            raise LaunchError(
                f'No suitable Report portal launches for name: {rp_launch_name}'
                f' and version: {sat_version} found'
            )

    test_args = {}
    test_args.setdefault('status', list())
    if skip_arg:
        test_args['status'].append('SKIPPED')
    if fail_args:
        test_args['status'].append('FAILED')
        if not fail_args == 'all':
            defect_types = fail_args.split(',')
            allowed_args = [*rp.defect_types.keys()]
            if not set(defect_types).issubset(set(allowed_args)):
                raise pytest.UsageError(
                    'Incorrect values to pytest option \'--only-failed\' are provided as '
                    f'\'{fail_args}\'. It should be none/one/mix of {allowed_args}'
                )
            test_args['defect_types'] = defect_types
    if user_arg:
        test_args['user'] = user_arg
    test_args['paths'] = config.args
    for ref_launch in ref_launches:
        _validate_launch(ref_launch)
        tests.extend(rp.get_tests(launch=ref_launch, **test_args))
    # remove inapplicable tests from the current test collection
    deselected = [
        i
        for i in items
        if f'{i.location[0]}.{i.location[2]}'.replace('::', '.')
        not in [t['name'].replace('::', '.') for t in tests]
    ]
    selected = list(set(items) - set(deselected))
    logger.debug(
        f'Selected {len(selected)} and deselected {len(deselected)} tests based on latest/given-/ '
        'launch test results.'
    )
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
