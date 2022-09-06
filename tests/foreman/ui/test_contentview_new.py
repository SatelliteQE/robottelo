"""Test class for Content View UI

Feature details: https://fedorahosted.org/katello/wiki/ContentViews


:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.datafactory import gen_string


@pytest.mark.tier2
def test_positive_create_cv_and_search_for_name(session):
    cv = gen_string('alpha')
    with session:
        session.contentview_new.create({'name': cv})
        assert session.contentview_new.search(cv)[0]['Name'] == cv


@pytest.mark.tier2
def test_positive_search_for_name(session, module_org):
    cv = entities.ContentView(organization=module_org).create()
    with session:
        assert session.contentview_new.search(cv.name)[0]['Name'] == cv
