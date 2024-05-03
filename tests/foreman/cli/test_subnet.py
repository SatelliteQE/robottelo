"""Test class for Subnet CLI

:Requirement: Subnet

:CaseAutomation: Automated

:CaseComponent: Networking

:Team: Rocket

:CaseImportance: Medium

"""

import random
import re

from fauxfactory import gen_choice, gen_integer, gen_ipaddr, gen_netmask
import pytest

from robottelo.constants import SUBNET_IPAM_TYPES
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.utils.datafactory import (
    filtered_datapoint,
    parametrized,
    valid_data_list,
)


@filtered_datapoint
def valid_addr_pools():
    """Returns a list of valid address pools"""
    return [
        [gen_integer(min_value=1, max_value=255), gen_integer(min_value=1, max_value=255)],
        [gen_integer(min_value=1, max_value=255)] * 2,
        [1, 255],
    ]


@filtered_datapoint
def invalid_addr_pools():
    """Returns a list of invalid address pools"""
    return [
        {'from': gen_integer(min_value=1, max_value=255)},
        {'to': gen_integer(min_value=1, max_value=255)},
        {
            'from': gen_integer(min_value=128, max_value=255),
            'to': gen_integer(min_value=1, max_value=127),
        },
        {'from': 256, 'to': 257},
    ]


@filtered_datapoint
def invalid_missing_attributes():
    """Returns a list of invalid missing attributes"""
    return [
        {'name': ''},
        {'network': '256.0.0.0'},
        {'network': ''},
        {'mask': '256.0.0.0'},
        {'mask': ''},
        {'mask': '255.0.255.0'},
    ]


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_CRUD(module_target_sat):
    """Create, update and delete subnet

    :id: d74a52a7-df56-44ef-89a3-081c14e81e43

    :expectedresults: Subnet is created, updated and deleted

    :CaseImportance: Critical
    """
    name = gen_choice(list(valid_data_list().values()))
    pool = sorted(valid_addr_pools()[0])
    mask = gen_netmask()
    # generate pool range from network address
    network = gen_ipaddr()
    from_ip = re.sub(r'\d+$', str(pool[0]), network)
    to_ip = re.sub(r'\d+$', str(pool[1]), network)
    domains_amount = random.randint(2, 3)
    domains = [module_target_sat.cli_factory.make_domain() for _ in range(domains_amount)]
    gateway = gen_ipaddr(ip3=True)
    ipam_type = SUBNET_IPAM_TYPES['dhcp']
    subnet = module_target_sat.cli_factory.make_subnet(
        {
            'name': name,
            'from': from_ip,
            'mask': mask,
            'network': network,
            'to': to_ip,
            'domain-ids': [domain['id'] for domain in domains],
            'gateway': gateway,
            'ipam': ipam_type,
        }
    )
    # Check if Subnet can be listed
    subnets_ids = [subnet_['id'] for subnet_ in module_target_sat.cli.Subnet.list()]
    assert subnet['id'] in subnets_ids
    assert subnet['name'] == name
    assert subnet['start-of-ip-range'] == from_ip
    assert subnet['end-of-ip-range'] == to_ip
    assert len(subnet['domains']) == domains_amount
    for domain in domains:
        assert domain['name'] in subnet['domains']
    assert gateway in subnet['gateway-addr']
    assert ipam_type in subnet['ipam']

    # update subnet
    new_name = gen_choice(list(valid_data_list().values()))
    pool = sorted(valid_addr_pools()[0])
    # generate pool range from network address
    new_network = gen_ipaddr()
    new_mask = gen_netmask()
    ip_from = re.sub(r'\d+$', str(pool[0]), new_network)
    ip_to = re.sub(r'\d+$', str(pool[1]), new_network)
    ipam_type = SUBNET_IPAM_TYPES['internal']
    module_target_sat.cli.Subnet.update(
        {
            'new-name': new_name,
            'from': ip_from,
            'id': subnet['id'],
            'to': ip_to,
            'mask': new_mask,
            'network': new_network,
            'ipam': ipam_type,
            'domain-ids': "",  # delete domains needed for subnet delete
        }
    )
    subnet = module_target_sat.cli.Subnet.info({'id': subnet['id']})
    assert subnet['name'] == new_name
    assert subnet['start-of-ip-range'] == ip_from
    assert subnet['end-of-ip-range'] == ip_to
    assert subnet['network-addr'] == new_network
    assert subnet['network-mask'] == new_mask
    assert ipam_type in subnet['ipam']

    # delete subnet
    module_target_sat.cli.Subnet.delete({'id': subnet['id']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Subnet.info({'id': subnet['id']})


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_missing_attributes()))
def test_negative_create_with_attributes(options, module_target_sat):
    """Create subnet with invalid or missing required attributes

    :id: de468dd3-7ba8-463e-881a-fd1cb3cfc7b6

    :parametrized: yes

    :expectedresults: Subnet is not created

    :CaseImportance: Medium
    """
    with pytest.raises(CLIFactoryError, match='Could not create the subnet:'):
        module_target_sat.cli_factory.make_subnet(options)


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.parametrize('pool', **parametrized(invalid_addr_pools()))
def test_negative_create_with_address_pool(pool, module_target_sat):
    """Create subnet with invalid address pool range

    :parametrized: yes

    :id: c7824327-b5ef-4f95-bd4b-ba4eff73551c

    :expectedresults: Subnet is not created

    :CaseImportance: Medium
    """
    mask = gen_netmask()
    network = gen_ipaddr()
    options = {'mask': mask, 'network': network}
    # generate pool range from network address
    for key, val in pool.items():
        options[key] = re.sub(r'\d+$', str(val), network)
    with pytest.raises(CLIFactoryError, match='Could not create the subnet:'):
        module_target_sat.cli_factory.make_subnet(options)


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_missing_attributes()))
def test_negative_update_attributes(request, options, module_target_sat):
    """Update subnet with invalid or missing required attributes

    :parametrized: yes

    :id: ab60372e-cef7-4495-bd66-68e7dbece475

    :expectedresults: Subnet is not updated

    :CaseImportance: Medium
    """
    subnet = module_target_sat.cli_factory.make_subnet()
    request.addfinalizer(lambda: module_target_sat.cli.Subnet.delete({'id': subnet['id']}))
    options['id'] = subnet['id']
    with pytest.raises(CLIReturnCodeError, match='Could not update the subnet:'):
        module_target_sat.cli.Subnet.update(options)
    # check - subnet is not updated
    result = module_target_sat.cli.Subnet.info({'id': subnet['id']})
    for key in ['name', 'network-addr', 'network-mask']:
        assert subnet[key] == result[key]


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_addr_pools()))
def test_negative_update_address_pool(request, options, module_target_sat):
    """Update subnet with invalid address pool

    :parametrized: yes

    :id: d0a857b4-be10-4b5d-86d4-43cf99c11619

    :expectedresults: Subnet is not updated

    :CaseImportance: Medium
    """
    subnet = module_target_sat.cli_factory.make_subnet()
    request.addfinalizer(lambda: module_target_sat.cli.Subnet.delete({'id': subnet['id']}))
    opts = {'id': subnet['id']}
    # generate pool range from network address
    for key, val in options.items():
        opts[key] = re.sub(r'\d+$', str(val), subnet['network-addr'])
    with pytest.raises(CLIReturnCodeError, match='Could not update the subnet:'):
        module_target_sat.cli.Subnet.update(opts)
    # check - subnet is not updated
    result = module_target_sat.cli.Subnet.info({'id': subnet['id']})
    for key in ['start-of-ip-range', 'end-of-ip-range']:
        assert result[key] == subnet[key]


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_set_parameter_option_presence():
    """Presence of set parameter option in command

    :id: f6ef75b2-6932-460c-80ba-2745244ec244

    :steps: 1. Check if 'set-parameter' option is present in subnet command.

    :expectedresults: The set parameter option to create with subnet should
        be present

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_positive_create_with_parameter():
    """Subnet with parameters can be created

    :id: cf40a3f7-5a09-41aa-8b48-874a2af7057d

    :steps:

        1. Attempt to 'Create Subnet' with all the details
        2. Also with parameter with single key and single value

    :expectedresults: The parameter should be created in subnet

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_positive_create_with_parameter_and_multiple_values():
    """Subnet parameters can be created with multiple values

    :id: 1e9ef184-bdf9-4eba-8055-f55b0dd9d6a0

    :steps:

        1. Attempt to 'Create Subnet' with all the details.
        2. Also with parameter having single key and multiple values
            separated with comma

    :expectedresults: The parameter with multiple values should be saved
        in subnet

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_positive_create_with_parameter_and_multiple_names():
    """Subnet parameters can be created with multiple names with valid
    separators

    :id: c5fe4a28-b75b-4eec-a56e-3bc2ac82e0cc

    :steps:

        1. Attempt to 'Create Subnet' with all the details
        2. Also with parameter having key with multiple names separated
            by valid separators(e.g fwd slash) and value

    :expectedresults: The parameter with multiple names separated by valid
        separators should be saved in subnet

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_negative_create_with_parameter_and_invalid_separator():
    """Subnet parameters can not be created with multiple names with
    invalid separators

    :id: e0842f7a-eb39-48b6-8c0b-64e02f10ce14

    :steps:

        1. Attempt to 'Create Subnet' with all the details
        2. Also with parameter having key with multiple names separated by
            invalid separators(e.g comma) and value

    :expectedresults: The parameter with multiple names separated by
        invalid separators should not be saved in subnet

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_with_multiple_parameters():
    """Subnet with more than one parameters

    :id: 2a9b3043-1add-43d2-af2f-ff39304eb698

    :steps:

        1. Attempt to 'Create Subnet' with all the details
        2. Also with multiple parameters having unique key and value.

    :expectedresults: The subnet should be created with multiple parameters
        having unique key names

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_negative_create_with_duplicated_parameters():
    """Subnet with more than one parameters with duplicate names

    :id: a720306f-be8a-49fb-afe1-bcb7ff1d104f

    :steps:

        1. Attempt to 'Create Subnet' with all the details
        2. Also with multiple parameters having duplicate key names and
            value

    :expectedresults: The subnet parameters should not be created with
        duplicate names

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_inherit_subnet_parmeters_in_host():
    """Host inherits parameters from subnet

    :id: 03fd00dc-7f04-4acb-ae21-1bd67dca8d8d

    :steps:

        1. Create valid subnet with a valid parameter
        2. Create host with above subnet
        3. Assign hosts primary interface with subnet
        4. List above hosts global parameters

    :expectedresults: The parameters from subnet should be displayed in
        host parameters

    :BZ: 1426612, 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_negative_inherit_subnet_parmeters_in_host():
    """Host does not inherits parameters from subnet for non primary
    interface

    :id: 6a7c078c-de97-40df-9dd3-8bc2ebd4656d

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with above subnet
        3. Assign hosts primary interface with subnet
        4. After host creation, edit the host and unset primary interface
        5. List above hosts global parameters

    :expectedresults: The parameters from subnet should not be displayed
        in host parameters
    :BZ: 1426612, 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_subnet_parameters_override_from_host():
    """Subnet parameters values can be overridden from host

    :id: 1220fa50-4ded-42be-b595-f120c02e3b9c

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with above subnet
        3. Assign hosts primary interface with subnet
        4. Override subnet parameter value from host using set-parameter
            subcommand with some other value

    :expectedresults:

        1. The subnet parameters should override from host
        2. The new value should be assigned to parameter
        3. The parameter and value should become host parameters
            and not global parameters

    :BZ: 1426612, 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_subnet_parameters_override_impact_on_subnet():
    """Override subnet parameter from host impact on subnet parameter

    :id: 4aeeba99-c5e4-41ae-baa9-6e028de52084

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with above subnet
        3. Assign hosts primary interface with subnet
        4. Override subnet parameter value from host using set-parameter
            subcommand

    :expectedresults: The override value of subnet parameter from host
        should not change actual value in subnet parameter

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_positive_update_parameter():
    """Subnet parameter can be updated

    :id: 47b0dbca-f8f0-4b93-9b9f-ddd28a8e1084

    :steps:

        1. Create valid subnet with valid parameter
        2. Update above subnet parameter with new name and
            value

    :expectedresults: The parameter name and value should be updated

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_negative_update_parameter():
    """Subnet parameter can not be updated with invalid names

    :id: f611070e-febb-4321-b5b8-c79b779debe2

    :steps:

        1. Create valid subnet with valid parameter
        2. Update above subnet parameter with some invalid
            name. e.g name with comma or space

    :expectedresults: The parameter should not be updated with invalid name

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_update_subnet_parameter_host_impact():
    """Update in parameter name and value from subnet component updates
        the parameter in host inheriting that subnet

    :id: 5c8e47d8-2e98-48ec-b14b-654555756adf

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with the above subnet
        3. Update subnet parameter with new name and value

    :expectedresults: The host parameters should have updated name and
        value from subnet parameters

    :BZ: 1426612, 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_positive_delete_subnet_parameter():
    """Subnet parameter can be deleted

    :id: ce6bd169-8ee6-483f-aedd-45a2eb55a1f9

    :steps:

        1. Create valid subnet with valid parameter
        2. Delete the above subnet parameter

    :expectedresults: The parameter should be deleted from subnet

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_multiple_parameters():
    """Multiple subnet parameters can be deleted at once

    :id: c75bbcf1-1ba6-479d-bf13-88ba1139fa99

    :steps:

        1. Create valid subnet with multiple valid parameters
        2. Delete more than one parameters at once

    :expectedresults: Multiple parameters should be deleted from subnet

    :BZ: 1426612
    """


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_delete_subnet_parameter_host_impact():
    """Deleting parameter from subnet component deletes the parameter in
        host inheriting that subnet

    :id: 6ab20db1-2d76-451a-8fca-b61699ef6eb2

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with the above subnet
        3. Delete the above parameter from subnet
        4. List subnet parameters for above host

    :expectedresults: The parameter should be deleted from host

    :BZ: 1426612, 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_delete_subnet_parameter_overrided_host_impact():
    """Deleting parameter from subnet component doesnt deletes its
        overridden parameter in host inheriting that subnet

    :id: 2481ca10-48c1-4d18-90ed-aa20377d6905

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with the above subnet
        3. Override subnet parameter value from host
        4. Delete the above parameter from subnet
        5. List host parameters

    :expectedresults: The parameter should not be deleted from host
        as it becomes host parameter now

    :BZ: 1426612
    """
