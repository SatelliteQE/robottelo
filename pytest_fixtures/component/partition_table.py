import pytest

from robottelo.constants import DEFAULT_PTABLE


@pytest.fixture(scope='session')
def default_partition_table(default_sat):
    # Get the Partition table ID
    return default_sat.api.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]
