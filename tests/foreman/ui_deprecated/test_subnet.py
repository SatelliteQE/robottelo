# -*- encoding: utf-8 -*-
"""Test class for Subnet UI

:Requirement: Subnet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import six

from fauxfactory import gen_ipaddr, gen_netmask, gen_string
from nailgun import entities
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    run_only_on, skip_if_bug_open, stubbed, tier1, tier2, tier3, upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_subnet, set_context
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


class SubnetTestCase(UITestCase):
    """Implements Subnet tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(SubnetTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new subnet using different names

        :id: 2318f13c-db38-4919-831f-667fc6e2e7bf

        :expectedresults: Subnet is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_subnet(
                        session,
                        subnet_name=name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.assertIsNotNone(self.subnet.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_long_name(self):
        """Create new subnet with 255 characters in name

        :id: b86772ad-a8ff-4c2b-93f4-4a715e4da59b

        :expectedresults: Subnet is created with 255 chars

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_subnet(
                        session,
                        subnet_name=name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.assertIsNotNone(
                        self.subnet.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new subnet with invalid names

        :id: d53056ad-a219-40d5-b20e-95ad343c9d38

        :expectedresults: Subnet is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_subnet(
                        session,
                        subnet_name=name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_params(self):
        """Create new subnet with negative values

        :id: 5caa6aed-2bba-43d8-bb40-2d80b9d42b69

        :expectedresults: Subnet is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_subnet(
                session,
                subnet_name=gen_string('alpha'),
                subnet_network='292.256.256.0',
                subnet_mask='292.292.292.0',
                subnet_gateway='292.256.256.254',
                subnet_primarydns='292.256.256.2',
                subnet_secondarydns='292.256.256.3',
            )
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.network_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.mask_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.gateway_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.dnsprimary_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.dnssecondary_haserror']))

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete an existing subnet

        :id: cb1265de-a0ed-40b7-ba25-fe92251b9001

        :expectedresults: Subnet is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_subnet(
                        session,
                        subnet_name=name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.subnet.delete(name)

    @run_only_on('sat')
    @tier1
    def test_negative_delete(self):
        """Delete subnet. Attempt to delete subnet, but cancel in the
        confirmation dialog box.

        :id: 9eed9020-8d13-4ba0-909a-db44ad0aecb6

        :expectedresults: Subnet is not deleted

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        with Session(self) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.subnet.delete(name, really=False)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update Subnet name

        :id: ec9f11e3-27a7-45d8-91fe-f04c20b595bc

        :expectedresults: Subnet name is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.subnet.update(name, new_subnet_name=new_name)
                    result_object = self.subnet.search_and_validate(new_name)
                    self.assertEqual(new_name, result_object['name'])
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_positive_update_network(self):
        """Update Subnet network

        :id: f79d3b1b-6101-4009-88ad-b259d4794e6c

        :expectedresults: Subnet network is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_network = gen_ipaddr(ip3=True)
        with Session(self) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.subnet.update(name, new_subnet_network=new_network)
            result_object = self.subnet.search_and_validate(name)
            self.assertEqual(new_network, result_object['network'])

    @run_only_on('sat')
    @tier1
    def test_positive_update_mask(self):
        """Update Subnet mask

        :id: 6cc5de06-5463-4919-abe4-92cef4506a54

        :expectedresults: Subnet mask is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_mask = gen_netmask(16, 31)
        with Session(self) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(1, 15),
            )
            self.subnet.update(name, new_subnet_mask=new_mask)
            result_object = self.subnet.search_and_validate(name)
            self.assertEqual(new_mask, result_object['mask'])

    @run_only_on('sat')
    @tier1
    def test_positive_sort_by_name(self):
        """Create some Subnet entities and sort them by name

        :id: 0b07341c-717e-46a9-86cc-7192f3d8d449

        :customerscenario: true

        :expectedresults: Subnet entities are sorted by name

        :BZ: 1268085

        :CaseImportance: Medium
        """
        organization = entities.Organization().create()
        name_list = [gen_string('alpha', 20) for _ in range(5)]
        with Session(self) as session:
            set_context(session, org=organization.name)
            for name in name_list:
                make_subnet(
                    session,
                    subnet_name=name,
                    subnet_network=gen_ipaddr(ip3=True),
                    subnet_mask=gen_netmask(),
                )
            self.assertEqual(
                self.subnet.sort_table_by_column('Name'),
                sorted(name_list, key=six.text_type.lower)
            )
            self.assertEqual(
                self.subnet.sort_table_by_column('Name'),
                sorted(name_list, key=six.text_type.lower, reverse=True)
            )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1494180)
    @tier1
    def test_positive_sort_by_network(self):
        """Create some Subnet entities and sort them by network address

        :id: 63dc846e-7520-4e8c-8875-a0109d7e5df4

        :customerscenario: true

        :expectedresults: Subnet entities are sorted by network address

        :BZ: 1268085, 1494180

        :CaseImportance: Medium
        """
        organization = entities.Organization().create()
        network_list = [gen_ipaddr(ip3=True) for _ in range(5)]
        network_list.sort(key=lambda s: map(int, s.split('.')), reverse=True)
        with Session(self) as session:
            set_context(session, org=organization.name)
            for ip in network_list:
                make_subnet(
                    session,
                    subnet_name=gen_string('alpha'),
                    subnet_network=ip,
                    subnet_mask=gen_netmask(),
                )
            sorted_list_asc = self.subnet.sort_table_by_column(
                'Network address')
            self.assertEqual(
                [el.split('/', 1)[0] for el in sorted_list_asc],
                network_list[::-1]
            )
            sorted_list_desc = self.subnet.sort_table_by_column(
                'Network address')
            self.assertEqual(
                [el.split('/', 1)[0] for el in sorted_list_desc],
                network_list
            )


class ParameterizedSubnetTestCase(UITestCase):
    """Implements parameterized subnet tests in UI"""

    @stubbed()
    @tier2
    def test_positive_parameter_tab_presence(self):
        """Presence of parameters tab in subnet

        :id: beea7e8b-6d8e-40b0-bac1-0ad90b944088

        :steps:

            1. Go to Subnets component in infrastructure menu.
            2. Attempt to create one subnet.
            3. In create subnet dialog, check if Parameters tab is displayed.

        :expectedresults: The parameter tab in subnet should be displayed
            and available.
        """

    @stubbed()
    @tier1
    def test_positive_create_with_parameter(self):
        """Subnet parameters can be created

        :id: 2b65952c-dd98-41be-8fa5-ed14fd4ace2b

        :steps:

            1. Go to Infrastructure -> Subnets.
            2. Attempt to 'Create Subnet'
            3. Update all the details for subnet creation
            4. In Parameters tab, attempt to '+Add Parameter'.
            5. Add parameter with single key and single value.
            6. Submit the changes for subnet with new parameter.

        :expectedresults: The parameter should be saved in subnet
        """

    @stubbed()
    @tier1
    def test_positive_create_with_parameter_and_multiple_values(self):
        """Subnet parameters can be created with multiple values

        :id: 35203666-6981-4ba7-814b-f73a6399b81f

        :steps:

            1. Go to Infrastructure -> Subnets.
            2. Attempt to 'Create Subnet'
            3. Update all the details for subnet creation
            4. In Parameters tab, attempt to '+Add Parameter'.
            5. Add parameter with single key and multiple values separated with
                comma
            6. Submit the changes for subnet with new parameter.

        :expectedresults: The parameter with multiple values should be saved
            in subnet
        """

    @stubbed()
    @tier1
    def test_positive_create_with_parameter_and_multiple_names(self):
        """Subnet parameters can be created with multiple names with valid
        separators

        :id: e02f8e6d-aeb4-40b8-9463-aef1135c0051

        :steps:

            1. Go to Infrastructure -> Subnets
            2. Attempt to 'Create Subnet'
            3. Update all the details for subnet creation
            4. In Parameters tab, attempt to '+Add Parameter'
            5. Add parameter with key having multiple names separated by valid
                separators e.g fwd slash and value
            6. Submit the changes for subnet with new parameter

        :expectedresults: The parameter with multiple names separated by valid
            separators should be saved in subnet
        """
    @stubbed()
    @tier1
    def test_negative_create_with_parameter_and_invalid_separator(self):
        """Subnet parameters can not be created with multiple names with
        invalid separators

        :id: 941e2633-5677-47cc-9ab0-d5e53b5ef900

        :steps:

            1. Go to Infrastructure -> Subnets
            2. Attempt to 'Create Subnet'
            3. Update all the details for subnet creation
            4. In Parameters tab, attempt to '+Add Parameter'
            5. Add parameter with key having multiple names separated by
                invalid separators. e.g comma
            6. Submit the changes for subnet with new parameter

        :expectedresults: The parameter with multiple names separated by
            invalid separators should not be saved in subnet
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_create_with_multiple_parameters(self):
        """Subnet with more than one parameters

        :id: 2274e7b3-60d6-497b-8a3c-638eda87c69f

        :steps:

            1. Go to Infrastructure -> Subnets
            2. Attempt to 'Create Subnet'
            3. Update all the details for subnet creation
            4. In Parameters tab, attempt to '+Add Parameter'
            5. Add parameter with key and value.
            6. Add more parameters with unique name and values
            7. Submit the changes for subnet with all parameters

        :expectedresults: The subnet should be created with multiple parameters
            having unique names
        """

    @stubbed()
    @tier1
    def test_negative_create_with_duplicated_parameters(self):
        """Subnet with more than one parameters with duplicate names

        :id: 33cdea80-6e86-4029-b4b5-5887e26a37b7

        :steps:

            1. Go to Infrastructure -> Subnets
            2. Attempt to 'Create Subnet'
            3. Update all the details for subnet creation
            4. In Parameters tab, attempt to '+Add Parameter'
            5. Add parameter with key and value.
            6. Attempt to add more parameters with duplicate name
            7. Submit the changes for subnet with all parameters

        :expectedresults: The subnet parameters shold not be created with
            duplicate names
        """

    @stubbed()
    @tier3
    def test_positive_inherit_subnet_parmeters_in_host(self):
        """Host inherits parameters from subnet

        :id: eb688084-c899-4de1-b6f0-983721df4451

        :steps:

            1. Create valid subnet with valid parameter
            2. Create host with above subnet
            3. Assign hosts primary interface with subnet
            4. Go to that host parameters tab, under Global Parameters tab.

        :expectedresults: The parameters from subnet should be displayed in
            host parameters tab
        """

    @stubbed()
    @tier3
    def test_negative_inherit_subnet_parmeters_in_host(self):
        """Host does not inherits parameters from subnet for non primary
        interface

        :id: 7ee6630e-9d9c-40de-93aa-722210a1a8b2

        :steps:

            1. Create valid subnet with valid parameter
            2. Create host with above subnet
            3. Assign hosts primary interface with subnet
            4. After host creation, edit the host and uncheck primary interface
            5. Go to that host parameters tab, under Global Parameters tab.

        :expectedresults: The parameters from subnet should not be displayed
            in host parameters tab
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_subnet_parameters_override_from_host(self):
        """Subnet parameters values can be overriden from host

        :id: fa8c4a14-4a6e-4116-84db-72d2854858da

        :steps:

            1. Create valid subnet with valid parameter
            2. Create host with above subnet
            3. Assign hosts primary interface with subnet
            4. Go to that host parameters tab and override subnet parameter
                value
            5. Submit the override the changes in subnet.

        :expectedresults: The subnet parameters should override from host
        """

    @stubbed()
    @tier2
    def test_positive_subnet_parameters_override_impact_on_subnet(self):
        """Override subnet parameter from host impact on subnet parameter

        :id: 63280dd0-4e29-486b-a5ee-d33d8cc93f3d

        :steps:

            1. Create valid subnet with valid parameter
            2. Create host with above subnet
            3. Assign hosts primary interface with subnet
            4. Go to that host parameters tab and override subnet parameter
                value
            5. Submit the override the changes in subnet.

        :expectedresults: The override value of subnet parameter from host
            should not change actual value in subnet parameter
        """

    @stubbed()
    @tier1
    def test_positive_update_parameter(self):
        """Subnet parameter can be updated

        :id: d9313a4b-20ae-4bb1-b395-0e2ecbb63397

        :steps:

            1. Create a subnet from Infrastructure menu.
            2. Update all the details for subnet creation
            3. Add parameter in subnet parameters tab
            4. Save subnet changes
            5. Edit the above subnet and update parameter with new name and
                value
            6. Save subnet changes

        :expectedresults: The parameter name and value should be updated
        """

    @stubbed()
    @tier1
    def test_negative_update_parameter(self):
        """Subnet parameter can not be updated with invalid names

        :id: ef5a8d41-d131-4a43-8a32-01df90334326

        :steps:

            1. Create a subnet from Infrastructure menu.
            2. Update all the details for subnet creation
            3. Add parameter in subnet parameters tab
            4. Save subnet changes
            5. Edit the above subnet and update parameter with some invalid
                name. e.g name with comma or space
            6. Save subnet changes

        :expectedresults: The parameter should not be updated with invalid name
        """

    @stubbed()
    @tier2
    def test_positive_update_subnet_parameter_host_impact(self):
        """Update in parameter name and value from subnet component updates
            the parameter in host inheriting that subnet

        :id: 44dcaad3-efa4-4725-82d7-762ed8b09659

        :steps:

            1. Create a subnet from Infrastructure menu
            2. Update all the details for subnet creation
            3. Add parameter in subnet parameters tab
            4. Save subnet changes
            5. Create host with the above subnet
            6. Edit the above subnet and update parameter with new name and
                value
            7. Go to Host parameters tab.

        :expectedresults: The host parameters should have updated name and
            value from subnet parameters
        """

    @stubbed()
    @tier1
    def test_positive_delete_subnet_parameter(self):
        """Subnet parameter can be deleted

        :id: be61fd27-18f0-44d7-8de9-d3b989d6d202

        :steps:

            1. Create a subnet from Infrastructure menu
            2. Update all the details for subnet creation
            3. Add parameter in subnet parameters tab
            4. Save subnet changes
            5. Edit the above subnet and click on 'remove' button to delete the
                subnet parameter
            6. Save subnet changes

        :expectedresults: The parameter should be deleted from subnet
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_delete_multiple_parameters(self):
        """Multiple subnet parameters can be deleted at once

        :id: bb66eae5-47e7-4f6b-8aa9-4142eb3e8aa6

        :steps:

            1. Create a subnet from Infrastructure menu
            2. Update all the details for subnet creation
            3. Add multiple parameters in subnet parameters tab
            4. Save subnet changes
            5. Edit the above subnet and click on 'remove' button to  delete
                more than one parameters
            6. Save subnet changes

        :expectedresults: Multiple parameters should be deleted from subnet
        """

    @stubbed()
    @tier2
    def test_positive_delete_subnet_parameter_host_impact(self):
        """Deleting parameter from subnet component deletes the parameter in
            host inheriting that subnet

        :id: e018e998-921a-4082-a75a-a51e845d64cc

        :steps:

            1. Create a subnet from Infrastructure menu
            2. Update all the details for subnet creation
            3. Add parameter in subnet parameters tab
            4. Save subnet changes
            5. Create host with the above subnet
            6. Edit the above subnet and click on 'remove' button to
                delete the parameter
            7. Save subnet changes
            8. Go to Host parameters tab

        :expectedresults: The parameter should be deleted from host
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_delete_subnet_parameter_overrided_host_impact(self):
        """Deleting parameter from subnet component doesnt deletes its
            overridden parameter in host inheriting that subnet

        :id: 58c89fbb-537c-4be5-a9ee-89f3593e9b19

        :steps:

            1. Create a subnet from Infrastructure menu
            2. Update all the details for subnet creation
            3. Add parameter in subnet parameters tab
            4. Save subnet changes
            5. Create host with the above subnet
            6. Override subnet parameter value from host
            7. Save host changes
            8. Edit the above subnet and click on 'remove' button to delete
                the parameter
            9. Save subnet changes
            10. Go to Host parameters tab

        :expectedresults: The parameter should not be deleted from host
            as it becomes host parameter now
        """
