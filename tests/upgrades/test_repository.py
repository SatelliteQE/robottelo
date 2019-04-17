"""Test for Repository related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fabric.api import execute, run
import os
from wait_for import wait_for

from nailgun import entities
from robottelo import ssh
from robottelo.api.utils import create_sync_custom_repo, promote
from robottelo.test import APITestCase, settings
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import (
    create_dict,
    dockerize,
    get_entity_data,
    rpm1,
    rpm2
)


class Scenario_repository_upstream_authorization_check(APITestCase):
    """ This test scenario is to verify the upstream username in post-upgrade for a custom
    repository which does have a upstream username but not password set on it in pre-upgrade.

    Test Steps:

        1. Before Satellite upgrade, Create a custom repository and sync it.
        2. Set the upstream username on same repository using foreman-rake.
        3. Upgrade Satellite.
        4. Check if the upstream username value is removed for same repository.
    """

    @classmethod
    def setUpClass(cls):
        cls.upstream_username = 'rTtest123'

    @pre_upgrade
    def test_pre_repository_scenario_upstream_authorization(self):
        """ Create a custom repository and set the upstream username on it.

        :id: preupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Create a custom repository and sync it.
            2. Set the upstream username on same repository using foreman-rake.

        :expectedresults:
            1. Upstream username should be set on repository.

        :BZ: 1641785
        """

        org = entities.Organization().create()
        custom_repo = create_sync_custom_repo(org_id=org.id)
        rake_repo = 'repo = Katello::Repository.find_by_id({0})'.format(custom_repo)
        rake_username = '; repo.upstream_username = "{0}"'.format(self.upstream_username)
        rake_repo_save = '; repo.save!(validate: false)'
        result = run("echo '{0}{1}{2}'|foreman-rake console".format(rake_repo, rake_username,
                                                                    rake_repo_save))
        self.assertIn('true', result)

        global_dict = {
            self.__class__.__name__: {'repo_id': custom_repo}
        }
        create_dict(global_dict)

    @post_upgrade
    def test_post_repository_scenario_upstream_authorization(self):
        """ Verify upstream username for pre-upgrade created repository.

        :id: postupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Verify upstream username for pre-upgrade created repository using
            foreman-rake.

        :expectedresults:
            1. upstream username should not exists on same repository.

        :BZ: 1641785
        """

        repo_id = get_entity_data(self.__class__.__name__)['repo_id']
        rake_repo = 'repo = Katello::RootRepository.find_by_id({0})'.format(repo_id)
        rake_username = '; repo.upstream_username'
        result = run("echo '{0}{1}'|foreman-rake console".format(rake_repo, rake_username))
        self.assertNotIn(self.upstream_username, result)


class Scenario_custom_repo_check(APITestCase):
    """" Scenario test to verify if we can create a custom repository and consume it
    via client then we alter the created custom repository and satellite will be able
    to sync back the repo.

    Test Steps:

            1. Before Satellite upgrade.
            2. Create new Organization and Location.
            3. Create Product, custom repo, cv.
            4. Create activation key and add subscription in it.
            5. Create a content host, register and install package on it.
            6. Upgrade Satellite.
            7. Remove Old package and add new package into custom repo.
            8. Sync repo, publish new version of cv.
            9  Try to install new package on client.

    BZ: 1429201,1698549
    """

    @classmethod
    def setUpClass(cls):
        cls.sat_host = settings.server.hostname
        cls.docker_vm = os.environ.get('DOCKER_VM')
        cls.file_path = '/var/www/html/pub/custom_repo/'
        cls.custom_repo = 'https://{0}{1}'.format(cls.sat_host, '/pub/custom_repo/')
        _, cls.rpm1_name = os.path.split(rpm1)
        _, cls.rpm2_name = os.path.split(rpm2)

    def _check_package_installed(self, client_container_id, package):
        """Verify if package is installed on docker content host.

        :param: str client_container_id: Container ID
        :param: str package : Package name
        """
        kwargs = {'host': self.docker_vm}
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'rpm -qa|grep {}'.format(package),
            **kwargs
        )[self.docker_vm]
        self.assertIn(package, installed_package)

    def _create_repo(self, post_upgrade=False):
        """ Creates a custom yum repository, that will be synced to satellite
        """
        if post_upgrade:
            run('wget {0} -P {1}'.format(rpm2, self.file_path))
            run('rm -rf {0}'.format(self.file_path + self.rpm1_name))
            run('createrepo --update {0}'.format(self.file_path))
        else:
            run('mkdir /var/www/html/pub/custom_repo')
            run('wget {0} -P {1}'.format(rpm1, self.file_path))
            run('createrepo --database {0}'.format(self.file_path))

    def _install_package(self, client_container_id, package):
        """Install the package on docker content host.

        :param: str client_container_id: Container ID
        :param: str package : package name
        """
        rpm_name = package.split('-')[0]
        kwargs = {'host': self.docker_vm}
        execute(docker_execute_command,
                client_container_id,
                'subscription-manager repos;yum clean all',
                **kwargs)[self.docker_vm]
        command = 'yum install -y {}'.format(rpm_name)
        execute(docker_execute_command, client_container_id, command, **kwargs)[self.docker_vm]
        self._check_package_installed(client_container_id, rpm_name)

    def _host_status(self, client_container_name=None):
        """ fetch the content host details.

        :param: str client_container_name: The content host hostname
        :return: nailgun.entity.host: host
        """
        host = entities.Host().search(
            query={'search': '{0}'.format(client_container_name)})
        return host

    def _host_location_update(self, client_container_name=None, loc=None):
        """ Check the content host status (as package profile update task does take time to
        upload) and update location.

        :param: str client_container_name: The content host hostname
        :param: str loc: Location
        """
        if len(self._host_status(client_container_name=client_container_name)) == 0:
            wait_for(
                lambda: len(self._host_status(client_container_name=client_container_name)) > 0,
                timeout=100,
                delay=2,
                logger=self.logger
            )
        host_loc = self._host_status(client_container_name=client_container_name)[0]
        host_loc.location = loc
        host_loc.update(['location'])

    def _create_publish_content_view(self, org, repo):
        """publish content view and return content view"""
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        return content_view

    @pre_upgrade
    def test_pre_scenario_custom_repo_check(self):
        """This is pre-upgrade scenario test to verify if we can create a
         custom repository and consume it via content host.

        :id: preupgrade-eb6831b1-c5b6-4941-a325-994a09467478

        :steps:
            1. Before Satellite upgrade.
            2. Create new Organization, Location.
            3. Create Product, custom repo, cv.
            4. Create activation key and add subscription.
            5. Create a content host, register and install package on it.

        :expectedresults:

            1. Custom repo is created.
            2. Package is installed on Content host.

        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        lce = entities.LifecycleEnvironment(organization=org).create()

        product = entities.Product(organization=org).create()

        self._create_repo()
        repo = entities.Repository(product=product.id, url=self.custom_repo).create()
        repo.sync()

        content_view = self._create_publish_content_view(org=org, repo=repo)
        promote(content_view.version[0], lce.id)

        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            'Packages/b/|grep {}'.format(org.label,
                                         lce.name,
                                         content_view.label,
                                         product.label,
                                         repo.label,
                                         self.rpm1_name)

            )

        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

        subscription = entities.Subscription(organization=org).search(
            query={'search': 'name={}'.format(product.name)})[0]
        ak = entities.ActivationKey(content_view=content_view,
                                    organization=org.id,
                                    environment=lce).create()
        ak.add_subscriptions(data={'subscription_id': subscription.id})

        rhel7_client = dockerize(ak_name=ak.name, distro='rhel7', org_label=org.label)
        client_container_id = [value for value in rhel7_client.values()][0]
        client_container_name = [key for key in rhel7_client.keys()][0]

        self._host_location_update(client_container_name=client_container_name, loc=loc)
        status = execute(docker_execute_command,
                         client_container_id,
                         'subscription-manager identity',
                         host=self.docker_vm)[self.docker_vm]
        self.assertIn(org.name, status)
        self._install_package(client_container_id, self.rpm1_name)

        scenario_dict = {self.__class__.__name__: {
            'content_view_name': content_view.name,
            'lce_id': lce.id,
            'lce_name': lce.name,
            'org_label': org.label,
            'prod_label': product.label,
            'rhel_client': rhel7_client,
            'repo_name': repo.name,
        }}
        create_dict(scenario_dict)

    @post_upgrade
    def test_post_scenario_custom_repo_check(self):
        """This is post-upgrade scenario test to verify if we can alter the
        created custom repository and satellite will be able to sync back
        the repo.

        :id: postupgrade-5c793577-e573-46a7-abbf-b6fd1f20b06e

        :steps:
            1. Remove old and add new package into custom repo.
            2. Sync repo , publish the new version of cv.
            3. Try to install new package on client.


        :expectedresults: Content host should able to pull the new rpm.

        """
        entity_data = get_entity_data(self.__class__.__name__)
        client = entity_data.get('rhel_client')
        client_container_id = list(client.values())[0]
        content_view_name = entity_data.get('content_view_name')
        lce_id = entity_data.get('lce_id')
        lce_name = entity_data.get('lce_name')
        org_label = entity_data.get('org_label')
        prod_label = entity_data.get('prod_label')
        repo_name = entity_data.get('repo_name')

        self._create_repo(post_upgrade=True)
        repo = entities.Repository(name=repo_name).search()[0]
        repo.sync()

        content_view = entities.ContentView(name=content_view_name).search()[0]
        content_view.publish()

        content_view = entities.ContentView(name=content_view_name).search()[0]
        promote(content_view.version[-1], lce_id)

        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            'Packages/c/| grep {}'.format(org_label,
                                          lce_name,
                                          content_view.label,
                                          prod_label,
                                          repo.label,
                                          self.rpm2_name)
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

        self._install_package(client_container_id, self.rpm2_name)
