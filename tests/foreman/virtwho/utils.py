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


def get_rhsm_logfile():
    """Return a dictionary by analysing rhsm.log, and then can know
        the virt-who configure file is deployed as expected or not.

    The following keys will be included:
    :[error]: how many error message exist, the expected value is 0.
    :[hypervisor_name]: the hypervisor display name in Content Hosts.
    :[guest_name]: the guest display name in Content Hosts.
    """
    data = dict()
    mapping = list()
    entry = None
    guest_name, guest_uuid = get_guest_info()
    ret, stdout = runcmd('cat /var/log/rhsm/rhsm.log')
    data['error'] = len(re.findall(r'\[.*ERROR.*\]', stdout))
    data['guest_name'] = guest_name
    for line in stdout.split('\n'):
        if line:
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
                data['hypervisor_name'] = item['hypervisorId']['hypervisorId']
                break
    return data


def deploy_configure_by_command(command):
    """Return the hypervisor_name and guest_name if deployed successfully.
    :param str command: when created a configure file by UI, you can read
        the deploy command line such as:
        `hammer virt-who-config deploy --id 1 --organization-id 1`
    :raises: VirtWhoError: If failed to deploy configure by this command.
    """
    virtwho_cleanup()
    register_system(get_system('guest'))
    ret, stdout = runcmd(command)
    status = get_virtwho_status()
    data = get_rhsm_logfile()
    if (status != 'running' or data['error'] != 0 or 'hypervisor_name' not in data):
        virtwho_cleanup()
        raise VirtWhoError("Failed to deploy virtwho configure")
    guest_name = data['guest_name']
    hypervisor_name = data['hypervisor_name']
    # Delete the hypervisor entry and always make sure it's new.
    hosts = Host.list({'search': hypervisor_name})
    for index, host in enumerate(hosts):
        Host.delete({'id': host['id']})
    runcmd("systemctl restart virt-who")
    return hypervisor_name, guest_name
