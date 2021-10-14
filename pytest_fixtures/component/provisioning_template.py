# Provisioning Template Fixtures
import pytest
from nailgun import entities

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
