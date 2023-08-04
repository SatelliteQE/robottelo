"""Test for Compute Resource UI

:Requirement: ComputeResources GCE

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-GCE

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json
import random

import pytest
from fauxfactory import gen_string
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import COMPUTE_PROFILE_SMALL
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import GCE_EXTERNAL_IP_DEFAULT
from robottelo.constants import GCE_MACHINE_TYPE_DEFAULT
from robottelo.constants import GCE_NETWORK_DEFAULT


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skip_if_not_set('http_proxy', 'gce')
def test_positive_default_end_to_end_with_custom_profile(
    session, sat_gce_org, sat_gce_loc, gce_cert, sat_gce
):
    """Create GCE compute resource with default properties and apply it's basic functionality.

    :id: 59ffd83e-a984-4c22-b91b-cad055b4fbd7

    :Steps:

        1. Create an GCE compute resource with default properties.
        2. Update the compute resource name and add new taxonomies.
        3. Associate compute profile with custom properties to GCE compute resource
        4. Delete the compute resource.

    :expectedresults: The GCE compute resource is created, updated, compute profile associated and
        deleted.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    cr_description = gen_string('alpha')
    new_org = sat_gce.api.Organization().create()
    new_loc = sat_gce.api.Location().create()
    json_key = json.dumps(gce_cert, indent=2)
    http_proxy = sat_gce.api.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.auth_proxy_url,
        username=settings.http_proxy.username,
        password=settings.http_proxy.password,
        organization=[sat_gce_org.id],
        location=[sat_gce_loc.id],
    ).create()
    with sat_gce.ui_session() as session:
        session.organization.select(org_name=sat_gce_org.name)
        session.location.select(loc_name=sat_gce_loc.name)
        # Compute Resource Create and Assertions
        session.computeresource.create(
            {
                'name': cr_name,
                'description': cr_description,
                'provider': FOREMAN_PROVIDERS['google'],
                'provider_content.http_proxy.value': http_proxy.name,
                'provider_content.json_key': json_key,
                'provider_content.zone.value': settings.gce.zone,
                'organizations.resources.assigned': [sat_gce_org.name],
                'locations.resources.assigned': [sat_gce_loc.name],
            }
        )
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['provider_content']['zone']['value']
        assert cr_values['provider_content']['http_proxy']['value'] == http_proxy.name
        assert cr_values['organizations']['resources']['assigned'] == [sat_gce_org.name]
        assert cr_values['locations']['resources']['assigned'] == [sat_gce_loc.name]
        # Compute Resource Edit/Updates and Assertions
        session.computeresource.edit(
            cr_name,
            {
                'name': new_cr_name,
                'organizations.resources.assigned': [new_org.name],
                'locations.resources.assigned': [new_loc.name],
            },
        )
        assert not session.computeresource.search(cr_name)
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert set(cr_values['organizations']['resources']['assigned']) == {
            sat_gce_org.name,
            new_org.name,
        }
        assert set(cr_values['locations']['resources']['assigned']) == {
            sat_gce_loc.name,
            new_loc.name,
        }

        # Compute Profile edit/updates and Assertions
        session.computeresource.update_computeprofile(
            new_cr_name,
            COMPUTE_PROFILE_SMALL,
            {
                'provider_content.machine_type': GCE_MACHINE_TYPE_DEFAULT,
                'provider_content.network': GCE_NETWORK_DEFAULT,
                'provider_content.external_ip': GCE_EXTERNAL_IP_DEFAULT,
                'provider_content.default_disk_size': '15',
            },
        )
        cr_profile_values = session.computeresource.read_computeprofile(
            new_cr_name, COMPUTE_PROFILE_SMALL
        )
        assert cr_profile_values['breadcrumb'] == f'Edit {COMPUTE_PROFILE_SMALL}'
        assert cr_profile_values['compute_profile'] == COMPUTE_PROFILE_SMALL
        assert (
            cr_profile_values['compute_resource']
            == f'{new_cr_name} ({settings.gce.zone}-{FOREMAN_PROVIDERS["google"]})'
        )
        assert cr_profile_values['provider_content']['machine_type'] == GCE_MACHINE_TYPE_DEFAULT
        assert cr_profile_values['provider_content']['network'] == GCE_NETWORK_DEFAULT

        assert cr_profile_values['provider_content']['external_ip'] == GCE_EXTERNAL_IP_DEFAULT

        assert cr_profile_values['provider_content']['default_disk_size'] == '15'

        # Compute Resource Delete and Assertion
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)


@pytest.mark.tier4
@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('gce')
@pytest.mark.parametrize('sat_gce', ['sat', 'puppet_sat'], indirect=True)
def test_positive_gce_provision_end_to_end(
    session,
    request,
    sat_gce,
    sat_gce_org,
    sat_gce_loc,
    sat_gce_default_os,
    gce_domain,
    gce_hostgroup_resource_image,
    googleclient,
    gce_setting_update,
):
    """Provision Host on GCE compute resource

    :id: 33542680-c23e-4d21-9cde-d0dca85b8eca

    :expectedresults: Host is provisioned successfully

    :CaseLevel: System
    """
    name = f'test{gen_string("alpha", 4).lower()}'
    hostname = f'{name}.{gce_domain.name}'
    gceapi_vmname = hostname.replace('.', '-')
    root_pwd = gen_string('alpha', 15)
    storage = [{'size': 20}]
    with sat_gce.ui_session() as session:
        session.organization.select(org_name=sat_gce_org.name)
        session.location.select(loc_name=sat_gce_loc.name)
        # Provision GCE Host
        with sat_gce.skip_yum_update_during_provisioning(template='Kickstart default finish'):
            session.host.create(
                {
                    'host.name': name,
                    'host.hostgroup': gce_hostgroup_resource_image.name,
                    'provider_content.virtual_machine.machine_type': 'g1-small',
                    'provider_content.virtual_machine.external_ip': True,
                    'provider_content.virtual_machine.network': 'default',
                    'provider_content.virtual_machine.storage': storage,
                    'operating_system.operating_system': sat_gce_default_os.title,
                    'operating_system.image': 'autogce_img',
                    'operating_system.root_password': root_pwd,
                }
            )
            wait_for(
                lambda: sat_gce.api.Host()
                .search(query={'search': f'name={hostname}'})[0]
                .build_status_label
                != 'Pending installation',
                timeout=600,
                delay=15,
                silent_failure=True,
                handle_exception=True,
            )
            # 1. Host Creation Assertions
            # 1.1 UI based Assertions
            host_info = session.host.get_details(hostname)
            assert session.host.search(hostname)[0]['Name'] == hostname
            assert host_info['properties']['properties_table']['Build'] == 'Installed clear'
            # 1.2 GCE Backend Assertions
            gceapi_vm = googleclient.get_vm(gceapi_vmname)
            assert gceapi_vm.is_running
            assert gceapi_vm
            assert gceapi_vm.name == gceapi_vmname
            assert gceapi_vm.zone == settings.gce.zone
            assert gceapi_vm.ip == host_info['properties']['properties_table']['IP Address']
            assert 'g1-small' in gceapi_vm.raw['machineType'].split('/')[-1]
            assert 'default' in gceapi_vm.raw['networkInterfaces'][0]['network'].split('/')[-1]
            # 2. Host Deletion Assertions
            session.host.delete(hostname)
            assert not sat_gce.api.Host().search(query={'search': f'name="{hostname}"'})
            # 2.2 GCE Backend Assertions
            assert gceapi_vm.is_stopping or gceapi_vm.is_stopped

    @request.addfinalizer
    def _finalize():
        gcehost = sat_gce.api.Host().search(query={'search': f'name={hostname}'})
        if gcehost:
            gcehost[0].delete()
        googleclient.disconnect()


@pytest.mark.tier4
@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('gce')
@pytest.mark.parametrize('sat_gce', ['sat', 'puppet_sat'], indirect=True)
def test_positive_gce_cloudinit_provision_end_to_end(
    session,
    request,
    sat_gce,
    sat_gce_org,
    sat_gce_loc,
    sat_gce_default_os,
    gce_domain,
    gce_hostgroup_resource_image,
    googleclient,
    gce_setting_update,
):
    """Provision Host on GCE compute resource

    :id: 80a86cbd-5a26-41df-98b7-1f5e5af837d8

    :expectedresults: Host is provisioned successfully

    :CaseLevel: System
    """
    name = f'test{gen_string("alpha", 4).lower()}'
    hostname = f'{name}.{gce_domain.name}'
    gceapi_vmname = hostname.replace('.', '-')
    storage = [{'size': 20}]
    root_pwd = gen_string('alpha', random.choice([8, 15]))
    with sat_gce.ui_session() as session:
        session.organization.select(org_name=sat_gce_org.name)
        session.location.select(loc_name=sat_gce_loc.name)
        # Provision GCE Host

        with sat_gce.skip_yum_update_during_provisioning(template='Kickstart default user data'):
            session.host.create(
                {
                    'host.name': name,
                    'host.hostgroup': gce_hostgroup_resource_image.name,
                    'provider_content.virtual_machine.machine_type': 'g1-small',
                    'provider_content.virtual_machine.external_ip': True,
                    'provider_content.virtual_machine.network': 'default',
                    'provider_content.virtual_machine.storage': storage,
                    'operating_system.operating_system': sat_gce_default_os.title,
                    'operating_system.image': 'autogce_img_cinit',
                    'operating_system.root_password': root_pwd,
                }
            )
            # 1. Host Creation Assertions
            # 1.1 UI based Assertions
            host_info = session.host.get_details(hostname)
            assert session.host.search(hostname)[0]['Name'] == hostname
            assert (
                host_info['properties']['properties_table']['Build'] == 'Pending installation clear'
            )
            # 1.2 GCE Backend Assertions
            gceapi_vm = googleclient.get_vm(gceapi_vmname)
            assert gceapi_vm
            assert gceapi_vm.is_running
            assert gceapi_vm.name == gceapi_vmname
            assert gceapi_vm.zone == settings.gce.zone
            assert gceapi_vm.ip == host_info['properties']['properties_table']['IP Address']
            assert 'g1-small' in gceapi_vm.raw['machineType'].split('/')[-1]
            assert 'default' in gceapi_vm.raw['networkInterfaces'][0]['network'].split('/')[-1]
            # 2. Host Deletion Assertions
            session.host.delete(hostname)
            assert not sat_gce.api.Host().search(query={'search': f'name="{hostname}"'})
            # 2.2 GCE Backend Assertions
            assert gceapi_vm.is_stopping or gceapi_vm.is_stopped

    @request.addfinalizer
    def _finalize():
        gcehost = sat_gce.api.Host().search(query={'search': f'name={hostname}'})
        if gcehost:
            gcehost[0].delete()
        googleclient.disconnect()
