"""Unit tests for the ``hosts`` paths.

An API reference can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html


:Requirement: Host

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

import http
import json

from fauxfactory import gen_choice, gen_integer, gen_ipaddr, gen_mac, gen_string
from nailgun import client
import pytest
from requests.exceptions import HTTPError

from robottelo.config import get_credentials
from robottelo.constants import DEFAULT_CV, DUMMY_BOOTC_FACTS, ENVIRONMENT
from robottelo.utils import datafactory


def update_smart_proxy(smart_proxy_location, smart_proxy):
    if smart_proxy_location.id not in [location.id for location in smart_proxy.location]:
        smart_proxy.location.append(smart_proxy_location)
        smart_proxy.update(['location'])


def test_positive_get_search(target_sat):
    """GET ``api/v2/hosts`` and specify the ``search`` parameter.

    :id: d63f87e5-66e6-4886-8b44-4129259493a6

    :expectedresults: HTTP 200 is returned, along with ``search`` term.

    :CaseImportance: Critical
    """
    query = gen_string('utf8', gen_integer(1, 100))
    response = client.get(
        target_sat.api.Host().path(),
        auth=get_credentials(),
        data={'search': query},
        verify=False,
    )
    assert response.status_code == http.client.OK
    assert response.json()['search'] == query


def test_positive_get_per_page(target_sat):
    """GET ``api/v2/hosts`` and specify the ``per_page`` parameter.

    :id: 9086f41c-b3b9-4af2-b6c4-46b80b4d1cfd

    :expectedresults: HTTP 200 is returned, along with per ``per_page``
        value.

    :CaseImportance: Critical
    """
    per_page = gen_integer(1, 1000)
    response = client.get(
        target_sat.api.Host().path(),
        auth=get_credentials(),
        data={'per_page': str(per_page)},
        verify=False,
    )
    assert response.status_code == http.client.OK
    assert response.json()['per_page'] == per_page


def test_positive_search_by_org_id(target_sat):
    """Search for host by specifying host's organization id

    :id: 56353f7c-b77e-4b6c-9ec3-51b58f9a18d8

    :customerscenario: true

    :expectedresults: The host was found, when the search with specified host's
        organization id was done

    :BZ: 1447958
    """
    host = target_sat.api.Host().create()
    # adding org id as GET parameter for correspondence with BZ
    query = target_sat.api.Host()
    query._meta['api_path'] += f'?organization_id={host.organization.id}'
    results = query.search()
    assert len(results) == 1
    assert results[0].id == host.id


@pytest.mark.parametrize('owner_type', ['User', 'Usergroup'])
def test_negative_create_with_owner_type(owner_type, target_sat):
    """Create a host and specify only ``owner_type``.

    :id: cdf9d16f-1c47-498a-be48-901355385dde

    :parametrized: yes

    :expectedresults: The host can't be created as ``owner`` is required.

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError) as error:
        target_sat.api.Host(owner_type=owner_type).create()
    assert str(422) in str(error)


@pytest.mark.parametrize('owner_type', ['User', 'Usergroup'])
def test_positive_update_owner_type(
    owner_type, module_org, module_location, module_user, module_target_sat
):
    """Update a host's ``owner_type``.

    :id: b72cd8ef-3a0b-4d2d-94f9-9b64908d699a

    :parametrized: yes

    :expectedresults: The host's ``owner_type`` attribute is updated as
        requested.

    :CaseImportance: Critical

    :BZ: 1210001
    """
    owners = {
        'User': module_user,
        'Usergroup': module_target_sat.api.UserGroup().create(),
    }
    host = module_target_sat.api.Host(organization=module_org, location=module_location).create()
    host.owner_type = owner_type
    host.owner = owners[owner_type]
    host = host.update(['owner_type', 'owner'])
    assert host.owner_type == owner_type
    assert host.owner.read() == owners[owner_type]


def test_positive_create_and_update_with_name(target_sat):
    """Create and update a host with different names and minimal input parameters

    :id: a7c0e8ec-3816-4092-88b1-0324cb271752

    :expectedresults: A host is created and updated with expected name

    :CaseImportance: Critical
    """
    name = gen_choice(datafactory.valid_hosts_list())
    host = target_sat.api.Host(name=name).create()
    assert host.name == f'{name}.{host.domain.read().name}'
    new_name = gen_choice(datafactory.valid_hosts_list())
    host.name = new_name
    host = host.update(['name'])
    assert host.name == f'{new_name}.{host.domain.read().name}'


def test_positive_create_and_update_with_ip(target_sat):
    """Create and update host with IP address specified

    :id: 3f266906-c509-42ce-9b20-def448bf8d86

    :expectedresults: A host is created and updated with static IP address

    :CaseImportance: Critical
    """
    ip_addr = gen_ipaddr()
    host = target_sat.api.Host(ip=ip_addr).create()
    assert host.ip == ip_addr
    new_ip_addr = gen_ipaddr()
    host.ip = new_ip_addr
    host = host.update(['ip'])
    assert host.ip == new_ip_addr


def test_positive_create_and_update_mac(target_sat):
    """Create host with MAC address and update it

    :id: 72e3b020-7347-4500-8669-c6ddf6dfd0b6

    :expectedresults: A host is created with MAC address updated with a new MAC address

    :CaseImportance: Critical
    """

    mac = gen_mac(multicast=False)
    host = target_sat.api.Host(mac=mac).create()
    assert host.mac == mac
    new_mac = gen_mac(multicast=False)
    host.mac = new_mac
    host = host.update(['mac'])
    assert host.mac == new_mac


def test_positive_create_and_update_with_hostgroup(
    module_org, module_location, module_lce, module_published_cv, module_target_sat
):
    """Create and update host with hostgroup specified

    :id: 8f9601f9-afd8-4a88-8f28-a5cbc996e805

    :expectedresults: A host is created and updated with expected hostgroup assigned
    """
    module_published_cv.version[0].promote(data={'environment_ids': module_lce.id, 'force': False})
    hostgroup = module_target_sat.api.HostGroup(
        location=[module_location], organization=[module_org]
    ).create()
    host = module_target_sat.api.Host(
        hostgroup=hostgroup,
        location=module_location,
        organization=module_org,
        content_facet_attributes={
            'content_view_id': module_published_cv.id,
            'lifecycle_environment_id': module_lce.id,
        },
    ).create()
    assert host.hostgroup.read().name == hostgroup.name
    new_hostgroup = module_target_sat.api.HostGroup(
        location=[host.location], organization=[host.organization]
    ).create()
    host.hostgroup = new_hostgroup
    host.content_facet_attributes = {
        'content_view_id': module_published_cv.id,
        'lifecycle_environment_id': module_lce.id,
    }
    host = host.update(['hostgroup', 'content_facet_attributes'])
    assert host.hostgroup.read().name == new_hostgroup.name


def test_positive_create_inherit_lce_cv(
    module_default_org_view, module_lce_library, module_org, module_target_sat
):
    """Create a host with hostgroup specified. Make sure host inherited
    hostgroup's lifecycle environment and content-view

    :id: 229cbdbc-838b-456c-bc6f-4ac895badfbc

    :expectedresults: Host's lifecycle environment and content view match
        the ones specified in hostgroup

    :BZ: 1391656
    """
    hostgroup = module_target_sat.api.HostGroup(
        content_view=module_default_org_view,
        lifecycle_environment=module_lce_library,
        organization=[module_org],
    ).create()
    host = module_target_sat.api.Host(hostgroup=hostgroup, organization=module_org).create()
    assert (
        host.content_facet_attributes['lifecycle_environment']['id']
        == hostgroup.lifecycle_environment.id
    )
    assert host.content_facet_attributes['content_view']['id'] == hostgroup.content_view.id


def test_positive_create_with_inherited_params(module_org, module_location, module_target_sat):
    """Create a new Host in organization and location with parameters

    :BZ: 1287223

    :id: 5e17e968-7fe2-4e5b-90ca-ae66f4e5307a

    :customerscenario: true

    :expectedresults: Host has inherited parameters from organization and
        location as well as global parameters

    :CaseImportance: High
    """
    org_param = module_target_sat.api.Parameter(organization=module_org).create()
    loc_param = module_target_sat.api.Parameter(location=module_location).create()
    host = module_target_sat.api.Host(location=module_location, organization=module_org).create()
    # get global parameters
    glob_param_list = {
        (param.name, param.value) for param in module_target_sat.api.CommonParameter().search()
    }
    # if there are no global parameters, create one
    if len(glob_param_list) == 0:
        param_name = gen_string('alpha')
        param_global_value = gen_string('numeric')
        module_target_sat.api.CommonParameter(name=param_name, value=param_global_value).create()
        glob_param_list = {
            (param.name, param.value) for param in module_target_sat.api.CommonParameter().search()
        }
    assert len(host.all_parameters) == 2 + len(glob_param_list)
    innerited_params = {(org_param.name, org_param.value), (loc_param.name, loc_param.value)}
    expected_params = innerited_params.union(glob_param_list)
    assert expected_params == {(param['name'], param['value']) for param in host.all_parameters}


def test_positive_create_and_update_with_puppet_proxy(
    session_puppet_enabled_sat, session_puppet_enabled_proxy
):
    """Create a host with puppet proxy specified and then create new host without specified
    puppet proxy and update the new host with the same puppet proxy

    :id: 9269d87b-abb9-48e0-b0d1-9b8e258e1ae3

    :expectedresults: Both hosts are associated with expected puppet proxy assigned

    :CaseImportance: Critical
    """
    # TODO Define the default capsule/SP port + URL on hosts.Capsule
    host = session_puppet_enabled_sat.api.Host(puppet_proxy=session_puppet_enabled_proxy).create()
    assert host.puppet_proxy.read().name == session_puppet_enabled_proxy.name
    new_host = session_puppet_enabled_sat.api.Host().create()
    new_host.puppet_proxy = session_puppet_enabled_proxy
    new_host = new_host.update(['puppet_proxy'])
    assert new_host.puppet_proxy.read().name == session_puppet_enabled_proxy.name


def test_positive_create_with_puppet_ca_proxy(
    session_puppet_enabled_sat, session_puppet_enabled_proxy
):
    """Create a host with puppet CA proxy specified and then create new host without specified
     puppet CA proxy and update the new host with the same puppet CA proxy

    :id: 1b73dd35-c2e8-44bd-b8f8-9e51428a6239

    :expectedresults: Both hosts are associated with expected puppet CA proxy assigned

    :CaseImportance: Critical
    """
    host = session_puppet_enabled_sat.api.Host(
        puppet_ca_proxy=session_puppet_enabled_proxy
    ).create()
    assert host.puppet_ca_proxy.read().name == session_puppet_enabled_proxy.name
    new_host = session_puppet_enabled_sat.api.Host().create()
    new_host.puppet_ca_proxy = session_puppet_enabled_proxy
    new_host = new_host.update(['puppet_ca_proxy'])
    assert new_host.puppet_ca_proxy.read().name == session_puppet_enabled_proxy.name


@pytest.mark.e2e
def test_positive_end_to_end_with_puppet_class(
    module_puppet_org,
    module_puppet_loc,
    module_env_search,
    module_puppet_classes,
    session_puppet_enabled_proxy,
    session_puppet_enabled_sat,
):
    """Create a host with associated puppet classes then remove it and update the host
    with same associated puppet classes

    :id: 2690d6b0-441b-44c5-b7d2-4093616e037e

    :BZ: 2046573

    :expectedresults: A host is created with expected puppet classes then puppet classes
        are removed and the host is updated with same puppet classes
    """
    update_smart_proxy(module_puppet_loc, session_puppet_enabled_proxy)
    host = session_puppet_enabled_sat.api.Host(
        organization=module_puppet_org,
        location=module_puppet_loc,
        environment=module_env_search,
        puppetclass=module_puppet_classes,
        puppet_proxy=session_puppet_enabled_proxy,
        puppet_ca_proxy=session_puppet_enabled_proxy,
    ).create()
    assert {puppet_class.id for puppet_class in host.puppetclass} == {
        puppet_class.id for puppet_class in module_puppet_classes
    }
    host.puppetclass = host.environment = host.puppet_ca_proxy = host.puppet_proxy = []
    host = host.update(['environment', 'puppetclass', 'puppet_ca_proxy', 'puppet_proxy'])
    assert len(host.puppetclass) == 0
    host.environment = module_env_search
    host.puppetclass = module_puppet_classes
    host.puppet_ca_proxy = session_puppet_enabled_proxy
    host.puppet_proxy = session_puppet_enabled_proxy
    host = host.update(['environment', 'puppetclass', 'puppet_ca_proxy', 'puppet_proxy'])
    assert {puppet_class.id for puppet_class in host.puppetclass} == {
        puppet_class.id for puppet_class in module_puppet_classes
    }


def test_positive_create_and_update_with_subnet(
    module_location, module_org, module_default_subnet, module_target_sat
):
    """Create and update a host with subnet specified

    :id: 9aa97aff-8439-4027-89ee-01c643fbf7d1

    :expectedresults: A host is created and updated with expected subnet assigned
    """
    host = module_target_sat.api.Host(
        location=module_location, organization=module_org, subnet=module_default_subnet
    ).create()
    assert host.subnet.read().name == module_default_subnet.name
    new_subnet = module_target_sat.api.Subnet(
        location=[module_location], organization=[module_org]
    ).create()
    host.subnet = new_subnet
    host = host.update(['subnet'])
    assert host.subnet.read().name == new_subnet.name
    # check that subnet values are included in the usage report
    if module_target_sat.network_type.has_ipv4:
        assert int(module_target_sat.get_reported_value('subnet_ipv4_count')) > 0
        assert int(module_target_sat.get_reported_value('hosts_with_ipv4only_interface_count')) > 0
        assert int(module_target_sat.get_reported_value('foreman_interfaces_ipv4only_count')) > 0
    if module_target_sat.network_type.has_ipv6:
        assert int(module_target_sat.get_reported_value('subnet_ipv6_count')) > 0
        assert int(module_target_sat.get_reported_value('hosts_with_ipv6only_interface_count')) > 0
        assert int(module_target_sat.get_reported_value('foreman_interfaces_ipv6only_count')) > 0


def test_positive_create_and_update_with_compresource(
    module_org, module_location, module_cr_libvirt, module_target_sat
):
    """Create and update a host with compute resource specified

    :id: 53069f2e-67a7-4d57-9846-acf6d8ce03cb

    :expectedresults: A host is created and updated with expected compute resource
        assigned
    """
    host = module_target_sat.api.Host(
        compute_resource=module_cr_libvirt, location=module_location, organization=module_org
    ).create()
    assert host.compute_resource.read().name == module_cr_libvirt.name
    new_compresource = module_target_sat.api.LibvirtComputeResource(
        location=[host.location], organization=[host.organization]
    ).create()
    host.compute_resource = new_compresource
    host = host.update(['compute_resource'])
    assert host.compute_resource.read().name == new_compresource.name


def test_positive_create_and_update_with_model(module_model, module_target_sat):
    """Create and update a host with model specified

    :id: 7a912a19-71e4-4843-87fd-bab98c156f4a

    :expectedresults: A host is created and updated with expected model assigned
    """
    host = module_target_sat.api.Host(model=module_model).create()
    assert host.model.read().name == module_model.name
    new_model = module_target_sat.api.Model().create()
    host.model = new_model
    host = host.update(['model'])
    assert host.model.read().name == new_model.name


def test_positive_create_and_update_with_user(
    module_org, module_location, module_user, module_target_sat
):
    """Create and update host with user specified

    :id: 72e20f8f-17dc-4e38-8ac1-d08df8758f56

    :expectedresults: A host is created and updated with expected user assigned
    """
    host = module_target_sat.api.Host(
        owner=module_user, owner_type='User', organization=module_org, location=module_location
    ).create()
    assert host.owner.read() == module_user
    new_user = module_target_sat.api.User(
        organization=[module_org], location=[module_location]
    ).create()
    host.owner = new_user
    host = host.update(['owner'])
    assert host.owner.read() == new_user


def test_positive_create_and_update_with_usergroup(
    module_org, module_location, function_role, module_target_sat
):
    """Create and update host with user group specified

    :id: 706e860c-8c05-4ddc-be20-0ecd9f0da813

    :expectedresults: A host is created and updated with expected user group assigned
    """
    user = module_target_sat.api.User(
        location=[module_location], organization=[module_org], role=[function_role]
    ).create()
    usergroup = module_target_sat.api.UserGroup(role=[function_role], user=[user]).create()
    host = module_target_sat.api.Host(
        location=module_location,
        organization=module_org,
        owner=usergroup,
        owner_type='Usergroup',
    ).create()
    assert host.owner.read().name == usergroup.name
    new_usergroup = module_target_sat.api.UserGroup(role=[function_role], user=[user]).create()
    host.owner = new_usergroup
    host = host.update(['owner'])
    assert host.owner.read().name == new_usergroup.name


@pytest.mark.parametrize('build', [True, False])
def test_positive_create_and_update_with_build_parameter(build, target_sat):
    """Create and update a host with 'build' parameter specified.
    Build parameter determines whether to enable the host for provisioning

    :id: de30cf62-5036-4247-a5f0-37dd2b4aae23

    :parametrized: yes

    :expectedresults: A host is created and updated with expected 'build' parameter
        value

    :CaseImportance: Critical
    """
    host = target_sat.api.Host(build=build).create()
    assert host.build == build
    host.build = not build
    host = host.update(['build'])
    assert host.build == (not build)


@pytest.mark.parametrize('enabled', [True, False], ids=['enabled', 'disabled'])
def test_positive_create_and_update_with_enabled_parameter(enabled, target_sat):
    """Create and update a host with 'enabled' parameter specified.
    Enabled parameter determines whether to include the host within
    Satellite 6 reporting

    :id: bd8d33f9-37de-4b8d-863e-9f73cd8dcec1

    :parametrized: yes

    :expectedresults: A host is created and updated with expected 'enabled' parameter
        value

    :CaseImportance: Critical
    """
    host = target_sat.api.Host(enabled=enabled).create()
    assert host.enabled == enabled
    host.enabled = not enabled
    host = host.update(['enabled'])
    assert host.enabled == (not enabled)


@pytest.mark.parametrize('managed', [True, False], ids=['managed', 'unmanaged'])
def test_positive_create_and_update_with_managed_parameter(managed, target_sat):
    """Create and update a host with managed parameter specified.
    Managed flag shows whether the host is managed or unmanaged and
    determines whether some extra parameters are required

    :id: 00dcfaed-6f54-4b6a-a022-9c97fb992324

    :parametrized: yes

    :expectedresults: A host is created and updated with expected managed parameter
        value

    :CaseImportance: Critical
    """
    host = target_sat.api.Host(managed=managed).create()
    assert host.managed == managed
    host.managed = not managed
    host = host.update(['managed'])
    assert host.managed == (not managed)


def test_positive_create_and_update_with_comment(target_sat):
    """Create and update a host with a comment

    :id: 9b78663f-139c-4d0b-9115-180624b0d41b

    :expectedresults: A host is created and updated with expected comment

    :CaseImportance: Critical
    """
    comment = gen_choice(list(datafactory.valid_data_list().values()))
    host = target_sat.api.Host(comment=comment).create()
    assert host.comment == comment
    new_comment = gen_choice(list(datafactory.valid_data_list().values()))
    host.comment = new_comment
    host = host.update(['comment'])
    assert host.comment == new_comment


def test_positive_create_and_update_with_compute_profile(module_compute_profile, module_target_sat):
    """Create and update a host with a compute profile specified

    :id: 94be25e8-035d-42c5-b1f3-3aa20030410d

    :expectedresults: A host is created and updated with expected compute profile
        assigned
    """
    host = module_target_sat.api.Host(compute_profile=module_compute_profile).create()
    assert host.compute_profile.read().name == module_compute_profile.name
    new_cprofile = module_target_sat.api.ComputeProfile().create()
    host.compute_profile = new_cprofile
    host = host.update(['compute_profile'])
    assert host.compute_profile.read().name == new_cprofile.name


def test_positive_create_and_update_with_content_view(
    module_org, module_location, module_default_org_view, module_lce_library, module_target_sat
):
    """Create and update host with a content view specified

    :id: 10f69c7a-088e-474c-b869-1ad12deda2ad

    :expectedresults: A host is created and updated with expected content view
    """
    host = module_target_sat.api.Host(
        organization=module_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': module_default_org_view.id,
            'lifecycle_environment_id': module_lce_library.id,
        },
    ).create()
    assert host.content_facet_attributes['content_view']['id'] == module_default_org_view.id
    assert host.content_facet_attributes['lifecycle_environment']['id'] == module_lce_library.id

    host.content_facet_attributes = {
        'content_view_id': module_default_org_view.id,
        'lifecycle_environment_id': module_lce_library.id,
    }
    host = host.update(['content_facet_attributes'])
    assert host.content_facet_attributes['content_view']['id'] == module_default_org_view.id
    assert host.content_facet_attributes['lifecycle_environment']['id'] == module_lce_library.id


@pytest.mark.e2e
def test_positive_end_to_end_with_host_parameters(module_org, module_location, module_target_sat):
    """Create a host with a host parameters specified
    then remove and update with the newly specified parameters

    :id: e3af6718-4016-4756-bbb0-e3c24ac1e340

    :expectedresults: A host is created with expected host parameters,
        parameters are removed and new parameters are updated

    :CaseImportance: Critical
    """
    parameters = [{'name': gen_string('alpha'), 'value': gen_string('alpha')}]
    host = module_target_sat.api.Host(
        organization=module_org,
        location=module_location,
        host_parameters_attributes=parameters,
    ).create()
    assert host.host_parameters_attributes[0]['name'] == parameters[0]['name']
    assert host.host_parameters_attributes[0]['value'] == parameters[0]['value']
    assert 'id' in host.host_parameters_attributes[0]

    parameters = []
    host.host_parameters_attributes = parameters
    host = host.update(['host_parameters_attributes'])
    assert host.host_parameters_attributes == []

    parameters = [{'name': gen_string('alpha'), 'value': gen_string('alpha')}]
    host.host_parameters_attributes = parameters
    host = host.update(['host_parameters_attributes'])
    assert host.host_parameters_attributes[0]['name'] == parameters[0]['name']
    assert host.host_parameters_attributes[0]['value'] == parameters[0]['value']
    assert 'id' in host.host_parameters_attributes[0]


@pytest.mark.e2e
def test_positive_end_to_end_with_image(
    module_org, module_location, module_cr_libvirt, module_libvirt_image, module_target_sat
):
    """Create a host with an image specified then remove it
    and update the host with the same image afterwards

    :id: 38b17b4d-d9d8-4ea1-aa0f-558496b990fc

    :expectedresults: A host is created with expected image, image is removed and
        host is updated with expected image
    """
    host = module_target_sat.api.Host(
        organization=module_org,
        location=module_location,
        compute_resource=module_cr_libvirt,
        image=module_libvirt_image,
    ).create()
    assert host.image.id == module_libvirt_image.id

    host.image = []
    host = host.update(['image'])
    assert host.image is None

    host.image = module_libvirt_image
    host = host.update(['image'])
    assert host.image.id == module_libvirt_image.id


@pytest.mark.parametrize('method', ['build', 'image'])
def test_positive_create_with_provision_method(
    method, module_org, module_location, module_cr_libvirt, module_target_sat
):
    """Create a host with provision method specified

    :id: c2243c30-f70a-4063-a4a4-f67b598a892b

    :parametrized: yes

    :expectedresults: A host is created with expected provision method

    :CaseImportance: Critical
    """
    # Compute resource is required for 'image' method
    host = module_target_sat.api.Host(
        organization=module_org,
        location=module_location,
        compute_resource=module_cr_libvirt,
        provision_method=method,
    ).create()
    assert host.provision_method == method


def test_positive_delete(target_sat):
    """Delete a host

    :id: ec725359-a75e-498c-9da8-f5abd2343dd3

    :expectedresults: Host is deleted

    :CaseImportance: Critical
    """
    host = target_sat.api.Host().create()
    host.delete()
    with pytest.raises(HTTPError):
        host.read()


def test_positive_create_and_update_domain(
    module_org, module_location, module_domain, module_target_sat
):
    """Create and update a host with a domain

    :id: 8ca9f67c-4c11-40f9-b434-4f200bad000f

    :expectedresults: A host is created and updated with expected domain
    """
    host = module_target_sat.api.Host(
        organization=module_org, location=module_location, domain=module_domain
    ).create()
    assert host.domain.read().name == module_domain.name

    new_domain = module_target_sat.api.Domain(
        organization=[module_org], location=[module_location]
    ).create()
    host.domain = new_domain
    host = host.update(['domain'])
    assert host.domain.read().name == new_domain.name


def test_positive_create_and_update_env(
    module_puppet_org, module_puppet_loc, module_puppet_environment, session_puppet_enabled_sat
):
    """Create and update a host with an environment

    :id: 87a08dbf-fd4c-4b6c-bf73-98ab70756fc6

    :expectedresults: A host is created and updated with expected environment
    """
    host = session_puppet_enabled_sat.api.Host(
        organization=module_puppet_org,
        location=module_puppet_loc,
        environment=module_puppet_environment,
    ).create()
    assert host.environment.read().name == module_puppet_environment.name

    new_env = session_puppet_enabled_sat.api.Environment(
        organization=[host.organization], location=[host.location]
    ).create()
    host.environment = new_env
    host = host.update(['environment'])
    assert host.environment.read().name == new_env.name


def test_positive_create_and_update_arch(module_architecture, module_target_sat):
    """Create and update a host with an architecture

    :id: 5f190b14-e6db-46e1-8cd1-e94e048e6a77

    :expectedresults: A host is created and updated with expected architecture
    """
    host = module_target_sat.api.Host(architecture=module_architecture).create()
    assert host.architecture.read().name == module_architecture.name

    new_arch = module_target_sat.api.Architecture(operatingsystem=[host.operatingsystem]).create()
    host.architecture = new_arch
    host = host.update(['architecture'])
    assert host.architecture.read().name == new_arch.name


def test_positive_create_and_update_os(module_os, module_target_sat):
    """Create and update a host with an operating system

    :id: 46edced1-8909-4066-b196-b8e22512341f

    :expectedresults: A host is created updated with expected operating system
    """
    host = module_target_sat.api.Host(operatingsystem=module_os).create()
    assert host.operatingsystem.read().name == module_os.name

    new_os = module_target_sat.api.OperatingSystem(
        architecture=[host.architecture], ptable=[host.ptable]
    ).create()
    medium = module_target_sat.api.Media(id=host.medium.id).read()
    medium.operatingsystem.append(new_os)
    medium.update(['operatingsystem'])
    host.operatingsystem = new_os
    host = host.update(['operatingsystem'])
    assert host.operatingsystem.read().name == new_os.name


def test_positive_create_and_update_medium(module_org, module_location, module_target_sat):
    """Create and update a host with a medium

    :id: d81cb65c-48b3-4ce3-971e-51b9dd123697

    :expectedresults: A host is created and updated with expected medium
    """
    medium = module_target_sat.api.Media(
        organization=[module_org], location=[module_location]
    ).create()
    host = module_target_sat.api.Host(medium=medium).create()
    assert host.medium.read().name == medium.name

    new_medium = module_target_sat.api.Media(
        operatingsystem=[host.operatingsystem],
        location=[host.location],
        organization=[host.organization],
    ).create()
    new_medium.operatingsystem.append(host.operatingsystem)
    new_medium.update(['operatingsystem'])
    host.medium = new_medium
    host = host.update(['medium'])
    assert host.medium.read().name == new_medium.name


def test_negative_update_name(module_host):
    """Attempt to update a host with invalid or empty name

    :id: 1c46b44c-a2ea-43a6-b4d9-244101b081e8

    :expectedresults: A host is not updated

    :CaseImportance: Critical
    """
    new_name = gen_choice(datafactory.invalid_values_list())
    host = module_host
    host.name = new_name
    with pytest.raises(HTTPError):
        host.update(['name'])
    assert host.read().name != f'{new_name}.{host.domain.read().name}'.lower()


def test_negative_update_mac(module_host):
    """Attempt to update a host with invalid or empty MAC address

    :id: 1954ea4e-e0c2-475f-af67-557e91ebc1e2

    :expectedresults: A host is not updated

    :CaseImportance: Critical
    """
    new_mac = gen_choice(datafactory.invalid_values_list())
    host = module_host
    host.mac = new_mac
    with pytest.raises(HTTPError):
        host.update(['mac'])
    assert host.read().mac != new_mac


def test_negative_update_arch(module_architecture, module_target_sat):
    """Attempt to update a host with an architecture, which does not belong
    to host's operating system

    :id: 07b9c0e7-f02b-4aff-99ae-5c203255aba1

    :expectedresults: A host is not updated
    """
    host = module_target_sat.api.Host().create()
    host.architecture = module_architecture
    with pytest.raises(HTTPError):
        host = host.update(['architecture'])
    assert host.read().architecture.read().name != module_architecture.name


def test_negative_update_os(target_sat):
    """Attempt to update a host with an operating system, which is not
    associated with host's medium

    :id: 40e79f73-6356-4d61-9806-7ade2f4f8829

    :expectedresults: A host is not updated
    """
    host = target_sat.api.Host().create()
    new_os = target_sat.api.OperatingSystem(
        architecture=[host.architecture], ptable=[host.ptable]
    ).create()
    host.operatingsystem = new_os
    with pytest.raises(HTTPError):
        host = host.update(['operatingsystem'])
    assert host.read().operatingsystem.read().name != new_os.name


def test_positive_read_content_source_id(
    module_org, module_location, module_lce, module_published_cv, target_sat
):
    """Read the host content_source_id attribute from the read request
    response

    :id: 0a7fd8d4-1ea8-4b21-8c46-10579644fd11

    :customerscenario: true

    :expectedresults: content_source_id is present in GET host request
        response

    :BZ: 1339613, 1488130
    """
    proxy = target_sat.api.SmartProxy().search(query={'url': f'{target_sat.url}:9090'})[0].read()
    module_published_cv.version[0].promote(data={'environment_ids': module_lce.id, 'force': False})
    host = target_sat.api.Host(
        organization=module_org,
        location=module_location,
        content_facet_attributes={
            'content_source_id': proxy.id,
            'content_view_id': module_published_cv.id,
            'lifecycle_environment_id': module_lce.id,
        },
    ).create()
    content_facet_attributes = host.content_facet_attributes
    assert content_facet_attributes is not None
    content_source_id = content_facet_attributes.get('content_source_id')
    assert content_source_id is not None
    assert content_source_id == proxy.id


def test_positive_update_content_source_id(
    module_org, module_location, module_lce, module_published_cv, target_sat
):
    """Read the host content_source_id attribute from the update request
    response

    :id: d47214d2-a54c-4385-abfb-a0607ecb6ec7

    :customerscenario: true

    :expectedresults: content_source_id is present in PUT host request
        response

    :BZ: 1339613, 1488130
    """
    proxy = target_sat.api.SmartProxy().search(query={'url': f'{target_sat.url}:9090'})[0]
    module_published_cv.version[0].promote(data={'environment_ids': module_lce.id, 'force': False})
    host = target_sat.api.Host(
        organization=module_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': module_published_cv.id,
            'lifecycle_environment_id': module_lce.id,
        },
    ).create()
    host.content_facet_attributes['content_source_id'] = proxy.id
    # we need to ensure that content_source_id is returned by PUT request,
    # we will use entity update_json as entity update method will invoke
    # read method after PUT request completion
    response = host.update_json(['content_facet_attributes'])
    content_facet_attributes = response.get('content_facet_attributes')
    assert content_facet_attributes is not None
    content_source_id = content_facet_attributes.get('content_source_id')
    assert content_source_id is not None
    assert content_source_id == proxy.id


@pytest.mark.upgrade
def test_positive_read_enc_information(
    module_puppet_org,
    module_puppet_loc,
    module_env_search,
    module_puppet_classes,
    module_lce_library,
    session_puppet_enabled_proxy,
    session_puppet_enabled_sat,
):
    """Attempt to read host ENC information

    :id: 0d5047ab-2686-43de-8f04-cfe12b62eebf

    :customerscenario: true

    :expectedresults: host ENC information read successfully

    :BZ: 1362372
    """
    lce = (
        session_puppet_enabled_sat.api.LifecycleEnvironment()
        .search(query={'search': f'name={ENVIRONMENT} and organization_id={module_puppet_org.id}'})[
            0
        ]
        .read()
    )
    cv = session_puppet_enabled_sat.api.ContentView(
        organization=module_puppet_org, name=DEFAULT_CV
    ).search()[0]
    update_smart_proxy(module_puppet_loc, session_puppet_enabled_proxy)
    # create 2 parameters
    host_parameters_attributes = []
    for _ in range(2):
        host_parameters_attributes.append(
            dict(name=gen_string('alpha'), value=gen_string('alphanumeric'))
        )
    host = session_puppet_enabled_sat.api.Host(
        organization=module_puppet_org,
        location=module_puppet_loc,
        environment=module_env_search,
        puppetclass=module_puppet_classes,
        content_facet_attributes={
            'content_view_id': cv.id,
            'lifecycle_environment_id': lce.id,
        },
        host_parameters_attributes=host_parameters_attributes,
        puppet_proxy=session_puppet_enabled_proxy,
        puppet_ca_proxy=session_puppet_enabled_proxy,
    ).create()
    host_enc_info = host.enc()
    assert {puppet_class.name for puppet_class in module_puppet_classes} == set(
        host_enc_info['data']['classes']
    )
    assert host_enc_info['data']['environment'] == module_env_search.name
    assert 'parameters' in host_enc_info['data']
    host_enc_parameters = host_enc_info['data']['parameters']
    assert host_enc_parameters['organization'] == module_puppet_org.name
    assert host_enc_parameters['location'] == module_puppet_loc.name
    assert host_enc_parameters['content_view'] == cv.label
    assert host_enc_parameters['lifecycle_environment'] == module_lce_library.name
    for param in host_parameters_attributes:
        assert param['name'] in host_enc_parameters
        assert host_enc_parameters[param['name']] == param['value']


@pytest.mark.e2e
@pytest.mark.no_containers
def test_positive_bootc_api_actions(target_sat, bootc_host, function_ak_with_cv, function_org):
    """Register a bootc host and validate API information

    :id: b94ab231-0dd8-4e47-a96b-972c5ee55f4d

    :expectedresults: Upon registering a Bootc host, the API returns correct information across multiple endpoints

    :CaseComponent:Hosts-Content

    :Verifies:SAT-27168, SAT-27170, SAT-27173

    :CaseImportance: Critical
    """
    bootc_dummy_info = json.loads(DUMMY_BOOTC_FACTS)
    assert bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status == 0
    assert bootc_host.subscribed
    # Testing bootc info from content_facet_attributes
    bootc_host = target_sat.api.Host().search(query={'search': f'name={bootc_host.hostname}'})[0]
    assert (
        bootc_host.content_facet_attributes['bootc_booted_image']
        == bootc_dummy_info['bootc.booted.image']
    )
    assert (
        bootc_host.content_facet_attributes['bootc_booted_digest']
        == bootc_dummy_info['bootc.booted.digest']
    )
    assert (
        bootc_host.content_facet_attributes['bootc_rollback_image']
        == bootc_dummy_info['bootc.rollback.image']
    )
    assert (
        bootc_host.content_facet_attributes['bootc_rollback_digest']
        == bootc_dummy_info['bootc.rollback.digest']
    )
    # Testing bootc info from hosts/bootc_images
    bootc_image_info = target_sat.api.Host().get_bootc_images()['results'][0]
    assert bootc_image_info['bootc_booted_image'] == bootc_dummy_info['bootc.booted.image']
    assert (
        bootc_image_info['digests'][0]['bootc_booted_digest']
        == bootc_dummy_info['bootc.booted.digest']
    )
    assert bootc_image_info['digests'][0]['host_count'] > 0

    # Testing bootc image is correctly included in the usage report
    os = bootc_host.operatingsystem.read_json()
    assert (
        int(target_sat.get_reported_value(f'image_mode_hosts_by_os_count|{os["family"]}')) == 1
    ), "host not included in usage report"


@pytest.mark.stubbed
def test_positive_add_future_subscription():
    """Attempt to add a future-dated subscription to a content host.

    :id: 603bb8eb-3435-4259-a036-400f2767de66

    :steps:

        1. Import a manifest with a future-dated subscription
        2. Add the subscription to the content host

    :expectedresults: The future-dated subscription was added to the host
    """


@pytest.mark.upgrade
@pytest.mark.stubbed
def test_positive_add_future_subscription_with_ak():
    """Register a content host with an activation key that has a
    future-dated subscription.

    :id: f5286a44-0891-4605-8a6f-787f4754b3c0

    :steps:

        1. Import a manifest with a future-dated subscription
        2. Add the subscription to an activation key
        3. Register a new content host with the activation key

    :expectedresults: The host was registered and future subscription added
    """


@pytest.mark.stubbed
def test_negative_auto_attach_future_subscription():
    """Run auto-attach on a content host, with a current and future-dated
    subscription.

    :id: f4a6feec-baf8-40c6-acb3-474b34419a62

    :steps:

        1. Import a manifest with a future-dated and current subscription
        2. Register a content host to the organization
        3. Run auto-attach on the content host

    :expectedresults: Only the current subscription was added to the host
    """


@pytest.mark.stubbed
def test_positive_create_baremetal_with_bios():
    """Create a new Host from provided MAC address

    :id: 9d74ed70-3197-4825-bf96-21eeb4a765f9

    :setup: Create a PXE-based VM with BIOS boot mode (outside of
        Satellite).

    :steps: Create a new host using 'BareMetal' option and MAC address of
        the pre-created VM

    :expectedresults: Host is created

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_create_baremetal_with_uefi():
    """Create a new Host from provided MAC address

    :id: 9b852c4d-a94f-4ba9-b666-ea4718320a42

    :setup: Create a PXE-based VM with UEFI boot mode (outside of
        Satellite).

    :steps: Create a new host using 'BareMetal' option and MAC address of
        the pre-created VM

    :expectedresults: Host is created

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_verify_files_with_pxegrub_uefi():
    """Provision a new Host and verify the tftp and dhcpd file
    structure is correct

    :id: 0c51c8ad-858c-44e1-8b14-8e0c52c29da1

    :steps:

        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS
           and PXE loader set to Grub UEFI
        3. Build the host

    :expectedresults: Verify [/var/lib/tftpboot/] contains the following
        dir/file structure:

            grub/bootia32.efi
            grtest_positive_verify_files_with_pxegrub_uefiub/bootx64.efi
            grub/01-AA-BB-CC-DD-EE-FF
            grub/efidefault
            grub/shim.efi

        And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_verify_files_with_pxegrub_uefi_secureboot():
    """Provision a new Host and verify the tftp and dhcpd file structure is
    correct

    :id: ac4d535f-09bb-49db-b38b-90f9bad5fa19

    :steps:

        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS
           and PXE loader set to Grub UEFI SecureBoot
        3. Build the host

    :expectedresults: Verify [/var/lib/tftpboot/] contains the following
        dir/file structure:

            grub/bootia32.efi
            grub/bootx64.efi
            grub/01-AA-BB-CC-DD-EE-FF
            grub/efidefault
            grub/shim.efi

        And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

    :CaseAutomation: NotAutomated

    :CaseComponent: TFTP

    :Team: Rocket
    """


@pytest.mark.stubbed
def test_positive_verify_files_with_pxegrub2_uefi():
    """Provision a new UEFI Host and verify the tftp and dhcpd file
    structure is correct

    :id: fb951256-e173-4c2a-a812-92db80443cec

    :steps:
        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS
           and PXE loader set to Grub2 UEFI
        3. Build the host

    :expectedresults: Verify [/var/lib/tftpboot/] contains the following
        dir/file structure:

            pxegrub2
            grub2/grub.cfg-01-aa-bb-cc-dd-ee-ff
            grub2/grub.cfg
            grub2/grubx32.efi
            grub2/grubx64.efi
            grub/shim.efi

        And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

    :CaseAutomation: NotAutomated

    :CaseComponent: TFTP

    :Team: Rocket
    """


@pytest.mark.stubbed
def test_positive_verify_files_with_pxegrub2_uefi_secureboot():
    """Provision a new UEFI Host and verify the tftp and dhcpd file
    structure is correct

    :id: c0ea18df-d8c0-403a-b053-f5e500f8e3a3

    :steps:
        1. Associate a pxegrub-type provisioning template with the os
        2. Create new host (can be fictive bare metal) with the above OS
           and PXE loader set to Grub2 UEFI SecureBoot
        3. Build the host

    :expectedresults: Verify [/var/lib/tftpboot/] contains the following
        dir/file structure:

            pxegrub2
            grub2/grub.cfg-01-aa-bb-cc-dd-ee-ff
            grub2/grub.cfg
            grub2/grubx32.efi
            grub2/grubx64.efi
            grub/shim.efi

        And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

    :CaseAutomation: NotAutomated

    :CaseComponent: TFTP

    :Team: Rocket
    """


def test_positive_read_puppet_proxy_name(session_puppet_enabled_sat, session_puppet_enabled_proxy):
    """Read a hostgroup created with puppet proxy and inspect server's
    response

    :id: 8825462e-f1dc-4054-b7fb-69c2b10722a2

    :expectedresults: Field 'puppet_proxy_name' is returned

    :BZ: 1371900

    :CaseImportance: Critical
    """
    host = (
        session_puppet_enabled_sat.api.Host(puppet_proxy=session_puppet_enabled_proxy)
        .create()
        .read_json()
    )
    assert 'puppet_proxy_name' in host
    assert session_puppet_enabled_proxy.name == host['puppet_proxy_name']


def test_positive_read_puppet_ca_proxy_name(
    session_puppet_enabled_sat, session_puppet_enabled_proxy
):
    """Read a hostgroup created with puppet ca proxy and inspect server's
    response

    :id: 8941395f-8040-4705-a981-5da21c47efd1

    :expectedresults: Field 'puppet_ca_proxy_name' is returned

    :BZ: 1371900

    :CaseImportance: Critical
    """
    host = (
        session_puppet_enabled_sat.api.Host(puppet_ca_proxy=session_puppet_enabled_proxy)
        .create()
        .read_json()
    )
    assert 'puppet_ca_proxy_name' in host
    assert session_puppet_enabled_proxy.name == host['puppet_ca_proxy_name']


def test_positive_list_hosts_thin_all(module_target_sat):
    """List hosts with thin=true and per_page=all

    :id: 00b7e603-aed5-4b19-bfec-1a179fad6743

    :expectedresults: Hosts listed without ISE

    :BZ: 1969263, 1644750

    :customerscenario: true
    """
    hosts = module_target_sat.api.Host().search(query={'thin': 'true', 'per_page': 'all'})
    assert module_target_sat.hostname in [host.name for host in hosts]
    keys = dir(hosts[0])
    assert 'id' in keys
    assert 'name' in keys
    # Can't check for only id and name being present because the framework adds
    # some data the API doesn't actually return (currently, it adds empty Environment).
    # Instead, check for some data to be missing, as opposed to non-thin.
    assert 'domain' not in keys
    assert 'ip' not in keys
    assert 'architecture' not in keys


class TestHostInterface:
    """Tests for Host Interfaces"""

    @pytest.mark.e2e
    def test_positive_create_end_to_end(self, module_host, target_sat):
        """Create update and delete an interface with different names and minimal input
        parameters

        :id: a45ee576-bec6-47a6-a018-a00e555eb2ad

        :expectedresults: An interface is created updated and deleted

        :CaseImportance: Critical
        """
        name = gen_choice(datafactory.valid_interfaces_list())
        interface = target_sat.api.Interface(host=module_host, name=name).create()
        assert interface.name == name
        new_name = gen_choice(datafactory.valid_interfaces_list())
        interface.name = new_name
        interface = interface.update(['name'])
        assert interface.name == new_name
        interface.delete()
        with pytest.raises(HTTPError):
            interface.read()

    def test_negative_end_to_end(self, module_host, target_sat):
        """Attempt to create and update an interface with different invalid entries as names
        (>255 chars, unsupported string types), at the end attempt to remove primary interface

        :id: 6fae26d8-8f62-41ba-a1cc-0185137ef70f

        :expectedresults: An interface is not created, not updated
            and primary interface is not deleted

        :CaseImportance: Critical
        """
        name = gen_choice(datafactory.invalid_interfaces_list())
        with pytest.raises(HTTPError) as error:
            target_sat.api.Interface(host=module_host, name=name).create()
        assert str(422) in str(error)
        interface = target_sat.api.Interface(host=module_host).create()
        interface.name = name
        with pytest.raises(HTTPError) as error:
            interface.update(['name'])
        assert interface.read().name != name
        assert str(422) in str(error)

        primary_interface = next(
            interface for interface in module_host.interface if interface.read().primary
        )
        with pytest.raises(HTTPError):
            primary_interface.delete()
        try:
            primary_interface.read()
        except HTTPError:
            pytest.fail("HTTPError 404 raised unexpectedly!")

    @pytest.mark.upgrade
    def test_positive_delete_and_check_host(self, target_sat):
        """Delete host's interface (not primary) and make sure the host was not
        accidentally removed altogether with the interface

        :BZ: 1285669

        :id: 3b3e9b3f-cfb2-433f-bd1f-0a8e1d9f0b34

        :expectedresults: An interface was successfully deleted, host was not
            deleted

        :CaseImportance: Critical
        """
        host = target_sat.api.Host().create()
        interface = target_sat.api.Interface(host=host, primary=False).create()
        interface.delete()
        with pytest.raises(HTTPError):
            interface.read()
        try:
            host.read()
        except HTTPError:
            pytest.fail("HTTPError 404 raised unexpectedly!")


class TestHostBulkAction:
    """Tests for host bulk actions."""

    def test_positive_bulk_destroy(self, module_org, module_target_sat):
        """Destroy multiple hosts make sure that hosts were removed,
        or were not removed when host is excluded from the list.

        :id: 06d63376-8bf6-11eb-ab9f-98fa9b6ecd5a

        :expectedresults: Included list of hosts,
            that are not part of excluded list of host, are removed.

        :CaseImportance: Medium
        """

        host_ids = []
        for _ in range(3):
            name = gen_choice(datafactory.valid_hosts_list())
            host = module_target_sat.api.Host(name=name, organization=module_org).create()
            host_ids.append(host.id)

        module_target_sat.api.Host().bulk_destroy(
            data={
                'organization_id': module_org.id,
                'included': {'ids': host_ids},
                'excluded': {'ids': host_ids[:-1]},
            }
        )
        for host_id in host_ids[:-1]:
            result = module_target_sat.api.Host(id=host_id).read()
            assert result.id == host_id

        with pytest.raises(HTTPError):
            module_target_sat.api.Host(id=host_ids[-1]).read()

        module_target_sat.api.Host().bulk_destroy(
            data={'organization_id': module_org.id, 'included': {'ids': host_ids[:-1]}}
        )
        for host_id in host_ids[:-1]:
            with pytest.raises(HTTPError):
                module_target_sat.api.Host(id=host_id).read()
