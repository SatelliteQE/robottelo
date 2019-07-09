"""Test class for Subnet UI

:Requirement: Subnet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Networking

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_ipaddr
from nailgun import entities
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@tier2
def test_positive_create_with_domain(session, module_org, module_loc):
    """Create new subnet with domain in same organization

    :id: adbc7189-b451-49df-aa10-2ae732832dfe

    :expectedresults: Subnet is created with domain associated

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    domain = entities.Domain(
        organization=[module_org], location=[module_loc]).create()
    with session:
        session.subnet.create({
            'subnet.name': name,
            'subnet.network_address': gen_ipaddr(ip3=True),
            'subnet.network_prefix': 12,
            'domains.resources.assigned': [domain.name]
        })
        subnet_values = session.subnet.read(name)
        assert subnet_values[
            'domains']['resources']['assigned'][0] == domain.name


@tier2
@upgrade
def test_positive_end_to_end(session):
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
        session.subnet.create({
            'subnet.name': name,
            'subnet.description': description,
            'subnet.protocol': 'IPv6',
            'subnet.network_address': network_address,
            'subnet.network_prefix': '24',
            'subnet.ipam': 'EUI-64',
            'subnet.mtu': '1600',
        })
        assert session.subnet.search(name)[0]['Name'] == name
        subnet_values = session.subnet.read(name)
        assert subnet_values['subnet']['name'] == name
        assert subnet_values['subnet']['description'] == description
        assert subnet_values['subnet']['protocol'] == 'IPv6'
        assert subnet_values['subnet']['network_address'] == network_address
        assert subnet_values['subnet']['network_prefix'] == '24'
        assert subnet_values['subnet']['ipam'] == 'EUI-64'
        assert subnet_values['subnet']['mtu'] == '1600'
        # Update subnet with new name
        session.subnet.update(name, {'subnet.name': new_name})
        assert session.subnet.search(new_name)[0]['Name'] == new_name
        # Delete architecture
        session.subnet.delete(new_name)
        assert not session.subnet.search(new_name)
