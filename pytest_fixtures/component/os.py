# Operating System Fixtures
import pytest
from nailgun import entities


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
        search_string = 'name="RedHat" AND (major="6" OR major="7" OR major="8")'
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


@pytest.fixture(scope='module')
def os_path(default_os):
    from robottelo.config import settings

    # Check what OS was found to use correct media
    if default_os.major == "6":
        os_distr_url = settings.repos.rhel6_os
    elif default_os.major == "7":
        os_distr_url = settings.repos.rhel7_os
    elif default_os.major == "8":
        os_distr_url = settings.repos.rhel8_os.baseos
    elif default_os.major == "9":
        os_distr_url = settings.repos.rhel9_os.baseos
    else:
        pytest.fail('Proposed RHEL version is not supported')
    return os_distr_url
