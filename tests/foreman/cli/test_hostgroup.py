# -*- encoding: utf-8 -*-
"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI.

@Requirement: Hostgroup

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.proxy import Proxy
from robottelo.cli.factory import (
    make_environment,
    make_hostgroup,
    make_location,
    make_org,
    make_os,
)
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_hostgroups_list,
)
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


class HostGroupTestCase(CLITestCase):
    """Test class for Host Group CLI"""

    @tier1
    def test_positive_create_with_name(self):
        """Successfully creates an HostGroup.

        @id: f5f2056f-d090-4e0d-8fb9-d29255a47908

        @Assert: HostGroup is created.
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                self.assertEqual(hostgroup['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an HostGroup with invalid data.

        @id: 853a6d43-129a-497b-94f0-08dc622862f8

        @Assert: HostGroup is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.create({'name': name})

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_env(self):
        """Check if hostgroup with environment can be created

        @id: f1bfb333-90cf-4a9f-b183-cf77c1773247

        @Assert: Hostgroup is created and has new environment assigned

        """
        environment = make_environment()
        hostgroup = make_hostgroup({'environment-id': environment['id']})
        self.assertEqual(environment['name'], hostgroup['environment'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_loc(self):
        """Check if hostgroup with location can be created

        @id: 84ae02a4-ea7e-43ce-87bd-7bbde3766b14

        @Assert: Hostgroup is created and has new location assigned

        """
        location = make_location()
        hostgroup = make_hostgroup({'location-ids': location['id']})
        self.assertIn(location['name'], hostgroup['locations'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_os(self):
        """Check if hostgroup with operating system can be created

        @id: d12c5939-1aac-44f5-8aa3-a04a824f4e83

        @Assert: Hostgroup is created and has operating system assigned

        """
        os = make_os()
        hostgroup = make_hostgroup({'operatingsystem-id': os['id']})
        self.assertEqual(hostgroup['operating-system'], os['title'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_org(self):
        """Check if hostgroup with organization can be created

        @id: 780d4b93-f35a-4c5b-a645-4053aed4c37b

        @Assert: Hostgroup is created and has new organization assigned

        """
        org = make_org()
        hostgroup = make_hostgroup({'organization-ids': org['id']})
        self.assertIn(org['name'], hostgroup['organizations'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_ca_proxy(self):
        """Check if hostgroup with puppet CA proxy server can be created

        @id: f7ea1c94-8a0e-4500-98b3-0ecd63b3ce3c

        @Assert: Hostgroup is created and has puppet CA proxy server assigned

        """
        puppet_proxy = Proxy.list()[0]
        hostgroup = make_hostgroup({'puppet-ca-proxy': puppet_proxy['name']})
        self.assertEqual(puppet_proxy['id'], hostgroup['puppet-ca-proxy-id'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_proxy(self):
        """Check if hostgroup with puppet proxy server can be created

        @id: 3a922d9f-7466-4565-b279-c1481f63a4ce

        @Assert: Hostgroup is created and has puppet proxy server assigned

        """
        puppet_proxy = Proxy.list()[0]
        hostgroup = make_hostgroup({'puppet-proxy': puppet_proxy['name']})
        self.assertEqual(
            puppet_proxy['id'],
            hostgroup['puppet-master-proxy-id'],
        )

    @tier1
    def test_positive_update_name(self):
        """Successfully update an HostGroup.

        @id: a36e3cbe-83d9-44ce-b8f7-5fab2a2cadf9

        @Assert: HostGroup is updated.
        """
        hostgroup = make_hostgroup()
        for new_name in valid_hostgroups_list():
            with self.subTest(new_name):
                HostGroup.update({
                    'id': hostgroup['id'],
                    'new-name': new_name,
                })
                hostgroup = HostGroup.info({'id': hostgroup['id']})
                self.assertEqual(hostgroup['name'], new_name)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Create HostGroup then fail to update its name

        @id: 42d208a4-f518-4ff2-9b7a-311adb460abd

        @assert: HostGroup name is not updated
        """
        hostgroup = make_hostgroup()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.update({
                        'id': hostgroup['id'],
                        'new-name': new_name,
                    })
                result = HostGroup.info({'id': hostgroup['id']})
                self.assertEqual(hostgroup['name'], result['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_id(self):
        """Create HostGroup with valid values then delete it
        by ID

        @id: fe7dedd4-d7c3-4c70-b70d-c2deff357b76

        @assert: HostGroup is deleted
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = make_hostgroup({'name': name})
                HostGroup.delete({'id': hostgroup['id']})
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.info({'id': hostgroup['id']})

    @run_only_on('sat')
    @tier1
    def test_negative_delete_by_id(self):
        """Create HostGroup then delete it by wrong ID

        @id: 047c9f1a-4dd6-4fdc-b7ed-37cc725c68d3

        @assert: HostGroup is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    HostGroup.delete({'id': entity_id})
