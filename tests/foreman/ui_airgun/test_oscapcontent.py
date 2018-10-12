"""Tests for Oscapcontent

:Requirement: Oscapcontent

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.config import settings
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2


@fixture(scope='module')
def oscap_content_path():
    return settings.oscap.content_path


@tier2
def test_positive_update(session, oscap_content_path):
    """Update OpenScap content.

    :id: 9870555d-0b60-41ab-a481-81d4d3f78fec

    :Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.
        3. Update the openscap content, here the Org.

    :expectedresults: Whether updating content for OpenScap is successful.

    :CaseLevel: Integration
    """
    title = gen_string('alpha')
    org = entities.Organization().create()
    with session:
        session.oscapcontent.create({
            'file_upload.title': title,
            'file_upload.scap_file': oscap_content_path,
        })
        session.oscapcontent.update(title, {
            'organizations.resources.assigned': [org.name]
        })
        oscap_val = session.oscapcontent.read(title)
        assert org.name in oscap_val['organizations']['resources']['assigned']
