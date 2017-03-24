# -*- encoding: utf-8 -*-
"""Test class for Organization UI

@Requirement: Organization

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_ipaddr, gen_string
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
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment, make_org
from robottelo.ui.locators import common_locators, locators, tab_locators
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
    return[
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

    # Tests for issues

    @tier1
    def test_positive_search_autocomplete(self):
        """Search for an organization can be auto-completed by partial
        name

        @id: f3c492ab-46fb-4b1d-b5d5-29a82385d681

        @expectedresults: Auto search for created organization works as
        intended
        """
        org_name = gen_string('alpha')
        part_string = org_name[:3]
        with Session(self.browser) as session:
            page = session.nav.go_to_org
            make_org(session, org_name=org_name)
            auto_search = self.org.auto_complete_search(
                page, locators['org.org_name'], part_string, org_name,
                search_key='name')
            self.assertIsNotNone(auto_search)

    @tier1
    def test_positive_create_with_name(self):
        """Create organization with valid name only.

        @id: bb5c6400-e837-4e3b-add9-bab2c0b826c9

        @expectedresults: Organization is created, label is auto-generated
        """
        with Session(self.browser) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))

    @tier1
    def test_positive_create_with_unmatched_name_label(self):
        """Create organization with valid unmatching name and label only

        @id: 82954640-05c2-4d6c-a293-dc4aa3e5611b

        @expectedresults: organization is created, label does not match name
        """
        with Session(self.browser) as session:
            for label in valid_labels():
                with self.subTest(label):
                    org_name = gen_string('alphanumeric')
                    make_org(
                        session, org_name=org_name, label=label)
                    self.org.search(org_name).click()
                    name = session.nav.wait_until_element(
                        locators['org.name']).get_attribute('value')
                    label = session.nav.wait_until_element(
                        locators['org.label']).get_attribute('value')
                    self.assertNotEqual(name, label)

    @tier1
    def test_positive_create_with_same_name_and_label(self):
        """Create organization with valid matching name and label only.

        @id: 73befc8c-bf96-48b7-8315-34f0cfef9382

        @expectedresults: organization is created, label matches name
        """
        with Session(self.browser) as session:
            for item in valid_labels():
                with self.subTest(item):
                    make_org(session, org_name=item, label=item)
                    self.org.search(item).click()
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

        @id: 29793945-c553-4a6e-881f-cdcde373aa62

        @expectedresults: organization is created, label is auto-generated

        @BZ: 1079482
        """
        with Session(self.browser) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.search(org_name).click()
                    label = session.nav.wait_until_element(
                        locators['org.label'])
                    label_value = label.get_attribute('value')
                    self.assertIsNotNone(label_value)

    @tier2
    def test_positive_create_with_both_loc_and_org(self):
        """Select both organization and location.

        @id: 7387a8cd-6ebb-4143-b77e-cfc72cb89ca9

        @expectedresults: Both organization and location are selected.

        @CaseLevel: Integration
        """
        with Session(self.browser) as session:
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

        @id: e69ab8c1-e53f-41fa-a84f-290c6c152484

        @expectedresults: organization is not created
        """
        with Session(self.browser) as session:
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

        @id: d7fd91aa-1a0e-4403-8dea-cc03cbb93070

        @expectedresults: organization is not created
        """
        with Session(self.browser) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.create(org_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @tier1
    def test_positive_delete(self):
        """Create organization with valid values then delete it.

        @id: 6b69d505-56b1-4d7d-bf2a-8762d5184ca8

        @expectedresults: Organization is deleted successfully
        """
        with Session(self.browser):
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    # Use nailgun to create org
                    entities.Organization(name=org_name).create()
                    self.org.delete(org_name)

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_verify_bugzilla_1225588(self):
        """Create Organization with valid values and upload manifest.
        Then try to delete that organization.

        @id: 851c8557-a406-4a70-9c8b-94bcf0482f8d

        @expectedresults: Organization is deleted successfully.

        @CaseLevel: Integration
        """
        org_name = gen_string('alphanumeric')
        org = entities.Organization(name=org_name).create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org_name, name='DEV')
            make_lifecycle_environment(
                session, org_name, name='QE', prior='DEV'
            )
            # Org cannot be deleted when selected,
            # So switching to Default Org and then deleting.
            session.nav.go_to_select_org('Default Organization')
            self.org.delete(org_name)
            for _ in range(10):
                status = self.org.search(org_name)
                if status is None:
                    break
            self.assertIsNone(status)

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_verify_bugzilla_1259248(self):
        """Create organization with valid manifest. Download debug
        certificate for that organization and refresh added manifest for few
        times in a row

        @id: 1fcd7cd1-8ba1-434f-b9fb-c4e920046eb4

        @expectedresults: Scenario passed successfully

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.original_manifest() as manifest:
            upload_manifest(org.id, manifest.content)
        try:
            with Session(self.browser) as session:
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

        @id: 776f5268-4f05-4cfc-a1e9-339a3e224677

        @expectedresults: Organization name is updated successfully
        """
        org_name = gen_string('alpha')
        with Session(self.browser) as session:
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

        @id: 1467a04e-ebd6-4106-94b1-841a4f0ddecb

        @expectedresults: Organization name is not updated
        """
        org_name = gen_string('alpha')
        with Session(self.browser) as session:
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
    def test_positive_remove_domain(self):
        """Add a domain to an organization and remove it by organization
        name and domain name.

        @id: a49e86c7-f859-4120-b59e-3f89e99a9054

        @expectedresults: the domain is removed from the organization

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for domain_name in generate_strings_list():
                with self.subTest(domain_name):
                    org_name = gen_string('alpha')
                    domain = entities.Domain(name=domain_name).create()
                    self.assertEqual(domain.name, domain_name)
                    make_org(session, org_name=org_name, domains=[domain_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_domains'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % domain_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(org_name, domains=[domain_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_domains'])
                    element = session.nav.wait_until_element(
                        (strategy, value % domain_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @tier2
    def test_positive_remove_user(self):
        """Create admin users then add user and remove it
        by using the organization name.

        @id: 01a221f7-d0fe-4b46-ab5c-b4e861677126

        @expectedresults: The user is added then removed from the organization

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for user_name in valid_users():
                with self.subTest(user_name):
                    org_name = gen_string('alpha')
                    # Use nailgun to create user
                    user = entities.User(
                        login=user_name,
                        firstname=user_name,
                        lastname=user_name,
                        password=gen_string('alpha'),
                    ).create()
                    self.assertEqual(user.login, user_name)
                    make_org(session, org_name=org_name, users=[user_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_users'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % user_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(
                        org_name, users=[user_name], new_users=None)
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_users'])
                    element = session.nav.wait_until_element(
                        (strategy, value % user_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_hostgroup(self):
        """Add a hostgroup and remove it by using the organization
        name and hostgroup name.

        @id: 12e2fc40-d721-4e71-af7c-3db67b9e718e

        @expectedresults: hostgroup is added to organization then removed.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for host_grp_name in generate_strings_list():
                with self.subTest(host_grp_name):
                    org_name = gen_string('alpha')
                    # Create hostgroup using nailgun
                    host_grp = entities.HostGroup(name=host_grp_name).create()
                    self.assertEqual(host_grp.name, host_grp_name)
                    make_org(
                        session, org_name=org_name, hostgroups=[host_grp_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_hostgrps'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % host_grp_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(
                        org_name,
                        hostgroups=[host_grp_name],
                        new_hostgroups=None
                    )
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_hostgrps'])
                    element = session.nav.wait_until_element(
                        (strategy, value % host_grp_name))
                    # Item is listed in 'All Items' list and not
                    # Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_smartproxy(self):
        """Add a smart proxy by using org and smartproxy name

        @id: 7ad6f610-91ca-4f1f-b9c4-8ce82f50ea9e

        @expectedresults: smartproxy is added

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_subnet(self):
        """Add a subnet using organization name and subnet name.

        @id: 6736cd82-a2b0-4fc0-a2bc-99c9f13464d7

        @expectedresults: subnet is added.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for subnet_name in generate_strings_list():
                with self.subTest(subnet_name):
                    org_name = gen_string('alpha')
                    # Create subnet using nailgun
                    subnet = entities.Subnet(
                        name=subnet_name,
                        network=gen_ipaddr(ip3=True),
                        mask='255.255.255.0'
                    ).create()
                    self.assertEqual(subnet.name, subnet_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_subnets=[subnet_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_subnets'])
                    element = session.nav.wait_until_element(
                        (strategy, value % subnet_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_domain(self):
        """Add a domain to an organization.

        @id: f5739862-ac2e-49ef-8f95-1823287f4978

        @expectedresults: Domain is added to organization.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for domain_name in generate_strings_list():
                with self.subTest(domain_name):
                    org_name = gen_string('alpha')
                    domain = entities.Domain(name=domain_name).create()
                    self.assertEqual(domain.name, domain_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_domains=[domain_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_domains'])
                    element = session.nav.wait_until_element(
                        (strategy, value % domain_name))
                    self.assertIsNotNone(element)

    @tier2
    def test_positive_add_user(self):
        """Create different types of users then add user using
        organization name.

        @id: 5f2ec06b-952d-445d-b8a1-c32d74d33584

        @expectedresults: User is added to organization.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for user_name in valid_users():
                with self.subTest(user_name):
                    org_name = gen_string('alpha')
                    user = entities.User(
                        login=user_name,
                        firstname=user_name,
                        lastname=user_name,
                        password=gen_string('alpha')
                    ).create()
                    self.assertEqual(user.login, user_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_users=[user_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_users'])
                    element = session.nav.wait_until_element(
                        (strategy, value % user_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_hostgroup(self):
        """Add a hostgroup by using the organization
        name and hostgroup name.

        @id: ce1b5334-5601-42ae-aa04-3e766daa3984

        @expectedresults: hostgroup is added to organization

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for host_grp_name in generate_strings_list():
                with self.subTest(host_grp_name):
                    org_name = gen_string('alpha')
                    # Create host group using nailgun
                    host_grp = entities.HostGroup(name=host_grp_name).create()
                    self.assertEqual(host_grp.name, host_grp_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_hostgroups=[host_grp_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_hostgrps'])
                    element = session.nav.wait_until_element(
                        (strategy, value % host_grp_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_location(self):
        """Add a location by using the organization name and location
        name

        @id: 65ee568b-c0c5-4849-969d-02d7a804292c

        @expectedresults: location is added to organization.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for location_name in generate_strings_list():
                with self.subTest(location_name):
                    org_name = gen_string('alpha')
                    location = entities.Location(name=location_name).create()
                    self.assertEqual(location.name, location_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_locations=[location_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_locations'])
                    element = session.nav.wait_until_element(
                        (strategy, value % location_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @skip_if_not_set('compute_resources')
    @tier2
    def test_positive_remove_compresource(self):
        """Remove compute resource using the organization name and
        compute resource name.

        @id: db119bb1-8f79-415b-a056-70a19ffceeea

        @expectedresults: compute resource is added then removed.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for resource_name in generate_strings_list():
                with self.subTest(resource_name):
                    org_name = gen_string('alpha')
                    url = (LIBVIRT_RESOURCE_URL %
                           settings.compute_resources.libvirt_hostname)
                    # Create compute resource using nailgun
                    resource = entities.LibvirtComputeResource(
                        name=resource_name,
                        url=url
                    ).create()
                    self.assertEqual(resource.name, resource_name)
                    make_org(
                        session, org_name=org_name, resources=[resource_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_resources'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % resource_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(
                        org_name,
                        resources=[resource_name],
                        new_resources=None
                    )
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_resources'])
                    element = session.nav.wait_until_element(
                        (strategy, value % resource_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_medium(self):
        """Remove medium by using organization name and medium name.

        @id: bcf3aaf4-cad9-4a22-a087-60b213eb87cf

        @expectedresults: medium is added then removed.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for medium_name in generate_strings_list():
                with self.subTest(medium_name):
                    org_name = gen_string('alpha')
                    # Create media using nailgun
                    medium = entities.Media(
                        name=medium_name,
                        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
                        os_family='Redhat',
                    ).create()
                    self.assertEqual(medium.name, medium_name)
                    make_org(session, org_name=org_name, medias=[medium_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_media'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % medium_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.navigator.go_to_org()
                    self.org.update(
                        org_name, medias=[medium_name], new_medias=None)
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_media'])
                    element = session.nav.wait_until_element(
                        (strategy, value % medium_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_template(self):
        """Remove config template.

        @id: 67bec745-5f10-494c-92a7-173ee63e8297

        @expectedresults: Config Template is added and then removed.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for template_name in generate_strings_list():
                with self.subTest(template_name):
                    org_name = gen_string('alpha')
                    # Create config template using nailgun
                    entities.ConfigTemplate(name=template_name).create()
                    make_org(
                        session, org_name=org_name, templates=[template_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_template'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % template_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(org_name, templates=[template_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_template'])
                    element = self.org.wait_until_element(
                        (strategy, value % template_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_ptable(self):
        """Remove partition table.

        @id: 75662a83-0921-45fd-a4b5-012c48bb003a

        @expectedresults: Partition table is added and then removed.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for ptable_name in generate_strings_list():
                with self.subTest(ptable_name):
                    org_name = gen_string('alpha')
                    # Create partition table using nailgun
                    entities.PartitionTable(name=ptable_name).create()
                    make_org(
                        session, org_name=org_name, ptables=[ptable_name])
                    self.org.click(self.org.search(org_name))
                    self.org.click(tab_locators['context.tab_ptable'])
                    element = self.org.wait_until_element(
                        (strategy1, value1 % ptable_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(org_name, ptables=[ptable_name])
                    self.org.click(self.org.search(org_name))
                    self.org.click(tab_locators['context.tab_ptable'])
                    element = self.org.wait_until_element(
                        (strategy, value % ptable_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_environment(self):
        """Add environment by using organization name and env name.

        @id: 95b96642-0424-4df1-83ef-d548ceb6e10b

        @expectedresults: Environment is added.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for env_name in valid_env_names():
                with self.subTest(env_name):
                    org_name = gen_string('alpha')
                    env = entities.Environment(name=env_name).create_json()
                    self.assertEqual(env['name'], env_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_envs=[env_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_env'])
                    element = session.nav.wait_until_element(
                        (strategy, value % env_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_smartproxy(self):
        """Remove smartproxy by using organization name and smartproxy
        name

        @id: 25bc6334-de59-462c-824a-51d615d9fdd0

        @expectedresults: smartproxy is added then removed

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @skip_if_not_set('compute_resources')
    @tier2
    def test_positive_add_compresource(self):
        """Add compute resource using the organization
        name and compute resource name.

        @id: de9f755a-cf06-4ee0-a2f7-f1bfb1015b36

        @expectedresults: compute resource is added.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for resource_name in generate_strings_list():
                with self.subTest(resource_name):
                    org_name = gen_string('alpha')
                    url = (LIBVIRT_RESOURCE_URL %
                           settings.compute_resources.libvirt_hostname)
                    # Create compute resource using nailgun
                    resource = entities.LibvirtComputeResource(
                        name=resource_name,
                        url=url,
                    ).create()
                    self.assertEqual(resource.name, resource_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_resources=[resource_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_resources'])
                    element = session.nav.wait_until_element(
                        (strategy, value % resource_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_medium(self):
        """Add medium by using the organization name and medium name.

        @id: e9b1004d-55f0-448f-8013-543d8b9ec248

        @expectedresults: medium is added.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for medium_name in generate_strings_list():
                with self.subTest(medium_name):
                    org_name = gen_string('alpha')
                    # Create media using nailgun
                    medium = entities.Media(
                        name=medium_name,
                        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
                        os_family='Redhat',
                    ).create()
                    self.assertEqual(medium.name, medium_name)
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_medias=[medium_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_media'])
                    element = session.nav.wait_until_element(
                        (strategy, value % medium_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_template(self):
        """Add config template by using organization name and
        config template name.

        @id: 2af534d4-2f92-4b25-81d9-d0129f9cf866

        @expectedresults: config template is added

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for template_name in generate_strings_list():
                with self.subTest(template_name):
                    org_name = gen_string('alpha')
                    # Create config template using nailgun
                    entities.ConfigTemplate(name=template_name).create()
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.update(org_name, new_templates=[template_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_template'])
                    element = session.nav.wait_until_element(
                        (strategy, value % template_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_environment(self):
        """Remove environment by using org & environment name.

        @id: 270de90d-062e-4893-89c9-f6d0665ab967

        @expectedresults: environment is removed from Organization.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for env_name in valid_env_names():
                with self.subTest(env_name):
                    org_name = gen_string('alpha')
                    # Create environment using nailgun
                    env = entities.Environment(name=env_name).create_json()
                    self.assertEqual(env['name'], env_name)
                    make_org(session, org_name=org_name, envs=[env_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_env'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % env_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(org_name, envs=[env_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_env'])
                    element = session.nav.wait_until_element(
                        (strategy, value % env_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_subnet(self):
        """Remove subnet by using organization name and subnet name.

        @id: bc59bdeb-b538-4473-a096-e4de2454497d

        @expectedresults: subnet is added then removed.

        @CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            for subnet_name in generate_strings_list():
                with self.subTest(subnet_name):
                    org_name = gen_string('alpha')
                    # Create subnet using nailgun
                    subnet = entities.Subnet(
                        name=subnet_name,
                        network=gen_ipaddr(ip3=True),
                        mask='255.255.255.0',
                    ).create()
                    self.assertEqual(subnet.name, subnet_name)
                    make_org(session, org_name=org_name, subnets=[subnet_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_subnets'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % subnet_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.org.update(org_name, subnets=[subnet_name])
                    self.org.search(org_name).click()
                    session.nav.click(tab_locators['context.tab_subnets'])
                    element = session.nav.wait_until_element(
                        (strategy, value % subnet_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)
