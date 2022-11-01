"""Common Upgrade test utilities """
from fabric.api import execute
from fabric.api import run
from nailgun import entities
from nailgun.entity_mixins import call_entity_method_with_timeout
from upgrade.helpers.docker import docker_execute_command
from wait_for import wait_for

from robottelo.config import settings


def run_goferd(client_hostname=None):
    """
    Start the goferd process.
    :param: str client_hostname: It should be container's id.
    """

    kwargs = {'async': True, 'host': settings.upgrade.docker_vm}
    execute(docker_execute_command, client_hostname, 'pkill -f gofer', **kwargs)
    execute(docker_execute_command, client_hostname, 'goferd -f', **kwargs)
    status = execute(
        docker_execute_command, client_hostname, 'ps -ef', host=settings.upgrade.docker_vm
    )[settings.upgrade.docker_vm]
    assert "goferd" in status


def check_package_installed(client_hostname=None, package=None):
    """
    Verify if package is installed on docker content host.
    :param: str client_hostname: It should be container's id.
    :param: str package: pass the package name to check the status
    :return: name of the installed package
    """

    kwargs = {'host': settings.upgrade.docker_vm}
    installed_package = execute(
        docker_execute_command, client_hostname, f'rpm -q {package}', **kwargs
    )[settings.upgrade.docker_vm]
    return installed_package


def install_or_update_package(client_hostname=None, update=False, package=None):
    """
    Install/update the package on docker content host.
    :param: str client_hostname: It should be container's id.
    :param: bool update:
    :param: str package:
    """
    kwargs = {'host': settings.upgrade.docker_vm}
    execute(
        docker_execute_command,
        client_hostname,
        'subscription-manager repos --enable=*;yum clean all',
        **kwargs,
    )[settings.upgrade.docker_vm]
    if update:
        command = f'yum update -y {package}'
    else:
        command = f'yum install -y {package}'

    execute(docker_execute_command, client_hostname, command, **kwargs)[settings.upgrade.docker_vm]
    assert package in check_package_installed(client_hostname=client_hostname, package=package)


def create_repo(rpm_name, repo_path, post_upgrade=False, other_rpm=None):
    """Creates a custom yum repository, that will be synced to satellite
    and later to capsule from satellite
    :param: str rpm_name : rpm name, required to create a repository.
    :param: str repo_path: Name of the repository path
    :param: bool post_upgrade: For Pre-upgrade, post_upgrade value will be False
    :param: str other_rpm: If we want to clean a specific rpm and update with
    latest then we pass other rpm.
    """
    if post_upgrade:
        run(f'wget {rpm_name} -P {repo_path}')
        run(f'rm -rf {repo_path + other_rpm}')
        run(f'createrepo --update {repo_path}')
    else:
        run(f'rm -rf {repo_path}')
        run(f'mkdir {repo_path}')
        run(f'wget {rpm_name} -P {repo_path}')
        # Renaming custom rpm to preRepoSync.rpm
        run(f'createrepo --database {repo_path}')


def host_status(client_container_name=None):
    """fetch the content host details.
    :param: str client_container_name: The content host hostname
    :return: nailgun.entity.host: host
    """
    host = entities.Host().search(query={'search': f'{client_container_name}'})
    return host


def host_location_update(client_container_name=None, logger_obj=None, loc=None):
    """Check the content host status (as package profile update task does
    take time to upload) and update location.

    :param: str client_container_name: The content host hostname
    :param: str loc: Location
    """
    if len(host_status(client_container_name=client_container_name)) == 0:
        wait_for(
            lambda: len(host_status(client_container_name=client_container_name)) > 0,
            timeout=100000,
            delay=2,
            logger=logger_obj,
        )
    host_loc = host_status(client_container_name=client_container_name)[0]
    host_loc.location = loc
    host_loc.update(['location'])


def publish_content_view(org=None, repolist=None):
    """
    publish content view and return content view
    :param: str org: Name of the organisation
    :param: str repolist: Name of the repolist
    :return: Return content view
    """

    content_view = entities.ContentView(organization=org).create()
    content_view.repository = repolist if type(repolist) is list else [repolist]
    content_view = content_view.update(['repository'])
    call_entity_method_with_timeout(content_view.publish, timeout=3400000)
    content_view = content_view.read()
    return content_view
