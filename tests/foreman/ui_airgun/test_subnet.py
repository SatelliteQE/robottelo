"""Test class for Subnet UI

:Requirement: Subnet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_ipaddr
from nailgun import entities
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


def test_positive_create(session):
    subnet = entities.Subnet()
    subnet.create_missing()
    name = subnet.name
    with session:
        session.subnet.create({
            'subnet.name': name,
            'subnet.protocol': 'IPv4',
            'subnet.network_address': subnet.network,
            'subnet.network_mask': subnet.mask,
            'subnet.boot_mode': 'Static',
        })
        assert session.subnet.search(name)[0]['Name'] == name
        subnet_values = session.subnet.read(name)
        assert subnet_values['subnet']['protocol'] == 'IPv4'
        assert subnet_values['subnet']['network_address'] == subnet.network
        assert subnet_values['subnet']['network_mask'] == subnet.mask


def test_positive_create_v6(session):
    name = gen_string('alpha')
    ip_address = gen_ipaddr(ipv6=True)
    with session:
        session.subnet.create({
            'subnet.name': name,
            'subnet.protocol': 'IPv6',
            'subnet.network_address': ip_address,
            'subnet.network_prefix': 12
        })
        assert session.subnet.search(name)[0]['Name'] == name
        subnet_values = session.subnet.read(name)
        assert subnet_values['subnet']['protocol'] == 'IPv6'
        assert subnet_values['subnet']['network_address'] == ip_address
        assert subnet_values['subnet']['network_prefix'] == '12'


@tier2
def test_positive_create_with_domain(session, module_org):
    """Create new subnet with domain in same organization

    :id: adbc7189-b451-49df-aa10-2ae732832dfe

    :expectedresults: Subnet is created with domain associated

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    domain = entities.Domain(organization=[module_org]).create()
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
