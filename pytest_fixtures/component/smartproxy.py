import pytest


@pytest.fixture(scope='session')
def default_smart_proxy(session_target_sat):
    smart_proxy = (
        session_target_sat.api.SmartProxy()
        .search(query={'search': f'name={session_target_sat.hostname}'})[0]
        .read()
    )
    return session_target_sat.api.SmartProxy(id=smart_proxy.id).read()


@pytest.fixture(scope='session')
def import_puppet_classes(default_smart_proxy):
    default_smart_proxy.import_puppetclasses(environment='production')
