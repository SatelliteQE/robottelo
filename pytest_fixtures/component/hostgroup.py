# Hostgroup Fixtures
import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.logging import logger


@pytest.fixture(scope='module')
def module_hostgroup(module_target_sat):
    return module_target_sat.api.HostGroup().create()


@pytest.fixture(scope='class')
def class_hostgroup(class_target_sat, class_org, class_location):
    """Create a hostgroup linked to specific org and location created at the class scope"""
    hostgroup = class_target_sat.api.HostGroup(
        organization=[class_org], location=[class_location]
    ).create()
    yield hostgroup
    try:
        hostgroup.delete()
    except HTTPError:
        logger.exception('Exception while deleting class scope hostgroup entity in teardown')


@pytest.fixture
def hostgroup_with_synced_ks(
    module_target_sat,
    module_sca_manifest_org,
    module_location,
    default_architecture,
    module_sync_kickstart_content,
    module_lce,
    default_partitiontable,
    pxe_loader,
):
    """
    This fixture returns new host group with LCE and CV with synced kickstart repository.
    """
    content_view = module_target_sat.api.ContentView(organization=module_sca_manifest_org).create()
    content_view.repository = [module_sync_kickstart_content.ksrepo]
    content_view.update(['repository'])
    task = content_view.publish()
    task_status = module_target_sat.wait_for_tasks(
        search_query=f'Actions::Katello::ContentView::Publish and id = {task["id"]}',
        search_rate=15,
        max_tries=10,
    )
    assert task_status[0].result == 'success'
    content_view = content_view.read()
    content_view.version[0].promote(data={'environment_ids': module_lce.id})

    return module_target_sat.api.HostGroup(
        organization=[module_sca_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=module_sync_kickstart_content.domain,
        content_source=module_target_sat.nailgun_smart_proxy.id,
        content_view=content_view,
        kickstart_repository=module_sync_kickstart_content.ksrepo,
        lifecycle_environment=module_lce,
        root_pass=settings.provisioning.host_root_password,
        operatingsystem=module_sync_kickstart_content.os,
        ptable=default_partitiontable,
        pxe_loader=pxe_loader.pxe_loader,
    ).create()


@pytest.fixture
def module_target_sat_in_org_and_loc(
    module_target_sat, module_org, module_location, current_sat_org, current_sat_location
):
    """Assigns `module_target_sat` host to `module_org` organization and `module_location` location in setup
    and reassigns it back in teardown.
    """
    host = module_target_sat.nailgun_smart_proxy.read()
    host.organization = [module_org]
    host.location = [module_location]
    host.update(['organization', 'location'])
    yield module_target_sat
    host.organization = [current_sat_org]
    host.location = [current_sat_location]
    host.update(['organization', 'location'])
