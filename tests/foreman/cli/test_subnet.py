# -*- encoding: utf-8 -*-
"""Test class for Subnet CLI

:Requirement: Subnet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Networking

:TestType: Functional

:Upstream: No
"""

import random
import re

from fauxfactory import gen_integer, gen_ipaddr
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_domain, make_subnet, CLIFactoryError
from robottelo.cli.subnet import Subnet
from robottelo.constants import SUBNET_IPAM_TYPES
from robottelo.datafactory import filtered_datapoint, valid_data_list
from robottelo.decorators import (
     stubbed, tier1, tier2, tier3, upgrade)
from robottelo.test import CLITestCase
from robozilla.decorators import skip_if_bug_open


@filtered_datapoint
def valid_addr_pools():
    """Returns a list of valid address pools"""
    return [
        [gen_integer(min_value=1, max_value=255),
         gen_integer(min_value=1, max_value=255)],
        [gen_integer(min_value=1, max_value=255)] * 2,
        [1, 255],
    ]


@filtered_datapoint
def invalid_addr_pools():
    """Returns a list of invalid address pools"""
    return [
        {u'from': gen_integer(min_value=1, max_value=255)},
        {u'to': gen_integer(min_value=1, max_value=255)},
        {u'from': gen_integer(min_value=128, max_value=255),
         u'to': gen_integer(min_value=1, max_value=127)},
        {u'from': 256, u'to': 257},
    ]


@filtered_datapoint
def invalid_missing_attributes():
    """Returns a list of invalid missing attributes"""
    return [
        {u'name': ''},
        {u'network': '256.0.0.0'},
        {u'network': ''},
        {u'mask': '256.0.0.0'},
        {u'mask': ''},
        {u'mask': '255.0.255.0'}
    ]


class SubnetTestCase(CLITestCase):
    """Subnet CLI tests.

    :CaseImportance: High
    """

    @tier1
    def test_positive_create_with_name(self):
        """Check if Subnet can be created with random names

        :id: 99cda3eb-3912-461b-83bd-f906b78eeca0

        :expectedresults: Subnet is created and has random name

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                subnet = make_subnet({'name': name})
                self.assertEqual(subnet['name'], name)

    @tier1
    @upgrade
    def test_positive_create_with_address_pool(self):
        """Create subnet with valid address pool

        :id: d74a52a7-df56-44ef-89a3-081c14e81e43

        :expectedresults: Subnet is created and address pool is set

        :CaseImportance: Critical
        """
        for pool in valid_addr_pools():
            with self.subTest(pool):
                pool.sort()
                mask = '255.255.255.0'
                # generate pool range from network address
                network = gen_ipaddr()
                from_ip = re.sub(r'\d+$', str(pool[0]), network)
                to_ip = re.sub(r'\d+$', str(pool[1]), network)
                subnet = make_subnet({
                    u'from': from_ip,
                    u'mask': mask,
                    u'network': network,
                    u'to': to_ip,
                })
                self.assertEqual(subnet['start-of-ip-range'], from_ip)
                self.assertEqual(subnet['end-of-ip-range'], to_ip)

    @tier1
    def test_positive_create_with_domain(self):
        """Check if subnet with domain can be created

        :id: 7ce7b139-d2b7-44f4-9c1a-1bd591f95334

        :expectedresults: Subnet is created and has new domain assigned

        :CaseImportance: Critical
        """
        domain = make_domain()
        subnet = make_subnet({'domain-ids': domain['id']})
        self.assertIn(domain['name'], subnet['domains'])

    @tier1
    def test_positive_create_with_domains(self):
        """Check if subnet with different amount of domains can be
        created in the system

        :id: e81ddec5-38b0-4c42-b89b-5cf2af580d39

        :expectedresults: Subnet is created and has new domains assigned
        """
        domains_amount = random.randint(3, 5)
        domains = [make_domain() for _ in range(domains_amount)]
        subnet = make_subnet({
            'domain-ids': [domain['id'] for domain in domains],
        })
        self.assertEqual(len(subnet['domains']), domains_amount)
        for domain in domains:
            self.assertIn(domain['name'], subnet['domains'])

    @tier1
    @upgrade
    def test_positive_create_with_gateway(self):
        """Check if subnet with gateway can be created

        :id: 483c0d1d-c542-4be5-8c56-27b2a09db54a

        :expectedresults: Subnet is created and has gateway assigned

        :CaseImportance: Critical
        """
        gateway = gen_ipaddr(ip3=True)
        subnet = make_subnet({'gateway': gateway})
        self.assertIn(gateway, subnet['gateway-addr'])

    @tier1
    @upgrade
    def test_positive_create_with_ipam(self):
        """Check if subnet with different ipam types can be created

        :id: ba4c66fd-50e6-441d-acc2-6ab39d8439d2

        :expectedresults: Subnet is created and correct ipam type is assigned

        :CaseImportance: Critical
        """
        for ipam_type in (SUBNET_IPAM_TYPES['dhcp'],
                          SUBNET_IPAM_TYPES['internal'],
                          SUBNET_IPAM_TYPES['none']):
            with self.subTest(ipam_type):
                subnet = make_subnet({'ipam': ipam_type})
                self.assertIn(ipam_type, subnet['ipam'])

    @tier1
    def test_negative_create_with_attributes(self):
        """Create subnet with invalid or missing required attributes

        :id: de468dd3-7ba8-463e-881a-fd1cb3cfc7b6

        :expectedresults: Subnet is not created

        :CaseImportance: Medium
        """
        for options in invalid_missing_attributes():
            with self.subTest(options):
                with self.assertRaisesRegex(
                    CLIFactoryError,
                    u'Could not create the subnet:'
                ):
                    make_subnet(options)

    @tier1
    @upgrade
    def test_negative_create_with_address_pool(self):
        """Create subnet with invalid address pool range

        :id: c7824327-b5ef-4f95-bd4b-ba4eff73551c

        :expectedresults: Subnet is not created

        :CaseImportance: Medium
        """
        mask = '255.255.255.0'
        network = gen_ipaddr()
        for pool in invalid_addr_pools():
            with self.subTest(pool):
                opts = {u'mask': mask, u'network': network}
                # generate pool range from network address
                for key, val in pool.items():
                    opts[key] = re.sub(r'\d+$', str(val), network)
                with self.assertRaises(CLIFactoryError) as raise_ctx:
                    make_subnet(opts)
                self.assert_error_msg(
                    raise_ctx,
                    u'Could not create the subnet:'
                )

    @tier1
    def test_positive_list(self):
        """Check if Subnet can be listed

        :id: 2ee376f7-9dd9-4b46-b414-801197d5455c

        :expectedresults: Subnet is listed
        """
        # Make a new subnet
        subnet = make_subnet()
        # Fetch ids from subnets list
        subnets_ids = [subnet_['id'] for subnet_ in Subnet.list()]
        self.assertIn(subnet['id'], subnets_ids)

    @tier1
    def test_positive_update_name(self):
        """Check if Subnet name can be updated

        :id: 34533e6c-7081-4b13-99bd-bd57533e05c0

        :expectedresults: Subnet name is updated

        :CaseImportance: Medium
        """
        new_subnet = make_subnet()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                Subnet.update({'id': new_subnet['id'], 'new-name': new_name})
                result = Subnet.info({'id': new_subnet['id']})
                self.assertEqual(result['name'], new_name)

    @tier1
    def test_positive_update_network_mask(self):
        """Check if Subnet network and mask can be updated

        :id: 6a8d7750-71f1-4cd8-bf90-f2eac457c3b4

        :expectedresults: Subnet network and mask are updated
        """
        network = gen_ipaddr()
        mask = '255.255.255.0'
        subnet = make_subnet({
            u'mask': mask,
            u'network': network,
        })
        new_network = gen_ipaddr()
        new_mask = '255.255.192.0'
        Subnet.update({
            u'id': subnet['id'],
            u'mask': new_mask,
            u'network': new_network,
        })
        # check - subnet is updated
        subnet = Subnet.info({u'id': subnet['id']})
        self.assertEqual(subnet['network-addr'], new_network)
        self.assertEqual(subnet['network-mask'], new_mask)

    @tier1
    def test_positive_update_address_pool(self):
        """Check if Subnet address pool can be updated

        :id: 18ced88f-d62e-4e15-8b7b-0a08c4ef239b

        :expectedresults: Subnet address pool is updated
        """
        subnet = make_subnet({u'mask': '255.255.255.0'})
        for pool in valid_addr_pools():
            with self.subTest(pool):
                pool.sort()
                # generate pool range from network address
                ip_from = re.sub(r'\d+$', str(pool[0]), subnet['network-addr'])
                ip_to = re.sub(r'\d+$', str(pool[1]), subnet['network-addr'])
                Subnet.update({
                    u'from': ip_from,
                    u'id': subnet['id'],
                    u'to': ip_to,
                })
                subnet = Subnet.info({u'id': subnet['id']})
                self.assertEqual(subnet['start-of-ip-range'], ip_from)
                self.assertEqual(subnet['end-of-ip-range'], ip_to)

    @tier1
    def test_negative_update_attributes(self):
        """Update subnet with invalid or missing required attributes

        :id: ab60372e-cef7-4495-bd66-68e7dbece475

        :expectedresults: Subnet is not updated

        :CaseImportance: Medium
        """
        subnet = make_subnet()
        for options in invalid_missing_attributes():
            with self.subTest(options):
                options['id'] = subnet['id']
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not update the subnet:'
                ):
                    Subnet.update(options)
                    # check - subnet is not updated
                    result = Subnet.info({u'id': subnet['id']})
                    for key in options.keys():
                        self.assertEqual(subnet[key], result[key])

    @tier1
    def test_negative_update_address_pool(self):
        """Update subnet with invalid address pool

        :id: d0a857b4-be10-4b5d-86d4-43cf99c11619

        :expectedresults: Subnet is not updated

        :CaseImportance: Medium
        """
        subnet = make_subnet()
        for options in invalid_addr_pools():
            with self.subTest(options):
                opts = {u'id': subnet['id']}
                # generate pool range from network address
                for key, val in options.items():
                    opts[key] = re.sub(r'\d+$', str(val), subnet['network-addr'])
                with self.assertRaisesRegex(
                    CLIReturnCodeError,
                    u'Could not update the subnet:'
                ):
                    Subnet.update(opts)
                # check - subnet is not updated
                result = Subnet.info({u'id': subnet['id']})
                for key in ['start-of-ip-range', 'end-of-ip-range']:
                    self.assertEqual(result[key], subnet[key])

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Check if Subnet can be deleted

        :id: ad269df8-4bb2-46a5-9c82-010a80087408

        :expectedresults: Subnet is deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                subnet = make_subnet({'name': name})
                Subnet.delete({'id': subnet['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Subnet.info({'id': subnet['id']})


class ParameterizedSubnetTestCase(CLITestCase):
    """Implements parametrized subnet tests in CLI

    :CaseImportance: Medium
    """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier2
    def test_positive_set_parameter_option_presence(self):
        """Presence of set parameter option in command

        :id: f6ef75b2-6932-460c-80ba-2745244ec244

        :steps:

            1. Check if 'set-parameter' option is present in
                subnet command.

        :expectedresults: The set parameter option to create with subnet should
            be present
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_positive_create_with_parameter(self):
        """Subnet with parameters can be created

        :id: cf40a3f7-5a09-41aa-8b48-874a2af7057d

        :steps:

            1. Attempt to 'Create Subnet' with all the details
            2. Also with parameter with single key and single value

        :expectedresults: The parameter should be created in subnet
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_positive_create_with_parameter_and_multiple_values(self):
        """Subnet parameters can be created with multiple values

        :id: 1e9ef184-bdf9-4eba-8055-f55b0dd9d6a0

        :steps:

            1. Attempt to 'Create Subnet' with all the details.
            2. Also with parameter having single key and multiple values
                separated with comma

        :expectedresults: The parameter with multiple values should be saved
            in subnet
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_positive_create_with_parameter_and_multiple_names(self):
        """Subnet parameters can be created with multiple names with valid
        separators

        :id: c5fe4a28-b75b-4eec-a56e-3bc2ac82e0cc

        :steps:

            1. Attempt to 'Create Subnet' with all the details
            2. Also with parameter having key with multiple names separated
                by valid separators(e.g fwd slash) and value

        :expectedresults: The parameter with multiple names separated by valid
            separators should be saved in subnet
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_negative_create_with_parameter_and_invalid_separator(self):
        """Subnet parameters can not be created with multiple names with
        invalid separators

        :id: e0842f7a-eb39-48b6-8c0b-64e02f10ce14

        :steps:

            1. Attempt to 'Create Subnet' with all the details
            2. Also with parameter having key with multiple names separated by
                invalid separators(e.g comma) and value

        :expectedresults: The parameter with multiple names separated by
            invalid separators should not be saved in subnet
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    @upgrade
    def test_positive_create_with_multiple_parameters(self):
        """Subnet with more than one parameters

        :id: 2a9b3043-1add-43d2-af2f-ff39304eb698

        :steps:

            1. Attempt to 'Create Subnet' with all the details
            2. Also with multiple parameters having unique key and value.

        :expectedresults: The subnet should be created with multiple parameters
            having unique key names
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_negative_create_with_duplicated_parameters(self):
        """Subnet with more than one parameters with duplicate names

        :id: a720306f-be8a-49fb-afe1-bcb7ff1d104f

        :steps:

            1. Attempt to 'Create Subnet' with all the details
            2. Also with multiple parameters having duplicate key names and
                value

        :expectedresults: The subnet parameters should not be created with
            duplicate names
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @skip_if_bug_open('bugzilla', 1470014)
    @tier3
    @upgrade
    def test_positive_inherit_subnet_parmeters_in_host(self):
        """Host inherits parameters from subnet

        :id: 03fd00dc-7f04-4acb-ae21-1bd67dca8d8d

        :steps:

            1. Create valid subnet with a valid parameter
            2. Create host with above subnet
            3. Assign hosts primary interface with subnet
            4. List above hosts global parameters

        :expectedresults: The parameters from subnet should be displayed in
            host parameters
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @skip_if_bug_open('bugzilla', 1470014)
    @tier3
    def test_negative_inherit_subnet_parmeters_in_host(self):
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
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @skip_if_bug_open('bugzilla', 1470014)
    @tier2
    def test_positive_subnet_parameters_override_from_host(self):
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
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier2
    @upgrade
    def test_positive_subnet_parameters_override_impact_on_subnet(self):
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
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_positive_update_parameter(self):
        """Subnet parameter can be updated

        :id: 47b0dbca-f8f0-4b93-9b9f-ddd28a8e1084

        :steps:

            1. Create valid subnet with valid parameter
            2. Update above subnet parameter with new name and
                value

        :expectedresults: The parameter name and value should be updated
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_negative_update_parameter(self):
        """Subnet parameter can not be updated with invalid names

        :id: f611070e-febb-4321-b5b8-c79b779debe2

        :steps:

            1. Create valid subnet with valid parameter
            2. Update above subnet parameter with some invalid
                name. e.g name with comma or space

        :expectedresults: The parameter should not be updated with invalid name
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @skip_if_bug_open('bugzilla', 1470014)
    @tier2
    def test_positive_update_subnet_parameter_host_impact(self):
        """Update in parameter name and value from subnet component updates
            the parameter in host inheriting that subnet

        :id: 5c8e47d8-2e98-48ec-b14b-654555756adf

        :steps:

            1. Create valid subnet with valid parameter
            2. Create host with the above subnet
            3. Update subnet parameter with new name and value

        :expectedresults: The host parameters should have updated name and
            value from subnet parameters
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    def test_positive_delete_subnet_parameter(self):
        """Subnet parameter can be deleted

        :id: ce6bd169-8ee6-483f-aedd-45a2eb55a1f9

        :steps:

            1. Create valid subnet with valid parameter
            2. Delete the above subnet parameter

        :expectedresults: The parameter should be deleted from subnet
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier1
    @upgrade
    def test_positive_delete_multiple_parameters(self):
        """Multiple subnet parameters can be deleted at once

        :id: c75bbcf1-1ba6-479d-bf13-88ba1139fa99

        :steps:

            1. Create valid subnet with multiple valid parameters
            2. Delete more than one parameters at once

        :expectedresults: Multiple parameters should be deleted from subnet
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @skip_if_bug_open('bugzilla', 1470014)
    @tier2
    def test_positive_delete_subnet_parameter_host_impact(self):
        """Deleting parameter from subnet component deletes the parameter in
            host inheriting that subnet

        :id: 6ab20db1-2d76-451a-8fca-b61699ef6eb2

        :steps:

            1. Create valid subnet with valid parameter
            2. Create host with the above subnet
            3. Delete the above parameter from subnet
            4. List subnet parameters for above host

        :expectedresults: The parameter should be deleted from host
        """

    @stubbed()
    @skip_if_bug_open('bugzilla', 1426612)
    @tier2
    def test_positive_delete_subnet_parameter_overrided_host_impact(self):
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
        """
