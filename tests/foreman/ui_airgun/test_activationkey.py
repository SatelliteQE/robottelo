from nailgun import entities

from robottelo.datafactory import gen_string
from robottelo.api.utils import promote


def test_positive_create(session):
    ak_name = gen_string('alpha')
    with session:
        session.activationkey.create({
            'name': ak_name,
            'unlimited_hosts': False,
            'max_hosts': 2,
            'description': gen_string('alpha'),
        })
        assert session.activationkey.search(ak_name) == ak_name


def test_positive_create_with_lce_and_cv(session):
    ak_name = gen_string('alpha')
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    content_view = entities.ContentView(organization=org).create()
    content_view.publish()
    promote(content_view.read().version[0], lce.id)
    with session:
        session.organization.select(org_name=org.name)
        session.activationkey.create({
            'name': ak_name,
            'lce': {lce.name: True},
            'content_view': content_view.name
        })
        assert session.activationkey.search(ak_name) == ak_name
        ak_values = session.activationkey.read(ak_name)
        assert {'name': lce.name, 'value': True} in ak_values['lce']


def test_positive_delete(session):
    name = gen_string('alpha')
    org = entities.Organization().create()
    entities.ActivationKey(name=name, organization=org).create()
    with session:
        session.organization.select(org_name=org.name)
        assert session.activationkey.search(name) == name
        session.activationkey.delete(name)
        assert session.activationkey.search(name) is None
