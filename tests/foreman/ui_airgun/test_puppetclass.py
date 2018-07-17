# -*- encoding: utf-8 -*-
"""Test class for Puppet Classes UI

:Requirement: Puppetclass

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from nailgun import entities

from robottelo.datafactory import gen_string


def test_positive_delete(session):
    name = gen_string('alpha')
    entities.PuppetClass(name=name).create()
    with session:
        session.puppetclass.delete(name)
        assert not session.puppetclass.search(name)
