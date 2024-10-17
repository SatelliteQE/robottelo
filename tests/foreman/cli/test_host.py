"""CLI tests for ``hammer host``.

:Requirement: Host

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Endeavour

:CaseImportance: High

"""

from random import choice
import re

from fauxfactory import gen_choice, gen_integer, gen_ipaddr, gen_mac, gen_string
import pytest
from wait_for import TimedOutError, wait_for
import yaml

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_SUBSCRIPTION_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_7_CUSTOM_PACKAGE,
    FAKE_8_CUSTOM_PACKAGE,
    FAKE_8_CUSTOM_PACKAGE_NAME,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.logging import logger
from robottelo.utils.datafactory import (
    invalid_values_list,
    valid_data_list,
    valid_hosts_list,
)


@pytest.fixture(scope="module")
def module_default_proxy(module_target_sat):
    """Use the default installation smart proxy"""
    return module_target_sat.cli.Proxy.list({'search': f'url = {module_target_sat.url}:9090'})[0]


@pytest.fixture
def function_host(target_sat):
    host_template = target_sat.api.Host()
    host_template.create_missing()
    # using CLI to create host
    host = target_sat.cli_factory.make_host(
        {
            'architecture-id': host_template.architecture.id,
            'domain-id': host_template.domain.id,
            'location-id': host_template.location.id,
            'mac': host_template.mac,
            'medium-id': host_template.medium.id,
            'name': host_template.name,
            'operatingsystem-id': host_template.operatingsystem.id,
            'organization-id': host_template.organization.id,
            'partition-table-id': host_template.ptable.id,
            'root-password': host_template.root_pass,
        }
    )
    yield host
    target_sat.cli.Host.delete({'id': host['id']})


@pytest.fixture
def function_user(target_sat, function_host):
    """
    Returns dict with user object and with password to this user
    """
    user_name = gen_string('alphanumeric')
    user_password = gen_string('alphanumeric')
    org = target_sat.api.Organization().search(
        query={'search': f'name="{function_host["organization"]["name"]}"'}
    )[0]
    location = target_sat.api.Location().search(
        query={'search': f'name="{function_host["location"]["name"]}"'}
    )[0]
    user = target_sat.api.User(
        admin=False,
        default_organization=org.id,
        organization=[org.id],
        default_location=location.id,
        location=[location.id],
        login=user_name,
        password=user_password,
    ).create()
    yield {'user': user, 'password': user_password}
    user.delete()


@pytest.fixture
def tracer_host(katello_host_tools_tracer_host):
    # create a custom, rhel version-specific mock-service repo
    rhelver = katello_host_tools_tracer_host.os_version.major
    katello_host_tools_tracer_host.create_custom_repos(
        **{f'mock_service_rhel{rhelver}': settings.repos['MOCK_SERVICE_REPO'][f'rhel{rhelver}']}
    )
    katello_host_tools_tracer_host.execute(f'yum -y install {settings.repos["MOCK_SERVICE_RPM"]}')
    assert (
        katello_host_tools_tracer_host.execute(
            f'rpm -q {settings.repos["MOCK_SERVICE_RPM"]}'
        ).status
        == 0
    )
    katello_host_tools_tracer_host.execute(f'systemctl start {settings.repos["MOCK_SERVICE_RPM"]}')

    return katello_host_tools_tracer_host


def update_smart_proxy(sat, location, smart_proxy):
    if location.id not in [location.id for location in smart_proxy.location]:
        smart_proxy.location.append(sat.api.Location(id=location.id))
    smart_proxy.update(['location'])


# -------------------------- HELP SCENARIOS --------------------------
def parse_two_columns(content, options_start_with_dash=False):
    """
    Parse part of the help message which consist from two columns,
    for example Options or Search / Order fields

    Example:
    >>> content = ['activation_key                  string']
    >>> parse_two_columns(content)
    >>> {'activation_key': 'string'}

    or:
    >>> content =  [
    >>> ' --thin THIN                                   Only list thin and name of hosts',
    >>> '                                               One of true/false, yes/no, 1/0.'
    >>> ]
    >>> parse_two_columns(content, True)
    >>> {'--thin THIN': ' Only list thin and name of hosts One of true/false, yes/no, 1/0.'}


    :param content: list of strings, item is equal to line in help message
    :param options_start_with_dash: when line is starting with dash and line has only one column
    and previous_line is not None, then line value is appended to the previous line
    :return: options dictionary
    """
    options = {}
    previous_line = None
    for line in content:
        # strip whitespaces and split for 2 or more whitespaces
        line_lst = list(filter(None, line.strip().split('  ')))
        if not line_lst:  # skip empty lines
            continue
        if len(line_lst) > 2:
            raise ValueError(
                'line is expected to have maximum of 2 fields, parameter and explanation, '
                f'but has {len(line_lst), line_lst}'
            )
        # if line has len 1, append the value as an empty string
        try:
            if options_start_with_dash and line_lst[0].startswith('-'):
                options[line_lst[0]] = line_lst[1]
                previous_line = line_lst[0]
            else:
                options[line_lst[0]] = line_lst[1]
        except IndexError:
            if options_start_with_dash and previous_line is not None:
                # append message to previous line value
                options[previous_line] = options[previous_line] + ' ' + line_lst[0]
            else:
                options[line_lst[0]] = ''
    return options


def parse_field_sets_table(content):
    """
    Return all fields name in lower case, from Predefined field sets category in help message

    :param content: list of strings, item is equal to line in help message
    :return: list of options

    Example:
    >>> content = [
    >>>  '-----------------------|-----|---------|-----',
    >>>  'FIELDS                 | ALL | DEFAULT | THIN',
    >>>  '-----------------------|-----|---------|-----',
    >>>  'Id                     | x   | x       | x',
    >>>  'Operating System       | x   | x       | x',
    >>> ]
    >>> parse_field_sets_table(content)
    >>> ['id', 'operating-system']
    """
    options = []
    for line in content:
        line = line.strip()
        if line.startswith('-'):  # skip over table lines
            continue

        # split table columns
        line_lst = line.split('|')
        # skip header
        if line_lst[0].isupper():
            continue
        options.append(line_lst[0].strip())
    return options


def parse_cli_entity_list_help_message(help_message):
    """
    Parse cli help message for entitiy list,
    for now, only Search / Order fields: are parsed,
    can be extended so all parts are parsed

    example: hammer host list --help

    :param help_message: string
    :return: dictionary with parsed csv
    """
    # the beginning of the yaml output is removed along
    # with the double quotes at the beginning and end
    categories = help_message.split('\n\n')
    parsed_dict = {}
    for category in categories:
        name, *content = category.split('\n')
        # special characters removed
        name = re.sub('\\[[0-9]m', '', name)[1:-1]
        name = name[:-1]  # remove colon from name
        if 'Usage' in name:
            continue
        if 'Options' in name:
            # used together with previous_line when line (message) is appended to previous line
            options = parse_two_columns(content, options_start_with_dash=True)
        elif 'field sets' in name:
            options = parse_field_sets_table(content)
        else:
            options = parse_two_columns(content)

        parsed_dict[name] = options
    return parsed_dict


def test_positive_search_all_field_sets(module_target_sat):
    """All fields in predefined field sets from hammer host list --help message are shown
    when specified as --fields in hammer host list command
    Note: host was created, so we there will always be at least 1 host
    and will be always created with same approach

    :id: 307585ce-d4f3-11eb-8949-98fa9b6ecd5a

    :steps:
        1. create fake host
        2. parse hammer host list --help message, obtain all fields from predefined field sets
        3. hammer list --fields=all fields
        4. identify the host that was created from the list
        5. verify that the host contains all the fields


    :expectedresults: all fields are shown in hammer list --fields

    :BZ: 1913311

    :customerscenario: true
    """
    new_host = module_target_sat.cli_factory.make_fake_host()
    host_help_yaml = module_target_sat.cli.Host.list(options={'help': ''}, output_format='yaml')
    host_help = yaml.load(host_help_yaml, yaml.SafeLoader)
    parsed_dict = parse_cli_entity_list_help_message(host_help[':message'])
    help_field_sets = parsed_dict['Predefined field sets']
    output_field_sets = module_target_sat.cli.Host.list(
        options={'fields': ','.join(help_field_sets)}
    )

    # get list index of the created host in the output_field_sets
    [host_idx] = [idx for idx, host in enumerate(output_field_sets) if new_host['id'] == host['id']]

    help_field_sets = [field.lower().replace(' ', '-') for field in help_field_sets]
    ignore_fields = ['trace-status']
    for field in help_field_sets:
        if field in ignore_fields:
            continue
        assert field in list(output_field_sets[host_idx].keys())


@pytest.mark.rhel_ver_match('8')
@pytest.mark.cli_host_subscription
@pytest.mark.tier3
def test_positive_host_list_with_cv_and_lce(
    target_sat,
    rhel_contenthost,
    function_ak_with_cv,
    function_promoted_cv,
    function_org,
    function_lce,
):
    """The output from hammer host list correctly includes both Content View and
    Lifecycle Environment fields. Specifying these fields explicitly in the command
    also yields the correct output.

    :id: 3ece2a52-0b91-453e-a4ea-c0376d79fd2d

    :steps:
        1. Register a Host
        2. Run the hammer host list command
        3. Verify information is correct and that both CV and LCE are in the output
        4. Run the hammer list command with CV and LCE fields specified
        5. Verify information is correct and that both CV and LCE are in the output

    :expectedresults: Both cases should return CV and LCE in the output

    :Verifies: SAT-23576, SAT-22677

    :customerscenario: true
    """
    # register client
    result = rhel_contenthost.register(function_org, None, function_ak_with_cv.name, target_sat)
    assert result.status == 0
    assert rhel_contenthost.subscribed
    # list host command without specifying cv or lce
    host_list = target_sat.cli.Host.list(output_format='json')
    host = next(i for i in host_list if i['name'] == rhel_contenthost.hostname)
    assert host['content-view'] == function_promoted_cv.name
    assert host['lifecycle-environment'] == function_lce.name
    # list host command with specifying cv and lce
    host_list_fields = target_sat.cli.Host.list(
        options={'fields': ['Name', 'Content view', 'Lifecycle environment']}, output_format='json'
    )
    host = next(i for i in host_list_fields if i['name'] == rhel_contenthost.hostname)
    assert host['content-view'] == function_promoted_cv.name
    assert host['lifecycle-environment'] == function_lce.name


# -------------------------- CREATE SCENARIOS -------------------------
@pytest.mark.e2e
@pytest.mark.cli_host_create
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_and_delete(target_sat, module_lce_library, module_published_cv):
    """A host can be created and deleted

    :id: 59fcbe50-9c6b-4c3c-87b3-272b4b584fb3

    :expectedresults: A host is created and deleted

    :BZ: 1260697, 1313056, 1361309

    :CaseImportance: Critical
    """
    name = valid_hosts_list()[0]
    host = target_sat.api.Host()
    host.create_missing()
    interface = (
        'type=interface,mac={},identifier=eth0,name={},domain_id={},'
        'ip={},primary=true,provision=true'
    ).format(host.mac, gen_string('alpha'), host.domain.id, gen_ipaddr())
    new_host = target_sat.cli_factory.make_host(
        {
            'architecture-id': host.architecture.id,
            'content-view-id': module_published_cv.id,
            'domain-id': host.domain.id,
            'interface': interface,
            'lifecycle-environment-id': module_lce_library.id,
            'location-id': host.location.id,
            'mac': host.mac,
            'medium-id': host.medium.id,
            'name': name,
            'operatingsystem-id': host.operatingsystem.id,
            'organization-id': host.organization.id,
            'partition-table-id': host.ptable.id,
            'root-password': host.root_pass,
        }
    )
    assert f'{name}.{host.domain.read().name}' == new_host['name']
    assert new_host['organization'] == host.organization.name
    assert new_host['content-information']['content-view']['name'] == module_published_cv.name
    assert (
        new_host['content-information']['lifecycle-environment']['name'] == module_lce_library.name
    )
    host_interface = target_sat.cli.HostInterface.info(
        {'host-id': new_host['id'], 'id': new_host['network-interfaces'][0]['id']}
    )
    assert host_interface['domain'] == host.domain.read().name

    target_sat.cli.Host.delete({'id': new_host['id']})
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Host.info({'id': new_host['id']})


@pytest.mark.e2e
@pytest.mark.cli_host_create
@pytest.mark.tier1
def test_positive_crud_interface_by_id(target_sat, default_location, default_org):
    """New network interface can be added to existing host, listed and removed.

    :id: e97dba92-61eb-47ad-a7d7-5f989292b12a

    :expectedresults: Interface added to host correctly and has proper
        domain and mac address

    :CaseImportance: Critical
    """
    domain = target_sat.api.Domain(location=[default_location], organization=[default_org]).create()

    mac = gen_mac(multicast=False)
    host = target_sat.cli_factory.make_fake_host({'domain-id': domain.id})
    number_of_interfaces = len(target_sat.cli.HostInterface.list({'host-id': host['id']}))

    target_sat.cli.HostInterface.create(
        {'host-id': host['id'], 'domain-id': domain.id, 'mac': mac, 'type': 'interface'}
    )
    host = target_sat.cli.Host.info({'id': host['id']})
    host_interface = target_sat.cli.HostInterface.info(
        {
            'host-id': host['id'],
            'id': [ni for ni in host['network-interfaces'].values() if ni['mac-address'] == mac][0][
                'id'
            ],
        }
    )
    assert host_interface['domain'] == domain.name
    assert host_interface['mac-address'] == mac
    assert (
        len(target_sat.cli.HostInterface.list({'host-id': host['id']})) == number_of_interfaces + 1
    )

    new_domain = target_sat.api.Domain(
        location=[default_location], organization=[default_org]
    ).create()
    new_mac = gen_mac(multicast=False)
    target_sat.cli.HostInterface.update(
        {
            'host-id': host['id'],
            'id': host_interface['id'],
            'domain-id': new_domain.id,
            'mac': new_mac,
        }
    )
    host_interface = target_sat.cli.HostInterface.info(
        {
            'host-id': host['id'],
            'id': [ni for ni in host['network-interfaces'].values() if ni['mac-address'] == mac][0][
                'id'
            ],
        }
    )
    assert host_interface['domain'] == new_domain.name
    assert host_interface['mac-address'] == new_mac

    target_sat.cli.HostInterface.delete({'host-id': host['id'], 'id': host_interface['id']})
    assert len(target_sat.cli.HostInterface.list({'host-id': host['id']})) == number_of_interfaces
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.HostInterface.info({'host-id': host['id'], 'id': host_interface['id']})


@pytest.mark.cli_host_create
@pytest.mark.tier2
def test_negative_create_with_content_source(
    module_lce_library, module_org, module_published_cv, module_target_sat
):
    """Attempt to create a host with invalid content source specified

    :id: d92d6aff-4ad3-467c-88a8-5a5e56614f58

    :BZ: 1260697

    :expectedresults: Host was not created

    :CaseImportance: Medium
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.make_fake_host(
            {
                'content-source-id': gen_integer(10000, 99999),
                'content-view-id': module_published_cv.id,
                'lifecycle-environment-id': module_lce_library.id,
                'organization': module_org.name,
            }
        )


@pytest.mark.cli_host_create
@pytest.mark.tier2
def test_negative_update_content_source(
    module_default_proxy, module_lce_library, module_org, module_published_cv, module_target_sat
):
    """Attempt to update host's content source with invalid value

    :id: 03243c56-3835-4b15-94df-15d436bbda87

    :BZ: 1260697, 1483252, 1313056

    :customerscenario: true

    :expectedresults: Host was not updated. Content source remains the same
        as it was before update

    :CaseImportance: Medium
    """
    host = module_target_sat.cli_factory.make_fake_host(
        {
            'content-source-id': module_default_proxy['id'],
            'content-view-id': module_published_cv.id,
            'lifecycle-environment-id': module_lce_library.id,
            'organization': module_org.name,
        }
    )
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Host.update(
            {'id': host['id'], 'content-source-id': gen_integer(10000, 99999)}
        )
    host = module_target_sat.cli.Host.info({'id': host['id']})
    assert host['content-information']['content-source']['name'] == module_default_proxy['name']


@pytest.mark.cli_host_create
@pytest.mark.tier1
def test_positive_create_with_lce_and_cv(
    module_lce, module_org, module_promoted_cv, module_target_sat
):
    """Check if host can be created with new lifecycle and
        new content view

    :id: c2075131-6b25-4af3-b1e9-a7a9190dd6f8

    :expectedresults: Host is created using new lifecycle and
        new content view

    :BZ: 1313056

    :CaseImportance: Critical
    """
    new_host = module_target_sat.cli_factory.make_fake_host(
        {
            'content-view-id': module_promoted_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'organization-id': module_org.id,
        }
    )
    assert new_host['content-information']['lifecycle-environment']['name'] == module_lce.name
    assert new_host['content-information']['content-view']['name'] == module_promoted_cv.name


@pytest.mark.cli_host_create
@pytest.mark.tier2
def test_positive_create_with_openscap_proxy_id(
    module_default_proxy, module_org, module_target_sat
):
    """Check if host can be created with OpenSCAP Proxy id

    :id: 3774ba08-3b18-4e64-b07f-53f6aa0504f3

    :expectedresults: Host is created and has OpenSCAP Proxy assigned

    :CaseImportance: Medium
    """
    host = module_target_sat.cli_factory.make_fake_host(
        {'organization-id': module_org.id, 'openscap-proxy-id': module_default_proxy['id']}
    )
    assert host['openscap-proxy'] == module_default_proxy['id']


@pytest.mark.cli_host_create
@pytest.mark.tier1
def test_negative_create_with_name(
    module_lce_library, module_org, module_published_cv, module_target_sat
):
    """Check if host can be created with random long names

    :id: f92b6070-b2d1-4e3e-975c-39f1b1096697

    :expectedresults: Host is not created

    :CaseImportance: Critical
    """
    name = gen_choice(invalid_values_list())
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.make_fake_host(
            {
                'name': name,
                'organization-id': module_org.id,
                'content-view-id': module_published_cv.id,
                'lifecycle-environment-id': module_lce_library.id,
            }
        )


@pytest.mark.cli_host_create
@pytest.mark.tier1
def test_negative_create_with_unpublished_cv(module_lce, module_org, module_cv, module_target_sat):
    """Check if host can be created using unpublished cv

    :id: 9997383d-3c27-4f14-94f9-4b8b51180eb6

    :expectedresults: Host is not created using new unpublished cv

    :CaseImportance: Critical
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.make_fake_host(
            {
                'content-view-id': module_cv.id,
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )


@pytest.mark.cli_host_create
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_katello_and_openscap_loaded(target_sat):
    """Verify that command line arguments from both Katello
    and foreman_openscap plugins are loaded and available
    at the same time

    :id: 5b5db1d4-50f9-45a0-bb92-4571fc8d729b

    :expectedresults: Command line arguments from both Katello
        and foreman_openscap are available in help message
        (note: help is generated dynamically based on apipie cache)

    :customerscenario: true

    :CaseImportance: Medium

    :BZ: 1671148
    """
    help_output = target_sat.cli.Host.execute('host update --help')
    for arg in ['lifecycle-environment[-id]', 'openscap-proxy-id']:
        assert any(
            f'--{arg}' in line for line in help_output.split('\n')
        ), f'--{arg} not supported by update subcommand'


@pytest.mark.cli_host_create
@pytest.mark.tier3
def test_positive_list_and_unregister(
    module_ak_with_cv, module_lce, module_org, rhel7_contenthost, target_sat
):
    """List registered host for a given org and unregister the host

    :id: b9c056cd-11ca-4870-bac4-0ebc4a782cb0

    :expectedresults: Host is listed for the given org and host is successfully unregistered.
        Unlike content host, host has not disappeared from list of hosts after unregistering.

    :parametrized: yes
    """
    result = rhel7_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
    assert result.status == 0
    assert rhel7_contenthost.subscribed
    hosts = target_sat.cli.Host.list({'organization-id': module_org.id})
    assert rhel7_contenthost.hostname in [host['name'] for host in hosts]
    result = rhel7_contenthost.unregister()
    assert result.status == 0
    hosts = target_sat.cli.Host.list({'organization-id': module_org.id})
    assert rhel7_contenthost.hostname in [host['name'] for host in hosts]


@pytest.mark.cli_host_create
@pytest.mark.tier3
def test_positive_list_by_last_checkin(
    module_org, rhel7_contenthost, target_sat, module_ak_with_cv
):
    """List all content hosts using last checkin criteria

    :id: e7d86b44-28c3-4525-afac-61a20e62daf8

    :customerscenario: true

    :expectedresults: Hosts are listed for the given time period

    :BZ: 1285992

    :parametrized: yes
    """
    result = rhel7_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    assert rhel7_contenthost.subscribed
    hosts = target_sat.cli.Host.list(
        {'search': 'last_checkin = "Today" or last_checkin = "Yesterday"'}
    )
    assert len(hosts) >= 1
    assert rhel7_contenthost.hostname in [host['name'] for host in hosts]


@pytest.mark.cli_host_create
@pytest.mark.tier3
def test_positive_list_infrastructure_hosts(
    module_org, rhel7_contenthost, target_sat, module_ak_with_cv
):
    """List infrasturcture hosts (Satellite and Capsule)

    :id: 9e4c873e-0954-4096-b337-bcd679181025

    :expectedresults: Infrastructure hosts are listed

    :parametrized: yes
    """
    result = rhel7_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
    assert result.status == 0
    assert rhel7_contenthost.subscribed
    target_sat.cli.Host.update({'name': target_sat.hostname, 'new-organization-id': module_org.id})
    # list satellite hosts
    hosts = target_sat.cli.Host.list({'search': 'infrastructure_facet.foreman=true'})
    assert len(hosts) == 2
    hostnames = [host['name'] for host in hosts]
    assert rhel7_contenthost.hostname not in hostnames
    assert target_sat.hostname in hostnames
    # list capsule hosts
    hosts = target_sat.cli.Host.list({'search': 'infrastructure_facet.smart_proxy_id=1'})
    hostnames = [host['name'] for host in hosts]
    assert len(hosts) == 2
    assert rhel7_contenthost.hostname not in hostnames
    assert target_sat.hostname in hostnames


@pytest.mark.cli_host_create
@pytest.mark.tier2
def test_positive_create_inherit_lce_cv(
    target_sat, module_published_cv, module_lce_library, module_org
):
    """Create a host with hostgroup specified. Make sure host inherited
    hostgroup's lifecycle environment and content-view

    :id: ba73b8c8-3ce1-4fa8-a33b-89ded9ffef47

    :expectedresults: Host's lifecycle environment and content view match
        the ones specified in hostgroup

    :BZ: 1391656
    """
    hostgroup = target_sat.api.HostGroup(
        content_view=module_published_cv,
        lifecycle_environment=module_lce_library,
        organization=[module_org],
    ).create()
    host = target_sat.cli_factory.make_fake_host(
        {'hostgroup-id': hostgroup.id, 'organization-id': module_org.id}
    )
    assert (
        int(host['content-information']['lifecycle-environment']['id'])
        == hostgroup.lifecycle_environment.id
    )
    assert int(host['content-information']['content-view']['id']) == hostgroup.content_view.id


@pytest.mark.cli_host_create
@pytest.mark.tier3
def test_positive_create_inherit_nested_hostgroup(target_sat):
    """Create two nested host groups with the same name, but different
    parents. Then create host using any from these hostgroups title

    :id: 7bc95130-3f20-493d-b54c-04c444d97563

    :expectedresults: Host created successfully using host group title

    :customerscenario: true

    :BZ: 1436162
    """
    options = target_sat.api.Host()
    options.create_missing()
    lce = target_sat.api.LifecycleEnvironment(organization=options.organization).create()
    content_view = target_sat.api.ContentView(organization=options.organization).create()
    content_view.publish()
    content_view.read().version[0].promote(data={'environment_ids': lce.id, 'force': False})
    host_name = gen_string('alpha').lower()
    nested_hg_name = gen_string('alpha')
    parent_hostgroups = []
    nested_hostgroups = []
    for _ in range(2):
        parent_hg_name = gen_string('alpha')
        parent_hg = target_sat.api.HostGroup(
            name=parent_hg_name, organization=[options.organization]
        ).create()
        parent_hostgroups.append(parent_hg)
        nested_hg = target_sat.api.HostGroup(
            architecture=options.architecture,
            content_view=content_view,
            domain=options.domain,
            lifecycle_environment=lce,
            location=[options.location],
            medium=options.medium,
            name=nested_hg_name,
            operatingsystem=options.operatingsystem,
            organization=[options.organization],
            parent=parent_hg,
            ptable=options.ptable,
        ).create()
        nested_hostgroups.append(nested_hg)

    host = target_sat.cli_factory.make_host(
        {
            'hostgroup-title': f'{parent_hostgroups[0].name}/{nested_hostgroups[0].name}',
            'location-id': options.location.id,
            'organization-id': options.organization.id,
            'name': host_name,
        }
    )
    assert f'{host_name}.{options.domain.read().name}' == host['name']


@pytest.mark.cli_host_create
@pytest.mark.tier3
def test_positive_list_with_nested_hostgroup(target_sat):
    """Create parent and nested host groups. Then create host using nested
    hostgroup and then find created host using list command

    :id: 50c964c3-d3d6-4832-a51c-62664d132229

    :customerscenario: true

    :expectedresults: Host is successfully listed and has both parent and
        nested host groups names in its hostgroup parameter

    :BZ: 1427554, 1955421
    """
    options = target_sat.api.Host()
    options.create_missing()
    host_name = gen_string('alpha').lower()
    parent_hg_name = gen_string('alpha')
    nested_hg_name = gen_string('alpha')
    lce = target_sat.api.LifecycleEnvironment(organization=options.organization).create()
    content_view = target_sat.api.ContentView(organization=options.organization).create()
    content_view.publish()
    content_view.read().version[0].promote(data={'environment_ids': lce.id, 'force': False})
    parent_hg = target_sat.api.HostGroup(
        name=parent_hg_name,
        organization=[options.organization],
        content_view=content_view,
        ptable=options.ptable,
    ).create()
    nested_hg = target_sat.api.HostGroup(
        architecture=options.architecture,
        domain=options.domain,
        lifecycle_environment=lce,
        location=[options.location],
        medium=options.medium,
        name=nested_hg_name,
        operatingsystem=options.operatingsystem,
        organization=[options.organization],
        parent=parent_hg,
    ).create()
    target_sat.cli_factory.make_host(
        {
            'hostgroup-id': nested_hg.id,
            'location-id': options.location.id,
            'organization-id': options.organization.id,
            'name': host_name,
        }
    )
    hosts = target_sat.cli.Host.list({'organization-id': options.organization.id})
    assert f'{parent_hg_name}/{nested_hg_name}' == hosts[0]['host-group']
    host = target_sat.cli.Host.info({'id': hosts[0]['id']})
    logger.info(f'Host info: {host}')
    assert host['operating-system']['medium'] == options.medium.name
    assert host['operating-system']['partition-table'] == options.ptable.name  # inherited
    if not target_sat.is_stream:
        assert 'id' in host['content-information']['lifecycle-environment']
        assert int(host['content-information']['lifecycle-environment']['id']) == int(lce.id)
        assert int(host['content-information']['content-view']['id']) == int(
            content_view.id
        )  # inherited


@pytest.mark.cli_host_create
@pytest.mark.stubbed
@pytest.mark.tier3
def test_negative_create_with_incompatible_pxe_loader():
    """Try to create host with a known OS and incompatible PXE loader

    :id: 75d7ab06-2d23-4f85-a080-faadfe2b294a

    :setup:
      1. Synchronize RHEL[5,6,7] kickstart repos


    :steps:
      1. create a new RHEL host using 'BareMetal' option and the following
         OS-PXE_loader combinations:

         a RHEL5,6 - GRUB2_UEFI
         b RHEL5,6 - GRUB2_UEFI_SB
         c RHEL7 - GRUB_UEFI
         d RHEL7 - GRUB_UEFI_SB

    :expectedresults:
      1. Warning message appears
      2. Files not deployed on TFTP
      3. Host not created

    :CaseAutomation: NotAutomated
    """


# -------------------------- UPDATE SCENARIOS -------------------------
@pytest.mark.e2e
@pytest.mark.cli_host_update
@pytest.mark.tier1
def test_positive_update_parameters_by_name(
    target_sat, function_host, module_architecture, module_location
):
    """A host can be updated with a new name, mac address, domain,
        location, environment, architecture, operating system and medium.
        Use id to access the host

    :id: 3a4c0b5a-5d87-477a-b80a-9af0ec3b4b6f

    :expectedresults: A host is updated and the name, mac address, domain,
        location, environment, architecture, operating system and medium
        matches

    :BZ: 1343392, 1679300

    :customerscenario: true

    :CaseImportance: Critical
    """
    new_name = valid_hosts_list()[0]
    new_mac = gen_mac(multicast=False)
    new_loc = module_location
    organization = target_sat.api.Organization().search(
        query={'search': f'name="{function_host["organization"]["name"]}"'}
    )[0]
    new_domain = target_sat.api.Domain(location=[new_loc], organization=[organization]).create()
    p_table_name = function_host['operating-system']['partition-table']['name']
    p_table = target_sat.api.PartitionTable().search(query={'search': f'name="{p_table_name}"'})
    new_os = target_sat.api.OperatingSystem(
        major=gen_integer(0, 10),
        minor=gen_integer(0, 10),
        name=gen_string('alphanumeric'),
        architecture=[module_architecture.id],
        ptable=[p_table[0].id],
    ).create()
    new_medium = target_sat.api.Media(
        location=[new_loc],
        organization=[organization],
        operatingsystem=[new_os],
    ).create()
    target_sat.cli.Host.update(
        {
            'architecture': module_architecture.name,
            'domain': new_domain.name,
            'name': function_host['name'],
            'mac': new_mac,
            'medium-id': new_medium.id,
            'new-name': new_name,
            'operatingsystem': new_os.title,
            'new-location-id': new_loc.id,
        }
    )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert '{}.{}'.format(new_name, host['network']['domain']['name']) == host['name']
    assert host['location']['name'] == new_loc.name
    assert host['network']['mac'] == new_mac
    assert host['network']['domain']['name'] == new_domain.name
    assert host['operating-system']['architecture']['name'] == module_architecture.name
    assert host['operating-system']['operating-system']['name'] == new_os.title
    assert host['operating-system']['medium']['name'] == new_medium.name


@pytest.mark.tier1
@pytest.mark.cli_host_update
def test_negative_update_name(function_host, target_sat):
    """A host can not be updated with invalid or empty name

    :id: e8068d2a-6a51-4627-908b-60a516c67032

    :expectedresults: A host is not updated

    :CaseImportance: Critical
    """
    new_name = gen_choice(invalid_values_list())
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Host.update({'id': function_host['id'], 'new-name': new_name})
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert '{}.{}'.format(new_name, host['network']['domain']).lower() != host['name']


@pytest.mark.tier1
@pytest.mark.cli_host_update
def test_negative_update_mac(function_host, target_sat):
    """A host can not be updated with invalid or empty MAC address

    :id: 2f03032d-789d-419f-9ff2-a6f3561444da

    :expectedresults: A host is not updated

    :CaseImportance: Critical
    """
    new_mac = gen_choice(invalid_values_list())
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Host.update({'id': function_host['id'], 'mac': new_mac})
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert host['network']['mac'] != new_mac


@pytest.mark.tier2
@pytest.mark.cli_host_update
def test_negative_update_arch(function_host, module_architecture, target_sat):
    """A host can not be updated with a architecture, which does not
    belong to host's operating system

    :id: a86524da-8caf-472b-9a3d-17a4385c3a18

    :expectedresults: A host is not updated
    """
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Host.update(
            {'architecture': module_architecture.name, 'id': function_host['id']}
        )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert host['operating-system']['architecture'] != module_architecture.name


@pytest.mark.tier2
@pytest.mark.cli_host_update
def test_negative_update_os(target_sat, function_host, module_architecture):
    """A host can not be updated with a operating system, which is
    not associated with host's medium

    :id: ff13d2af-e54a-4daf-a24d-7ec930b4fbbe

    :expectedresults: A host is not updated
    """
    p_table_name = function_host['operating-system']['partition-table']['name']
    p_table = target_sat.api.PartitionTable().search(query={'search': f'name="{p_table_name}"'})[0]
    new_os = target_sat.api.OperatingSystem(
        major=gen_integer(0, 10),
        name=gen_string('alphanumeric'),
        architecture=[module_architecture.id],
        ptable=[p_table.id],
    ).create()
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Host.update(
            {
                'architecture': module_architecture.name,
                'id': function_host['id'],
                'operatingsystem': new_os.title,
            }
        )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert host['operating-system']['operating-system'] != new_os.title


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.cli_host_update
def test_hammer_host_info_output(target_sat, module_user):
    """Verify re-add of 'owner-id' in `hammer host info` output

    :id: 03468516-0ebb-11eb-8ad8-0c7a158cbff4

    :steps:
        1. Update the host with any owner
        2. Get host info by running `hammer host info`
        3. Create new user and update his location and organization based on the hosts
        4. Update the host with new owner
        5. Verify that the owner-id has changed

    :expectedresults: 'owner-id' should be in `hammer host info` output

    :customerscenario: true

    :BZ: 1779093, 1910314
    """
    user = target_sat.api.User().search(
        query={'search': f'login={settings.server.admin_username}'}
    )[0]
    target_sat.cli.Host.update(
        {'owner': settings.server.admin_username, 'owner-type': 'User', 'id': '1'}
    )
    result_info = target_sat.cli.Host.info(options={'id': '1', 'fields': 'Additional info'})
    assert int(result_info['additional-info']['owner-id']) == user.id
    host = target_sat.cli.Host.info({'id': '1'})
    target_sat.cli.User.update(
        {
            'id': module_user.id,
            'organizations': [host['organization']['name']],
            'locations': [host['location']['name']],
        }
    )
    target_sat.cli.Host.update({'owner-id': module_user.id, 'id': '1'})
    result_info = target_sat.cli.Host.info(options={'id': '1', 'fields': 'Additional info'})
    assert int(result_info['additional-info']['owner-id']) == module_user.id


@pytest.mark.cli_host_parameter
@pytest.mark.tier1
def test_positive_parameter_crud(function_host, target_sat):
    """Add, update and remove host parameter with valid name.

    :id: 76034424-cf18-4ced-916b-ee9798c311bc

    :expectedresults: Host parameter was successfully added, updated and
        removed.

    :CaseImportance: Critical
    """
    name = next(iter(valid_data_list()))
    value = valid_data_list()[name]
    target_sat.cli.Host.set_parameter(
        {'host-id': function_host['id'], 'name': name, 'value': value}
    )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert (name, value) in [(param['name'], param['value']) for param in host['parameters']]

    new_value = valid_data_list()[name]
    target_sat.cli.Host.set_parameter({'host-id': host['id'], 'name': name, 'value': new_value})
    host = target_sat.cli.Host.info({'id': host['id']})

    assert (name, new_value) in [(param['name'], param['value']) for param in host['parameters']]

    target_sat.cli.Host.delete_parameter({'host-id': host['id'], 'name': name})
    host = target_sat.cli.Host.info({'id': host['id']})
    assert name not in [param['name'] for param in host['parameters']]


# -------------------------- HOST PARAMETER SCENARIOS -------------------------
@pytest.mark.cli_host_parameter
@pytest.mark.tier1
def test_negative_add_parameter(function_host, target_sat):
    """Try to add host parameter with different invalid names.

    :id: 473f8c3f-b66e-4526-88af-e139cc3dabcb

    :expectedresults: Host parameter was not added.


    :CaseImportance: Critical
    """
    name = gen_choice(invalid_values_list()).lower()
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Host.set_parameter(
            {
                'host-id': function_host['id'],
                'name': name,
                'value': gen_string('alphanumeric'),
            }
        )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert name not in host['parameters']


@pytest.mark.cli_host_parameter
@pytest.mark.tier2
def test_negative_view_parameter_by_non_admin_user(target_sat, function_host, function_user):
    """Attempt to view parameters with non admin user without Parameter
     permissions

    :id: 65ba89f0-9bee-43d9-814b-9f5a194558f8

    :customerscenario: true

    :steps:
        1. As admin user create a host
        2. Set a host parameter name and value
        3. Create a non admin user with the following permissions:
            Host: [view_hosts],
            Organization: [view_organizations],
        4. Get the host info as the non admin user

    :expectedresults: The non admin user is not able to read the parameters

    :BZ: 1296662
    """
    param_name = gen_string('alpha').lower()
    param_value = gen_string('alphanumeric')
    target_sat.cli.Host.set_parameter(
        {'host-id': function_host['id'], 'name': param_name, 'value': param_value}
    )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert (param_name, param_value) in [
        (param['name'], param['value']) for param in host['parameters']
    ]
    role = target_sat.api.Role(name=gen_string('alphanumeric')).create()
    target_sat.cli_factory.add_role_permissions(
        role.id,
        resource_permissions={
            'Host': {'permissions': ['view_hosts']},
            'Organization': {'permissions': ['view_organizations']},
        },
    )
    target_sat.cli.User.add_role({'id': function_user['user'].id, 'role-id': role.id})
    host = target_sat.cli.Host.with_user(
        username=function_user['user'].login, password=function_user['password']
    ).info({'id': host['id']})
    assert not host.get('parameters')


@pytest.mark.cli_host_parameter
@pytest.mark.tier2
def test_positive_view_parameter_by_non_admin_user(target_sat, function_host, function_user):
    """Attempt to view parameters with non admin user that has
    Parameter::vew_params permission

    :id: 22d7d7cf-3d4f-4ae2-beaf-c11e41f2d439

    :customerscenario: true

    :steps:
        1. As admin user create a host
        2. Set a host parameter name and value
        3. Create a non admin user with the following permissions:
            Host: [view_hosts],
            Organization: [view_organizations],
            Parameter: [view_params]
        4. Get the host info as the non admin user

    :expectedresults: The non admin user is able to read the parameters

    :BZ: 1296662
    """
    param_name = gen_string('alpha').lower()
    param_value = gen_string('alphanumeric')
    target_sat.cli.Host.set_parameter(
        {'host-id': function_host['id'], 'name': param_name, 'value': param_value}
    )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert (param_name, param_value) in [
        (param['name'], param['value']) for param in host['parameters']
    ]
    role = target_sat.api.Role(name=gen_string('alphanumeric')).create()
    target_sat.cli_factory.add_role_permissions(
        role.id,
        resource_permissions={
            'Host': {'permissions': ['view_hosts']},
            'Organization': {'permissions': ['view_organizations']},
            'Parameter': {'permissions': ['view_params']},
        },
    )
    target_sat.cli.User.add_role({'id': function_user['user'].id, 'role-id': role.id})
    host = target_sat.cli.Host.with_user(
        username=function_user['user'].login, password=function_user['password']
    ).info({'id': host['id']})
    assert (param_name, param_value) in [
        (param['name'], param['value']) for param in host['parameters']
    ]


@pytest.mark.cli_host_parameter
@pytest.mark.tier2
def test_negative_edit_parameter_by_non_admin_user(target_sat, function_host, function_user):
    """Attempt to edit parameter with non admin user that has
    Parameter::vew_params permission

    :id: 2b40b3b9-42db-48c8-a9d7-7c308dc6add0

    :customerscenario: true

    :steps:
        1. As admin user create a host
        2. Set a host parameter name and value
        3. Create a non admin user with the following permissions:
            Host: [view_hosts],
            Organization: [view_organizations],
            Parameter: [view_params]
        4. Attempt to edit the parameter value as the non admin user

    :expectedresults: The non admin user is not able to edit the parameter

    :BZ: 1296662
    """
    param_name = gen_string('alpha').lower()
    param_value = gen_string('alphanumeric')
    target_sat.cli.Host.set_parameter(
        {'host-id': function_host['id'], 'name': param_name, 'value': param_value}
    )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert (param_name, param_value) in [
        (param['name'], param['value']) for param in host['parameters']
    ]
    role = target_sat.api.Role(name=gen_string('alphanumeric')).create()
    target_sat.cli_factory.add_role_permissions(
        role.id,
        resource_permissions={
            'Host': {'permissions': ['view_hosts']},
            'Organization': {'permissions': ['view_organizations']},
            'Parameter': {'permissions': ['view_params']},
        },
    )
    target_sat.cli.User.add_role({'id': function_user['user'].id, 'role-id': role.id})
    param_new_value = gen_string('alphanumeric')
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Host.with_user(
            username=function_user['user'].login, password=function_user['password']
        ).set_parameter(
            {'host-id': function_host['id'], 'name': param_name, 'value': param_new_value}
        )
    host = target_sat.cli.Host.info({'id': function_host['id']})
    assert (param_name, param_value) in [
        (param['name'], param['value']) for param in host['parameters']
    ]


@pytest.mark.cli_host_parameter
@pytest.mark.tier2
def test_positive_set_multi_line_and_with_spaces_parameter_value(function_host, target_sat):
    """Check that host parameter value with multi-line and spaces is
    correctly restored from yaml format

    :id: 776feffd-1b46-46e9-925d-4739194c15cc

    :customerscenario: true

    :expectedresults: host parameter value is the same when restored
        from yaml format

    :BZ: 1315282
    """
    param_name = gen_string('alpha').lower()
    # long string that should be escaped and affected by line break with
    # yaml dump by default
    param_value = (
        'auth                          include              '
        'password-auth\r\n'
        'account     include                  password-auth'
    )
    # count parameters of a host
    response = target_sat.cli.Host.info(
        {'id': function_host['id']}, output_format='yaml', return_raw_response=True
    )
    assert response.status == 0
    yaml_content = yaml.load(response.stdout, yaml.SafeLoader)
    host_initial_params = yaml_content.get('Parameters')
    # set parameter
    target_sat.cli.Host.set_parameter(
        {'host-id': function_host['id'], 'name': param_name, 'value': param_value}
    )
    response = target_sat.cli.Host.info(
        {'id': function_host['id']}, output_format='yaml', return_raw_response=True
    )
    assert response.status == 0
    yaml_content = yaml.load(response.stdout, yaml.SafeLoader)
    host_parameters = yaml_content.get('Parameters')
    # check that number of params increased by one
    assert len(host_parameters) == 1 + len(host_initial_params)
    filtered_params = [param for param in host_parameters if param['name'] == param_name]
    assert len(filtered_params) == 1
    assert filtered_params[0]['value'] == param_value


# -------------------------- HOST PROVISION SCENARIOS -------------------------
@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_provision_baremetal_with_bios_syslinux():
    """Provision RHEL system on a new BIOS BM Host with SYSLINUX loader
    from provided MAC address

    :id: 01509973-9f0b-4166-9fbd-59b753a7384b

    :setup:
      1. Create a PXE-based VM with BIOS boot mode (outside of
         Satellite).
      2. Synchronize a RHEL Kickstart repo

    :steps:
      1. create a new RHEL host using 'BareMetal' option,
         PXEGRUB loader and MAC address of the pre-created VM
      2. do the provisioning assertions (assertion steps #1-6)
      3. reboot the host

    :expectedresults:
      1. The loader files on TFTP are in the appropriate format and in the
         appropriate dirs.
      2. PXE handoff is successful (tcpdump shows the VM has requested
         the correct files)
      3. VM started to provision (might be tricky to automate console
         checks)
      4. VM accessible via SSH, shows correct OS version in
         ``/etc/*release``
      5. Host info command states 'built' in the status
      6. GRUB config changes the boot order (boot local first)
      7. Hosts boots straight to RHEL after reboot (step #4)

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_provision_baremetal_with_uefi_syslinux():
    """Provision RHEL system on a new UEFI BM Host with SYSLINUX loader
    from provided MAC address

    :id: a02e39a9-e04b-483f-8036-a5fe0348f615

    :setup:
      1. Create a PXE-based VM with UEFI boot mode (outside of
         Satellite).
      2. Synchronize a RHEL Kickstart repo

    :steps:
      1. create a new RHEL host using 'BareMetal' option,
         PXELINUX BIOS loader and MAC address of the pre-created VM
      2. do the provisioning assertions (assertion steps #1-6)
      3. reboot the host

    :expectedresults:
      1. The loader files on TFTP are in the appropriate format and in the
         appropriate dirs.
      2. PXE handoff is successful (tcpdump shows the VM has requested
         the correct files)
      3. VM started to provision (might be tricky to automate console
         checks)
      4. VM accessible via SSH, shows correct OS version in
         ``/etc/*release``
      5. Host info command states 'built' in the status
      6. GRUB config changes the boot order (boot local first)
      7. Hosts boots straight to RHEL after reboot (step #4)

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_provision_baremetal_with_uefi_grub():
    """Provision a RHEL system on a new UEFI BM Host with GRUB loader from
    a provided MAC address

    :id: 508b268b-244d-4bf0-a92a-fbee96e7e8ae

    :setup:
      1. Create a PXE-based VM with UEFI boot mode (outside of
         Satellite).
      2. Synchronize a RHEL6 Kickstart repo (el7 kernel is too new
         for GRUB v1)

    :steps:
      1. create a new RHEL6 host using 'BareMetal' option,
         PXEGRUB loader and MAC address of the pre-created VM
      2. reboot the VM (to ensure the NW boot is run)
      3. do the provisioning assertions (assertion steps #1-6)
      4. reboot the host

    :expectedresults:
      1. The loader files on TFTP are in the appropriate format and in the
         appropriate dirs.
      2. PXE handoff is successful (tcpdump shows the VM has requested
         the correct files)
      3. VM started to provision (might be tricky to automate console
         checks)
      4. VM accessible via SSH, shows correct OS version in
         ``/etc/*release``
      5. Host info command states 'built' in the status
      6. GRUB config changes the boot order (boot local first)
      7. Hosts boots straight to RHEL after reboot (step #4)


    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_provision_baremetal_with_uefi_grub2():
    """Provision a RHEL7+ system on a new UEFI BM Host with GRUB2 loader
    from a provided MAC address

    :id: b944c1b4-8612-4299-ac2e-9f77487ba669

    :setup:
      1. Create a PXE-based VM with UEFI boot mode (outside of
         Satellite).
      2. Synchronize a RHEL7+ Kickstart repo
         (el6 kernel is too old for GRUB2)

    :steps:
      1. create a new RHEL7+ host using 'BareMetal' option,
         PXEGRUB2 loader and MAC address of the pre-created VM
      2. reboot the VM (to ensure the NW boot is run)
      3. do the provisioning assertions (assertion steps #1-6)
      4. reboot the host


    :expectedresults:
      1. The loader files on TFTP are in the appropriate format and in the
         appropriate dirs.
      2. PXE handoff is successful (tcpdump shows the VM has requested
         the correct files)
      3. VM started to provision (might be tricky to automate console
         checks)
      4. VM accessible via SSH, shows correct OS version in
         ``/etc/*release``
      5. Host info command states 'built' in the status
      6. GRUB config changes the boot order (boot local first)
      7. Hosts boots straight to RHEL after reboot (step #4)


    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_provision_baremetal_with_uefi_secureboot():
    """Provision RHEL7+ on a new SecureBoot-enabled UEFI BM Host from
    provided MAC address

    :id: f5a0fe7b-0899-42df-81ad-be3143785303

    :setup:
      1. Create a PXE-based VM with UEFI boot mode from
         a secureboot image (outside of Satellite).
      2. Synchronize a RHEL7+ Kickstart repo
         (el6 kernel is too old for GRUB2)

    :steps:
      1. The loader files on TFTP are in the appropriate format and in the
         appropriate dirs.
      2. PXE handoff is successful (tcpdump shows the VM has requested
         the correct files)
      3. VM started to provision (might be tricky to automate console
         checks)
      4. VM accessible via SSH, shows correct OS version in
         ``/etc/*release``
      5. Host info command states 'built' in the status
      6. GRUB config changes the boot order (boot local first)
      7. Hosts boots straight to RHEL after reboot (step #4)

    :expectedresults: Host is provisioned

    :CaseAutomation: NotAutomated
    """


@pytest.fixture
def setup_custom_repo(target_sat, module_org, katello_host_tools_host, request):
    """Create custom repository content"""

    # get package details
    details = {}
    if katello_host_tools_host.os_version.major == 6:
        custom_repo = 'yum_6'
        details['package'] = FAKE_1_CUSTOM_PACKAGE
        details['new_package'] = FAKE_2_CUSTOM_PACKAGE
        details['package_name'] = FAKE_1_CUSTOM_PACKAGE_NAME
        details['errata'] = settings.repos.yum_6.errata[2]
        details['security_errata'] = settings.repos.yum_6.errata[2]
    else:
        custom_repo = 'yum_3'
        details['package'] = FAKE_7_CUSTOM_PACKAGE
        details['new_package'] = FAKE_8_CUSTOM_PACKAGE
        details['package_name'] = FAKE_8_CUSTOM_PACKAGE_NAME
        details['errata'] = settings.repos.yum_3.errata[0]
        details['security_errata'] = settings.repos.yum_3.errata[25]
    prod = target_sat.api.Product(
        organization=module_org, name=f'custom_{gen_string("alpha")}'
    ).create()
    custom_repo = target_sat.api.Repository(
        organization=module_org,
        product=prod,
        content_type='yum',
        url=settings.repos[custom_repo].url,
    ).create()
    custom_repo.sync()

    # make sure repo is enabled
    katello_host_tools_host.enable_repo(
        f'{module_org.name}_{prod.name}_{custom_repo.name}', force=True
    )
    # refresh repository metadata
    katello_host_tools_host.subscription_manager_list_repos()
    return details


@pytest.fixture
def yum_security_plugin(katello_host_tools_host):
    """Enable yum-security-plugin if the distro version requires it.
    Rhel6 yum version does not support updating of a specific advisory out of the box.
    It requires the security plugin to be installed first
    """
    if katello_host_tools_host.os_version.major < 7:
        katello_host_tools_host.create_custom_repos(
            os_repo=settings.repos[f'rhel{katello_host_tools_host.os_version.major}_os']
        )
        katello_host_tools_host.execute('yum makecache')
        yum_plugin_install = katello_host_tools_host.execute('yum -y install yum-plugin-security')
        assert yum_plugin_install.status == 0, "Failed to install yum-plugin-security plugin"


@pytest.mark.e2e
@pytest.mark.cli_katello_host_tools
@pytest.mark.rhel_ver_match('[^6].*')
@pytest.mark.tier3
def test_positive_report_package_installed_removed(
    katello_host_tools_host, setup_custom_repo, target_sat
):
    """Ensure installed/removed package is reported to satellite

    :id: fa5dc238-74c3-4c8a-aa6f-e0a91ba543e3

    :customerscenario: true

    :steps:
        1. register a host to activation key with content view that contain
           packages
        2. install a package 1 from the available packages
        3. list the host installed packages with search for package 1 name
        4. remove the package 1
        5. list the host installed packages with search for package 1 name

    :expectedresults:
        1. after step3: package 1 is listed in installed packages
        2. after step5: installed packages list is empty

    :BZ: 1463809

    :parametrized: yes
    """
    client = katello_host_tools_host
    host_info = target_sat.cli.Host.info({'name': client.hostname})
    client.run(f'yum install -y {setup_custom_repo["package"]}')
    result = client.run(f'rpm -q {setup_custom_repo["package"]}')
    assert result.status == 0
    installed_packages = target_sat.cli.Host.package_list(
        {'host-id': host_info['id'], 'search': f'name={setup_custom_repo["package_name"]}'}
    )
    assert len(installed_packages) == 1
    assert installed_packages[0]['nvra'] == setup_custom_repo["package"]
    result = client.run(f'yum remove -y {setup_custom_repo["package"]}')
    assert result.status == 0
    installed_packages = target_sat.cli.Host.package_list(
        {'host-id': host_info['id'], 'search': f'name={setup_custom_repo["package_name"]}'}
    )
    assert len(installed_packages) == 0


@pytest.mark.cli_katello_host_tools
@pytest.mark.rhel_ver_match('[^6].*')
@pytest.mark.tier3
def test_positive_package_applicability(katello_host_tools_host, setup_custom_repo, target_sat):
    """Ensure packages applicability is functioning properly

    :id: d283b65b-19c1-4eba-87ea-f929b0ee4116

    :customerscenario: true

    :steps:
        1. register a host to activation key with content view that contain
           a minimum of 2 packages, package 1 and package 2,
           where package 2 is an upgrade/update of package 1
        2. install the package 1
        3. list the host applicable packages for package 1 name
        4. install the package 2
        5. list the host applicable packages for package 1 name

    :expectedresults:
        1. after step 3: package 2 is listed in applicable packages
        2. after step 5: applicable packages list is empty

    :BZ: 1463809

    :parametrized: yes
    """
    client = katello_host_tools_host
    host_info = target_sat.cli.Host.info({'name': client.hostname})
    client.run(f'yum install -y {setup_custom_repo["package"]}')
    result = client.run(f'rpm -q {setup_custom_repo["package"]}')
    assert result.status == 0
    applicable_packages, _ = wait_for(
        lambda: target_sat.cli.Package.list(
            {
                'host-id': host_info['id'],
                'packages-restrict-applicable': 'true',
                'search': f'name={setup_custom_repo["package_name"]}',
            }
        ),
        fail_condition=[],
        timeout=120,
        delay=5,
    )
    assert any(
        setup_custom_repo["new_package"] in package['filename'] for package in applicable_packages
    )
    # install package update
    client.run(f'yum install -y {setup_custom_repo["new_package"]}')
    result = client.run(f'rpm -q {setup_custom_repo["new_package"]}')
    assert result.status == 0
    applicable_packages = target_sat.cli.Package.list(
        {
            'host-id': host_info['id'],
            'packages-restrict-applicable': 'true',
            'search': f'name={setup_custom_repo["package"]}',
        }
    )
    assert len(applicable_packages) == 0


@pytest.mark.e2e
@pytest.mark.cli_katello_host_tools
@pytest.mark.rhel_ver_match('[^6].*')
@pytest.mark.pit_client
@pytest.mark.pit_server
@pytest.mark.tier3
def test_positive_erratum_applicability(
    katello_host_tools_host, setup_custom_repo, yum_security_plugin, target_sat
):
    """Ensure erratum applicability is functioning properly

    :id: 139de508-916e-4c91-88ad-b4973a6fa104

    :steps:
        1. register a host to activation key with content view that contain
           a package with errata
        2. install the package
        3. list the host applicable errata
        4. install the errata
        5. list the host applicable errata

    :expectedresults:
        1. after step 3: errata of package is in applicable errata list
        2. after step 5: errata of package is not in applicable errata list

    :BZ: 1463809,1740790

    :parametrized: yes
    """
    client = katello_host_tools_host
    host_info = target_sat.cli.Host.info({'name': client.hostname})
    client.run(f'yum install -y {setup_custom_repo["package"]}')
    result = client.run(f'rpm -q {setup_custom_repo["package"]}')
    client.subscription_manager_list_repos()
    applicable_errata, _ = wait_for(
        lambda: target_sat.cli.Host.errata_list({'host-id': host_info['id']}),
        handle_exception=True,
        fail_condition=[],
        timeout=120,
        delay=5,
    )
    assert [
        erratum
        for erratum in applicable_errata
        if erratum['installable'] == 'true'
        and erratum['erratum-id'] == setup_custom_repo["security_errata"]
    ]
    # apply the erratum
    result = client.run(f'yum update -y --advisory {setup_custom_repo["security_errata"]}')
    assert result.status == 0
    client.subscription_manager_list_repos()
    # verify that the applied erratum is not present in the list of installable errata
    try:
        applicable_erratum, _ = wait_for(
            lambda: setup_custom_repo["security_errata"]
            not in [
                errata['erratum-id']
                for errata in target_sat.cli.Host.errata_list({'host-id': host_info['id']})
                if errata['installable'] == 'true'
            ],
            handle_exception=True,
            timeout=300,
            delay=5,
        )
    except TimedOutError as err:
        raise TimedOutError(
            f"Timed out waiting for erratum \"{setup_custom_repo['security_errata']}\""
            " to disappear from the list"
        ) from err


@pytest.mark.cli_katello_host_tools
@pytest.mark.rhel_ver_match('[^6].*')
@pytest.mark.tier3
def test_positive_apply_security_erratum(katello_host_tools_host, setup_custom_repo, target_sat):
    """Apply security erratum to a host

    :id: 4d1095c8-d354-42ac-af44-adf6dbb46deb

    :expectedresults: erratum is recognized by the
        `yum update --security` command on client

    :customerscenario: true

    :BZ: 1420671

    :parametrized: yes
    """
    client = katello_host_tools_host
    host_info = target_sat.cli.Host.info({'name': client.hostname})
    client.run(f'yum install -y {setup_custom_repo["new_package"]}')
    client.run(f'yum downgrade -y {setup_custom_repo["package_name"]}')
    # Check that host has applicable errata
    host_erratum, _ = wait_for(
        lambda: target_sat.cli.Host.errata_list({'host-id': host_info['id']})[0],
        handle_exception=True,
        timeout=120,
        delay=5,
    )
    assert host_erratum['erratum-id'] == setup_custom_repo["security_errata"]
    assert host_erratum['installable'] == 'true'
    # Check the erratum becomes available
    result = client.run('yum update --assumeno --security | grep "No packages needed for security"')
    assert result.status == 1


@pytest.mark.cli_katello_host_tools
@pytest.mark.tier3
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('[^6].*')
def test_positive_install_package_via_rex(
    module_org, katello_host_tools_host, target_sat, setup_custom_repo
):
    """Install a package to a host remotely using remote execution,
    install package using Katello SSH job template, host package list is used to verify that

    :id: 751c05b4-d7a3-48a2-8860-f0d15fdce204

    :expectedresults: Package was installed

    :parametrized: yes
    """
    client = katello_host_tools_host
    host_info = target_sat.cli.Host.info({'name': client.hostname})
    client.configure_rex(satellite=target_sat, org=module_org, register=False)
    # Apply errata to the host collection using job invocation
    target_sat.cli.JobInvocation.create(
        {
            'feature': 'katello_package_install',
            'search-query': f'name ~ {client.hostname}',
            'inputs': f'package={setup_custom_repo["package"]}',
            'organization-id': module_org.id,
        }
    )
    result = client.run(f'rpm -q {setup_custom_repo["package"]}')
    assert result.status == 0
    installed_packages = target_sat.cli.Host.package_list(
        {'host-id': host_info['id'], 'search': f'name={setup_custom_repo["package_name"]}'}
    )
    assert len(installed_packages) == 1


# -------------------------- HOST SUBSCRIPTION SUBCOMMAND SCENARIOS -------------------------
@pytest.mark.rhel_ver_match('9')
@pytest.mark.cli_host_subscription
@pytest.mark.tier3
def test_positive_register(
    module_org,
    module_promoted_cv,
    module_lce,
    module_ak_with_cv,
    rhel_contenthost,
    target_sat,
):
    """Attempt to register a host

    :id: b1c601ee-4def-42ce-b353-fc2657237533

    :expectedresults: host successfully registered

    :parametrized: yes
    """
    hosts = target_sat.cli.Host.list(
        {
            'organization-id': module_org.id,
            'search': rhel_contenthost.hostname,
        }
    )
    assert len(hosts) == 0
    target_sat.cli.Host.subscription_register(
        {
            'organization-id': module_org.id,
            'content-view-id': module_promoted_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'name': rhel_contenthost.hostname,
        }
    )
    hosts = target_sat.cli.Host.list(
        {
            'organization-id': module_org.id,
            'search': rhel_contenthost.hostname,
        }
    )
    assert len(hosts) > 0
    host = target_sat.cli.Host.info({'id': hosts[0]['id']})
    assert host['name'] == rhel_contenthost.hostname
    # note: when not registered the following command lead to exception,
    # see unregister
    host_subscriptions = target_sat.cli.ActivationKey.subscriptions(
        {
            'organization-id': module_org.id,
            'id': module_ak_with_cv.id,
            'host-id': host['id'],
        },
        output_format='json',
    )
    assert len(host_subscriptions) == 0


@pytest.mark.rhel_ver_match('9')
@pytest.mark.cli_host_subscription
@pytest.mark.tier3
def test_positive_without_attach_with_lce(
    target_sat,
    rhel_contenthost,
    function_ak_with_cv,
    function_org,
    function_lce,
):
    """Attempt to enable a repository of a subscription that was not
    attached to a host.
    This test is not using the host_subscription entities except
    subscription_name and repository_id

    :id: fc469e70-a7cb-4fca-b0ea-3c9e3dfff849

    :expectedresults: Repository enabled due to SCA.

    :parametrized: yes
    """
    content_view = target_sat.api.ContentView(organization=function_org).create()
    target_sat.cli_factory.setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhsclient7'],
            'repository': REPOS['rhsclient7']['name'],
            'organization-id': function_org.id,
            'content-view-id': content_view.id,
            'lifecycle-environment-id': function_lce.id,
            'activationkey-id': function_ak_with_cv.id,
            'subscription': DEFAULT_SUBSCRIPTION_NAME,
        },
        force_use_cdn=True,
    )

    # register client
    result = rhel_contenthost.register(function_org, None, function_ak_with_cv.name, target_sat)
    assert result.status == 0
    assert rhel_contenthost.subscribed
    res = rhel_contenthost.enable_repo(REPOS['rhsclient7']['id'])
    assert res.status == 0
    assert f"Repository '{REPOS['rhsclient7']['id']}' is enabled for this system." in res.stdout


@pytest.mark.rhel_ver_match('9')
@pytest.mark.pit_client
@pytest.mark.pit_server
@pytest.mark.cli_host_subscription
@pytest.mark.tier3
@pytest.mark.e2e
def test_syspurpose_end_to_end(
    target_sat,
    module_org,
    module_promoted_cv,
    module_lce,
    module_rhst_repo,
    default_subscription,
    rhel_contenthost,
):
    """Create a host with system purpose values set by activation key.

    :id: b88e9b6c-2348-49ce-b5e9-a2b9f0abed3f

    :expectedresults: host is registered and system purpose values are correct.

    :CaseImportance: Critical

    :parametrized: yes
    """
    # Create an activation key with test values
    purpose_addons = "test-addon1, test-addon2"
    activation_key = target_sat.api.ActivationKey(
        content_view=module_promoted_cv,
        environment=module_lce,
        organization=module_org,
        purpose_addons=[purpose_addons],
        purpose_role="test-role",
        purpose_usage="test-usage",
        service_level="Self-Support",
    ).create()
    # Register a host using the activation key
    res = rhel_contenthost.register(module_org, None, activation_key.name, target_sat)
    assert res.status == 0, f'Failed to register host: {res.stderr}'
    assert rhel_contenthost.subscribed
    rhel_contenthost.enable_repo(module_rhst_repo)
    host = target_sat.cli.Host.info({'name': rhel_contenthost.hostname})
    # Assert system purpose values are set in the host as expected
    assert host['subscription-information']['system-purpose']['purpose-addons'][0] == purpose_addons
    assert host['subscription-information']['system-purpose']['purpose-role'] == "test-role"
    assert host['subscription-information']['system-purpose']['purpose-usage'] == "test-usage"
    assert host['subscription-information']['system-purpose']['service-level'] == "Self-Support"
    # Change system purpose values in the host
    target_sat.cli.Host.update(
        {
            'purpose-addons': "test-addon3",
            'purpose-role': "test-role2",
            'purpose-usage': "test-usage2",
            'service-level': "Self-Support2",
            'id': host['id'],
        }
    )
    host = target_sat.cli.Host.info({'id': host['id']})
    # Assert system purpose values have been updated in the host as expected
    assert host['subscription-information']['system-purpose']['purpose-addons'][0] == "test-addon3"
    assert host['subscription-information']['system-purpose']['purpose-role'] == "test-role2"
    assert host['subscription-information']['system-purpose']['purpose-usage'] == "test-usage2"
    assert host['subscription-information']['system-purpose']['service-level'] == "Self-Support2"

    # Unregister host
    target_sat.cli.Host.subscription_unregister({'host': rhel_contenthost.hostname})
    with pytest.raises(CLIReturnCodeError):
        # raise error that the host was not registered by
        # subscription-manager register
        target_sat.cli.ActivationKey.subscriptions(
            {
                'organization-id': module_org.id,
                'id': activation_key.id,
                'host-id': host['id'],
            }
        )


# -------------------------- MULTI-CV SCENARIOS -------------------------
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('[^7]')
def test_negative_multi_cv_registration(
    module_org,
    module_ak_with_cv,
    module_lce,
    module_lce_library,
    module_published_cv,
    module_promoted_cv,
    target_sat,
    rhel_contenthost,
):
    """Attempt to register a host to multiple content view environments.

    :id: 52be9b92-55aa-44b7-8157-1998a8effb40

    :steps:
        1. Register a host with global reg, just to get the sub-man config and certs right
        2. Unregister the host
        3. Verify that allow_multiple_content_views setting is not exposed
        4. Attempt to register the host with subscription-manager, passing multiple environments
        5. Confirm that registration fails

    :expectedresults: allow_multiple_content_views setting is not exposed, and defaults to false.
        So registration fails because multiple environments are not allowed.

    :CaseImportance: Critical

    :CaseComponent: Hosts-Content

    :team: Phoenix-subscriptions

    :parametrized: yes
    """

    # Register with global reg, just to get the sub-man config and certs right
    result = rhel_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
    assert result.status == 0
    assert rhel_contenthost.subscribed

    # Unregister the host
    unregister_result = rhel_contenthost.unregister()
    assert unregister_result.status == 0

    # Verify that allow_multiple_content_views setting is not exposed
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Settings.info({'name': 'allow_multiple_content_views'})

    env_names = f"{module_lce_library.name}/{module_published_cv.name},{module_lce.name}/{module_promoted_cv.name}"

    # Register the host with subscription-manager, passing multiple environments
    res = rhel_contenthost.register_contenthost(module_org.label, lce=None, environments=env_names)
    assert (
        res.status == 70
    ), f'Expecting error "Registering to multiple environments is not enabled"; instead got: {res.stderr}'


@pytest.mark.rhel_ver_match('[^7]')
def test_positive_multi_cv_registration(
    session_multicv_sat,
    session_multicv_org,
    session_multicv_default_ak,
    session_multicv_lce,
    rhel_contenthost,
):
    """Register a host to multiple content view environments.

    :id: d0f78923-cace-4dc4-9936-81fe7e189a6b

    :steps:
        1. Register a host with global reg, just to get the sub-man config and certs right
        2. Unregister the host
        3. Attempt to register the host with subscription-manager, passing multiple environments
        4. Confirm that registration succeeds
        5. Confirm that the host is registered to both environments

    :expectedresults: Registration succeeds and the host is registered to both environments.

    :CaseImportance: Critical

    :CaseComponent: Hosts-Content

    :team: Phoenix-subscriptions

    :parametrized: yes
    """

    library_lce = (
        session_multicv_sat.api.LifecycleEnvironment()
        .search(query={'search': f'name=Library and organization_id={session_multicv_org.id}'})[0]
        .read()
    )

    # Create a content view
    cv1 = session_multicv_sat.api.ContentView(organization=session_multicv_org).create()
    cv1.publish()
    cv1 = cv1.read()

    # Create a second content view
    cv2 = session_multicv_sat.api.ContentView(organization=session_multicv_org).create()
    cv2.publish()
    cv2 = cv2.read()
    cv2_version = cv2.version[0]
    cv2_version.promote(data={'environment_ids': session_multicv_lce.id})

    # Register with global reg, just to get the sub-man config and certs right
    result = rhel_contenthost.register(
        session_multicv_org, None, session_multicv_default_ak.name, session_multicv_sat
    )
    assert result.status == 0
    assert rhel_contenthost.subscribed

    # Unregister the host
    unregister_result = rhel_contenthost.unregister()
    assert unregister_result.status == 0

    # Register the host with subscription-manager, passing multiple environments
    env_names = f"{library_lce.name}/{cv1.name},{session_multicv_lce.name}/{cv2.name}"
    res = rhel_contenthost.register_contenthost(
        session_multicv_org.label, lce=None, environments=env_names
    )

    # Confirm that registration succeeds
    assert res.status == 0
    assert rhel_contenthost.subscribed

    # Confirm that the host is registered to both environments
    host = session_multicv_sat.cli.Host.info({'name': rhel_contenthost.hostname})
    assert (
        len(host['content-information']['content-view-environments']) == 2
    ), "Expected host to be registered to both environments"


@pytest.mark.rhel_ver_match('[^7]')
def test_positive_multi_cv_assignment(
    session_multicv_sat,
    session_multicv_org,
    session_multicv_default_ak,
    session_multicv_lce,
    rhel_contenthost,
):
    """Register a host and assign it to multiple content view environments with Hammer.

    :id: c6a120a8-c6b6-483e-ac76-0e67d754038c

    :steps:
        1. Register a host with global registration
        2. Update the host using hammer to assign it to multiple content view environments
        3. Confirm that the host is registered to both environments

    :expectedresults: The update succeeds and the host is assigned to both environments.

    :CaseImportance: Critical

    :CaseComponent: Hosts-Content

    :team: Phoenix-subscriptions

    :parametrized: yes
    """

    library_lce = (
        session_multicv_sat.api.LifecycleEnvironment()
        .search(query={'search': f'name=Library and organization_id={session_multicv_org.id}'})[0]
        .read()
    )

    # Create a content view
    cv1 = session_multicv_sat.api.ContentView(organization=session_multicv_org).create()
    cv1.publish()
    cv1 = cv1.read()

    # Create a second content view
    cv2 = session_multicv_sat.api.ContentView(organization=session_multicv_org).create()
    cv2.publish()
    cv2 = cv2.read()
    cv2_version = cv2.version[0]
    cv2_version.promote(data={'environment_ids': session_multicv_lce.id})

    # Register with global registration
    result = rhel_contenthost.register(
        session_multicv_org, None, session_multicv_default_ak.name, session_multicv_sat
    )
    assert result.status == 0
    assert rhel_contenthost.subscribed

    # Assign multiple content view environments to the host using hammer
    env_names = f"{library_lce.name}/{cv1.name},{session_multicv_lce.name}/{cv2.name}"
    host = session_multicv_sat.cli.Host.info({'name': rhel_contenthost.hostname})
    session_multicv_sat.cli.Host.update({'id': host['id'], 'content-view-environments': env_names})

    # Confirm that the host is registered to both environments
    host = session_multicv_sat.cli.Host.info({'name': rhel_contenthost.hostname})
    assert (
        len(host['content-information']['content-view-environments']) == 2
    ), "Expected host to be registered to both environments"


@pytest.mark.rhel_ver_match('[^7]')
def test_positive_multi_cv_host_repo_availability(
    session_multicv_sat,
    rhel_contenthost,
    session_multicv_org,
    session_multicv_default_ak,
):
    """Multi-environment hosts should have access to repositories from all of their content view environments.

    :id: 6a15d591-be84-4b5b-8deb-8ea6eb32fee6

    :setup:
        1. Create two lifecycle environments
        2. Create two synced custom repositories
        3. Create two content views, each with a repo in them, and promote them to their own lifecycle environment

    :steps:
        1. Register a host with global registration to a single content view environment
        2. Assign the host to multiple content view environments
        3. Confirm repos listed in subscription-manager repos match the repos in the content view environments

    :expectedresults: Host sees repositories from both content view environments, not just one.

    :CaseImportance: Critical

    :CaseComponent: Hosts-Content

    :team: Phoenix-subscriptions

    :parametrized: yes
    """

    # Create two lifecycle environments
    lce1 = session_multicv_sat.api.LifecycleEnvironment(organization=session_multicv_org).create()
    lce2 = session_multicv_sat.api.LifecycleEnvironment(organization=session_multicv_org).create()

    # Create two synced custom repositories
    repo_instances = []
    for repo in ['RepoA', 'RepoB']:
        repo_id = session_multicv_sat.api_factory.create_sync_custom_repo(
            org_id=session_multicv_org.id,
            product_name=gen_string('alpha'),
            repo_name=repo,
            repo_url=settings.repos.fake_repo_zoo3,
        )
        repo_instances.append(session_multicv_sat.api.Repository(id=repo_id).read())

    repo_b = repo_instances.pop()
    repo_a = repo_instances.pop()

    # Create two content views, each with a repo in them, and promote them to their own lifecycle environment

    cv1 = session_multicv_sat.api.ContentView(
        organization=session_multicv_org, repository=[repo_a]
    ).create()
    cv1.publish()
    cv1 = cv1.read()

    module_published_cvv = cv1.read().version[0]
    module_published_cvv.promote(data={'environment_ids': lce1.id})

    cv2 = session_multicv_sat.api.ContentView(
        organization=session_multicv_org, repository=[repo_b]
    ).create()
    cv2.publish()
    cv2_content_view_version = cv2.read().version[0]
    cv2_content_view_version.promote(data={'environment_ids': lce2.id})

    # Register with global registration
    result = rhel_contenthost.register(
        session_multicv_org, None, session_multicv_default_ak.name, session_multicv_sat
    )
    assert result.status == 0
    assert rhel_contenthost.subscribed

    # Assign the host to multiple content view environments with subscription-manager
    env_names = f"{lce2.name}/{cv2.name},{lce1.name}/{cv1.name}"
    rhel_contenthost.subscription_manager_environments_set(env_names)

    host = session_multicv_sat.cli.Host.info({'name': rhel_contenthost.hostname})
    repos = rhel_contenthost.subscription_manager_list_repos()
    # Confirm that the host is registered to both environments
    assert (
        len(host['content-information']['content-view-environments']) == 2
    ), "Expected host to be registered to both environments"
    # Confirm that the host sees repositories from both content view environments
    assert repo_a.label in repos.stdout
    assert repo_b.label in repos.stdout


# -------------------------- HOST ERRATA SUBCOMMAND SCENARIOS -------------------------
@pytest.mark.tier1
def test_positive_errata_list_of_sat_server(target_sat):
    """Check if errata list doesn't raise exception. Check BZ for details.

    :id: 6b22f0c0-9c4b-11e6-ab93-68f72889dc7f

    :expectedresults: Satellite host errata list not failing

    :BZ: 1351040

    :CaseImportance: Critical
    """
    hostname = target_sat.execute('hostname').stdout.strip()
    host = target_sat.cli.Host.info({'name': hostname})
    assert isinstance(target_sat.cli.Host.errata_list({'host-id': host['id']}), list)


# -------------------------- HOST ENC SUBCOMMAND SCENARIOS -------------------------
@pytest.mark.tier1
def test_positive_dump_enc_yaml(target_sat):
    """Dump host's ENC YAML. Check BZ for details.

    :id: 50bf2530-788c-4710-a382-d034d73d5d4d

    :expectedresults: Ensure that enc-dump does not fail

    :customerscenario: true

    :BZ: 1372731, 1392747

    :CaseImportance: Critical
    """
    enc_dump = target_sat.cli.Host.enc_dump({'name': target_sat.hostname})
    assert f'fqdn: {target_sat.hostname}' in enc_dump
    assert f'ip: {target_sat.ip_addr}' in enc_dump
    assert 'ssh-rsa' in enc_dump


# -------------------------- HOST TRACE SUBCOMMAND SCENARIOS -------------------------
@pytest.mark.pit_client
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6].*')
def test_positive_tracer_list_and_resolve(tracer_host, target_sat):
    """Install tracer on client, downgrade the service, check from the satellite
    that tracer shows and resolves the problem. The test works with a package specified
    in settings. This package is expected to install a systemd service which is expected
    to log its version to /var/log/{package}/service.log.
    The rpm is not supposed to start the service upon install.

    :id: 81c83a2c-4b9d-11ec-a5b3-98fa9b6ecd5a

    :expectedresults: Tracer detected and resolved the problem, the affected service
        was restarted

    :parametrized: yes

    :CaseImportance: Medium

    :CaseComponent: katello-tracer

    :Team: Phoenix-subscriptions

    :bz: 2186188
    """
    client = tracer_host
    package = settings.repos["MOCK_SERVICE_RPM"]
    host_info = target_sat.cli.Host.info({'name': client.hostname})

    # mark the service log messages for later comparison and downgrade the pkg version
    service_ver_log_old = tracer_host.execute(f'cat /var/log/{package}/service.log')
    package_downgrade = tracer_host.execute(f'yum -y downgrade {package}')
    assert package_downgrade.status == 0

    # tracer should detect a new trace
    traces = target_sat.cli.HostTraces.list({'host-id': host_info['id']})[0]
    assert package == traces['application']

    # resolve traces and make sure that they disappear
    target_sat.cli.HostTraces.resolve({'host-id': host_info['id'], 'trace-ids': traces['trace-id']})
    traces = target_sat.cli.HostTraces.list({'host-id': host_info['id']})
    assert not traces

    # verify on the host end, that the service was really restarted
    service_ver_log_new = tracer_host.execute(f'cat /var/log/{package}/service.log')
    assert (
        service_ver_log_new != service_ver_log_old
    ), f'The service {package} did not seem to be restarted'


# ---------------------------- PUPPET ENABLED IN INSTALLER TESTS -----------------------
@pytest.mark.cli_puppet_enabled
@pytest.mark.tier1
def test_positive_host_with_puppet(
    session_puppet_enabled_sat,
    session_puppet_enabled_proxy,
    module_puppet_org,
    module_puppet_loc,
    module_puppet_environment,
):
    """Create update read and delete host with puppet environment

    :id: 8ae79fbe-79f4-11ec-80f5-98fa9b6ecd5a

    :expectedresults: puppet environment

    :CaseImportance: Critical
    """

    host_template = session_puppet_enabled_sat.api.Host()
    host_template.create_missing()
    host = session_puppet_enabled_sat.cli_factory.make_host(
        {
            'architecture-id': host_template.architecture.id,
            'domain-id': host_template.domain.id,
            'puppet-environment-id': host_template.environment.id,
            'location-id': host_template.location.id,
            'mac': host_template.mac,
            'medium-id': host_template.medium.id,
            'name': host_template.name,
            'operatingsystem-id': host_template.operatingsystem.id,
            'organization-id': host_template.organization.id,
            'partition-table-id': host_template.ptable.id,
            'puppet-proxy-id': session_puppet_enabled_proxy.id,
            'root-password': host_template.root_pass,
        }
    )
    session_puppet_enabled_sat.api.Environment(
        id=module_puppet_environment.id,
        organization=[host_template.organization],
        location=[host_template.location],
    ).update(['location', 'organization'])

    session_puppet_enabled_sat.cli.Host.update(
        {
            'name': host.name,
            'puppet-environment': module_puppet_environment.name,
        }
    )
    host = session_puppet_enabled_sat.cli.Host.info({'id': host['id']})
    assert host['puppet-environment'] == module_puppet_environment.name
    session_puppet_enabled_sat.cli.Host.delete({'id': host['id']})


@pytest.fixture
def function_host_content_source(
    target_sat,
    module_capsule_configured,
    module_lce_library,
    module_org,
    module_ak_with_cv_repo,
    module_product,
    module_repository,
    module_cv_repo,
    rhel_contenthost,
):
    target_sat.cli.Product.info({'id': module_product.id, 'organization-id': module_org.id})
    module_ak_with_cv_repo.content_override(
        data={
            'content_overrides': [
                {
                    'content_label': '_'.join(
                        [module_org.name, module_product.name, module_repository.name]
                    ),
                    'value': '1',
                }
            ]
        }
    )
    target_sat.cli.Capsule.update(
        {'name': module_capsule_configured.hostname, 'organization-ids': [module_org.id]}
    )
    # target_sat.cli.Capsule.info({'name': module_capsule_configured.hostname})
    res = rhel_contenthost.register(module_org, None, module_ak_with_cv_repo.name, target_sat)
    assert res.status == 0, f'Failed to register host: {res.stderr}'
    return res


@pytest.mark.tier2
@pytest.mark.cli_puppet_enabled
def test_positive_list_scparams(
    session_puppet_enabled_sat,
    session_puppet_enabled_proxy,
    module_env_search,
    module_puppet_loc,
    module_puppet_lce_library,
    module_puppet_org,
    module_puppet_classes,
):
    """List all smart class parameters using host id

    :id: 61814875-5ccd-4c04-a638-d36fe089d514

    :expectedresults: Overridden sc-param from puppet
        class are listed
    """
    update_smart_proxy(session_puppet_enabled_sat, module_puppet_loc, session_puppet_enabled_proxy)
    # Create hostgroup with associated puppet class
    host = session_puppet_enabled_sat.cli_factory.make_fake_host(
        {
            'puppet-class-ids': [module_puppet_classes[0].id],
            'puppet-environment': module_env_search.name,
            'organization-id': module_puppet_org.id,
            'location-id': module_puppet_loc.id,
            'lifecycle-environment-id': module_puppet_lce_library.id,
            'puppet-ca-proxy-id': session_puppet_enabled_proxy.id,
            'puppet-proxy-id': session_puppet_enabled_proxy.id,
        }
    )

    # Override one of the sc-params from puppet class
    sc_params_list = session_puppet_enabled_sat.cli.SmartClassParameter.list(
        {
            'puppet-environment': module_env_search.name,
            'search': f'puppetclass="{module_puppet_classes[0].name}"',
        }
    )
    scp_id = choice(sc_params_list)['id']
    session_puppet_enabled_sat.cli.SmartClassParameter.update({'id': scp_id, 'override': 1})
    # Verify that affected sc-param is listed
    host_scparams = session_puppet_enabled_sat.cli.Host.sc_params({'host': host['name']})
    assert scp_id in [scp['id'] for scp in host_scparams]


@pytest.mark.cli_puppet_enabled
@pytest.mark.tier1
def test_positive_create_with_puppet_class_name(
    session_puppet_enabled_sat,
    session_puppet_enabled_proxy,
    module_env_search,
    module_puppet_loc,
    module_puppet_org,
    module_puppet_lce_library,
    module_puppet_classes,
):
    """Check if host can be created with puppet class name

    :id: a65df36e-db4b-48d2-b0e1-5ccfbefd1e7a

    :expectedresults: Host is created and has puppet class assigned

    :CaseImportance: Critical
    """
    update_smart_proxy(session_puppet_enabled_sat, module_puppet_loc, session_puppet_enabled_proxy)
    host = session_puppet_enabled_sat.cli_factory.make_fake_host(
        {
            'puppet-class-ids': [module_puppet_classes[0].id],
            'puppet-environment': module_env_search.name,
            'organization-id': module_puppet_org.id,
            'location-id': module_puppet_loc.id,
            'lifecycle-environment-id': module_puppet_lce_library.id,
            'puppet-ca-proxy-id': session_puppet_enabled_proxy.id,
            'puppet-proxy-id': session_puppet_enabled_proxy.id,
        }
    )
    host_classes = session_puppet_enabled_sat.cli.Host.puppetclasses({'host': host['name']})
    assert module_puppet_classes[0].name in [puppet['name'] for puppet in host_classes]


@pytest.mark.cli_puppet_enabled
@pytest.mark.tier2
def test_positive_update_host_owner_and_verify_puppet_class_name(
    session_puppet_enabled_sat,
    session_puppet_enabled_proxy,
    module_env_search,
    module_puppet_org,
    module_puppet_loc,
    module_puppet_lce_library,
    module_puppet_classes,
    module_puppet_user,
):
    """Update host owner and check puppet clases associated to the host

    :id: 2b7dd148-914b-11eb-8a3a-98fa9b6ecd5a

    :expectedresults: Host is updated with new owner
        and puppet class is still assigned and shown

    :CaseImportance: Medium

    :BZ: 1851149, 1809952

    :customerscenario: true
    """
    update_smart_proxy(session_puppet_enabled_sat, module_puppet_loc, session_puppet_enabled_proxy)
    host = session_puppet_enabled_sat.cli_factory.make_fake_host(
        {
            'puppet-class-ids': [module_puppet_classes[0].id],
            'puppet-environment': module_env_search.name,
            'organization-id': module_puppet_org.id,
            'location-id': module_puppet_loc.id,
            'lifecycle-environment-id': module_puppet_lce_library.id,
            'puppet-ca-proxy-id': session_puppet_enabled_proxy.id,
            'puppet-proxy-id': session_puppet_enabled_proxy.id,
        }
    )
    host_classes = session_puppet_enabled_sat.cli.Host.puppetclasses({'host': host['name']})
    assert module_puppet_classes[0].name in [puppet['name'] for puppet in host_classes]

    session_puppet_enabled_sat.cli.Host.update(
        {'id': host['id'], 'owner': module_puppet_user.login, 'owner-type': 'User'}
    )
    host = session_puppet_enabled_sat.cli.Host.info({'id': host['id']})
    assert int(host['additional-info']['owner-id']) == module_puppet_user.id
    assert host['additional-info']['owner-type'] == 'User'

    host_classes = session_puppet_enabled_sat.cli.Host.puppetclasses({'host': host['name']})
    assert module_puppet_classes[0].name in [puppet['name'] for puppet in host_classes]


@pytest.mark.cli_puppet_enabled
@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.rhel_ver_match('[9]')
@pytest.mark.no_containers
def test_positive_create_and_update_with_content_source(
    target_sat,
    module_capsule_configured,
    module_org,
    module_lce,
    module_repository,
    rhel_contenthost,
    function_host_content_source,
):
    """Create a host with content source specified and update content
        source

    :id: 5712f4db-3610-447d-b1da-0fe461577d59

    :BZ: 1260697, 1483252, 1313056, 1488465

    :expectedresults: A host is created with expected content source
        assigned and then content source is successfully updated

    :CaseImportance: High
    """
    target_sat.cli.Repository.synchronize({'id': module_repository.id})

    host = target_sat.cli.Host.info({'name': rhel_contenthost.hostname})
    assert (
        host['content-information']['content-source']['name'] == target_sat.hostname
        or host['content-information']['content-source']['name'] == ''
    )

    # set a new proxy
    target_sat.cli.Capsule.update(
        {'name': module_capsule_configured.hostname, 'organization-id': module_org.id}
    )
    target_sat.cli.Capsule.content_add_lifecycle_environment(
        {
            'name': module_capsule_configured.hostname,
            'organization-id': module_org.id,
            'environment-id': module_lce.id,
        }
    )
    target_sat.cli.Host.update(
        {'id': host['id'], 'content-source': module_capsule_configured.hostname}
    )
    host = target_sat.cli.Host.info({'id': host['id']})
    assert (
        host['content-information']['content-source']['name'] == module_capsule_configured.hostname
    )

    # run an ansible job that makes a host aware that it should use a different content source
    target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Configure host for new content source',
            'search-query': f"name ~ {rhel_contenthost.hostname}",
        }
    )

    # test that the new content source is really used to get content
    package = 'at'
    assert rhel_contenthost.execute(f'rpm -q {package}').status != 0
    assert rhel_contenthost.execute(f'dnf -y install {package}').status != 0
    target_sat.cli.Capsule.content_synchronize({'name': module_capsule_configured.hostname})
    assert rhel_contenthost.execute(f'dnf -y install {package}').status == 0
    assert rhel_contenthost.execute(f'rpm -q {package}').status == 0


@pytest.mark.cli_host_create
@pytest.mark.tier2
def test_positive_create_host_with_lifecycle_environment_name(
    module_lce,
    module_org,
    module_promoted_cv,
    module_target_sat,
):
    """Attempt to create a host with lifecycle-environment name specified

    :id: 7445ad21-538f-4357-8bd1-9676d2478633

    :BZ: 2106256

    :expectedresults: Host is created with no errors

    :customerscenario: true

    :CaseImportance: Medium
    """
    found_host = False
    new_host = module_target_sat.cli_factory.make_fake_host(
        {
            'content-view-id': module_promoted_cv.id,
            'lifecycle-environment': module_lce.name,
            'organization-id': module_org.id,
        }
    )
    hosts = module_target_sat.cli.Host.list({'organization-id': module_org.id})
    found_host = any(new_host.name in i.values() for i in hosts)
    assert found_host, 'Assertion failed: host not found'


@pytest.mark.rhel_ver_match('^6')
@pytest.mark.parametrize(
    'setting_update', ['validate_host_lce_content_source_coherence'], indirect=False
)
def test_host_registration_with_capsule_using_content_coherence(
    module_target_sat,
    setting_update,
    module_sca_manifest_org,
    module_activation_key,
    rhel_contenthost,
    module_capsule_configured,
):
    """Register client with capsule when settings "validate_host_lce_content_source_coherence" is set to Yes/No

    :id: 17dbec62-eed4-4a51-9927-80919457a124

    :Verifies: SAT-22048

    :setup:
        1. Create AK which is associated with the organization
        2. Configure capsule with satellite

    :steps:
        1. Register client with capsule when settings "validate_host_lce_content_source_coherence" is set to Yes
        2. Check output for "HTTP error code 422: Validation failed: Content view environment content facets is invalid"
        3. Re-register client with settings "validate_host_lce_content_source_coherence" is set to No
        4. Check output there should not be any error like "Validation failed" or "HTTP error code 422"

    :expectedresults: Host registration success with error when settings set to Yes and Host registration success when
     settings set to No

    :customerscenario: true

    :parametrized: yes

    :CaseImportance: High
    """
    # set a new proxy
    module_target_sat.cli.Capsule.update(
        {'name': module_capsule_configured.hostname, 'organization-ids': module_sca_manifest_org.id}
    )
    # Register client with capsule when settings "validate_host_lce_content_source_coherence" is set to Yes
    module_target_sat.cli.Settings.set(
        {'name': 'validate_host_lce_content_source_coherence', 'value': 'true'}
    )
    result = rhel_contenthost.register(
        module_sca_manifest_org,
        None,
        module_activation_key.name,
        module_capsule_configured,
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Check output for "HTTP error code 422: Validation failed: Content view environment content facets is invalid"
    assert 'Validation failed' in result.stderr, f'Error is: {result.stderr}'
    if rhel_contenthost.os_version.major != 7:
        assert 'HTTP error code 422' in result.stderr, f'Error is: {result.stderr}'

    # Re-register client with settings "validate_host_lce_content_source_coherence" is set to No
    module_target_sat.cli.Settings.set(
        {'name': 'validate_host_lce_content_source_coherence', 'value': 'false'}
    )
    result = rhel_contenthost.register(
        module_sca_manifest_org,
        None,
        module_activation_key.name,
        module_capsule_configured,
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Check output there should not any error like "Validation failed" or "HTTP error code 422"
    assert 'Validation failed' not in result.stderr, f'Error is: {result.stderr}'
    if rhel_contenthost.os_version.major != 7:
        assert 'HTTP error code 422' not in result.stderr, f'Error is: {result.stderr}'
