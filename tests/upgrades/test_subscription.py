"""Test for subscription related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fabric.api import execute
from nailgun import entities
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import delete_manifest
from upgrade_tests.helpers.scenarios import dockerize
from upgrade_tests.helpers.scenarios import get_entity_data
from upgrade_tests.helpers.scenarios import upload_manifest
from wait_for import wait_for

from robottelo import manifests
from robottelo.test import APITestCase
from robottelo.test import settings
from robottelo.upgrade_utility import host_location_update


class Scenario_manifest_refresh(APITestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    manifest refresh before and after upgrade

    Test Steps:

    1. Before Satellite upgrade, upload a manifest.
    2. Refresh the manifest.
    3. Upgrade satellite.
    4. Refresh the manifest.
    5. Delete the manifest.

    """

    @classmethod
    def setUpClass(cls):
        cls.org_name = 'preupgrade_subscription_org'
        cls.manifest_url = settings.fake_manifest.url

    @pre_upgrade
    def test_pre_manifest_scenario_refresh(self):
        """Pre-upgrade scenario that upload and refresh manifest in satellite
         which will be refreshed in post upgrade scenario.


        :id: preupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Before Satellite upgrade, upload and refresh manifest.

        :expectedresults: Manifest should upload and refresh successfully.
         """
        org = entities.Organization(name=self.org_name).create()
        upload_manifest(self.manifest_url['default'], org.name)
        history = entities.Subscription(organization=org).manifest_history(
            data={'organization_id': org.id}
        )
        self.assertEqual(
            "{0} file imported successfully.".format(org.name), history[0]['statusMessage']
        )
        sub = entities.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        self.assertGreater(len(sub.search()), 0)

    @post_upgrade(depend_on=test_pre_manifest_scenario_refresh)
    def test_post_manifest_scenario_refresh(self):
        """Post-upgrade scenario that verifies manifest refreshed successfully
        and deleted successfully.

        :id: postupgrade-29b246aa-2c7f-49f4-870a-7a0075e184b1

        :steps:
            1. Refresh manifest
            2. Delete manifest

        :expectedresults:
            1. The manifest should refresh and delete successfully.
         """
        org = entities.Organization().search(query={'search': 'name={0}'.format(self.org_name)})[0]
        sub = entities.Subscription(organization=org)
        sub.refresh_manifest(data={'organization_id': org.id})
        self.assertGreater(len(sub.search()), 0)
        delete_manifest(self.org_name)
        history = entities.Subscription(organization=org).manifest_history(
            data={'organization_id': org.id}
        )
        self.assertEqual("Subscriptions deleted by foreman_admin", history[0]['statusMessage'])


class Scenario_contenthost_subscription_autoattach_check(APITestCase):
    """Test subscription auto-attach post migration on a pre-upgrade client registered with
    Satellite.

        Test Steps:

        1. Before Satellite upgrade.
        2. Create new Organization and Location.
        3. Upload a manifest in it.
        4. Create a AK with 'auto-attach False' and without Subscription add in it.
        5. Create a content host.
        6. Update content host location.
        7. Upgrade Satellite/Capsule.
        8. Run subscription auto-attach on content host.
        9. Check if it is Subscribed.
    """

    @classmethod
    def setUpClass(cls):
        cls.docker_vm = settings.upgrade.docker_vm

    @pre_upgrade
    def test_pre_subscription_scenario_autoattach(self):
        """Create content host and register with Satellite

        :id: preupgrade-940fc78c-ffa6-4d9a-9c4b-efa1b9480a22

        :steps:
            1. Before Satellite upgrade.
            2. Create new Organization and Location
            3. Upload a manifest in it.
            4. Create a AK with 'auto-attach False' and without Subscription add in it.
            5. Create a content host.
            6. Update content host location.

        :expectedresults:
            1. Content host should be created.
            2. Content host location should be updated.
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        manifests.upload_manifest_locked(org.id, interface=manifests.INTERFACE_API)
        act_key = entities.ActivationKey(
            auto_attach=False, organization=org.id, environment=org.library.id
        ).create()
        rhel7_client = dockerize(ak_name=act_key.name, distro='rhel7', org_label=org.label)
        client_container_id = [value for value in rhel7_client.values()][0]
        client_container_name = [key for key in rhel7_client.keys()][0]
        host_location_update(
            client_container_name=client_container_name, logger_obj=self.logger, loc=loc
        )

        wait_for(
            lambda: org.name
            in execute(
                docker_execute_command,
                client_container_id,
                'subscription-manager identity',
                host=self.docker_vm,
            )[self.docker_vm],
            timeout=100,
            delay=2,
            logger=self.logger,
        )
        status = execute(
            docker_execute_command,
            client_container_id,
            'subscription-manager identity',
            host=self.docker_vm,
        )[self.docker_vm]
        self.assertIn(org.name, status)

        global_dict = {self.__class__.__name__: {'client_container_id': client_container_id}}
        create_dict(global_dict)

    @post_upgrade(depend_on=test_pre_subscription_scenario_autoattach)
    def test_post_subscription_scenario_autoattach(self):
        """Run subscription auto-attach on pre-upgrade content host registered
        with Satellite.

        :id: postupgrade-940fc78c-ffa6-4d9a-9c4b-efa1b9480a22

        :steps:
            1. Run subscription auto-attach on content host.

        :expectedresults:
            1. Pre-upgrade content host should get Subscribed.
         """
        client_container_id = get_entity_data(self.__class__.__name__)['client_container_id']
        subscription = execute(
            docker_execute_command,
            client_container_id,
            'subscription-manager attach --auto',
            host=self.docker_vm,
        )[self.docker_vm]
        self.assertIn('Subscribed', subscription)
