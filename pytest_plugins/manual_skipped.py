import pytest

from robottelo.logging import collection_logger as logger


def pytest_configure(config):
    """Register custom marker for stubbed test cases."""
    config.addinivalue_line('markers', 'stubbed: Tests that are not automated yet or manual only.')


def pytest_collection_modifyitems(session, config, items):
    """Remove/Include stubbed tests from collection based on CLI option"""
    opt_passed = config.getvalue('mark_manuals_passed')
    opt_skipped = config.getvalue('mark_manuals_skipped')
    # TODO turn this into a flag or a choice option, this logic is just silly.
    mark_skipped = opt_skipped and not opt_passed
    include_stubbed = config.getvalue('include_stubbed')
    selected = []
    deselected = []
    for item in items:
        stub_marked = item.get_closest_marker(name='stubbed')
        # The test case is stubbed, and --include-stubbed was passed, include in collection
        if stub_marked and include_stubbed:
            selected.append(item)
            # enforce skip/pass behavior by marking skip
            if mark_skipped:
                logger.debug(f'Marking collected stubbed test "{item.nodeid}" to skip')
                item.add_marker(marker=pytest.mark.skip(reason='This is a Manual test!'))
            continue

        # The test case is stubbed, but --include-stubbed was NOT passed, deselect the item
        if stub_marked and not include_stubbed:
            logger.debug(
                f'Deselecting stubbed test {item.nodeid}, '
                'use --include-stubbed to include in collection'
            )
            deselected.append(item)
            continue

        # Its a non-stubbed item, this hook doesn't apply
        selected.append(item)

    config.hook.pytest_deselected(items=deselected)
    items[:] = selected


def pytest_addoption(parser):
    """Add options to pytest to modify manual tests as skipped and control collection"""
    parser.addoption(
        '--include-stubbed',
        action='store_true',
        default=False,
        help='Include stubbed tests in collection, by default they are deselected',
    )
    parser.addoption(
        '--mark-manuals-skipped',
        action='store_true',
        default=True,
        help='Mark stubbed tests as skipped tests.',
    )
    parser.addoption(
        '--mark-manuals-passed',
        action='store_true',
        default=False,
        help='Mark stubbed tests as passed tests.',
    )
