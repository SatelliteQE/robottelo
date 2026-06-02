from fauxfactory import gen_alpha
import pytest

from robottelo.constants import DEFAULT_PTABLE


@pytest.fixture(scope='session')
def default_partition_table(session_target_sat):
    # Get the Partition table ID
    return session_target_sat.api.PartitionTable().search(
        query={'search': f'name="{DEFAULT_PTABLE}"'}
    )[0]


@pytest.fixture(scope='module')
def locked_partition_table(module_target_sat):
    """Create a locked partition table. Delete it afterward."""
    ptable = module_target_sat.api.PartitionTable(name=gen_alpha(), locked=True).create()
    yield ptable
    ptable.locked = False
    ptable.update(['locked']).delete()
