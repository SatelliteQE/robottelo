# Azure CR Fixtures
import pytest
from fauxfactory import gen_string
from wrapanapi import AzureSystem

from robottelo.config import settings
from robottelo.constants import AZURERM_RHEL7_FT_BYOS_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_CUSTOM_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_GALLERY_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_IMG_URN
from robottelo.constants import AZURERM_RHEL7_UD_IMG_URN
from robottelo.constants import DEFAULT_ARCHITECTURE


@pytest.fixture(scope='session')
def sat_azure(request, session_puppet_enabled_sat, session_target_sat):
    hosts = {'sat': session_target_sat, 'puppet_sat': session_puppet_enabled_sat}
    yield hosts[request.param]


@pytest.fixture(scope='module')
def sat_azure_org(sat_azure):
    yield sat_azure.api.Organization().create()


@pytest.fixture(scope='module')
def sat_azure_loc(sat_azure):
    yield sat_azure.api.Location().create()


@pytest.fixture(scope='module')
def sat_azure_domain(sat_azure, sat_azure_loc, sat_azure_org):
    yield sat_azure.api.Domain(location=[sat_azure_loc], organization=[sat_azure_org]).create()


@pytest.fixture(scope='module')
def sat_azure_default_os(sat_azure):
    """Default OS on the Satellite"""
    search_string = 'name="RedHat" AND (major="6" OR major="7" OR major="8" OR major="9")'
    return sat_azure.api.OperatingSystem().search(query={'search': search_string})[0].read()


@pytest.fixture(scope='module')
def sat_azure_default_architecture(sat_azure):
    arch = (
        sat_azure.api.Architecture()
        .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]
        .read()
    )
    return arch


@pytest.fixture(scope='session')
def azurerm_settings():
    deps = {
        'tenant': settings.azurerm.tenant_id,
        'app_ident': settings.azurerm.client_id,
        'sub_id': settings.azurerm.subscription_id,
        'resource_group': settings.azurerm.resource_group,
        'secret': settings.azurerm.client_secret,
        'region': settings.azurerm.azure_region.lower().replace(' ', ''),
    }
    return deps


@pytest.fixture(scope='session')
def azurermclient(azurerm_settings):
    """Connect to AzureRM using wrapanapi AzureSystem"""
    azurermclient = AzureSystem(
        username=azurerm_settings['app_ident'],
        password=azurerm_settings['secret'],
        tenant_id=azurerm_settings['tenant'],
        subscription_id=azurerm_settings['sub_id'],
        provisioning={
            "resource_group": azurerm_settings['resource_group'],
            "template_container": None,
            "region_api": azurerm_settings['region'],
        },
    )
    yield azurermclient
    azurermclient.disconnect()


@pytest.fixture(scope='module')
def module_azurerm_cr(azurerm_settings, sat_azure_org, sat_azure_loc, sat_azure):
    """Create AzureRM Compute Resource"""
    azure_cr = sat_azure.api.AzureRMComputeResource(
        name=gen_string('alpha'),
        provider='AzureRm',
        tenant=azurerm_settings['tenant'],
        app_ident=azurerm_settings['app_ident'],
        sub_id=azurerm_settings['sub_id'],
        secret_key=azurerm_settings['secret'],
        region=azurerm_settings['region'],
        organization=[sat_azure_org],
        location=[sat_azure_loc],
    ).create()
    return azure_cr


@pytest.fixture(scope='module')
def module_azurerm_finishimg(
    sat_azure_default_architecture,
    sat_azure_default_os,
    sat_azure,
    module_azurerm_cr,
):
    """Creates Finish Template image on AzureRM Compute Resource"""
    finish_image = sat_azure.api.Image(
        architecture=sat_azure_default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=sat_azure_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_byos_finishimg(
    sat_azure_default_architecture,
    sat_azure_default_os,
    module_azurerm_cr,
    sat_azure,
):
    """Creates BYOS Finish Template image on AzureRM Compute Resource"""
    finish_image = sat_azure.api.Image(
        architecture=sat_azure_default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=sat_azure_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_BYOS_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_cloudimg(
    sat_azure_default_architecture,
    sat_azure_default_os,
    sat_azure,
    module_azurerm_cr,
):
    """Creates cloudinit image on AzureRM Compute Resource"""
    finish_image = sat_azure.api.Image(
        architecture=sat_azure_default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=sat_azure_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_UD_IMG_URN,
        user_data=True,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_gallery_finishimg(
    sat_azure_default_architecture,
    sat_azure_default_os,
    sat_azure,
    module_azurerm_cr,
):
    """Creates Shared Gallery Finish Template image on AzureRM Compute Resource"""
    finish_image = sat_azure.api.Image(
        architecture=sat_azure_default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=sat_azure_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_GALLERY_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_custom_finishimg(
    sat_azure_default_architecture,
    sat_azure_default_os,
    sat_azure,
    module_azurerm_cr,
):
    """Creates Custom Finish Template image on AzureRM Compute Resource"""
    finish_image = sat_azure.api.Image(
        architecture=sat_azure_default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=sat_azure_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
    ).create()
    return finish_image
