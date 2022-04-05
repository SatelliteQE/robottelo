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


@pytest.fixture(scope='module')
def module_azurerm_cr(azurerm_settings, module_org, module_location, default_sat):
    """Create AzureRM Compute Resource"""
    azure_cr = default_sat.api.AzureRMComputeResource(
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
def module_azurerm_cr_puppet(
    azurerm_settings, module_puppet_org, module_puppet_loc, session_puppet_enabled_sat
):
    """Create AzureRM Compute Resource"""
    azure_cr = session_puppet_enabled_sat.api.AzureRMComputeResource(
        name=gen_string('alpha'),
        provider='AzureRm',
        tenant=azurerm_settings['tenant'],
        app_ident=azurerm_settings['app_ident'],
        sub_id=azurerm_settings['sub_id'],
        secret_key=azurerm_settings['secret'],
        region=azurerm_settings['region'],
        organization=[module_puppet_org],
        location=[module_puppet_loc],
    ).create()
    return azure_cr


@pytest.fixture(scope='module')
def module_azurerm_finishimg(
    default_architecture,
    default_os,
    default_sat,
    module_azurerm_cr,
):
    """Creates Finish Template image on AzureRM Compute Resource"""
    finish_image = default_sat.api.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_finishimg_puppet(
    session_puppet_default_architecture,
    session_puppet_default_os,
    session_puppet_enabled_sat,
    module_azurerm_cr_puppet,
):
    """Creates Finish Template image on AzureRM Compute Resource"""
    finish_image = session_puppet_enabled_sat.api.Image(
        architecture=session_puppet_default_architecture,
        compute_resource=module_azurerm_cr_puppet,
        name=gen_string('alpha'),
        operatingsystem=session_puppet_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_byos_finishimg(
    default_architecture,
    default_os,
    module_azurerm_cr,
    default_sat,
):
    """Creates BYOS Finish Template image on AzureRM Compute Resource"""
    finish_image = default_sat.api.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_BYOS_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_byos_finishimg_puppet(
    session_puppet_default_architecture,
    session_puppet_default_os,
    module_azurerm_cr_puppet,
    session_puppet_enabled_sat,
):
    """Creates BYOS Finish Template image on AzureRM Compute Resource"""
    finish_image = session_puppet_enabled_sat.api.Image(
        architecture=session_puppet_default_architecture,
        compute_resource=module_azurerm_cr_puppet,
        name=gen_string('alpha'),
        operatingsystem=session_puppet_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_BYOS_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_cloudimg(
    default_architecture,
    default_os,
    default_sat,
    module_azurerm_cr,
):
    """Creates cloudinit image on AzureRM Compute Resource"""
    finish_image = default_sat.api.Image(
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
def module_azurerm_cloudimg_puppet(
    session_puppet_default_architecture,
    session_puppet_default_os,
    session_puppet_enabled_sat,
    module_azurerm_cr_puppet,
):
    """Creates cloudinit image on AzureRM Compute Resource"""
    finish_image = session_puppet_enabled_sat.api.Image(
        architecture=session_puppet_default_architecture,
        compute_resource=module_azurerm_cr_puppet,
        name=gen_string('alpha'),
        operatingsystem=session_puppet_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_UD_IMG_URN,
        user_data=True,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_gallery_finishimg(
    default_architecture,
    default_os,
    default_sat,
    module_azurerm_cr,
):
    """Creates Shared Gallery Finish Template image on AzureRM Compute Resource"""
    finish_image = default_sat.api.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_GALLERY_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_gallery_finishimg_puppet(
    session_puppet_default_architecture,
    session_puppet_default_os,
    session_puppet_enabled_sat,
    module_azurerm_cr_puppet,
):
    """Creates Shared Gallery Finish Template image on AzureRM Compute Resource"""
    finish_image = session_puppet_enabled_sat.api.Image(
        architecture=session_puppet_default_architecture,
        compute_resource=module_azurerm_cr_puppet,
        name=gen_string('alpha'),
        operatingsystem=session_puppet_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_GALLERY_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_custom_finishimg(
    default_architecture,
    default_os,
    default_sat,
    module_azurerm_cr,
):
    """Creates Custom Finish Template image on AzureRM Compute Resource"""
    finish_image = default_sat.api.Image(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_azurerm_custom_finishimg_puppet(
    session_puppet_default_architecture,
    session_puppet_default_os,
    session_puppet_enabled_sat,
    module_azurerm_cr_puppet,
):
    """Creates Custom Finish Template image on AzureRM Compute Resource"""
    finish_image = session_puppet_enabled_sat.api.Image(
        architecture=session_puppet_default_architecture,
        compute_resource=module_azurerm_cr_puppet,
        name=gen_string('alpha'),
        operatingsystem=session_puppet_default_os,
        username=settings.azurerm.username,
        uuid=AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
    ).create()
    return finish_image


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
