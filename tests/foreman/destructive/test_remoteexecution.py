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


def register_host(satellite, host):
    org = satellite.cli.Org.create({'name': gen_string('alpha')})
    # repo = settings.repos['SATCLIENT_REPO'][f'RHEL{host.os_version.major}']
    lce = satellite.cli_factory.make_lifecycle_environment({'organization-id': org['id']})
    cv = satellite.cli_factory.make_content_view({'organization-id': org['id']})
    satellite.cli.ContentView.publish({'id': cv['id']})
    cvv = satellite.cli.ContentView.info({'id': cv['id']})['versions'][0]
    satellite.cli.ContentView.version_promote(
        {'id': cvv['id'], 'to-lifecycle-environment-id': lce['id']}
    )
    ak_with_cv = satellite.cli_factory.make_activation_key(
        {
            'organization-id': org['id'],
            'lifecycle-environment-id': lce.id,
            'content-view-id': cv.id,
            'name': gen_string('alpha'),
        }
    )
    # host.register(org, None, ak_with_cv.name, satellite, repo_data=f'repo={repo}')
    host.register(org, None, ak_with_cv.name, satellite)


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
        f'journalctl -u sshd | grep {satellite.ip} | grep CA | wc -l > /root/saved_sshd_log'
    )


def log_compare(satellite, host):
    return host.execute(
        f'[ $(( $(cat /root/saved_sshd_log) + 1 )) -eq $(journalctl -u sshd | grep {satellite.ip} | grep " CA " | wc -l) ]'
    ).status


def copy_host_CA(host, satellite, host_path, satellite_path):
    host_ca_file_local = f'/tmp/{gen_string("alpha")}'
    host.get(host_path, host_ca_file_local)
    satellite.put(host_ca_file_local, satellite_path)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match([settings.content_host.default_rhel_version])
def test_positive_ssh_ca_sat_only(ca_sat, rhel_contenthost):
    sat = ca_sat[0]
    host = rhel_contenthost
    sat_ca_file = ca_sat[1]
    log_save(sat, host)
    command = InstallerCommand(
        foreman_proxy_plugin_remote_execution_script_ssh_user_ca_public_keys_file=sat_ca_file,
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


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match([settings.content_host.default_rhel_version])
def test_positive_ssh_ca_host_only(target_sat, ca_contenthost, host_ca_file_on_satellite):
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
def test_positive_ssh_ca_sat_and_host(ca_sat, ca_contenthost, host_ca_file_on_satellite):
    sat = ca_sat[0]
    sat_ca_file = ca_sat[1]
    host = ca_contenthost[0]
    host_ca_file = ca_contenthost[1]
    copy_host_CA(host, sat, host_ca_file, host_ca_file_on_satellite)
    log_save(sat, host)
    command = InstallerCommand(
        foreman_proxy_plugin_remote_execution_script_ssh_user_ca_public_key_file=sat_ca_file,
        foreman_proxy_plugin_remote_execution_script_ssh_host_ca_public_keys_file=host_ca_file_on_satellite,
    )
    assert sat.install(command).status == 0
    register_host(sat, host)
    # SSH REX
    result = test_execution(sat, host)
    # assert the run actually happened and it was authenticated using cert
    assert result['success'] == '1'
    logger.debug(result)
    assert log_compare(sat, host) == 0
    check = host.execute('grep rex_passed /root/test')
    assert check.status == 0
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
