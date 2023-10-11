from fauxfactory import gen_string
import pytest


@pytest.fixture(scope='module')
def module_discovery_hostgroup(module_org, module_location, module_target_sat):
    host = module_target_sat.api.Host(organization=module_org, location=module_location).create()
    return module_target_sat.api.HostGroup(
        organization=[module_org],
        location=[module_location],
        medium=host.medium,
        root_pass=gen_string('alpha'),
        operatingsystem=host.operatingsystem,
        ptable=host.ptable,
        domain=host.domain,
        architecture=host.architecture,
    ).create()


@pytest.fixture(scope='module')
def discovery_org(module_org, module_target_sat):
    discovery_org = module_target_sat.update_setting('discovery_organization', module_org.name)
    yield module_org
    module_target_sat.update_setting('discovery_organization', discovery_org)


@pytest.fixture(scope='module')
def discovery_location(module_location, module_target_sat):
    discovery_loc = module_target_sat.update_setting('discovery_location', module_location.name)
    yield module_location
    module_target_sat.update_setting('discovery_location', discovery_loc)
