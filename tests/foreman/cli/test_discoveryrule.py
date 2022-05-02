"""Test class for Foreman Discovery Rules

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: DiscoveryPlugin

:Assignee: gsulliva

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
from functools import partial

import pytest
from attrdict import AttrDict
from fauxfactory import gen_choice
from fauxfactory import gen_string
from nailgun.entities import Role as RoleEntity
from nailgun.entities import User as UserEntity
from requests import HTTPError

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.discoveryrule import DiscoveryRule
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_discoveryrule
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.logging import logger


@filtered_datapoint
def invalid_hostnames_list():
    """Generates a list of invalid host names.

    :return: Returns the invalid host names list
    """
    return {
        'cjk': gen_string('cjk'),
        'latin': gen_string('latin1'),
        'numeric': gen_string('numeric'),
        'utf8': gen_string('utf8'),
        'special': '$#@!*',
        'whitespace': '" "',
        'negative': '-1',
    }


class TestDiscoveryRule:
    """Implements Foreman discovery Rules tests in CLI."""

    @pytest.fixture(scope='function')
    def discoveryrule_factory(self, class_org, class_location, class_hostgroup):
        def _create_discoveryrule(org, loc, hostgroup, options=None):
            """Makes a new discovery rule and asserts its success"""
            options = options or {}

            searches = [
                'cpu_count = 1',
                'disk_count < 5',
                'memory > 500',
                'model = KVM',
                'Organization = Default_Organization',
                'last_report = Today',
                'subnet =  192.168.100.0',
                'facts.architecture != x86_64',
            ]

            if not any(options.get(key) for key in ['organizations', 'organization-ids']):
                options['organization-ids'] = org.id
            if not any(options.get(key) for key in ['locations', 'locations-ids']):
                options['location-ids'] = loc.id
            if not any(options.get(key) for key in ['hostgroup', 'hostgroup-ids']):
                options['hostgroup-id'] = hostgroup.id
            if options.get('search') is None:
                options['search'] = gen_choice(searches)

            # create a simple object from the dictionary that the CLI factory provides
            # This allows for consistent attributized access of all fixture entities in the tests
            return AttrDict(make_discoveryrule(options))

        return partial(
            _create_discoveryrule, org=class_org, loc=class_location, hostgroup=class_hostgroup
        )

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_with_name(self, name, discoveryrule_factory):
        """Create Discovery Rule using different names

        :id: 066e66bc-c572-4ae9-b458-90daf83bab54

        :expectedresults: Rule should be successfully created

        :CaseImportance: Critical

        :parametrized: yes
        """
        rule = discoveryrule_factory(options={'name': name})
        assert rule.name == name

    @pytest.mark.tier1
    def test_positive_create_with_search(self, discoveryrule_factory):
        """Create Discovery Rule using different search queries

        :id: 2383e898-a968-4183-a270-55e9350e0596

        :expectedresults: Rule should be successfully created and has expected
            search value

        :CaseImportance: Critical
        """
        search_query = 'cpu_count = 2'
        rule = discoveryrule_factory(options={'search': search_query})
        assert rule.search == search_query

    @pytest.mark.tier2
    def test_positive_create_with_hostname(self, discoveryrule_factory):
        """Create Discovery Rule using valid hostname

        :id: deee22c3-dcfd-4940-b27c-cca137ec9a92

        :expectedresults: Rule should be successfully created and has expected
            hostname value

        :CaseLevel: Component
        """
        host_name = 'myhost'
        rule = discoveryrule_factory(options={'hostname': host_name})
        assert rule['hostname-template'] == host_name

    @pytest.mark.tier1
    def test_positive_create_with_org_loc_id(
        self, discoveryrule_factory, class_org, class_location, class_hostgroup
    ):
        """Create discovery rule by associating org and location ids

        :id: bdb4c581-d27a-4d1a-920b-89689e68a57f

        :expectedresults: Rule was created and with given org & location names.

        :BZ: 1377990, 1523221

        :CaseImportance: Critical
        """
        rule = discoveryrule_factory(
            options={
                'hostgroup-id': class_hostgroup.id,
                'organization-ids': class_org.id,
                'location-ids': class_location.id,
            }
        )
        assert class_org.name in rule.organizations
        assert class_location.name in rule.locations

    @pytest.mark.tier2
    def test_positive_create_with_org_loc_name(
        self, discoveryrule_factory, class_org, class_location, class_hostgroup
    ):
        """Create discovery rule by associating org and location names

        :id: f0d550ae-16d8-48ec-817e-d2e5b7405b46

        :expectedresults: Rule was created and with given org & location names.

        :BZ: 1377990
        """
        rule = discoveryrule_factory(
            options={
                'hostgroup-id': class_hostgroup.id,
                'organizations': class_org.name,
                'locations': class_location.name,
            }
        )
        assert class_org.name in rule.organizations
        assert class_location.name in rule.locations

    @pytest.mark.tier2
    def test_positive_create_with_hosts_limit(self, discoveryrule_factory):
        """Create Discovery Rule providing any number from range 1..100 for
        hosts limit option

        :id: c28422c2-1f6a-4045-b722-f9f9d864e963

        :expectedresults: Rule should be successfully created and has expected
            hosts limit value

        :CaseLevel: Component
        """
        hosts_limit = '5'
        rule = discoveryrule_factory(options={'hosts-limit': hosts_limit})
        assert rule['hosts-limit'] == hosts_limit

    @pytest.mark.tier1
    def test_positive_create_with_max_count(self, discoveryrule_factory):
        """Create Discovery Rule providing any number from range 1..100 for
        max count option

        :id: 590ca353-d3d7-4700-be34-13de00f46276

        :expectedresults: Rule should be successfully created and has max_count
            set as per given value

        :CaseLevel: Component
        """
        max_count = '10'
        rule = discoveryrule_factory(options={'max-count': max_count})
        assert rule['hosts-limit'] == max_count

    @pytest.mark.tier1
    def test_positive_create_with_priority(self, discoveryrule_factory):
        """Create Discovery Rule providing any number from range 1..100 for
        priority option

        :id: 8ef58279-0ad3-41a4-b8dd-65594afdb655

        :expectedresults: Rule should be successfully created and has expected
            priority value

        :CaseImportance: Critical
        """
        available = set(range(1, 1000)) - {AttrDict(r).priority for r in DiscoveryRule.list()}
        rule_priority = random.sample(available, 1)
        rule = discoveryrule_factory(options={'priority': rule_priority[0]})
        assert rule.priority == str(rule_priority[0])

    @pytest.mark.tier2
    def test_positive_create_disabled_rule(self, discoveryrule_factory):
        """Create Discovery Rule in disabled state

        :id: 8837a0c6-e19a-4c33-8b87-07b6f69dbb0f

        :expectedresults: Disabled rule should be successfully created

        :CaseLevel: Component
        """
        rule = discoveryrule_factory(options={'enabled': 'false'})
        assert rule.enabled == 'false'

    @pytest.mark.tier3
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_invalid_name(self, name, discoveryrule_factory):
        """Create Discovery Rule with invalid names

        :id: a0350dc9-8f5b-4673-be88-a5e35d1f8ca7

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Medium

        :CaseLevel: Component

        :parametrized: yes
        """
        with pytest.raises(CLIFactoryError):
            discoveryrule_factory(options={'name': name})

    @pytest.mark.tier3
    @pytest.mark.parametrize('name', **parametrized(invalid_hostnames_list()))
    def test_negative_create_with_invalid_hostname(self, name, discoveryrule_factory):
        """Create Discovery Rule with invalid hostname

        :id: 0ae51085-30d0-44f9-9e49-abe928a8a4b7

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Medium

        :CaseLevel: Component

        :BZ: 1378427

        :parametrized: yes
        """
        with pytest.raises(CLIFactoryError):
            discoveryrule_factory(options={'hostname': name})

    @pytest.mark.tier3
    def test_negative_create_with_too_long_limit(self, discoveryrule_factory):
        """Create Discovery Rule with too long host limit value

        :id: 12dbb023-c963-4ead-a81e-ad53033de947

        :expectedresults: Validation error should be raised and rule should not
            be created

        :CaseImportance: Medium
        """
        with pytest.raises(CLIFactoryError):
            discoveryrule_factory(options={'hosts-limit': '9999999999'})

    @pytest.mark.tier1
    def test_negative_create_with_same_name(self, discoveryrule_factory):
        """Create Discovery Rule with name that already exists

        :id: 0906cf64-ed0b-49af-844f-1af22f81ab94

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        discoveryrule_factory(options={'name': name})
        with pytest.raises(CLIFactoryError):
            discoveryrule_factory(options={'name': name})

    @pytest.mark.tier1
    def test_positive_delete(self, discoveryrule_factory):
        """Delete existing Discovery Rule

        :id: c9b88a94-13c4-496f-a5c1-c088187250dc

        :expectedresults: Rule should be successfully deleted

        :CaseImportance: Critical
        """
        rule = discoveryrule_factory()
        DiscoveryRule.delete({'id': rule.id})
        with pytest.raises(CLIReturnCodeError):
            DiscoveryRule.info({'id': rule.id})

    @pytest.mark.tier3
    def test_positive_update_name(self, discoveryrule_factory):
        """Update discovery rule name

        :id: 1045e2c4-e1f7-42c9-95f7-488fc79bf70b

        :expectedresults: Rule name is updated

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        rule = discoveryrule_factory()
        new_name = gen_string('numeric')
        DiscoveryRule.update({'id': rule.id, 'name': new_name})
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert rule.name == new_name

    @pytest.mark.tier2
    def test_positive_update_org_loc_by_id(self, discoveryrule_factory):
        """Update org and location of selected discovery rule using org/loc ids

        :id: 26da79aa-30e5-4052-98ae-141de071a68a

        :expectedresults: Rule was updated and with given org & location.

        :BZ: 1377990

        :CaseLevel: Component
        """
        new_org = AttrDict(make_org())
        new_loc = AttrDict(make_location())
        new_hostgroup = AttrDict(
            make_hostgroup({'organization-ids': new_org.id, 'location-ids': new_loc.id})
        )
        rule = discoveryrule_factory()
        DiscoveryRule.update(
            {
                'id': rule.id,
                'organization-ids': new_org.id,
                'location-ids': new_loc.id,
                'hostgroup-id': new_hostgroup.id,
            }
        )
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert new_org.name in rule.organizations
        assert new_loc.name in rule.locations

    @pytest.mark.tier3
    def test_positive_update_org_loc_by_name(self, discoveryrule_factory):
        """Update org and location of selected discovery rule using org/loc
        names

        :id: 7a5d61ac-6a2d-48f6-a00d-df437a7dc3c4

        :expectedresults: Rule was updated and with given org & location.

        :BZ: 1377990

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        new_org = AttrDict(make_org())
        new_loc = AttrDict(make_location())
        new_hostgroup = AttrDict(
            make_hostgroup({'organization-ids': new_org.id, 'location-ids': new_loc.id})
        )
        rule = discoveryrule_factory()
        DiscoveryRule.update(
            {
                'id': rule.id,
                'organizations': new_org.name,
                'locations': new_loc.name,
                'hostgroup-id': new_hostgroup.id,
            }
        )
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert new_org.name in rule.organizations
        assert new_loc.name in rule.locations

    @pytest.mark.tier2
    def test_positive_update_query(self, discoveryrule_factory):
        """Update discovery rule search query

        :id: 86943095-acc5-40ff-8e3c-88c76b36333d

        :expectedresults: Rule search field is updated

        :CaseLevel: Component
        """
        rule = discoveryrule_factory()
        new_query = 'model = KVM'
        DiscoveryRule.update({'id': rule.id, 'search': new_query})
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert rule.search == new_query

    @pytest.mark.tier2
    def test_positive_update_hostgroup(self, discoveryrule_factory, class_org):
        """Update discovery rule host group

        :id: 07992a3f-2aa9-4e45-b2e8-ef3d2f255292

        :expectedresults: Rule host group is updated

        :CaseLevel: Component
        """
        new_hostgroup = AttrDict(make_hostgroup({'organization-ids': class_org.id}))
        rule = discoveryrule_factory()
        DiscoveryRule.update({'id': rule.id, 'hostgroup': new_hostgroup.name})
        rule = DiscoveryRule.info({'id': rule.id})
        # AttrDict doesn't support attributized access on key with a hyphen
        assert rule['host-group'] == new_hostgroup.name

    @pytest.mark.tier2
    def test_positive_update_hostname(self, discoveryrule_factory):
        """Update discovery rule hostname value

        :id: 4c123488-92df-42f6-afe3-8a88cd90ffc2

        :expectedresults: Rule host name is updated

        :CaseLevel: Component
        """
        new_hostname = gen_string('alpha')
        rule = discoveryrule_factory()
        DiscoveryRule.update({'id': rule.id, 'hostname': new_hostname})
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert rule['hostname-template'] == new_hostname

    @pytest.mark.tier2
    def test_positive_update_limit(self, discoveryrule_factory):
        """Update discovery rule limit value

        :id: efa6f5bc-4d56-4449-90f5-330affbcfb09

        :expectedresults: Rule host limit field is updated

        :CaseLevel: Component
        """
        rule = discoveryrule_factory(options={'hosts-limit': '5'})
        new_limit = '10'
        DiscoveryRule.update({'id': rule.id, 'hosts-limit': new_limit})
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert rule['hosts-limit'] == new_limit

    @pytest.mark.tier1
    def test_positive_update_priority(self, discoveryrule_factory):
        """Update discovery rule priority value

        :id: 0543cc73-c692-4bbf-818b-37353ec98986

        :expectedresults: Rule priority is updated

        :CaseImportance: Critical
        """
        available = set(range(1, 1000)) - {AttrDict(r).priority for r in DiscoveryRule.list()}
        rule_priority = random.sample(available, 1)
        rule = discoveryrule_factory(options={'priority': rule_priority[0]})
        assert rule.priority == str(rule_priority[0])
        available = set(range(1, 1000)) - {AttrDict(r).priority for r in DiscoveryRule.list()}
        rule_priority = random.sample(available, 1)
        DiscoveryRule.update({'id': rule.id, 'priority': rule_priority[0]})
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert rule.priority == str(rule_priority[0])

    @pytest.mark.tier1
    def test_positive_update_disable_enable(self, discoveryrule_factory):
        """Update discovery rule enabled state. (Disabled->Enabled)

        :id: 64e8b21b-2ab0-49c3-a12d-02dbdb36647a

        :expectedresults: Rule is successfully enabled

        :CaseImportance: Critical
        """
        rule = discoveryrule_factory(options={'enabled': 'false'})
        assert rule.enabled == 'false'
        DiscoveryRule.update({'id': rule.id, 'enabled': 'true'})
        rule = AttrDict(DiscoveryRule.info({'id': rule.id}))
        assert rule.enabled == 'true'

    @pytest.mark.tier3
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, name, discoveryrule_factory):
        """Update discovery rule name using invalid names only

        :id: 8293cc6a-d983-460a-b76e-221ad02b54b7

        :expectedresults: Rule name is not updated

        :CaseLevel: Component

        :CaseImportance: Medium

        :parametrized: yes
        """
        rule = discoveryrule_factory()
        with pytest.raises(CLIReturnCodeError):
            DiscoveryRule.update({'id': rule.id, 'name': name})

    @pytest.mark.tier3
    def test_negative_update_hostname(self, discoveryrule_factory):
        """Update discovery rule host name using number as a value

        :id: c382dbc7-9509-4060-9038-1617f7fef038

        :expectedresults: Rule host name is not updated

        :CaseImportance: Medium

        :CaseLevel: Component
        """
        rule = discoveryrule_factory()
        with pytest.raises(CLIReturnCodeError):
            DiscoveryRule.update({'id': rule.id, 'hostname': '$#@!*'})

    @pytest.mark.tier3
    def test_negative_update_limit(self, discoveryrule_factory):
        """Update discovery rule host limit using invalid values

        :id: e3257d8a-91b9-406f-bd74-0fd1fb05bb77

        :expectedresults: Rule host limit is not updated

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        rule = discoveryrule_factory()
        host_limit = gen_string('alpha')
        with pytest.raises(CLIReturnCodeError):
            DiscoveryRule.update({'id': rule.id, 'hosts-limit': host_limit})

    @pytest.mark.tier3
    def test_negative_update_priority(self, discoveryrule_factory):
        """Update discovery rule priority using invalid values

        :id: 0778dd00-aa19-4062-bdf3-752e1b546ec2

        :expectedresults: Rule priority is not updated

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        rule = discoveryrule_factory()
        priority = gen_string('alpha')
        with pytest.raises(CLIReturnCodeError):
            DiscoveryRule.update({'id': rule.id, 'priority': priority})


class TestDiscoveryRuleRole:
    """Implements Foreman discovery Rules tests along with roles from CLI."""

    @pytest.fixture(scope='class')
    def class_user_manager(self, class_user_password, class_org, class_location):
        try:
            manager_role = RoleEntity().search(query={'search': 'name="Discovery Manager"'})[0]
        except IndexError:
            pytest.fail('Discovery Manager role was not found, setup cannot continue')
        user = UserEntity(
            organization=[class_org],
            location=[class_location],
            password=class_user_password,
            role=[manager_role],
        ).create()
        yield user
        try:
            user.delete()
        except HTTPError:
            logger.exception('Exception while deleting class scope user entity in teardown')

    @pytest.fixture(scope='class')
    def class_user_reader(self, class_user_password, class_org, class_location):
        try:
            reader_role = RoleEntity().search(query={'search': 'name="Discovery Reader"'})[0]
        except IndexError:
            pytest.fail('Discovery Manager role was not found, setup cannot continue')
        user = UserEntity(
            organization=[class_org],
            location=[class_location],
            password=class_user_password,
            role=[reader_role],
        ).create()
        yield user
        try:
            user.delete()
        except HTTPError:
            logger.exception('Exception while deleting class scope user entity in teardown')

    @pytest.mark.tier2
    def test_positive_create_rule_with_non_admin_user(
        self, class_org, class_location, class_user_password, class_user_manager, class_hostgroup
    ):
        """Create rule with non-admin user by associating discovery_manager role

        :id: 056535aa-3338-4c1e-8a4b-ebfc8bd6e456

        :expectedresults: Rule should be created successfully.

        :CaseLevel: Integration
        """
        rule_name = gen_string('alpha')
        rule = AttrDict(
            DiscoveryRule.with_user(class_user_manager.login, class_user_password).create(
                {
                    'name': rule_name,
                    'search': 'cpu_count = 5',
                    'organizations': class_org.name,
                    'locations': class_location.name,
                    'hostgroup-id': class_hostgroup.id,
                }
            )
        )
        rule = AttrDict(
            DiscoveryRule.with_user(class_user_manager.login, class_user_password).info(
                {'id': rule.id}
            )
        )
        assert rule.name == rule_name

    @pytest.mark.tier2
    def test_positive_delete_rule_with_non_admin_user(
        self, class_org, class_location, class_user_manager, class_hostgroup, class_user_password
    ):
        """Delete rule with non-admin user by associating discovery_manager role

        :id: 87ab969b-7d92-478d-a5c0-1c0d50e9bdd6

        :expectedresults: Rule should be deleted successfully.

        :CaseLevel: Integration
        """
        rule_name = gen_string('alpha')
        rule = AttrDict(
            DiscoveryRule.with_user(class_user_manager.login, class_user_password).create(
                {
                    'name': rule_name,
                    'search': 'cpu_count = 5',
                    'organizations': class_org.name,
                    'locations': class_location.name,
                    'hostgroup-id': class_hostgroup.id,
                }
            )
        )
        rule = AttrDict(
            DiscoveryRule.with_user(class_user_manager.login, class_user_password).info(
                {'id': rule.id}
            )
        )

        DiscoveryRule.with_user(class_user_manager.login, class_user_password).delete(
            {'id': rule.id}
        )
        with pytest.raises(CLIReturnCodeError):
            DiscoveryRule.info({'id': rule.id})

    @pytest.mark.tier2
    def test_positive_view_existing_rule_with_non_admin_user(
        self, class_org, class_location, class_user_password, class_user_reader, class_hostgroup
    ):
        """Existing rule should be viewed to non-admin user by associating
        discovery_reader role.

        :id: 7b1d90b9-fc2d-4ccb-93d3-605c2da876f7

        :Steps:

            1. create a rule with admin user
            2. create a non-admin user and assign 'Discovery Reader' role
            3. Login with non-admin user

        :expectedresults: Rule should be visible to non-admin user.

        :CaseLevel: Integration
        """
        rule_name = gen_string('alpha')
        rule = AttrDict(
            make_discoveryrule(
                {
                    'name': rule_name,
                    'enabled': 'false',
                    'search': "last_report = Today",
                    'organizations': class_org.name,
                    'locations': class_location.name,
                    'hostgroup-id': class_hostgroup.id,
                }
            )
        )
        rule = AttrDict(
            DiscoveryRule.with_user(class_user_reader.login, class_user_password).info(
                {'id': rule.id}
            )
        )
        assert rule.name == rule_name

    @pytest.mark.tier2
    def test_negative_delete_rule_with_non_admin_user(
        self, class_org, class_location, class_user_password, class_user_reader, class_hostgroup
    ):
        """Delete rule with non-admin user by associating discovery_reader role

        :id: f7f9569b-916e-46f3-bd89-a05e33483741

        :expectedresults: User should validation error and rule should not be
            deleted successfully.

        :CaseLevel: Integration
        """
        rule = AttrDict(
            make_discoveryrule(
                {
                    'enabled': 'false',
                    'search': "last_report = Today",
                    'organizations': class_org.name,
                    'locations': class_location.name,
                    'hostgroup-id': class_hostgroup.id,
                }
            )
        )
        rule = AttrDict(
            DiscoveryRule.with_user(class_user_reader.login, class_user_password).info(
                {'id': rule.id}
            )
        )
        with pytest.raises(CLIReturnCodeError):
            DiscoveryRule.with_user(class_user_reader.login, class_user_password).delete(
                {'id': rule.id}
            )
