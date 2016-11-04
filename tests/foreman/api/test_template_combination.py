# -*- coding: utf-8 -*-
"""Tests for template combination"""
from nailgun import entities
from robottelo.decorators import tier1, skip_if_bug_open
from robottelo.test import APITestCase


class TestTemplateCombination(APITestCase):
    """TemplateCombination tests"""

    @tier1
    @skip_if_bug_open('bugzilla', 1369737)
    def test_positive_deleting_combination(self):
        hostgroup = entities.HostGroup().create()
        env=entities.Environment().create()
        template = entities.ConfigTemplate(snippet=False).create()
        template.template_combinations.append({
            'hostgroup_id': hostgroup.id,
            'environment_id': env.id
        })
        print(repr(hostgroup))
        print(repr(env))
        print(repr(template))
        print(repr(template.update()))
