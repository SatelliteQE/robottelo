"""Test for Capsule related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Capsule

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fabric.api import execute
from fabric.api import run
from upgrade.helpers.tasks import wait_untill_capsule_sync
from upgrade_tests.helpers.scenarios import rpm1
from upgrade_tests.helpers.scenarios import rpm2

from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import promote
from robottelo.config import settings
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


class TestCapsuleSyncsPostUpgrade:
    """
    Test the capsule sync in the post-upgrade of pre-upgraded repo.

    :id: eb8970fa-98cc-4a99-99fb-1c12c4e319c9

    :steps:

        1. Before Satellite upgrade, Sync a repo/rpm in satellite
        2. Upgrade the Satellite.
        3. Run capsule sync post upgrade.
        4. Check if the repo/rpm is been synced to capsule.

    :expectedresults:

        1. The repo/rpm should be synced to satellite
        2. Activation key's environment id should be available in the content views environment
        id's list
        3. After upgrade, The capsule sync should be successful
        4. The repos/rpms from satellite should be synced to satellite
    """

    @pytest.mark.pre_upgrade
    def test_pre_user_scenario_capsule_sync(self, request, default_sat, default_org):
        """Pre-upgrade scenario that creates and sync repository with
        rpm in satellite which will be synced in post upgrade scenario.
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
        repo_url = f'http://{default_sat.hostname}/pub/{repo_name}'
        ak = default_sat.api.ActivationKey(organization=default_org.id).search(
            query={'search': f'name={activation_key}'}
        )[0]
        ak_env = ak.environment.read()

        product = default_sat.api.Product(name=prod_name, organization=default_org.id).create()
        create_repo(rpm1, repo_path)
        repo = default_sat.api.Repository(product=product.id, name=repo_name, url=repo_url).create()
        repo.sync()
        content_view = default_sat.api.ContentView(
            name=cv_name, organization=default_org.id
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        promote(content_view.read().version[0], ak_env.id)
        content_view_env_id = [env.id for env in content_view.read().environment]
        assert ak_env.id in content_view_env_id

    @pytest.mark.post_upgrade(depend_on=test_pre_user_scenario_capsule_sync)
    def test_post_user_scenario_capsule_sync(
        self, request, dependent_scenario_name, default_sat, default_org
    ):
        """Post-upgrade scenario that sync capsule from satellite and then
        verifies if the repo/rpm of pre-upgrade scenario is synced to capsule
        """
        request.addfinalizer(lambda: cleanup(content_view, repo, product))
        pre_test_name = dependent_scenario_name
        rpm_name = rpm1.split('/')[-1]
        cap_host = settings.upgrade.capsule_hostname
        activation_key = (
            settings.upgrade.capsule_ak[settings.upgrade.os]
            or settings.upgrade.custom_capsule_ak[settings.upgrade.os]
        )
        ak = default_sat.api.ActivationKey(organization=default_org.id).search(
            query={'search': f'name={activation_key}'}
        )[0]
        repo = default_sat.api.Repository(organization=default_org.id).search(
            query={'search': f'name={pre_test_name}_repo'}
        )[0]
        product = default_sat.api.Product(organization=default_org.id).search(
            query={'search': f'name={pre_test_name}_prod'}
        )[0]
        env_name = ak.environment.read()
        org_name = env_name.organization.read_json()['label']

        content_view = default_sat.api.ContentView(organization=f'{default_org.id}').search(
            query={'search': f'name={pre_test_name}_cv'}
        )[0]
        capsule = default_sat.api.SmartProxy().search(query={'search': f'name={cap_host}'})[0]
        call_entity_method_with_timeout(
            default_sat.api.Capsule(id=capsule.id).content_sync, timeout=3600
        )
        result = execute(
            lambda: run(
                f'[ -f /var/lib/pulp/published/yum/http/repos/'
                f'{org_name}/{env_name.name}/{content_view.name}/custom/{pre_test_name}_prod/'
                f'{pre_test_name}_repo/Packages/b/{rpm_name} ]; echo $?'
            ),
            host=cap_host,
        )[cap_host]
        assert result == '0'


class TestCapsuleSyncNewRepoPostUpgrade:
    """
    Post-upgrade scenario that creates and sync repository with rpm, sync capsule with satellite
    and verifies if the repo/rpm in satellite is synced to capsule.

    :id: 7c1d3441-3e8d-4ac2-8102-30e18274658c

    :steps:

        1. Upgrade satellite from previous satellite version.
        2. Post Upgrade , Sync a repo/rpm in satellite.
        3. Run capsule sync.
        4. Check if the repo/rpm is been synced to capsule.

    :expectedresults:

        1. The repo/rpm should be synced to satellite
        2. Capsule sync should be successful
        3. The repo/rpm from satellite should be synced to capsule
    """

    @pytest.mark.post_upgrade
    def test_post_user_scenario_capsule_sync_yum_repo(self, request, default_sat, default_org):
        """Sync Capsule Post upgrade"""
        request.addfinalizer(lambda: cleanup(content_view, repo, product))
        repo_name = gen_string('alpha')
        rpm_name = rpm2.split('/')[-1]
        activation_key = (
            settings.upgrade.capsule_ak[settings.upgrade.os]
            or settings.upgrade.custom_capsule_ak[settings.upgrade.os]
        )
        cap_host = settings.upgrade.capsule_hostname
        ak = default_sat.api.ActivationKey(organization=default_org.id).search(
            query={'search': f'name={activation_key}'}
        )[0]
        ak_env = ak.environment.read()
        repo_url = f'http://{default_sat.hostname}/pub/{repo_name}/'
        product = default_sat.api.Product(organization=default_org.id).create()
        repo_path = f'/var/www/html/pub/{repo_name}/'
        create_repo(rpm2, repo_path)

        repo = default_sat.api.Repository(
            product=product.id, name=f'{repo_name}', url=repo_url
        ).create()
        repo.sync()
        content_view = default_sat.api.ContentView(organization=default_org.id).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        promote(content_view.read().version[0], ak_env.id)
        content_view_env = [env.id for env in content_view.read().environment]
        assert ak_env.id in content_view_env

        wait_untill_capsule_sync(cap_host)
        result = execute(
            lambda: run(
                f'[ -f /var/lib/pulp/published/yum/http/repos/{default_org.label}/{ak_env.name}/'
                f'{content_view.name}/custom/{product.name}/{repo_name}/Packages/c/{rpm_name} ];'
                f' echo $?'
            ),
            host=cap_host,
        )[cap_host]
        assert '0' == result
