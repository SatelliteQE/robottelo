"""Test for Client related Upgrade Scenario's

content-host-d containers use SATHOST env var, which is passed through sat6-upgrade functions
sat6-upgrade requires env.satellite_hostname to be set, this is required for these tests

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Hosts-Content

:Team: Proton

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.config import settings
from robottelo.constants import (
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE_NAME,
    FAKE_4_CUSTOM_PACKAGE_NAME,
)
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def pre_client_package_installation_setup(
    rhel_contenthost,
    client_upgrade_shared_satellite,
    upgrade_action,
):
    """Create product and repo, from which a package will be installed
    post upgrade. Create a content host and register it.

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
    rhel_contenthost._skip_context_checkin = True
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'rex_upgrade_{gen_alpha()}'
        test_data = Box(
            {
                'satellite': target_sat,
                'contenthost': rhel_contenthost,
                'ak': None,
                'org': None,
                'location': None,
                'lce': None,
                'test_name': test_name,
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
        result = rhel_contenthost.api_register(
            target_sat,
            organization=org,
            activation_keys=[ak.name],
            location=location,
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
        test_data.location = location
        test_data.lce = lce
        test_data.product = product
        test_data.ak = ak
        sat_upgrade.ready()
        yield test_data


@pytest.mark.client_upgrades
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_pre_client_package_installation(pre_client_package_installation_setup):
    """Post-upgrade install of a package on a client created and registered pre-upgrade.

    :id: eedab638-fdc9-41fa-bc81-75dd2790f7be

    :steps: Install package on the pre-upgrade registered client

    :expectedresults: The package is installed on client
    """
    rhel_client = pre_client_package_installation_setup.contenthost
    target_sat = pre_client_package_installation_setup.satellite
    target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Install Package - Katello Script Default',
            'inputs': f'package={FAKE_2_CUSTOM_PACKAGE_NAME}',
            'search-query': f'name ~ {rhel_client.hostname}',
        }
    )
    # Verify that package is really installed
    result = rhel_client.execute(f"rpm -q {FAKE_0_CUSTOM_PACKAGE_NAME}")
    assert FAKE_0_CUSTOM_PACKAGE_NAME in result.stdout


@pytest.mark.client_upgrades
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_post_scenario_post_client_package_installation(pre_client_package_installation_setup):
    """Post-upgrade test that installs a package on a client registered post-upgrade
    and then verifies the package is installed.

    :id: 1a881c07-595f-425f-aca9-df2337824a8e

    :steps:

        1. Create and sync new post-upgrade repo from which a package will be
           installed on content host
        2. Add repo to CV
        3. Create an activation key that uses the CV and use it to register a client
        4. Install a package on the client

    :expectedresults:

        1. The content host is successfully registered
        2. The package is installed on the client
    """
    rhel_client = pre_client_package_installation_setup.contenthost
    rhel_client.execute('subscription-manager unregister')
    rhel_client.execute('subscription-manager clean')
    target_sat = pre_client_package_installation_setup.satellite
    if settings.UPGRADE.TO_VERSION == 'stream':
        target_sat._swap_nailgun('master')
    else:
        target_sat._swap_nailgun(f"{settings.UPGRADE.TO_VERSION}.z")
    org = target_sat.api.Organization(id=pre_client_package_installation_setup.org.id).read()
    location = target_sat.api.Location(id=pre_client_package_installation_setup.location.id).read()
    lce = target_sat.api.LifecycleEnvironment(
        id=pre_client_package_installation_setup.lce.id
    ).read()
    product = pre_client_package_installation_setup.product
    test_name = pre_client_package_installation_setup.test_name
    repo = target_sat.api.Repository(
        product=product.id,
        name=f'{test_name}_yum_repo_post_upgrade',
        url=settings.repos.yum_2.url,
        content_type='yum',
    ).create()
    target_sat.api.Repository.sync(repo)
    content_view = target_sat.publish_content_view(org, [repo], f'{test_name}_cv_post_upgrade')
    content_view.version[0].promote(data={'environment_ids': lce.id})
    ak = target_sat.api.ActivationKey(
        name=f'{test_name}_ak_post_upgrade',
        organization=org.id,
        environment=lce,
        content_view=content_view,
    ).create()
    result = rhel_client.api_register(
        target_sat,
        organization=org,
        activation_keys=[ak.name],
        location=location,
    )
    assert f'The registered system name is: {rhel_client.hostname}' in result.stdout
    rhel_client.execute('subscription-manager repos --enable=* && yum clean all')
    target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Install Package - Katello Script Default',
            'inputs': f'package={FAKE_2_CUSTOM_PACKAGE_NAME}',
            'search-query': f'name ~ {rhel_client.hostname}',
        }
    )
    # Verifies that package is really installed
    result = rhel_client.execute(f"rpm -q {FAKE_2_CUSTOM_PACKAGE_NAME}")
    assert FAKE_2_CUSTOM_PACKAGE_NAME in result.stdout
