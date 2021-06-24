"""Test class for Job Invocation procedure

:Requirement: JobInvocation

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from inflection import camelize
from nailgun import entities

from robottelo.api.utils import update_vm_host_location
from robottelo.cli.host import Host
from robottelo.config import settings
from robottelo.datafactory import gen_string
from robottelo.helpers import add_remote_execution_ssh_key


def _setup_host_client(client, org_label, subnet_id=None, by_ip=True):
    """Setup a broker host for remote execution.

    :param Broker rhel client: where client is broker instance.
    :param str org_label: The organization label.
    :param int subnet: (Optional) Nailgun subnet entity id, to be used by the host client.
    :param bool by_ip: Whether remote execution will use ip or host name to access server.
    """
    client.install_katello_ca()
    client.register_contenthost(org_label, lce='Library')
    assert client.subscribed
    add_remote_execution_ssh_key(client.ip_addr)
    if subnet_id is not None:
        Host.update({'name': client.hostname, 'subnet-id': subnet_id})
    if by_ip:
        # connect to host by ip
        Host.set_parameter(
            {'host': client.hostname, 'name': 'remote_execution_connect_by_ip', 'value': 'True'}
        )


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_loc(module_org):
    location = entities.Location(organization=[module_org]).create()
    smart_proxy = (
        entities.SmartProxy().search(query={'search': f'name={settings.server.hostname}'})[0].read()
    )
    smart_proxy.location.append(entities.Location(id=location.id))
    smart_proxy.update(['location'])
    return location


@pytest.fixture
def module_rhel_client_by_ip(module_org, module_loc, rhel7_contenthost):
    """Setup a broker rhel client to be used in remote execution by ip"""
    _setup_host_client(rhel7_contenthost, module_org.label)
    update_vm_host_location(rhel7_contenthost, location_id=module_loc.id)
    yield rhel7_contenthost


@pytest.mark.tier4
def test_positive_run_default_job_template_by_ip(session, module_org, module_rhel_client_by_ip):
    """Run a job template on a host connected by ip

    :id: 9a90aa9a-00b4-460e-b7e6-250360ee8e4d

    :Setup: Use pre-defined job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :CaseLevel: System
    """
    hostname = module_rhel_client_by_ip.hostname
    with session:
        session.organization.select(module_org.name)
        assert session.host.search(hostname)[0]['Name'] == hostname
        session.jobinvocation.run(
            {
                'job_category': 'Commands',
                'job_template': 'Run Command - SSH Default',
                'search_query': f'name ^ {hostname}',
                'template_content.command': 'ls',
            }
        )
        session.jobinvocation.wait_job_invocation_state(entity_name='Run ls', host_name=hostname)
        status = session.jobinvocation.read(entity_name='Run ls', host_name=hostname)
        assert status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.tier4
def test_positive_run_custom_job_template_by_ip(session, module_org, module_rhel_client_by_ip):
    """Run a job template on a host connected by ip

    :id: e283ae09-8b14-4ce1-9a76-c1bbd511d58c

    :Setup: Create a working job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :CaseLevel: System
    """
    hostname = module_rhel_client_by_ip.hostname
    job_template_name = gen_string('alpha')
    with session:
        session.organization.select(module_org.name)
        assert session.host.search(hostname)[0]['Name'] == hostname
        session.jobtemplate.create(
            {
                'template.name': job_template_name,
                'template.template_editor.rendering_options': 'Editor',
                'template.template_editor.editor': '<%= input("command") %>',
                'job.provider_type': 'SSH',
                'inputs': [{'name': 'command', 'required': True, 'input_type': 'User input'}],
            }
        )
        assert session.jobtemplate.search(job_template_name)[0]['Name'] == job_template_name
        session.jobinvocation.run(
            {
                'job_category': 'Miscellaneous',
                'job_template': job_template_name,
                'search_query': f'name ^ {hostname}',
                'template_content.command': 'ls',
            }
        )
        job_description = f'{camelize(job_template_name.lower())} with inputs command="ls"'
        session.jobinvocation.wait_job_invocation_state(
            entity_name=job_description, host_name=hostname
        )
        status = session.jobinvocation.read(entity_name=job_description, host_name=hostname)
        assert status['overview']['hosts_table'][0]['Status'] == 'success'
