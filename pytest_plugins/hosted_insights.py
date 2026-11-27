"""Keep synthetic hosted Insights ingestion out of the daily production upload peak."""

from datetime import UTC, datetime

import pytest

from robottelo.config import settings
from robottelo.logging import logger


def pytest_addoption(parser):
    parser.addoption(
        '--allow-hosted-insights-during-peak',
        action='store_true',
        default=False,
        help='Run hosted_insights tests during the configured UTC upload exclusion window.',
    )


def pytest_configure(config):
    cloud = settings.rh_cloud
    for name, default in (('skip_peak_uploads', True), ('allow_peak_uploads', False)):
        if not isinstance(cloud.get(name, default), bool):
            raise pytest.UsageError(f'RH_CLOUD.{name.upper()} must be a boolean')
    window = []
    for name in ('peak_upload_start_utc', 'peak_upload_end_utc'):
        value = cloud.get(name, '23:00' if name == 'peak_upload_start_utc' else '10:30')
        try:
            parsed = datetime.strptime(value, '%H:%M').time()
            if parsed.strftime('%H:%M') != value:
                raise ValueError()
        except (TypeError, ValueError):
            raise pytest.UsageError(
                f'RH_CLOUD.{name.upper()} must be a UTC time in HH:MM format'
            ) from None
        window.append(parsed)
    if window[0] == window[1]:
        raise pytest.UsageError('Hosted Insights peak window start and end must differ')
    config._hosted_insights_peak_window = tuple(window)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    # Run before pytest sets up fixtures. Do not resolve a Satellite just to decide
    # whether a test is eligible, or make collection depend on worker wall clocks.
    if item.get_closest_marker('hosted_insights') is None:
        return
    if not settings.rh_cloud.get('skip_peak_uploads', True):
        return
    start, end = item.config._hosted_insights_peak_window
    now = datetime.now(UTC).time()
    during_peak = start <= now < end if start < end else now >= start or now < end
    if not during_peak:
        return
    window = f'{start:%H:%M}–{end:%H:%M} UTC'
    if item.config.getoption('allow_hosted_insights_during_peak') or settings.rh_cloud.get(
        'allow_peak_uploads', False
    ):
        logger.warning('Overriding hosted Insights upload exclusion (%s): %s', window, item.nodeid)
        return
    pytest.skip(
        f'Hosted Insights uploads excluded during {window}; '
        'use --allow-hosted-insights-during-peak or '
        'ROBOTTELO_RH_CLOUD__ALLOW_PEAK_UPLOADS=true for an intentional run'
    )
