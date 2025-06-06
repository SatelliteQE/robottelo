# EC2 CR Fixtures
from fauxfactory import gen_string
import pytest
from wrapanapi import EC2System

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_OS_SEARCH_QUERY,
    DEFAULT_PTABLE,
)


@pytest.fixture(scope='module')
def sat_ec2(request, session_target_sat):
    hosts = {'sat': session_target_sat}
    return hosts[request.param]


@pytest.fixture(scope='module')
def sat_ec2_org(sat_ec2):
    return sat_ec2.api.Organization().create()


@pytest.fixture(scope='module')
def sat_ec2_loc(sat_ec2):
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


@pytest.fixture(scope='module')
def sat_ec2_default_partition_table(sat_ec2):
    # Get the Partition table ID
    return sat_ec2.api.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]


@pytest.fixture(scope='module')
def ec2_settings():
    return dict(
        access_key=settings.ec2.access_key,
        secret_key=settings.ec2.secret_key,
        region=settings.ec2.region,
        image=settings.ec2.image,
        availability_zone=settings.ec2.availability_zone,
        subnet=settings.ec2.subnet,
        security_groups=settings.ec2.security_groups,
        managed_ip=settings.ec2.managed_ip,
    )


@pytest.fixture(scope='module')
def ec2client(ec2_settings):
    """Connect to EC2 using wrapanapi EC2System"""
    ec2client = EC2System(
        username=ec2_settings['access_key'],
        password=ec2_settings['secret_key'],
        region=ec2_settings['region'],
    )
    yield ec2client
    ec2client.disconnect()


@pytest.fixture(scope='module')
def module_ec2_cr(ec2_settings, sat_ec2_org, sat_ec2_loc, sat_ec2):
    """Create EC2 Compute Resource"""
    return sat_ec2.api.EC2ComputeResource(
        name=gen_string('alpha'),
        provider='EC2',
        user=ec2_settings['access_key'],
        password=ec2_settings['secret_key'],
        region=ec2_settings['region'],
        organization=[sat_ec2_org],
        location=[sat_ec2_loc],
    ).create()


@pytest.fixture(scope='module')
def ec2_hostgroup(
    sat_ec2,
    sat_ec2_default_architecture,
    module_ec2_cr,
    sat_ec2_domain,
    sat_ec2_loc,
    sat_ec2_default_os,
    sat_ec2_org,
    sat_ec2_default_partition_table,
):
    """Sets Hostgroup for EC2 Host Provisioning"""
    return sat_ec2.api.HostGroup(
        architecture=sat_ec2_default_architecture,
        compute_resource=module_ec2_cr,
        domain=sat_ec2_domain,
        location=[sat_ec2_loc],
        root_pass="dog8code",
        operatingsystem=sat_ec2_default_os,
        organization=[sat_ec2_org],
        ptable=sat_ec2_default_partition_table,
    ).create()


@pytest.fixture(scope='module')
def module_ec2_finishimg(
    sat_ec2_default_architecture,
    sat_ec2_default_os,
    sat_ec2,
    module_ec2_cr,
):
    """Creates Finish Template image on EC2 Compute Resource"""
    return sat_ec2.api.Image(
        architecture=sat_ec2_default_architecture,
        compute_resource=module_ec2_cr,
        name=gen_string('alpha'),
        operatingsystem=sat_ec2_default_os,
        username="root",
        uuid=settings.ec2.image,
    ).create()
