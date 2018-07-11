# -*- encoding: utf-8 -*-
"""Test class for Host Group UI

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string


def test_positive_create(session):
    name = gen_string('alpha')
    with session:
        session.hostgroup.create({'name': name})
        # TODO delete this line if bugzilla 1599303 is closed
        session.hostgroup.search(name)
        assert session.hostgroup.search(name)[0]['Name'] == name
