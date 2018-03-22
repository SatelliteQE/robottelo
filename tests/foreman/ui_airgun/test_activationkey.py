from nailgun import entities

from robottelo.api.utils import (
    create_sync_custom_repo,
    cv_publish_promote,
    promote,
)
from robottelo.constants import DISTRO_RHEL6
from robottelo.datafactory import gen_string
from robottelo.decorators import tier3
from robottelo.vm import VirtualMachine


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


def test_positive_edit(session):
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    org = entities.Organization().create()
    entities.ActivationKey(name=name, organization=org).create()
    with session:
        session.organization.select(org_name=org.name)
        assert session.activationkey.search(name) == name
        session.activationkey.update(
            name,
            values={
                'name': new_name,
                'description': description,
            },
        )
        ak_values = session.activationkey.read(new_name)
        assert ak_values['name'] == new_name
        assert ak_values['description'] == description


@tier3
def test_positive_delete_with_system(session):
    """Delete an Activation key which has registered systems

    :id: 86cd070e-cf46-4bb1-b555-e7cb42e4dc9f

    :Steps:
        1. Create an Activation key
        2. Register systems to it
        3. Delete the Activation key

    :expectedresults: Activation key is deleted

    :CaseLevel: System
    """
    name = gen_string('alpha')
    cv_name = gen_string('alpha')
    env_name = gen_string('alpha')
    product_name = gen_string('alpha')
    org = entities.Organization().create()
    # Helper function to create and promote CV to next environment
    repo_id = create_sync_custom_repo(product_name=product_name, org_id=org.id)
    cv_publish_promote(cv_name, env_name, repo_id, org.id)
    with session:
        session.organization.select(org_name=org.name)
        session.activationkey.create({
            'name': name,
            'lce': {env_name: True},
            'content_view': cv_name
        })
        assert session.activationkey.search(name) == name
        session.activationkey.associate_product(name, product_name)
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(org.label, name)
            assert vm.subscribed
            session.activationkey.delete(name)
            assert session.activationkey.search(name) is None
