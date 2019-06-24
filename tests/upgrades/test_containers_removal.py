"""Tests verifying that Containers support is properly removed

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ContainerManagement

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
from fauxfactory import gen_string

from nailgun import entities
from robottelo import ssh
from robottelo.test import APITestCase, settings
from robottelo.vm import VirtualMachine
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import (
    create_dict,
    get_entity_data,
)


class Scenario_containers_support_removal(APITestCase):
    """"Verify containers run before upgrade are still running
    after upgrade, despite foreman_docker removal.

    Test Steps:

            1. Before Satellite upgrade.
            2. Create docker host
            3. Create and run container from dockerhub
            4. Create and run container from external registry
            5. Upgrade Satellite
            6. Verify that upgrade procedure removed foreman_docker support
            7. Verify container from dockerhub is still running
            8. Verify container from external registry is still running
    """

    @classmethod
    def setUpClass(cls):
        super(Scenario_containers_support_removal, cls).setUpClass()

    def _vm_cleanup(self, hostname=None):
        """ Cleanup the VM from provisioning server

        :param str hostname: The content host hostname
        """
        if hostname:
            vm = VirtualMachine(
                hostname=hostname,
                target_image=hostname,
                provisioning_server=settings.clients.provisioning_server,
                )
            vm._created = True
            vm.destroy()

    @pre_upgrade
    def test_pre_scenario_containers_support_removal(self):
        """Pre-upgrade scenario test to verify containers created and run
        before upgrade are still running after upgrade.

        :id: preupgrade-f6de07ae-14c7-4452-9cb1-cafe2aa648ae

        :steps:

            1. Create docker host
            2. Create and run container from dockerhub
            3. Create and run container from external registry

        :expectedresults:

            1. Docker host is created
            2. Container from dockerhub is created and running
            3. Container from external registry is created and running

        """
        repo_name = 'rhel'
        compute_resource_name = gen_string('alpha')
        registry_url = settings.docker.external_registry_1

        org = entities.Organization().create()

        docker_host = VirtualMachine(
            source_image=settings.docker.docker_image,
            tag=u'docker'
        )
        docker_host.create()
        try:
            docker_host.install_katello_ca()

            compute_resource = entities.DockerComputeResource(
                name=compute_resource_name,
                organization=[org],
                url='http://{0}:2375'.format(docker_host.ip_addr),
            ).create()

            # Only one registry with given URL can exist on Satellite,
            # so search for it first and create it only if necessary
            try:
                registry = entities.Registry().search(filters={'url': registry_url})[0]
            except IndexError:
                registry = entities.Registry(
                    url=registry_url,
                    organization=[org],
                ).create()

            # container from dockerhub
            dockerhub_container = entities.DockerHubContainer(
                command='sleep inf',
                compute_resource=compute_resource,
                organization=[org],
            ).create()
            self.assertEqual(
                dockerhub_container.compute_resource.id, compute_resource.id)

            # container from external registry
            external_container = entities.DockerRegistryContainer(
                command='sleep inf',
                compute_resource=compute_resource,
                organization=[org],
                registry=registry,
                repository_name=repo_name,
            ).create()
            self.assertEqual(
                external_container.compute_resource.id, compute_resource.id)
            self.assertEqual(external_container.registry.id, registry.id)
            self.assertEqual(external_container.repository_name, repo_name)

            running_containers = docker_host.run('docker ps')
            self.assertEqual(running_containers.return_code, 0)

            self.assertTrue(any(dockerhub_container.name in line
                                for line in running_containers.stdout))
            self.assertTrue(any(external_container.name in line
                                for line in running_containers.stdout))

            scenario_dict = {self.__class__.__name__: {
                'docker_host': docker_host.hostname,
                'dockerhub_container': dockerhub_container.name,
                'external_container': external_container.name,
            }}
            create_dict(scenario_dict)
        except Exception as exp:
            self._vm_cleanup(hostname=docker_host.hostname)
            raise Exception(exp)

    @post_upgrade(depend_on=test_pre_scenario_containers_support_removal)
    def test_post_scenario_containers_support_removal(self):
        """Post-upgrade scenario test to verify containers created and run
        before upgrade are still running after upgrade.

        :id: postupgrade-f6de07ae-14c7-4452-9cb1-cafe2aa648ae

        :steps:

            1. Verify that upgrade procedure removed foreman_docker support
            2. Verify container from dockerhub is still running
            3. Verify container from external registry is still running

        :expectedresults:

            1. Upgrade procedure removed support for foreman_docker
            2. Container from dockerhub is still running
            3. Container from external registry is still running

        """
        entity_data = get_entity_data(self.__class__.__name__)
        docker_host_hostname = entity_data.get('docker_host')
        dockerhub_container = entity_data.get('dockerhub_container')
        external_container = entity_data.get('external_container')

        extract_log_command = "sed -n '/{delimiter}/,/{delimiter}/p' {path}".format(
            delimiter="RemoveForemanDockerSupport",
            path="/var/log/foreman-installer/satellite.log"
        )
        docker_log = ssh.command(extract_log_command, output_format='plain')
        self.assertEqual(docker_log.return_code, 0)

        docker_log = docker_log.stdout.split("\n")

        self.assertTrue(any("RemoveForemanDockerSupport: migrated" in line
                            for line in docker_log))
        self.assertTrue(any("remove_column(:containers, :capsule_id)" in line
                            for line in docker_log))

        removed_tables = ('docker_images', 'docker_tags',
                          'docker_container_wizard_states_images',
                          'containers')

        for table in removed_tables:
            self.assertTrue(any("table_exists?(:{})".format(table)
                                in line for line in docker_log))

        running_containers = ssh.command('docker ps', hostname=docker_host_hostname)
        self.assertEqual(running_containers.return_code, 0)

        self.assertTrue(any(dockerhub_container in line
                            for line in running_containers.stdout))
        self.assertTrue(any(external_container in line
                            for line in running_containers.stdout))

        self._vm_cleanup(hostname=docker_host_hostname)
