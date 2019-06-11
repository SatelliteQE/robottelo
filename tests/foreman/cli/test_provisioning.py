"""Provisioning tests

:Requirement: Provisioning

:CaseAutomation: NotAutomated

:CaseLevel: System

:CaseComponent: Provisioning

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""

import logging
import math
import paramiko
import pytest
import time

from nailgun import entities
from fauxfactory import gen_string
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_PTABLE,
    DEFAULT_SUBSCRIPTION_NAME,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.cli.factory import (
    make_host,
)
from robottelo.decorators import (
    tier3,
)
from robottelo.helpers import (
    get_nailgun_config,
)
from robottelo import manifests

LOGGER = logging.getLogger('robottelo')


@pytest.fixture(scope='session')
def user_credentials():
    # Create a new user with admin permissions
    login = gen_string('alphanumeric')
    password = gen_string('alphanumeric')
    entities.User(
        admin=True, login=login, password=password
    ).create()
    server_config = get_nailgun_config()
    server_config.auth = (login, password)
    return server_config


@pytest.fixture(scope='session')
def org(user_credentials):
    org = entities.Organization(user_credentials).create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    return org


@pytest.fixture(scope='session')
def loc(user_credentials, org):
    loc = entities.Location(user_credentials).create()
    loc.organization = [org]
    loc.update()
    return loc


@pytest.fixture(scope='session')
def domain(user_credentials, org, loc):
    dom = entities.Domain(user_credentials, id=1).read()
    dom.organization = dom.organization + [org]
    dom.location = dom.location + [loc]
    dom = dom.update(['organization', 'location'])
    return dom


@pytest.fixture(scope='session')
def capsule(user_credentials, org, loc):
    capsule = entities.SmartProxy(id=1).read()
    if org not in capsule.organization:
        capsule.organization.append(org)
    if loc not in capsule.location:
        capsule.location.append(loc)
    capsule = capsule.update(['organization', 'location'])
    return capsule


@pytest.fixture(scope='session')
def subnet(user_credentials, org, loc, domain, capsule):
    subnet_name = gen_string('alpha')
    subnet = entities.Subnet(
        user_credentials,
        name=subnet_name,
        location=[loc],
        organization=[org],
        ipam=settings.vlan_networking.dhcp_ipam,
        network=settings.vlan_networking.subnet,
        gateway=settings.vlan_networking.gateway,
        from_=settings.vlan_networking.dhcp_from,
        to=settings.vlan_networking.dhcp_to,
        mask=settings.vlan_networking.netmask,
        dns_primary=settings.vlan_networking.dns_primary,
        domain=[domain],
        dns=capsule,
        dhcp=capsule,
        discovery=capsule,
        # httpboot=capsule,   # TODO
        template=capsule,
        tftp=capsule,
        remote_execution_proxy=[capsule],
    ).create()
    return subnet


@pytest.fixture(scope='session')
def lce(user_credentials, org):
    return entities.LifecycleEnvironment(
                user_credentials,
                organization=org).create()


@pytest.fixture(scope='session')
def rhel7(user_credentials, org):
    repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhel7']['name'],
        reposet=REPOSET['rhel7'],
        releasever=REPOS['rhel7']['releasever'],
    )
    repo = entities.Repository(user_credentials, id=repo_id)
    response = repo.sync(synchronous=False)
    entities.ForemanTask(id=response['id']).poll(timeout=1800)
    return repo.read()


@pytest.fixture(scope='session')
def rhel7ks(user_credentials, org):
    repo_id = enable_rhrepo_and_fetchid(
        basearch=REPOS['rhel7ks']['arch'],
        org_id=org.id,
        product=REPOS['rhel7ks']['product'],
        releasever=REPOS['rhel7ks']['releasever'],
        repo=REPOS['rhel7ks']['name'],
        reposet=REPOS['rhel7ks']['reposet'],
    )
    repo = entities.Repository(user_credentials, id=repo_id)
    response = repo.sync(synchronous=False)
    entities.ForemanTask(id=response['id']).poll(timeout=1800)
    return repo.read()


@pytest.fixture(scope='session')
def rhel8ks(user_credentials, org):
    # First RHEL8 AppStream KS
    repo_id = enable_rhrepo_and_fetchid(
            basearch=REPOS['rhel8ksappstream']['arch'],
            org_id=org.id,
            product=REPOS['rhel8ksappstream']['product'],
            releasever=REPOS['rhel8ksappstream']['releasever'],
            repo=REPOS['rhel8ksappstream']['name'],
            reposet=REPOS['rhel8ksappstream']['reposet'],
    )
    repo = entities.Repository(user_credentials, id=repo_id)
    response = repo.sync(synchronous=False)
    # Now RHEL8 BaseOS KS which we will return at the end
    repo_id = enable_rhrepo_and_fetchid(
            basearch=REPOS['rhel8ksbaseos']['arch'],
            org_id=org.id,
            product=REPOS['rhel8ksbaseos']['product'],
            releasever=REPOS['rhel8ksbaseos']['releasever'],
            repo=REPOS['rhel8ksbaseos']['name'],
            reposet=REPOS['rhel8ksbaseos']['reposet'],
    )
    repo = entities.Repository(user_credentials, id=repo_id)
    response = repo.sync(synchronous=False)
    # Wait for sync to finish
    entities.ForemanTask(id=response['id']).poll(timeout=1800)
    entities.ForemanTask(id=response['id']).poll(timeout=100)
    return repo


@pytest.fixture(scope='session')
def cv(user_credentials, org, rhel7, rhel7ks):
    # TODO: Some puppet modules in here would be nice
    content_view = entities.ContentView(
        user_credentials,
        organization=org
    ).create()

    content_view.repository = [rhel7, rhel7ks]
    content_view = content_view.update(['repository'])
    return content_view


@pytest.fixture(scope='session')
def cvv(user_credentials, org, cv, lce):
    cv.publish()
    cv = cv.read()
    assert len(cv.version) == 1, "Single CV version expected"
    cv_version = cv.version[0].read()
    assert len(cv_version.environment) == 1, "Single LCE expected for the given CV version"
    promote(cv_version, lce.id)
    cv = cv.read()
    assert len(cv.version) == 1, "Single CV version expected"
    return cv_version.read()


@pytest.fixture(scope='session')
def ak(user_credentials, org, cv, lce):
    activation_key_name = gen_string('alpha')
    activation_key = entities.ActivationKey(
        user_credentials,
        name=activation_key_name,
        environment=lce,
        organization=org,
        content_view=cv,
    ).create()
    for sub in entities.Subscription(organization=org).search():
        if sub.read_json()['name'] == DEFAULT_SUBSCRIPTION_NAME:
            activation_key.add_subscriptions(data={
                'quantity': 1,
                'subscription_id': sub.id,
            })
            break
    return activation_key


@pytest.fixture(scope='session')
def cr(user_credentials, org, loc):
    compute_resource = entities.LibvirtComputeResource(
        user_credentials,
        url='qemu+ssh://root@{0}/system'.format(
            settings.compute_resources.libvirt_hostname
        ),
        set_console_password=False,
        organization=[org],
        location=[loc]
    ).create()
    return compute_resource


@pytest.fixture(scope='session')
def arch(user_credentials):
    return entities.Architecture().search(
        query={'search': 'name=x86_64'})[0].read()


@pytest.fixture(scope='session')
def os(user_credentials):
    return entities.OperatingSystem().search(
        query={'search': 'name=RedHat and major=7 and minor=6'})[0].read()


@pytest.fixture(scope='session')
def env(user_credentials, org, loc):
    # TODO: We want custom env created by CV I guess
    env = entities.Environment().search(
        query={'search': 'name=production'})[0].read()
    org.environment.append(env)
    org.update(['environment'])
    org.read()
    loc.environment.append(env)
    loc.update(['environment'])
    loc.read()
    return env


@pytest.fixture(scope='session')
def ptable(user_credentials):
    return entities.PartitionTable().search(
        query={'search': 'name="{0}"'.format(DEFAULT_PTABLE)})[0].read()


@pytest.fixture(scope='session')
def hg(user_credentials, org, loc, capsule, domain, subnet, os, lce, arch, cv, env,
       rhel7ks, ptable, cr, ak):
    hg = entities.HostGroup(
        user_credentials,
        architecture=arch,
        # compute_resource=cr,
        content_source=capsule,
        content_view=cv,
        domain=domain,
        environment=env,
        kickstart_repository=rhel7ks,
        lifecycle_environment=lce,
        location=[loc],
        name=gen_string('alpha'),
        operatingsystem=os,
        organization=[org],
        ptable=ptable,
        realm=None,
        subnet=subnet,
    ).create(create_missing=False)
    entities.Parameter(hostgroup=hg, name='kt_activation_keys', value=ak.name).create()
    # FIXME: it should be possible to set this at creation time
    hg.pxe_loader = "PXELinux BIOS"
    hg.update(['pxe_loader'])
    return hg


def _wait_for_build_done(host):
    """Block while given host is in build mode"""
    provisioning_timeout = 1800
    poll_interval = 10

    for i in range(math.ceil(provisioning_timeout/poll_interval)):
        host = host.read()
        if host.build_status_label != 'Pending installation':
            assert host.build_status_label == 'Installed',\
                'Failed to provision host - status {0}'.format(host.build_status_label)
            break
        time.sleep(poll_interval)
    assert host.build_status_label == 'Installed',\
        'Failed to provision host in a specified timeout: {0}s'.format(provisioning_timeout)


def _get_ssh_connection(hostname, username, password):
    LOGGER.debug('Openning SSH connection to {0}'.format(hostname))
    client = paramiko.SSHClient()
    # Parsing an instance of the AutoAddPolicy to set_missing_host_key_policy()
    # changes it to allow any host
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Connect to the server
    client.connect(hostname=hostname, port=22, username=username, password=password,
                   timeout=120, allow_agent=False, look_for_keys=False)
    return client


def _execute_ssh_command(connection, command):
    LOGGER.debug("Running '{0}' on the host".format(command))
    stdin, stdout, stderr = connection.exec_command(command, timeout=60)
    stdout_read = stdout.read()
    stderr_read = stderr.read()
    exit_code = stdout.channel.recv_exit_status()
    LOGGER.debug("Command returned stdout '{0}' and stderr '{1}'".format(stdout_read, stderr_read))
    return exit_code, stdout_read, stderr_read


def _wait_for_ssh_ready(host, root_pass):
    hostname = host.ip
    timeout = 100
    start = time.time()
    e = None
    while (time.time() - start) <= timeout:
        try:
            _get_ssh_connection(hostname, 'root', root_pass)
        except paramiko.ssh_exception.NoValidConnectionsError as exc:
            e = exc
            continue
        else:
            return
    raise TimeoutError("Failed waiting on host %s ssh to come up: %s" % (hostname, e))


def _run_rex_job(host, job_category, root_pass):
    """Run remote execution job with given job_category on a host"""
    templates = entities.JobTemplate().search(
        query={'search': 'name~command and job_category~{0}'.format(job_category)}
    )
    assert len(templates) > 0, 'API returned 0 command job templates'
    template = templates[0].read()

    file_name = '/tmp/rex_test_{0}'.format(gen_string('alpha'))
    file_content = gen_string('alpha')

    invocation_command = entities.JobInvocation().run(data={
        'job_template_id': template.id,
        'inputs': {'command': 'echo "{0}" > {1}'.format(file_content, file_name)},
        'targeting_type': 'static_query',
        'search_query': 'name ~ {0}'.format(host.name)
    })
    assert invocation_command['output']['total_count'] == 1, \
        'Incorrect total count for {0} rex on {1}'.format(job_category, host)
    assert invocation_command['output']['success_count'] == 1, \
        'Incorrect success count for {0} rex on {1}'.format(job_category, host)

    connection = _get_ssh_connection(host.ip, 'root', root_pass)
    rc, stdout, stderr = _execute_ssh_command(connection, 'cat {0}'.format(file_name))
    assert rc == 0
    assert file_content in str(stdout)
    assert len(stderr) == 0
    connection.close()


def _run_sub_man_status(host, root_pass):
    """Run `subscription-manager status` on a host and ensure output is sane"""
    connection = _get_ssh_connection(host.ip, 'root', root_pass)
    rc, stdout, stderr = _execute_ssh_command(connection, 'subscription-manager status')
    assert rc == 0
    assert 'Overall Status: Current' in str(stdout)
    assert len(stderr) == 0
    connection.close()


def _check_package_install(host, root_pass):
    """Make sure we are able to install package from Satellite"""
    connection = _get_ssh_connection(host.ip, 'root', root_pass)
    # Make sure package is not installed
    rc, stdout, stderr = _execute_ssh_command(connection, 'rpm -q zsh')
    assert rc == 1
    # Install package
    rc, stdout, stderr = _execute_ssh_command(connection, 'yum -y install zsh')
    assert rc == 0
    assert 'Installed:' in str(stdout)
    assert 'zsh' in str(stdout)
    assert 'Complete!' in str(stdout)
    # Make sure package is installed
    rc, stdout, stderr = _execute_ssh_command(connection, 'rpm -q zsh')
    assert rc == 0
    assert 'zsh' in str(stdout)
    assert len(stderr) == 0
    connection.close()


@tier3
def test_rhel_pxe_provisioning_on_libvirt(user_credentials, org, loc, domain, subnet, lce,
                                          rhel7, rhel7ks, cv, cvv, ak, cr, arch, os, env, hg):
    """Provision RHEL system via PXE on libvirt and make sure it behaves

    :id: a272a594-f758-40ef-95ec-813245e44b63

    :steps:
        1. Provision RHEL system via PXE on libvirt
        2. Check that resulting host is registered to Satellite
        3. Check host can install package from Satellite

    :expectedresults:
        1. Host installs
        2. Host is registered to Satellite and subscription status is 'Success'
        3. Host can install package from Satellite
    """
    LOGGER.info(">>> User/pass: %s/%s" % user_credentials.auth)
    LOGGER.info(">>> Org: [%s] %s" % (org.id, org.name))
    LOGGER.info(">>> Loc: [%s] %s" % (loc.id, loc.name))
    LOGGER.info(">>> Domain: [%s] %s" % (domain.id, domain.name))
    LOGGER.info(">>> Subnet: [%s] %s" % (subnet.id, subnet.name))
    LOGGER.info(">>> Lifecycle environment: [%s] %s" % (lce.id, lce.name))
    LOGGER.info(">>> Base repo: [%s] %s" % (rhel7.id, rhel7.name))
    LOGGER.info(">>> KS repo: [%s] %s" % (rhel7ks.id, rhel7ks.name))
    LOGGER.info(">>> Content view: [%s] %s" % (cv.id, cv.name))
    LOGGER.info(">>> Content view version: [%s]" % (cvv.id))
    LOGGER.info(">>> Activation key: [%s] %s" % (ak.id, ak.name))
    LOGGER.info(">>> Compute resource: [%s] %s" % (cr.id, cr.name))
    LOGGER.info(">>> Architecture: [%s] %s" % (arch.id, arch.name))
    LOGGER.info(">>> Operating system: [%s] %s %s.%s" % (os.id, os.name, os.major, os.minor))
    LOGGER.info(">>> Environment: [%s] %s" % (env.id, env.name))
    LOGGER.info(">>> Host group: [%s] %s" % (hg.id, hg.name))
    host_ip = '192.168.11.104'   # FIXME Do not hardcode this one
    host_name = gen_string('alpha').lower()
    host_pass = gen_string('alpha')
    LOGGER.info(">>> Host IP: %s" % host_ip)
    LOGGER.info(">>> Host name: %s" % host_name)
    LOGGER.info(">>> Host root password: %s" % host_pass)
    host_parameters = [{'name': 'remote_execution_connect_by_ip', 'value': True}]
    host_parameters_str = ','.join(["%s=%s" % (i['name'], i['value']) for i in host_parameters])
    LOGGER.info(">>> Host parameters: %s" % host_parameters_str)
    parameters = {
        'build': 'yes',
        'compute-attributes': 'start=1',
        'compute-resource-id': cr.id,   # FIXME This should be in host group
        'hostgroup-id': hg.id,
        'interface': 'compute_type=bridge, compute_bridge=br0',
        'ip': host_ip,
        'location-id': loc.id,
        'name': host_name,
        'organization-id': org.id,
        'root-password': host_pass,
        'volume': 'pool_name=images, capacity=5G',
        'parameters': host_parameters_str,
    }
    host = make_host(parameters)
    host = entities.Host(id=host['id']).read()
    _wait_for_build_done(host)
    _wait_for_ssh_ready(host, host_pass)
    _run_rex_job(host, 'Commands', host_pass)
    _run_rex_job(host, 'Ansible Commands', host_pass)
    _run_sub_man_status(host, host_pass)
    _check_package_install(host, host_pass)
    host.delete()
