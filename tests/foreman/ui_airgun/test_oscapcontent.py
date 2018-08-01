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
from robottelo.decorators import tier2


def test_positive_create(session):
    title = gen_string('alpha')
    oscap_content_path = settings.oscap.content_path
    with session:
        session.oscapcontent.upload_new({
            'title': title,
            'scap_file': oscap_content_path,
        })
        assert session.oscapcontent.search(title)[0]['Title'] == title


def test_positive_delete(session):
    title = gen_string('alpha')
    oscap_content_path = settings.oscap.content_path
    with session:
        session.oscapcontent.upload_new({
            'title': title,
            'scap_file': oscap_content_path,
        })
        session.oscapcontent.delete(title)
        assert not session.oscapcontent.search(title)


@tier2
def test_positive_update(session):
    """Update OpenScap content.

    :id: 9870555d-0b60-41ab-a481-81d4d3f78fec

    :Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.
        3. Update the openscap content, here the Org.

    :expectedresults: Whether creating  content for OpenScap is successful.

    :CaseLevel: Integration
    """
    title = gen_string('alpha')
    org = entities.Organization().create()
    oscap_content_path = settings.oscap.content_path
    with session:
        session.oscapcontent.upload_new({
            'title': title,
            'scap_file': oscap_content_path,
        })
        session.oscapcontent.edit(title, {
            'organizations.resources.assigned': [org.name]
        })
        oscap_val = session.oscapcontent.read(title)
        assert org.name in oscap_val['organizations']['resources']['assigned']
