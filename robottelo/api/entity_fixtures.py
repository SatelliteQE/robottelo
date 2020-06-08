# Module-wide Nailgun Entity Fixtures to be used by API, CLI and UI Tests
import pytest
from fauxfactory import gen_string
from nailgun import entities
from wrapanapi import AzureSystem
from wrapanapi import GoogleCloudSystem

from robottelo.constants import AZURERM_RG_DEFAULT
from robottelo.constants import AZURERM_RHEL7_FT_IMG_URN
from robottelo.constants import AZURERM_RHEL7_UD_IMG_URN
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DEFAULT_PXE_TEMPLATE
from robottelo.constants import DEFAULT_TEMPLATE
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.helpers import download_gce_cert
from robottelo.test import settings

# Global Satellite Entities


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_location(module_org):
    return entities.Location(organization=[module_org]).create()


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='module')
def module_smart_proxy(module_location):
    smart_proxy = (
        entities.SmartProxy()
        .search(query={'search': 'name={0}'.format(settings.server.hostname)})[0]
        .read()
    )
    smart_proxy.location.append(entities.Location(id=module_location.id))
    smart_proxy.update(['location'])
    return entities.SmartProxy(id=smart_proxy.id).read()


@pytest.fixture(scope='module')
def module_domain(module_org, module_location):
    return entities.Domain(location=[module_location], organization=[module_org]).create()


@pytest.fixture(scope='module')
def module_subnet(module_org, module_location, module_domain, module_smart_proxy):
    network = settings.vlan_networking.subnet
    subnet = entities.Subnet(
        network=network,
        mask=settings.vlan_networking.netmask,
        domain=[module_domain],
        location=[module_location],
        organization=[module_org],
        dns=module_smart_proxy,
        dhcp=module_smart_proxy,
        tftp=module_smart_proxy,
        discovery=module_smart_proxy,
        ipam='DHCP',
    ).create()
    return subnet


@pytest.fixture(scope='module')
def module_partiontable(module_org, module_location):
    ptable = (
        entities.PartitionTable()
        .search(query={'search': 'name="{0}"'.format(DEFAULT_PTABLE)})[0]
        .read()
    )
    ptable.location.append(module_location)
    ptable.organization.append(module_org)
    ptable.update(['location', 'organization'])
    return entities.PartitionTable(id=ptable.id).read()


@pytest.fixture(scope='module')
def module_provisioingtemplate(module_org, module_location):
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
def module_configtemaplate(module_org, module_location):
    pxe_template = entities.ProvisioningTemplate().search(
        query={'search': 'name="{0}"'.format(DEFAULT_PXE_TEMPLATE)}
    )
    pxe_template = pxe_template[0].read()
    pxe_template.organization.append(module_org)
    pxe_template.location.append(module_location)
    pxe_template.update(['organization', 'location'])
    pxe_template = entities.ProvisioningTemplate(id=pxe_template.id).read()
    return pxe_template


@pytest.fixture(scope='module')
def module_architecture():
    arch = (
        entities.Architecture()
        .search(query={'search': 'name="{0}"'.format(DEFAULT_ARCHITECTURE)})[0]
        .read()
    )
    return arch


@pytest.fixture(scope='module')
def module_os(
    module_architecture,
    module_partiontable,
    module_configtemaplate,
    module_provisioingtemplate,
    os=None,
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
        os = (
            entities.OperatingSystem()
            .search(
                query={
                    'search': 'family="Redhat" AND major="{0}" AND minor="{1}")'.format(
                        os.split(' ')[1].split('.')[0], os.split(' ')[1].split('.')[1]
                    )
                }
            )[0]
            .read()
        )
    os.architecture.append(module_architecture)
    os.ptable.append(module_partiontable)
    os.config_template.append(module_configtemaplate)
    os.provisioning_template.append(module_provisioingtemplate)
    os.update(['architecture', 'ptable', 'config_template', 'provisioning_template'])
    os = entities.OperatingSystem(id=os.id).read()
    return os


@pytest.fixture(scope='module')
def module_puppet_environment(module_org, module_location):
    environments = entities.Environment().search(
        query=dict(search='organization_id={0}'.format(module_org.id))
    )
    if len(environments) > 0:
        environment = environments[0].read()
        environment.location.append(module_location)
        environment = environment.update(['location'])
    else:
        environment = entities.Environment(
            organization=[module_org], location=[module_location]
        ).create()
    puppetenv = entities.Environment(id=environment.id).read()
    return puppetenv


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
def module_azurerm_finishimg(module_architecture, module_os, module_azurerm_cr):
    """ Creates Finish Template image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=module_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=module_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_cloudimg(module_architecture, module_os, module_azurerm_cr):
    """ Creates cloudinit image on AzureRM Compute Resource """
    finish_image = entities.Image(
        architecture=module_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=module_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_UD_IMG_URN,
        user_data=True,
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


@pytest.fixture(scope='class')
def module_cv(module_org):
    return entities.ContentView(organization=module_org).create()
