"""Test class for Fact  CLI

:Requirement: Fact

:CaseAutomation: Automated

:CaseComponent: Fact

:Team: Rocket

:CaseImportance: Critical

"""

from fauxfactory import gen_ipaddr, gen_mac, gen_string
import pytest

from robottelo.config import settings

pytestmark = [pytest.mark.tier1]


@pytest.mark.skip_if_open('BZ:2161294')
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'fact', ['uptime', 'os::family', 'uptime_seconds', 'memorysize', 'ipaddress']
)
def test_positive_list_by_name(fact, module_target_sat):
    """Test Fact List

    :id: 83794d97-d21b-4482-9522-9b41053e595f

    :expectedresults: Fact List is displayed

    :parametrized: yes

    :BZ: 2161294
    """
    facts = module_target_sat.cli.Fact().list(options={'search': f'fact={fact}'})
    assert facts[0]['fact'] == fact


@pytest.mark.parametrize('fact', ['uptime_days', 'memoryfree'])
def test_negative_list_ignored_by_name(fact, module_target_sat):
    """Test Fact List

    :id: b6375f39-b8c3-4807-b04b-b0e43644441f

    :expectedresults: Ignored fact is not listed

    :parametrized: yes
    """
    assert module_target_sat.cli.Fact().list(options={'search': f'fact={fact}'}) == []


def test_negative_list_by_name(module_target_sat):
    """Test Fact List failure

    :id: bd56d27e-59c0-4f35-bd53-2999af7c6946

    :expectedresults: Fact List is not displayed
    """
    assert (
        module_target_sat.cli.Fact().list(options={'search': f'fact={gen_string("alpha")}'}) == []
    )


@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_update_client_facts_verify_imported_values(
    module_target_sat, rhel_contenthost, module_org, module_location, module_activation_key
):
    """Update client facts and verify the facts are updated in Satellite.

    :id: ea94ccb7-a125-4be3-932a-bfcb035d3604

    :steps:
        1. Add a new interface to the host.
        2. Register the host to Satellite
        3. Update the facts in Satellite.
        4. Read all the facts for the host.
        5. Verify that all the facts(new and existing) are updated in Satellite.

    :expectedresults: Facts are successfully updated in the Satellite.
    """
    mac_address = gen_mac(multicast=False)
    ip = gen_ipaddr()
    # Create eth1 interface on the host
    add_interface_command = (
        f'ip link add eth1 type dummy && ifconfig eth1 hw ether {mac_address} &&'
        f'ip addr add {ip}/24 brd + dev eth1 label eth1:1 &&'
        'ip link set dev eth1 up'
    )
    assert rhel_contenthost.execute(add_interface_command).status == 0
    result = rhel_contenthost.register(
        target=module_target_sat,
        org=module_org,
        loc=module_location,
        activation_keys=[module_activation_key.name],
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    rhel_contenthost.execute('subscription-manager facts --update')
    facts = module_target_sat.cli.Fact().list(
        options={'search': f'host={rhel_contenthost.hostname}'}, output_format='json'
    )
    facts_dict = {fact['fact']: fact['value'] for fact in facts}
    expected_values = {
        'net::interface::eth1::ipv4_address': ip,
        'net::interface::eth1::mac_address': mac_address.lower(),
        'network::fqdn': rhel_contenthost.hostname,
        'lscpu::architecture': rhel_contenthost.arch,
    }
    for fact, expected_value in expected_values.items():
        actual_value = facts_dict.get(fact)
        assert (
            actual_value == expected_value
        ), f'Assertion failed: {fact} (expected: {expected_value}, actual: {actual_value})'
