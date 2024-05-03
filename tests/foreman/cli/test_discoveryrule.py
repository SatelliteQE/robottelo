"""Test class for Foreman Discovery Rules

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseComponent: DiscoveryPlugin

:Team: Rocket

:CaseImportance: High

"""

from functools import partial
import random

from box import Box
from fauxfactory import gen_choice, gen_integer, gen_string
from nailgun.entities import Role as RoleEntity, User as UserEntity
import pytest
from requests import HTTPError

from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.logging import logger
from robottelo.utils.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    parametrized,
    valid_data_list,
)


@filtered_datapoint
def invalid_hostnames_list():
    """Generates a list of invalid host names.

    :return: Returns the invalid host names list.
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


def gen_int32(min_value=1):
    max_value = (2**31) - 1
    return gen_integer(min_value=min_value, max_value=max_value)


class TestDiscoveryRule:
    """Implements Foreman discovery Rules tests in CLI."""

    @pytest.fixture
    def discoveryrule_factory(self, class_org, class_location, class_hostgroup, target_sat):
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
                'subnet = 192.168.100.0',
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
            return Box(target_sat.cli_factory.discoveryrule(options))

        return partial(
            _create_discoveryrule, org=class_org, loc=class_location, hostgroup=class_hostgroup
        )

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_with_name(self, name, discoveryrule_factory, target_sat):
        """Create Discovery Rule using different names

        :id: 066e66bc-c572-4ae9-b458-90daf83bab54

        :expectedresults: Rule should be successfully created.

        :CaseImportance: Critical

        :parametrized: yes
        """
        rule = discoveryrule_factory(options={'name': name, 'priority': gen_int32()})
        assert rule.name == name
        target_sat.cli.DiscoveryRule.delete({'id': rule.id})
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.DiscoveryRule.info({'id': rule.id})

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
        custom_query = 'processor = x86'
        rule = discoveryrule_factory(options={'search': custom_query})
        assert rule.search == custom_query

    @pytest.mark.tier2
    def test_positive_create_with_hostname(self, discoveryrule_factory):
        """Create Discovery Rule using valid hostname

        :id: deee22c3-dcfd-4940-b27c-cca137ec9a92

        :expectedresults: Rule should be successfully created and has expected
            hostname value

        """
        host_name = 'myhost'
        rule = discoveryrule_factory(options={'hostname': host_name})
        assert rule['hostname-template'] == host_name

    @pytest.mark.tier1
    def test_positive_create_and_update_with_org_loc_id(
        self, discoveryrule_factory, class_org, class_location, class_hostgroup, target_sat
    ):
        """Create discovery rule by associating org and location ids and update

        :id: bdb4c581-d27a-4d1a-920b-89689e68a57f

        :expectedresults: Rule was created with given org & location ids and updated.

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

        new_org = target_sat.cli_factory.make_org()
        new_loc = target_sat.cli_factory.make_location()
        new_hostgroup = target_sat.cli_factory.hostgroup(
            {'organization-ids': new_org.id, 'location-ids': new_loc.id}
        )
        target_sat.cli.DiscoveryRule.update(
            {
                'id': rule.id,
                'organization-ids': new_org.id,
                'location-ids': new_loc.id,
                'hostgroup-id': new_hostgroup.id,
            }
        )
        rule = target_sat.cli.DiscoveryRule.info({'id': rule.id}, output_format='json')
        assert new_org.name == rule['organizations'][0]['name']
        assert new_loc.name == rule['locations'][0]['name']
        assert new_hostgroup.name == rule['host-group']['name']

    @pytest.mark.tier2
    def test_positive_create_and_update_with_org_loc_name(
        self, discoveryrule_factory, class_org, class_location, class_hostgroup, target_sat
    ):
        """Create discovery rule by associating org and location names and update

        :id: f0d550ae-16d8-48ec-817e-d2e5b7405b46

        :expectedresults: Rule was created and with given org & location names and updated

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

        new_org = target_sat.cli_factory.make_org()
        new_loc = target_sat.cli_factory.make_location()
        new_hostgroup = target_sat.cli_factory.hostgroup(
            {'organization-ids': new_org.id, 'location-ids': new_loc.id}
        )

        target_sat.cli.DiscoveryRule.update(
            {
                'id': rule.id,
                'organizations': new_org.name,
                'locations': new_loc.name,
                'hostgroup-id': new_hostgroup.id,
            }
        )
        rule = target_sat.cli.DiscoveryRule.info({'id': rule.id}, output_format='json')
        assert new_org.name == rule['organizations'][0]['name']
        assert new_loc.name == rule['locations'][0]['name']
        assert new_hostgroup.name == rule['host-group']['name']

    @pytest.mark.tier2
    def test_positive_create_with_hosts_limit(self, discoveryrule_factory):
        """Create Discovery Rule providing any number from range 1..100 for
        hosts limit option

        :id: c28422c2-1f6a-4045-b722-f9f9d864e963

        :expectedresults: Rule should be successfully created and has expected
            hosts limit value

        """
        hosts_limit = '5'
        rule = discoveryrule_factory(options={'hosts-limit': hosts_limit})
        assert rule['hosts-limit'] == hosts_limit

    @pytest.mark.tier1
    def test_positive_create_and_update_with_priority(self, discoveryrule_factory, target_sat):
        """Create Discovery Rule providing any number from range 1..100 for
        priority option and update

        :id: 8ef58279-0ad3-41a4-b8dd-65594afdb655

        :expectedresults: Rule should be successfully created/updated and has expected
            priority value

        :CaseImportance: Critical
        """
        available = set(range(1, 1000)) - {
            int(Box(r).priority) for r in target_sat.cli.DiscoveryRule.list()
        }
        rule_priority = random.sample(sorted(available), 1)
        rule = discoveryrule_factory(options={'priority': rule_priority[0]})
        assert rule.priority == str(rule_priority[0])
        # Update
        target_sat.cli.DiscoveryRule.update({'id': rule.id, 'priority': rule_priority[0]})
        rule = Box(target_sat.cli.DiscoveryRule.info({'id': rule.id}))
        assert rule.priority == str(rule_priority[0])

    @pytest.mark.tier2
    def test_positive_create_disabled_rule(self, discoveryrule_factory):
        """Create Discovery Rule in disabled state

        :id: 8837a0c6-e19a-4c33-8b87-07b6f69dbb0f

        :expectedresults: Disabled rule should be successfully created

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

    @pytest.mark.tier3
    def test_positive_update_discovery_params(self, discoveryrule_factory, class_org, target_sat):
        """Update discovery rule parameters

        :id: 1045e2c4-e1f7-42c9-95f7-488fc79bf70b

        :expectedresults: Rule params are updated

        :CaseImportance: Medium
        """
        rule = discoveryrule_factory(options={'hosts-limit': '5'})
        new_name = gen_string('alpha')
        new_query = 'model = KVM'
        new_hostname = gen_string('alpha')
        new_limit = '10'
        new_hostgroup = target_sat.cli_factory.hostgroup({'organization-ids': class_org.id})

        target_sat.cli.DiscoveryRule.update(
            {
                'id': rule.id,
                'name': new_name,
                'search': new_query,
                'hostgroup': new_hostgroup.name,
                'hostname': new_hostname,
                'hosts-limit': new_limit,
            }
        )

        rule = Box(target_sat.cli.DiscoveryRule.info({'id': rule.id}))
        assert rule.name == new_name
        assert rule.search == new_query
        assert rule['host-group'] == new_hostgroup.name
        assert rule['hostname-template'] == new_hostname
        assert rule['hosts-limit'] == new_limit

    @pytest.mark.tier1
    def test_positive_update_disable_enable(self, discoveryrule_factory, target_sat):
        """Update discovery rule enabled state. (Disabled->Enabled)

        :id: 64e8b21b-2ab0-49c3-a12d-02dbdb36647a

        :expectedresults: Rule is successfully enabled

        :CaseImportance: Critical
        """
        rule = discoveryrule_factory(options={'enabled': 'false'})
        assert rule.enabled == 'false'
        target_sat.cli.DiscoveryRule.update({'id': rule.id, 'enabled': 'true'})
        rule = Box(target_sat.cli.DiscoveryRule.info({'id': rule.id}))
        assert rule.enabled == 'true'

    @pytest.mark.tier3
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_update_discovery_params(self, name, discoveryrule_factory, target_sat):
        """Update discovery rule name using invalid parameters

        :id: 8293cc6a-d983-460a-b76e-221ad02b54b7

        :expectedresults: Rule params are not updated

        :CaseImportance: Medium

        :parametrized: yes
        """
        rule = discoveryrule_factory()
        priority = gen_string('alpha')
        host_limit = gen_string('alpha')
        params = {
            'name': name,
            'hostname': '$#@!*',
            'hosts-limit': host_limit,
            'priority': priority,
        }
        key = random.choice(list(params.keys()))
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.DiscoveryRule.update(
                {
                    'id': rule.id,
                    key: params[key],
                }
            )

    @pytest.mark.tier1
    def test_positive_delete(self, discoveryrule_factory, target_sat):
        """Delete existing Discovery Rule

        :id: c9b88a94-13c4-496f-a5c1-c088187250dc

        :expectedresults: Rule should be successfully deleted

        :CaseImportance: Critical
        """
        rule = discoveryrule_factory()
        target_sat.cli.DiscoveryRule.delete({'id': rule.id})
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.DiscoveryRule.info({'id': rule.id})


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
        except HTTPError as err:
            logger.exception(err)
            logger.error('Exception while deleting class scope user entity in teardown')

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
        except HTTPError as err:
            logger.exception(err)
            logger.error('Exception while deleting class scope user entity in teardown')

    @pytest.mark.tier2
    def test_positive_crud_with_non_admin_user(
        self,
        class_org,
        class_location,
        class_user_password,
        class_user_manager,
        class_hostgroup,
        target_sat,
    ):
        """Create, update and delete rule with non-admin user by associating discovery_manager role

        :id: 056535aa-3338-4c1e-8a4b-ebfc8bd6e456

        :expectedresults: Rule should be created and deleted successfully.

        """
        rule_name = gen_string('alpha')
        new_name = gen_string('alpha')
        rule = Box(
            target_sat.cli.DiscoveryRule.with_user(
                class_user_manager.login, class_user_password
            ).create(
                {
                    'name': rule_name,
                    'search': 'cpu_count = 5',
                    'organizations': class_org.name,
                    'locations': class_location.name,
                    'hostgroup-id': class_hostgroup.id,
                }
            )
        )
        rule = Box(
            target_sat.cli.DiscoveryRule.with_user(
                class_user_manager.login, class_user_password
            ).info({'id': rule.id})
        )
        assert rule.name == rule_name

        target_sat.cli.DiscoveryRule.update(
            {
                'id': rule.id,
                'name': new_name,
            }
        )

        rule = Box(target_sat.cli.DiscoveryRule.info({'id': rule.id}))
        assert rule.name == new_name

        target_sat.cli.DiscoveryRule.with_user(
            class_user_manager.login, class_user_password
        ).delete({'id': rule.id})
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.DiscoveryRule.info({'id': rule.id})

    @pytest.mark.tier2
    def test_negative_delete_rule_with_non_admin_user(
        self,
        class_org,
        class_location,
        class_user_password,
        class_user_reader,
        class_hostgroup,
        target_sat,
    ):
        """Delete rule with non-admin user by associating discovery_reader role

        :id: f7f9569b-916e-46f3-bd89-a05e33483741

        :expectedresults: User should validation error and rule should not be
            deleted successfully.

        """
        rule = target_sat.cli_factory.make_discoveryrule(
            {
                'enabled': 'false',
                'search': "last_report = Today",
                'organizations': class_org.name,
                'locations': class_location.name,
                'hostgroup-id': class_hostgroup.id,
            }
        )

        rule = Box(
            target_sat.cli.DiscoveryRule.with_user(
                class_user_reader.login, class_user_password
            ).info({'id': rule.id})
        )
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.DiscoveryRule.with_user(
                class_user_reader.login, class_user_password
            ).delete({'id': rule.id})
