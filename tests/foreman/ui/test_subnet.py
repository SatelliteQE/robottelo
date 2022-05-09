"""Test class for Subnet UI

:Requirement: Subnet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Networking

:Assignee: rdrazny

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_ipaddr

from robottelo.datafactory import gen_string


@pytest.fixture(scope='module')
def module_dom(module_target_sat, module_org, module_location):
    d = module_target_sat.api.Domain(
        organization=[module_org.id], location=[module_location.id]
    ).create()
    yield d.read()
    d.delete()


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_target_sat, module_dom):
    """Perform end to end testing for subnet component in ipv6 network

    :id: f77031c9-2ca8-44db-8afa-d0212aeda540

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alphanumeric')
    network_address = gen_ipaddr(ip3=True, ipv6=True)
    with session:
        session.subnet.create(
            {
                'subnet.name': name,
                'subnet.description': description,
                'subnet.protocol': 'IPv6',
                'subnet.network_address': network_address,
                'subnet.network_prefix': '24',
                'subnet.ipam': 'EUI-64',
                'subnet.mtu': '1600',
                'domains.resources.assigned': [module_dom.name],
            }
        )
        sn = module_target_sat.api.Subnet().search(query={'search': f'name={name}'})
        assert sn, f'Subnet {sn} expected to exist, but it is not listed'
        sn = sn[0]
        subnet_values = session.subnet.read(name, widget_names=['subnet', 'domains'])
        assert subnet_values['subnet']['name'] == name
        assert subnet_values['subnet']['description'] == description
        assert subnet_values['subnet']['protocol'] == 'IPv6'
        assert subnet_values['subnet']['network_address'] == network_address
        assert subnet_values['subnet']['network_prefix'] == '24'
        assert subnet_values['subnet']['ipam'] == 'EUI-64'
        assert subnet_values['subnet']['mtu'] == '1600'
        assert module_dom.name in subnet_values['domains']['resources']['assigned']
        # Update subnet with new name
        session.subnet.update(name, {'subnet.name': new_name})
        assert sn.read().name == new_name
        # Delete the subnet
        sn.domain = []
        sn.update(['domain'])
        session.subnet.delete(new_name)
        assert not module_target_sat.api.Subnet().search(
            query={'search': f'name={new_name}'}
        ), 'The subnet was supposed to be deleted'
