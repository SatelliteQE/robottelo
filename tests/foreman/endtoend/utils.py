"""Module that aggregates common bits of the end to end tests."""
from broker import VMBroker

from robottelo.config import setting_is_set
from robottelo.hosts import ContentHost

AK_CONTENT_LABEL = 'rhel-6-server-rhev-agent-rpms'


class ClientProvisioningMixin:
    def client_provisioning(
        self, activation_key_name, organization_label, package_name='python-kitchen'
    ):
        """Provision a Satellite's client.

        Do the following:

        1. Install Katello CA cert on the client
        2. Register the client using Activation Key
        3. Install a package on the client served by the Satellite server.

        :param activation_key_name: Name of the Activation Key to register.
        :param organization_label: Organization label where the Activation Key
            is available.
        :param package_name: Name of the package to be installed on the client.
        """
        if not setting_is_set('clients'):
            return
        with VMBroker(nick='rhel6', host_classes={'host': ContentHost}) as host:
            # Pull rpm from Foreman server and install on client
            host.install_katello_ca()
            # Register client with foreman server using act keys
            host.register_contenthost(organization_label, activation_key_name)
            assert host.subscribed
            # Install rpm on client
            result = host.run(f'yum install -y {package_name}')
            assert result.status == 0
            # Verify that the package is installed by querying it
            result = host.run(f'rpm -q {package_name}')
            assert result.status == 0
