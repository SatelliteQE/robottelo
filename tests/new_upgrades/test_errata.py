"""Test for Errata related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: ErrataManagement

:Team: Phoenix-content

:CaseImportance: Critical

"""

from box import Box
from fauxfactory import gen_alpha
import pytest
from wait_for import wait_for

from robottelo import constants
from robottelo.config import settings
from robottelo.hosts import ContentHost
from robottelo.logging import logger
from robottelo.utils.shared_resource import SharedResource


def _create_custom_rhel_n_client_repos(target_sat, product, v_major):
    """Create custom RHEL (system) and Satellite Client repos and sync them"""
    repos = []
    rhel_repo_urls = [settings.repos[f'rhel{v_major}_os']]
    if v_major > 7:
        rhel_repo_urls = [rhel_repo_urls[0]['BASEOS'], rhel_repo_urls[0]['APPSTREAM']]

    client_repo_url = settings.repos.satclient_repo[f'rhel{v_major}']
    if not all([all(rhel_repo_urls), client_repo_url]):
        raise ValueError(
            f'Repo URLs for RHEL {v_major} system repository or/and '
            f'Satellite Client repository for RHEL {v_major} are not set.'
        )
    # Satellite Client repo
    repos.append(
        target_sat.api.Repository(
            product=product.id,
            name=f'RHEL {v_major} Client',
            content_type='yum',
            url=client_repo_url,
        ).create()
    )
    # RHEL system repo(s)
    for url in rhel_repo_urls:
        repos.append(
            target_sat.api.Repository(
                product=product.id,
                name=f'RHEL {v_major} {url.split("/")[-4]}',
                content_type='yum',
                url=url,
            ).create()
        )

    for repo in repos:
        repo.sync(timeout=3000)
    return repos


def _get_rh_rhel_n_client_repos(target_sat, org, rhel_client):
    """Get list of RHEL (system) and Satellite Client repository IDs

    This method assumes that the RHEL and Satellite Client repositories
    are already created and synced.

    :return: List[entities.Repository]: repositories
    """
    rhel_repo_labels = ['rhel_bos', 'rhel_aps'] if rhel_client.os_version.major > 7 else ['rhel']
    rhel_repos = [
        target_sat.api.Repository(organization=org).search(
            query={'search': rhel_client.REPOS[repo]['id']}
        )[0]
        for repo in rhel_repo_labels
    ]
    sat_client_repo = target_sat.api.Repository(organization=org).search(
        query={'search': rhel_client.REPOS[constants.PRODUCT_KEY_SAT_CLIENT]['id']}
    )[0]

    return [*rhel_repos, sat_client_repo]


def _check_yum_plugins_count(host):
    """Check yum loaded plugins message count"""
    host.execute('yum clean all')
    plugins_count = host.execute('yum repolist | grep "Loaded plugins" | wc -l').stdout
    # The 'Loaded plugins' can happen once or (in the case of enabled repository upload) twice.
    assert int(plugins_count) <= 2, 'Loaded plugins message is displayed more than twice'


@pytest.fixture
def generate_errata_for_client_setup(
    errata_upgrade_shared_satellite,
    rhel_contenthost,
    upgrade_action,
):
    """Create product and repo from which the errata will be generated for the
    Satellite content host.

    :steps:
        1. Create Product and Custom Yum Repo
        2. Create custom tools, rhel repos and sync them
        3. Create content view and publish it
        4. Create activation key, add subscription if applicable (if the org is SCA-disabled)
        5. Register RHEL host to Satellite
        6. Generate Errata by installing outdated/older packages
        7. Check that errata applicability generated expected errata list for the given client.

    :expectedresults:
        1. The content host is created
        2. errata count, erratum list will be generated to Satellite content host
        3. All the expected errata are ready-to-be-applied on the client
    """
    target_sat = errata_upgrade_shared_satellite
    rhel_contenthost._satellite = target_sat
    with SharedResource(
        target_sat.hostname, upgrade_action, target_sat=target_sat, action_is_recoverable=True
    ) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'rhel_client': rhel_contenthost.hostname,
                'activation_key': None,
                'custom_repo_id': None,
                'product_id': None,
                'content_view_id': None,
                'synced_repo_ids': None,
                'organization_id': None,
            }
        )
        test_name = f'errata_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        test_data.organization_id = org.id
        environment = target_sat.api.LifecycleEnvironment(organization=org).search(
            query={'search': f'name={constants.ENVIRONMENT}'}
        )[0]
        product = target_sat.api.Product(name=f'{test_name}_prod', organization=org).create()
        test_data.product_id = product.id
        custom_yum_repo = target_sat.api.Repository(
            product=product.id,
            name=f'{test_name}_repo',
            content_type='yum',
            url=settings.repos.yum_9.url,
        ).create()
        test_data.custom_repo_id = custom_yum_repo.id
        product.sync()
        synced_repos = _create_custom_rhel_n_client_repos(
            target_sat, product, rhel_contenthost.os_version.major
        )
        test_data.synced_repo_ids = [repo.id for repo in synced_repos]
        repolist = [
            custom_yum_repo,
            *synced_repos,
        ]
        content_view = target_sat.publish_content_view(org, repolist, f'{test_name}_cv')
        test_data.content_view_id = content_view.id
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak',
            content_view=content_view,
            organization=org.id,
            environment=environment,
        ).create()
        test_data.activation_key = ak.name
        if not target_sat.is_sca_mode_enabled(org.id):
            subscription = target_sat.api.Subscription(organization=org).search(
                query={'search': f'name={product.name}'}
            )[0]
            ak.add_subscriptions(data={'subscription_id': subscription.id})
        # Override/enable all AK repos (disabled by default since 6.15)
        c_labels = [
            i['label'] for i in ak.product_content(data={'content_access_mode_all': '1'})['results']
        ]
        ak.content_override(
            data={
                'content_overrides': [{'content_label': label, 'value': '1'} for label in c_labels]
            }
        )
        rhel_contenthost.api_register(target_sat, organization=org, activation_keys=[ak.name])
        rhel_contenthost.add_rex_key(satellite=target_sat)
        rhel_contenthost.install_katello_host_tools()
        rhel_contenthost.execute('subscription-manager refresh')

        _check_yum_plugins_count(rhel_contenthost)

        pkg_install = rhel_contenthost.execute(
            f'yum -y install {" ".join(constants.FAKE_9_YUM_OUTDATED_PACKAGES)}'
        )
        assert pkg_install.status == 0, 'Failed to install packages'
        host = target_sat.api.Host().search(query={'search': f'activation_key={ak.name}'})[0]
        assert host.id == rhel_contenthost.nailgun_host.id, 'Host not found in Satellite'
        assert rhel_contenthost.applicable_errata_count > 1, (
            f'No applicable errata found for host {host.name}'
        )
        erratum_list = target_sat.api.Errata(repository=custom_yum_repo).search(
            query={'order': 'updated ASC', 'per_page': 1000}
        )
        errata_ids = [errata.errata_id for errata in erratum_list]
        assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
@pytest.mark.no_containers
@pytest.mark.errata_upgrade
def test_post_scenario_errata_count_installation(generate_errata_for_client_setup):
    """Post-upgrade scenario that applies errata on the RHEL client that was set up
    in the pre-upgrade test and verifies that the errata was applied correctly.

    :id: postupgrade-88fd28e6-b4df-46c0-91d6-784859fd1c21

    :steps:

        1. Recover pre_upgrade data for post_upgrade verification
        2. Verify errata count has not changed on Satellite
        3. Verify the errata_ids
        4. Verify installation of errata is successfull
        5. Verify that the errata application updated packages on client
        6. Verify that all expected erratas were installed on client.

    :expectedresults:
        1. errata count and erratum list should same after Satellite upgrade
        2. Installation of errata should pass successfully.

    :BZ: 1625649

    :customerscenario: true
    """
    target_sat = generate_errata_for_client_setup.target_sat
    custom_repo_id = generate_errata_for_client_setup.custom_repo_id
    activation_key = generate_errata_for_client_setup.activation_key
    organization_id = generate_errata_for_client_setup.organization_id
    rhel_client = ContentHost.get_host_by_hostname(generate_errata_for_client_setup.rhel_client)
    rhel_client._satellite = target_sat
    custom_yum_repo = target_sat.api.Repository(id=custom_repo_id).read()
    host = target_sat.api.Host().search(query={'search': f'activation_key={activation_key}'})[0]
    assert host.id == rhel_client.nailgun_host.id, 'Host not found in Satellite'
    organization = target_sat.api.Organization(id=organization_id).read()

    _check_yum_plugins_count(rhel_client)

    # Verifying errata count has not changed on Satellite
    installable_errata_count = rhel_client.applicable_errata_count
    assert installable_errata_count > 1, f'No applicable errata found for host {host.name}'
    erratum_list = target_sat.api.Errata(repository=custom_yum_repo).search(
        query={'order': 'updated ASC', 'per_page': 1000}
    )
    errata_ids = [errata.errata_id for errata in erratum_list]
    assert sorted(errata_ids) == sorted(settings.repos.yum_9.errata)

    for errata in settings.repos.yum_9.errata:
        task_id = target_sat.api.JobInvocation().run(
            data={
                'feature': 'katello_errata_install',
                'inputs': {'errata': errata},
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel_client.hostname}',
                'organization_id': organization.id,
            },
        )['id']
        target_sat.wait_for_tasks(
            search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
            search_rate=15,
            max_tries=10,
        )
        installable_errata_count -= 1

    # waiting for errata count to become 0, as profile uploading take some amount of time
    wait_for(
        lambda: rhel_client.applicable_errata_count == 0,
        timeout=400,
        delay=2,
        logger=logger,
    )
    pkg_check = rhel_client.execute(f'rpm -q {" ".join(constants.FAKE_9_YUM_UPDATED_PACKAGES)}')
    assert pkg_check.status == 0, 'Package check failed. One or more packages were not updated'
    errata_check = rhel_client.execute('dnf updateinfo list')
    for errata in settings.repos.yum_9.errata:
        assert errata not in errata_check.stdout, (
            'Errata check failed. One or more errata were not applied'
        )
