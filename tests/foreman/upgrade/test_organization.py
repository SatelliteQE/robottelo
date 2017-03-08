# -*- encoding: utf-8 -*-

"""Test class for Organization PostUpgrade

:Requirement: Organization

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Structural

:CaseImportance: High

:Upstream: No
"""
from robottelo.cli.org import Org
from robottelo.datafactory import get_valid_preupgrade_data
from robottelo.decorators import tier1
from robottelo.test import CLITestCase


class OrganizationTestCase(CLITestCase):
    """Tests for Post Upgrade Organizations verification via Hammer CLI"""

    @tier1
    def test_positive_exits_org_by_id(self):
        """Test whether the Organization exists on Post Upgrade - id

        :id: da2821d0-1ea2-423d-8172-7372c98d8858

        :assert: Organization by id exists post Upgrade
        """
        for org, org_id in get_valid_preupgrade_data(
                'organization-tests', 'id'):
            with self.subTest(org_id):
                result = Org.exists(search=('name', org))
                self.assertEqual(str(org_id), result['id'])

    @tier1
    def test_positive_exists_org_by_name(self):
        """Test whether the Organization exists on Post Upgrade - name

        :id: 639c3fec-ed5d-4c05-a301-801e3b47efb8

        :assert: Organization by name exists post Upgrade
        """
        for org, org_name in get_valid_preupgrade_data(
                'organization-tests', 'name'):
            with self.subTest(org_name):
                result = Org.exists(search=('name', org))
                self.assertEqual(org_name, result['name'])

    @tier1
    def test_positive_association_org_smart_proxy(self):
        """Test Smart Proxy is associated with Organization

        :id: 9986ec9d-b37c-482c-9bb1-7c25f6bfd34c

        :assert: Smart Proxy is associated with Organization
        """
        for org, sp in get_valid_preupgrade_data(
                'organization-tests', 'smart-proxy'):
            with self.subTest(sp):
                result = Org.info({'name': org})
                self.assertIn(sp, result['smart-proxies'])

    @tier1
    def test_positive_association_org_template(self):
        """Test Template is associated with Organization

        :id: 2c8a6362-f95f-4aec-bc63-57242a639167

        :assert: Template is associated with Organization
        """
        for org, template in get_valid_preupgrade_data(
                'organization-tests', 'template'):
            with self.subTest(template):
                result = Org.info({'name': org})
                self.assertIn(template, result['templates'])

    @tier1
    def test_positive_association_org_puppet_environment(self):
        """Test Puppet Environment is associated with Organization

        :id: 12c6d711-c6d6-4bcb-9e24-01cadb205f7b

        :assert: Puppet Environment is associated with Organization
        """
        for org, penv in get_valid_preupgrade_data(
                'organization-tests', 'Puppet-Environments'):
            with self.subTest(penv):
                result = Org.info({'name': org})
                self.assertIn(penv, result['environments'])
