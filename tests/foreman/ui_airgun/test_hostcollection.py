"""Test class for Host Collection UI

:Requirement: Hostcollection

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.api.utils import promote
from robottelo.datafactory import gen_string
from robottelo.decorators import tier3


def test_positive_create(session):
    hc_name = gen_string('alpha')
    with session:
        session.hostcollection.create({
            'name': hc_name,
            'unlimited_hosts': False,
            'max_hosts': 3,
            'description': gen_string('alpha'),
        })
        assert session.hostcollection.search(hc_name) == hc_name


@tier3
def test_positive_add_host(session):
    """Check if host can be added to Host Collection

    :id: 80824c9f-15a1-4f76-b7ac-7d9ca9f6ed9e

    :expectedresults: Host is added to Host Collection successfully

    :CaseLevel: System
    """
    hc_name = gen_string('alpha')
    org = entities.Organization().create()
    cv = entities.ContentView(organization=org).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    cv.publish()
    promote(cv.read().version[0], lce.id)
    host = entities.Host(
        organization=org,
        content_facet_attributes={
            'content_view_id': cv.id,
            'lifecycle_environment_id': lce.id,
        },
    ).create()
    with session:
        session.organization.select(org_name=org.name)
        session.hostcollection.create({'name': hc_name})
        assert session.hostcollection.search(hc_name) == hc_name
        session.hostcollection.associate_host(hc_name, host.name)
        hc_values = session.hostcollection.read(hc_name)
        assert hc_values['hosts']['resources']['assigned'][0] == host.name
