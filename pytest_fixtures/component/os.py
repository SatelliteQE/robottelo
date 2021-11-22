# Operating System Fixtures
import pytest
from nailgun import entities

from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION


@pytest.fixture(scope='session')
def default_os(
    default_architecture,
    default_partitiontable,
    default_pxetemplate,
    request,
):
    """Returns an Operating System entity read from searching Redhat family

    Indirect parametrization should pass an operating system version string like 'RHEL 7.9'
    Default operating system will find the first RHEL6 or RHEL7 entity
    """
    os = getattr(request, 'param', None)
    if os is None:
        search_string = (
            f'name="RedHat" AND (major="{RHEL_6_MAJOR_VERSION}" '
            f'OR major="{RHEL_7_MAJOR_VERSION}")'
        )
    else:
        version = os.split(' ')[1].split('.')
        search_string = f'family="Redhat" AND major="{version[0]}" AND minor="{version[1]}"'
    os = entities.OperatingSystem().search(query={'search': search_string})[0].read()
    os.architecture.append(default_architecture)
    os.ptable.append(default_partitiontable)
    os.provisioning_template.append(default_pxetemplate)
    os.update(['architecture', 'ptable', 'provisioning_template'])
    os = entities.OperatingSystem(id=os.id).read()
    return os


@pytest.fixture(scope='module')
def module_os():
    return entities.OperatingSystem().create()
