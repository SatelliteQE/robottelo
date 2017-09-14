# -*- encoding: utf-8 -*-
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

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import INSTALL_MEDIUM_URL, LIBVIRT_RESOURCE_URL
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_names_list,
    invalid_values_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment, make_org
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_labels():
    """Returns a list of valid labels"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    ]


@filtered_datapoint
def valid_users():
    """Returns a list of valid users"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
        gen_string('utf8'),
        gen_string('latin1'),
        # Note: HTML username is invalid as per the UI msg.
    ]


@filtered_datapoint
def valid_env_names():
    """Returns a list of valid environment names"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    ]


class OrganizationTestCase(UITestCase):
    """Implements Organization tests in UI"""

    @tier1
    def test_positive_search_autocomplete(self):
        """Search for an organization can be auto-completed by partial
        name

        :id: f3c492ab-46fb-4b1d-b5d5-29a82385d681

        :expectedresults: Auto search for created organization works as
            intended

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        part_string = org_name[:3]
        with Session(self) as session:
            page = session.nav.go_to_org
            make_org(session, org_name=org_name)
            auto_search = self.org.auto_complete_search(
                page, locators['org.org_name'], part_string, org_name,
                search_key='name')
            self.assertIsNotNone(auto_search)

    @tier1
    def test_positive_search_scoped(self):
        """Test scoped search functionality for organization by label

        :id: 18ad9aad-335a-414e-843e-e1c05ec6bcbb

        :expectedresults: Proper organization is found

        :BZ: 1259374

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        label = gen_string('alpha')
        with Session(self) as session:
            make_org(session, org_name=org_name, label=label)
            for query in [
                'label = {}'.format(label),
                'label ~ {}'.format(label[:-5]),
                'label ^ "{}"'.format(label),
            ]:
                self.assertIsNotNone(
                    self.org.search(org_name, _raw_query=query))

    @tier1
    def test_positive_create_with_name(self):
        """Create organization with valid name only.

        :id: bb5c6400-e837-4e3b-add9-bab2c0b826c9

        :expectedresults: Organization is created, label is auto-generated

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))

    @tier1
    def test_positive_create_with_unmatched_name_label(self):
        """Create organization with valid unmatching name and label only

        :id: 82954640-05c2-4d6c-a293-dc4aa3e5611b

        :expectedresults: organization is created, label does not match name

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for label in valid_labels():
                with self.subTest(label):
                    org_name = gen_string('alphanumeric')
                    make_org(
                        session, org_name=org_name, label=label)
                    self.org.search_and_click(org_name)
                    name = session.nav.wait_until_element(
                        locators['org.name']).get_attribute('value')
                    label = session.nav.wait_until_element(
                        locators['org.label']).get_attribute('value')
                    self.assertNotEqual(name, label)

    @tier1
    def test_positive_create_with_same_name_and_label(self):
        """Create organization with valid matching name and label only.

        :id: 73befc8c-bf96-48b7-8315-34f0cfef9382

        :expectedresults: organization is created, label matches name

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for item in valid_labels():
                with self.subTest(item):
                    make_org(session, org_name=item, label=item)
                    self.org.search_and_click(item)
                    name = self.org.wait_until_element(
                        locators['org.name']).get_attribute('value')
                    label = self.org.wait_until_element(
                        locators['org.label']).get_attribute('value')
                    self.assertEqual(name, label)

    @skip_if_bug_open('bugzilla', 1079482)
    @tier1
    def test_positive_create_with_auto_populated_label(self):
        """Create organization with valid name. Check that organization
        label is auto-populated

        :id: 29793945-c553-4a6e-881f-cdcde373aa62

        :expectedresults: organization is created, label is auto-generated

        :BZ: 1079482

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.search_and_click(org_name)
                    label = session.nav.wait_until_element(
                        locators['org.label'])
                    label_value = label.get_attribute('value')
                    self.assertIsNotNone(label_value)

    @tier2
    def test_positive_create_with_both_loc_and_org(self):
        """Select both organization and location.

        :id: 7387a8cd-6ebb-4143-b77e-cfc72cb89ca9

        :expectedresults: Both organization and location are selected.

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    #  Use nailgun to create Location
                    location = entities.Location(name=name).create()
                    self.assertEqual(location.name, name)
                    make_org(session, org_name=name, locations=[name])
                    self.assertIsNotNone(self.org.search(name))
                    organization = session.nav.go_to_select_org(name)
                    location = session.nav.go_to_select_loc(name)
                    self.assertEqual(organization, name)
                    self.assertEqual(location, name)

    @tier1
    def test_negative_create(self):
        """Try to create organization and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        :id: e69ab8c1-e53f-41fa-a84f-290c6c152484

        :expectedresults: organization is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in invalid_values_list(interface='ui'):
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @tier1
    def test_negative_create_with_same_name(self):
        """Create organization with valid names, then create a new one
        with same names.

        :id: d7fd91aa-1a0e-4403-8dea-cc03cbb93070

        :expectedresults: organization is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.create(org_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create organization with valid values then delete it.

        :id: 6b69d505-56b1-4d7d-bf2a-8762d5184ca8

        :expectedresults: Organization is deleted successfully

        :CaseImportance: Critical
        """
        with Session(self):
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    entities.Organization(name=org_name).create()
                    self.org.delete(org_name, dropdown_present=True)

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    @upgrade
    def test_verify_bugzilla_1225588(self):
        """Create Organization with valid values and upload manifest.
        Then try to delete that organization.

        :id: 851c8557-a406-4a70-9c8b-94bcf0482f8d

        :expectedresults: Organization is deleted successfully.

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org_name = gen_string('alphanumeric')
        org = entities.Organization(name=org_name).create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        with Session(self) as session:
            make_lifecycle_environment(session, org_name, name='DEV')
            make_lifecycle_environment(
                session, org_name, name='QE', prior='DEV'
            )
            # Org cannot be deleted when selected,
            # So switching to Default Org and then deleting.
            session.nav.go_to_select_org('Default Organization')
            self.org.delete(org_name, dropdown_present=True)
            for _ in range(10):
                status = self.org.search(org_name)
                if status is None:
                    break
            self.assertIsNone(status)

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    @upgrade
    def test_verify_bugzilla_1259248(self):
        """Create organization with valid manifest. Download debug
        certificate for that organization and refresh added manifest for few
        times in a row

        :id: 1fcd7cd1-8ba1-434f-b9fb-c4e920046eb4

        :expectedresults: Scenario passed successfully

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.original_manifest() as manifest:
            upload_manifest(org.id, manifest.content)
        try:
            with Session(self) as session:
                for _ in range(3):
                    self.assertIsNotNone(org.download_debug_certificate())
                    session.nav.go_to_select_org(org.name)
                    session.nav.go_to_red_hat_subscriptions()
                    self.subscriptions.refresh()
                    self.assertIsNone(session.nav.wait_until_element(
                        common_locators['notif.error'], timeout=5))
                    self.assertTrue(session.nav.wait_until_element(
                        common_locators['alert.success'], timeout=180))
        finally:
            sub.delete_manifest(data={'organization_id': org.id})

    @tier1
    def test_positive_update_name(self):
        """Create organization with valid values then update its name.

        :id: 776f5268-4f05-4cfc-a1e9-339a3e224677

        :expectedresults: Organization name is updated successfully

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        with Session(self) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.org.update(org_name, new_name=new_name)
                    self.assertIsNotNone(self.org.search(new_name))
                    org_name = new_name  # for next iteration

    @tier1
    def test_negative_update(self):
        """Create organization with valid values then try to update it
        using incorrect name values

        :id: 1467a04e-ebd6-4106-94b1-841a4f0ddecb

        :expectedresults: Organization name is not updated

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        with Session(self) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.org.update(org_name, new_name=new_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_domain(self):
        """Create Org with domain.

        :id: f5739862-ac2e-49ef-8f95-1823287f4978

        :expectedresults: Domain is added to organization during creation.

        :CaseLevel: Integration
        """
        with Session(self):
            for domain_name in generate_strings_list():
                with self.subTest(domain_name):
                    domain = entities.Domain(name=domain_name).create()
                    self.assertEqual(domain.name, domain_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'domains', domain_name))

    @run_only_on('sat')
    @tier2
    def test_positive_update_domain(self):
        """Add a domain to an organization and remove it by organization
        name and domain name.

        :id: a49e86c7-f859-4120-b59e-3f89e99a9054

        :expectedresults: the domain is added and removed from the organization

        :CaseLevel: Integration
        """

        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for domain_name in generate_strings_list():
                with self.subTest(domain_name):
                    domain = entities.Domain(name=domain_name).create()
                    self.assertEqual(domain.name, domain_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'domains',
                        'entity_name': domain_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @tier2
    def test_positive_create_with_user(self):
        """Create different types of users then add user during organization
        creation.

        :id: 5f2ec06b-952d-445d-b8a1-c32d74d33584

        :expectedresults: User is added to organization during creation.

        :CaseLevel: Integration
        """
        with Session(self):
            for user_name in valid_users():
                with self.subTest(user_name):
                    user = entities.User(
                        login=user_name,
                        firstname=user_name,
                        lastname=user_name,
                        password=gen_string('alpha')
                    ).create()
                    self.assertEqual(user.login, user_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'users', user_name))

    @tier2
    def test_positive_update_user(self):
        """Create admin users then add user and remove it
        by using the organization name.

        :id: 01a221f7-d0fe-4b46-ab5c-b4e861677126

        :expectedresults: The user is added then removed from the organization

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for user_name in valid_users():
                with self.subTest(user_name):
                    # Use nailgun to create user
                    user = entities.User(
                        login=user_name,
                        firstname=user_name,
                        lastname=user_name,
                        password=gen_string('alpha'),
                    ).create()
                    self.assertEqual(user.login, user_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'users',
                        'entity_name': user_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(
                        **kwargs))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_hostgroup(self):
        """Add a hostgroup during organization creation.

        :id: ce1b5334-5601-42ae-aa04-3e766daa3984

        :expectedresults: hostgroup is added to organization

        :CaseLevel: Integration
        """
        with Session(self):
            for hostgroup_name in generate_strings_list():
                with self.subTest(hostgroup_name):
                    # Create host group using nailgun
                    hostgroup = entities.HostGroup(
                        name=hostgroup_name).create()
                    self.assertEqual(hostgroup.name, hostgroup_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'hostgroups', hostgroup_name))

    @run_only_on('sat')
    @tier2
    def test_positive_update_hostgroup(self):
        """Add a hostgroup and remove it by using the organization
        name and hostgroup name.

        :id: 12e2fc40-d721-4e71-af7c-3db67b9e718e

        :expectedresults: hostgroup is added to organization then removed.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for hostgroup_name in generate_strings_list():
                with self.subTest(hostgroup_name):
                    # Create hostgroup using nailgun
                    hostgroup = entities.HostGroup(
                        name=hostgroup_name).create()
                    self.assertEqual(hostgroup.name, hostgroup_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'hostgroups',
                        'entity_name': hostgroup_name,
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_location(self):
        """Add a location during organization creation

        :id: 65ee568b-c0c5-4849-969d-02d7a804292c

        :expectedresults: location is added to organization.

        :CaseLevel: Integration
        """
        with Session(self):
            for location_name in generate_strings_list():
                with self.subTest(location_name):
                    location = entities.Location(name=location_name).create()
                    self.assertEqual(location.name, location_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'locations', location_name))

    @run_only_on('sat')
    @tier2
    def test_positive_update_location(self):
        """Check location is added and removed from/to existing organization

        :id: 086efafa-0d7f-11e7-81e9-68f72889dc7f

        :expectedresults: location is added/removed to/from organization.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for location_name in generate_strings_list():
                with self.subTest(location_name):
                    location = entities.Location(
                        name=location_name).create()
                    self.assertEqual(location.name, location_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'locations',
                        'entity_name': location_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @run_only_on('sat')
    @skip_if_not_set('compute_resources')
    @tier2
    def test_positive_create_with_compresource(self):
        """Add compute resource during organization creation

        :id: de9f755a-cf06-4ee0-a2f7-f1bfb1015b36

        :expectedresults: compute resource is added.

        :CaseLevel: Integration
        """
        with Session(self):
            for resource_name in generate_strings_list():
                with self.subTest(resource_name):
                    url = (LIBVIRT_RESOURCE_URL %
                           settings.compute_resources.libvirt_hostname)
                    # Create compute resource using nailgun
                    resource = entities.LibvirtComputeResource(
                        name=resource_name,
                        url=url,
                    ).create()
                    self.assertEqual(resource.name, resource_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'resources', resource_name))

    @run_only_on('sat')
    @skip_if_not_set('compute_resources')
    @tier2
    def test_positive_update_compresource(self):
        """Remove compute resource using the organization name and
        compute resource name.

        :id: db119bb1-8f79-415b-a056-70a19ffceeea

        :expectedresults: compute resource is added then removed.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for resource_name in generate_strings_list():
                with self.subTest(resource_name):
                    url = (LIBVIRT_RESOURCE_URL %
                           settings.compute_resources.libvirt_hostname)
                    # Create compute resource using nailgun
                    resource = entities.LibvirtComputeResource(
                        name=resource_name,
                        url=url
                    ).create()
                    self.assertEqual(resource.name, resource_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'resources',
                        'entity_name': resource_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_media(self):
        """Add medium during organization creation.

        :id: e9b1004d-55f0-448f-8013-543d8b9ec248

        :expectedresults: medium is added.

        :CaseLevel: Integration
        """
        with Session(self):
            for media_name in generate_strings_list():
                with self.subTest(media_name):
                    # Create media using nailgun
                    media = entities.Media(
                        name=media_name,
                        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
                        os_family='Redhat',
                    ).create()
                    self.assertEqual(media.name, media_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'medias', media_name))

    @run_only_on('sat')
    @tier2
    def test_positive_update_media(self):
        """Add/Remove medium from/to organization.

        :id: bcf3aaf4-cad9-4a22-a087-60b213eb87cf

        :expectedresults: medium is added then removed.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for media_name in generate_strings_list():
                with self.subTest(media_name):
                    # Create media using nailgun
                    media = entities.Media(
                        name=media_name,
                        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
                        os_family='Redhat',
                    ).create()
                    self.assertEqual(media.name, media_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'medias',
                        'entity_name': media_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_template(self):
        """Add config template during organization creation.

        :id: 2af534d4-2f92-4b25-81d9-d0129f9cf866

        :expectedresults: config template is added

        :CaseLevel: Integration
        """
        with Session(self):
            for template_name in generate_strings_list():
                with self.subTest(template_name):
                    # Create config template using nailgun
                    template = entities.ProvisioningTemplate(
                        name=template_name).create()
                    self.assertEqual(template.name, template_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'templates', template_name))

    @run_only_on('sat')
    @tier2
    def test_positive_update_template(self):
        """Add and Remove config template.

        :id: 67bec745-5f10-494c-92a7-173ee63e8297

        :expectedresults: Config Template is added and then removed.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for template_name in generate_strings_list():
                with self.subTest(template_name):
                    # Create config template using nailgun
                    template = entities.ProvisioningTemplate(
                        name=template_name).create()
                    self.assertEqual(template.name, template_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'templates',
                        'entity_name': template_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_ptable(self):
        """Add ptable during organization creation

        :id: a33f66f0-0d89-11e7-abd9-68f72889dc7f

        :expectedresults: Partition table is added.

        :CaseLevel: Integration
        """
        with Session(self):
            for ptable_name in generate_strings_list():
                with self.subTest(ptable_name):
                    # Create partition table using nailgun
                    ptable = entities.PartitionTable(name=ptable_name).create()
                    self.assertEqual(ptable.name, ptable_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'ptables', ptable_name))

    @run_only_on('sat')
    @tier2
    def test_positive_update_ptable(self):
        """Remove partition table.

        :id: 75662a83-0921-45fd-a4b5-012c48bb003a

        :expectedresults: Partition table is added and then removed.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for ptable_name in generate_strings_list():
                with self.subTest(ptable_name):
                    # Create partition table using nailgun
                    ptable = entities.PartitionTable(name=ptable_name).create()
                    self.assertEqual(ptable.name, ptable_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'ptables',
                        'entity_name': ptable_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_environment(self):
        """Add environment during organization creation.

        :id: 95b96642-0424-4df1-83ef-d548ceb6e10b

        :expectedresults: Environment is added.

        :CaseLevel: Integration
        """
        with Session(self):
            for environment_name in valid_env_names():
                with self.subTest(environment_name):
                    environment = entities.Environment(
                        name=environment_name).create()
                    self.assertEqual(environment.name, environment_name)
                    self.assertIsNotNone(self.org.create_with_entity(
                        gen_string('alpha'), 'envs', environment_name))

    @run_only_on('sat')
    @tier2
    def test_positive_update_environment(self):
        """Add and Remove environment by using org & environment name.

        :id: 270de90d-062e-4893-89c9-f6d0665ab967

        :expectedresults: environment is added then removed from Organization.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            org_name = gen_string('alpha')
            make_org(session, org_name=org_name)
            for environment_name in valid_env_names():
                with self.subTest(environment_name):
                    # Create environment using nailgun
                    environment = entities.Environment(
                        name=environment_name).create()
                    self.assertEqual(environment.name, environment_name)
                    kwargs = {
                        'org_name': org_name,
                        'entity_type': 'envs',
                        'entity_name': environment_name
                    }
                    self.assertIsNotNone(self.org.add_entity(**kwargs))
                    self.assertIsNotNone(self.org.remove_entity(**kwargs))

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_with_smartproxy(self):
        """Add a smart proxy during org creation.

        :id: 7ad6f610-91ca-4f1f-b9c4-8ce82f50ea9e

        :expectedresults: smartproxy is added

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_update_smartproxy(self):
        """Add and Remove smartproxy by using organization name and smartproxy
        name

        :id: 25bc6334-de59-462c-824a-51d615d9fdd0

        :expectedresults: smartproxy is added then removed

        :caseautomation: notautomated

        :CaseLevel: Integration
        """
