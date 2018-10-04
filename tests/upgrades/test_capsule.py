"""Test for Capsule related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os

from automation_tools.satellite6 import hammer
from fabric.api import execute, run
from robottelo.test import APITestCase, settings
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import (
    create_dict,
    get_entity_data,
    rpm1,
    rpm2
)


class Scenario_capsule_sync(APITestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test if
    package added to satellite preupgrade is synced to capsule post upgrade.

    Test Steps:

    1. Before Satellite upgrade, Sync a repo/rpm in satellite.
    2. Upgrade satellite/capsule.
    3. Run capsule sync post upgrade.
    4. Check if the repo/rpm is been synced to capsule.

    """
    @classmethod
    def setUpClass(cls):
        cls.sat_host = settings.server.hostname
        cls.cls_name = 'Scenario_capsule_sync'
        cls.cap_host = os.environ.get(
            'RHEV_CAP_HOST', os.environ.get('CAPSULE_HOSTNAME'))
        cls.repo_name = 'capsulesync_TestRepo_' + cls.cls_name
        cls.repo_path = '/var/www/html/pub/preupgradeCapSync_repo/'
        cls.rpm_name = rpm1.split('/')[-1]
        cls.prod_name = 'Scenario_preUpgradeCapSync_' + cls.cls_name
        cls.activation_key = os.environ.get(
            'CAPSULE_AK', os.environ.get('RHEV_CAPSULE_AK'))
        cls.cv_name = 'Scenario_precapSync_' + cls.cls_name
        cls.org_id = '1'
        cls.repo_url = 'http://{0}{1}'.format(
            cls.sat_host, '/pub/preupgradeCapSync_repo/')

    def create_repo(self):
        """ Creates a custom yum repository, that will be synced to satellite
        and later to capsule from satellite
        """
        run('rm -rf {}'.format(self.repo_path))
        run('mkdir {}'.format(self.repo_path))
        run('wget {0} -P {1}'.format(rpm1, self.repo_path))
        # Renaming custom rpm to preRepoSync.rpm
        run('createrepo --database {0}'.format(self.repo_path))

    @pre_upgrade
    def test_pre_user_scenario_capsule_sync(self):
        """Pre-upgrade scenario that creates and sync repository with
        rpm in satellite which will be synced in post upgrade scenario.


        :id: preupgrade-eb8970fa-98cc-4a99-99fb-1c12c4e319c9

        :steps:
            1. Before Satellite upgrade, Sync a repo/rpm in satellite

        :expectedresults: The repo/rpm should be synced to satellite

         """
        _, env_name = hammer.hammer_determine_cv_and_env_from_ak(
            self.activation_key, '1')
        self.create_repo()
        print(hammer.hammer_product_create(self.prod_name, self.org_id))
        prod_list = hammer.hammer(
            'product list --organization-id {}'.format(self.org_id))
        self.assertEqual(
            self.prod_name,
            hammer.get_attribute_value(prod_list, self.prod_name, 'name')
        )
        print(hammer.hammer_repository_create(
            self.repo_name, self.org_id, self.prod_name, self.repo_url))
        repo_list = hammer.hammer(
            'repository list --product {0} --organization-id {1}'.format(
                self.prod_name, self.org_id))
        self.assertEqual(
            self.repo_name,
            hammer.get_attribute_value(repo_list, self.repo_name, 'name')
        )
        print(hammer.hammer_repository_synchronize(
            self.repo_name, self.org_id, self.prod_name))
        print(hammer.hammer_content_view_create(self.cv_name, self.org_id))
        print(hammer.hammer_content_view_add_repository(
            self.cv_name, self.org_id, self.prod_name, self.repo_name))
        print(hammer.hammer_content_view_publish(self.cv_name, self.org_id))
        cv_ver = hammer.get_latest_cv_version(self.cv_name)
        env_data = hammer.hammer(
            'lifecycle-environment list --organization-id {0} '
            '--name {1}'.format(self.org_id, env_name))
        env_id = hammer.get_attribute_value(
            env_data,
            env_name,
            'id'
        )
        print(hammer.hammer_content_view_promote_version(
            self.cv_name, cv_ver, env_id, self.org_id))
        global_dict = {self.__class__.__name__: {
            'env_name': env_name}}
        create_dict(global_dict)

    @post_upgrade
    def test_post_user_scenario_capsule_sync(self):
        """Post-upgrade scenario that sync capsule from satellite and then
        verifies if the repo/rpm of pre-upgrade scenario is synced to capsule


        :id: postupgrade-eb8970fa-98cc-4a99-99fb-1c12c4e319c9

        :steps:
            1. Run capsule sync post upgrade.
            2. Check if the repo/rpm is been synced to capsule.

        :expectedresults:
            1. The capsule sync should be successful
            2. The repos/rpms from satellite should be synced to satellite

         """
        env_name = get_entity_data(self.__class__.__name__)['env_name']
        cap_data = hammer.hammer('capsule list')
        cap_id = hammer.get_attribute_value(cap_data, self.cap_host, 'id')
        org_data = hammer.hammer('organization list')
        org_name = hammer.get_attribute_value(
            org_data, int(self.org_id), 'label')
        print(hammer.hammer(
            'capsule content synchronize --id {0}'.format(cap_id)))
        result = execute(
            lambda: run(
                '[ -f /var/lib/pulp/published/yum/http/repos/'
                '{0}/{1}/{2}/custom/{3}/{4}/Packages/b/{5} ]; echo $?'.format(
                    org_name, env_name, self.cv_name,
                    self.prod_name, self.repo_name, self.rpm_name)),
            host=self.cap_host
        )[self.cap_host]
        self.assertEqual('0', result)


class Scenario_capsule_sync_2(APITestCase):
    """
    The test class contains pre-upgrade and post-upgrade scenarios to test if
    package added postupgrade in satellite is snyced to capsule post upgrade.

    Test Steps:

    1. Upgrade Satellite and Capsule.
    2. Sync a repo/rpm in satellite.
    3. Run capsule sync.
    4. Check if the repo/rpm is been synced to capsule.

    """
    @classmethod
    def setUpClass(cls):
        cls.cls_name = 'Scenario_capsule_sync_2'
        cls.sat_host = settings.server.hostname
        cls.cap_host = os.environ.get(
            'RHEV_CAP_HOST', os.environ.get('CAPSULE_HOSTNAME'))
        cls.repo_name = 'capsulesync_TestRepo_' + cls.cls_name
        cls.repo_path = '/var/www/html/pub/postupgradeCapSync_repo/'
        cls.rpm_name = rpm2.split('/')[-1]
        cls.prod_name = 'Scenario_postUpgradeCapSync_' + cls.cls_name
        cls.activation_key = os.environ.get(
            'CAPSULE_AK', os.environ.get('RHEV_CAPSULE_AK'))
        cls.cv_name = 'Scenario_postcapSync_' + cls.cls_name
        cls.org_id = '1'
        cls.repo_url = 'http://{0}{1}'.format(
            cls.sat_host, '/pub/postupgradeCapSync_repo/')

    def create_repo(self):
        """ Creates a custom yum repository, that will be synced to satellite
        and later to capsule from satellite
        """
        run('rm -rf {}'.format(self.repo_path))
        run('mkdir {}'.format(self.repo_path))
        run('wget {0} -P {1}'.format(rpm2, self.repo_path))
        # Renaming custom rpm to preRepoSync.rpm
        run('createrepo --database {0}'.format(self.repo_path))

    @post_upgrade
    def test_post_user_scenario_capsule_sync_2(self):
        """Post-upgrade scenario that creates and sync repository with
        rpm, sync capsule with satellite and verifies if the repo/rpm in
        satellite is synced to capsule.


        :id: postupgrade-7c1d3441-3e8d-4ac2-8102-30e18274658c

        :steps:
            1. Post Upgrade , Sync a repo/rpm in satellite.
            2. Run capsule sync.
            3. Check if the repo/rpm is been synced to capsule.

        :expectedresults:
            1. The repo/rpm should be synced to satellite
            2. Capsule sync should be successful
            3. The repo/rpm from satellite should be synced to capsule

        """
        _, env_name = hammer.hammer_determine_cv_and_env_from_ak(
            self.activation_key, '1')
        self.create_repo()
        print(hammer.hammer_product_create(self.prod_name, self.org_id))
        prod_list = hammer.hammer(
            'product list --organization-id {}'.format(self.org_id))
        self.assertEqual(
            self.prod_name,
            hammer.get_attribute_value(prod_list, self.prod_name, 'name')
        )
        print(hammer.hammer_repository_create(
            self.repo_name, self.org_id, self.prod_name, self.repo_url))
        repo_list = hammer.hammer(
            'repository list --product {0} --organization-id {1}'.format(
                self.prod_name, self.org_id))
        self.assertEqual(
            self.repo_name,
            hammer.get_attribute_value(repo_list, self.repo_name, 'name')
        )
        print(hammer.hammer_repository_synchronize(
            self.repo_name, self.org_id, self.prod_name))
        print(hammer.hammer_content_view_create(self.cv_name, self.org_id))
        print(hammer.hammer_content_view_add_repository(
            self.cv_name, self.org_id, self.prod_name, self.repo_name))
        print(hammer.hammer_content_view_publish(self.cv_name, self.org_id))
        cv_ver = hammer.get_latest_cv_version(self.cv_name)
        env_data = hammer.hammer(
            'lifecycle-environment list --organization-id {0} '
            '--name {1}'.format(self.org_id, env_name))
        env_id = hammer.get_attribute_value(
            env_data,
            env_name,
            'id'
        )
        print(hammer.hammer_content_view_promote_version(
            self.cv_name, cv_ver, env_id, self.org_id))
        cap_data = hammer.hammer('capsule list')
        cap_id = hammer.get_attribute_value(cap_data, self.cap_host, 'id')
        org_data = hammer.hammer('organization list')
        org_name = hammer.get_attribute_value(
            org_data, int(self.org_id), 'label')
        print(hammer.hammer(
            'capsule content synchronize --id {0}'.format(cap_id)))
        result = execute(
            lambda: run('[ -f /var/lib/pulp/published/yum/http/repos/'
                        '{0}/{1}/{2}/custom/{3}/{4}/Packages/c/{5} ]; '
                        'echo $?'.format(
                            org_name, env_name, self.cv_name,
                            self.prod_name, self.repo_name, self.rpm_name)),
            host=self.cap_host
        )[self.cap_host]
        self.assertEqual('0', result)
