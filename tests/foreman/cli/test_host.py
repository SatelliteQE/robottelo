"""CLI tests for ``hammer host``.

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

import pytest
import yaml
from fauxfactory import gen_choice
from fauxfactory import gen_integer
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_string
from nailgun import entities

from robottelo import ssh
from robottelo.api.utils import promote
from robottelo.cleanup import vm_cleanup
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import add_role_permissions
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_architecture
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_environment
from robottelo.cli.factory import make_fake_host
from robottelo.cli.factory import make_host
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_proxy
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.host import Host
from robottelo.cli.host import HostInterface
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.location import Location
from robottelo.cli.org import Org
from robottelo.cli.proxy import Proxy
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import ENVIRONMENT
from robottelo.constants import NO_REPOS_AVAILABLE
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants import SATELLITE_SUBSCRIPTION_NAME
from robottelo.constants import SM_OVERALL_STATUS
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_hosts_list
from robottelo.decorators import skip_if_not_set
from robottelo.vm import VirtualMachine
from robottelo.vm import VirtualMachineError


@pytest.fixture(scope="module")
def module_default_proxy():
    """ Use the default installation smart proxy """
    return Proxy.list({'search': f'url = https://{settings.server.hostname}:9090'})[0]


@pytest.fixture(scope="module")
def module_promoted_cv(module_lce, module_published_cv):
    promote(module_published_cv.version[0], environment_id=module_lce.id)
    return module_published_cv


@pytest.fixture(scope="function")
def function_proxy():
    proxy = make_proxy()
    yield proxy
    Proxy.delete({'id': proxy['id']})


@pytest.fixture(scope="function")
def function_host_content_source(
    module_default_proxy, module_lce_library, module_org, module_published_cv
):
    host = make_fake_host(
        {
            'content-source-id': module_default_proxy['id'],
            'content-view-id': module_published_cv.id,
            'lifecycle-environment-id': module_lce_library.id,
            'organization': module_org.name,
        }
    )
    yield host
    Host.delete({'id': host['id']})


@pytest.fixture(scope="module")
def module_make_ak(module_lce, module_org, module_promoted_cv):
    return make_activation_key(
        {
            'content-view-id': module_promoted_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'organization-id': module_org.id,
        }
    )


@pytest.fixture(scope="function")
def function_make_host(module_default_proxy):
    host_template = entities.Host()
    host_template.create_missing()
    org_id = host_template.organization.id
    loc_id = host_template.location.id
    # using CLI to create host
    return make_host(
        {
            'architecture-id': host_template.architecture.id,
            'domain-id': host_template.domain.id,
            'environment-id': host_template.environment.id,
            'location-id': loc_id,
            'mac': host_template.mac,
            'medium-id': host_template.medium.id,
            'name': host_template.name,
            'operatingsystem-id': host_template.operatingsystem.id,
            'organization-id': org_id,
            'partition-table-id': host_template.ptable.id,
            'puppet-proxy-id': module_default_proxy['id'],
            'root-password': host_template.root_pass,
        }
    )


@pytest.fixture(scope="function")
def function_make_user(function_make_host):
    """
    Returns dict with user object and with password to this user
    """
    user_name = gen_string('alphanumeric')
    user_password = gen_string('alphanumeric')
    org = Org.info({'name': function_make_host['organization']})
    location = Location.info({'name': function_make_host['location']})
    user = make_user(
        {
            'admin': False,
            'default-organization-id': org['id'],
            'organization-ids': [org['id']],
            'default-location-id': location['id'],
            'location-ids': [location['id']],
            'login': user_name,
            'password': user_password,
        }
    )
    return {'user': user, 'password': user_password}


# -------------------------- CREATE SCENARIOS -------------------------
@pytest.mark.host_create
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_and_delete(module_lce_library, module_published_cv):
    """A host can be created and deleted

    :id: 59fcbe50-9c6b-4c3c-87b3-272b4b584fb3

    :expectedresults: A host is created and deleted

    :BZ: 1260697, 1313056, 1361309

    :CaseImportance: Critical
    """
    name = valid_hosts_list()[0]
    host = entities.Host()
    host.create_missing()
    interface = (
        "type=interface,mac={},identifier=eth0,name={},domain_id={},"
        "ip={},primary=true,provision=true"
    ).format(host.mac, gen_string('alpha'), host.domain.id, gen_ipaddr())
    new_host = make_host(
        {
            'architecture-id': host.architecture.id,
            'content-view-id': module_published_cv.id,
            'domain-id': host.domain.id,
            'environment-id': host.environment.id,
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
    host_interface = HostInterface.info(
        {'host-id': new_host['id'], 'id': new_host['network-interfaces'][0]['id']}
    )
    assert host_interface['domain'] == host.domain.read().name

    Host.delete({'id': new_host['id']})
    with pytest.raises(CLIReturnCodeError):
        Host.info({'id': new_host['id']})


@pytest.mark.host_create
@pytest.mark.tier1
def test_positive_add_interface_by_id():
    """New network interface can be added to existing host

    :id: e97dba92-61eb-47ad-a7d7-5f989292b12a

    :expectedresults: Interface added to host correctly and has proper
        domain and mac address

    :CaseImportance: Critical
    """
    domain = make_domain(
        {'organizations': 'Default Organization', 'locations': 'Default Location'}
    )
    mac = gen_mac(multicast=False)
    host = make_fake_host({'domain-id': domain['id']})
    HostInterface.create(
        {'host-id': host['id'], 'domain-id': domain['id'], 'mac': mac, 'type': 'interface'}
    )
    host = Host.info({'id': host['id']})
    host_interface = HostInterface.info(
        {
            'host-id': host['id'],
            'id': [ni for ni in host['network-interfaces'] if ni['mac-address'] == mac][0]['id'],
        }
    )
    assert host_interface['domain'] == domain['name']
    assert host_interface['mac-address'] == mac


@pytest.mark.host_create
@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_create_and_update_with_content_source(
    function_host_content_source, function_proxy, module_default_proxy
):
    """Create a host with content source specified and update content
        source

    :id: 5712f4db-3610-447d-b1da-0fe461577d59

    :customerscenario: true

    :BZ: 1260697, 1483252, 1313056, 1488465

    :expectedresults: A host is created with expected content source
        assigned and then content source is successfully updated

    :CaseImportance: High
    """
    host = function_host_content_source
    assert host['content-information']['content-source']['name'] == module_default_proxy['name']
    new_content_source = function_proxy
    Host.update({'id': host['id'], 'content-source-id': new_content_source['id']})
    host = Host.info({'id': host['id']})
    assert host['content-information']['content-source']['name'] == new_content_source['name']


@pytest.mark.host_create
@pytest.mark.tier2
def test_negative_create_with_content_source(module_lce_library, module_org, module_published_cv):
    """Attempt to create a host with invalid content source specified

    :id: d92d6aff-4ad3-467c-88a8-5a5e56614f58

    :BZ: 1260697

    :expectedresults: Host was not created

    :CaseImportance: Medium
    """
    with pytest.raises(CLIFactoryError):
        make_fake_host(
            {
                'content-source-id': gen_integer(10000, 99999),
                'content-view-id': module_published_cv.id,
                'lifecycle-environment-id': module_lce_library.id,
                'organization': module_org.name,
            }
        )


@pytest.mark.host_create
@pytest.mark.tier2
def test_negative_update_content_source(
    module_default_proxy, module_lce_library, module_org, module_published_cv
):
    """Attempt to update host's content source with invalid value

    :id: 03243c56-3835-4b15-94df-15d436bbda87

    :BZ: 1260697, 1483252, 1313056

    :expectedresults: Host was not updated. Content source remains the same
        as it was before update

    :CaseImportance: Medium
    """
    host = make_fake_host(
        {
            'content-source-id': module_default_proxy['id'],
            'content-view-id': module_published_cv.id,
            'lifecycle-environment-id': module_lce_library.id,
            'organization': module_org.name,
        }
    )
    with pytest.raises(CLIReturnCodeError):
        Host.update({'id': host['id'], 'content-source-id': gen_integer(10000, 99999)})
    host = Host.info({'id': host['id']})
    assert host['content-information']['content-source']['name'] == module_default_proxy['name']


@pytest.mark.host_create
@pytest.mark.tier1
def test_positive_create_with_lce_and_cv(module_lce, module_org, module_promoted_cv):
    """Check if host can be created with new lifecycle and
        new content view

    :id: c2075131-6b25-4af3-b1e9-a7a9190dd6f8

    :expectedresults: Host is created using new lifecycle and
        new content view

    :BZ: 1313056

    :CaseImportance: Critical
    """
    new_host = make_fake_host(
        {
            'content-view-id': module_promoted_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'organization-id': module_org.id,
        }
    )
    assert new_host['content-information']['lifecycle-environment']['name'] == module_lce.name
    assert new_host['content-information']['content-view']['name'] == module_promoted_cv.name


@pytest.mark.host_create
@pytest.mark.tier1
def test_positive_create_with_puppet_class_name(
    module_env_search, module_org, module_puppet_classes
):
    """Check if host can be created with puppet class name

    :id: a65df36e-db4b-48d2-b0e1-5ccfbefd1e7a

    :expectedresults: Host is created and has puppet class assigned

    :CaseImportance: Critical
    """
    host = make_fake_host(
        {
            'puppet-classes': module_puppet_classes[0].name,
            'environment': module_env_search.name,
            'organization-id': module_org.id,
        }
    )
    host_classes = Host.puppetclasses({'host': host['name']})
    assert module_puppet_classes[0].name in [puppet['name'] for puppet in host_classes]


@pytest.mark.host_create
@pytest.mark.tier2
def test_positive_create_with_openscap_proxy_id(module_default_proxy, module_org):
    """Check if host can be created with OpenSCAP Proxy id

    :id: 3774ba08-3b18-4e64-b07f-53f6aa0504f3

    :expectedresults: Host is created and has OpenSCAP Proxy assigned

    :CaseImportance: Medium
    """
    host = make_fake_host(
        {'organization-id': module_org.id, 'openscap-proxy-id': module_default_proxy['id']}
    )
    assert host['openscap-proxy'] == module_default_proxy['id']


@pytest.mark.host_create
@pytest.mark.tier1
def test_negative_create_with_name(module_lce_library, module_org, module_published_cv):
    """Check if host can be created with random long names

    :id: f92b6070-b2d1-4e3e-975c-39f1b1096697

    :expectedresults: Host is not created

    :CaseImportance: Critical
    """
    name = gen_choice(invalid_values_list())
    with pytest.raises(CLIFactoryError):
        make_fake_host(
            {
                'name': name,
                'organization-id': module_org.id,
                'content-view-id': module_published_cv.id,
                'lifecycle-environment-id': module_lce_library.id,
            }
        )


@pytest.mark.host_create
@pytest.mark.tier1
def test_negative_create_with_unpublished_cv(module_lce, module_org, module_cv):
    """Check if host can be created using unpublished cv

    :id: 9997383d-3c27-4f14-94f9-4b8b51180eb6

    :expectedresults: Host is not created using new unpublished cv

    :CaseImportance: Critical
    """
    with pytest.raises(CLIFactoryError):
        make_fake_host(
            {
                'content-view-id': module_cv.id,
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )


@pytest.mark.host_create
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_katello_and_openscap_loaded():
    """Verify that command line arguments from both Katello
    and foreman_openscap plugins are loaded and available
    at the same time

    :id: 5b5db1d4-50f9-45a0-bb92-4571fc8d729b

    :expectedresults: Command line arguments from both Katello
        and foreman_openscap are available in help message
        (note: help is generated dynamically based on apipie cache)

    :CaseLevel: System

    :CaseImportance: Medium

    :BZ: 1671148
    """
    help_output = Host.execute('host update --help')
    for arg in ['lifecycle-environment[-id]', 'openscap-proxy-id']:
        assert any(
            f'--{arg}' in line for line in help_output
        ), f"--{arg} not supported by update subcommand"


@pytest.mark.host_create
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_register_with_no_ak(module_lce, module_org, module_promoted_cv):
    """Register host to satellite without activation key

    :id: 6a7cedd2-aa9c-4113-a83b-3f0eea43ecb4

    :expectedresults: Host successfully registered to appropriate org

    :CaseLevel: System
    """
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        client.install_katello_ca()
        client.register_contenthost(
            module_org.label,
            lce=f'{module_lce.label}/{module_promoted_cv.label}',
        )
        assert client.subscribed


@pytest.mark.host_create
@pytest.mark.tier3
def test_negative_register_twice(module_make_ak, module_org):
    """Attempt to register a host twice to Satellite

    :id: 0af81129-cd69-4fa7-a128-9e8fcf2d03b1

    :expectedresults: host cannot be registered twice

    :CaseLevel: System
    """
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        client.install_katello_ca()
        client.register_contenthost(module_org.label, module_make_ak['name'])
        assert client.subscribed
        result = client.register_contenthost(module_org.label, module_make_ak['name'], force=False)
        # Depending on distro version, successful return_code may be 0 or
        # 1, so we can't verify host wasn't registered by return_code != 0
        # check. Verifying return_code == 64 here, which stands for content
        # host being already registered.
        assert result.return_code == 64


@pytest.mark.host_create
@pytest.mark.tier2
def test_positive_list_scparams(module_env_search, module_org, module_puppet_classes):
    """List all smart class parameters using host id

    :id: 61814875-5ccd-4c04-a638-d36fe089d514

    :expectedresults: Overridden sc-param from puppet
        class are listed

    :CaseLevel: Integration
    """
    # Create hostgroup with associated puppet class
    host = make_fake_host(
        {
            'puppet-classes': module_puppet_classes[0].name,
            'environment': module_env_search.name,
            'organization-id': module_org.id,
        }
    )

    # Override one of the sc-params from puppet class
    sc_params_list = SmartClassParameter.list(
        {
            'environment': module_env_search.name,
            'search': 'puppetclass="{}"'.format(module_puppet_classes[0].name),
        }
    )
    scp_id = choice(sc_params_list)['id']
    SmartClassParameter.update({'id': scp_id, 'override': 1})
    # Verify that affected sc-param is listed
    host_scparams = Host.sc_params({'host': host['name']})
    assert scp_id in [scp['id'] for scp in host_scparams]


@pytest.mark.host_create
@pytest.mark.tier3
def test_positive_list(module_make_ak, module_lce, module_org):
    """List hosts for a given org

    :id: b9c056cd-11ca-4870-bac4-0ebc4a782cb0

    :expectedresults: Hosts are listed for the given org

    :CaseLevel: System
    """
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        client.install_katello_ca()
        client.register_contenthost(module_org.label, module_make_ak['name'])
        assert client.subscribed
        hosts = Host.list({'organization-id': module_org.id, 'environment-id': module_lce.id})
        assert len(hosts) >= 1
        assert client.hostname in [host['name'] for host in hosts]


@pytest.mark.host_create
@pytest.mark.tier3
def test_positive_list_by_last_checkin(module_lce, module_org, module_promoted_cv):
    """List all content hosts using last checkin criteria

    :id: e7d86b44-28c3-4525-afac-61a20e62daf8

    :customerscenario: true

    :expectedresults: Hosts are listed for the given time period

    :BZ: 1285992

    :CaseLevel: System
    """
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        client.install_katello_ca()
        client.register_contenthost(
            module_org.label,
            lce=f'{module_lce.label}/{module_promoted_cv.label}',
        )
        assert client.subscribed
        hosts = Host.list({'search': 'last_checkin = "Today" or last_checkin = "Yesterday"'})
        assert len(hosts) >= 1
        assert client.hostname in [host['name'] for host in hosts]


@pytest.mark.host_create
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_unregister(module_make_ak, module_lce, module_org):
    """Unregister a host

    :id: c5ce988d-d0ea-4958-9956-5a4b039b285c

    :expectedresults: Host is successfully unregistered. Unlike content
        host, host has not disappeared from list of hosts after
        unregistering.

    :CaseLevel: System
    """
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        client.install_katello_ca()
        client.register_contenthost(module_org.label, module_make_ak['name'])
        assert client.subscribed
        hosts = Host.list({'organization-id': module_org.id, 'environment-id': module_lce.id})
        assert len(hosts) >= 1
        assert client.hostname in [host['name'] for host in hosts]
        result = client.run('subscription-manager unregister')
        assert result.return_code == 0
        hosts = Host.list({'organization-id': module_org.id, 'environment-id': module_lce.id})
        assert client.hostname in [host['name'] for host in hosts]


@skip_if_not_set('compute_resources')
@pytest.mark.host_create
@pytest.mark.tier1
def test_positive_create_using_libvirt_without_mac(
    module_location, module_org, module_default_proxy
):
    """Create a libvirt host and not specify a MAC address.

    :id: b003faa9-2810-4176-94d2-ea84bed248eb

    :expectedresults: Host is created

    :CaseImportance: Critical
    """
    compute_resource = entities.LibvirtComputeResource(
        url=f'qemu+ssh://root@{settings.compute_resources.libvirt_hostname}/system',
        organization=[module_org.id],
        location=[module_location.id],
    ).create()
    host = entities.Host(organization=module_org.id, location=module_location.id)
    host.create_missing()
    result = make_host(
        {
            'architecture-id': host.architecture.id,
            'compute-resource-id': compute_resource.id,
            'domain-id': host.domain.id,
            'environment-id': host.environment.id,
            'location-id': host.location.id,
            'medium-id': host.medium.id,
            'name': host.name,
            'operatingsystem-id': host.operatingsystem.id,
            'organization-id': host.organization.id,
            'partition-table-id': host.ptable.id,
            'puppet-proxy-id': module_default_proxy['id'],
            'root-password': host.root_pass,
        }
    )
    assert result['name'] == host.name + '.' + host.domain.name
    Host.delete({'id': result['id']})


@pytest.mark.host_create
@pytest.mark.tier2
def test_positive_create_inherit_lce_cv(module_published_cv, module_lce_library, module_org):
    """Create a host with hostgroup specified. Make sure host inherited
    hostgroup's lifecycle environment and content-view

    :id: ba73b8c8-3ce1-4fa8-a33b-89ded9ffef47

    :expectedresults: Host's lifecycle environment and content view match
        the ones specified in hostgroup

    :CaseLevel: Integration

    :BZ: 1391656
    """
    hostgroup = make_hostgroup(
        {
            'content-view-id': module_published_cv.id,
            'lifecycle-environment-id': module_lce_library.id,
            'organization-ids': module_org.id,
        }
    )
    host = make_fake_host({'hostgroup-id': hostgroup['id'], 'organization-id': module_org.id})
    assert (
        host['content-information']['lifecycle-environment']['name']
        == hostgroup['lifecycle-environment']['name']
    )
    assert host['content-information']['content-view']['name'] == hostgroup['content-view']['name']


@pytest.mark.host_create
@pytest.mark.tier3
def test_positive_create_inherit_nested_hostgroup():
    """Create two nested host groups with the same name, but different
    parents. Then create host using any from these hostgroups title

    :id: 7bc95130-3f20-493d-b54c-04c444d97563

    :expectedresults: Host created successfully using host group title

    :CaseLevel: System

    :BZ: 1436162
    """
    options = entities.Host()
    options.create_missing()
    lce = make_lifecycle_environment({'organization-id': options.organization.id})
    cv = make_content_view({'organization-id': options.organization.id})
    ContentView.publish({'id': cv['id']})
    version_id = ContentView.version_list({'content-view-id': cv['id']})[0]['id']
    ContentView.version_promote({'id': version_id, 'to-lifecycle-environment-id': lce['id']})
    host_name = gen_string('alpha').lower()
    nested_hg_name = gen_string('alpha')
    parent_hostgroups = []
    nested_hostgroups = []
    for _ in range(2):
        parent_hg_name = gen_string('alpha')
        parent_hostgroups.append(
            make_hostgroup({'name': parent_hg_name, 'organization-ids': options.organization.id})
        )
        nested_hostgroups.append(
            make_hostgroup(
                {
                    'name': nested_hg_name,
                    'parent': parent_hg_name,
                    'organization-ids': options.organization.id,
                    'architecture-id': options.architecture.id,
                    'domain-id': options.domain.id,
                    'medium-id': options.medium.id,
                    'operatingsystem-id': options.operatingsystem.id,
                    'partition-table-id': options.ptable.id,
                    'location-ids': options.location.id,
                    'content-view-id': cv['id'],
                    'lifecycle-environment-id': lce['id'],
                }
            )
        )

    host = make_host(
        {
            'hostgroup-title': nested_hostgroups[0]['title'],
            'location-id': options.location.id,
            'organization-id': options.organization.id,
            'name': host_name,
        }
    )
    assert f'{host_name}.{options.domain.read().name}' == host['name']


@pytest.mark.host_create
@pytest.mark.tier3
def test_positive_list_with_nested_hostgroup():
    """Create parent and nested host groups. Then create host using nested
    hostgroup and then find created host using list command

    :id: 50c964c3-d3d6-4832-a51c-62664d132229

    :customerscenario: true

    :expectedresults: Host is successfully listed and has both parent and
        nested host groups names in its hostgroup parameter

    :BZ: 1427554

    :CaseLevel: System
    """
    options = entities.Host()
    options.create_missing()
    host_name = gen_string('alpha').lower()
    parent_hg_name = gen_string('alpha')
    nested_hg_name = gen_string('alpha')
    lce = make_lifecycle_environment({'organization-id': options.organization.id})
    cv = make_content_view({'organization-id': options.organization.id})
    ContentView.publish({'id': cv['id']})
    version_id = ContentView.version_list({'content-view-id': cv['id']})[0]['id']
    ContentView.version_promote({'id': version_id, 'to-lifecycle-environment-id': lce['id']})
    make_hostgroup({'name': parent_hg_name, 'organization-ids': options.organization.id})
    nested_hostgroup = make_hostgroup(
        {
            'name': nested_hg_name,
            'parent': parent_hg_name,
            'organization-ids': options.organization.id,
            'architecture-id': options.architecture.id,
            'domain-id': options.domain.id,
            'medium-id': options.medium.id,
            'operatingsystem-id': options.operatingsystem.id,
            'partition-table-id': options.ptable.id,
            'location-ids': options.location.id,
            'content-view-id': cv['id'],
            'lifecycle-environment-id': lce['id'],
        }
    )
    make_host(
        {
            'hostgroup-id': nested_hostgroup['id'],
            'location-id': options.location.id,
            'organization-id': options.organization.id,
            'name': host_name,
        }
    )
    hosts = Host.list({'organization-id': options.organization.id})
    assert f'{parent_hg_name}/{nested_hg_name}' == hosts[0]['host-group']


@pytest.mark.host_create
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

    :CaseLevel: System
    """


# -------------------------- UPDATE SCENARIOS -------------------------
@pytest.mark.host_update
@pytest.mark.tier1
def test_positive_update_parameters_by_name(function_make_host):
    """A host can be updated with a new name, mac address, domain,
        location, environment, architecture, operating system and medium.
        Use id to access the host

    :id: 3a4c0b5a-5d87-477a-b80a-9af0ec3b4b6f

    :expectedresults: A host is updated and the name, mac address, domain,
        location, environment, architecture, operating system and medium
        matches

    :BZ: 1343392, 1679300

    :CaseImportance: Critical
    """
    new_name = valid_hosts_list()[0]
    new_mac = gen_mac(multicast=False)
    new_loc = make_location()
    new_domain = make_domain(
        {'locations': new_loc['name'], 'organizations': function_make_host['organization']}
    )
    new_env = make_environment(
        {'locations': new_loc['name'], 'organizations': function_make_host['organization']}
    )
    new_arch = make_architecture()
    new_os = make_os(
        {
            'architectures': new_arch['name'],
            'partition-tables': function_make_host['operating-system']['partition-table'],
        }
    )
    new_medium = make_medium(
        {
            'locations': new_loc['name'],
            'organizations': function_make_host['organization'],
            'operatingsystems': new_os['title'],
        }
    )
    Host.update(
        {
            'architecture': new_arch['name'],
            'domain': new_domain['name'],
            'environment': new_env['name'],
            'name': function_make_host['name'],
            'mac': new_mac,
            'medium-id': new_medium['id'],
            'new-name': new_name,
            'operatingsystem': new_os['title'],
            'new-location-id': new_loc['id'],
        }
    )
    host = Host.info({'id': function_make_host['id']})
    assert '{}.{}'.format(new_name, host['network']['domain']) == host['name']
    assert host['location'] == new_loc['name']
    assert host['network']['mac'] == new_mac
    assert host['network']['domain'] == new_domain['name']
    assert host['puppet-environment'] == new_env['name']
    assert host['operating-system']['architecture'] == new_arch['name']
    assert host['operating-system']['operating-system'] == new_os['title']
    assert host['operating-system']['medium'] == new_medium['name']


@pytest.mark.tier1
@pytest.mark.host_update
def test_negative_update_name(function_make_host):
    """A host can not be updated with invalid or empty name

    :id: e8068d2a-6a51-4627-908b-60a516c67032

    :expectedresults: A host is not updated

    :CaseImportance: Critical
    """
    new_name = gen_choice(invalid_values_list())
    with pytest.raises(CLIReturnCodeError):
        Host.update({'id': function_make_host['id'], 'new-name': new_name})
    host = Host.info({'id': function_make_host['id']})
    assert '{}.{}'.format(new_name, host['network']['domain']).lower() != host['name']


@pytest.mark.tier1
@pytest.mark.host_update
def test_negative_update_mac(function_make_host):
    """A host can not be updated with invalid or empty MAC address

    :id: 2f03032d-789d-419f-9ff2-a6f3561444da

    :expectedresults: A host is not updated

    :CaseImportance: Critical
    """
    new_mac = gen_choice(invalid_values_list())
    with pytest.raises(CLIReturnCodeError):
        Host.update({'id': function_make_host['id'], 'mac': new_mac})
    host = Host.info({'id': function_make_host['id']})
    assert host['network']['mac'] != new_mac


@pytest.mark.tier2
@pytest.mark.host_update
def test_negative_update_arch(function_make_host):
    """A host can not be updated with a architecture, which does not
    belong to host's operating system

    :id: a86524da-8caf-472b-9a3d-17a4385c3a18

    :expectedresults: A host is not updated

    :CaseLevel: Integration
    """
    new_arch = make_architecture()
    with pytest.raises(CLIReturnCodeError):
        Host.update({'architecture': new_arch['name'], 'id': function_make_host['id']})
    host = Host.info({'id': function_make_host['id']})
    assert host['operating-system']['architecture'] != new_arch['name']


@pytest.mark.tier2
@pytest.mark.host_update
def test_negative_update_os(function_make_host):
    """A host can not be updated with a operating system, which is
    not associated with host's medium

    :id: ff13d2af-e54a-4daf-a24d-7ec930b4fbbe

    :expectedresults: A host is not updated

    :CaseLevel: Integration
    """
    new_arch = make_architecture()
    new_os = make_os(
        {
            'architectures': new_arch['name'],
            'partition-tables': function_make_host['operating-system']['partition-table'],
        }
    )
    with pytest.raises(CLIReturnCodeError):
        Host.update(
            {
                'architecture': new_arch['name'],
                'id': function_make_host['id'],
                'operatingsystem': new_os['title'],
            }
        )
    host = Host.info({'id': function_make_host['id']})
    assert host['operating-system']['operating-system'] != new_os['title']


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.host_update
def test_hammer_host_info_output():
    """Verify re-add of 'owner-id' in `hammer host info` output

    :id: 03468516-0ebb-11eb-8ad8-0c7a158cbff4

    :Steps:
        1. Update the host with any owner
        2. Get host info by running `hammer host info`

    :expectedresults: 'owner-id' should be in `hammer host info` output

    :BZ: 1779093
    """
    result_list = User.list()
    Host.update({'owner': settings.server.admin_username, 'owner-type': 'User', 'id': '1'})
    result_info = Host.info(options={'id': '1', 'fields': 'Additional info'})
    assert result_info['additional-info']['owner-id'] in [result['id'] for result in result_list]


# -------------------------- HOST PARAMETER SCENARIOS -------------------------
@pytest.mark.host_parameter
@pytest.mark.tier1
def test_positive_parameter_crud(function_make_host):
    """Add, update and remove host parameter with valid name.

    :id: 76034424-cf18-4ced-916b-ee9798c311bc

    :expectedresults: Host parameter was successfully added, updated and
        removed.

    :CaseImportance: Critical
    """
    name = next(iter(valid_data_list()))
    value = valid_data_list()[name]
    Host.set_parameter({'host-id': function_make_host['id'], 'name': name, 'value': value})
    host = Host.info({'id': function_make_host['id']})
    assert name in host['parameters'].keys()
    assert value == host['parameters'][name]

    new_value = valid_data_list()[name]
    Host.set_parameter({'host-id': host['id'], 'name': name, 'value': new_value})
    host = Host.info({'id': host['id']})
    assert name in host['parameters'].keys()
    assert new_value == host['parameters'][name]

    Host.delete_parameter({'host-id': host['id'], 'name': name})
    host = Host.info({'id': host['id']})
    assert name not in host['parameters'].keys()


@pytest.mark.host_parameter
@pytest.mark.tier1
def test_negative_add_parameter(function_make_host):
    """Try to add host parameter with different invalid names.

    :id: 473f8c3f-b66e-4526-88af-e139cc3dabcb

    :expectedresults: Host parameter was not added.


    :CaseImportance: Critical
    """
    name = gen_choice(invalid_values_list()).lower()
    with pytest.raises(CLIReturnCodeError):
        Host.set_parameter(
            {
                'host-id': function_make_host['id'],
                'name': name,
                'value': gen_string('alphanumeric'),
            }
        )
    host = Host.info({'id': function_make_host['id']})
    assert name not in host['parameters'].keys()


@pytest.mark.host_parameter
@pytest.mark.tier2
def test_negative_view_parameter_by_non_admin_user(function_make_host, function_make_user):
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
    Host.set_parameter(
        {'host-id': function_make_host['id'], 'name': param_name, 'value': param_value}
    )
    host = Host.info({'id': function_make_host['id']})
    assert host['parameters'][param_name] == param_value
    role = make_role()
    add_role_permissions(
        role['id'],
        resource_permissions={
            'Host': {'permissions': ['view_hosts']},
            'Organization': {'permissions': ['view_organizations']},
        },
    )
    User.add_role({'id': function_make_user['user']['id'], 'role-id': role['id']})
    host = Host.with_user(
        username=function_make_user['user']['login'], password=function_make_user['password']
    ).info({'id': host['id']})
    assert not host.get('parameters')


@pytest.mark.host_parameter
@pytest.mark.tier2
def test_positive_view_parameter_by_non_admin_user(function_make_host, function_make_user):
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
    Host.set_parameter(
        {'host-id': function_make_host['id'], 'name': param_name, 'value': param_value}
    )
    host = Host.info({'id': function_make_host['id']})
    assert host['parameters'][param_name] == param_value
    role = make_role()
    add_role_permissions(
        role['id'],
        resource_permissions={
            'Host': {'permissions': ['view_hosts']},
            'Organization': {'permissions': ['view_organizations']},
            'Parameter': {'permissions': ['view_params']},
        },
    )
    User.add_role({'id': function_make_user['user']['id'], 'role-id': role['id']})
    host = Host.with_user(
        username=function_make_user['user']['login'], password=function_make_user['password']
    ).info({'id': host['id']})
    assert param_name in host['parameters']
    assert host['parameters'][param_name] == param_value


@pytest.mark.host_parameter
@pytest.mark.tier2
def test_negative_edit_parameter_by_non_admin_user(function_make_host, function_make_user):
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
    Host.set_parameter(
        {'host-id': function_make_host['id'], 'name': param_name, 'value': param_value}
    )
    host = Host.info({'id': function_make_host['id']})
    assert host['parameters'][param_name] == param_value
    role = make_role()
    add_role_permissions(
        role['id'],
        resource_permissions={
            'Host': {'permissions': ['view_hosts']},
            'Organization': {'permissions': ['view_organizations']},
            'Parameter': {'permissions': ['view_params']},
        },
    )
    User.add_role({'id': function_make_user['user']['id'], 'role-id': role['id']})
    param_new_value = gen_string('alphanumeric')
    with pytest.raises(CLIReturnCodeError):

        Host.with_user(
            username=function_make_user['user']['login'], password=function_make_user['password']
        ).set_parameter(
            {'host-id': function_make_host['id'], 'name': param_name, 'value': param_new_value}
        )
    host = Host.info({'id': function_make_host['id']})
    assert host['parameters'][param_name] == param_value


@pytest.mark.host_parameter
@pytest.mark.tier2
def test_positive_set_multi_line_and_with_spaces_parameter_value(function_make_host):
    """Check that host parameter value with multi-line and spaces is
    correctly restored from yaml format

    :id: 776feffd-1b46-46e9-925d-4739194c15cc

    :customerscenario: true

    :expectedresults: host parameter value is the same when restored
        from yaml format

    :BZ: 1315282

    :CaseLevel: Integration
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
    response = Host.info(
        {'id': function_make_host['id']}, output_format='yaml', return_raw_response=True
    )
    assert response.return_code == 0
    yaml_content = yaml.load('\n'.join(response.stdout))
    host_initial_params = yaml_content.get('Parameters')
    # set parameter
    Host.set_parameter(
        {'host-id': function_make_host['id'], 'name': param_name, 'value': param_value}
    )
    response = Host.info(
        {'id': function_make_host['id']}, output_format='yaml', return_raw_response=True
    )
    assert response.return_code == 0
    yaml_content = yaml.load('\n'.join(response.stdout))
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

    :CaseLevel: System
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

    :CaseLevel: System
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

    :CaseLevel: System
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

    :CaseLevel: System
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

    :CaseLevel: System
    """


# ------------------------ HOST SUBSCRIPTION SUBCOMMAND FIXTURES AND CLASS -----------------------
@skip_if_not_set('fake_manifest')
@pytest.fixture(scope="module")
def host_subscription(module_cv, module_lce, module_org):
    activation_key = make_activation_key(
        {'lifecycle-environment-id': module_lce.id, 'organization-id': module_org.id}
    )

    subscription_name = SATELLITE_SUBSCRIPTION_NAME
    # create a satellite tools repository content
    setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': activation_key['id'],
            'subscription': subscription_name,
        },
        force_use_cdn=True,
    )
    org_subscriptions = Subscription.list({'organization-id': module_org.id})
    default_subscription_id = None
    repository_id = REPOS['rhst7']['id']
    for org_subscription in org_subscriptions:
        if org_subscription['name'] == subscription_name:
            default_subscription_id = org_subscription['id']
            break
    # create a new lce for hosts subscription
    hosts_env = make_lifecycle_environment({'organization-id': module_org.id})
    # refresh content view data
    content_view = ContentView.info({'id': module_cv.id})
    content_view_version = content_view['versions'][-1]
    ContentView.version_promote(
        {
            'id': content_view_version['id'],
            'organization-id': module_org.id,
            'to-lifecycle-environment-id': hosts_env['id'],
        }
    )
    return {
        'ak': activation_key,
        'cv': content_view,
        'default_subscription_id': default_subscription_id,
        'hosts_env': hosts_env,
        'lce': module_lce,
        'org': module_org,
        'repository_id': repository_id,
        'subscription_name': subscription_name,
    }


@skip_if_not_set('clients')
@pytest.fixture(scope="function")
def host_subscription_client():
    client = VirtualMachine(distro=DISTRO_RHEL7)
    client.create()
    client.install_katello_ca()
    yield client
    vm_cleanup(client)


@pytest.fixture(scope="module")
def module_host_subscription(host_subscription):
    yield HostSubscription(host_subscription)


@skip_if_not_set('clients')
@pytest.mark.run_in_one_thread
class HostSubscription:
    def __init__(self, host_subscription):
        self.ak = host_subscription['ak']
        self.content_view = host_subscription['cv']
        self.default_subscription_id = host_subscription['default_subscription_id']
        self.hosts_env = host_subscription['hosts_env']
        self.lce = host_subscription['lce']
        self.org = host_subscription['org']
        self.repository_id = host_subscription['repository_id']
        self.subscription_name = host_subscription['subscription_name']
        self.client = None

    def set_client(self, client):
        self.client = client

    def get_client(self):
        return self.client

    def _register_client(
        self,
        activation_key=None,
        lce=False,
        enable_repo=False,
        auto_attach=False,
    ):
        """Register the client as a content host consumer

        :param activation_key: activation key if registration with activation
            key
        :param lce: boolean to indicate whether the registration should be made
            by environment
        :param enable_repo: boolean to indicate whether to enable repository
        :param auto_attach: boolean to indicate whether to register with
            auto-attach option, in case of registration with activation key a
            command is launched
        :return: the registration result
        """

        if activation_key is None:
            activation_key = self.ak

        if lce:
            result = self.client.register_contenthost(
                self.org.name,
                lce='{}/{}'.format(self.hosts_env['name'], self.content_view['name']),
                auto_attach=auto_attach,
            )
        else:
            result = self.client.register_contenthost(
                self.org.name, activation_key=activation_key['name']
            )
            if auto_attach and self.client.subscribed:
                result = self.client.run('subscription-manager attach --auto')

        if self.client.subscribed and enable_repo:
            self.client.enable_repo(self.repository_id)

        return result

    def _client_enable_repo(self):
        """Enable the client default repository"""
        result = self.client.run(f'subscription-manager repos --enable {self.repository_id}')
        return result

    def _make_activation_key(self, add_subscription=False):
        """Create a new activation key

        :param add_subscription: boolean to indicate whether to add the default
            subscription to the created activation key
        :return: the created activation key
        """
        activation_key = make_activation_key(
            {
                'organization-id': self.org.id,
                'content-view-id': self.content_view['id'],
                'lifecycle-environment-id': self.hosts_env['id'],
            }
        )
        ActivationKey.update(
            {'organization-id': self.org.id, 'id': activation_key['id'], 'auto-attach': 0}
        )
        if add_subscription:
            ActivationKey.add_subscription(
                {
                    'organization-id': self.org.id,
                    'id': activation_key['id'],
                    'subscription-id': self.default_subscription_id,
                }
            )
        return activation_key

    def _host_subscription_register(self):
        """Register the subscription of client as a content host consumer"""
        Host.subscription_register(
            {
                'organization-id': self.org.id,
                'content-view-id': self.content_view['id'],
                'lifecycle-environment-id': self.hosts_env['id'],
                'name': self.client.hostname,
            }
        )


# -------------------------- HOST SUBSCRIPTION SUBCOMMAND SCENARIOS -------------------------
@pytest.mark.host_subscription
@pytest.mark.tier3
def test_positive_register(module_host_subscription, host_subscription_client):
    """Attempt to register a host

    :id: b1c601ee-4def-42ce-b353-fc2657237533

    :expectedresults: host successfully registered

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    activation_key = module_host_subscription._make_activation_key(add_subscription=False)
    hosts = Host.list(
        {
            'organization-id': module_host_subscription.org.id,
            'search': module_host_subscription.client.hostname,
        }
    )
    assert len(hosts) == 0
    module_host_subscription._host_subscription_register()
    hosts = Host.list(
        {
            'organization-id': module_host_subscription.org.id,
            'search': module_host_subscription.client.hostname,
        }
    )
    assert len(hosts) > 0
    host = Host.info({'id': hosts[0]['id']})
    assert host['name'] == module_host_subscription.client.hostname
    # note: when not registered the following command lead to exception,
    # see unregister
    host_subscriptions = ActivationKey.subscriptions(
        {
            'organization-id': module_host_subscription.org.id,
            'id': activation_key['id'],
            'host-id': host['id'],
        },
        output_format='json',
    )
    assert len(host_subscriptions) == 0


@pytest.mark.host_subscription
@pytest.mark.tier3
def test_positive_attach(module_host_subscription, host_subscription_client):
    """Attempt to attach a subscription to host

    :id: d5825bfb-59e3-4d49-8df8-902cc7a9d66b

    :BZ: 1199515

    :expectedresults: host successfully subscribed, subscription repository
        enabled, and repository package installed

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    # create an activation key without subscriptions
    activation_key = module_host_subscription._make_activation_key(add_subscription=False)
    # register the client host
    module_host_subscription._host_subscription_register()
    host = Host.info({'name': module_host_subscription.client.hostname})
    module_host_subscription._register_client(activation_key=activation_key)
    assert module_host_subscription.client.subscribed
    # attach the subscription to host
    Host.subscription_attach(
        {
            'host-id': host['id'],
            'subscription-id': module_host_subscription.default_subscription_id,
        }
    )
    result = module_host_subscription._client_enable_repo()
    assert result.return_code == 0
    # ensure that katello agent can be installed
    try:
        module_host_subscription.client.install_katello_agent()
    except VirtualMachineError:
        pytest.fail("VirtualMachineError raised unexpectedly!")


@pytest.mark.host_subscription
@pytest.mark.tier3
def test_positive_attach_with_lce(module_host_subscription, host_subscription_client):
    """Attempt to attach a subscription to host, registered by lce

    :id: a362b959-9dde-4d1b-ae62-136c6ef943ba

    :BZ: 1199515

    :expectedresults: host successfully subscribed, subscription
        repository enabled, and repository package installed

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    module_host_subscription._register_client(lce=True, auto_attach=True)
    assert module_host_subscription.client.subscribed
    host = Host.info({'name': module_host_subscription.client.hostname})
    Host.subscription_attach(
        {
            'host-id': host['id'],
            'subscription-id': module_host_subscription.default_subscription_id,
        }
    )
    result = module_host_subscription._client_enable_repo()
    assert result.return_code == 0
    # ensure that katello agent can be installed
    try:
        module_host_subscription.client.install_katello_agent()
    except VirtualMachineError:
        pytest.fail("VirtualMachineError raised unexpectedly!")


@pytest.mark.host_subscription
@pytest.mark.tier3
def test_negative_without_attach(module_host_subscription, host_subscription_client):
    """Register content host from satellite, register client to uuid
    of that content host, as there was no attach on the client,
    Test if the list of the repository subscriptions is empty

    :id: 54a2c95f-be08-4353-a96c-4bc4d96ad03d

    :expectedresults: repository list is empty

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    module_host_subscription._host_subscription_register()
    host = Host.info({'name': module_host_subscription.client.hostname})
    module_host_subscription.client.register_contenthost(
        module_host_subscription.org.name,
        consumerid=host['subscription-information']['uuid'],
        force=False,
    )
    client_status = module_host_subscription.client.subscription_manager_status()
    assert SM_OVERALL_STATUS['current'] in client_status.stdout
    repo_list = module_host_subscription.client.subscription_manager_list_repos()
    assert NO_REPOS_AVAILABLE in repo_list.stdout


@pytest.mark.host_subscription
@pytest.mark.tier3
def test_negative_without_attach_with_lce(module_host_subscription, host_subscription_client):
    """Attempt to enable a repository of a subscription that was not
    attached to a host
    This test is not using the host_subscription entities except
    subscription_name and repository_id

    :id: fc469e70-a7cb-4fca-b0ea-3c9e3dfff849

    :expectedresults: repository not enabled on host

    :CaseLevel: System
    """
    # Setup as in host_subscription
    module_host_subscription.set_client(host_subscription_client)
    org = make_org()
    lce_env = make_lifecycle_environment({'organization-id': org['id']})
    content_view = make_content_view({'organization-id': org['id']})
    activation_key = make_activation_key(
        {'lifecycle-environment-id': lce_env['id'], 'organization-id': org['id']}
    )
    setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org['id'],
            'content-view-id': content_view['id'],
            'lifecycle-environment-id': lce_env['id'],
            'activationkey-id': activation_key['id'],
            'subscription': module_host_subscription.subscription_name,
        },
        force_use_cdn=True,
    )
    hosts_env = make_lifecycle_environment({'organization-id': org['id']})
    # refresh content view data
    content_view = ContentView.info({'id': content_view['id']})
    content_view_version = content_view['versions'][-1]
    ContentView.version_promote(
        {
            'id': content_view_version['id'],
            'organization-id': org['id'],
            'to-lifecycle-environment-id': hosts_env['id'],
        }
    )

    # register client
    module_host_subscription.client.register_contenthost(
        org['name'],
        lce='{}/{}'.format(hosts_env['name'], content_view['name']),
        auto_attach=False,
    )

    # disable repository set to
    default_cv = ContentView.info({'name': DEFAULT_CV, 'organization-id': org['id']})
    default_lce = LifecycleEnvironment.info({'name': ENVIRONMENT, 'organization-id': org['id']})
    ContentView.remove(
        {
            'id': content_view['id'],
            'lifecycle-environments': ",".join([ENVIRONMENT, lce_env['name'], hosts_env['name']]),
            'organization-id': org['id'],
            'system-content-view-id': default_cv['id'],
            'system-environment-id': default_lce['id'],
            'key-content-view-id': default_cv['id'],
            'key-environment-id': default_lce['id'],
        }
    )
    ContentView.delete({'id': content_view['id']})
    RepositorySet.disable(
        {
            'basearch': 'x86_64',
            'name': REPOSET['rhst7'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
        }
    )

    # get list of available subscriptions which are matched with default subscription
    subscriptions = module_host_subscription.client.run(
        'subscription-manager list --available --matches "%s" --pool-only'
        % DEFAULT_SUBSCRIPTION_NAME
    )
    pool_id = subscriptions.stdout[0]
    # attach to plain RHEL subsctiption
    module_host_subscription.client.run('subscription-manager attach --pool "%s"' % pool_id)
    assert module_host_subscription.client.subscribed
    result = module_host_subscription._client_enable_repo()
    assert result.return_code != 0


@pytest.mark.host_subscription
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_remove(module_host_subscription, host_subscription_client):
    """Attempt to remove a subscription from content host

    :id: 3833c349-1f5b-41ac-bbac-2c1f33232d76

    :expectedresults: subscription successfully removed from host

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    activation_key = module_host_subscription._make_activation_key(add_subscription=True)
    module_host_subscription._host_subscription_register()
    host = Host.info({'name': module_host_subscription.client.hostname})
    host_subscriptions = ActivationKey.subscriptions(
        {
            'organization-id': module_host_subscription.org.id,
            'id': activation_key['id'],
            'host-id': host['id'],
        },
        output_format='json',
    )
    assert module_host_subscription.subscription_name not in [
        sub['name'] for sub in host_subscriptions
    ]
    module_host_subscription._register_client(activation_key=activation_key)
    Host.subscription_attach(
        {
            'host-id': host['id'],
            'subscription-id': module_host_subscription.default_subscription_id,
        }
    )
    host_subscriptions = ActivationKey.subscriptions(
        {
            'organization-id': module_host_subscription.org.id,
            'id': activation_key['id'],
            'host-id': host['id'],
        },
        output_format='json',
    )
    assert module_host_subscription.subscription_name in [
        sub['name'] for sub in host_subscriptions
    ]
    Host.subscription_remove(
        {
            'host-id': host['id'],
            'subscription-id': module_host_subscription.default_subscription_id,
        }
    )
    host_subscriptions = ActivationKey.subscriptions(
        {
            'organization-id': module_host_subscription.org.id,
            'id': activation_key['id'],
            'host-id': host['id'],
        },
        output_format='json',
    )
    assert module_host_subscription.subscription_name not in [
        sub['name'] for sub in host_subscriptions
    ]


@pytest.mark.host_subscription
@pytest.mark.tier3
def test_positive_auto_attach(module_host_subscription, host_subscription_client):
    """Attempt to auto attach a subscription to content host

    :id: e3eebf72-d512-4892-828b-70165ea4b129

    :expectedresults: host successfully subscribed, subscription
        repository enabled, and repository package installed

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    activation_key = module_host_subscription._make_activation_key(add_subscription=True)
    module_host_subscription._host_subscription_register()
    host = Host.info({'name': module_host_subscription.client.hostname})
    module_host_subscription._register_client(activation_key=activation_key)
    Host.subscription_auto_attach({'host-id': host['id']})
    result = module_host_subscription._client_enable_repo()
    assert result.return_code == 0
    # ensure that katello agent can be installed
    try:
        module_host_subscription.client.install_katello_agent()
    except VirtualMachineError:
        pytest.fail("VirtualMachineError raised unexpectedly!")


@pytest.mark.host_subscription
@pytest.mark.tier3
def test_positive_unregister_host_subscription(module_host_subscription, host_subscription_client):
    """Attempt to unregister host subscription

    :id: 608f5b6d-4688-478e-8be8-e946771d5247

    :expectedresults: host subscription is unregistered

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    # register the host client
    activation_key = module_host_subscription._make_activation_key(add_subscription=True)
    module_host_subscription._register_client(
        activation_key=activation_key, enable_repo=True, auto_attach=True
    )
    assert module_host_subscription.client.subscribed
    host = Host.info({'name': module_host_subscription.client.hostname})
    host_subscriptions = ActivationKey.subscriptions(
        {
            'organization-id': module_host_subscription.org.id,
            'id': activation_key['id'],
            'host-id': host['id'],
        },
        output_format='json',
    )
    assert len(host_subscriptions) > 0
    Host.subscription_unregister({'host': module_host_subscription.client.hostname})
    with pytest.raises(CLIReturnCodeError):
        # raise error that the host was not registered by
        # subscription-manager register
        ActivationKey.subscriptions(
            {
                'organization-id': module_host_subscription.org.id,
                'id': activation_key['id'],
                'host-id': host['id'],
            }
        )


@pytest.mark.host_subscription
@pytest.mark.tier3
def test_syspurpose_end_to_end(module_host_subscription, host_subscription_client):
    """Create a host with system purpose values set by activation key.

    :id: b88e9b6c-2348-49ce-b5e9-a2b9f0abed3f

    :expectedresults: host is registered and system purpose values are correct.

    :CaseLevel: System
    """
    module_host_subscription.set_client(host_subscription_client)
    # Create an activation key with test values
    purpose_addons = "test-addon1, test-addon2"
    activation_key = make_activation_key(
        {
            'purpose-addons': purpose_addons,
            'purpose-role': "test-role",
            'purpose-usage': "test-usage",
            'service-level': "Self-Support",
            'lifecycle-environment-id': module_host_subscription.lce.id,
            'organization-id': module_host_subscription.org.id,
            'content-view-id': module_host_subscription.content_view['id'],
        }
    )
    ActivationKey.add_subscription(
        {
            'organization-id': module_host_subscription.org.id,
            'id': activation_key['id'],
            'subscription-id': module_host_subscription.default_subscription_id,
        }
    )
    # Register a host using the activation key
    module_host_subscription._register_client(
        activation_key=activation_key, enable_repo=True, auto_attach=True
    )
    assert module_host_subscription.client.subscribed
    host = Host.info({'name': module_host_subscription.client.hostname})
    # Assert system purpose values are set in the host as expected
    assert host['subscription-information']['system-purpose']['purpose-addons'] == purpose_addons
    assert host['subscription-information']['system-purpose']['purpose-role'] == "test-role"
    assert host['subscription-information']['system-purpose']['purpose-usage'] == "test-usage"
    assert host['subscription-information']['system-purpose']['service-level'] == "Self-Support"
    # Change system purpose values in the host
    Host.update(
        {
            'purpose-addons': "test-addon3",
            'purpose-role': "test-role2",
            'purpose-usage': "test-usage2",
            'service-level': "Self-Support2",
            'id': host['id'],
        }
    )
    host = Host.info({'id': host['id']})
    # Assert system purpose values have been updated in the host as expected
    assert host['subscription-information']['system-purpose']['purpose-addons'] == "test-addon3"
    assert host['subscription-information']['system-purpose']['purpose-role'] == "test-role2"
    assert host['subscription-information']['system-purpose']['purpose-usage'] == "test-usage2"
    assert host['subscription-information']['system-purpose']['service-level'] == "Self-Support2"
    host_subscriptions = ActivationKey.subscriptions(
        {
            'organization-id': module_host_subscription.org.id,
            'id': activation_key['id'],
            'host-id': host['id'],
        },
        output_format='json',
    )
    assert len(host_subscriptions) > 0
    assert host_subscriptions[0]['name'] == module_host_subscription.subscription_name
    # Unregister host
    Host.subscription_unregister({'host': module_host_subscription.client.hostname})
    with pytest.raises(CLIReturnCodeError):
        # raise error that the host was not registered by
        # subscription-manager register
        ActivationKey.subscriptions(
            {
                'organization-id': module_host_subscription.org.id,
                'id': activation_key['id'],
                'host-id': host['id'],
            }
        )


# -------------------------- HOST ERRATA SUBCOMMAND SCENARIOS -------------------------
@pytest.mark.tier1
def test_positive_errata_list_of_sat_server():
    """Check if errata list doesn't raise exception. Check BZ for details.

    :id: 6b22f0c0-9c4b-11e6-ab93-68f72889dc7f

    :expectedresults: Satellite host errata list not failing

    :BZ: 1351040

    :CaseImportance: Critical
    """
    hostname = ssh.command('hostname').stdout[0]
    host = Host.info({'name': hostname})
    assert isinstance(Host.errata_list({'host-id': host['id']}), list)


# -------------------------- HOST ENC SUBCOMMAND SCENARIOS -------------------------
@pytest.mark.tier1
def test_positive_dump_enc_yaml():
    """Dump host's ENC YAML. Check BZ for details.

    :id: 50bf2530-788c-4710-a382-d034d73d5d4d

    :expectedresults: Ensure that enc-dump does not fail

    :customerscenario: true

    :BZ: 1372731

    :CaseImportance: Critical
    """
    hostname = ssh.command('hostname').stdout[0]
    assert isinstance(Host.enc_dump({'name': hostname}), list)
