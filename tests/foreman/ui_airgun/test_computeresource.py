"""Test for Compute Resource UI

:Requirement: Computeresource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import requests
from nailgun import entities

from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, parametrize, run_in_one_thread, tier2
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS


@fixture(scope='module')
def module_ca_cert():
    return (
        None
        if settings.rhev.ca_cert is None
        else requests.get(settings.rhev.ca_cert).content.decode()
    )


@fixture(scope='module')
def rhev_data():
    return {
        'rhev_url': settings.rhev.hostname,
        'username': settings.rhev.username,
        'password': settings.rhev.password,
        'datacenter': settings.rhev.datacenter,
        'vm_name': settings.rhev.vm_name,
    }


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@tier2
@parametrize('version', [True, False])
def test_positive_add_resource(session, module_ca_cert, rhev_data, version):
    """Create new RHEV Compute Resource using APIv3/APIv4 and autoloaded cert

    :id: f75e994a-6da1-40a3-9685-42387388b300

    :expectedresults: resource created successfully and has expected protocol
        version

    :CaseLevel: Integration
    """
    # Our RHEV testing uses custom cert which we specify manually.
    # That means we're not testing the ability to automatically fill a
    # self-signed certificate upon clicking Load Datacenters / Test Connection.
    name = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': name,
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_data['rhev_url'],
            'provider_content.user': rhev_data['username'],
            'provider_content.password': rhev_data['password'],
            'provider_content.api4': version,
            'provider_content.datacenter.value': rhev_data['datacenter'],
            'provider_content.certification_authorities': module_ca_cert
        })
        resource_values = session.computeresource.read(name)
        assert resource_values['name'] == name
        assert resource_values['provider_content']['api4'] == version


@tier2
@parametrize('version', [True, False])
def test_positive_edit_resource_description(
        session, module_ca_cert, rhev_data, version):
    """Edit RHEV Compute Resource with another description

    :id: f75544b1-3943-4cc6-98d1-f2d0fbe7244c

    :expectedresults: resource updated successfully and has new description

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    description = gen_string('alpha')
    new_description = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': name,
            'description': description,
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_data['rhev_url'],
            'provider_content.user': rhev_data['username'],
            'provider_content.password': rhev_data['password'],
            'provider_content.api4': version,
            'provider_content.datacenter.value': rhev_data['datacenter'],
            'provider_content.certification_authorities': module_ca_cert
        })
        resource_values = session.computeresource.read(name)
        assert resource_values['description'] == description
        session.computeresource.edit(name, {'description': new_description})
        resource_values = session.computeresource.read(name)
        assert resource_values['description'] == new_description


@tier2
@parametrize('version', [True, False])
def test_positive_list_resource_vms(
        session, module_ca_cert, rhev_data, version):
    """List VMs for RHEV Compute Resource

    :id: eea2f2b1-e9f4-448d-8c54-51fb25af3d5f

    :expectedresults: VMs listed for provided compute resource

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': name,
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_data['rhev_url'],
            'provider_content.user': rhev_data['username'],
            'provider_content.password': rhev_data['password'],
            'provider_content.api4': version,
            'provider_content.datacenter.value': rhev_data['datacenter'],
            'provider_content.certification_authorities': module_ca_cert
        })
        vm = session.computeresource.list_vms(name, rhev_data['vm_name'])
        assert vm['Name'].read() == rhev_data['vm_name']


@tier2
def test_positive_edit_resource_version(session, module_ca_cert, rhev_data):
    """Edit RHEV Compute Resource with another protocol version

    :id: 6e7985b6-a605-4fb8-8710-17a046bdac53

    :expectedresults: resource updated successfully and switched to another
        protocol version

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': name,
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_data['rhev_url'],
            'provider_content.user': rhev_data['username'],
            'provider_content.password': rhev_data['password'],
            'provider_content.api4': False,
            'provider_content.datacenter.value': rhev_data['datacenter'],
            'provider_content.certification_authorities': module_ca_cert
        })
        resource_values = session.computeresource.read(name)
        assert not resource_values['provider_content']['api4']
        session.computeresource.edit(name, {'provider_content.api4': True})
        resource_values = session.computeresource.read(name)
        assert resource_values['provider_content']['api4']


@tier2
@parametrize('version', [True, False])
@run_in_one_thread
def test_positive_resource_vm_power_management(
        session, module_ca_cert, rhev_data, version):
    """Read current RHEV Compute Resource virtual machine power status and
    change it to opposite one

    :id: 47aea4b7-9258-4863-8966-900bc9e94116

    :expectedresults: virtual machine is powered on or powered off depending on
        its initial state

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': name,
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_data['rhev_url'],
            'provider_content.user': rhev_data['username'],
            'provider_content.password': rhev_data['password'],
            'provider_content.api4': version,
            'provider_content.datacenter.value': rhev_data['datacenter'],
            'provider_content.certification_authorities': module_ca_cert
        })
        status = session.computeresource.vm_status(name, rhev_data['vm_name'])
        if status:
            session.computeresource.vm_poweroff(name, rhev_data['vm_name'])
        else:
            session.computeresource.vm_poweron(name, rhev_data['vm_name'])
        assert session.computeresource.vm_status(
            name, rhev_data['vm_name']) is not status
