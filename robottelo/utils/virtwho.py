"""Utility module to handle the virtwho configure UI/CLI/API testing"""
import json
import re
import uuid

import requests
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url
from nailgun import entities
from wait_for import wait_for

from robottelo import ssh
from robottelo.cli.base import Base
from robottelo.cli.host import Host
from robottelo.cli.virt_who_config import VirtWhoConfig
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG

ETC_VIRTWHO_CONFIG = "/etc/virt-who.conf"


class VirtWhoError(Exception):
    """Exception raised for failed virtwho operations"""


def _parse_entry(entry):
    """Parse the string and return json format"""
    try:
        return json.loads(entry)
    except json.decoder.JSONDecodeError:
        return None


def get_system(system_type):
    """Return a dict account for ssh connect.

    :param str system_type: The type of the system, should be one of
        ('satellite', 'esx', 'xen', 'hyperv', 'rhevm', 'libvirt', 'kubevirt', 'ahv').
    :raises: VirtWhoError: If wrong ``system_type`` specified.
    """
    hypervisor_list = ['esx', 'xen', 'hyperv', 'rhevm', 'libvirt', 'kubevirt', 'ahv']
    system_type_list = ['satellite']
    system_type_list.extend(hypervisor_list)
    if system_type in hypervisor_list:
        return {
            'hostname': getattr(settings.virtwho, system_type).guest,
            'username': getattr(settings.virtwho, system_type).guest_username,
            'password': getattr(settings.virtwho, system_type).guest_password,
            'port': getattr(settings.virtwho, system_type).guest_port,
        }
    elif system_type == 'satellite':
        return {
            'hostname': settings.server.hostname,
            'username': settings.server.ssh_username,
            'password': settings.server.ssh_password,
        }
    else:
        raise VirtWhoError(
            f'"{system_type}" system type is not supported. Please use one of {system_type_list}'
        )


def get_guest_info(hypervisor_type):
    """Return the guest_name, guest_uuid"""
    _, guest_name = runcmd('hostname', system=get_system(hypervisor_type))
    _, guest_uuid = runcmd('dmidecode -s system-uuid', system=get_system(hypervisor_type))
    if not guest_uuid or not guest_name:
        raise VirtWhoError(f'Failed to get the guest info for {hypervisor_type}')
    # Different UUID for vcenter by dmidecode and vcenter MOB
    if hypervisor_type == 'esx':
        guest_uuid = guest_uuid.split('-')[-1]
    if hypervisor_type == 'hyperv':
        guest_uuid = guest_uuid.split('-')[-1].upper()
    return guest_name, guest_uuid


def runcmd(cmd, system=None, timeout=600000, output_format='base'):
    """Return the retcode and stdout.

    :param str cmd: The command line will be executed in the target system.
    :param dict system: the system account which ssh will connect to,
        it will connect to the satellite host if the system is None.
    :param int timeout: Time to wait for establish the connection.
    :param str output_format: base|json|csv|list
    """
    system = system or get_system('satellite')
    result = ssh.command(cmd, **system, timeout=timeout, output_format=output_format)
    return result.status, result.stdout.strip()


def register_system(system, activation_key=None, org='Default_Organization', env='Library'):
    """Return True if the system is registered to satellite successfully.

    :param dict system: system account used by ssh to connect and register.
    :param str activation_key: the activation key will be used to register.
    :param str org: Which organization will be used to register.
    :param str env: Which environment will be used to register.
    :raises: VirtWhoError: If failed to register the system.
    """
    runcmd('subscription-manager unregister', system)
    runcmd('subscription-manager clean', system)
    runcmd('rpm -qa | grep katello-ca-consumer | xargs rpm -e |sort', system)
    runcmd(
        'rpm -ihv http://{}/pub/katello-ca-consumer-latest.noarch.rpm'.format(
            settings.server.hostname
        ),
        system,
    )
    cmd = f'subscription-manager register --org={org} --environment={env} '
    if activation_key is not None:
        cmd += f'--activationkey={activation_key}'
    else:
        cmd += '--username={} --password={}'.format(
            settings.server.admin_username, settings.server.admin_password
        )
    ret, stdout = runcmd(cmd, system)
    if ret == 0 or "system has been registered" in stdout:
        return True
    else:
        raise VirtWhoError(f'Failed to register system: {system}')


def virtwho_cleanup():
    """Before running test cases, need to clean the environment.
    Do the following:
    1. stop virt-who service.
    2. kill all the virt-who pid
    3. clean rhsm.log message, make sure there is no old message exist.
    4. clean all the configure files in /etc/virt-who.d/
    """
    runcmd("systemctl stop virt-who")
    runcmd("pkill -9 virt-who")
    runcmd("rm -f /var/run/virt-who.pid")
    runcmd("rm -f /var/log/rhsm/rhsm.log")
    runcmd("rm -rf /etc/virt-who.d/*")
    runcmd("rm -rf /tmp/deploy_script.sh")


def get_virtwho_status():
    """Return the status of virt-who service, it will help us to know
    the virt-who configuration file is deployed or not.
    """
    _, logs = runcmd('cat /var/log/rhsm/rhsm.log')
    error = len(re.findall(r'\[.*ERROR.*\]', logs))
    ret, stdout = runcmd('systemctl status virt-who')
    running_stauts = ['is running', 'Active: active (running)']
    stopped_status = ['is stopped', 'Active: inactive (dead)']
    if ret != 0:
        return 'undefined'
    if error != 0:
        return 'logerror'
    if any(key in stdout for key in running_stauts):
        return 'running'
    elif any(key in stdout for key in stopped_status):
        return 'stopped'
    else:
        return 'undefined'


def get_configure_id(name):
    """Return the configure id by hammer.
    :param str name: the configure name you have created.
    :raises: VirtWhoError: If failed to get the configure info by hammer.
    """
    config = VirtWhoConfig.info({'name': name})
    if 'id' in config['general-information']:
        return config['general-information']['id']
    else:
        raise VirtWhoError(f"No configure id found for {name}")


def get_configure_command(config_id, org=DEFAULT_ORG):
    """Return the deploy command line based on configure id.
    :param str config_id: the unique id of the configure file you have created.
    :param str org: the satellite organization name.
    """
    username, password = Base._get_username_password()
    return "hammer -u {} -p {} virt-who-config deploy --id {} --organization '{}' ".format(
        username, password, config_id, org
    )


def get_configure_file(config_id):
    """Return the configuration file full name in /etc/virt-who.d
    :param str config_id: the unique id of the configuration file you have created.
    """
    return f"/etc/virt-who.d/virt-who-config-{config_id}.conf"


def get_configure_option(option, filename):
    """Return the option's value for the specific file.

    :param str option: the option name in the configuration file
    :param str filename: the configuration file, it could be:
        /etc/sysconfig/virt-who
        /etc/virt-who.d/virt-who-config-{}.conf
    :raises: VirtWhoError: If this option name not in the file.
    """
    cmd = f"grep -v '^#' {filename} | grep ^{option}"
    ret, stdout = runcmd(cmd)
    if ret == 0 and option in stdout:
        value = stdout.split('=')[1].strip()
        return value
    else:
        raise VirtWhoError(f"option {option} is not exist or not be enabled in {filename}")


def get_rhsm_log():
    """
    Return the content of log file /var/log/rhsm/rhsm.log
    """
    _, logs = runcmd('cat /var/log/rhsm/rhsm.log')
    return logs


def _get_hypervisor_mapping(hypervisor_type):
    """Analysing rhsm.log and get to know: what is the hypervisor_name
    for the specific guest.
    :param str logs: the output of rhsm.log.
    :param str hypervisor_type: esx, libvirt, rhevm, xen, libvirt, kubevirt, ahv
    :raises: VirtWhoError: If hypervisor_name is None.
    :return: hypervisor_name and guest_name
    """
    wait_for(
        lambda: 'Host-to-guest mapping being sent to' in get_rhsm_log(),
        timeout=10,
        delay=2,
    )
    logs = get_rhsm_log()
    mapping = list()
    entry = None
    guest_name, guest_uuid = get_guest_info(hypervisor_type)
    for line in logs.split('\n'):
        if not line:
            continue
        if line[0].isdigit():
            if entry:
                mapping.append(_parse_entry(entry))
            entry = '{'
            continue
        if entry:
            entry += line
    else:
        mapping.append(_parse_entry(entry))
    mapping = [_ for _ in mapping if _ is not None]
    # Always check the last json section to get the hypervisorId
    for item in mapping[-1]['hypervisors']:
        for guest in item['guestIds']:
            if guest_uuid in guest['guestId']:
                hypervisor_name = item['hypervisorId']['hypervisorId']
                break
    if hypervisor_name:
        return hypervisor_name, guest_name
    else:
        raise VirtWhoError(f"Failed to get the hypervisor_name for guest {guest_name}")


def deploy_validation(hypervisor_type):
    """Checkout the deploy result
    :param str hypervisor_type: esx, libvirt, rhevm, xen, libvirt, kubevirt, ahv
    :raises: VirtWhoError: If failed to start virt-who servcie.
    :ruturn: hypervisor_name and guest_name
    """
    status = get_virtwho_status()
    if status != 'running':
        raise VirtWhoError("Failed to start virt-who service")
    hypervisor_name, guest_name = _get_hypervisor_mapping(hypervisor_type)
    for host in Host.list({'search': hypervisor_name}):
        Host.delete({'id': host['id']})
    restart_virtwho_service()
    return hypervisor_name, guest_name


def deploy_configure_by_command(command, hypervisor_type, debug=False, org='Default_Organization'):
    """Deploy and run virt-who servcie by the hammer command.

    :param str command: get the command by UI/CLI/API, it should be like:
        `hammer virt-who-config deploy --id 1 --organization-id 1`
    :param str hypervisor_type: esx, libvirt, rhevm, xen, libvirt, kubevirt, ahv
    :param bool debug: if VIRTWHO_DEBUG=1, this option should be True.
    :param str org: Organization Label
    """
    virtwho_cleanup()
    guest_name, guest_uuid = get_guest_info(hypervisor_type)
    if Host.list({'search': guest_name}):
        Host.delete({'name': guest_name})
    register_system(get_system(hypervisor_type), org=org)
    ret, stdout = runcmd(command)
    if ret != 0 or 'Finished successfully' not in stdout:
        raise VirtWhoError(f"Failed to deploy configure by {command}")
    if debug:
        return deploy_validation(hypervisor_type)


def deploy_configure_by_script(
    script_content, hypervisor_type, debug=False, org='Default_Organization'
):
    """Deploy and run virt-who service by the shell script.
    :param str script_content: get the script by UI or API.
    :param str hypervisor_type: esx, libvirt, rhevm, xen, libvirt, kubevirt, ahv
    :param bool debug: if VIRTWHO_DEBUG=1, this option should be True.
    :param str org: Organization Label
    """
    script_filename = "/tmp/deploy_script.sh"
    script_content = script_content.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
    virtwho_cleanup()
    register_system(get_system(hypervisor_type), org=org)
    with open(script_filename, 'w') as fp:
        fp.write(script_content)
    ssh.get_client().put(script_filename)
    ret, stdout = runcmd(f'sh {script_filename}')
    if ret != 0 or 'Finished successfully' not in stdout:
        raise VirtWhoError(f"Failed to deploy configure by {script_filename}")
    if debug:
        return deploy_validation(hypervisor_type)


def deploy_configure_by_command_check(command):
    """Deploy and run virt-who service by the hammer command to check deploy log.

    :param str command: get the command by UI/CLI/API, it should be like:
        `hammer virt-who-config deploy --id 1 --organization-id 1`
    :param str hypervisor_type: esx, libvirt, rhevm, xen, libvirt, kubevirt, ahv
    :param str org: Organization Label
    """
    virtwho_cleanup()
    try:
        ret, stdout = runcmd(command)
    except Exception:
        raise VirtWhoError(f"Failed to deploy configure by {command}")
    else:
        if ret != 0 or 'Finished successfully' not in stdout:
            raise VirtWhoError(f"Failed to deploy configure by {command}")
        else:
            return 'Finished successfully'


def restart_virtwho_service():
    """
    Do the following:
    1. remove rhsm.log to ensure there are no old messages.
    2. restart virt-who service via systemctl command
    """
    runcmd("rm -f /var/log/rhsm/rhsm.log")
    runcmd("systemctl restart virt-who; sleep 10")


def update_configure_option(option, value, config_file):
    """
    Update option in virt-who config file
    :param option: the option you want to update
    :param value:  set the option to the value
    :param config_file: path of virt-who config file
    """
    cmd = 'sed -i "s|^{0}.*|{0}={1}|g" {2}'.format(option, value, config_file)
    ret, output = runcmd(cmd)
    if ret != 0:
        raise VirtWhoError(f"Failed to set option {option} value to {value}")


def delete_configure_option(option, config_file):
    """
    Delete option in virt-who config file
    :param option: the option you want to delete
    :param config_file: path of virt-who config file
    """
    cmd = 'sed -i "/^{0}/d" {1}; sed -i "/^#{0}/d" {1}'.format(option, config_file)
    ret, output = runcmd(cmd)
    if ret != 0:
        raise VirtWhoError(f"Failed to delete option {option}")


def add_configure_option(option, value, config_file):
    """
    Add option to virt-who config file
    :param option: the option you want to add
    :param value:  the value of the option
    :param config_file: path of virt-who config file
    """
    try:
        get_configure_option(option, config_file)
    except Exception:
        cmd = f'echo -e "\n{option}={value}" >> {config_file}'
        ret, output = runcmd(cmd)
        if ret != 0:
            raise VirtWhoError(f"Failed to add option {option}={value}")
    else:
        raise VirtWhoError(f"option {option} is already exist in {config_file}")


def hypervisor_json_create(hypervisors, guests):
    """
    Create a hypervisor guest json data. For example:
    {'hypervisors': [{'hypervisorId': '820b5143-3885-4dba-9358-4ce8c30d934e',
    'guestIds': [{'guestId': 'afb91b1f-8438-46f5-bc67-d7ab328ef782', 'state': 1,
    'attributes': {'active': 1, 'virtWhoType': 'esx'}}]}]}
    :param hypervisors: how many hypervisors will be created
    :param guests: how many guests will be created
    """
    hypervisors_list = []
    for i in range(hypervisors):
        guest_list = []
        for c in range(guests):
            guest_list.append(
                {
                    "guestId": str(uuid.uuid4()),
                    "state": 1,
                    "attributes": {"active": 1, "virtWhoType": "esx"},
                }
            )
        hypervisor = {"guestIds": guest_list}
        hypervisors_list.append(hypervisor)
    mapping = {"hypervisors": hypervisors_list}
    return mapping


def create_fake_hypervisor_content(org_label, hypervisors, guests):
    """
    Post the fake hypervisor content to satellite server
    :param hypervisors: how many hypervisors will be created
    :param guests: how many guests will be created
    :param org_label: the label of the Organization
    :return data: the hypervisor content
    """
    data = hypervisor_json_create(hypervisors, guests)
    url = f"https://{settings.server.hostname}/rhsm/hypervisors/{org_label}"
    auth = (settings.server.admin_username, settings.server.admin_password)
    result = requests.post(url, auth=auth, verify=False, json=data)
    assert result.status_code == 200
    return data


def get_hypervisor_info(hypervisor_type):
    """
    Get the hypervisor_name and guest_name from rhsm.log.
    """
    hypervisor_name, guest_name = _get_hypervisor_mapping(hypervisor_type)
    return hypervisor_name, guest_name


def virtwho_package_locked():
    """
    Uninstall virt-who package and lock the satellite-maintain packages.
    """
    runcmd('rpm -e virt-who; satellite-maintain packages lock')
    result = runcmd('satellite-maintain packages is-locked')
    assert "Packages are locked" in result[1]


def create_http_proxy(org, name=None, url=None, http_type='https'):
    """
    Creat a new http-proxy with attributes.
    :param name: Name of the proxy
    :param url: URL of the proxy including schema (https://proxy.example.com:8080)
    :param http_type: https or http
    :param org: instance of the organization
    :return:
    """
    org = entities.Organization().search(query={'search': f'name="{org.name}"'})[0]
    http_proxy_name = name or gen_string('alpha', 15)
    http_proxy_url = (
        url or f'{gen_url(scheme=http_type)}:{gen_integer(min_value=10, max_value=9999)}'
    )
    http_proxy = entities.HTTPProxy(
        name=http_proxy_name,
        url=http_proxy_url,
        organization=[org.id],
    ).create()
    return http_proxy.url, http_proxy.name, http_proxy.id
