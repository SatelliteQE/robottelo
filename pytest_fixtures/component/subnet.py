# Subnet Fixtures
import pytest
from nailgun import entities

from robottelo.config import settings


@pytest.mark.vlan_networking
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


@pytest.fixture(scope='module')
def module_default_subnet(module_org, module_location):
    return entities.Subnet(location=[module_location], organization=[module_org]).create()
