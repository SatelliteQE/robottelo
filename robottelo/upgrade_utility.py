"""Common Upgrade test utilities """
from fabric.api import execute
from robottelo.test import settings
from upgrade.helpers.docker import docker_execute_command


class CommonUpgradeUtility(object):
    """
    This class will be used by upgrade test cases to re-utilize all the defined module
    in their test cases execution.
    """
    def __init__(self, container_id=None, package=None):
        self.client_container_id = container_id
        self.package = package

    def run_goferd(self):
        """Start the goferd process."""

        kwargs = {'async': True, 'host': settings.upgrade.docker_vm}
        execute(
            docker_execute_command,
            self.client_container_id,
            'pkill -f gofer',
            **kwargs
        )
        execute(
            docker_execute_command,
            self.client_container_id,
            'goferd -f',
            **kwargs
        )
        status = execute(docker_execute_command, self.client_container_id, 'ps -aux',
                         host=settings.upgrade.docker_vm)[settings.upgrade.docker_vm]
        return status

    def check_package_installed(self):
        """Verify if package is installed on docker content host."""

        kwargs = {'host': settings.upgrade.docker_vm}
        installed_package = execute(
            docker_execute_command,
            self.client_container_id,
            'yum list installed {}'.format(self.package),
            **kwargs
        )[settings.upgrade.docker_vm]
        return installed_package

    def install_or_update_package(self, update=False):
        """
        Install/update the package on docker content host.
        :param bool update:
        """
        kwargs = {'host': settings.upgrade.docker_vm}
        execute(docker_execute_command,
                self.client_container_id,
                'subscription-manager repos --enable=*;yum clean all',
                **kwargs)[settings.upgrade.docker_vm]
        if update:
            command = 'yum update -y {}'.format(self.package)
        else:
            command = 'yum install -y {}'.format(self.package)

        execute(docker_execute_command, self.client_container_id, command, **kwargs)[
            settings.upgrade.docker_vm]
        self.assertIn(self.check_package_installed(), self.package)

    def assertIn(self, member, container):
        """
        This method is used to check the member existence in
        container otherwise raise an exception.

        :param member
        :param container
        :return:
        """
        if member not in container:
            standardMsg = '{} not found in {}' .format(member, container)
            raise Exception(standardMsg)
