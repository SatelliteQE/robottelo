# Module-wide Nailgun Entity Fixtures to be used by API, CLI and UI Tests
import os

import pytest
from fauxfactory import gen_string
from nailgun import entities
from wrapanapi import AzureSystem
from wrapanapi import GoogleCloudSystem

from robottelo import ssh
from robottelo.constants import AZURERM_RG_DEFAULT
from robottelo.constants import AZURERM_RHEL7_FT_BYOS_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_CUSTOM_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_GALLERY_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_IMG_URN
from robottelo.constants import AZURERM_RHEL7_UD_IMG_URN
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_PXE_TEMPLATE
from robottelo.constants import DEFAULT_TEMPLATE
from robottelo.constants import ENVIRONMENT
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.helpers import download_gce_cert
from robottelo.helpers import file_downloader
from robottelo.test import settings

# Global Satellite Entities

if not settings.configured:
    settings.configure()


@pytest.fixture(scope='session')
def default_org():
    return entities.Organization().search(query={'search': f'name={DEFAULT_ORG}'})[0]


@pytest.fixture(scope='session')
def default_location():
    return entities.Location().search(query={'search': f'name={DEFAULT_LOC}'})[0]


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_location(module_org):
    return entities.Location(organization=[module_org]).create()


@pytest.fixture(scope='session')
def default_lce():
    return entities.LifecycleEnvironment().search(query={'search': f'name={ENVIRONMENT}'})[0]


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='session')
def default_smart_proxy():
    smart_proxy = (
        entities.SmartProxy()
        .search(query={'search': 'name={0}'.format(settings.server.hostname)})[0]
        .read()
    )
    return entities.SmartProxy(id=smart_proxy.id).read()


@pytest.fixture(scope='session')
def default_domain(default_smart_proxy):
    *_, domain_name = settings.server.hostname.partition('.')
    dom = entities.Domain().search(query={'search': 'name={}'.format(domain_name)})[0]
    dom.dns = default_smart_proxy
    dom.update(['dns'])
    return entities.Domain(id=dom.id).read()


@pytest.fixture(scope='module')
def module_domain(module_org, module_location):
    return entities.Domain(location=[module_location], organization=[module_org]).create()


@pytest.fixture(scope='module')
def module_subnet(module_org, module_location, default_domain, default_smart_proxy):
    network = settings.vlan_networking.subnet
    subnet = entities.Subnet(
        network=network,
        mask=settings.vlan_networking.netmask,
        domain=[default_domain],
        location=[module_location],
        organization=[module_org],
        dns=default_smart_proxy,
        dhcp=default_smart_proxy,
        tftp=default_smart_proxy,
        discovery=default_smart_proxy,
        ipam='DHCP',
    ).create()
    return subnet


@pytest.fixture(scope='session')
def default_partitiontable():
    ptables = entities.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})
    if ptables:
        return ptables[0].read()


@pytest.fixture(scope='module')
def module_provisioningtemplate_default(module_org, module_location):
    provisioning_template = entities.ProvisioningTemplate().search(
        query={'search': 'name="{0}"'.format(DEFAULT_TEMPLATE)}
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
        query={'search': 'name="{0}"'.format(DEFAULT_PXE_TEMPLATE)}
    )
    pxe_template = pxe_template[0].read()
    pxe_template.organization.append(module_org)
    pxe_template.location.append(module_location)
    pxe_template.update(['organization', 'location'])
    pxe_template = entities.ProvisioningTemplate(id=pxe_template.id).read()
    return pxe_template


@pytest.fixture(scope='session')
def default_architecture():
    arch = (
        entities.Architecture()
        .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]
        .read()
    )
    return arch


@pytest.fixture(scope='session')
def default_os(
    default_architecture, default_partitiontable, default_pxetemplate, os=None,
):
    if os is None:
        os = (
            entities.OperatingSystem()
            .search(
                query={
                    'search': 'name="RedHat" AND (major="{0}" OR major="{1}")'.format(
                        RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION
                    )
                }
            )[0]
            .read()
        )
    else:
        major = os.split(' ')[1].split('.')[0]
        minor = os.split(' ')[1].split('.')[1]
        os = (
            entities.OperatingSystem()
            .search(query={'search': f'family="Redhat" AND major="{major}" AND minor="{minor}"'})[
                0
            ]
            .read()
        )
    os.architecture.append(default_architecture)
    os.ptable.append(default_partitiontable)
    os.provisioning_template.append(default_pxetemplate)
    os.update(['architecture', 'ptable', 'provisioning_template'])
    os = entities.OperatingSystem(id=os.id).read()
    return os


@pytest.fixture(scope='session')
def default_puppet_environment(module_org):
    environments = entities.Environment().search(
        query=dict(search='organization_id={0}'.format(module_org.id))
    )
    if environments:
        return environments[0].read()


@pytest.fixture(scope='module')
def module_puppet_environment(module_org, module_location):
    environment = entities.Environment(
        organization=[module_org], location=[module_location]
    ).create()
    return entities.Environment(id=environment.id).read()


# Google Cloud Engine Entities


@pytest.fixture(scope='session')
def googleclient():
    gceclient = GoogleCloudSystem(
        project=settings.gce.project_id,
        zone=settings.gce.zone,
        file_path=download_gce_cert(),
        file_type='json',
    )
    yield gceclient
    gceclient.disconnect()


@pytest.fixture(scope='session')
def gce_latest_rhel_uuid(googleclient):
    template_names = [img.name for img in googleclient.list_templates(True)]
    latest_rhel7_template = max(name for name in template_names if name.startswith('rhel-7'))
    latest_rhel7_uuid = googleclient.get_template(latest_rhel7_template, project='rhel-cloud').uuid
    return latest_rhel7_uuid


@pytest.fixture(scope='session')
def gce_custom_cloudinit_uuid(googleclient):
    cloudinit_uuid = googleclient.get_template('customcinit', project=settings.gce.project_id).uuid
    return cloudinit_uuid


@pytest.fixture(scope='module')
def module_gce_compute(module_org, module_location):
    gce_cr = entities.GCEComputeResource(
        name=gen_string('alphanumeric'),
        provider='GCE',
        email=settings.gce.client_email,
        key_path=settings.gce.cert_path,
        project=settings.gce.project_id,
        zone=settings.gce.zone,
        organization=[module_org],
        location=[module_location],
    ).create()
    return gce_cr


# Azure Entities


@pytest.fixture(scope='session')
def azurerm_settings():
    deps = {
        'tenant': settings.azurerm.tenant_id,
        'app_ident': settings.azurerm.client_id,
        'sub_id': settings.azurerm.subscription_id,
        'secret': settings.azurerm.client_secret,
        'region': settings.azurerm.azure_region.lower().replace(' ', ''),
    }
    return deps


@pytest.fixture(scope='module')
def module_azurerm_cr(azurerm_settings, module_org, module_location):
    """ Create AzureRM Compute Resource """
    azure_cr = entities.AzureRMComputeResource(
        name=gen_string('alpha'),
        provider='AzureRm',
        tenant=azurerm_settings['tenant'],
        app_ident=azurerm_settings['app_ident'],
        sub_id=azurerm_settings['sub_id'],
        secret_key=azurerm_settings['secret'],
        region=azurerm_settings['region'],
        organization=[module_org],
        location=[module_location],
    ).create()
    return azure_cr


@pytest.fixture(scope='module')
def module_azurerm_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_byos_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates BYOS Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_BYOS_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_cloudimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates cloudinit image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_UD_IMG_URN,
        user_data=True,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_gallery_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates Shared Gallery Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_GALLERY_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_custom_finishimg(default_architecture, default_os, module_azurerm_cr):
    """ Creates Custom Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='session')
def azurermclient(azurerm_settings):
    """ Connect to AzureRM using wrapanapi AzureSystem"""
    azurermclient = AzureSystem(
        username=azurerm_settings['app_ident'],
        password=azurerm_settings['secret'],
        tenant_id=azurerm_settings['tenant'],
        subscription_id=azurerm_settings['sub_id'],
        provisioning={
            "resource_group": AZURERM_RG_DEFAULT,
            "template_container": None,
            "region_api": azurerm_settings['region'],
        },
    )
    yield azurermclient
    azurermclient.disconnect()


# Katello Entities


@pytest.fixture(scope='module')
def module_product(module_org):
    return entities.Product(organization=module_org).create()


@pytest.fixture(scope='module')
def module_cv(module_org):
    return entities.ContentView(organization=module_org).create()


@pytest.fixture(scope='session')
def default_contentview(module_org):
    return entities.ContentView().search(
        query={
            'search': 'label=Default_Organization_View',
            'organization_id': '{}'.format(module_org.id),
        }
    )


@pytest.fixture(scope="module")
def tailoring_file_path():
    """ Return Tailoring file path."""
    return file_downloader(file_url=settings.oscap.tailoring_path)[0]


@pytest.fixture(scope="module")
def oscap_content_path():
    """ Download scap content from satellite and return local path of it."""
    _, file_name = os.path.split(settings.oscap.content_path)
    local_file = f"/tmp/{file_name}"
    ssh.download_file(settings.oscap.content_path, local_file)
    return local_file


@pytest.fixture(scope='session')
def default_pxetemplate():
    pxe_template = entities.ProvisioningTemplate().search(query={'search': DEFAULT_PXE_TEMPLATE})
    return pxe_template[0].read()
