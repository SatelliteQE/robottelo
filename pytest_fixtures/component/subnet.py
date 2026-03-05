# Subnet Fixtures
from fauxfactory import gen_ipaddr
import pytest


@pytest.fixture(scope='module')
def module_default_subnet(module_target_sat, module_org, module_location):
    subnet_kwargs = {
        'location': [module_location],
        'organization': [module_org],
    }
    # Create subnet with appropriate network type based on satellite configuration
    if module_target_sat.network_type.has_ipv6:
        subnet_kwargs['network_type'] = 'IPv6'
        subnet_kwargs['network'] = gen_ipaddr(ip3=True, ipv6=True)
        subnet_kwargs['mask'] = 'ffff:ffff:ffff:ffff::'
        subnet_kwargs['ipam'] = 'EUI-64'
    else:
        subnet_kwargs['network_type'] = 'IPv4'
    return module_target_sat.api.Subnet(**subnet_kwargs).create()
