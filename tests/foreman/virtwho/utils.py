"""Utility module to handle the virtwho configure UI/CLI/API testing"""
import re
import json
from robottelo import ssh
from robottelo.config import settings
from robottelo.cli.host import Host


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
    return guest_name, guest_uuid


def runcmd(cmd, system=None, timeout=None):
    """Return the retcode and stdout.
    :param str cmd: The command line will be executed in the target system.
    :param dict system: the system account which ssh will connect to,
        it will connect to the satellite host if the system is None.
    :param int timeout: Time to wait for establish the connection.
    """
    system = system or get_system('satellite')
    result = ssh.command(cmd, **system, timeout=timeout)
    ret = result.return_code
    stdout = '\n'.join(result.stdout).strip()
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
    ret, stdout = runcmd('systemctl status virt-who')
    running_stauts = ['is running', 'Active: active (running)']
    stopped_status = ['is stopped', 'Active: inactive (dead)']
    if ret != 0:
        return 'undefined'
    if any(key in stdout for key in running_stauts):
        return 'running'
    elif any(key in stdout for key in stopped_status):
        return 'stopped'
    else:
        return 'undefined'


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


def deploy_validation(debug=True):
    """Checkout the deploy result
    :param bool debug: if VIRTWHO_DEBUG=0, this option should be False,
        because there is no json data logged in rhsm.log.
    :raises: VirtWhoError: If failed to start virt-who servcie.
    """
    status = get_virtwho_status()
    _, logs = runcmd('cat /var/log/rhsm/rhsm.log')
    error = len(re.findall(r'\[.*ERROR.*\]', logs))
    if status != 'running' or error != 0:
        raise VirtWhoError("Failed to start virt-who service")
    if debug:
        hypervisor_name, guest_name = _get_hypervisor_mapping(logs)
        # Delete the hypervisor entry and always make sure it's new.
        hosts = Host.list({'search': hypervisor_name})
        for index, host in enumerate(hosts):
            Host.delete({'id': host['id']})
        runcmd("systemctl restart virt-who")
        return hypervisor_name, guest_name


def deploy_configure_by_command(command, debug=True):
    """Deploy and run virt-who servcie by the hammer command.
    :param str command: get the command by UI/CLI/API, it should be like:
        `hammer virt-who-config deploy --id 1 --organization-id 1`
    :param bool debug: if VIRTWHO_DEBUG=0, this option should be False.
    """
    virtwho_cleanup()
    register_system(get_system('guest'))
    runcmd(command)
    return deploy_validation(debug)


def deploy_configure_by_script(script_content, debug=True):
    """Deploy and run virt-who servcie by the shell script.
    :param str script_content: get the script by UI or API.
    :param bool debug: if VIRTWHO_DEBUG=0, this option should be False.
    """
    script_filename = "/tmp/deploy_script.sh"
    virtwho_cleanup()
    register_system(get_system('guest'))
    script_content = (
        script_content
        .replace('&amp;', '&')
        .replace('&gt;', '>')
        .replace('&lt;', '<')
    )
    with open(script_filename, 'w') as fp:
        fp.write(script_content)
    ssh.upload_file(script_filename, script_filename)
    runcmd('sh {}'.format(script_filename))
    return deploy_validation(debug)
