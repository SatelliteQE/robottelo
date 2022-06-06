import pytest

from robottelo.constants import DEFAULT_PTABLE


@pytest.fixture(scope='session')
def default_partition_table(session_target_sat):
    # Get the Partition table ID
    return session_target_sat.api.PartitionTable().search(
        query={'search': f'name="{DEFAULT_PTABLE}"'}
    )[0]
