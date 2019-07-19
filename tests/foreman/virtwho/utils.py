"""Utility module to handle the virtwho configure UI/CLI/API testing"""
import re
from robottelo import ssh
from robottelo.config import settings
from robottelo.cli.host import Host


class VirtWhoError(Exception):
    """Exception raised for failed virtwho operations"""


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


def runcmd(cmd, system=None, timeout=None):
    """Return the retcode and stdout.
    :param str cmd: The command line will be executed in the target system.
    :param dict system: the system account which ssh will connect to,
        it will connect to the satellite host if the system is None.
    :param int timeout: Time to wait for establish the connection.
    """
    system = system or get_system('satellite')
    result = ssh.command(cmd, **system, timeout=timeout)
    return result.return_code, '\n'.join(result.stdout)


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
    :[reporter_id]: it can be defined by virtwho configure.
    :[interval_time]: it can be defined by virtwho configure.
    :[hypervisor_id]: it can be defined by virtwho configure.
    :[hypervisor_name]: get to know the hypervisor's hostname.
    :[guest_id]: get to know the guest_id.
    """
    ret, stdout = runcmd('cat /var/log/rhsm/rhsm.log')
    data = dict()
    data['error'] = len(re.findall(r'\[.*ERROR.*\]', stdout))
    if "virtwho.main DEBUG" in stdout:
        res = re.findall(r"reporter_id='(.*?)'", stdout)
        if len(res) > 0:
            data['reporter_id'] = res[0].strip()
        res = re.findall(r"infinite loop with(.*?)seconds", stdout)
        if len(res) > 0:
            data['interval_time'] = int(res[0].strip())
        res = re.findall(r'[^\s]*"hypervisorId": "(.*?)"', stdout)
        if len(res) > 0:
            data['hypervisor_id'] = res[0].strip()
        res = re.findall(r'[^\s]*"name": "(.*?)"', stdout)
        if len(res) > 0:
            data['hypervisor_name'] = res[0].strip()
        res = re.findall(r'[^\s]*guestId": "(.*?)"', stdout)
        if len(res) > 0:
            data['guest_id'] = res[0].strip()
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
    if (status != 'running' or data['error'] != 0 or 'hypervisor_id' not in data):
        virtwho_cleanup()
        raise VirtWhoError("Failed to deploy virtwho configure")
    # Get the hostname for guest.
    _, guest_name = runcmd('hostname', system=get_system('guest'))
    # Delete the hypervisor entry and always make sure it's new.
    hypervisor_name = data['hypervisor_id']
    hosts = Host.list({'search': hypervisor_name})
    for index, host in enumerate(hosts):
        Host.delete({'id': host['id']})
    runcmd("systemctl restart virt-who")
    return hypervisor_name, guest_name.strip()
