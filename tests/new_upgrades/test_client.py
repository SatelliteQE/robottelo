"""Test for Client related Upgrade Scenario's

content-host-d containers use SATHOST env var, which is passed through sat6-upgrade functions
sat6-upgrade requires env.satellite_hostname to be set, this is required for these tests

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Hosts-Content

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

import pytest
from box import Box
from fauxfactory import gen_alpha

from robottelo.config import settings
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME, FAKE_4_CUSTOM_PACKAGE_NAME
from robottelo.hosts import ContentHost
from robottelo.utils.shared_resource import SharedResource


# @pytest.fixture
# def client_for_upgrade(module_target_sat, rex_contenthost, module_org):
#     rex_contenthost.create_custom_repos(fake_yum=settings.repos.yum_1.url)
#     return rex_contenthost


# class TestScenarioUpgradeOldClientAndPackageInstallation:
#     """This section contains pre and post upgrade scenarios to test if the
#     package can be installed on the preupgrade client remotely.
# 
#     Test Steps::
# 
#         1. Before Satellite upgrade, create a content host and register it with
#             Satellite
#         2. Upgrade Satellite and client
#         3. Install package post upgrade on a pre-upgrade client from Satellite
#         4. Check if the package is installed on the pre-upgrade client
#     """

@pytest.fixture
def pre_client_package_installation_setup(
    rhel_contenthost,
    client_upgrade_shared_satellite,
    upgrade_action,
):
    """Create product and repo, from which a package will be installed
    post upgrade. Create a content host and register it.

    :id: preupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

    :setup:

        1. Create and sync repo from which a package can be
            installed on content host
        2. Add repo to CV and then to Activation key

    :steps:

        1. Create a content host and register with Activation key

    :expectedresults:

        1. The "pre-upgrade" content host is created and registered.
        2. The new repo is enabled on the content host.

    """
    target_sat = client_upgrade_shared_satellite
    # rhel_contenthost._skip_context_checkin = True
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'rex_upgrade_{gen_alpha()}'
        test_data = Box(
            {
                'satellite': target_sat,
                'contenthost': rhel_contenthost,
                'ak': None,
                'org': None,
            }
        )
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        library_id = int(
            target_sat.cli.LifecycleEnvironment.list(
                {'organization-id': org.id, 'library': 'true'}
            )[0]['id']
        )
        product = target_sat.api.Product(organization=org, name=f'{test_name}_prod').create()
        repo = target_sat.api.Repository(
            product=product,
            name=f'{test_name}_yum_repo',
            url=settings.repos.yum_1.url,
            content_type='yum',
        ).create()
        target_sat.api.Repository.sync(repo)
        lce = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=library_id
        ).create()
        content_view = target_sat.publish_content_view(org, [repo], f'{test_name}_cv')
        content_view.version[0].promote(data={'environment_ids': lce.id})
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak', organization=org.id, environment=lce, content_view=content_view
        ).create()
        test_data.ak = ak
        result = rhel_contenthost.api_register(
            target_sat, organization=org, activation_keys=[ak.name], location=location,
        )
        assert f'The registered system name is: {rhel_contenthost.hostname}' in result.stdout
        rhel_contenthost.execute('subscription-manager repos --enable=* && yum clean all')
        target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Install Package - Katello Script Default',
                'inputs': f'package={FAKE_4_CUSTOM_PACKAGE_NAME}',
                'search-query': f'name ~ {rhel_contenthost.hostname}',
            }
        )
        result = rhel_contenthost.execute(f"rpm -q {FAKE_4_CUSTOM_PACKAGE_NAME}")
        assert FAKE_4_CUSTOM_PACKAGE_NAME in result.stdout
        test_data.org = org
        test_data.ak = ak
        sat_upgrade.ready()
        yield test_data



@pytest.mark.client_upgrades
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([8])
def test_pre_client_package_installation(pre_client_package_installation_setup):
    """Post-upgrade install of a package on a client created and registered pre-upgrade.

    :id: postupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

    :steps: Install package on the pre-upgrade registered client

    :expectedresults: The package is installed on client
    """
    rhel_client = pre_client_package_installation_setup.contenthost
    target_sat = pre_client_package_installation_setup.satellite
    target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Install Package - Katello Script Default',
            'inputs': f'package={FAKE_0_CUSTOM_PACKAGE_NAME}',
            'search-query': f'name ~ {rhel_client.hostname}',
        }
    )
    # Verify that package is really installed
    result = rhel_client.execute(f"rpm -q {FAKE_0_CUSTOM_PACKAGE_NAME}")
    assert FAKE_0_CUSTOM_PACKAGE_NAME in result.stdout


class TestScenarioUpgradeNewClientAndPackageInstallation:
    """This section contains post-upgrade scenarios to test if a package
    can be installed on a client created postupgrade, remotely.

    Test Steps:

        1. Upgrade Satellite
        2. After Satellite upgrade, create a content host and register it with
            Satellite
        3. Install package to the client from Satellite
        4. Check if the package is installed on the post-upgrade client
    """

    @pytest.mark.post_upgrade
    @pytest.mark.rhel_ver_list([8])
    def test_post_scenario_post_client_package_installation(
        self,
        module_target_sat,
        client_for_upgrade,
    ):
        """Post-upgrade test that creates a client, installs a package on
        the post-upgrade created client and then verifies the package is installed.

        :id: postupgrade-1a881c07-595f-425f-aca9-df2337824a8e

        :steps:

            1. Create a content host with existing client ak
            2. Create and sync new post-upgrade repo from which a package will be
                installed on content host
            3. Add repo to CV and then in Activation key
            4. Install package on the pre-upgrade client

        :expectedresults:

            1. The content host is created
            2. The new repo and its product has been added to ak using which
                the content host is created
            3. The package is installed on post-upgrade client
        """
        module_target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Install Package - Katello Script Default',
                'inputs': f'package={FAKE_0_CUSTOM_PACKAGE_NAME}',
                'search-query': f'name ~ {client_for_upgrade.hostname}',
            }
        )
        # Verifies that package is really installed
        result = client_for_upgrade.execute(f"rpm -q {FAKE_0_CUSTOM_PACKAGE_NAME}")
        assert FAKE_0_CUSTOM_PACKAGE_NAME in result.stdout
