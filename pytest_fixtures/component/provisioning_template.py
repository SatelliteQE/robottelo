# Provisioning Template Fixtures
import pytest
from box import Box
from nailgun import entities
from packaging.version import Version

from robottelo import constants
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_PXE_TEMPLATE
from robottelo.constants import DEFAULT_TEMPLATE


@pytest.fixture(scope='module')
def module_provisioningtemplate_default(module_org, module_location):
    provisioning_template = entities.ProvisioningTemplate().search(
        query={'search': f'name="{DEFAULT_TEMPLATE}"'}
    )
    provisioning_template = provisioning_template[0].read()
    provisioning_template.organization.append(module_org)
    provisioning_template.location.append(module_location)
    provisioning_template.update(['organization', 'location'])
    provisioning_template = entities.ProvisioningTemplate(id=provisioning_template.id).read()
    return provisioning_template


@pytest.fixture(scope='module')
def module_provisioningtemplate_pxe(module_org, module_location):
    pxe_template = entities.ProvisioningTemplate().search(
        query={'search': f'name="{DEFAULT_PXE_TEMPLATE}"'}
    )
    pxe_template = pxe_template[0].read()
    pxe_template.organization.append(module_org)
    pxe_template.location.append(module_location)
    pxe_template.update(['organization', 'location'])
    pxe_template = entities.ProvisioningTemplate(id=pxe_template.id).read()
    return pxe_template


@pytest.fixture(scope='session')
def default_partitiontable():
    ptables = entities.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})
    if ptables:
        return ptables[0].read()


@pytest.fixture(scope='module')
def module_env():
    return entities.Environment().create()


@pytest.fixture(scope='session')
def default_pxetemplate():
    pxe_template = entities.ProvisioningTemplate().search(query={'search': DEFAULT_PXE_TEMPLATE})
    return pxe_template[0].read()


@pytest.fixture(scope="module")
def module_sync_kickstart_content(
    request, module_target_sat, module_sca_manifest_org, module_location
):
    """
    This fixture sets up kickstart repositories for a specific RHEL version
    that is specified in `request.param`.
    """
    repo_names = []
    tasks = []
    rhel_ver = request.param
    if int(rhel_ver) <= 7:
        repo_names.append(f'rhel{rhel_ver}')
    else:
        repo_names.append(f'rhel{rhel_ver}_bos')
    for name in repo_names:
        rh_kickstart_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=module_sca_manifest_org.id,
            product=constants.REPOS['kickstart'][name]['product'],
            repo=constants.REPOS['kickstart'][name]['name'],
            reposet=constants.REPOS['kickstart'][name]['reposet'],
            releasever=constants.REPOS['kickstart'][name]['version'],
        )
        rh_repo = module_target_sat.api.Repository(id=rh_kickstart_repo_id).read()
        task = rh_repo.sync(synchronous=False)
        tasks.append(task)
    for task in tasks:
        module_target_sat.wait_for_tasks(
            search_query=(f'id = {task["id"]}'),
            poll_timeout=2500,
        )
        task_status = module_target_sat.api.ForemanTask(id=task['id']).poll()
        assert task_status['result'] == 'success'
    rhel_xy = Version(
        constants.REPOS['kickstart'][f'rhel{rhel_ver}']['version']
        if rhel_ver == 7
        else constants.REPOS['kickstart'][f'rhel{rhel_ver}_bos']['version']
    )
    o_systems = module_target_sat.api.OperatingSystem().search(
        query={'search': f'family=Redhat and major={rhel_xy.major} and minor={rhel_xy.minor}'}
    )
    assert o_systems, f'Operating system RHEL {rhel_xy} was not found'
    os = o_systems[0].read()
    domain = module_target_sat.api.Domain(
        location=[module_location], organization=[module_sca_manifest_org]
    ).create()
    return Box(rhel_ver=rhel_ver, os=os, domain=domain)
