"""Utility module to handle the virtwho configure UI/CLI/API testing"""
import re
import json
from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.cli.host import Host
from robottelo.cli.virt_who_config import VirtWhoConfig

VIRTWHO_SYSCONFIG = "/etc/sysconfig/virt-who"


class VirtWhoError(Exception):
    """Exception raised for failed virtwho operations"""


def _parse_entry(entry):
    """Paser the the string and return json format"""
    try:
        return json.loads(entry)
    except json.decoder.JSONDecodeError:
        return None


def get_system(system_type):
    """Return a dict account for ssh connect.
    :param str system_type: The type of the system, should be one of
        ('satellite', 'guest').
    :raises: VirtWhoError: If wrong ``system_type`` specified.
    """
    if system_type == 'guest':
        return{
            'hostname': settings.virtwho.guest,
            'username': settings.virtwho.guest_username,
            'password': settings.virtwho.guest_password,
            'port': settings.virtwho.guest_port,
        }
    elif system_type == 'satellite':
        return{
            'hostname': settings.server.hostname,
            'username': settings.server.ssh_username,
            'password': settings.server.ssh_password,
        }
    else:
        raise VirtWhoError(
            '"{}" system type is not supported. Please use one of {}'
            .format(system_type, ('satellite', 'guest'))
        )


def get_guest_info():
    """Return the guest_name, guest_uuid"""
    hypervisor_type = settings.virtwho.hypervisor_type
    _, guest_name = runcmd(
        'hostname',
        system=get_system('guest')
    )
    _, guest_uuid = runcmd(
        'dmidecode -s system-uuid',
        system=get_system('guest')
    )
    if (not guest_uuid or not guest_name):
        raise VirtWhoError(
            'Failed to get the guest info for {}'
            .format(hypervisor_type)
        )
    # Different UUID for vcenter by dmidecode and vcenter MOB
    if hypervisor_type == 'esx':
        guest_uuid = guest_uuid.split('-')[-1]
    if hypervisor_type == 'hyperv':
        guest_uuid = guest_uuid.split('-')[-1].upper()
    return guest_name, guest_uuid


def runcmd(cmd, system=None, timeout=None, output_format='plain'):
    """Return the retcode and stdout.
    :param str cmd: The command line will be executed in the target system.
    :param dict system: the system account which ssh will connect to,
        it will connect to the satellite host if the system is None.
    :param int timeout: Time to wait for establish the connection.
    :param str output_format: plain|json|csv|list
    """
    system = system or get_system('satellite')
    result = ssh.command(
        cmd, **system, timeout=timeout,
        output_format=output_format
    )
    ret = result.return_code
    stdout = result.stdout.strip()
    return ret, stdout


def register_system(system, activation_key=None, org='Default_Organization'):
    """Return True if the system is registered to satellite successfully.
    :param dict system: system account used by ssh to connect and register.
    :param str activation_key: the activation key will be used to register.
    :param str org: Which organization will be used to register.
    :raises: VirtWhoError: If failed to register the system.
    """
    runcmd('subscription-manager unregister', system)
    runcmd('subscription-manager clean', system)
    runcmd('rpm -qa | grep katello-ca-consumer | xargs rpm -e |sort', system)
    runcmd(
        'rpm -ihv http://{}/pub/katello-ca-consumer-latest.noarch.rpm'
        .format(settings.server.hostname), system
    )
    cmd = 'subscription-manager register --org={} '.format(org)
    if activation_key is not None:
        cmd += '--activationkey={}'.format(activation_key)
    else:
        cmd += '--username={} --password={}'.format(
            settings.server.admin_username,
            settings.server.admin_password)
    ret, stdout = runcmd(cmd, system)
    if ret == 0 or "system has been registered" in stdout:
        return True
    else:
        raise VirtWhoError(
            'Failed to register system: {}'.format(system)
        )


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


def get_virtwho_status():
    """Return the status of virt-who service, it will help us to know
    the virt-who configure file is deployed or not.
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
        raise VirtWhoError("No configure id found for {}".format(name))


def get_configure_command(config_id, org=DEFAULT_ORG):
    """Return the deploy command line based on configure id.
    :param str config_id: the unique id of the configure file you have created.
    :param str org: the satellite organization name.
    """
    return (
        "hammer virt-who-config deploy --id {} --organization '{}'"
        .format(config_id, org)
    )


def get_configure_file(config_id):
    """Return the configure file full name in /etc/virt-who.d
    :param str config_id: the unique id of the configure file you have created.
    """
    return (
        "/etc/virt-who.d/virt-who-config-{}.conf"
        .format(config_id)
    )


def get_configure_option(option, filename):
    """Return the option's value for the specific file.
    :param str option: the option name in the configure file
    :param str filename: the configure file, it could be:
        /etc/sysconfig/virt-who
        /etc/virt-who.d/virt-who-config-{}.conf
    :raises: VirtWhoError: If no this option name in the file.
    """
    cmd = "grep -v '^#' {} | grep ^{}".format(filename, option)
    ret, stdout = runcmd(cmd)
    if ret == 0 and option in stdout:
        value = stdout.split('=')[1].strip()
        return value
    else:
        raise VirtWhoError(
            "option {} is not exist or not be enabled in {}"
            .format(option, filename)
        )


def _get_hypervisor_mapping(logs):
    """Analysing rhsm.log and get to know: what is the hypervisor_name
    for the specific guest.
    :param str logs: the output of rhsm.log.
    :raises: VirtWhoError: If hypervisor_name is None.
    :return: hypervisor_name and guest_name
    """
    mapping = list()
    entry = None
    guest_name, guest_uuid = get_guest_info()
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
        raise VirtWhoError(
            "Failed to get the hypervisor_name for guest {}"
            .format(guest_name)
        )


def deploy_validation():
    """Checkout the deploy result
    :raises: VirtWhoError: If failed to start virt-who servcie.
    :ruturn: hypervisor_name and guest_name
    """
    status = get_virtwho_status()
    if status != 'running':
        raise VirtWhoError("Failed to start virt-who service")
    _, logs = runcmd('cat /var/log/rhsm/rhsm.log')
    hypervisor_name, guest_name = _get_hypervisor_mapping(logs)
    for host in Host.list({'search': hypervisor_name}):
        Host.delete({'id': host['id']})
    runcmd("systemctl restart virt-who; sleep 5")
    return hypervisor_name, guest_name


def deploy_configure_by_command(command, debug=False):
    """Deploy and run virt-who servcie by the hammer command.
    :param str command: get the command by UI/CLI/API, it should be like:
        `hammer virt-who-config deploy --id 1 --organization-id 1`
    :param bool debug: if VIRTWHO_DEBUG=1, this option should be True.
    """
    virtwho_cleanup()
    register_system(get_system('guest'))
    ret, stdout = runcmd(command)
    if ret != 0 or 'Finished successfully' not in stdout:
        raise VirtWhoError(
            "Failed to deploy configure by {}"
            .format(command)
        )
    if debug:
        return deploy_validation()


def deploy_configure_by_script(script_content, debug=False):
    """Deploy and run virt-who servcie by the shell script.
    :param str script_content: get the script by UI or API.
    :param bool debug: if VIRTWHO_DEBUG=1, this option should be True.
    """
    script_filename = "/tmp/deploy_script.sh"
    script_content = (
        script_content
        .replace('&amp;', '&')
        .replace('&gt;', '>')
        .replace('&lt;', '<')
    )
    virtwho_cleanup()
    register_system(get_system('guest'))
    with open(script_filename, 'w') as fp:
        fp.write(script_content)
    ssh.upload_file(script_filename, script_filename)
    ret, stdout = runcmd('sh {}'.format(script_filename))
    if ret != 0 or 'Finished successfully' not in stdout:
        raise VirtWhoError(
            "Failed to deploy configure by {}"
            .format(script_filename)
        )
    if debug:
        return deploy_validation()


def restart_virtwho_service():
    """
    Do the following:
    1. clean rhsm.log message, make sure there is no old message exist.
    2. restart virt-who service via systemctl command
    """
    runcmd("rm -f /var/log/rhsm/rhsm.log")
    runcmd("systemctl restart virt-who; sleep 5")


def update_configure_option(option, value, config_file):
    """
    Update option in virt-who config file
    :param option: the option you want to update
    :param value:  set the option to the value
    :param config_file: path of virt-who config file
    """
    cmd = 'sed -i "s|^{0}.*|{0}={1}|g" {2}'.format(
        option, value, config_file)
    ret, output = runcmd(cmd)
    if ret != 0:
        raise VirtWhoError(
            "Failed to set option {0} value to {1}".format(option, value))


def delete_configure_option(option, config_file):
    """
    Delete option in virt-who config file
    :param option: the option you want to delete
    :param config_file: path of virt-who config file
    """
    cmd = 'sed -i "/^{0}/d" {1}; sed -i "/^#{0}/d" {1}'.format(
        option, config_file)
    ret, output = runcmd(cmd)
    if ret != 0:
        raise VirtWhoError("Failed to delete option {}".format(option))


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
        cmd = 'echo -e "\n{0}={1}" >> {2}'.format(option, value, config_file)
        ret, output = runcmd(cmd)
        if ret != 0:
            raise VirtWhoError(
                "Failed to add option {0}={1}".format(option, value))
    else:
        raise VirtWhoError(
            "option {} is already exist in {}"
            .format(option, config_file)
        )
