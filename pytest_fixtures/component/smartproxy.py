import pytest

from robottelo.config import settings


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


@pytest.fixture(scope='module')
def module_fake_proxy(request, module_target_sat):
    """Create a Proxy and register the cleanup function"""
    port_pool_range = settings.fake_capsules.port_range
    if module_target_sat.execute(f'semanage port -l | grep {port_pool_range}').status != 0:
        module_target_sat.execute(f'semanage port -a -t websm_port_t -p tcp {port_pool_range}')
    proxy = module_target_sat.cli_factory.make_proxy()

    @request.addfinalizer
    def _cleanup():
        module_target_sat.cli.Proxy.delete({'id': proxy['id']})

    return proxy
