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
    """Return or create the configured default OS and attach provisioning defaults."""
    search_string = f'name="{settings.supportability.content_hosts.default_os_name}"'

    operating_systems = session_target_sat.api.OperatingSystem().search(
        query={'search': search_string}
    )
    if operating_systems:
        os = operating_systems[0].read()
    else:
        os = session_target_sat.api.OperatingSystem(
            name=settings.supportability.content_hosts.default_os_name,
            family='Redhat',
            major=str(settings.content_host.default_rhel_version),
            minor='0',
        ).create()

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
    if int(default_os.major) <= 7:
        os_distr_url = getattr(settings.repos, f'rhel{default_os.major}_os')
    elif int(default_os.major) > 7:
        os_distr_url = getattr(settings.repos, f'rhel{default_os.major}_os').baseos
    else:
        pytest.fail('Proposed RHEL version is not supported')
    return os_distr_url
