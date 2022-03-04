"""Test class for puppet plugin CLI

:Requirement: Puppet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
import requests
from fauxfactory import gen_string


def test_positive_puppet_bootstrap(
    session_puppet_enabled_sat,
    session_puppet_enabled_proxy,
    session_puppet_default_os,
    module_puppet_org,
    module_puppet_environment,
):
    """Test that provisioning template renders snippet for puppet bootstrapping.

    :id: 71140e1a-6e4d-4110-bb2d-8d381f183d64

    :setup:
        1. Requires Satellite with http and templates feature enabled.

    :steps:
        1. Create a host providing puppet env, proxy and params.
        2. Get rendered provisioning template using host's token.
        3. Check the render contains puppet snippet in it.

    :expectedresults:
        1. Puppet snippet rendered in the provisioning template.

    """
    host_params = [
        {
            'name': 'enable-puppet7',
            'value': 'True',
            'parameter-type': 'boolean',
        }
    ]

    host = session_puppet_enabled_sat.api.Host(
        build=True,
        environment=module_puppet_environment,
        host_parameters_attributes=host_params,
        organization=module_puppet_org,
        operatingsystem=session_puppet_default_os,
        puppet_proxy=session_puppet_enabled_proxy,
        puppet_ca_proxy=session_puppet_enabled_proxy,
        root_pass=gen_string('alphanumeric'),
    ).create()

    render = requests.get(
        (
            f'http://{session_puppet_enabled_sat.hostname}:8000/'
            f'unattended/provision?token={host.token}'
        ),
    ).text

    puppet_config = (
        "if [ -f /usr/bin/dnf ]; then\n"
        "  dnf -y install puppet-agent\n"
        "else\n"
        "  yum -t -y install puppet-agent\n"
        "fi\n"
        "\n"
        "cat > /etc/puppetlabs/puppet/puppet.conf << EOF\n"
        "[main]\n"
        "\n"
        "[agent]\n"
        "pluginsync      = true\n"
        "report          = true\n"
        f"ca_server       = {session_puppet_enabled_proxy.name}\n"
        f"certname        = {host.name}\n"
        f"server          = {session_puppet_enabled_proxy.name}\n"
        f"environment     = {module_puppet_environment.name}\n"
    )
    puppet_run = (
        'puppet agent --config /etc/puppetlabs/puppet/puppet.conf --onetime '
        f'--tags no_such_tag --server {session_puppet_enabled_proxy.name}'
    )

    assert puppet_config in render
    assert puppet_run in render
