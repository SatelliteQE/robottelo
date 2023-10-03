"""Test class for Content View UI

:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No

import pytest
from fauxfactory import gen_string

from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


@pytest.mark.tier2
def test_positive_create_cv(session, target_sat):
    """Able to create cv and search for it

    :id: 15666f4e-d6e6-448a-97df-fede20cc2d1a

    :steps:
        1. Create a CV in the UI
        2. Search for the CV

    :expectedresults: CV is visible in the UI, and matches the given name

    :CaseLevel: System

    :CaseImportance: High
    """
    cv = gen_string('alpha')
    with target_sat.ui_session() as session:
        session.contentview_new.create(dict(name=cv))
        assert session.contentview_new.search(cv)[0]['Name'] == cv

        
@pytest.mark.tier2
def test_different_org_publish(
    session, target_sat, module_entitlement_manifest_org, module_lce, module_location
):
    """
    :id: 27e9f33c-9b06-4034-a8e1-3416cd8e636a

    :steps:
        1. Create a content view and attach a RHEL 7 repo to it. Publish the CV
        2. In UI, subscribe a content host in Organization 'A' and Location 'B' to the CV.
        3. In UI, set your current Organization as 'A' and current Location as 'C'.
        4. Publish the content view.

    :expectedresults: CV is successfully published with a different location than
    the subscribed host

    :bz:2190473
    """
    cv = target_sat.api.ContentView(organization=module_entitlement_manifest_org).create()
    new_loc = target_sat.api.Location().create()
    repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_entitlement_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    repo = target_sat.api.Repository(id=repo_id)
    repo.sync()
    cv.repository = [repo]
    cv.update(['repository'])
    cv.publish()
    target_sat.api.Host(
        organization=module_entitlement_manifest_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': cv.id,
            'lifecycle_environment_id': module_lce.id,
        },
    ).create()
    with target_sat.ui_session() as session:
        session.location.select(loc_name=new_loc.name)
        session.organization.select(org_name=module_entitlement_manifest_org.name)
        response = session.contentview_new.publish(cv.name)
        assert response[0]['Version'] == 'Version 2.0'

