"""Test for Remote Execution

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
from nailgun import client
from nailgun.entity_mixins import TaskFailedError
import pytest

from robottelo.config import get_credentials, settings
from robottelo.exceptions import CLIFactoryError
from robottelo.hosts import get_sat_version
from robottelo.logging import logger
from robottelo.utils.installer import InstallerCommand

CAPSULE_TARGET_VERSION = f'6.{get_sat_version().minor}.z'

pytestmark = pytest.mark.destructive


def test_negative_run_capsule_upgrade_playbook_on_satellite(target_sat):
    """Run Capsule Upgrade playbook against the Satellite itself

    :id: 99462a11-5133-415d-ba64-4354da539a34

    :steps:
        1. Add REX key to the Satellite server.
        2. Run the Capsule Upgrade Playbook.
        3. Check the job output for proper failure reason.

    :expectedresults: Should fail

    :BZ: 2152951

    :CaseImportance: Medium
    """
    template_name = 'Capsule Upgrade Playbook'
    template_id = (
        target_sat.api.JobTemplate().search(query={'search': f'name="{template_name}"'})[0].id
    )
    target_sat.add_rex_key(satellite=target_sat)
    with pytest.raises(TaskFailedError) as error:
        target_sat.api.JobInvocation().run(
            data={
                'job_template_id': template_id,
                'inputs': {
                    'target_version': CAPSULE_TARGET_VERSION,
                    'whitelist_options': "repositories-validqqate,repositories-setup",
                },
                'targeting_type': "static_query",
                'search_query': f"name = {target_sat.hostname}",
            }
        )
    assert 'A sub task failed' in error.value.args[0]
    job = target_sat.api.JobInvocation().search(
        query={
            'search': f'host={target_sat.hostname},'
            'status=failed,description="Capsule Upgrade Playbook"'
        }
    )[0]
    host = target_sat.api.Host().search(query={'search': target_sat.hostname})
    response = client.get(
        f'{target_sat.url}/api/job_invocations/{job.id}/hosts/{host[0].id}',
        auth=get_credentials(),
        verify=False,
    )
    assert 'This playbook cannot be executed on a Satellite server.' in response.text


@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([8])
def test_positive_use_alternate_directory(
    target_sat, rhel_contenthost, default_org, default_location
):
    """Use alternate working directory on client to execute rex jobs

    :id: a0181f18-d3dc-4bd9-a2a6-430c2a49809e

    :expectedresults: Verify the job was successfully ran against the host

    :customerscenario: true

    :parametrized: yes
    """
    client = rhel_contenthost
    ak = target_sat.cli_factory.make_activation_key(
        {
            'lifecycle-environment': 'Library',
            'content-view': 'Default Organization View',
            'organization-id': default_org.id,
        }
    )
    result = client.register(default_org, default_location, ak.name, target_sat)
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    testdir = gen_string('alpha')
    result = client.run(f'mkdir /{testdir}')
    assert result.status == 0
    result = client.run(f'chcon --reference=/var /{testdir}')
    assert result.status == 0
    result = target_sat.execute(
        f"sed -i r's/^:remote_working_dir:.*/:remote_working_dir: \\/{testdir}/' \
        /etc/foreman-proxy/settings.d/remote_execution_ssh.yml",
    )
    assert result.status == 0
    result = target_sat.execute('systemctl restart foreman-proxy')
    assert result.status == 0

    command = f'echo {gen_string("alpha")}'
    invocation_command = target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': f'command={command}',
            'search-query': f"name ~ {client.hostname}",
        }
    )
    result = target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    try:
        assert result['success'] == '1'
    except AssertionError as err:
        output = ' '.join(
            target_sat.cli.JobInvocation.get_output(
                {'id': invocation_command['id'], 'host': client.hostname}
            )
        )
        result = f'host output: {output}'
        raise AssertionError(result) from err

    task = target_sat.cli.Task.list_tasks({'search': command})[0]
    search = target_sat.cli.Task.list_tasks({'search': f'id={task["id"]}'})
    assert search[0]['action'] == task['action']


def create_CA(host, path='/root/CA', name=None):
    assert host.execute(f'mkdir -p {path}').status == 0
    filename = 'id_ca' if name is None else f'id_{name}_ca'
    assert (
        host.execute(
            f'cd {path} && if ! [ -f {filename} ]; then ssh-keygen -t ed25519 -f {filename} -N ""; fi'
        ).status
        == 0
    )
    return filename


@pytest.fixture
def ca_sat(target_sat):
    path = "/root/CA"
    sat_ssh_path = '/var/lib/foreman-proxy/ssh/'
    filename = create_CA(target_sat, path)
    ca_path = f'{path}/{filename}'
    key_name = 'id_rsa_foreman_proxy'
    cert_name = f'{key_name}-cert.pub'
    assert (
        target_sat.execute(
            f'cd {sat_ssh_path} && cp {ca_path}.pub . && restorecon {filename}.pub && chown foreman-proxy {filename}.pub && chgrp foreman-proxy {filename}.pub'
        ).status
        == 0
    )
    assert (
        target_sat.execute(
            f'cd {sat_ssh_path} && ssh-keygen -s {ca_path} -I satellite -n root {key_name}.pub && restorecon {cert_name} && chown foreman-proxy {cert_name} && chgrp foreman-proxy {cert_name}'
        ).status
        == 0
    )
    return (target_sat, f'{sat_ssh_path}/{filename}.pub')


@pytest.fixture
def ca_contenthost(rhel_contenthost):
    path = '/root/CA'
    host_ssh_path = '/etc/ssh'
    filename = create_CA(rhel_contenthost, path, 'host')
    ca_path = f'{path}/{filename}'
    # create a host key and sign it
    key_name = 'ssh_host_ed25519_key'
    cert_name = f'{key_name}-cert.pub'
    assert (
        rhel_contenthost.execute(
            f'cd {host_ssh_path} && if ! [ -f ssh_host_ed25519_key ]; then ssh-keygen -t ed25519 -f {key_name} -N ""; fi'
        ).status
        == 0
    )
    assert (
        rhel_contenthost.execute(
            f'cd {host_ssh_path} && ssh-keygen -s {ca_path} -I host -n {rhel_contenthost.hostname} -h {key_name}.pub'
        ).status
        == 0
    )
    # setup cert usage
    assert (
        rhel_contenthost.execute(
            f'mkdir -p {host_ssh_path}/sshd_config.d && cd {host_ssh_path}/sshd_config.d && echo "HostCertificate {host_ssh_path}/{cert_name}" > 60-host-cert.conf'
        ).status
        == 0
    )
    assert rhel_contenthost.execute('systemctl restart sshd').status == 0
    return (rhel_contenthost, f'{ca_path}.pub')


@pytest.fixture
def host_ca_file_on_satellite(ca_contenthost):
    return f'/var/lib/foreman-proxy/ssh/{ca_contenthost[1].split("/")[-1]}'


def register_host(satellite, host, cockpit=False):
    org = satellite.api.Organization().create()
    if cockpit:
        rhelver = host.os_version.major
        if rhelver > 7:
            repo = [settings.repos[f'rhel{rhelver}_os']['baseos']]
        else:
            repo = [settings.repos['rhel7_os'], settings.repos['rhel7_extras']]
    else:
        repo = []
    satellite.register_host_custom_repo(org, host, repo)
    return org


def test_execution(satellite, host):
    command = "echo rex_passed $(date) > /root/test"
    invocation_command = satellite.cli_factory.job_invocation(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': f'command={command}',
            'search-query': f"name ~ {host.hostname}",
        }
    )
    return satellite.cli.JobInvocation.info({'id': invocation_command['id']})


def log_save(satellite, host):
    host.execute(
        f'journalctl -u sshd | grep {satellite.ip_addr} | grep CA | wc -l > /root/saved_sshd_log'
    )


def log_compare(satellite, host):
    return host.execute(
        f'[ $(( $(cat /root/saved_sshd_log) + 1 )) -eq $(journalctl -u sshd | grep {satellite.ip_addr} | grep " CA " | wc -l) ]'
    ).status


def copy_host_CA(host, satellite, host_path, satellite_path):
    host_ca_file_local = f'/tmp/{gen_string("alpha")}'
    host.get(host_path, host_ca_file_local)
    satellite.put(host_ca_file_local, satellite_path)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match([settings.content_host.default_rhel_version])
def test_positive_ssh_ca_sat_only(ca_sat, rhel_contenthost):
    """Setup Satellite's SSH key's cert, register host and run REX on that host

    :id: 353a21bf-f379-440a-9dc6-e17bf6414713

    :expectedresults: Verify the job has been run successfully against the host, Sat's cert hasn't been added to host's authorized_keys and CA verification has been used instead

    :parametrized: yes
    """
    sat = ca_sat[0]
    host = rhel_contenthost
    sat_ca_file = ca_sat[1]
    log_save(sat, host)
    command = InstallerCommand(
        foreman_proxy_plugin_remote_execution_script_ssh_user_ca_public_key_file=sat_ca_file,
    )
    assert sat.install(command).status == 0
    register_host(sat, host)
    result = test_execution(sat, host)
    # assert the run actually happened and it was authenticated using cert
    assert result.status == 0
    logger.debug(result)
    assert log_compare(sat, host) == 0
    check = host.execute('grep rex_passed /root/test')
    assert check.status == 0
    check = host.execute(f'grep {sat.hostname} /root/.ssh/authorized_keys')
    assert check.status != 0


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match([settings.content_host.default_rhel_version])
def test_negative_ssh_ca_sat_wrong_cert(ca_sat, rhel_contenthost):
    """Setup Satellite's SSH key's cert, register host, setup incorrect cert on Satellite and run REX on the host

    :id: 7ddd170b-d489-4e2a-93af-ccf0c1a9d4ca

    :expectedresults: Verify the job has failed against the host

    :parametrized: yes
    """
    sat = ca_sat[0]
    host = rhel_contenthost
    sat_ca_file = ca_sat[1]
    command = InstallerCommand(
        foreman_proxy_plugin_remote_execution_script_ssh_user_ca_public_key_file=sat_ca_file,
    )
    assert sat.install(command).status == 0
    register_host(sat, host)

    # create a different cert for the Satellite, with a wrong principal
    sat_ssh_path = '/var/lib/foreman-proxy/ssh/'
    key_name = 'id_rsa_foreman_proxy'
    cert_name = f'{key_name}-cert.pub'
    assert (
        sat.execute(
            f'cd {sat_ssh_path} && ssh-keygen -s /root/CA/id_ca -I satellite -n wronguser {key_name}.pub && restorecon {cert_name} && chown foreman-proxy {cert_name} && chgrp foreman-proxy {cert_name}'
        ).status
        == 0
    )

    # assert the run fails
    with pytest.raises(CLIFactoryError) as err:
        test_execution(sat, host)
    assert 'A sub task failed' in err.value.args[0]
    check = host.execute('grep rex_passed /root/test')
    assert check.status != 0


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match([settings.content_host.default_rhel_version])
def test_positive_ssh_ca_host_only(target_sat, ca_contenthost, host_ca_file_on_satellite):
    """Setup host's SSH key's cert, add CA to Sat, register host and run REX on that host

    :id: 0ad9bbf7-0be5-49ca-8d79-969242b6b9bc

    :expectedresults: Verify the job has been run successfully against the host

    :parametrized: yes
    """
    sat = target_sat
    host = ca_contenthost[0]
    host_ca_file = ca_contenthost[1]
    copy_host_CA(host, sat, host_ca_file, host_ca_file_on_satellite)
    log_save(sat, host)
    command = InstallerCommand(
        foreman_proxy_plugin_remote_execution_script_ssh_host_ca_public_keys_file=host_ca_file_on_satellite,
    )
    assert sat.install(command).status == 0
    register_host(sat, host)
    result = test_execution(sat, host)
    # assert the run actually happened and it was NOT authenticated using cert
    assert result['success'] == '1'
    logger.debug(result)
    assert log_compare(sat, host) != 0
    check = host.execute('grep rex_passed /root/test')
    assert check.status == 0


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match([settings.content_host.default_rhel_version])
def test_negative_ssh_ca_host_wrong_cert(target_sat, ca_contenthost, host_ca_file_on_satellite):
    """Setup host's SSH key's cert, add a different CA to Sat, register host and run REX on that host

    :id: 9e23d27d-a3a8-4c0d-9a0f-892d392aa660

    :expectedresults: Verify the job has failed against the host

    :parametrized: yes
    """
    sat = target_sat
    host = ca_contenthost[0]
    fake_ca_dir = '/'.join(host_ca_file_on_satellite.split('/')[:-1])
    fake_ca_filename = host_ca_file_on_satellite.split('/')[-1]
    sat.execute(
        f'cd {fake_ca_dir} && {{ rm -f {fake_ca_filename}; ssh-keygen -t ed25519 -f {fake_ca_filename} -N ""; }}'
    )
    command = InstallerCommand(
        foreman_proxy_plugin_remote_execution_script_ssh_host_ca_public_keys_file=host_ca_file_on_satellite,
    )
    assert sat.install(command).status == 0
    register_host(sat, host)
    # assert the run failed
    with pytest.raises(CLIFactoryError) as err:
        test_execution(sat, host)
    assert 'A sub task failed' in err.value.args[0]
    check = host.execute('grep rex_passed /root/test')
    assert check.status != 0


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match([settings.content_host.default_rhel_version])
def test_positive_ssh_ca_sat_and_host_ssh_ansible_cockpit(
    ca_sat, ca_contenthost, host_ca_file_on_satellite
):
    """Setup Satellite's SSH key's cert, setup host's SSH key's cert, add CA to Sat, register host and run REX on that host

    :id: 97c17417-3b20-4876-bf9c-7219a91acee2

    :expectedresults: Verify the job has been run successfully against the host, Sat's cert hasn't been added to host's authorized_keys and CA verification has been used instead


    :parametrized: yes
    """
    sat = ca_sat[0]
    sat_ca_file = ca_sat[1]
    host = ca_contenthost[0]
    host_ca_file = ca_contenthost[1]
    copy_host_CA(host, sat, host_ca_file, host_ca_file_on_satellite)
    # setup CA
    log_save(sat, host)
    command = InstallerCommand(
        foreman_proxy_plugin_remote_execution_script_ssh_user_ca_public_key_file=sat_ca_file,
        foreman_proxy_plugin_remote_execution_script_ssh_host_ca_public_keys_file=host_ca_file_on_satellite,
    )
    assert sat.install(command).status == 0
    org = register_host(sat, host, cockpit=True)
    # SSH REX
    result = test_execution(sat, host)
    # assert the run actually happened and it was authenticated using cert
    assert result['success'] == '1'
    logger.debug(result)
    assert log_compare(sat, host) == 0
    check = host.execute('grep rex_passed /root/test')
    assert check.status == 0
    check = host.execute(f'grep {sat.hostname} /root/.ssh/authorized_keys')
    assert check.status != 0
    # ANSIBLE REX
    log_save(sat, host)
    command = "echo rex2_passed $(date) > /root/test"
    invocation_command = sat.cli_factory.job_invocation(
        {
            'job-template': 'Run Command - Ansible Default',
            'inputs': f'command={command}',
            'search-query': f'name ~ {host.hostname}',
        }
    )
    result = sat.cli.JobInvocation.info({'id': invocation_command['id']})
    # assert the run actually happened and it was authenticated using cert
    assert result['success'] == '1'
    logger.debug(result)
    assert log_compare(sat, host) == 0
    check = host.execute('grep rex2_passed /root/test')
    assert check.status == 0
    # COCKPIT
    log_save(sat, host)
    # setup Satellite for cockpit
    sat.register_to_cdn()
    sat.install_cockpit()
    sat.cli.Service.restart()
    # setup cockpit on host
    host.install_cockpit()
    # run cockpit
    # note that merely opening a cockpit in UI connects to ssh already
    # note that this is a UI part, as opposed to the previous parts and previous SSH CA tests
    with sat.ui_session() as session:
        session.organization.select(org_name=org.name)
        hostname_inside_cockpit = session.host.get_webconsole_content(
            entity_name=host.hostname,
            rhel_version=host.os_version.major,
        )
        assert host.hostname in hostname_inside_cockpit, (
            f'cockpit page shows hostname {hostname_inside_cockpit} instead of {host.hostname}'
        )
    assert log_compare(sat, host) == 0
