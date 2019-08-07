"""Test for Capsule related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fabric.api import execute, run
from nailgun import entities
from robottelo.test import APITestCase, settings
from robottelo.api.utils import promote, call_entity_method_with_timeout
from upgrade.helpers.tasks import wait_untill_capsule_sync
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
        cls.cap_host = settings.upgrade.rhev_cap_host or settings.upgrade.capsule_hostname
        cls.repo_name = 'capsulesync_TestRepo_' + cls.cls_name
        cls.repo_path = '/var/www/html/pub/preupgradeCapSync_repo/'
        cls.rpm_name = rpm1.split('/')[-1]
        cls.prod_name = 'Scenario_preUpgradeCapSync_' + cls.cls_name
        cls.activation_key = settings.upgrade.rhev_capsule_ak or settings.upgrade.capsule_ak
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
        ak = entities.ActivationKey(organization=self.org_id).search(
            query={'search': 'name={}'.format(self.activation_key)})[0]
        ak_env = ak.environment.read()
        product = entities.Product(
            name=self.prod_name, organization=self.org_id).create()
        self.create_repo()
        repo = entities.Repository(
            product=product.id, name=self.repo_name,
            url=self.repo_url).create()
        repo.sync()
        content_view = entities.ContentView(
            name=self.cv_name, organization=self.org_id).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        promote(content_view.read().version[0], ak_env.id)
        self.assertEqual(content_view.read().environment[-1].id, ak_env.id)

        global_dict = {self.__class__.__name__: {
            'env_name': ak_env.name}}
        create_dict(global_dict)

    @post_upgrade(depend_on=test_pre_user_scenario_capsule_sync)
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
        org_name = entities.Organization().search(
            query={'search': 'id={}'.format(self.org_id)})[0].label
        capsule = entities.SmartProxy().search(
            query={'search': 'name={}'.format(self.cap_host)})[0]
        call_entity_method_with_timeout(
            entities.Capsule(id=capsule.id).content_sync, timeout=3600)
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
        cls.cap_host = settings.upgrade.rhev_cap_host or settings.upgrade.capsule_hostname
        cls.repo_name = 'capsulesync_TestRepo_' + cls.cls_name
        cls.repo_path = '/var/www/html/pub/postupgradeCapSync_repo/'
        cls.rpm_name = rpm2.split('/')[-1]
        cls.prod_name = 'Scenario_postUpgradeCapSync_' + cls.cls_name
        cls.activation_key = settings.upgrade.rhev_capsule_ak or settings.upgrade.capsule_ak
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
        ak = entities.ActivationKey(organization=self.org_id).search(
            query={'search': 'name={}'.format(self.activation_key)})[0]
        ak_env = ak.environment.read()
        product = entities.Product(
            name=self.prod_name, organization=self.org_id).create()
        self.create_repo()
        repo = entities.Repository(
            product=product.id, name=self.repo_name,
            url=self.repo_url).create()
        repo.sync()
        content_view = entities.ContentView(
            name=self.cv_name, organization=self.org_id).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        promote(content_view.read().version[0], ak_env.id)
        self.assertEqual(content_view.read().environment[-1].id, ak_env.id)
        wait_untill_capsule_sync(self.cap_host)
        org_name = entities.Organization().search(
            query={'search': 'id={}'.format(self.org_id)})[0].label
        result = execute(
            lambda: run(
                '[ -f /var/lib/pulp/published/yum/http/repos/'
                '{0}/{1}/{2}/custom/{3}/{4}/Packages/c/{5} ]; echo $?'.format(
                    org_name, ak_env.name, self.cv_name,
                    self.prod_name, self.repo_name, self.rpm_name)),
            host=self.cap_host
        )[self.cap_host]
        self.assertEqual('0', result)
