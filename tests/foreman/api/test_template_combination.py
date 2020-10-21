"""Tests for template combination

:Requirement: TemplateCombination

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ProvisioningTemplates

:TestType: Functional

:Upstream: No
"""
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.decorators import tier1
from robottelo.decorators import upgrade
from robottelo.test import APITestCase


class TemplateCombinationTestCase(APITestCase):
    """Implements TemplateCombination tests"""

    @classmethod
    def setUpClass(cls):
        """Create hostgroup and environment to be used on
        TemplateCombination creation
        """
        super().setUpClass()
        cls.hostgroup = entities.HostGroup().create()
        cls.env = entities.Environment().create()

    @classmethod
    def tearDownClass(cls):
        """Delete hostgroup and environment used on
        TemplateCombination creation
        """
        super().tearDownClass()
        for entity in (cls.hostgroup, cls.env):
            entity.delete()

    def setUp(self):
        """Create ProvisioningTemplate and TemplateConfiguration for each test"""
        super().setUp()
        self.template = entities.ProvisioningTemplate(
            snippet=False,
            template_combinations=[
                {'hostgroup_id': self.hostgroup.id, 'environment_id': self.env.id}
            ],
        )
        self.template = self.template.create()
        template_combination_dct = self.template.template_combinations[0]
        self.template_combination = entities.TemplateCombination(
            id=template_combination_dct['id'],
            environment=self.env,
            provisioning_template=self.template,
            hostgroup=self.hostgroup,
        )

    def tearDown(self):
        """Delete ProvisioningTemplate used on tests"""
        super().tearDown()
        # Clean combination if it is not already deleted
        try:
            self.template_combination.delete()
        except HTTPError:
            pass
        self.template.delete()

    @tier1
    def test_positive_get_combination(self):
        """Assert API template combination get method works.

        :id: 2447674e-c37e-11e6-93cb-68f72889dc7f

        :Setup: save a template combination

        :expectedresults: TemplateCombination can be retrieved through API

        :CaseImportance: Critical

        :BZ: 1369737
        """
        combination = self.template_combination.read()
        self.assertIsInstance(combination, entities.TemplateCombination)
        self.assertEqual(self.template.id, combination.provisioning_template.id)
        self.assertEqual(self.env.id, combination.environment.id)
        self.assertEqual(self.hostgroup.id, combination.hostgroup.id)

    @tier1
    @upgrade
    def test_positive_delete_combination(self):
        """Assert API template combination delete method works.

        :id: 3a5cb370-c5f6-11e6-bb2f-68f72889dc7f

        :Setup: save a template combination

        :expectedresults: TemplateCombination can be deleted through API

        :CaseImportance: Critical

        :BZ: 1369737
        """
        combination = self.template_combination.read()
        self.assertIsInstance(combination, entities.TemplateCombination)
        self.assertEqual(1, len(self.template.read().template_combinations))
        combination.delete()
        self.assertRaises(HTTPError, combination.read)
        self.assertEqual(0, len(self.template.read().template_combinations))
