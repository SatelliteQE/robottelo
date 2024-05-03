"""Tests for the ``smart_proxies`` paths.

:Requirement: Smartproxy

:CaseAutomation: Automated

:CaseComponent: ForemanProxy

:Team: Platform

:CaseImportance: Critical

"""

from fauxfactory import gen_string, gen_url
import pytest
from requests import HTTPError

from robottelo.config import user_nailgun_config


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.tier1
def test_positive_update_capsule(request, pytestconfig, target_sat, module_capsule_configured):
    """Update various capsule properties

    :id: a3d3eaa9-ed8d-42e6-9c83-20251e5ca9af

    :steps:
        1. Get deployed capsule from fixture
        2. Refresh features
        3. Update capsule organization
        4. Update capsule location
        5. Update capsule name

    :expectedresults: All capsule properties are updated

    :bz: 2077824

    :customerscenario: true
    """
    new_name = f'{gen_string("alpha")}-{module_capsule_configured.hostname}'
    capsule = target_sat.api.SmartProxy().search(
        query={'search': f'name = {module_capsule_configured.hostname}'}
    )[0]

    # refresh features
    features = capsule.refresh()
    result = module_capsule_configured.install(cmd_args=['enable-foreman-proxy-plugin-openscap'])
    assert result.status == 0, 'Installer failed when enabling OpenSCAP plugin.'
    features_new = capsule.refresh()
    assert len(features_new["features"]) == len(features["features"]) + 1
    assert 'Openscap' in [feature["name"] for feature in features_new["features"]]

    # update organizations
    organizations = [target_sat.api.Organization().create() for _ in range(2)]
    capsule.organization = organizations
    capsule = capsule.update(['organization'])
    assert {org.id for org in capsule.organization} == {org.id for org in organizations}

    # update locations
    locations = [target_sat.api.Location().create() for _ in range(2)]
    capsule.location = locations
    capsule = capsule.update(['location'])
    assert {loc.id for loc in capsule.organization} == {loc.id for loc in organizations}

    # update name
    capsule.name = new_name
    capsule = capsule.update(['name'])
    assert capsule.name == new_name

    @request.addfinalizer
    def _finalize():
        # Updating the hostname back
        if (
            cap := target_sat.api.SmartProxy().search(query={'search': f'name = {new_name}'})
            and pytestconfig.option.n_minus
        ):
            cap = cap[0]
            cap.name = module_capsule_configured.hostname
            cap.update(['name'])

    # serching for non-default capsule BZ#2077824
    capsules = target_sat.api.SmartProxy().search(query={'search': 'id != 1'})
    assert len(capsules) > 0
    assert capsule.url in [cps.url for cps in capsules]
    assert capsule.name in [cps.name for cps in capsules]


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
def test_negative_create_with_url(target_sat):
    """Capsule creation with random URL

    :id: e48a6260-97e0-4234-a69c-77bbbcde85d6

    :expectedresults: Proxy is not created
    """
    # Create a random proxy
    with pytest.raises(HTTPError) as context:
        target_sat.api.SmartProxy(url=gen_url(scheme='https')).create()
    assert 'Unable to communicate' in context.value.response.text


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete(target_sat):
    """Capsule deletion

    :id: 872bf12e-736d-43d1-87cf-2923966b59d0

    :expectedresults: Capsule is deleted

    :BZ: 1398695
    """
    new_port = target_sat.available_capsule_port
    with target_sat.default_url_on_new_port(9090, new_port) as url:
        proxy = target_sat.api.SmartProxy(url=url).create()
        proxy.delete()
    with pytest.raises(HTTPError):
        proxy.read()


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier1
def test_positive_update_url(request, target_sat):
    """Capsule url updated

    :id: 0305fd54-4e0c-4dd9-a537-d342c3dc867e

    :expectedresults: Capsule has the url updated
    """
    # Create fake capsule with name
    name = gen_string('alpha')
    port = target_sat.available_capsule_port
    with target_sat.default_url_on_new_port(9090, port) as url:
        proxy = target_sat.api.SmartProxy(url=url, name=name).create()
        assert proxy.name == name
    # Open another tunnel to update url
    new_port = target_sat.available_capsule_port
    with target_sat.default_url_on_new_port(9090, new_port) as url:
        proxy.url = url
        proxy = proxy.update(['url'])
        assert proxy.url == url


@pytest.mark.skip_if_not_set('fake_capsules')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_import_puppet_classes(
    request,
    session_puppet_enabled_sat,
    puppet_proxy_port_range,
    module_puppet_org,
    module_puppet_loc,
):
    """Import puppet classes from proxy for admin and non-admin user

    :id: 385efd1b-6146-47bf-babf-0127ce5955ed

    :expectedresults: Puppet classes are imported from proxy

    :CaseComponent: Puppet

    :BZ: 1398695, 2142555

    :customerscenario: true
    """
    puppet_sat = session_puppet_enabled_sat
    update_msg = (
        'Successfully updated environment and puppetclasses from the on-disk puppet installation'
    )
    no_update_msg = 'No changes to your environments detected'
    # Create role, add permissions and create non-admin user
    user_login = gen_string('alpha')
    user_password = gen_string('alpha')
    role = puppet_sat.api.Role().create()
    puppet_sat.api_factory.create_role_permissions(
        role,
        {
            'ForemanPuppet::Puppetclass': [
                'view_puppetclasses',
                'create_puppetclasses',
                'import_puppetclasses',
            ]
        },
    )
    user = puppet_sat.api.User(
        role=[role],
        admin=True,
        login=user_login,
        password=user_password,
        organization=[module_puppet_org],
        location=[module_puppet_loc],
    ).create()
    request.addfinalizer(user.delete)
    request.addfinalizer(role.delete)

    new_port = puppet_sat.available_capsule_port
    with puppet_sat.default_url_on_new_port(9090, new_port) as url:
        proxy = puppet_sat.api.SmartProxy(url=url).create()

        result = proxy.import_puppetclasses()
        assert result['message'] in [update_msg, no_update_msg]
        # Import puppetclasses with environment
        result = proxy.import_puppetclasses(environment='production')
        assert result['message'] in [update_msg, no_update_msg]

        # Non-Admin user with access to import_puppetclasses
        user_cfg = user_nailgun_config(user_login, user_password)
        user_cfg.url = f'https://{puppet_sat.hostname}'
        user_proxy = puppet_sat.api.SmartProxy(server_config=user_cfg, id=proxy.id).read()

        result = user_proxy.import_puppetclasses()
        assert result['message'] in [update_msg, no_update_msg]
        # Import puppetclasses with environment
        result = user_proxy.import_puppetclasses(environment='production')
        assert result['message'] in [update_msg, no_update_msg]

    request.addfinalizer(puppet_sat.api.SmartProxy(id=proxy.id).delete)
