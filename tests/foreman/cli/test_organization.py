"""Test class for Organization CLI

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

from robottelo.cleanup import capsule_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_compute_resource
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_proxy
from robottelo.cli.factory import make_subnet
from robottelo.cli.factory import make_template
from robottelo.cli.factory import make_user
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.org import Org
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_org_names_list


@filtered_datapoint
def valid_labels_list():
    """Random simpler data for positive creation

    Use this when name and label must match. Labels cannot contain the same
    data type as names, so this is a bit limited compared to other tests.
    Label cannot contain characters other than ascii alpha numerals, '_', '-'.
    """
    return [
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        f"{gen_string('alpha', 5)}-{gen_string('alpha', 5)}",
        f"{gen_string('alpha', 5)}_{gen_string('alpha', 5)}",
    ]


@pytest.fixture
def proxy():
    """Create a Proxy and clean up when done."""
    proxy = make_proxy()
    yield proxy
    capsule_cleanup(proxy_id=proxy['id'])


@pytest.mark.tier2
def test_verify_bugzilla_1078866():
    """hammer organization <info,list> --help types information
    doubled

    :id: 7938bcc4-7107-40b0-bb88-6288ebec0dcd

    :BZ: 1078866, 1647323

    :expectedresults: no duplicated lines in usage message

    :CaseImportance: Low
    """
    # org list --help:
    result = Org.list({'help': True}, output_format=None)
    # get list of lines and check they all are unique
    lines = [line for line in result if line != '' and '----' not in line]
    assert len(set(lines)) == len(lines)

    # org info --help:info returns more lines (obviously), ignore exception
    result = Org.info({'help': True}, output_format=None)

    # get list of lines and check they all are unique
    lines = [line for line in result['options']]
    assert len(set(lines)) == len(lines)


@pytest.mark.tier1
def test_positive_CRD():
    """Create organization with valid name, label and description

    :id: 35840da7-668e-4f78-990a-738aa688d586

    :expectedresults: organization is created with attributes

    :CaseImportance: Critical

    create read
    """
    # Create
    name = valid_org_names_list()[0]
    label = valid_labels_list()[0]
    desc = list(valid_data_list().values())[0]
    org = make_org({'name': name, 'label': label, 'description': desc})

    assert org['name'] == name
    assert org['label'] == label
    assert org['description'] == desc

    # List
    result = Org.list({'search': f'name={name}'})
    assert len(result) == 1
    assert result[0]['name'] == name

    # Search scoped
    for query in [
        f'label = {label}',
        f'description ~ {desc[:-5]}',
        f'name ^ "{name}"',
    ]:
        result = Org.list({'search': query})
        assert len(result) == 1
        assert result[0]['name'] == name

    # Search by name and label
    result = Org.exists(search=('name', name))
    assert result['name'] == name
    result = Org.exists(search=('label', label))
    assert result['name'] == name

    # Info by name and label
    result = Org.info({'label': label})
    assert result['id'] == org['id']
    result = Org.info({'name': name})
    assert org['id'] == result['id']

    # Delete
    Org.delete({'id': org['id']})
    with pytest.raises(CLIReturnCodeError):
        result = Org.info({'id': org['id']})


@pytest.mark.tier2
def test_positive_create_with_system_admin_user():
    """Create organization using user with system admin role

    :id: 1482ab6e-18c7-4a62-81a2-cc969ac373fe

    :expectedresults: organization is created

    :BZ: 1644586
    """
    login = gen_string('alpha')
    password = gen_string('alpha')
    org_name = gen_string('alpha')
    make_user({'login': login, 'password': password})
    User.add_role({'login': login, 'role': 'System admin'})
    make_org({'user': login, 'password': password, 'name': org_name})
    result = Org.info({'name': org_name})
    assert result['name'] == org_name


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_add_and_remove_subnets(module_org):
    """add and remove a subnet from organization

    :id: adb5310b-76c5-4aca-8220-fdf0fe605cb0

    :BZ:
        1. Add and remove subnet by name
        2. Add and remove subnet by id

    :expectedresults: Subnets are handled as expected

    :BZ: 1395229

    :CaseLevel: Integration
    """
    subnets = [make_subnet() for _ in range(0, 2)]
    Org.add_subnet({'name': module_org.name, 'subnet': subnets[0]['name']})
    Org.add_subnet({'name': module_org.name, 'subnet-id': subnets[1]['id']})
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['subnets']) == 2, "Failed to add subnets"
    Org.remove_subnet({'name': module_org.name, 'subnet': subnets[0]['name']})
    Org.remove_subnet({'name': module_org.name, 'subnet-id': subnets[1]['id']})
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['subnets']) == 0, "Failed to remove subnets"


@pytest.mark.tier2
def test_positive_add_and_remove_users(module_org):
    """Add and remove (admin) user to organization

    :id: c35b2e88-a65f-4eea-ba55-89cef59f30be

    :expectedresults: Users are added and removed from the org

    :steps:
        1. create and delete user by name
        2. create and delete user by id
        3. create and delete admin user by name
        4. create and delete admin user by id

    :BZ: 1395229

    :CaseLevel: Integration
    """
    user = make_user()
    admin_user = make_user({'admin': '1'})
    assert admin_user['admin'] == 'yes'

    # add and remove user and admin user by name
    Org.add_user({'name': module_org.name, 'user': user['login']})
    Org.add_user({'name': module_org.name, 'user': admin_user['login']})
    org_info = Org.info({'name': module_org.name})
    assert user['login'] in org_info['users'], "Failed to add user by name"
    assert admin_user['login'] in org_info['users'], "Failed to add admin user by name"

    Org.remove_user({'name': module_org.name, 'user': user['login']})
    Org.remove_user({'name': module_org.name, 'user': admin_user['login']})
    org_info = Org.info({'name': module_org.name})
    assert user['login'] not in org_info['users'], "Failed to remove user by name"
    assert admin_user['login'] not in org_info['users'], "Failed to remove admin user by name"

    # add and remove user and admin user by id
    Org.add_user({'id': module_org.id, 'user-id': user['id']})
    Org.add_user({'id': module_org.id, 'user-id': admin_user['id']})
    org_info = Org.info({'id': module_org.id})
    assert user['login'] in org_info['users'], "Failed to add user by id"
    assert admin_user['login'] in org_info['users'], "Failed to add admin user by id"

    Org.remove_user({'id': module_org.id, 'user-id': user['id']})
    Org.remove_user({'id': module_org.id, 'user-id': admin_user['id']})
    org_info = Org.info({'id': module_org.id})
    assert user['login'] not in org_info['users'], "Failed to remove user by id"
    assert admin_user['login'] not in org_info['users'], "Failed to remove admin user by id"


@pytest.mark.tier2
def test_positive_add_and_remove_hostgroups(module_org):
    """add and remove a hostgroup from an organization

    :id: 34e2c7c8-dc20-4709-a5a9-83c0dee9d84d

    :expectedresults: Hostgroups are handled as expected

    :BZ: 1395229

    :steps:
        1. add and remove hostgroup by name
        2. add and remove hostgroup by id

    :CaseLevel: Integration
    """
    hostgroups = [make_hostgroup() for _ in range(0, 2)]

    Org.add_hostgroup({'hostgroup-id': hostgroups[0]['id'], 'id': module_org.id})
    Org.add_hostgroup({'hostgroup': hostgroups[1]['name'], 'name': module_org.name})
    org_info = Org.info({'name': module_org.name})
    assert hostgroups[0]['name'] in org_info['hostgroups'], "Failed to add hostgroup by id"
    assert hostgroups[1]['name'] in org_info['hostgroups'], "Failed to add hostgroup by name"
    Org.remove_hostgroup({'hostgroup-id': hostgroups[1]['id'], 'id': module_org.id})
    Org.remove_hostgroup({'hostgroup': hostgroups[0]['name'], 'name': module_org.name})
    org_info = Org.info({'id': module_org.id})
    assert hostgroups[0]['name'] not in org_info['hostgroups'], "Failed to remove hostgroup by name"
    assert hostgroups[1]['name'] not in org_info['hostgroups'], "Failed to remove hostgroup by id"


@pytest.mark.skip_if_not_set('libvirt')
@pytest.mark.tier2
@pytest.mark.libvirt_discovery
@pytest.mark.upgrade
def test_positive_add_and_remove_compute_resources(module_org):
    """Add and remove a compute resource from organization

    :id: 415c14ab-f879-4ed8-9ba7-8af4ada2e277

    :expectedresults: Compute resource are handled as expected

    :BZ: 1395229

    :steps:
        1. Add and remove compute resource by id
        2. Add and remove compute resource by name

    :CaseLevel: Integration
    """
    compute_resources = [
        make_compute_resource(
            {
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'url': f'qemu+ssh://root@{settings.libvirt.libvirt_hostname}/system',
            },
        )
        for _ in range(0, 2)
    ]
    Org.add_compute_resource(
        {'compute-resource-id': compute_resources[0]['id'], 'id': module_org.id}
    )
    Org.add_compute_resource(
        {'compute-resource': compute_resources[1]['name'], 'name': module_org.name}
    )
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['compute-resources']) == 2, "Failed to add compute resources"
    Org.remove_compute_resource(
        {'compute-resource-id': compute_resources[0]['id'], 'id': module_org.id}
    )
    Org.remove_compute_resource(
        {'compute-resource': compute_resources[1]['name'], 'name': module_org.name}
    )
    org_info = Org.info({'id': module_org.id})
    assert (
        compute_resources[0]['name'] not in org_info['compute-resources']
    ), "Failed to remove compute resource by id"
    assert (
        compute_resources[1]['name'] not in org_info['compute-resources']
    ), "Failed to remove compute resource by name"


@pytest.mark.tier2
def test_positive_add_and_remove_media(module_org):
    """Add and remove medium to organization

    :id: c2943a81-c8f7-44c4-926b-388055d7c290

    :expectedresults: Media are handled as expected

    :BZ: 1395229

    :steps:
        1. add and remove medium by id
        2. add and remove medium by name

    :CaseLevel: Integration
    """
    media = [make_medium() for _ in range(0, 2)]
    Org.add_medium({'id': module_org.id, 'medium-id': media[0]['id']})
    Org.add_medium({'name': module_org.name, 'medium': media[1]['name']})
    org_info = Org.info({'id': module_org.id})
    assert media[0]['name'] in org_info['installation-media'], "Failed to add medium by id"
    assert media[1]['name'] in org_info['installation-media'], "Failed to add medium by name"
    Org.remove_medium({'name': module_org.name, 'medium': media[0]['name']})
    Org.remove_medium({'id': module_org.id, 'medium-id': media[1]['id']})
    org_info = Org.info({'id': module_org.id})
    assert media[0]['name'] not in org_info['installation-media'], "Failed to remove medium by name"
    assert media[1]['name'] not in org_info['installation-media'], "Failed to remove medium by id"


@pytest.mark.tier2
@pytest.mark.skip_if_open("BZ:1845860")
@pytest.mark.skip_if_open("BZ:1886876")
def test_positive_add_and_remove_templates(module_org):
    """Add and remove provisioning templates to organization

    :id: bd46a192-488f-4da0-bf47-1f370ae5f55c

    :expectedresults: Templates are handled as expected

    :BZ: 1845860, 1886876

    :steps:
        1. Add and remove template by id
        2. Add and remove template by name

    :CaseLevel: Integration
    """
    # create and remove templates by name
    name = list(valid_data_list().values())[0]

    template = make_template({'content': gen_string('alpha'), 'name': name})
    # Add provisioning-template
    Org.add_provisioning_template(
        {'name': module_org.name, 'provisioning-template': template['name']}
    )
    org_info = Org.info({'name': module_org.name})
    assert (
        f"{template['name']} ({template['type']})" in org_info['templates']
    ), "Failed to add template by name"
    # Remove provisioning-template
    Org.remove_provisioning_template(
        {'provisioning-template': template['name'], 'name': module_org.name}
    )
    org_info = Org.info({'name': module_org.name})
    assert (
        f"{template['name']} ({template['type']})" not in org_info['templates']
    ), "Failed to remove template by name"

    # add and remove templates by id
    # Add provisioning-template
    Org.add_provisioning_template({'provisioning-template-id': template['id'], 'id': module_org.id})
    org_info = Org.info({'id': module_org.id})
    assert (
        f"{template['name']} ({template['type']})" in org_info['templates']
    ), "Failed to add template by name"
    # Remove provisioning-template
    Org.remove_provisioning_template(
        {'provisioning-template-id': template['id'], 'id': module_org.id}
    )
    org_info = Org.info({'id': module_org.id})
    assert (
        f"{template['name']} ({template['type']})" not in org_info['templates']
    ), "Failed to remove template by id"


@pytest.mark.tier2
def test_positive_add_and_remove_domains(module_org):
    """Add and remove domains to organization

    :id: 97359ffe-4ce6-4e44-9e3f-583d3fdebbc8

    :expectedresults: Domains are handled correctly

    :BZ: 1395229

    :steps:
        1. Add and remove domain by name
        2. Add and remove domain by id

    :CaseLevel: Integration
    """
    domains = [make_domain() for _ in range(0, 2)]
    Org.add_domain({'domain-id': domains[0]['id'], 'name': module_org.name})
    Org.add_domain({'domain': domains[1]['name'], 'name': module_org.name})
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['domains']) == 2, "Failed to add domains"
    assert domains[0]['name'] in org_info['domains']
    assert domains[1]['name'] in org_info['domains']
    Org.remove_domain({'domain': domains[0]['name'], 'name': module_org.name})
    Org.remove_domain({'domain-id': domains[1]['id'], 'id': module_org.id})
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['domains']) == 0, "Failed to remove domains"


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_add_and_remove_lce(module_org):
    """Remove a lifecycle environment from organization

    :id: bfa9198e-6078-4f10-b79a-3d7f51b835fd

    :expectedresults: Lifecycle environment is handled as expected

    :steps:
        1. create and add lce to org
        2. remove lce from org

    :CaseLevel: Integration
    """
    # Create a lifecycle environment.
    lc_env_name = make_lifecycle_environment({'organization-id': module_org.id})['name']
    lc_env_attrs = {'name': lc_env_name, 'organization-id': module_org.id}
    # Read back information about the lifecycle environment. Verify the
    # sanity of that information.
    response = LifecycleEnvironment.list(lc_env_attrs)
    assert response[0]['name'] == lc_env_name
    # Delete it.
    LifecycleEnvironment.delete(lc_env_attrs)
    # We should get a zero-length response when searching for the LC env.
    response = LifecycleEnvironment.list(lc_env_attrs)
    assert len(response) == 0


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_add_and_remove_capsules(proxy, module_org):
    """Add and remove a capsule from organization

    :id: 71af64ec-5cbb-4dd8-ba90-652e302305ec

    :expectedresults: Capsules are handled correctly

    :steps:
        1. add and remove capsule by ip
        2. add and remove capsule by name

    :CaseLevel: Integration
    """
    Org.add_smart_proxy({'id': module_org.id, 'smart-proxy-id': proxy['id']})
    org_info = Org.info({'name': module_org.name})
    assert proxy['name'] in org_info['smart-proxies'], "Failed to add capsule by id"
    Org.remove_smart_proxy({'id': module_org.id, 'smart-proxy-id': proxy['id']})
    org_info = Org.info({'id': module_org.id})
    assert proxy['name'] not in org_info['smart-proxies'], "Failed to remove capsule by id"
    Org.add_smart_proxy({'name': module_org.name, 'smart-proxy': proxy['name']})
    org_info = Org.info({'name': module_org.name})
    assert proxy['name'] in org_info['smart-proxies'], "Failed to add capsule by name"
    Org.remove_smart_proxy({'name': module_org.name, 'smart-proxy': proxy['name']})
    org_info = Org.info({'name': module_org.name})
    assert proxy['name'] not in org_info['smart-proxies'], "Failed to add capsule by name"


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_add_and_remove_locations(module_org):
    """Add and remove a locations from organization

    :id: 37b63e5c-8fd5-439c-9540-972b597b590a

    :expectedresults: Locations are handled

    :BZ: 1395229, 1473387

    :steps:
        1. add and remove locations by name
        2. add and remove locations by id

    :CaseLevel: Integration
    """
    locations = [make_location() for _ in range(0, 2)]
    Org.add_location({'location-id': locations[0]['id'], 'name': module_org.name})
    Org.add_location({'location': locations[1]['name'], 'name': module_org.name})
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['locations']) == 2, "Failed to add locations"
    assert locations[0]['name'] in org_info['locations']
    assert locations[1]['name'] in org_info['locations']
    Org.remove_location({'location-id': locations[0]['id'], 'id': module_org.id})
    Org.remove_location({'location': locations[1]['name'], 'id': module_org.id})
    org_info = Org.info({'id': module_org.id})
    assert not org_info.get('locations'), "Failed to remove locations"


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_add_and_remove_parameter(module_org):
    """Remove a parameter from organization

    :id: e4099279-4e73-4c14-9e7c-912b3787b99f

    :expectedresults: Parameter is removed from the org

    :CaseImportance: Critical
    """
    param_name = gen_string('alpha')
    param_new_value = gen_string('alpha')

    org_info = Org.info({'id': module_org.id})
    assert len(org_info['parameters']) == 0

    # Create parameter
    Org.set_parameter(
        {'name': param_name, 'value': gen_string('alpha'), 'organization-id': module_org.id}
    )
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['parameters']) == 1

    # Update
    Org.set_parameter(
        {'name': param_name, 'value': param_new_value, 'organization': module_org.name}
    )
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['parameters']) == 1
    assert param_new_value == org_info['parameters'][param_name.lower()]

    # Delete parameter
    Org.delete_parameter({'name': param_name, 'organization': module_org.name})
    org_info = Org.info({'id': module_org.id})
    assert len(org_info['parameters']) == 0
    assert param_name.lower() not in org_info['parameters']


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_invalid_name(name):
    """Try to create an organization with invalid name, but valid label and
    description

    :id: f0aecf1e-d093-4365-af85-b3650ed21318

    :parametrized: yes

    :expectedresults: organization is not created

    """
    with pytest.raises(CLIFactoryError):
        make_org(
            {
                'description': gen_string('alpha'),
                'label': gen_string('alpha'),
                'name': name,
            }
        )


@pytest.mark.tier1
def test_negative_create_same_name(module_org):
    """Create a new organization with same name, description, and label.

    :id: 07924e1f-1eff-4bae-b0db-e41b84966bc1

    :expectedresults: organization is not created

    :CaseImportance: Critical
    """
    with pytest.raises(CLIFactoryError):
        make_org(
            {
                'description': module_org.description,
                'label': module_org.label,
                'name': module_org.name,
            }
        )


@pytest.mark.tier1
def test_positive_update(module_org):
    """Update organization name and description

    :id: 66581003-f5d9-443c-8cd6-00f68087e8e9

    :expectedresults: organization name is updated

    :CaseImportance: Critical
    """

    new_name = valid_org_names_list()[0]
    new_desc = list(valid_data_list().values())[0]

    # upgrade name
    Org.update({'id': module_org.id, 'new-name': new_name})
    org = Org.info({'id': module_org.id})
    assert org['name'] == new_name

    # upgrade description
    Org.update({'description': new_desc, 'id': org['id']})
    org = Org.info({'id': org['id']})
    assert org['description'] == new_desc


@pytest.mark.tier1
@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
def test_negative_update_name(new_name, module_org):
    """Fail to update organization name for invalid values.

    :id: 582d41b8-370d-45ed-9b7b-8096608e1324

    :parametrized: yes

    :expectedresults: organization name is not updated

    """
    with pytest.raises(CLIReturnCodeError):
        Org.update({'id': module_org.id, 'new-name': new_name})


@pytest.mark.tier2
def test_positive_create_user_with_timezone(module_org):
    """Create and remove user with valid timezone in an organization

    :id: b9b92c00-ee99-4da2-84c5-0a576a862100

    :customerscenario: true

    :BZ: 1733269

    :CaseLevel: Integration

    :CaseImportance: High

    :steps:
        1. Add user from organization with valid timezone
        2. Validate user's timezone
        3. Remove user from organization and validate

    :expectedresults: User created and removed successfully with valid timezone

    """
    users_timezones = [
        'Pacific Time (US & Canada)',
        'International Date Line West',
        'American Samoa',
        'Tokyo',
        'Samoa',
    ]
    for timezone in users_timezones:
        user = make_user({'timezone': timezone, 'admin': '1'})
        Org.add_user({'name': module_org.name, 'user': user['login']})

        org_info = Org.info({'name': module_org.name})
        assert user['login'] in org_info['users']
        assert user['timezone'] == timezone
        Org.remove_user({'id': module_org.id, 'user-id': user['id']})
        org_info = Org.info({'name': module_org.name})
        assert user['login'] not in org_info['users']
