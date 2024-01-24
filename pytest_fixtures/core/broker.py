from contextlib import contextmanager

from box import Box
from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.hosts import ContentHostError, Satellite, lru_sat_ready_rhel


@pytest.fixture(scope='session')
def _default_sat(align_to_satellite):
    """Returns a Satellite object for settings.server.hostname"""
    if settings.server.hostname:
        try:
            return Satellite.get_host_by_hostname(settings.server.hostname)
        except ContentHostError:
            return Satellite()
    return None


@contextmanager
def _target_sat_imp(request, _default_sat, satellite_factory):
    """This is the actual working part of the following target_sat fixtures"""
    if request.node.get_closest_marker(name='destructive'):
        new_sat = satellite_factory()
        yield new_sat
        new_sat.teardown()
        Broker(hosts=[new_sat]).checkin()
    elif 'sanity' in request.config.option.markexpr:
        installer_sat = lru_sat_ready_rhel(settings.server.version.rhel_version)
        settings.set('server.hostname', installer_sat.hostname)
        yield installer_sat
    else:
        yield _default_sat


@pytest.fixture
def target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='module')
def module_target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='session')
def session_target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='class')
def class_target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='module')
def module_discovery_sat(
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
):
    """Creates a Satellite with discovery installed and configured"""
    sat = module_provisioning_sat.sat
    # Register to CDN and install discovery image
    sat.register_to_cdn()
    sat.execute('yum -y --disableplugin=foreman-protector install foreman-discovery-image')
    sat.unregister()
    # Symlink image so it can be uploaded for KEXEC
    disc_img_path = sat.execute(
        'find /usr/share/foreman-discovery-image -name "foreman-discovery-image-*.iso"'
    ).stdout[:-1]
    disc_img_name = disc_img_path.split("/")[-1]
    sat.execute(f'ln -s {disc_img_path} /var/www/html/pub/{disc_img_name}')
    # Change 'Default PXE global template entry'
    pxe_entry = sat.api.Setting().search(query={'search': 'Default PXE global template entry'})[0]
    if pxe_entry.value != "discovery":
        pxe_entry.value = "discovery"
        pxe_entry.update(['value'])
    # Build PXE default template to get default PXE file
    sat.api.ProvisioningTemplate().build_pxe_default()

    # Update discovery taxonomies settings
    discovery_loc = sat.api.Setting().search(query={'search': 'name=discovery_location'})[0]
    discovery_loc.value = module_location.name
    discovery_loc.update(['value'])
    discovery_org = sat.api.Setting().search(query={'search': 'name=discovery_organization'})[0]
    discovery_org.value = module_sca_manifest_org.name
    discovery_org.update(['value'])

    # Enable flag to auto provision discovered hosts via discovery rules
    discovery_auto = sat.api.Setting().search(query={'search': 'name=discovery_auto'})[0]
    discovery_auto.value = 'true'
    discovery_auto.update(['value'])

    return Box(sat=sat, iso=disc_img_name)
