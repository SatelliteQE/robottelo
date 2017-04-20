# coding=utf-8
"""Module that aggregates common bits of the end to end tests."""
from robottelo.constants import DISTRO_RHEL6
from robottelo.decorators import setting_is_set
from robottelo.vm import VirtualMachine

AK_CONTENT_LABEL = u'rhel-6-server-rhev-agent-rpms'


class ClientProvisioningMixin(object):
    def client_provisioning(
            self, activation_key_name, organization_label,
            package_name='python-kitchen'):
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
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            # Pull rpm from Foreman server and install on client
            vm.install_katello_ca()
            # Register client with foreman server using act keys
            result = vm.register_contenthost(
                organization_label, activation_key_name)
            self.assertTrue(vm.subscribed)
            # Install rpm on client
            result = vm.run('yum install -y {0}'.format(package_name))
            self.assertEqual(result.return_code, 0)
            # Verify that the package is installed by querying it
            result = vm.run('rpm -q {0}'.format(package_name))
            self.assertEqual(result.return_code, 0)
