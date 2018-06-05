# -*- encoding: utf-8 -*-
"""Test class for Locations UI

:Requirement: Location

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string


def test_positive_create(session):
    loc_name = gen_string('alpha')
    with session:
        session.location.create({
            'name': loc_name,
            'description': gen_string('alpha'),
        })
        assert session.location.search(loc_name)[0]['Name'] == loc_name
