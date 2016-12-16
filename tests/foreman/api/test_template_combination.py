# -*- coding: utf-8 -*-
"""Tests for template combination

@Requirement: TemplateCombination

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: Medium

@Upstream: No
"""
from nailgun import entities

from robottelo.decorators import tier1, skip_if_bug_open
from robottelo.test import APITestCase


def _delete_entities(*entities):
    for ent in entities:
        ent.delete()


class TemplateCombinationTestCase(APITestCase):
    """Implements TemplateCombination tests"""

    @classmethod
    def setUpClass(cls):
        super(TemplateCombinationTestCase, cls).setUpClass()
        cls.hostgroup = entities.HostGroup().create()
        cls.env = entities.Environment().create()

    @classmethod
    def tearDownClass(cls):
        super(TemplateCombinationTestCase, cls).tearDownClass()
        _delete_entities(cls.hostgroup, cls.env)

    def setUp(self):
        super(TemplateCombinationTestCase, self).setUp()
        self.template = entities.ConfigTemplate(
            snippet=False,
            template_combinations=[{
                'hostgroup_id':
                    self.hostgroup.id,
                'environment_id': self.env.id
            }])
        self.template = self.template.create()
        template_combination_dct = self.template.template_combinations[0]
        self.template_combination = entities.TemplateCombination(
            id=template_combination_dct['id'],
            environment=self.env,
            config_template=self.template,
            hostgroup=self.hostgroup
        )

    def tearDown(self):
        super(TemplateCombinationTestCase, self).tearDown()
        _delete_entities(self.template_combination, self.template)

    @tier1
    @skip_if_bug_open('bugzilla', 1369737)
    def test_positive_get_combination(self):
        """Assert API template combination get method works. Delete is
        indirectly tested on tearDown

        @id: 2447674e-c37e-11e6-93cb-68f72889dc7f

        @Setup: save a template combination
        """
        combination = self.template_combination.read()
        self.assertIsInstance(combination, entities.TemplateCombination)
        self.assertEqual(self.template.id, combination.config_template.id)
        self.assertEqual(self.env.id, combination.environment.id)
        self.assertEqual(self.hostgroup.id, combination.hostgroup.id)
