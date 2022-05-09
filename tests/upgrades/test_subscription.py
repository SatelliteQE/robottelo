"""Test for subscription related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SubscriptionManagement

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fabric.api import execute
from nailgun import entities
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests.helpers.scenarios import delete_manifest
from upgrade_tests.helpers.scenarios import dockerize
from upgrade_tests.helpers.scenarios import upload_manifest
from wait_for import wait_for

from robottelo import manifests
from robottelo import ssh
from robottelo.config import settings
from robottelo.upgrade_utility import host_location_update


class TestManifestScenarioRefresh:
    """
    The scenario to test the refresh of a manifest created before upgrade.
    """

    @pytest.mark.skip('Skipping due to manifest refresh issues')
    @pytest.mark.pre_upgrade
    def test_pre_manifest_scenario_refresh(self, request):
        """Before upgrade, upload & refresh the manifest.

        :id: preupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Before Satellite upgrade, upload and refresh manifest.

        :expectedresults: Manifest should be uploaded and refreshed successfully.
        """
        org = entities.Organization(name=f"{request.node.name}_org").create()
        upload_manifest(settings.fake_manifest.url['default'], org.name)
        history = entities.Subscription(organization=org).manifest_history(
            data={'organization_id': org.id}
        )
        assert f"{org.name} file imported successfully." == history[0]['statusMessage']
        sub = entities.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        assert len(sub.search()) > 0

    @pytest.mark.skip('Skipping due to manifest refresh issues')
    @pytest.mark.post_upgrade(depend_on=test_pre_manifest_scenario_refresh)
    def test_post_manifest_scenario_refresh(self, request, dependent_scenario_name):
        """After upgrade, Check the manifest refresh and delete functionality.

        :id: postupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Refresh manifest.
            2. Delete manifest.

        :expectedresults: After upgrade,
            1. Pre-upgrade manifest should be refreshed and deleted.
        """
        pre_test_name = dependent_scenario_name
        org = entities.Organization().search(query={'search': f'name={pre_test_name}_org'})[0]
        request.addfinalizer(org.delete)
        sub = entities.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        assert len(sub.search()) > 0
        delete_manifest(org.name)
        history = entities.Subscription(organization=org).manifest_history(
            data={'organization_id': org.id}
        )
        assert "Subscriptions deleted by foreman_admin" == history[0]['statusMessage']


class TestSubscriptionAutoAttach:
    """
    The scenario to test auto-attachment of subscription on the the client registered before
    upgrade.
    """

    @pytest.mark.pre_upgrade
    def test_pre_subscription_scenario_autoattach(self, request, target_sat):
        """Create content host and register with Satellite

        :id: preupgrade-940fc78c-ffa6-4d9a-9c4b-efa1b9480a22

        :steps:
            1. Before Satellite upgrade.
            2. Create new Organization and Location.
            3. Upload a manifest in it.
            4. Create a AK with 'auto-attach False' and without Subscription add in it.
            5. Create a content host.
            6. Update content host location.

        :expectedresults:
            1. Content host should be created.
            2. Content host location should be updated.
        """
        docker_vm = settings.upgrade.docker_vm
        container_name = f"{request.node.name}_docker_client"
        org = entities.Organization(name=request.node.name + "_org").create()
        loc = entities.Location(name=request.node.name + "_loc", organization=[org]).create()
        manifests.upload_manifest_locked(org.id, interface=manifests.INTERFACE_API)
        act_key = entities.ActivationKey(
            auto_attach=False,
            organization=org.id,
            environment=org.library.id,
            name=request.node.name + "_ak",
        ).create()
        rhel7_client = dockerize(ak_name=act_key.name, distro='rhel7', org_label=org.label)
        client_container_id = [value for value in rhel7_client.values()][0]
        ssh.command(
            f"docker rename {client_container_id} {container_name}", hostname=f'{docker_vm}'
        )
        client_container_hostname = [key for key in rhel7_client.keys()][0]
        host_location_update(client_container_name=f"{client_container_hostname}", loc=loc)
        wait_for(
            lambda: org.name
            in execute(
                docker_execute_command,
                client_container_id,
                'subscription-manager identity',
                host=docker_vm,
            )[docker_vm],
            timeout=300,
            delay=30,
        )
        status = execute(
            docker_execute_command,
            client_container_id,
            'subscription-manager identity',
            host=docker_vm,
        )[docker_vm]
        assert org.name in status

    @pytest.mark.post_upgrade(depend_on=test_pre_subscription_scenario_autoattach)
    def test_post_subscription_scenario_autoattach(
        self, request, dependent_scenario_name, target_sat
    ):
        """Run subscription auto-attach on pre-upgrade content host registered
        with Satellite.

        :id: postupgrade-940fc78c-ffa6-4d9a-9c4b-efa1b9480a22

        :steps:
            1. Run subscription auto-attach on content host.
            2. Delete the content host, activation key, location & organization.

        :expectedresults: After upgrade,
            1. Pre-upgrade content host should get subscribed.
            2. All the cleanup should be completed successfully.
        """
        docker_vm = settings.upgrade.docker_vm
        pre_test_name = dependent_scenario_name
        docker_container_name = f'{pre_test_name}' + "_docker_client"
        docker_hostname = execute(
            docker_execute_command,
            docker_container_name,
            'hostname',
            host=docker_vm,
        )[docker_vm]
        org = entities.Organization().search(query={'search': f'name="{pre_test_name}_org"'})[0]
        request.addfinalizer(org.delete)
        loc = entities.Location().search(query={'search': f'name="{pre_test_name}_loc"'})[0]
        request.addfinalizer(loc.delete)
        act_key = entities.ActivationKey(organization=org).search(
            query={'search': f'name="{pre_test_name}_ak"'}
        )[0]
        request.addfinalizer(act_key.delete)
        host = entities.Host(organization=org).search(
            query={'search': f'name="{docker_hostname.casefold()}"'}
        )[0]
        delete_manifest(org.name)
        request.addfinalizer(host.delete)
        subscription = execute(
            docker_execute_command,
            docker_container_name,
            'subscription-manager attach --auto',
            host=docker_vm,
        )[docker_vm]
        assert 'Subscribed' in subscription
        ssh.command(
            f"docker stop {docker_container_name}; docker rm {docker_container_name}",
            hostname=f'{docker_vm}',
        )
