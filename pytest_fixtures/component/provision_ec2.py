# EC2 CR Fixtures
from fauxfactory import gen_string
import pytest
from wrapanapi import EC2System

from robottelo.config import settings
from robottelo.constants import (
    AZURERM_RHEL7_FT_BYOS_IMG_URN,
    AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
    AZURERM_RHEL7_FT_GALLERY_IMG_URN,
    AZURERM_RHEL7_FT_IMG_URN,
    AZURERM_RHEL7_UD_IMG_URN,
    DEFAULT_ARCHITECTURE,
    DEFAULT_OS_SEARCH_QUERY,
)


@pytest.fixture(scope='session')
def sat_ec2(request, session_puppet_enabled_sat, session_target_sat):
    hosts = {'sat': session_target_sat, 'puppet_sat': session_puppet_enabled_sat}
    return hosts[request.param]


@pytest.fixture(scope='module')
def sat_ec2_org(sat_azure):
    return sat_ec2.api.Organization().create()


@pytest.fixture(scope='module')
def sat_ec2_loc(sat_azure):
    return sat_ec2.api.Location().create()


@pytest.fixture(scope='module')
def sat_ec2_domain(sat_ec2, sat_ec2_loc, sat_ec2_org):
    return sat_ec2.api.Domain(location=[sat_ec2_loc], organization=[sat_ec2_org]).create()


@pytest.fixture(scope='module')
def sat_ec2_default_os(sat_ec2):
    """Default OS on the Satellite"""
    return sat_ec2.api.OperatingSystem().search(query={'search': DEFAULT_OS_SEARCH_QUERY})[0].read()


@pytest.fixture(scope='module')
def sat_ec2_default_architecture(sat_ec2):
    return (
        sat_ec2.api.Architecture()
        .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]
        .read()
    )


@pytest.fixture(scope='session')
def ec2_settings():
    return {
        'aws_access_key': settings.ec2.access_key,
        'aws_secret_key': settings.ec2.secret_key,
        'aws_region': settings.ec2.region,
        'aws_image': settings.ec2.image,
        'aws_availability_zone': settings.ec2.availability_zone,
        'aws_subnet': settings.ec2.subnet,
        'aws_security_groups': settings.ec2.security_groups,
        'aws_managed_ip': settings.ec2.managed_ip,
    }
