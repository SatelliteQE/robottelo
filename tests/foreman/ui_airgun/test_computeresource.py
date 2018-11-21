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


_provider_parameteres = [
    {
        'provider': 'vmware',
        'params': {
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': settings.vmware.vcenter,
            'provider_content.user': settings.vmware.username,
            'provider_content.password': settings.vmware.password,
        },
        'assertable': [
            'provider',
            'provider_content.vcenter',
            'provider_content.user',
        ],
    },
    {
        'provider': 'ec2',
        'params': {
            'provider': FOREMAN_PROVIDERS['ec2'],
            'provider_content.access_key': settings.ec2.access_key,
            'provider_content.secret_key': settings.ec2.secret_key,
        },
        'assertable': [
            'provider',
            'provider_content.access_key',
        ],
    },
    {
        'provider': 'rhev_v3',
        'params': {
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': settings.rhev.hostname,
            'provider_content.user': settings.rhev.username,
            'provider_content.password': settings.rhev.password,
            'provider_content.api4': False,
            'provider_content.datacenter.value': settings.rhev.datacenter,
            'provider_content.certification_authorities':
                None
                if settings.rhev.ca_cert is None
                else requests.get(settings.rhev.ca_cert).content.decode(),
        },
        'assertable': [
            'provider',
            'provider_content.api4',
            'provider_content.url',
            'provider_content.user',
            'provider_content.certification_authorities',
            'provider_content.datacenter.value',
        ],
    },
    {
        'provider': 'rhev_v4',
        'params': {
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': settings.rhev.hostname,
            'provider_content.user': settings.rhev.username,
            'provider_content.password': settings.rhev.password,
            'provider_content.api4': True,
            'provider_content.datacenter.value': settings.rhev.datacenter,
            'provider_content.certification_authorities':
                None
                if settings.rhev.ca_cert is None
                else requests.get(settings.rhev.ca_cert).content.decode(),
        },
        'assertable': [
            'provider',
            'provider_content.api4',
            'provider_content.url',
            'provider_content.user',
            'provider_content.certification_authorities',
            'provider_content.datacenter.value',
        ],
    },
]


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


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


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


@tier2
@parametrize('provider', _provider_parameteres,
             ids=[i['provider'] for i in _provider_parameteres])
def test_positive_create_edit_desc_delete_resource(session, module_org, module_loc, provider):
    """Create, edit description and delete compute resource

    :id: f75544b1-3943-4cc6-98d1-f2d0fbe7244e

    :expectedresults: resource created, updated with new description and deleted successfully

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    description = gen_string('alpha', length=40)
    new_description = gen_string('alpha', length=50)
    provider['params']['name'] = name
    provider['params']['description'] = description

    def _get_value(data, keys):
        """Given data like:

            {
                "aaa": {
                    "bbb": {
                        "ccc": 1
                    }
                }
            }

        and keys like:

            ['aaa', 'bbb', 'ccc']

        returns value for that key - in our example 1

        :param dict data: (possibly nasted) dictionary from which you want to obtain the result
        :param list keys: list of one (for flat dictionary) or more (for nasted dictionary) keys
        """
        if len(keys) == 1:
            return data[keys[0]]
        else:
            return _get_value(data[keys[0]], keys[1:])

    with session:
        session.computeresource.create(provider['params'])
        resource_values = session.computeresource.read(name)
        for assertable in provider['assertable']:
            keys = assertable.split('.')
            assert provider['params']['.'.join(keys)] == _get_value(resource_values, keys)
        assert resource_values['name'] == name
        assert resource_values['description'] == description
        assert resource_values['organizations']['resources']['assigned'] == [module_org.name]
        assert module_org.name not in resource_values['organizations']['resources']['unassigned']
        assert resource_values['locations']['resources']['assigned'] == [module_loc.name]
        assert module_loc.name not in resource_values['locations']['resources']['unassigned']
        session.computeresource.edit(name, {'description': new_description})
        resource_values = session.computeresource.read(name)
        assert resource_values['description'] == new_description
        session.computeresource.delete(name)
        assert not session.computeresource.search(name)
