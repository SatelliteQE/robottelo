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

from robottelo.datafactory import gen_string


@pytest.mark.tier2
def test_positive_create_cv(session):
    """Able to create cv and search for it

    :id: 1bad50d8-4909-47ef-8524-8c703c75069d

    :CaseLevel: System
    """
    cv = gen_string('alpha')
    with session:
        session.contentview_new.create(dict(name=cv))
        assert session.contentview_new.search(cv)[0]['Name'] == cv


@pytest.mark.tier2
def test_positive_search_for_cv(session, module_org, target_sat):
    """Able to search for a cv name

    :id: 4a097af5-66bf-4dce-8f79-25a5f60eb2cb

    :CaseLevel: System
    """
    cv = target_sat.api.ContentView(organization=module_org).create()
    with session:
        assert session.contentview_new.search(cv.name)[0]['Name'] == cv.name


@pytest.mark.tier1
def test_positive_publish(session, module_org, target_sat):
    cv = target_sat.api.ContentView(organization=module_org).create()
    with session:
        result = session.contentview_new.publish(cv.name)
        assert result['Version'] == 'Version 1.0'
