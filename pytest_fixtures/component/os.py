# Operating System Fixtures
import pytest

from robottelo.config import settings


@pytest.fixture(scope='session')
def default_os(
    default_architecture,
    default_partitiontable,
    default_pxetemplate,
    session_target_sat,
):
    """Returns an Operating System entity read from searching for supportability.content_host.default_os_name"""
    search_string = f'name="{settings.supportability.content_hosts.default_os_name}"'

    try:
        os = (
            session_target_sat.api.OperatingSystem()
            .search(query={'search': search_string})[0]
            .read()
        )
    except IndexError as e:
        raise RuntimeError(f"Could not find operating system for '{search_string}'") from e

    os.architecture.append(default_architecture)
    os.ptable.append(default_partitiontable)
    os.provisioning_template.append(default_pxetemplate)
    os.update(['architecture', 'ptable', 'provisioning_template'])

    return session_target_sat.api.OperatingSystem(id=os.id).read()


@pytest.fixture(scope='module')
def module_os(module_target_sat):
    return module_target_sat.api.OperatingSystem().create()


@pytest.fixture(scope='module')
def os_path(default_os):
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
