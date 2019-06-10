"""Tests for Oscapcontent

:Requirement: Oscapcontent

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import ANY_CONTEXT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade


@fixture(scope='module')
def oscap_content_path():
    return settings.oscap.content_path


@tier2
@upgrade
def test_positive_end_to_end(session, oscap_content_path):
    """Perform end to end testing for openscap content component

    :id: 9870555d-0b60-41ab-a481-81d4d3f78fec

    :Steps:

        1. Create an openscap content.
        2. Read values from created entity.
        3. Update the openscap content with new name.
        4. Delete openscap content

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration
    """
    title = gen_string('alpha')
    new_title = gen_string('alpha')
    org = entities.Organization().create()
    loc = entities.Location().create()
    with session:
        session.oscapcontent.create({
            'file_upload.title': title,
            'file_upload.scap_file': oscap_content_path,
            'organizations.resources.assigned': [org.name],
            'locations.resources.assigned': [loc.name],
        })
        oscap_values = session.oscapcontent.read(title)
        assert oscap_values['file_upload']['title'] == title
        assert oscap_values['file_upload'][
            'uploaded_scap_file'] == oscap_content_path.rsplit('/', 1)[-1]
        assert org.name in oscap_values['organizations']['resources']['assigned']
        assert loc.name in oscap_values['locations']['resources']['assigned']
        session.oscapcontent.update(title, {'file_upload.title': new_title})
        assert session.oscapcontent.search(new_title)[0]['Title'] == new_title
        assert not session.oscapcontent.search(title)
        session.oscapcontent.delete(new_title)
        assert not session.oscapcontent.search(new_title)


@tier2
def test_negative_create_with_same_name(session, oscap_content_path):
    """Create OpenScap content with same name

    :id: f5c6491d-b83c-4ca2-afdf-4bb93e6dd92b

    :Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.
        3. Create openscap content with same name

    :expectedresults: Creating content for OpenScap is not successful.

    :BZ: 1474172

    :customerscenario: true

    :CaseImportance: Critical
    """
    content_name = gen_string('alpha')
    with session:
        session.organization.select(org_name=ANY_CONTEXT['org'])
        session.location.select(loc_name=ANY_CONTEXT['location'])
        session.oscapcontent.create({
            'file_upload.title': content_name,
            'file_upload.scap_file': oscap_content_path,
        })
        assert session.oscapcontent.search(content_name)[0]['Title'] == content_name
        with pytest.raises(AssertionError) as context:
            session.oscapcontent.create({
                'file_upload.title': content_name,
                'file_upload.scap_file': oscap_content_path,
            })
        assert 'has already been taken' in str(context.value)
