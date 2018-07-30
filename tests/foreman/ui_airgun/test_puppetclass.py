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


def test_positive_delete(session):
    puppet_class = entities.PuppetClass().create()
    with session:
        session.puppetclass.delete(puppet_class.name)
        assert not session.puppetclass.search(puppet_class.name)
