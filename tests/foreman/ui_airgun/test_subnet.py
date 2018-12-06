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
