"""Test class for Organization UI

:Requirement: Organization

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: OrganizationsLocations

:Assignee: shwsingh

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import INSTALL_MEDIUM_URL
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.manifests import original_manifest
from robottelo.manifests import upload_manifest_locked

CUSTOM_REPO_ERRATA_ID = settings.repos.yum_0.errata[0]


@pytest.fixture(scope='module')
def module_repos_col(module_org, module_lce, module_target_sat, request):
    upload_manifest_locked(org_id=module_org.id)
    repos_collection = module_target_sat.cli_factory.RepositoryCollection(
        repositories=[
            # As Satellite Tools may be added as custom repo and to have a "Fully entitled" host,
            # force the host to consume an RH product with adding a cdn repo.
            module_target_sat.cli_factory.YumRepository(url=settings.repos.yum_0.url),
        ],
    )
    repos_collection.setup_content(module_org.id, module_lce.id)
    yield repos_collection

    @request.addfinalizer
    def _cleanup():
        try:
            module_target_sat.api.Subscription(organization=module_org).delete_manifest(
                data={'organization_id': module_org.id}
            )
        except Exception:
            logger.exception('Exception cleaning manifest:')


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session):
    """Perform end to end testing for organization component

    :id: 91003f52-63a6-4b0d-9b68-2b5717fd200e

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    label = gen_string('alphanumeric')
    description = gen_string('alpha')

    # entities to be added and removed
    user = entities.User().create()
    media = entities.Media(
        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6), os_family='Redhat'
    ).create()
    template = entities.ProvisioningTemplate().create()
    ptable = entities.PartitionTable().create()
    domain = entities.Domain().create()
    env = entities.Environment().create()
    hostgroup = entities.HostGroup().create()
    location = entities.Location().create()

    widget_list = [
        'primary',
        'users',
        'media',
        'provisioning_templates',
        'partition_tables',
        'domains',
        'environments',
        'host_groups',
        'locations',
    ]

    with session:
        session.organization.create({'name': name, 'label': label, 'description': description})
        assert session.organization.search(name)[0]['Name'] == name
        org_values = session.organization.read(name, widget_names='primary')
        assert org_values['primary']['name'] == name
        assert org_values['primary']['label'] == label
        assert org_values['primary']['description'] == description

        # add attributes
        session.organization.update(
            name,
            {
                'primary.name': new_name,
                'users.resources.assigned': [user.login],
                'media.resources.assigned': [media.name],
                'provisioning_templates.resources.assigned': [template.name],
                'partition_tables.resources.assigned': [ptable.name],
                'domains.resources.assigned': [domain.name],
                'environments.resources.assigned': [env.name],
                'host_groups.resources.assigned': [hostgroup.name],
                'locations.resources.assigned': [location.name],
            },
        )

        org_values = session.organization.read(new_name, widget_names=widget_list)
        with pytest.raises(AssertionError):
            session.organization.delete(new_name)
        assert user.login in org_values['users']['resources']['assigned']
        assert media.name in org_values['media']['resources']['assigned']
        assert template.name in org_values['provisioning_templates']['resources']['assigned']
        assert ptable.name in org_values['partition_tables']['resources']['assigned']
        assert domain.name in org_values['domains']['resources']['assigned']
        assert env.name in org_values['environments']['resources']['assigned']
        assert hostgroup.name in org_values['host_groups']['resources']['assigned']
        assert location.name in org_values['locations']['resources']['assigned']

        ptables_before_remove = len(org_values['partition_tables']['resources']['assigned'])
        templates_before_remove = len(org_values['provisioning_templates']['resources']['assigned'])

        # remove attributes
        session.organization.update(
            new_name,
            {
                'users.resources.unassigned': [user.login],
                'media.resources.unassigned': [media.name],
                'provisioning_templates.resources.unassigned': [template.name],
                'partition_tables.resources.unassigned': [ptable.name],
                'domains.resources.unassigned': [domain.name],
                'environments.resources.unassigned': [env.name],
                'host_groups.resources.unassigned': [hostgroup.name],
                'locations.resources.unassigned': [location.name],
            },
        )

        org_values = session.organization.read(new_name, widget_names=widget_list)
        assert len(org_values['users']['resources']['assigned']) == 0
        assert user.login in org_values['users']['resources']['unassigned']
        assert len(org_values['media']['resources']['assigned']) == 0
        assert media.name in org_values['media']['resources']['unassigned']
        assert len(org_values['partition_tables']['resources']['assigned']) < ptables_before_remove
        assert (
            len(org_values['provisioning_templates']['resources']['assigned'])
            < templates_before_remove
        )
        assert len(org_values['domains']['resources']['assigned']) == 0
        assert domain.name in org_values['domains']['resources']['unassigned']
        assert len(org_values['environments']['resources']['assigned']) == 0
        assert env.name in org_values['environments']['resources']['unassigned']
        assert len(org_values['host_groups']['resources']['assigned']) == 0
        assert hostgroup.name in org_values['host_groups']['resources']['unassigned']
        assert len(org_values['locations']['resources']['assigned']) == 0
        assert location.name in org_values['locations']['resources']['unassigned']

        # delete org
        session.organization.select(DEFAULT_ORG)
        session.organization.delete(new_name)
        assert not session.organization.search(new_name)


@pytest.mark.tier2
def test_positive_search_scoped(session):
    """Test scoped search functionality for organization by label

    :id: 18ad9aad-335a-414e-843e-e1c05ec6bcbb

    :customerscenario: true

    :expectedresults: Proper organization is found

    :BZ: 1259374

    """
    org_name = gen_string('alpha')
    label = gen_string('alpha')
    with session:
        session.organization.create({'name': org_name, 'label': label})
        for query in [
            f'label = {label}',
            f'label ~ {label[:-5]}',
            f'label ^ "{label}"',
        ]:
            assert session.organization.search(query)[0]['Name'] == org_name


@pytest.mark.skip_if_open("BZ:1321543")
@pytest.mark.tier2
def test_positive_create_with_all_users(session):
    """Create organization and new user. Check 'all users' setting for
    organization. Verify that user is assigned to organization and
    vice versa organization is assigned to user

    :id: 5bfcbd10-750c-4ef6-87b6-a8eb2eae4ce7

    :expectedresults: Organization and user entities assigned to each other

    :BZ: 1321543

    :CaseLevel: Integration
    """
    user = entities.User().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(org.name, {'users.all_users': True})
        org_values = session.organization.read(org.name, widget_names='users')
        assert user.login in org_values['users']['resources']['assigned']
        session.organization.search(org.name)
        session.organization.select(org_name=org.name)
        found_users = session.user.search(user.login)
        assert user.login in [user['Username'] for user in found_users]
        user_values = session.user.read(user.login)
        assert org.name in user_values['organizations']['resources']['assigned']


@pytest.mark.skip_if_not_set('libvirt')
@pytest.mark.on_premises_provisioning
@pytest.mark.tier2
def test_positive_update_compresource(session):
    """Add/Remove compute resource from/to organization.

    :id: db119bb1-8f79-415b-a056-70a19ffceeea

    :expectedresults: Compute resource is added and then removed.

    :CaseLevel: Integration
    """
    url = f'{LIBVIRT_RESOURCE_URL}{settings.libvirt.libvirt_hostname}'
    resource = entities.LibvirtComputeResource(url=url).create()
    resource_name = resource.name + ' (Libvirt)'
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'compute_resources.resources.assigned': [resource_name]}
        )
        org_values = session.organization.read(org.name, widget_names='compute_resources')
        assert org_values['compute_resources']['resources']['assigned'][0] == resource_name
        session.organization.update(
            org.name, {'compute_resources.resources.unassigned': [resource_name]}
        )
        org_values = session.organization.read(org.name, widget_names='compute_resources')
        assert len(org_values['compute_resources']['resources']['assigned']) == 0
        assert resource_name in org_values['compute_resources']['resources']['unassigned']


@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_with_manifest_lces(session):
    """Create Organization with valid values and upload manifest.
    Then try to delete that organization.

    :id: 851c8557-a406-4a70-9c8b-94bcf0482f8d

    :expectedresults: Organization is deleted successfully.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    upload_manifest_locked(org.id)
    with session:
        session.organization.select(org.name)
        session.lifecycleenvironment.create({'name': 'DEV'})
        session.lifecycleenvironment.create({'name': 'QE'}, prior_entity_name='DEV')
        # Org cannot be deleted when selected,
        # So switching to Default Org and then deleting.
        session.organization.select(DEFAULT_ORG)
        session.organization.delete(org.name)
        assert not session.organization.search(org.name)


@pytest.mark.skip('Skipping due to manifest refresh issues')
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_download_debug_cert_after_refresh(session):
    """Create organization with valid manifest. Download debug
    certificate for that organization and refresh added manifest for few
    times in a row

    :id: 1fcd7cd1-8ba1-434f-b9fb-c4e920046eb4

    :expectedresults: Scenario passed successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    try:
        upload_manifest_locked(org.id, original_manifest())
        with session:
            session.organization.select(org.name)
            for _ in range(3):
                assert org.download_debug_certificate()
                session.subscription.refresh_manifest()
    finally:
        entities.Subscription(organization=org).delete_manifest(data={'organization_id': org.id})


@pytest.mark.tier2
def test_positive_errata_view_organization_switch(
    session, module_org, module_lce, module_repos_col, module_target_sat
):
    """Verify no errata list visible on Organization switch

    :id: faad9cf3-f8d5-49a6-87d1-431837b67675

    :Steps: Create an Organization having a product synced which contains errata.

    :expectedresults: Verify that the errata belonging to one Organization is not
                      showing in the Default organization.

    :CaseImportance: High

    :CaseLevel: Integration
    """
    rc = module_target_sat.cli_factory.RepositoryCollection(
        repositories=[module_target_sat.cli_factory.YumRepository(settings.repos.yum_3.url)]
    )
    rc.setup_content(module_org.id, module_lce.id)
    with session:
        assert (
            session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)[0]['Errata ID']
            == CUSTOM_REPO_ERRATA_ID
        )
        session.organization.select(org_name="Default Organization")
        assert not session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_product_view_organization_switch(session, module_org, module_product):
    """Verify product created in one organization is not visible in another

    :id: 50cc459a-3a23-433a-99b9-9f3b929e6d64

    :Steps:
            1. Create an Organization having a product and verify that product is present in
               the Organization.
            2. Switch the Organization to default and verify that product is not visible in it.

    :expectedresults: Verify that the Product belonging to one Organization is not visible in
                      another organization.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    with session:
        assert session.product.search(module_product.name)
        session.organization.select(org_name="Default Organization")
        assert not session.product.search(module_product.name) == module_product.name
