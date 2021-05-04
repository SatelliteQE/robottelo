"""Test for Capsule related Upgrade Scenario's

:Requirement: Upgraded Satellite & Capsule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Capsule

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fabric.api import execute
from fabric.api import run
from nailgun import entities
from upgrade.helpers.tasks import wait_untill_capsule_sync
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import rpm1
from upgrade_tests.helpers.scenarios import rpm2

from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.datafactory import gen_string
from robottelo.upgrade_utility import create_repo


def cleanup(content_view, repo, product):
    """
    This function is used to perform the cleanup of created content view, repository and product.
    """
    cv_env_details = content_view.read_json()
    for content in cv_env_details['environments']:
        content_view.delete_from_environment(content['id'])
    content_view.delete()
    repo.delete()
    product.delete()

    # To clean the orphaned content for next run, it is used to fix KCS#4820591
    run("foreman-rake katello:delete_orphaned_content")


class TestCapsuleSync:
    """
    The test class contains pre-upgrade and post-upgrade scenario to test the capsule sync
    in the post-upgrade of pre-upgraded repo.
    """

    @pre_upgrade
    def test_pre_user_scenario_capsule_sync(self, request):
        """Pre-upgrade scenario that creates and sync repository with
        rpm in satellite which will be synced in post upgrade scenario.

        :id: preupgrade-eb8970fa-98cc-4a99-99fb-1c12c4e319c9

        :steps:
            1. Before Satellite upgrade, Sync a repo/rpm in satellite

        :expectedresults:
            1. The repo/rpm should be synced to satellite
            2. Activation key's environment id should be available in the content views environment
            id's list

        """
        pre_test_name = request.node.name
        repo_name = f"{pre_test_name}_repo"
        repo_path = f'/var/www/html/pub/{repo_name}/'
        activation_key = (
            settings.upgrade.capsule_ak[settings.upgrade.os]
            or settings.upgrade.custom_capsule_ak[settings.upgrade.os]
        )
        prod_name = f"{pre_test_name}_prod"
        cv_name = f"{pre_test_name}_cv"
        repo_url = f'http://{settings.server.hostname}/pub/{repo_name}'
        org = entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
        ak = entities.ActivationKey(organization=org.id).search(
            query={'search': f'name={activation_key}'}
        )[0]
        ak_env = ak.environment.read()

        product = entities.Product(name=prod_name, organization=org.id).create()
        create_repo(rpm1, repo_path)
        repo = entities.Repository(product=product.id, name=repo_name, url=repo_url).create()
        repo.sync()
        content_view = entities.ContentView(name=cv_name, organization=org.id).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        promote(content_view.read().version[0], ak_env.id)
        content_view_env_id = [env.id for env in content_view.read().environment]
        assert ak_env.id in content_view_env_id

    @post_upgrade(depend_on=test_pre_user_scenario_capsule_sync)
    def test_post_user_scenario_capsule_sync(self, request, dependent_scenario_name):
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
        request.addfinalizer(lambda: cleanup(content_view, repo, product))
        org = entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
        pre_test_name = dependent_scenario_name
        rpm_name = rpm1.split('/')[-1]
        cap_host = settings.upgrade.capsule_hostname
        activation_key = (
            settings.upgrade.capsule_ak[settings.upgrade.os]
            or settings.upgrade.custom_capsule_ak[settings.upgrade.os]
        )
        ak = entities.ActivationKey(organization=org.id).search(
            query={'search': f'name={activation_key}'}
        )[0]
        repo = entities.Repository(organization=org.id).search(
            query={'search': f'name={pre_test_name}_repo'}
        )[0]
        product = entities.Product(organization=org.id).search(
            query={'search': f'name={pre_test_name}_prod'}
        )[0]
        env_name = ak.environment.read()
        org_name = env_name.organization.read_json()['label']

        content_view = entities.ContentView(organization=f'{org.id}').search(
            query={'search': f'name={pre_test_name}_cv'}
        )[0]
        capsule = entities.SmartProxy().search(query={'search': f'name={cap_host}'})[0]
        call_entity_method_with_timeout(entities.Capsule(id=capsule.id).content_sync, timeout=3600)
        result = execute(
            lambda: run(
                f'[ -f /var/lib/pulp/published/yum/http/repos/'
                f'{org_name}/{env_name.name}/{content_view.name}/custom/{pre_test_name}_prod/'
                f'{pre_test_name}_repo/Packages/b/{rpm_name} ]; echo $?'
            ),
            host=cap_host,
        )[cap_host]
        assert result == '0'


class TestCapsuleSyncNewRepo:
    """
    The test class contains a post-upgrade scenario to test the capsule sync of new added yum
    and puppet repo.
    """

    @post_upgrade
    def test_post_user_scenario_capsule_sync_yum_repo(self, request):
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
        request.addfinalizer(lambda: cleanup(content_view, repo, product))
        repo_name = gen_string('alpha')
        rpm_name = rpm2.split('/')[-1]
        org = entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
        activation_key = (
            settings.upgrade.capsule_ak[settings.upgrade.os]
            or settings.upgrade.custom_capsule_ak[settings.upgrade.os]
        )
        cap_host = settings.upgrade.capsule_hostname
        ak = entities.ActivationKey(organization=org.id).search(
            query={'search': f'name={activation_key}'}
        )[0]
        ak_env = ak.environment.read()
        repo_url = f'http://{settings.server.hostname}/pub/{repo_name}/'
        product = entities.Product(organization=org.id).create()
        repo_path = f'/var/www/html/pub/{repo_name}/'
        create_repo(rpm2, repo_path)

        repo = entities.Repository(product=product.id, name=f'{repo_name}', url=repo_url).create()
        repo.sync()
        content_view = entities.ContentView(organization=org.id).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        promote(content_view.read().version[0], ak_env.id)
        content_view_env = [env.id for env in content_view.read().environment]
        assert ak_env.id in content_view_env

        wait_untill_capsule_sync(cap_host)
        result = execute(
            lambda: run(
                f'[ -f /var/lib/pulp/published/yum/http/repos/{org.label}/{ak_env.name}/'
                f'{content_view.name}/custom/{product.name}/{repo_name}/Packages/c/{rpm_name} ];'
                f' echo $?'
            ),
            host=cap_host,
        )[cap_host]
        assert '0' == result

    @post_upgrade
    def test_post_user_scenario_capsule_sync_puppet_repo(self, request):
        """Post-upgrade scenario that creates and sync repository with
        puppet modules, sync capsule with satellite and verifies it's status.

        :id: postupgrade-7c597e9d-8db9-455e-bd19-acb5efa990a7

        :steps:
            1. Post Upgrade , Sync a puppet repo, Add to C.V. in Satellite.
            2. Run Capsule sync.
            3. Check Capsule sync status.

        :expectedresults: Capsule sync should complete successfully with puppet repo content.

        """
        request.addfinalizer(lambda: cleanup(content_view, repo, product))
        cap_host = settings.upgrade.capsule_hostname
        org = entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]
        lc_env = entities.LifecycleEnvironment(organization=org).search(
            query={'search': 'name="{}"'.format('Dev')}
        )[0]

        product = entities.Product(organization=org).create()
        repo = entities.Repository(
            product=product, content_type='puppet', url=CUSTOM_PUPPET_REPO
        ).create()
        repo.sync()
        module = repo.puppet_modules()
        content_view = entities.ContentView(organization=org).create()
        entities.ContentViewPuppetModule(
            author=module['results'][0]['author'],
            name=module['results'][0]['name'],
            content_view=content_view,
        ).create()
        entities.ContentViewPuppetModule(
            author=module['results'][1]['author'],
            name=module['results'][1]['name'],
            content_view=content_view,
        ).create()
        content_view.publish()
        promote(content_view.read().version[0], lc_env.id)

        # Run a Capsule sync
        capsule = entities.SmartProxy().search(query={'search': f'name={cap_host}'})[0]
        call_entity_method_with_timeout(entities.Capsule(id=capsule.id).content_sync, timeout=3600)
        sync_status = entities.Capsule(id=capsule.id).content_get_sync()
        assert sync_status['active_sync_tasks']
        assert sync_status['last_failed_sync_tasks']
