# Host Specific Fixtures
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.constants import DEFAULT_CV
from robottelo.constants import ENVIRONMENT
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


@pytest.fixture
def function_host(target_sat):
    return target_sat.api.Host().create()


@pytest.fixture(scope='module')
def module_host():
    return entities.Host().create()


@pytest.fixture(scope='module')
def module_model():
    return entities.Model().create()


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.fixture(scope="module")
def setup_rhst_repo():
    """Prepare Satellite tools repository for usage in specified organization"""
    org = entities.Organization().create()
    cv = entities.ContentView(organization=org).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    ak = entities.ActivationKey(
        environment=lce,
        organization=org,
    ).create()
    repo_name = 'rhst7'
    setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET[repo_name],
            'repository': REPOS[repo_name]['name'],
            'organization-id': org.id,
            'content-view-id': cv.id,
            'lifecycle-environment-id': lce.id,
            'activationkey-id': ak.id,
        }
    )
    return {'ak': ak, 'cv': cv, 'lce': lce, 'org': org, 'repo_name': repo_name}


@pytest.fixture(scope='module')
def module_host_template(module_org, smart_proxy_location, module_target_sat):
    host_template = module_target_sat.api.Host(
        organization=module_org, location=smart_proxy_location, build=True
    )
    host_template.create_missing()
    return host_template


@pytest.fixture
def host_ui_options(module_host_template):
    os_name = (
        f'{module_host_template.operatingsystem.name} {module_host_template.operatingsystem.major}'
    )
    values = {
        'host.name': module_host_template.name,
        'host.organization': module_host_template.organization.name,
        'host.location': module_host_template.location.name,
        'host.lce': ENVIRONMENT,
        'host.content_view': DEFAULT_CV,
        'operating_system.architecture': module_host_template.architecture.name,
        'operating_system.operating_system': os_name,
        'operating_system.media_type': 'All Media',
        'operating_system.media': module_host_template.medium.name,
        'operating_system.ptable': module_host_template.ptable.name,
        'operating_system.root_password': module_host_template.root_pass,
        'interfaces.interface.interface_type': 'Interface',
        'interfaces.interface.device_identifier': gen_string('alpha'),
        'interfaces.interface.mac': module_host_template.mac,
        'interfaces.interface.domain': module_host_template.domain.name,
        'interfaces.interface.primary': True,
        'interfaces.interface.interface_additional_data.virtual_nic': False,
        'parameters.global_params': None,
        'parameters.host_params': None,
        'additional_information.comment': 'Host with fake data',
    }
    host_name = f'{module_host_template.name}.{module_host_template.domain.name}'
    return values, host_name
