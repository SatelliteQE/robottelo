from nailgun import entities

from robottelo.api.utils import (
    create_sync_custom_repo,
    cv_publish_promote,
    promote,
)
from robottelo.constants import DISTRO_RHEL6, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, skip_if_not_set, tier3
from robottelo.vm import VirtualMachine


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


def test_positive_create(session):
    ak_name = gen_string('alpha')
    with session:
        session.activationkey.create({
            'name': ak_name,
            'hosts_limit': 2,
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


@skip_if_not_set('clients')
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


@skip_if_not_set('clients')
@tier3
def test_negative_usage_limit(session, module_org):
    """Test that Usage limit actually limits usage

    :id: 9fe2d661-66f8-46a4-ae3f-0a9329494bdd

    :Steps:
        1. Create Activation key
        2. Update Usage Limit to a finite number
        3. Register Systems to match the Usage Limit
        4. Attempt to register an other system after reaching the Usage
            Limit

    :expectedresults: System Registration fails. Appropriate error shown

    :CaseLevel: System
    """
    name = gen_string('alpha')
    hosts_limit = '1'
    with session:
        session.activationkey.create({
            'name': name,
            'lce': {ENVIRONMENT: True},
        })
        assert session.activationkey.search(name) == name
        session.activationkey.update(name, values={'hosts_limit': hosts_limit})
        ak = session.activationkey.read(name)
        assert ak['hosts_limit'] == hosts_limit
    with VirtualMachine(distro=DISTRO_RHEL6) as vm1:
        with VirtualMachine(distro=DISTRO_RHEL6) as vm2:
            vm1.install_katello_ca()
            vm1.register_contenthost(module_org.label, name)
            assert vm1.subscribed
            vm2.install_katello_ca()
            result = vm2.register_contenthost(module_org.label, name)
            assert not vm2.subscribed
            assert len(result.stderr) > 0
            assert (
                'Max Hosts ({0}) reached for activation key'
                .format(hosts_limit)
                in result.stderr
            )
