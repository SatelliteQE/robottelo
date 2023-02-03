"""Test for Client related Upgrade Scenario's

content-host-d containers use SATHOST env var, which is passed through sat6-upgrade functions
sat6-upgrade requires env.satellite_hostname to be set, this is required for these tests

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:Team: Phoenix

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time

import pytest
from fabric.api import execute
from upgrade.helpers.docker import docker_execute_command
from upgrade_tests.helpers.scenarios import dockerize

from robottelo.config import settings
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE
from robottelo.constants import REPOS


# host machine for containers
docker_vm = settings.upgrade.docker_vm


@pytest.fixture(scope='module')
def pre_upgrade_repo(module_product, module_target_sat):
    """Enable custom errata repository"""
    pre_upgrade_repo = module_target_sat.api.Repository(
        url=settings.repos.yum_0.url, product=module_product
    ).create()
    assert pre_upgrade_repo.sync()['result'] == 'success'
    return pre_upgrade_repo


@pytest.fixture(scope='module')
def post_upgrade_repo(module_product, module_target_sat):
    """Enable custom errata repository"""
    post_upgrade_repo = module_target_sat.api.Repository(
        url=settings.repos.yum_9.url, product=module_product
    ).create()
    assert post_upgrade_repo.sync()['result'] == 'success'
    return post_upgrade_repo


@pytest.fixture(scope='module')
def pre_upgrade_cv(default_org, pre_upgrade_repo, module_target_sat):
    """Create and publish repo"""
    pre_upgrade_cv = module_target_sat.api.ContentView(
        organization=default_org, repository=[pre_upgrade_repo.id]
    ).create()
    pre_upgrade_cv.publish()
    pre_upgrade_cv = pre_upgrade_cv.read()
    return pre_upgrade_cv


@pytest.fixture(scope='module')
def post_upgrade_cv(default_org, post_upgrade_repo, module_target_sat):
    """Create and publish repo"""
    post_upgrade_cv = module_target_sat.api.ContentView(
        organization=default_org, repository=[post_upgrade_repo.id]
    ).create()
    post_upgrade_cv.publish()
    post_upgrade_cv = post_upgrade_cv.read()
    return post_upgrade_cv


@pytest.fixture(scope='module')
def module_ak(default_org, module_lce_library, pre_upgrade_repo, module_product, module_target_sat):
    """Create a module AK in Library LCE"""
    ak = module_target_sat.api.ActivationKey(
        content_view=DEFAULT_CV,
        environment=module_lce_library,
        organization=default_org,
    ).create()
    # Fetch available subscriptions
    subs = module_target_sat.api.Subscription(organization=default_org).search()
    assert len(subs) > 0
    # Add default subscription to activation key
    sub_found = False
    for sub in subs:
        if sub.name == DEFAULT_SUBSCRIPTION_NAME:
            ak.add_subscriptions(data={'subscription_id': sub.id})
            sub_found = True
    assert sub_found
    # Enable RHEL tools repo in activation key
    ak.content_override(
        data={'content_overrides': [{'content_label': REPOS['rhst7']['id'], 'value': '1'}]}
    )
    # Add custom subscription to activation key
    custom_sub = module_target_sat.api.Subscription().search(
        query={'search': f'name={module_product.name}'}
    )
    ak.add_subscriptions(data={'subscription_id': custom_sub[0].id})
    return ak


class TestScenarioUpgradeOldClientAndPackageInstallation:
    """This section contains pre and post upgrade scenarios to test if the
    package can be installed on the preupgrade client remotely.

    Test Steps::

        1. Before Satellite upgrade, create a content host and register it with
            Satellite
        2. Upgrade Satellite and client
        3. Install package post upgrade on a pre-upgrade client from Satellite
        4. Check if the package is installed on the pre-upgrade client
    """

    @pytest.mark.pre_upgrade
    def test_pre_scenario_preclient_package_installation(
        default_org, pre_upgrade_cv, pre_upgrade_repo, module_ak, save_test_data
    ):
        """Create product and repo, from which a package will be installed
        post upgrade. Create a content host and register it.

        :id: preupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

        :setup:

            1. Create and sync repo from which a package can be
                installed on content host
            2. Add repo to CV and then to Activation key


        :steps:

            1. Create a container as content host and register with Activation key

        :expectedresults:

            1. The "pre-upgrade" content host is created and registered.
            2. The new repo is enabled on the content host.

        """
        rhel7_client = dockerize(
            ak_name=module_ak.name, distro='rhel7', org_label=default_org.label
        )
        client_container_id = list(rhel7_client.values())[0]
        # Wait 60 seconds as script in /tmp takes up to 2 min inc the repo sync time
        time.sleep(60)
        # Use yum install again in case script was not yet finished
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'yum -y install katello-agent',
            host=docker_vm,
        )[docker_vm]
        # Assert gofer was installed after yum completes
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'rpm -q gofer',
            host=docker_vm,
        )[docker_vm]
        assert 'package gofer is not installed' not in installed_package
        # Run goferd on client as its docker container
        kwargs = {'async': True, 'host': docker_vm}
        execute(docker_execute_command, client_container_id, 'goferd -f', **kwargs)
        # Holding on for 30 seconds while goferd starts
        time.sleep(30)
        status = execute(docker_execute_command, client_container_id, 'ps -aux', host=docker_vm)[
            docker_vm
        ]
        assert 'goferd' in status
        # Save client info to disk for post-upgrade test
        save_test_data({__name__: rhel7_client})

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_preclient_package_installation)
    def test_post_scenario_preclient_package_installation(
        default_org, module_target_sat, pre_upgrade_data
    ):
        """Post-upgrade install of a package on a client created and registered pre-upgrade.

        :id: postupgrade-eedab638-fdc9-41fa-bc81-75dd2790f7be

        :steps: Install package on the pre-upgrade registered client

        :expectedresults: The package is installed on client
        """
        client = pre_upgrade_data.get(__name__)
        client_name = str(list(client.keys())[0]).lower()
        client_id = (
            module_target_sat.api.Host().search(query={'search': f'name={client_name}'})[0].id
        )
        module_target_sat.api.Host().install_content(
            data={
                'organization_id': default_org.id,
                'included': {'ids': [client_id]},
                'content_type': 'package',
                'content': [FAKE_0_CUSTOM_PACKAGE],
            }
        )
        # Verifies that package is really installed
        installed_package = execute(
            docker_execute_command,
            list(client.values())[0],
            f'rpm -q {FAKE_0_CUSTOM_PACKAGE}',
            host=docker_vm,
        )[docker_vm]
        assert FAKE_0_CUSTOM_PACKAGE in installed_package


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
    def test_post_scenario_postclient_package_installation(
        default_org, post_upgrade_repo, module_ak, module_target_sat, module_lce
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
        rhel7_client = dockerize(
            ak_name=module_ak.name, distro='rhel7', org_label=default_org.label
        )
        client_container_id = list(rhel7_client.values())[0]
        client_name = list(rhel7_client.keys())[0].lower()
        # Wait 60 seconds as script in /tmp takes up to 2 min inc the repo sync time
        time.sleep(60)
        # Use yum install again in case script was not yet finished
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'yum -y install katello-agent',
            host=docker_vm,
        )[docker_vm]
        # Assert gofer was installed after yum completes
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            'rpm -q gofer',
            host=docker_vm,
        )[docker_vm]
        assert 'package gofer is not installed' not in installed_package
        # Run goferd on client as its docker container
        kwargs = {'async': True, 'host': docker_vm}
        execute(docker_execute_command, client_container_id, 'goferd -f', **kwargs)
        # Holding on for 30 seconds while goferd starts
        time.sleep(30)
        status = execute(docker_execute_command, client_container_id, 'ps -aux', host=docker_vm)[
            docker_vm
        ]
        assert 'goferd' in status
        client_id = (
            module_target_sat.api.Host().search(query={'search': f'name={client_name}'})[0].id
        )
        module_target_sat.api.Host().install_content(
            data={
                'organization_id': default_org.id,
                'included': {'ids': [client_id]},
                'content_type': 'package',
                'content': [FAKE_4_CUSTOM_PACKAGE],
            }
        )
        # Validate if that package is really installed
        installed_package = execute(
            docker_execute_command,
            client_container_id,
            f'rpm -q {FAKE_4_CUSTOM_PACKAGE}',
            host=docker_vm,
        )[docker_vm]
        assert FAKE_4_CUSTOM_PACKAGE in installed_package
