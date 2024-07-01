"""Test class for Content View UI

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest


@pytest.mark.tier2
def test_positive_create_cv(session, target_sat):
    """Able to create cv and search for it

    :id: 15666f4e-d6e6-448a-97df-fede20cc2d1a

    :steps:
        1. Create a CV in the UI
        2. Search for the CV

    :expectedresults: CV is visible in the UI, and matches the given name

    :CaseImportance: High
    """
    cv = gen_string('alpha')
    with target_sat.ui_session() as session:
        session.contentview_new.create(dict(name=cv))
        assert session.contentview_new.search(cv)[0]['Name'] == cv


@pytest.mark.tier2
def test_no_blank_page_on_language_switch(session, target_sat, module_org):
    """Able to view the new CV UI when the language is set to something other
    than English

    :id: d8745aca-b199-4c7e-a970-b1f0f5c5d56c

    :steps:
        1. Change the Satellite system language to French
        2. Attempt to view the CV UI, and read the CV table

    :expectedresults: CV UI is visible, and isn't a blank page

    :BZ: 2163538

    :customerscenario: true
    """
    user_password = gen_string('alpha')
    user = target_sat.api.User(
        default_organization=module_org,
        organization=[module_org],
        password=user_password,
        admin=True,
    ).create()
    cv = target_sat.api.ContentView(organization=module_org).create()
    cv.publish()
    with target_sat.ui_session(user=user.login, password=user_password) as session:
        session.user.update(user.login, {'user.language': 'Français'})
        assert session.contentview_new.read_french_lang_cv()
