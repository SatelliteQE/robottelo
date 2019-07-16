"""Test class for Organization UI

:Requirement: Organization

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: OrganizationsLocations

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from pytest import raises

from robottelo.config import settings
from robottelo.constants import ANY_CONTEXT, DEFAULT_ORG, INSTALL_MEDIUM_URL, LIBVIRT_RESOURCE_URL
from robottelo.decorators import skip_if_not_set, tier2, upgrade
from robottelo.manifests import original_manifest, upload_manifest_locked
from robozilla.decorators import skip_if_bug_open


@tier2
@upgrade
def test_positive_end_to_end(session):
    """Perform end to end testing for organization component

    :id: 91003f52-63a6-4b0d-9b68-2b5717fd200e

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    label = gen_string('alphanumeric')
    description = gen_string('alpha')
    with session:
        session.organization.create({
            'name': name, 'label': label, 'description': description,
        })
        assert session.organization.search(name)[0]['Name'] == name
        org_values = session.organization.read(name)
        assert org_values['primary']['name'] == name
        assert org_values['primary']['label'] == label
        assert org_values['primary']['description'] == description
        session.organization.update(name, {'primary.name': new_name})
        assert session.organization.search(new_name)[0]['Name'] == new_name
        with raises(AssertionError):
            session.organization.delete(new_name)
        session.organization.select(DEFAULT_ORG)
        session.organization.delete(new_name)
        assert not session.organization.search(new_name)


@tier2
def test_positive_search_scoped(session):
    """Test scoped search functionality for organization by label

    :id: 18ad9aad-335a-414e-843e-e1c05ec6bcbb

    :customerscenario: true

    :expectedresults: Proper organization is found

    :BZ: 1259374

    :CaseImportance: Critical
    """
    org_name = gen_string('alpha')
    label = gen_string('alpha')
    with session:
        session.organization.create({'name': org_name, 'label': label})
        for query in [
            'label = {}'.format(label),
            'label ~ {}'.format(label[:-5]),
            'label ^ "{}"'.format(label),
        ]:
            assert session.organization.search(query)[0]['Name'] == org_name


@tier2
def test_positive_update_user(session):
    """Add new user and then remove it from organization

    :id: 01a221f7-d0fe-4b46-ab5c-b4e861677126

    :expectedresults: User successfully added and then removed from
        organization resources

    :CaseLevel: Integration
    """
    user = entities.User().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'users.resources.assigned': [user.login]})
        org_values = session.organization.read(org.name)
        assert org_values['users']['resources']['assigned'][0] == user.login
        session.organization.update(
            org.name, {'users.resources.unassigned': [user.login]})
        org_values = session.organization.read(org.name)
        assert len(org_values['users']['resources']['assigned']) == 0
        assert user.login in org_values['users']['resources']['unassigned']


@skip_if_bug_open('bugzilla', 1730292)
@tier2
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
        session.organization.update(
            org.name, {'users.all_users': True})
        org_values = session.organization.read(org.name)
        assert user.login in org_values['users']['resources']['assigned']
        session.organization.search(org.name)
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=ANY_CONTEXT['location'])
        assert session.user.search(user.login)[0]['Username'] == user.login
        user_values = session.user.read(user.login)
        assert org.name == user_values[
            'organizations']['resources']['assigned'][0]


@skip_if_not_set('compute_resources')
@tier2
def test_positive_update_compresource(session):
    """Add/Remove compute resource from/to organization.

    :id: db119bb1-8f79-415b-a056-70a19ffceeea

    :expectedresults: Compute resource is added and then removed.

    :CaseLevel: Integration
    """
    url = (
        LIBVIRT_RESOURCE_URL % settings.compute_resources.libvirt_hostname)
    resource = entities.LibvirtComputeResource(url=url).create()
    resource_name = resource.name + ' (Libvirt)'
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name,
            {'compute_resources.resources.assigned': [resource_name]}
        )
        org_values = session.organization.read(org.name)
        assert org_values[
            'compute_resources']['resources']['assigned'][0] == resource_name
        session.organization.update(
            org.name,
            {'compute_resources.resources.unassigned': [resource_name]}
        )
        org_values = session.organization.read(org.name)
        assert len(
            org_values['compute_resources']['resources']['assigned']) == 0
        assert resource_name in org_values[
            'compute_resources']['resources']['unassigned']


@tier2
def test_positive_update_media(session):
    """Add/Remove medium from/to organization.

    :id: bcf3aaf4-cad9-4a22-a087-60b213eb87cf

    :expectedresults: Medium is added and then removed.

    :CaseLevel: Integration
    """
    media = entities.Media(
        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
        os_family='Redhat',
    ).create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'media.resources.assigned': [media.name]})
        org_values = session.organization.read(org.name)
        assert org_values['media']['resources']['assigned'][0] == media.name
        session.organization.update(
            org.name, {'media.resources.unassigned': [media.name]})
        org_values = session.organization.read(org.name)
        assert len(org_values['media']['resources']['assigned']) == 0
        assert media.name in org_values['media']['resources']['unassigned']


@tier2
def test_positive_update_template(session):
    """Add and remove provisioning template from/to organization.

    :id: 67bec745-5f10-494c-92a7-173ee63e8297

    :expectedresults: Provisioning Template is added and then removed.

    :CaseLevel: Integration
    """
    template = entities.ProvisioningTemplate().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name,
            {'provisioning_templates.resources.assigned': [template.name]}
        )
        org_values = session.organization.read(org.name)
        assert template.name in org_values[
            'provisioning_templates']['resources']['assigned']
        session.organization.update(
            org.name,
            {'provisioning_templates.resources.unassigned': [template.name]}
        )
        org_values = session.organization.read(org.name)
        assert template.name in org_values[
            'provisioning_templates']['resources']['unassigned']


@tier2
def test_positive_update_ptable(session):
    """Add/Remove partition table from/to organization.

    :id: 75662a83-0921-45fd-a4b5-012c48bb003a

    :expectedresults: Partition table is added and then removed.

    :CaseLevel: Integration
    """
    ptable = entities.PartitionTable().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'partition_tables.resources.assigned': [ptable.name]})
        org_values = session.organization.read(org.name)
        assert ptable.name in org_values[
            'partition_tables']['resources']['assigned']
        session.organization.update(
            org.name, {'partition_tables.resources.unassigned': [ptable.name]})
        org_values = session.organization.read(org.name)
        assert ptable.name in org_values[
            'partition_tables']['resources']['unassigned']


@tier2
def test_positive_update_domain(session):
    """Add/Remove domain from/to organization.

    :id: a49e86c7-f859-4120-b59e-3f89e99a9054

    :expectedresults: Domain is added and removed from the organization

    :CaseLevel: Integration
    """
    domain = entities.Domain().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'domains.resources.assigned': [domain.name]})
        org_values = session.organization.read(org.name)
        assert org_values['domains']['resources']['assigned'][0] == domain.name
        session.organization.update(
            org.name, {'domains.resources.unassigned': [domain.name]})
        org_values = session.organization.read(org.name)
        assert len(org_values['domains']['resources']['assigned']) == 0
        assert domain.name in org_values['domains']['resources']['unassigned']


@tier2
def test_positive_update_environment(session):
    """Add/Remove environment from/to organization.

    :id: 270de90d-062e-4893-89c9-f6d0665ab967

    :expectedresults: Environment is added then removed from organization.

    :CaseLevel: Integration
    """
    env = entities.Environment().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'environments.resources.assigned': [env.name]})
        org_values = session.organization.read(org.name)
        assert org_values[
            'environments']['resources']['assigned'][0] == env.name
        session.organization.update(
            org.name, {'environments.resources.unassigned': [env.name]})
        org_values = session.organization.read(org.name)
        assert len(org_values['environments']['resources']['assigned']) == 0
        assert env.name in org_values[
            'environments']['resources']['unassigned']


@tier2
def test_positive_update_hostgroup(session):
    """Add/Remove host group from/to organization.

    :id: 12e2fc40-d721-4e71-af7c-3db67b9e718e

    :expectedresults: Host group is added to organization and then removed.

    :CaseLevel: Integration
    """
    hostgroup = entities.HostGroup().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'host_groups.resources.assigned': [hostgroup.name]})
        org_values = session.organization.read(org.name)
        assert org_values[
            'host_groups']['resources']['assigned'][0] == hostgroup.name
        session.organization.update(
            org.name, {'host_groups.resources.unassigned': [hostgroup.name]})
        org_values = session.organization.read(org.name)
        assert len(org_values['host_groups']['resources']['assigned']) == 0
        assert hostgroup.name in org_values[
            'host_groups']['resources']['unassigned']


@tier2
def test_positive_update_location(session):
    """Add/Remove location from/to organization.

    :id: 086efafa-0d7f-11e7-81e9-68f72889dc7f

    :expectedresults: Location is added/removed to/from organization.

    :CaseLevel: Integration
    """
    location = entities.Location().create()
    org = entities.Organization().create()
    with session:
        session.organization.update(
            org.name, {'locations.resources.assigned': [location.name]})
        org_values = session.organization.read(org.name)
        assert org_values[
            'locations']['resources']['assigned'][0] == location.name
        session.organization.update(
            org.name, {'locations.resources.unassigned': [location.name]})
        org_values = session.organization.read(org.name)
        assert len(org_values['locations']['resources']['assigned']) == 0
        assert location.name in org_values[
            'locations']['resources']['unassigned']


@skip_if_not_set('fake_manifest')
@tier2
@upgrade
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
        session.lifecycleenvironment.create(
            {'name': 'QE'},
            prior_entity_name='DEV',
        )
        # Org cannot be deleted when selected,
        # So switching to Default Org and then deleting.
        session.organization.select(DEFAULT_ORG)
        session.organization.delete(org.name)
        assert not session.organization.search(org.name)


@skip_if_not_set('fake_manifest')
@tier2
@upgrade
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
