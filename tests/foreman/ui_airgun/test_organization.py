"""Test class for Organization UI

:Requirement: Organization

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import INSTALL_MEDIUM_URL, LIBVIRT_RESOURCE_URL
from robottelo.decorators import skip_if_bug_open, skip_if_not_set, tier2


def test_positive_create(session):
    org_name = gen_string('alpha')
    with session:
        session.organization.create({
            'name': org_name,
            'label': gen_string('alpha'),
            'description': gen_string('alpha'),
        })
        assert session.organization.search(org_name)[0]['Name'] == org_name


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


@skip_if_bug_open('bugzilla', 1321543)
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
