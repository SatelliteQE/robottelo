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


def test_positive_create(session):
    subnet = entities.Subnet()
    subnet.create_missing()
    name = subnet.name
    with session:
        session.subnet.create({
            'name': name,
            'protocol': 'IPv4',
            'network_address': subnet.network,
            'network_mask': subnet.mask,
            'boot_mode': 'Static',
        })
        assert session.subnet.search(name) == name
        subnet_values = session.subnet.read(name)
        assert subnet_values['protocol'] == 'IPv4'
        assert subnet_values['network_address'] == subnet.network
        assert subnet_values['network_mask'] == subnet.mask


def test_positive_create_v6(session):
    name = gen_string('alpha')
    ip_address = gen_ipaddr(ipv6=True)
    with session:
        session.subnet.create({
            'name': name,
            'protocol': 'IPv6',
            'network_address': ip_address,
            'network_prefix': 12
        })
        assert session.subnet.search(name) == name
        subnet_values = session.subnet.read(name)
        assert subnet_values['protocol'] == 'IPv6'
        assert subnet_values['network_address'] == ip_address
        assert subnet_values['network_prefix'] == '12'
