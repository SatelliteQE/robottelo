"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from robottelo.config import settings
from robottelo.decorators import (
    fixture,
    tier2,
)

from .utils import (
    deploy_configure_by_command,
    deploy_configure_by_script,
    get_configure_id,
    get_configure_file,
    get_configure_option,
    get_configure_command,
    VIRTWHO_SYSCONFIG,
)


@fixture(scope='module')
def form_data():
    hypervisor_type = settings.virtwho.hypervisor_type
    hypervisor_server = settings.virtwho.hypervisor_server
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': hypervisor_type,
        'hypervisor_content.server': hypervisor_server,
    }
    if hypervisor_type == 'libvirt':
        form['hypervisor_content.username'] = (
            settings.virtwho.hypervisor_username)
    elif hypervisor_type == 'kubevirt':
        form['hypervisor_content.kubeconfig'] = (
            settings.virtwho.hypervisor_config_file)
    else:
        form['hypervisor_content.username'] = (
            settings.virtwho.hypervisor_username)
        form['hypervisor_content.password'] = (
            settings.virtwho.hypervisor_password)
    return form


@tier2
def test_positive_deploy_configure_by_id(session, form_data):
    """ Verify configure created and deployed with id.

    :id: c5385f69-aa7e-4fc0-b126-08aacb14bfb8

    :expectedresults:
        1. Config can be created and deployed by command
        2. No error msg in /var/log/rhsm/rhsm.log
        3. Report is sent to satellite
        4. Virtual sku can be generated and attached
        5. Config can be deleted

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        values = session.virtwho_configure.read(name)
        command = values['deploy']['command']
        hypervisor_name, guest_name = deploy_configure_by_command(command, debug=True)
        assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
        hypervisor_display_name = session.contenthost.search(hypervisor_name)[0]['Name']
        vdc_physical = 'product_id = {} and type=NORMAL'.format(
            settings.virtwho.sku_vdc_physical)
        vdc_virtual = 'product_id = {} and type=STACK_DERIVED'.format(
            settings.virtwho.sku_vdc_physical)
        session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
        assert session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
        session.contenthost.add_subscription(guest_name, vdc_virtual)
        assert session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_deploy_configure_by_script(session, form_data):
    """ Verify configure created and deployed with script.

    :id: cae3671c-a583-4e67-a0de-95d191d2174c

    :expectedresults:
        1. Config can be created and deployed by script
        2. No error msg in /var/log/rhsm/rhsm.log
        3. Report is sent to satellite
        4. Virtual sku can be generated and attached
        5. Config can be deleted

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        values = session.virtwho_configure.read(name)
        script = values['deploy']['script']
        hypervisor_name, guest_name = deploy_configure_by_script(script, debug=True)
        assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
        hypervisor_display_name = session.contenthost.search(hypervisor_name)[0]['Name']
        vdc_physical = 'product_id = {} and type=NORMAL'.format(
            settings.virtwho.sku_vdc_physical)
        vdc_virtual = 'product_id = {} and type=STACK_DERIVED'.format(
            settings.virtwho.sku_vdc_physical)
        session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
        assert session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
        session.contenthost.add_subscription(guest_name, vdc_virtual)
        assert session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_debug_option(session, form_data):
    """ Verify debug checkbox and the value changes of VIRTWHO_DEBUG

    :id: d6f9940f-c003-4099-97bf-4d8820ab710e

    :expectedresults:
        1. if debug is checked, VIRTWHO_DEBUG=1 in /etc/sysconfig/virt-who
        2. if debug is unchecked, VIRTWHO_DEBUG=0 in /etc/sysconfig/virt-who

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id)
        deploy_configure_by_command(config_command)
        assert get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG) == '1'
        session.virtwho_configure.edit(name, {'debug': False})
        results = session.virtwho_configure.read(name)
        assert results['overview']['debug'] is False
        deploy_configure_by_command(config_command)
        assert get_configure_option('VIRTWHO_DEBUG', VIRTWHO_SYSCONFIG) == '0'
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_interval_option(session, form_data):
    """ Verify interval dropdown options and the value changes of VIRTWHO_INTERVAL.

    :id: 412a01eb-ae9c-4b23-aeb5-2595873b27e2

    :expectedresults:
        VIRTWHO_INTERVAL can be changed in /etc/sysconfig/virt-who if the
        dropdown option is selected to Every 2/4/8/12/24 hours, Every 2/3 days.

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id)
        intervals = {
            'Every hour': '3600',
            'Every 2 hours': '7200',
            'Every 4 hours': '14400',
            'Every 8 hours': '28800',
            'Every 12 hours': '43200',
            'Every 24 hours': '86400',
            'Every 2 days':  '172800',
            'Every 3 days':  '259200',
        }
        for option, value in sorted(intervals.items(), key=lambda item: int(item[1])):
            session.virtwho_configure.edit(name, {'interval': option})
            results = session.virtwho_configure.read(name)
            assert results['overview']['interval'] == option
            deploy_configure_by_command(config_command)
            assert get_configure_option('VIRTWHO_INTERVAL', VIRTWHO_SYSCONFIG) == value
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_hypervisor_id_option(session, form_data):
    """ Verify Hypervisor ID dropdown options.

    :id: dd490f5f-8371-4be6-81d5-a02bbff43de8

    :expectedresults:
        hypervisor_id can be changed in virt-who-config-{}.conf if the
        dropdown option is selected to uuid/hwuuid/hostname.

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id)
        config_file = get_configure_file(config_id)
        values = ['uuid', 'hostname']
        if form_data['hypervisor_type'] in ('esx', 'rhevm'):
            values.append('hwuuid')
        for value in values:
            session.virtwho_configure.edit(name, {'hypervisor_id': value})
            results = session.virtwho_configure.read(name)
            assert results['overview']['hypervisor_id'] == value
            deploy_configure_by_command(config_command)
            assert get_configure_option('hypervisor_id', config_file) == value
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_filtering_option(session, form_data):
    """ Verify Filtering dropdown options.

    :id: 107c5644-cbf4-48b6-8975-718b661177b0

    :expectedresults:
        1. if filtering is selected to Whitelist, 'Filter hosts' can be set.
        2. if filtering is selected to Blacklist, 'Exclude hosts' can be set.

    :CaseLevel: Integration

    :CaseImportance: Medium

    :BZ: 1735670
    """
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id)
        config_file = get_configure_file(config_id)
        hypervisor_type = form_data['hypervisor_type']
        regex = '.*redhat.com'
        whitelist = {
            'filtering': 'Whitelist',
            'filtering_content.filter_hosts': regex,
        }
        blacklist = {
            'filtering': 'Blacklist',
            'filtering_content.exclude_hosts': regex,
        }
        if hypervisor_type == 'esx':
            whitelist['filtering_content.filter_host_parents'] = regex
            blacklist['filtering_content.exclude_host_parents'] = regex
        # Update Whitelist and check the result
        session.virtwho_configure.edit(name, whitelist)
        results = session.virtwho_configure.read(name)
        assert results['overview']['filter_hosts'] == regex
        if hypervisor_type == 'esx':
            assert results['overview']['filter_host_parents'] == regex
        deploy_configure_by_command(config_command)
        assert regex == get_configure_option('filter_hosts', config_file)
        if hypervisor_type == 'esx':
            assert regex == get_configure_option('filter_host_parents', config_file)
        # Update Blacklist and check the result
        session.virtwho_configure.edit(name, blacklist)
        results = session.virtwho_configure.read(name)
        assert results['overview']['exclude_hosts'] == regex
        if hypervisor_type == 'esx':
            assert results['overview']['exclude_host_parents'] == regex
        deploy_configure_by_command(config_command)
        assert regex == get_configure_option('exclude_hosts', config_file)
        if hypervisor_type == 'esx':
            assert regex == get_configure_option('exclude_host_parents', config_file)
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_proxy_option(session, form_data):
    """ Verify 'HTTP Proxy' and 'Ignore Proxy' options.

    :id: 59b70a9e-59b1-494c-8668-d824ace8efbf

    :expectedresults:
        http_proxy ad NO_PROXY will be setting in /etc/sysconfig/virt-who.

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id)
        http_proxy = 'test.rexample.com:3128'
        no_proxy = 'test.satellite.com'
        session.virtwho_configure.edit(name, {
            'proxy': http_proxy,
            'no_proxy': no_proxy,
        })
        results = session.virtwho_configure.read(name)
        assert results['overview']['proxy'] == http_proxy
        assert results['overview']['no_proxy'] == no_proxy
        deploy_configure_by_command(config_command)
        assert get_configure_option('http_proxy', VIRTWHO_SYSCONFIG) == http_proxy
        assert get_configure_option('NO_PROXY', VIRTWHO_SYSCONFIG) == no_proxy
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_virtwho_roles(session):
    """ Verify the default roles for virtwho configure

    :id: 69e30452-a655-45e3-9651-a32bf229f284

    :expectedresults:
        'Virt-who Manager', 'Virt-who Reporter', 'Virt-who Viewer' existing

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    roles = {
        'Virt-who Manager': {
            'Satellite virt who configure/config': [
                'view_virt_who_config',
                'create_virt_who_config',
                'edit_virt_who_config',
                'destroy_virt_who_config']
        },
        'Virt-who Reporter': {
            'Host': ['create_hosts', 'edit_hosts'],
            'Lifecycle Environment': ['view_lifecycle_environments'],
            '(Miscellaneous)': ['my_organizations']
        },
        'Virt-who Viewer': {
            'Satellite virt who configure/config': ['view_virt_who_config']
        }
    }
    with session:
        for role_name, role_filters in roles.items():
            assert session.role.search(role_name)[0]['Name'] == role_name
            assigned_permissions = session.filter.read_permissions(role_name)
            assert sorted(assigned_permissions) == sorted(role_filters)


@tier2
def test_positive_virtwho_configs_widget(session, form_data):
    """Check if Virt-who Configurations Status Widget is working in the Dashboard UI

    :id: 6bed6d55-2bd5-4438-9f72-d48e78566789

    :Steps:

        1. Create a Virt-who Configuration
        2. Navigate Monitor -> Dashboard
        3. Review the Virt-who Configurations Status widget

    :expectedresults: The widget is updated with all details.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    org_name = gen_string('alpha')
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.organization.create({'name': org_name})
        session.organization.select(org_name)
        session.virtwho_configure.create(form_data)
        expected_values = [
            {'Configuration Status': 'No Reports', 'Count': '1'},
            {'Configuration Status': 'No Change', 'Count': '0'},
            {'Configuration Status': 'OK', 'Count': '0'},
            {'Configuration Status': 'Total Configurations', 'Count': '1'}
        ]
        values = session.dashboard.read('VirtWhoConfigStatus')
        assert values['config_status'] == expected_values
        assert values['latest_config'] == 'No configuration found'
        # Check the 'Status' changed after deployed the virt-who config
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, org_name)
        deploy_configure_by_command(config_command)
        assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
        expected_values = [
            {'Configuration Status': 'No Reports', 'Count': '0'},
            {'Configuration Status': 'No Change', 'Count': '0'},
            {'Configuration Status': 'OK', 'Count': '1'},
            {'Configuration Status': 'Total Configurations', 'Count': '1'}
        ]
        values = session.dashboard.read('VirtWhoConfigStatus')
        assert values['config_status'] == expected_values
        assert values['latest_config'] == 'No configuration found'
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)
        session.organization.select("Default Organization")
        session.organization.delete(org_name)
