"""Test class for Activation key UI

:Requirement: Activationkey

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ActivationKeys

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from airgun.session import Session
from broker import VMBroker
from fauxfactory import gen_string
from nailgun import entities

from robottelo import constants
from robottelo import manifests
from robottelo.api.utils import create_role_permissions
from robottelo.api.utils import create_sync_custom_repo
from robottelo.api.utils import cv_publish_promote
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import enable_sync_redhat_repo
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.config import settings
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.hosts import ContentHost
from robottelo.products import RepositoryCollection
from robottelo.products import SatelliteToolsRepository


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end_crud(session, module_org):
    """Perform end to end testing for activation key component

    :id: b6b98c45-e41e-4c7a-9be4-997273b7e24d

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    cv = entities.ContentView(organization=module_org).create()
    cv.publish()
    with session:
        # Create activation key with content view and LCE assigned
        session.activationkey.create(
            {'name': name, 'lce': {constants.ENVIRONMENT: True}, 'content_view': cv.name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        # Verify content view and LCE are assigned
        ak_values = session.activationkey.read(name, widget_names='details')
        assert ak_values['details']['name'] == name
        assert ak_values['details']['content_view'] == cv.name
        assert ak_values['details']['lce'][constants.ENVIRONMENT][constants.ENVIRONMENT]
        # Update activation key with new name
        session.activationkey.update(name, {'details.name': new_name})
        assert session.activationkey.search(new_name)[0]['Name'] == new_name
        assert session.activationkey.search(name)[0]['Name'] != name
        # Delete activation key
        session.activationkey.delete(new_name)
        assert session.activationkey.search(new_name)[0]['Name'] != new_name


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_end_to_end_register(session, rhel7_contenthost, default_sat):
    """Create activation key and use it during content host registering

    :id: dfaecf6a-ba61-47e1-87c5-f8966a319b41

    :expectedresults: Content host was registered successfully using activation
        key, association is reflected on webUI

    :CaseLevel: System

    :CaseImportance: High
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=constants.DISTRO_RHEL7, repositories=[SatelliteToolsRepository()]
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    ak_name = repos_collection.setup_content_data['activation_key']['name']

    repos_collection.setup_virtual_machine(rhel7_contenthost, default_sat)
    with session:
        session.organization.select(org.name)
        chost = session.contenthost.read(rhel7_contenthost.hostname, widget_names='details')
        assert chost['details']['registered_by'] == f'Activation Key {ak_name}'
        ak_values = session.activationkey.read(ak_name, widget_names='content_hosts')
        assert len(ak_values['content_hosts']['table']) == 1
        assert ak_values['content_hosts']['table'][0]['Name'] == rhel7_contenthost.hostname


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.parametrize('cv_name', **parametrized(valid_data_list('ui')))
def test_positive_create_with_cv(session, module_org, cv_name):
    """Create Activation key for all variations of Content Views

    :id: 2ad000f1-6c80-46aa-a61b-9ea62cefe91b

    :parametrized: yes

    :expectedresults: Activation key is created

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    env_name = gen_string('alpha')
    repo_id = create_sync_custom_repo(module_org.id)
    cv_publish_promote(cv_name, env_name, repo_id, module_org.id)
    with session:
        session.activationkey.create(
            {'name': name, 'lce': {env_name: True}, 'content_view': cv_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['content_view'] == cv_name


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_search_scoped(session, module_org):
    """Test scoped search for different activation key parameters

    :id: 2c2ee1d7-0997-4a89-8f0a-b04e4b6177c0

    :customerscenario: true

    :expectedresults: Search functionality returns correct activation key

    :BZ: 1259374

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    env_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    description = gen_string('alpha')
    repo_id = create_sync_custom_repo(module_org.id)
    cv_publish_promote(cv_name, env_name, repo_id, module_org.id)
    with session:
        session.activationkey.create(
            {
                'name': name,
                'description': description,
                'lce': {env_name: True},
                'content_view': cv_name,
            }
        )
        for query_type, query_value in [
            ('content_view', cv_name),
            ('environment', env_name),
            ('description', description),
        ]:
            assert session.activationkey.search(f'{query_type} = {query_value}')[0]['Name'] == name


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_create_with_host_collection(session, module_org):
    """Create Activation key with Host Collection

    :id: 0e4ad2b4-47a7-4087-828f-2b0535a97b69

    :expectedresults: Activation key is created

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    hc = entities.HostCollection(organization=module_org).create()
    with session:
        session.activationkey.create({'name': name, 'lce': {constants.ENVIRONMENT: True}})
        assert session.activationkey.search(name)[0]['Name'] == name
        session.activationkey.add_host_collection(name, hc.name)
        ak = session.activationkey.read(name, widget_names='host_collections')
        assert ak['host_collections']['resources']['assigned'][0]['Name'] == hc.name


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_create_with_envs(session, module_org):
    """Create Activation key with lifecycle environment

    :id: f75e994a-6da1-40a3-9685-f8387388b3f0

    :expectedresults: Activation key is created

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    cv_name = gen_string('alpha')
    env_name = gen_string('alphanumeric')
    # Helper function to create and sync custom repository
    repo_id = create_sync_custom_repo(module_org.id)
    # Helper function to create and promote CV to next env
    cv_publish_promote(cv_name, env_name, repo_id, module_org.id)
    with session:
        session.activationkey.create(
            {'name': name, 'lce': {env_name: True}, 'content_view': cv_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['lce'][env_name][env_name]


@pytest.mark.tier2
def test_positive_add_host_collection_non_admin(module_org, test_name):
    """Test that host collection can be associated to Activation Keys by
    non-admin user.

    :id: 417f0b36-fd49-4414-87ab-6f72a09696f2

    :expectedresults: Activation key is created, added host collection is
        listed

    :BZ: 1473212

    :CaseLevel: Integration
    """
    ak_name = gen_string('alpha')
    hc = entities.HostCollection(organization=module_org).create()
    # Create non-admin user with specified permissions
    roles = [entities.Role().create()]
    user_permissions = {
        'Katello::ActivationKey': constants.PERMISSIONS['Katello::ActivationKey'],
        'Katello::HostCollection': constants.PERMISSIONS['Katello::HostCollection'],
    }
    viewer_role = entities.Role().search(query={'search': 'name="Viewer"'})[0]
    roles.append(viewer_role)
    create_role_permissions(roles[0], user_permissions)
    password = gen_string('alphanumeric')
    user = entities.User(
        admin=False, role=roles, password=password, organization=[module_org]
    ).create()
    with Session(test_name, user=user.login, password=password) as session:
        session.activationkey.create({'name': ak_name, 'lce': {constants.ENVIRONMENT: True}})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        session.activationkey.add_host_collection(ak_name, hc.name)
        ak = session.activationkey.read(ak_name, widget_names='host_collections')
        assert ak['host_collections']['resources']['assigned'][0]['Name'] == hc.name


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_remove_host_collection_non_admin(module_org, test_name):
    """Test that host collection can be removed from Activation Keys by
    non-admin user.

    :id: 187456ec-5690-4524-9701-8bdb74c7912a

    :expectedresults: Activation key is created, removed host collection is not
        listed

    :CaseLevel: Integration
    """
    ak_name = gen_string('alpha')
    hc = entities.HostCollection(organization=module_org).create()
    # Create non-admin user with specified permissions
    roles = [entities.Role().create()]
    user_permissions = {
        'Katello::ActivationKey': constants.PERMISSIONS['Katello::ActivationKey'],
        'Katello::HostCollection': constants.PERMISSIONS['Katello::HostCollection'],
    }
    viewer_role = entities.Role().search(query={'search': 'name="Viewer"'})[0]
    roles.append(viewer_role)
    create_role_permissions(roles[0], user_permissions)
    password = gen_string('alphanumeric')
    user = entities.User(
        admin=False, role=roles, password=password, organization=[module_org]
    ).create()
    with Session(test_name, user=user.login, password=password) as session:
        session.activationkey.create({'name': ak_name, 'lce': {constants.ENVIRONMENT: True}})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        session.activationkey.add_host_collection(ak_name, hc.name)
        ak = session.activationkey.read(ak_name, widget_names='host_collections')
        assert ak['host_collections']['resources']['assigned'][0]['Name'] == hc.name
        # remove Host Collection
        session.activationkey.remove_host_collection(ak_name, hc.name)
        ak = session.activationkey.read(ak_name, widget_names='host_collections')
        assert not ak['host_collections']['resources']['assigned']


@pytest.mark.tier2
def test_positive_delete_with_env(session, module_org):
    """Create Activation key with environment and delete it

    :id: b6019881-3d6e-4b75-89f5-1b62aff3b1ca

    :expectedresults: Activation key is deleted

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    cv_name = gen_string('alpha')
    env_name = gen_string('alpha')
    # Helper function to create and promote CV to next environment
    repo_id = create_sync_custom_repo(module_org.id)
    cv_publish_promote(cv_name, env_name, repo_id, module_org.id)
    with session:
        session.activationkey.create({'name': name, 'lce': {env_name: True}})
        assert session.activationkey.search(name)[0]['Name'] == name
        session.activationkey.delete(name)
        assert session.activationkey.search(name)[0]['Name'] != name


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_with_cv(session, module_org):
    """Create Activation key with content view and delete it

    :id: 7e40e1ed-8314-406b-9451-05f64806a6e6

    :expectedresults: Activation key is deleted

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    cv_name = gen_string('alpha')
    env_name = gen_string('alpha')
    # Helper function to create and promote CV to next environment
    repo_id = create_sync_custom_repo(module_org.id)
    cv_publish_promote(cv_name, env_name, repo_id, module_org.id)
    with session:
        session.activationkey.create(
            {'name': name, 'lce': {env_name: True}, 'content_view': cv_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        session.activationkey.delete(name)
        assert session.activationkey.search(name)[0]['Name'] != name


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_update_env(session, module_org):
    """Update Environment in an Activation key

    :id: 895cda6a-bb1e-4b94-a858-95f0be78a17b

    :expectedresults: Activation key is updated

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    cv_name = gen_string('alpha')
    env_name = gen_string('alphanumeric')
    # Helper function to create and promote CV to next environment
    repo_id = create_sync_custom_repo(module_org.id)
    cv_publish_promote(cv_name, env_name, repo_id, module_org.id)
    with session:
        session.activationkey.create({'name': name, 'lce': {constants.ENVIRONMENT: True}})
        assert session.activationkey.search(name)[0]['Name'] == name
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['lce'][env_name][constants.ENVIRONMENT]
        assert not ak['details']['lce'][env_name][env_name]
        session.activationkey.update(name, {'details.lce': {env_name: True}})
        ak = session.activationkey.read(name, widget_names='details')
        assert not ak['details']['lce'][env_name][constants.ENVIRONMENT]
        assert ak['details']['lce'][env_name][env_name]


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.parametrize('cv2_name', **parametrized(valid_data_list('ui')))
def test_positive_update_cv(session, module_org, cv2_name):
    """Update Content View in an Activation key

    :id: 68880ca6-acb9-4a16-aaa0-ced680126732

    :parametrized: yes

    :Steps:
        1. Create Activation key
        2. Update the Content view with another Content view which has custom
            products

    :expectedresults: Activation key is updated

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    env1_name = gen_string('alpha')
    env2_name = gen_string('alpha')
    cv1_name = gen_string('alpha')
    # Helper function to create and promote CV to next environment
    repo1_id = create_sync_custom_repo(module_org.id)
    cv_publish_promote(cv1_name, env1_name, repo1_id, module_org.id)
    repo2_id = create_sync_custom_repo(module_org.id)
    cv_publish_promote(cv2_name, env2_name, repo2_id, module_org.id)
    with session:
        session.activationkey.create(
            {'name': name, 'lce': {env1_name: True}, 'content_view': cv1_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['content_view'] == cv1_name
        session.activationkey.update(
            name, {'details': {'lce': {env2_name: True}, 'content_view': cv2_name}}
        )
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['content_view'] == cv2_name


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
def test_positive_update_rh_product(session):
    """Update Content View in an Activation key

    :id: 9b0ac209-45de-4cc4-97e8-e191f3f37239

    :Steps:

        1. Create an activation key
        2. Update the content view with another content view which has RH
            products

    :expectedresults: Activation key is updated

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    env1_name = gen_string('alpha')
    env2_name = gen_string('alpha')
    cv1_name = gen_string('alpha')
    cv2_name = gen_string('alpha')
    rh_repo1 = {
        'name': constants.REPOS['rhva6']['name'],
        'product': constants.PRDS['rhel'],
        'reposet': constants.REPOSET['rhva6'],
        'basearch': constants.DEFAULT_ARCHITECTURE,
        'releasever': constants.DEFAULT_RELEASE_VERSION,
    }
    rh_repo2 = {
        'name': ('Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs i386 6Server'),
        'product': constants.PRDS['rhel'],
        'reposet': constants.REPOSET['rhva6'],
        'basearch': 'i386',
        'releasever': constants.DEFAULT_RELEASE_VERSION,
    }
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    repo1_id = enable_sync_redhat_repo(rh_repo1, org.id)
    cv_publish_promote(cv1_name, env1_name, repo1_id, org.id)
    repo2_id = enable_sync_redhat_repo(rh_repo2, org.id)
    cv_publish_promote(cv2_name, env2_name, repo2_id, org.id)
    with session:
        session.organization.select(org.name)
        session.activationkey.create(
            {'name': name, 'lce': {env1_name: True}, 'content_view': cv1_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['content_view'] == cv1_name
        session.activationkey.update(
            name, {'details': {'lce': {env2_name: True}, 'content_view': cv2_name}}
        )
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['content_view'] == cv2_name


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
def test_positive_add_rh_product(session):
    """Test that RH product can be associated to Activation Keys

    :id: d805341b-6d2f-4e16-8cb4-902de00b9a6c

    :expectedresults: RH products are successfully associated to Activation key

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    cv_name = gen_string('alpha')
    env_name = gen_string('alpha')
    rh_repo = {
        'name': constants.REPOS['rhva6']['name'],
        'product': constants.PRDS['rhel'],
        'reposet': constants.REPOSET['rhva6'],
        'basearch': constants.DEFAULT_ARCHITECTURE,
        'releasever': constants.DEFAULT_RELEASE_VERSION,
    }
    # Create new org to import manifest
    org = entities.Organization().create()
    # Upload manifest
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    # Helper function to create and promote CV to next environment
    repo_id = enable_sync_redhat_repo(rh_repo, org.id)
    cv_publish_promote(cv_name, env_name, repo_id, org.id)
    with session:
        session.organization.select(org.name)
        session.activationkey.create(
            {'name': name, 'lce': {env_name: True}, 'content_view': cv_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        session.activationkey.add_subscription(name, constants.DEFAULT_SUBSCRIPTION_NAME)
        ak = session.activationkey.read(name, widget_names='subscriptions')
        subs_name = ak['subscriptions']['resources']['assigned'][0]['Repository Name']
        assert subs_name == constants.DEFAULT_SUBSCRIPTION_NAME


@pytest.mark.tier2
def test_positive_add_custom_product(session, module_org):
    """Test that custom product can be associated to Activation Keys

    :id: e66db2bf-517a-46ff-ba23-9f9744bef884

    :expectedresults: Custom products are successfully associated to Activation
        key

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    cv_name = gen_string('alpha')
    env_name = gen_string('alpha')
    product_name = gen_string('alpha')
    # Helper function to create and promote CV to next environment
    repo_id = create_sync_custom_repo(org_id=module_org.id, product_name=product_name)
    cv_publish_promote(cv_name, env_name, repo_id, module_org.id)
    with session:
        session.activationkey.create(
            {'name': name, 'lce': {env_name: True}, 'content_view': cv_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        session.activationkey.add_subscription(name, product_name)
        ak = session.activationkey.read(name, widget_names='subscriptions')
        assigned_prod = ak['subscriptions']['resources']['assigned'][0]['Repository Name']
        assert assigned_prod == product_name


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_add_rh_and_custom_products(session):
    """Test that RH/Custom product can be associated to Activation keys

    :id: 3d8876fa-1412-47ca-a7a4-bce2e8baf3bc

    :Steps:
        1. Create Activation key
        2. Associate RH product(s) to Activation Key
        3. Associate custom product(s) to Activation Key

    :expectedresults: RH/Custom product is successfully associated to
        Activation key

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    rh_repo = {
        'name': constants.REPOS['rhva6']['name'],
        'product': constants.PRDS['rhel'],
        'reposet': constants.REPOSET['rhva6'],
        'basearch': constants.DEFAULT_ARCHITECTURE,
        'releasever': constants.DEFAULT_RELEASE_VERSION,
    }
    custom_product_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    org = entities.Organization().create()
    product = entities.Product(name=custom_product_name, organization=org).create()
    repo = entities.Repository(name=repo_name, product=product).create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    rhel_repo_id = enable_rhrepo_and_fetchid(
        basearch=rh_repo['basearch'],
        org_id=org.id,
        product=rh_repo['product'],
        repo=rh_repo['name'],
        reposet=rh_repo['reposet'],
        releasever=rh_repo['releasever'],
    )
    for repo_id in [rhel_repo_id, repo.id]:
        entities.Repository(id=repo_id).sync()
    with session:
        session.organization.select(org.name)
        session.activationkey.create(
            {
                'name': name,
                'lce': {constants.ENVIRONMENT: True},
                'content_view': constants.DEFAULT_CV,
            }
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        for subscription in (constants.DEFAULT_SUBSCRIPTION_NAME, custom_product_name):
            session.activationkey.add_subscription(name, subscription)
        ak = session.activationkey.read(name, widget_names='subscriptions')
        subscriptions = [
            subscription['Repository Name']
            for subscription in ak['subscriptions']['resources']['assigned']
        ]
        assert {constants.DEFAULT_SUBSCRIPTION_NAME, custom_product_name} == set(subscriptions)


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_fetch_product_content(session):
    """Associate RH & custom product with AK and fetch AK's product content

    :id: 4c37fb12-ea2a-404e-b7cc-a2735e8dedb6

    :expectedresults: Both Red Hat and custom product subscriptions are
        assigned as Activation Key's product content

    :BZ: 1426386, 1432285

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=constants.PRDS['rhel'],
        repo=constants.REPOS['rhst7']['name'],
        reposet=constants.REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    custom_product = entities.Product(organization=org).create()
    custom_repo = entities.Repository(
        name=gen_string('alphanumeric').upper(),  # first letter is always
        # uppercase on product content page, workarounding it for
        # successful checks
        product=custom_product,
    ).create()
    custom_repo.sync()
    cv = entities.ContentView(organization=org, repository=[rh_repo_id, custom_repo.id]).create()
    cv.publish()
    ak = entities.ActivationKey(content_view=cv, organization=org).create()
    with session:
        session.organization.select(org.name)
        for subscription in (constants.DEFAULT_SUBSCRIPTION_NAME, custom_product.name):
            session.activationkey.add_subscription(ak.name, subscription)
        ak = session.activationkey.read(ak.name, widget_names='repository_sets')
        reposets = [reposet['Repository Name'] for reposet in ak['repository_sets']['table']]
        assert {custom_repo.name, constants.REPOSET['rhst7']} == set(reposets)


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_access_non_admin_user(session, test_name):
    """Access activation key that has specific name and assigned environment by
    user that has filter configured for that specific activation key

    :id: 358a22d1-d576-475a-b90c-98e90a2ed1a9

    :customerscenario: true

    :expectedresults: Only expected activation key can be accessed by new non
        admin user

    :BZ: 1463813

    :CaseLevel: Integration
    """
    ak_name = gen_string('alpha')
    non_searchable_ak_name = gen_string('alpha')
    org = entities.Organization().create()
    envs_list = ['STAGING', 'DEV', 'IT', 'UAT', 'PROD']
    for name in envs_list:
        entities.LifecycleEnvironment(name=name, organization=org).create()
    env_name = random.choice(envs_list)
    cv = entities.ContentView(organization=org).create()
    cv.publish()
    promote(cv.read().version[0], entities.LifecycleEnvironment(name=env_name).search()[0].id)
    # Create new role
    role = entities.Role().create()
    # Create filter with predefined activation keys search criteria
    envs_condition = ' or '.join(['environment = ' + s for s in envs_list])
    entities.Filter(
        organization=[org],
        permission=entities.Permission(name='view_activation_keys').search(),
        role=role,
        search=f'name ~ {ak_name} and ({envs_condition})',
    ).create()

    # Add permissions for Organization and Location
    entities.Filter(
        permission=entities.Permission().search(query={'search': 'resource_type="Organization"'}),
        role=role,
    ).create()
    entities.Filter(
        permission=entities.Permission().search(query={'search': 'resource_type="Location"'}),
        role=role,
    ).create()

    # Create new user with a configured role
    default_loc = entities.Location().search(query={'search': f'name="{constants.DEFAULT_LOC}"'})[0]
    user_login = gen_string('alpha')
    user_password = gen_string('alpha')
    entities.User(
        role=[role],
        admin=False,
        login=user_login,
        password=user_password,
        organization=[org],
        location=[default_loc],
        default_organization=org,
    ).create()

    with session:
        session.organization.select(org_name=org.name)
        session.location.select(constants.DEFAULT_LOC)
        for name in [ak_name, non_searchable_ak_name]:
            session.activationkey.create(
                {'name': name, 'lce': {env_name: True}, 'content_view': cv.name}
            )
            assert session.activationkey.read(name, widget_names='details')['details']['lce'][
                env_name
            ][env_name]

    with Session(test_name, user=user_login, password=user_password) as session:
        session.organization.select(org.name)
        session.location.select(constants.DEFAULT_LOC)
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        assert (
            session.activationkey.search(non_searchable_ak_name)[0]['Name']
            != non_searchable_ak_name
        )


@pytest.mark.tier2
def test_positive_remove_user(session, module_org, test_name):
    """Delete any user who has previously created an activation key
    and check that activation key still exists

    :id: f0504bd8-52d2-40cd-91c6-64d71b14c876

    :expectedresults: Activation Key can be read

    :BZ: 1291271
    """
    ak_name = gen_string('alpha')
    # Create user
    password = gen_string('alpha')
    user = entities.User(admin=True, default_organization=module_org, password=password).create()
    # Create Activation Key using new user credentials
    with Session(test_name, user.login, password) as non_admin_session:
        non_admin_session.activationkey.create(
            {'name': ak_name, 'lce': {constants.ENVIRONMENT: True}}
        )
        assert non_admin_session.activationkey.search(ak_name)[0]['Name'] == ak_name
    # Remove user and check that AK still exists
    user.delete()
    with session:
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name


@pytest.mark.tier2
def test_positive_add_docker_repo_cv(session, module_org):
    """Add docker repository to a non-composite content view and
    publish it. Then create an activation key and associate it with the
    Docker content view.

    :id: e4935729-c5bc-46be-a23a-93ebde6b3506

    :expectedresults: Content view with docker repo can be added to
        activation key

    :CaseLevel: Integration
    """
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repo = entities.Repository(
        content_type=constants.REPO_TYPE['docker'],
        product=entities.Product(organization=module_org).create(),
        url=constants.CONTAINER_REGISTRY_HUB,
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    cvv = content_view.read().version[0].read()
    promote(cvv, lce.id)
    ak_name = gen_string('alphanumeric')
    with session:
        session.activationkey.create(
            {'name': ak_name, 'lce': {lce.name: True}, 'content_view': content_view.name}
        )
        ak = session.activationkey.read(ak_name, 'details')
        assert ak['details']['content_view'] == content_view.name
        assert ak['details']['lce'][lce.name][lce.name]


@pytest.mark.tier2
def test_positive_add_docker_repo_ccv(session, module_org):
    """Add docker repository to a non-composite content view and publish it.
    Then add this content view to a composite content view and publish it.
    Create an activation key and associate it with the composite Docker content
    view.

    :id: 0d412f54-6333-413e-8040-4e51ae5c069c

    :expectedresults: Docker-based content view can be added to activation
        key

    :CaseLevel: Integration
    """
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repo = entities.Repository(
        content_type=constants.REPO_TYPE['docker'],
        product=entities.Product(organization=module_org).create(),
        url=constants.CONTAINER_REGISTRY_HUB,
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    cvv = content_view.read().version[0].read()
    promote(cvv, lce.id)
    composite_cv = entities.ContentView(
        component=[cvv], composite=True, organization=module_org
    ).create()
    composite_cv.publish()
    ccvv = composite_cv.read().version[0].read()
    promote(ccvv, lce.id)
    ak_name = gen_string('alphanumeric')
    with session:
        session.activationkey.create(
            {'name': ak_name, 'lce': {lce.name: True}, 'content_view': composite_cv.name}
        )
        ak = session.activationkey.read(ak_name, 'details')
        assert ak['details']['content_view'] == composite_cv.name
        assert ak['details']['lce'][lce.name][lce.name]


@pytest.mark.skip_if_not_set('clients')
@pytest.mark.tier3
def test_positive_add_host(session, module_org, rhel6_contenthost, default_sat):
    """Test that hosts can be associated to Activation Keys

    :id: 886e9ea5-d917-40e0-a3b1-41254c4bf5bf

    :Steps:
        1. Create Activation key
        2. Create different hosts
        3. Associate the hosts to Activation key

    :expectedresults: Hosts are successfully associated to Activation key

    :CaseLevel: System
    """
    ak = entities.ActivationKey(
        environment=entities.LifecycleEnvironment(
            name=constants.ENVIRONMENT, organization=module_org
        ).search()[0],
        organization=module_org,
    ).create()

    rhel6_contenthost.install_katello_ca(default_sat)
    rhel6_contenthost.register_contenthost(module_org.label, ak.name)
    assert rhel6_contenthost.subscribed
    with session:
        session.organization.select(module_org.name)
        ak = session.activationkey.read(ak.name, widget_names='content_hosts')
        assert len(ak['content_hosts']['table']) == 1
        assert ak['content_hosts']['table'][0]['Name'] == rhel6_contenthost.hostname


@pytest.mark.skip_if_not_set('clients')
@pytest.mark.tier3
def test_positive_delete_with_system(session, rhel6_contenthost, default_sat):
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
        session.activationkey.create(
            {'name': name, 'lce': {env_name: True}, 'content_view': cv_name}
        )
        assert session.activationkey.search(name)[0]['Name'] == name
        session.activationkey.add_subscription(name, product_name)
        rhel6_contenthost.install_katello_ca(default_sat)
        rhel6_contenthost.register_contenthost(org.label, name)
        assert rhel6_contenthost.subscribed
        session.activationkey.delete(name)
        assert session.activationkey.search(name)[0]['Name'] != name


@pytest.mark.skip_if_not_set('clients')
@pytest.mark.tier3
def test_negative_usage_limit(session, module_org, rhel6_contenthost, default_sat):
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
        session.activationkey.create({'name': name, 'lce': {constants.ENVIRONMENT: True}})
        assert session.activationkey.search(name)[0]['Name'] == name
        session.activationkey.update(name, {'details.hosts_limit': hosts_limit})
        ak = session.activationkey.read(name, widget_names='details')
        assert ak['details']['hosts_limit'] == hosts_limit
    with VMBroker(nick='rhel6', host_classes={'host': ContentHost}, _count=2) as hosts:
        vm1, vm2 = hosts
        vm1.install_katello_ca(default_sat)
        vm1.register_contenthost(module_org.label, name)
        assert vm1.subscribed
        vm2.install_katello_ca(default_sat)
        result = vm2.register_contenthost(module_org.label, name)
        assert not vm2.subscribed
        assert len(result.stderr)
        assert f'Max Hosts ({hosts_limit}) reached for activation key' in result.stderr


@pytest.mark.skip_if_not_set('clients')
@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
def test_positive_add_multiple_aks_to_system(session, module_org, rhel6_contenthost, default_sat):
    """Check if multiple Activation keys can be attached to a system

    :id: 4d6b6b69-9d63-4180-af2e-a5d908f8adb7

    :expectedresults: Multiple Activation keys are attached to a system

    :CaseLevel: System
    """
    key_1_name = gen_string('alpha')
    key_2_name = gen_string('alpha')
    cv_1_name = gen_string('alpha')
    cv_2_name = gen_string('alpha')
    env_1_name = gen_string('alpha')
    env_2_name = gen_string('alpha')
    product_1_name = gen_string('alpha')
    product_2_name = gen_string('alpha')
    repo_1_id = create_sync_custom_repo(org_id=module_org.id, product_name=product_1_name)
    cv_publish_promote(cv_1_name, env_1_name, repo_1_id, module_org.id)
    repo_2_id = create_sync_custom_repo(
        org_id=module_org.id, product_name=product_2_name, repo_url=settings.repos.yum_2.url
    )
    cv_publish_promote(cv_2_name, env_2_name, repo_2_id, module_org.id)
    with session:
        # Create 2 activation keys
        session.location.select(constants.DEFAULT_LOC)
        for key_name, env_name, cv_name, product_name in (
            (key_1_name, env_1_name, cv_1_name, product_1_name),
            (key_2_name, env_2_name, cv_2_name, product_2_name),
        ):
            session.activationkey.create(
                {'name': key_name, 'lce': {env_name: True}, 'content_view': cv_name}
            )
            assert session.activationkey.search(key_name)[0]['Name'] == key_name
            session.activationkey.add_subscription(key_name, product_name)
            ak = session.activationkey.read(key_name, widget_names='subscriptions')
            subscriptions = [
                subscription['Repository Name']
                for subscription in ak['subscriptions']['resources']['assigned']
            ]
            assert product_name in subscriptions
        # Create VM
        rhel6_contenthost.install_katello_ca(default_sat)
        rhel6_contenthost.register_contenthost(module_org.label, ','.join([key_1_name, key_2_name]))
        assert rhel6_contenthost.subscribed
        # Assert the content-host association with activation keys
        for key_name in [key_1_name, key_2_name]:
            ak = session.activationkey.read(key_name, widget_names='content_hosts')
            assert len(ak['content_hosts']['table']) == 1
            assert ak['content_hosts']['table'][0]['Name'] == rhel6_contenthost.hostname


@pytest.mark.skip_if_not_set('clients')
@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_host_associations(session, default_sat):
    """Register few hosts with different activation keys and ensure proper
    data is reflected under Associations > Content Hosts tab

    :id: 111aa2af-caf4-4940-8e4b-5b071d488876

    :expectedresults: Only hosts, registered by specific AK are shown under
        Associations > Content Hosts tab

    :customerscenario: true

    :BZ: 1344033, 1372826, 1394388

    :CaseLevel: System
    """
    org = entities.Organization().create()
    org_entities = setup_org_for_a_custom_repo(
        {'url': settings.repos.yum_1.url, 'organization-id': org.id}
    )
    ak1 = entities.ActivationKey(id=org_entities['activationkey-id']).read()
    ak2 = entities.ActivationKey(
        content_view=org_entities['content-view-id'],
        environment=org_entities['lifecycle-environment-id'],
        organization=org.id,
    ).create()
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}, _count=2) as hosts:
        vm1, vm2 = hosts
        vm1.install_katello_ca(default_sat)
        vm1.register_contenthost(org.label, ak1.name)
        assert vm1.subscribed
        vm2.install_katello_ca(default_sat)
        vm2.register_contenthost(org.label, ak2.name)
        assert vm2.subscribed
        with session:
            session.organization.select(org.name)
            ak1 = session.activationkey.read(ak1.name, widget_names='content_hosts')
            assert len(ak1['content_hosts']['table']) == 1
            assert ak1['content_hosts']['table'][0]['Name'] == vm1.hostname
            ak2 = session.activationkey.read(ak2.name, widget_names='content_hosts')
            assert len(ak2['content_hosts']['table']) == 1
            assert ak2['content_hosts']['table'][0]['Name'] == vm2.hostname


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
def test_positive_service_level_subscription_with_custom_product(
    session, rhel7_contenthost, default_sat
):
    """Subscribe a host to activation key with Premium service level and with
    custom product

    :id: 195a8049-860e-494d-b7f0-0794384194f7

    :customerscenario: true

    :steps:
        1. Create a product with custom repository synchronized
        2. Create and Publish a content view with the created repository
        3. Create an activation key and assign the created content view
        4. Add a RedHat subscription to activation key (The product
           subscription should be added automatically)
        5. Set the activation service_level to Premium
        6. Register a host to activation key
        7. List consumed subscriptions on host
        8. List the subscription in Content Host UI

    :expectedresults:
        1. The product subscription is listed in consumed subscriptions on host
        2. The product subscription is listed in the contenthost subscriptions
           UI

    :BZ: 1394357

    :CaseLevel: System
    """
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    entities_ids = setup_org_for_a_custom_repo(
        {'url': settings.repos.yum_1.url, 'organization-id': org.id}
    )
    product = entities.Product(id=entities_ids['product-id']).read()
    activation_key = entities.ActivationKey(id=entities_ids['activationkey-id']).read()
    # add the default RH subscription
    subscription = entities.Subscription(organization=org).search(
        query={'search': f'name="{constants.DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': subscription.id})
    # ensure all the needed subscriptions are attached to activation key
    results = activation_key.subscriptions()['results']
    assert {product.name, constants.DEFAULT_SUBSCRIPTION_NAME} == {
        ak_subscription['name'] for ak_subscription in results
    }
    # Set the activation service_level to Premium
    activation_key.service_level = 'Premium'
    activation_key = activation_key.update(['service_level'])

    rhel7_contenthost.install_katello_ca(default_sat)
    rhel7_contenthost.register_contenthost(org.label, activation_key=activation_key.name)
    assert rhel7_contenthost.subscribed
    result = rhel7_contenthost.run('subscription-manager list --consumed')
    assert result.status == 0
    assert f'Subscription Name:   {product.name}' in '\n'.join(result.stdout)
    with session:
        session.organization.select(org.name)
        chost = session.contenthost.read(rhel7_contenthost.hostname, widget_names='subscriptions')
        subscriptions = {
            subs['Repository Name'] for subs in chost['subscriptions']['resources']['assigned']
        }
        assert product.name in subscriptions


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
def test_positive_delete_manifest(session):
    """Check if deleting a manifest removes it from Activation key

    :id: 512d8e41-b937-451e-a9c6-840457d3d7d4

    :Steps:
        1. Create Activation key
        2. Associate a manifest to the Activation Key
        3. Delete the manifest

    :expectedresults: Deleting a manifest removes it from the Activation
        key

    :CaseLevel: Integration
    """
    # Upload manifest
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    # Create activation key
    activation_key = entities.ActivationKey(organization=org).create()
    # Associate a manifest to the activation key
    subscription = entities.Subscription(organization=org).search(
        query={'search': f'name="{constants.DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': subscription.id})
    with session:
        session.organization.select(org.name)
        # Verify subscription is assigned to activation key
        ak = session.activationkey.read(activation_key.name, widget_names='subscriptions')
        assert (
            ak['subscriptions']['resources']['assigned'][0]['Repository Name']
            == constants.DEFAULT_SUBSCRIPTION_NAME
        )
        # Delete the manifest
        # Ignore "404 Not Found" as server will connect to upstream subscription service to verify
        # the consumer uuid, that will be displayed in flash error messages
        # Note: this happen only when using clone manifest.
        session.subscription.delete_manifest(ignore_error_messages='404 Not Found')
        assert not session.subscription.has_manifest
        # Verify subscription is not assigned to activation key anymore
        ak = session.activationkey.read(activation_key.name, widget_names='subscriptions')
        assert not ak['subscriptions']['resources']['assigned']
