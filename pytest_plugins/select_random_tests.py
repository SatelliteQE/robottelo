import math
import random

from fauxfactory import gen_string
import pytest

from robottelo.logging import logger


def pytest_addoption(parser):
    """Add --select-random-tests option to select and run N random tests from the selected test collection.
    Examples:
        pytest tests/foreman/ --select-random-tests 4 --random-seed fksdjn
        pytest tests/foreman/ --select-random-tests '5%'
    """
    parser.addoption(
        '--select-random-tests',
        action='store',
        default=0,
        help='Number/Percentage of tests to randomly select and run from selected test collection. \n '
        'To re-run same collection later, provide seed value using --random-seed. '
        'OR check robottelo.log to get the seed value that was generated randomly.',
    )
    parser.addoption(
        '--random-seed',
        action='store',
        default=gen_string('alpha'),
        help='Seed value for random test collection. Should be used with --select-random-tests option.',
    )


def pytest_configure(config):
    """Register select_random_tests and random_seed markers to avoid warnings."""
    markers = [
        'select_random_tests: Number/Percentage of tests to randomly select and run.',
        'random_seed: Seed value for random test collection.',
    ]
    for marker in markers:
        config.addinivalue_line('markers', marker)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items, config):
    """Modify test collection to select and run N random tests from the selected test collection."""
    select_random_tests = config.getoption('select_random_tests')
    random_seed = config.getoption('random_seed')
    if select_random_tests:
        select_random_tests = (
            math.ceil(len(items) * float(select_random_tests.split('%')[0]) / 100)
            if '%' in select_random_tests
            else int(select_random_tests)
        )
        try:
            random.seed(random_seed)
            selected = random.sample(items, k=select_random_tests)
        except ValueError as err:
            logger.warning(
                'Number of tests to select randomly are greater than the tests in the selected collection. '
                f'Tests collected: {len(items)}, Tests to select randomly: {select_random_tests}, Seed value: {random_seed}'
            )
            raise err
        logger.info(
            'Modifying test collection based on --select-random-tests pytest option. '
            f'Tests collected: {len(items)}, Tests to select randomly: {select_random_tests}, Seed value: {random_seed}'
        )
        deselected = [item for item in items if item not in selected]
        # selected will be empty if no filter option was passed, defaulting to full items list
        items[:] = selected if deselected else items
        config.hook.pytest_deselected(items=deselected)
