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
from robottelo.utils.issue_handlers import is_open

pytestmark = [pytest.mark.tier1]


@pytest.mark.upgrade
@pytest.mark.parametrize(
    'fact',
    [
        'system_uptime',
        'os::family',
        'system_uptime::seconds',
        'memory::system::total',
        'networking::ip',
    ],
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


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.pit_client
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_facts_end_to_end(
    module_target_sat, rhel_contenthost, module_org, module_location, module_activation_key
):
    """Update client facts and run Ansible roles and verify the facts are updated in Satellite.

    :id: ea94ccb7-a125-4be3-932a-bfcb035d3604

    :Verifies: SAT-27056

    :steps:
        1. Add a new interface to the host.
        2. Register the host to Satellite
        3. Gather ansible facts by running ansible roles on the host.
        4. Update the facts in Satellite.
        5. Read all the facts for the host.
        6. Verify that all the facts (new and existing) are updated in Satellite.

    :expectedresults: Facts are successfully updated in the Satellite.
    """
    ip = gen_ipaddr()
    mac_address = gen_mac(multicast=False)
    # Create eth1 interface on the host
    add_interface_command = (
        f'nmcli connection add type dummy ifname eth1 ipv4.method manual ipv4.addresses {ip} && '
        f'nmcli connection modify id dummy-eth1 ethernet.mac-address {mac_address}'
    )
    assert rhel_contenthost.execute(add_interface_command).status == 0
    result = rhel_contenthost.register(
        target=module_target_sat,
        org=module_org,
        loc=module_location,
        activation_keys=[module_activation_key.name],
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    host = rhel_contenthost.nailgun_host
    # gather ansible facts by running ansible roles on the host
    task_id = host.play_ansible_roles()
    module_target_sat.wait_for_tasks(
        search_query=f'id = {task_id}',
        poll_timeout=100,
    )
    task_details = module_target_sat.api.ForemanTask().search(query={'search': f'id = {task_id}'})
    assert task_details[0].result == 'success'
    facts = module_target_sat.cli.Fact().list(
        options={'search': f'host={rhel_contenthost.hostname}'}, output_format='json'
    )
    facts_dict = {fact['fact']: fact['value'] for fact in facts}
    expected_values = {
        'net::interface::eth1::ipv4_address': ip,
        'network::fqdn': rhel_contenthost.hostname,
        'lscpu::architecture': rhel_contenthost.arch,
        'ansible_distribution_major_version': str(rhel_contenthost.os_version.major),
        'ansible_fqdn': rhel_contenthost.hostname,
    }
    if not is_open('SAT-27056'):
        expected_values['net::interface::eth1::mac_address'] = mac_address.lower()
    for fact, expected_value in expected_values.items():
        actual_value = facts_dict.get(fact)
        assert (
            actual_value == expected_value
        ), f'Assertion failed: {fact} (expected: {expected_value}, actual: {actual_value})'


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_custom_facts_and_clean_orphaned_facts(
    module_target_sat, module_org, module_location, module_activation_key, rhel_contenthost
):
    """Create custom facts, verify they are updated on Satellite and cleanup the orphaned facts successfully without
    any foreign key violation.

    :id: ae0b5574-cc8b-4f0c-ba7b-c6f480c08e06

    :BZ: 2004158

    :customerscenario: true

    :steps:
        1. Create few custom facts
        2. Verify on Satellite
        3. Run "foreman-rake facts:clean" to clean orphaned facts.

    :expectedresults: Custom facts are created, uploaded successfully and orphaned facts are cleaned up without
     any foreign key violation.
    """
    result = rhel_contenthost.register(
        target=module_target_sat,
        org=module_org,
        loc=module_location,
        activation_keys=[module_activation_key.name],
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    host = rhel_contenthost.nailgun_host
    custom_facts = {
        "operatingsystem": "RedHat",
        "operatingsystemrelease": f'{settings.content_host.default_rhel_version}',
        "custom_fact": "new_custom_fact",
    }
    rhel_contenthost.execute('subscription-manager facts --update')
    host.upload_facts(data={'name': rhel_contenthost.hostname, 'facts': custom_facts})
    facts = module_target_sat.cli.Fact().list(
        options={'search': f'host={rhel_contenthost.hostname}'}, output_format='json'
    )

    facts_dict = {fact['fact']: fact['value'] for fact in facts}
    expected_values = {
        'operatingsystem': custom_facts['operatingsystem'],
        'operatingsystemrelease': custom_facts['operatingsystemrelease'],
        'custom_fact': custom_facts['custom_fact'],
        'network::fqdn': rhel_contenthost.hostname,
    }
    for fact, expected_value in expected_values.items():
        actual_value = facts_dict.get(fact)
        assert (
            actual_value == expected_value
        ), f'Assertion failed: {fact} (expected: {expected_value}, actual: {actual_value})'

    # Cleanup orphaned facts
    result = module_target_sat.execute('foreman-rake facts:clean')
    assert "Finished, cleaned" in result.stdout
    assert result.status == 0
