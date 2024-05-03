"""Test class for Organization UI

:Requirement: Organization

:CaseAutomation: Automated

:CaseComponent: OrganizationsandLocations

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG, INSTALL_MEDIUM_URL, LIBVIRT_RESOURCE_URL
from robottelo.logging import logger

CUSTOM_REPO_ERRATA_ID = settings.repos.yum_0.errata[0]


@pytest.fixture(scope='module')
def module_repos_col(request, module_entitlement_manifest_org, module_lce, module_target_sat):
    repos_collection = module_target_sat.cli_factory.RepositoryCollection(
        repositories=[
            # As Satellite Tools may be added as custom repo and to have a "Fully entitled" host,
            # force the host to consume an RH product with adding a cdn repo.
            module_target_sat.cli_factory.YumRepository(url=settings.repos.yum_0.url),
        ],
    )
    repos_collection.setup_content(module_entitlement_manifest_org.id, module_lce.id)
    yield repos_collection

    @request.addfinalizer
    def _cleanup():
        try:
            module_target_sat.api.Subscription(
                organization=module_entitlement_manifest_org
            ).delete_manifest(data={'organization_id': module_entitlement_manifest_org.id})
        except Exception:
            logger.exception('Exception cleaning manifest:')


@pytest.mark.e2e
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_target_sat):
    """Perform end to end testing for organization component

    :id: abe878a9-a6bc-41e5-a39a-0fed9012b80f

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    label = gen_string('alphanumeric')
    description = gen_string('alpha')

    # entities to be added and removed
    user = module_target_sat.api.User().create()
    media = module_target_sat.api.Media(
        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6), os_family='Redhat'
    ).create()
    template = module_target_sat.api.ProvisioningTemplate().create()
    ptable = module_target_sat.api.PartitionTable().create()
    domain = module_target_sat.api.Domain().create()
    hostgroup = module_target_sat.api.HostGroup().create()
    location = module_target_sat.api.Location().create()

    widget_list = [
        'primary',
        'users',
        'media',
        'provisioning_templates',
        'partition_tables',
        'domains',
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
                'host_groups.resources.assigned': [hostgroup.name],
                'locations.resources.assigned': [location.name],
            },
        )
        assert session.organization.search(new_name)
        org_values = session.organization.read(new_name, widget_names=widget_list)
        with pytest.raises(AssertionError) as context:
            assert not session.organization.delete(new_name)
        assert (
            'The current organization cannot be deleted. Please switch to a '
            'different organization before deleting.' in str(context.value)
        )
        assert user.login in org_values['users']['resources']['assigned']
        assert media.name in org_values['media']['resources']['assigned']
        assert template.name in org_values['provisioning_templates']['resources']['assigned']
        assert ptable.name in org_values['partition_tables']['resources']['assigned']
        assert domain.name in org_values['domains']['resources']['assigned']
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

    :id: f0d81840-ecbb-43d2-9aff-236a9ec1c595

    :customerscenario: true

    :expectedresults: Proper organization is found

    :BZ: 1259374

    :CaseImportance: Medium
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
def test_positive_create_with_all_users(session, module_target_sat):
    """Create organization and new user. Check 'all users' setting for
    organization. Verify that user is assigned to organization and
    vice versa organization is assigned to user

    :id: 6032be70-00a0-4ccd-ad01-391546074879

    :customerscenario: true

    :expectedresults: Organization and user entities assigned to each other

    :BZ: 1321543
    """
    user = module_target_sat.api.User().create()
    org = module_target_sat.api.Organization().create()
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
@pytest.mark.tier2
def test_positive_update_compresource(session, module_target_sat):
    """Add/Remove compute resource from/to organization.

    :id: a49349b9-4637-4ef6-b65b-bd3eccb5a12a

    :expectedresults: Compute resource is added and then removed.
    """
    url = f'{LIBVIRT_RESOURCE_URL}{settings.libvirt.libvirt_hostname}'
    resource = module_target_sat.api.LibvirtComputeResource(url=url).create()
    resource_name = resource.name + ' (Libvirt)'
    org = module_target_sat.api.Organization().create()
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
def test_positive_delete_with_manifest_lces(session, target_sat, function_entitlement_manifest_org):
    """Create Organization with valid values and upload manifest.
    Then try to delete that organization.

    :id: 2f0d580f-2207-4e5e-86ec-80071a29f56c

    :expectedresults: Organization is deleted successfully.

    :CaseImportance: Critical
    """
    org = function_entitlement_manifest_org
    with session:
        session.organization.select(org.name)
        session.lifecycleenvironment.create({'name': 'DEV'})
        session.lifecycleenvironment.create({'name': 'QE'}, prior_entity_name='DEV')
        # Org cannot be deleted when selected,
        # So switching to Default Org and then deleting.
        session.organization.select(DEFAULT_ORG)
        session.organization.delete(org.name)
        assert not session.organization.search(org.name)


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_download_debug_cert_after_refresh(
    session, target_sat, function_entitlement_manifest_org
):
    """Create organization with valid manifest. Download debug
    certificate for that organization and refresh added manifest for few
    times in a row

    :id: f437c033-a662-4697-b418-5479a8a0a397

    :expectedresults: Scenario passed successfully

    :CaseImportance: High
    """
    org = function_entitlement_manifest_org
    try:
        with session:
            session.organization.select(org.name)
            for _ in range(3):
                assert org.download_debug_certificate()
                session.subscription.refresh_manifest()
    finally:
        target_sat.api.Subscription(organization=org).delete_manifest(
            data={'organization_id': org.id}
        )


@pytest.mark.tier2
def test_positive_errata_view_organization_switch(
    session, module_org, module_lce, module_repos_col, module_target_sat
):
    """Verify no errata list visible on Organization switch

    :id: faad9cf3-f8d5-49a6-87d1-431837b67675

    :steps: Create an Organization having a product synced which contains errata.

    :expectedresults: Verify that the errata belonging to one Organization is not
                      showing in the Default organization.

    :CaseImportance: High
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

    :steps:
            1. Create an Organization having a product and verify that product is present in
               the Organization.
            2. Switch the Organization to default and verify that product is not visible in it.

    :expectedresults: Verify that the Product belonging to one Organization is not visible in
                      another organization.

    :CaseImportance: High
    """
    with session:
        assert session.product.search(module_product.name)
        session.organization.select(org_name="Default Organization")
        assert session.product.search(module_product.name) != module_product.name


@pytest.mark.tier2
def test_positive_prepare_for_sca_only_deprecation(target_sat):
    """Verify that Simple Content Access endpoints are deprecated and will be required
        for all organizations in Katello 4.12

    :id: df7e6806-6664-4dc5-baf6-bb41935e3031

    :expectedresults: Attempting to create an Organization with sca set to False, will throw
        deprecation endpoint message
    """
    with target_sat.ui_session() as session:
        session.organization.create(
            {
                'name': gen_string('alpha'),
                'label': gen_string('alpha'),
                'sca': False,
            }
        )
        results = target_sat.execute('tail -100 /var/log/foreman/production.log').stdout
    assert 'Simple Content Access will be required for all organizations in Katello 4.12' in results


def test_positive_prepare_for_sca_only_organization(target_sat, function_entitlement_manifest_org):
    """Verify that the organization details page notifies users that Simple Content Access
        will be required for all organizations in Satellite 6.16

    :id: 3a6a848b-3c16-4dbb-8f52-5ea57a9a97ef

    :expectedresults: The Organization details page notifies users that Simple Content Access will
        be required for all organizations in Satellite 6.16
    """
    with target_sat.ui_session() as session:
        session.organization.select(function_entitlement_manifest_org.name)
        sca_alert = session.organization.read(
            function_entitlement_manifest_org.name, widget_names='primary'
        )
        assert (
            'Simple Content Access will be required for all organizations in Satellite 6.16.'
            in sca_alert['primary']['sca_alert']
        )
