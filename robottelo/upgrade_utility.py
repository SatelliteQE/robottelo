"""Common Upgrade test utilities """

from wait_for import wait_for
from fabric.api import execute, run
from robottelo.vm import VirtualMachine, settings
from upgrade.helpers.docker import docker_execute_command
from robottelo.api.utils import call_entity_method_with_timeout, entities


class CommonUpgradeUtility(object):
    """ CommonUpgradeUtility class for upgrade test cases """

    def __init__(self, container_id=None):
        self.client_container_id = container_id

    def run_goferd(self):
        """
        Start the goferd process.
        :return: status of execution
        """

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
        status = execute(docker_execute_command, self.client_container_id, 'ps -ef',
                         host=settings.upgrade.docker_vm)[settings.upgrade.docker_vm]
        return status

    def check_package_installed(self, package=None):
        """
        Verify if package is installed on docker content host."""

        kwargs = {'host': settings.upgrade.docker_vm}
        installed_package = execute(
            docker_execute_command,
            self.client_container_id,
            'yum list installed {}'.format(package),
            **kwargs
        )[settings.upgrade.docker_vm]
        return installed_package

    def install_or_update_package(self, update=False, package=None):
        """
        Install/update the package on docker content host.
        :param bool update:
        :param str package:
        :return:
        """
        kwargs = {'host': settings.upgrade.docker_vm}
        execute(docker_execute_command,
                self.client_container_id,
                'subscription-manager repos --enable=*;yum clean all',
                **kwargs)[settings.upgrade.docker_vm]
        if update:
            command = 'yum update -y {}'.format(package)
        else:
            command = 'yum install -y {}'.format(package)

        execute(docker_execute_command, self.client_container_id, command, **kwargs)[
            settings.upgrade.docker_vm]
        self.assertIn(self.check_package_installed(), package)

    def create_repo(self, rpm_name, repo_path, post_upgrade=False, other_rpm=None):
        """ Creates a custom yum repository, that will be synced to satellite
        and later to capsule from satellite
        :param str rpm_name : rpm name, required to create a repository.
        :param str repo_path: Name of the repository path
        :param bool post_upgrade: For Pre-upgrade, post_upgrade value will be False
        :param str other_rpm: If we want to clean a specific rpm and update with
        latest then we pass other rpm.
        :return:
        """
        if post_upgrade:
            run('wget {0} -P {1}'.format(rpm_name, repo_path))
            run('rm -rf {0}'.format(repo_path + other_rpm))
            run('createrepo --update {0}'.format(repo_path))
        else:
            run('rm -rf {}'.format(repo_path))
            run('mkdir {}'.format(repo_path))
            run('wget {0} -P {1}'.format(rpm_name, repo_path))
            # Renaming custom rpm to preRepoSync.rpm
            run('createrepo --database {0}'.format(repo_path))

    def host_status(self, client_container_name=None):
        """ fetch the content host details.
        :param: str client_container_name: The content host hostname
        :return: nailgun.entity.host: host
        """
        host = entities.Host().search(
            query={'search': '{0}'.format(client_container_name)})
        return host

    def host_location_update(self, client_container_name=None, loc=None):
        """ Check the content host status (as package profile update task does take time to
        upload) and update location.

        :param: str client_container_name: The content host hostname
        :param: str loc: Location
        :return:
        """
        if len(self.host_status(client_container_name=client_container_name)) == 0:
            wait_for(
                lambda: len(self.host_status(client_container_name=client_container_name
                                             )) > 0,
                timeout=100,
                delay=2,
                logger=self.logger
            )
        host_loc = self.host_status(client_container_name=client_container_name)[0]
        host_loc.location = loc
        host_loc.update(['location'])

    def publish_content_view(self, org=None, repolist=None):
        """
        publish content view and return content view
        :param str org: Name of the organisation
        :param str repolist: Name of the repolist
        :return Return content view
        """

        content_view = entities.ContentView(organization=org).create()
        content_view.repository = repolist
        content_view = content_view.update(['repository'])
        call_entity_method_with_timeout(content_view.publish, timeout=3400)
        content_view = content_view.read()
        return content_view

    def cleanup_of_provisioned_server(self, hostname=None, provisioning_server=None,
                                      distro=None):
        """ Cleanup the VM from provisioning server

        :param str hostname: The content host hostname
        :param str provisioning_server: provision server name
        :param str distro: distro type
        """
        if hostname:
            vm = VirtualMachine(
                hostname=hostname,
                target_image=hostname,
                provisioning_server=provisioning_server,
                distro=distro,
            )
            vm._created = True
            vm.destroy()

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
