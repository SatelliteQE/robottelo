# Domain Fixtures
import pytest
from nailgun import entities


@pytest.fixture(scope='session')
def default_domain(session_target_sat, default_smart_proxy):
    domain_name = session_target_sat.hostname.partition('.')[-1]
    dom = entities.Domain().search(query={'search': f'name={domain_name}'})[0]
    dom.dns = default_smart_proxy
    dom.update(['dns'])
    return entities.Domain(id=dom.id).read()


@pytest.fixture(scope='module')
def module_domain(module_org, module_location):
    return entities.Domain(location=[module_location], organization=[module_org]).create()
