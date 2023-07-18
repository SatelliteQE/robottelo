"""Test class for Content View UI

:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string


@pytest.mark.tier2
def test_positive_create_cv(session, target_sat):
    """Able to create cv and search for it
    :id: 1bad50d8-4909-47ef-8524-8c703c75069d

    :CaseLevel: System
    """
    cv = gen_string('alpha')
    with target_sat.ui_session() as session:
        session.contentview_new.create(dict(name=cv))
        assert session.contentview_new.search(cv)[0]['Name'] == cv
