# Domain Fixtures
import pytest


@pytest.fixture(scope='session')
def default_domain(session_target_sat, default_smart_proxy):
    domain_name = session_target_sat.hostname.partition('.')[-1]
    dom = session_target_sat.api.Domain().search(query={'search': f'name={domain_name}'})[0]
    if 'dns' in session_target_sat.get_features():
        dom.dns = default_smart_proxy
        dom.update(['dns'])
    return session_target_sat.api.Domain(id=dom.id).read()


@pytest.fixture(scope='module')
def module_domain(module_target_sat, module_org, module_location):
    return module_target_sat.api.Domain(
        location=[module_location], organization=[module_org]
    ).create()
