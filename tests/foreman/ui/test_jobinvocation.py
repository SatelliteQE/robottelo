"""Test class for Job Invocation procedure

:Requirement: JobInvocation

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from inflection import camelize
from nailgun import entities

from robottelo.cli.host import Host
from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC_ID, DISTRO_RHEL6
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier3
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.vm import VirtualMachine


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_subnet(module_org):
    domain = entities.Domain(organization=[module_org]).create()
    return entities.Subnet(
        domain=[domain],
        gateway=settings.vlan_networking.gateway,
        ipam='DHCP',
        location=[entities.Location(id=DEFAULT_LOC_ID)],
        mask=settings.vlan_networking.netmask,
        network=settings.vlan_networking.subnet,
        network_type='IPv4',
        remote_execution_proxy=[entities.SmartProxy(id=1)],
        organization=[module_org],
    ).create()


@tier3
def test_positive_run_default_job_template_by_ip(
        session, module_org, module_subnet):
    """Run a job template on a host connected by ip

    :id: 9a90aa9a-00b4-460e-b7e6-250360ee8e4d

    :Setup: Use pre-defined job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :CaseLevel: Integration
    """
    with VirtualMachine(
        distro=DISTRO_RHEL6,
        provisioning_server=settings.compute_resources.libvirt_hostname,
        bridge=settings.vlan_networking.bridge,
    ) as client:
        client.install_katello_ca()
        client.register_contenthost(module_org.label, lce='Library')
        assert client.subscribed
        add_remote_execution_ssh_key(client.ip_addr)
        Host.update({
            'name': client.hostname,
            'subnet-id': module_subnet.id,
        })
        # connect to host by ip
        Host.set_parameter({
            'host': client.hostname,
            'name': 'remote_execution_connect_by_ip',
            'value': 'True',
        })
        hostname = client.hostname
        with session:
            session.organization.select(module_org.name)
            assert session.host.search(hostname)[0]['Name'] == hostname
            session.jobinvocation.run({
                'job_category': 'Commands',
                'job_template': 'Run Command - SSH Default',
                'search_query': 'name ^ {}'.format(hostname),
                'template_content.command': 'ls',
            })
            session.jobinvocation.wait_job_invocation_state(
                entity_name='Run ls', host_name=hostname)
            status = session.jobinvocation.read(
                entity_name='Run ls', host_name=hostname)
            assert status['overview']['hosts_table'][0]['Status'] == 'success'


@tier3
def test_positive_run_custom_job_template_by_ip(
        session, module_org, module_subnet):
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
    with VirtualMachine(
            distro=DISTRO_RHEL6,
            provisioning_server=settings.compute_resources.libvirt_hostname,
            bridge=settings.vlan_networking.bridge,
    ) as client:
        client.install_katello_ca()
        client.register_contenthost(module_org.label, lce='Library')
        assert client.subscribed
        add_remote_execution_ssh_key(client.ip_addr)
        Host.update({
            'name': client.hostname,
            'subnet-id': module_subnet.id,
        })
        # connect to host by ip
        Host.set_parameter({
            'host': client.hostname,
            'name': 'remote_execution_connect_by_ip',
            'value': 'True',
        })
        hostname = client.hostname
        job_template_name = gen_string('alpha')
        with session:
            session.organization.select(module_org.name)
            assert session.host.search(hostname)[0]['Name'] == hostname
            session.jobtemplate.create({
                'template.name': job_template_name,
                'template.template_editor.rendering_options': 'Input',
                'template.template_editor.editor': '<%= input("command") %>',
                'job.provider_type': 'SSH',
                'inputs': [{
                    'name': 'command',
                    'required': True,
                    'input_type': 'User input',
                }],
            })
            assert session.jobtemplate.search(
                job_template_name)[0]['Name'] == job_template_name
            session.jobinvocation.run({
                'job_category': 'Miscellaneous',
                'job_template': job_template_name,
                'search_query': 'name ^ {}'.format(hostname),
                'template_content.command': 'ls',
            })
            job_description = '{0} with inputs command="ls"'.format(
                     camelize(job_template_name.lower()))
            session.jobinvocation.wait_job_invocation_state(
                entity_name=job_description,
                host_name=hostname
            )
            status = session.jobinvocation.read(
                entity_name=job_description,
                host_name=hostname
            )
            assert status['overview']['hosts_table'][0]['Status'] == 'success'
