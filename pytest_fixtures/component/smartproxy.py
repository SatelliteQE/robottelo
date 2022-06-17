import pytest
from fauxfactory import gen_string

from robottelo.cleanup import capsule_cleanup
from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.helpers import default_url_on_new_port
from robottelo.helpers import get_available_capsule_port


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
    args = {'name': gen_string(str_type='alpha')}
    newport = get_available_capsule_port()
    try:
        with default_url_on_new_port(9090, newport) as url:
            args['url'] = url
            proxy = module_target_sat.api.SmartProxy(**args).create()
            yield proxy
            capsule_cleanup(proxy.id)
    except CapsuleTunnelError as err:
        pytest.fail(f'Failed to create ssh tunnel: {err}')
