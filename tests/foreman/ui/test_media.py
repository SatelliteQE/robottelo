"""Test class for Media UI

:Requirement: Media

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo.constants import INSTALL_MEDIUM_URL
from robottelo.decorators import fixture, tier2, upgrade


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc(module_org):
    return entities.Location(organization=[module_org]).create()


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for media component

    :id: fb7a248a-21ef-43b2-a488-8d7628a55ccd

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    path = INSTALL_MEDIUM_URL % gen_string('alpha', 6)
    with session:
        # Create new media
        session.media.create({
            'medium.name': name,
            'medium.path': path,
            'medium.os_family': 'Windows',
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        assert session.media.search(name)[0]['Name'] == name
        media_values = session.media.read(name)
        assert media_values['medium']['name'] == name
        assert media_values['medium']['path'] == path
        assert media_values['medium']['os_family'] == 'Windows'
        assert media_values['organizations']['resources']['assigned'] == [module_org.name]
        assert media_values['locations']['resources']['assigned'] == [module_loc.name]
        # Update media with new name
        session.media.update(name, {'medium.name': new_name})
        assert session.media.search(new_name)[0]['Name'] == new_name
        # Delete media
        session.media.delete(new_name)
        assert not session.media.search(new_name)
