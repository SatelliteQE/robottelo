"""API Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: ErrataManagement

:Assignee: addubey

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
# For ease of use hc refers to host-collection throughout this document
from time import sleep

import pytest
from nailgun import entities

from robottelo import constants
from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import upload_manifest
from robottelo.api.utils import wait_for_tasks
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.host import Host
from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME

pytestmark = [
    pytest.mark.run_in_one_thread,
    pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    ),
]

CUSTOM_REPO_URL = settings.repos.yum_9.url
CUSTOM_REPO_ERRATA_ID = settings.repos.yum_6.errata[2]


@pytest.fixture(scope='module')
def activation_key(module_org, module_lce):
    activation_key = entities.ActivationKey(
        environment=module_lce, organization=module_org
    ).create()
    return activation_key


@pytest.fixture(scope='module')
def rh_repo(module_org, module_lce, module_cv, activation_key):
    return setup_org_for_a_rh_repo(
        {
            'product': constants.PRDS['rhel'],
            'repository-set': constants.REPOSET['rhst7'],
            'repository': constants.REPOS['rhst7']['name'],
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': activation_key.id,
        },
        force_manifest_upload=True,
    )


@pytest.fixture(scope='module')
def custom_repo(module_org, module_lce, module_cv, activation_key):
    return setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_9.url,
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': activation_key.id,
        }
    )


def _install_package(
    module_org, clients, host_ids, package_name, via_ssh=True, rpm_package_name=None
):
    """Install package via SSH CLI if via_ssh is True, otherwise
    install via http api: PUT /api/v2/hosts/bulk/install_content
    """
    if via_ssh:
        for client in clients:
            result = client.run(f'yum install -y {package_name}')
            assert result.status == 0
            result = client.run(f'rpm -q {package_name}')
            assert result.status == 0
    else:
        entities.Host().install_content(
            data={
                'organization_id': module_org.id,
                'included': {'ids': host_ids},
                'content_type': 'package',
                'content': [package_name],
            }
        )
        _validate_package_installed(clients, rpm_package_name)


def _validate_package_installed(hosts, package_name, expected_installed=True, timeout=240):
    """Check whether package was installed on the list of hosts."""
    for host in hosts:
        for _ in range(timeout // 15):
            result = host.run(f'rpm -q {package_name}')
            if (
                result.status == 0
                and expected_installed
                or result.status != 0
                and not expected_installed
            ):
                break
            sleep(15)
        else:
            pytest.fail(
                'Package {} was not {} host {}'.format(
                    package_name,
                    'installed on' if expected_installed else 'removed from',
                    host.hostname,
                )
            )


def _validate_errata_counts(module_org, host, errata_type, expected_value, timeout=120):
    """Check whether host contains expected errata counts."""
    for _ in range(timeout // 5):
        host = host.read()
        if host.content_facet_attributes['errata_counts'][errata_type] == expected_value:
            break
        sleep(5)
    else:
        pytest.fail(
            'Host {} contains {} {} errata, but expected to contain '
            '{} of them'.format(
                host.name,
                host.content_facet_attributes['errata_counts'][errata_type],
                errata_type,
                expected_value,
            )
        )


def _fetch_available_errata(module_org, host, expected_amount, timeout=120):
    """Fetch available errata for host."""
    errata = host.errata()
    for _ in range(timeout // 5):
        if len(errata['results']) == expected_amount:
            return errata['results']
        sleep(5)
        errata = host.errata()
    else:
        pytest.fail(
            'Host {} contains {} available errata, but expected to '
            'contain {} of them'.format(host.name, len(errata['results']), expected_amount)
        )


@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.rhel_ver_list([7, 8, 9])
def test_positive_install_in_hc(module_org, activation_key, custom_repo, target_sat, content_hosts):
    """Install errata in a host-collection

    :id: 6f0242df-6511-4c0f-95fc-3fa32c63a064

    :Setup: Errata synced on satellite server.

    :Steps: PUT /api/v2/hosts/bulk/update_content

    :expectedresults: errata is installed in the host-collection.

    :CaseLevel: System

    :BZ: 1983043
    """
    for client in content_hosts:
        client.install_katello_ca(target_sat)
        client.register_contenthost(module_org.label, activation_key.name)
        assert client.subscribed
        client.add_rex_key(satellite=target_sat)
    host_ids = [client.nailgun_host.id for client in content_hosts]
    _install_package(
        module_org,
        clients=content_hosts,
        host_ids=host_ids,
        package_name=constants.FAKE_1_CUSTOM_PACKAGE,
    )
    host_collection = target_sat.api.HostCollection(organization=module_org).create()
    host_ids = [client.nailgun_host.id for client in content_hosts]
    host_collection.host_ids = host_ids
    host_collection = host_collection.update(['host_ids'])
    task_id = target_sat.api.JobInvocation().run(
        data={
            'feature': 'katello_errata_install',
            'inputs': {'errata': str(CUSTOM_REPO_ERRATA_ID)},
            'targeting_type': 'static_query',
            'search_query': f'host_collection_id = {host_collection.id}',
            'organization_id': module_org.id,
        },
    )['id']
    wait_for_tasks(
        search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
        search_rate=15,
        max_tries=10,
    )
    for client in content_hosts:
        result = client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}')
        assert result.status == 0


@pytest.mark.tier3
@pytest.mark.rhel_ver_list([7, 8, 9])
def test_positive_install_in_host(
    module_org, activation_key, custom_repo, rhel_contenthost, target_sat
):
    """Install errata in a host

    :id: 1e6fc159-b0d6-436f-b945-2a5731c46df5

    :Setup: Errata synced on satellite server.

    :Steps: POST /api/v2/job_invocations/{hash}

    :expectedresults: errata is installed in the host.

    :parametrized: yes

    :CaseLevel: System

    :BZ: 1983043
    """
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(module_org.label, activation_key.name)
    assert rhel_contenthost.subscribed
    host_id = rhel_contenthost.nailgun_host.id
    _install_package(
        module_org,
        clients=[rhel_contenthost],
        host_ids=[host_id],
        package_name=constants.FAKE_1_CUSTOM_PACKAGE,
    )
    rhel_contenthost.add_rex_key(satellite=target_sat)
    task_id = target_sat.api.JobInvocation().run(
        data={
            'feature': 'katello_errata_install',
            'inputs': {'errata': str(CUSTOM_REPO_ERRATA_ID)},
            'targeting_type': 'static_query',
            'search_query': f'name = {rhel_contenthost.hostname}',
            'organization_id': module_org.id,
        },
    )['id']
    wait_for_tasks(
        search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
        search_rate=15,
        max_tries=10,
    )
    _validate_package_installed([rhel_contenthost], constants.FAKE_2_CUSTOM_PACKAGE)


@pytest.mark.tier3
@pytest.mark.rhel_ver_list([7, 8, 9])
def test_positive_install_multiple_in_host(
    module_org, activation_key, custom_repo, rhel_contenthost, target_sat
):
    """For a host with multiple applicable errata install one and ensure
    the rest of errata is still available

    :id: 67b7e95b-9809-455a-a74e-f1815cc537fc

    :customerscenario: true

    :BZ: 1469800, 1528275, 1983043, 1905560

    :expectedresults: errata installation task succeeded, available errata
        counter decreased by one; it's possible to schedule another errata
        installation

    :CaseImportance: Medium

    :parametrized: yes

    :CaseLevel: System
    """
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(module_org.label, activation_key.name)
    assert rhel_contenthost.subscribed
    host = rhel_contenthost.nailgun_host
    for package in constants.FAKE_9_YUM_OUTDATED_PACKAGES:
        _install_package(
            module_org, clients=[rhel_contenthost], host_ids=[host.id], package_name=package
        )
    host = host.read()
    applicable_errata_count = host.content_facet_attributes['errata_counts']['total']
    assert applicable_errata_count > 1
    rhel_contenthost.add_rex_key(satellite=target_sat)
    for errata in settings.repos.yum_9.errata[1:4]:
        task_id = target_sat.api.JobInvocation().run(
            data={
                'feature': 'katello_errata_install',
                'inputs': {'errata': str(errata)},
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel_contenthost.hostname}',
                'organization_id': module_org.id,
            },
        )['id']
        wait_for_tasks(
            search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
            search_rate=20,
            max_tries=15,
        )
        host = host.read()
        applicable_errata_count -= 1
        assert host.content_facet_attributes['errata_counts']['total'] == applicable_errata_count


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_list(module_org, custom_repo, target_sat):
    """View all errata specific to repository

    :id: 1efceabf-9821-4804-bacf-2213ac0c7550

    :Setup: Errata synced on satellite server.

    :Steps: Create two repositories each synced and containing errata

    :expectedresults: Check that the errata belonging to one repo is not
        showing in the other.

    :CaseLevel: System
    """
    repo1 = target_sat.api.Repository(id=custom_repo['repository-id']).read()
    repo2 = target_sat.api.Repository(
        product=target_sat.api.Product().create(), url=settings.repos.yum_3.url
    ).create()
    repo2.sync()
    repo1_errata_ids = [
        errata['errata_id'] for errata in repo1.errata(data={'per_page': '1000'})['results']
    ]
    repo2_errata_ids = [
        errata['errata_id'] for errata in repo2.errata(data={'per_page': '1000'})['results']
    ]
    assert len(repo1_errata_ids) == len(settings.repos.yum_9.errata)
    assert len(repo2_errata_ids) == len(settings.repos.yum_3.errata)
    assert CUSTOM_REPO_ERRATA_ID in repo1_errata_ids
    assert CUSTOM_REPO_ERRATA_ID not in repo2_errata_ids
    assert settings.repos.yum_3.errata[5] in repo2_errata_ids
    assert settings.repos.yum_3.errata[5] not in repo1_errata_ids


@pytest.mark.tier3
def test_positive_list_updated(module_org, custom_repo, target_sat):
    """View all errata in an Org sorted by Updated

    :id: 560d6584-70bd-4d1b-993a-cc7665a9e600

    :Setup: Errata synced on satellite server.

    :Steps: GET /katello/api/errata

    :expectedresults: Errata is filtered by Org and sorted by Updated date.

    :CaseLevel: System
    """
    repo = target_sat.api.Repository(id=custom_repo['repository-id']).read()
    assert repo.sync()['result'] == 'success'
    erratum_list = target_sat.api.Errata(repository=repo).search(
        query={'order': 'updated ASC', 'per_page': '1000'}
    )
    updated = [errata.updated for errata in erratum_list]
    assert updated == sorted(updated)


@pytest.mark.tier3
def test_positive_sorted_issue_date_and_filter_by_cve(module_org, custom_repo, target_sat):
    """Sort by issued date and filter errata by CVE

    :id: a921d4c2-8d3d-4462-ba6c-fbd4b898a3f2

    :Setup: Errata synced on satellite server.

    :Steps: GET /katello/api/errata

    :expectedresults: Errata is sorted by issued date and filtered by CVE.

    :CaseLevel: System
    """
    # Errata is sorted by issued date.
    erratum_list = entities.Errata(repository=custom_repo['repository-id']).search(
        query={'order': 'issued ASC', 'per_page': '1000'}
    )
    issued = [errata.issued for errata in erratum_list]
    assert issued == sorted(issued)

    # Errata is filtered by CVE
    erratum_list = target_sat.api.Errata(repository=custom_repo['repository-id']).search(
        query={'order': 'cve DESC', 'per_page': '1000'}
    )
    # Most of Errata don't have any CVEs. Removing empty CVEs from results
    erratum_cves = [errata.cves for errata in erratum_list if errata.cves]
    # Verifying each errata have its CVEs sorted in DESC order
    for errata_cves in erratum_cves:
        cve_ids = [cve['cve_id'] for cve in errata_cves]
        assert cve_ids == sorted(cve_ids, reverse=True)


@pytest.fixture(scope='module')
def setup_content_rhel6():
    """Setup content fot rhel6 content host
    Using `Red Hat Enterprise Virtualization Agents for RHEL 6 Server (RPMs)`
    from manifest, SATTOOLS_REPO for host-tools and yum_9 repo as custom repo.

    :return: Activation Key, Organization, subscription list
    """
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)

    rh_repo_id_rhva = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=constants.PRDS['rhel'],
        repo=constants.REPOS['rhva6']['name'],
        reposet=constants.REPOSET['rhva6'],
        releasever=constants.DEFAULT_RELEASE_VERSION,
    )
    rh_repo = entities.Repository(id=rh_repo_id_rhva).read()
    rh_repo.sync()

    host_tools_product = entities.Product(organization=org).create()
    host_tools_repo = entities.Repository(
        product=host_tools_product,
    ).create()
    host_tools_repo.url = settings.repos.SATCLIENT_REPO.RHEL6
    host_tools_repo = host_tools_repo.update(['url'])
    host_tools_repo.sync()

    custom_product = entities.Product(organization=org).create()
    custom_repo = entities.Repository(
        product=custom_product,
    ).create()
    custom_repo.url = CUSTOM_REPO_URL
    custom_repo = custom_repo.update(['url'])
    custom_repo.sync()

    lce = entities.LifecycleEnvironment(organization=org).create()

    cv = entities.ContentView(
        organization=org,
        repository=[rh_repo_id_rhva, host_tools_repo.id, custom_repo.id],
    ).create()
    cv.publish()
    cvv = cv.read().version[0].read()
    cvv.promote(data={'environment_ids': lce.id, 'force': False})

    ak = entities.ActivationKey(content_view=cv, organization=org, environment=lce).create()

    sub_list = [DEFAULT_SUBSCRIPTION_NAME, host_tools_product.name, custom_product.name]
    for sub_name in sub_list:
        subscription = entities.Subscription(organization=org).search(
            query={'search': f'name="{sub_name}"'}
        )[0]
        ak.add_subscriptions(data={'subscription_id': subscription.id})
    return ak, org, sub_list


@pytest.mark.tier3
def test_positive_get_count_for_host(setup_content_rhel6, rhel6_contenthost, target_sat):
    """Available errata count when retrieving Host

    :id: 2f35933f-8026-414e-8f75-7f4ec048faae

    :Setup:

        1. Errata synced on satellite server.
        2. Some Content hosts present.

    :Steps: GET /api/v2/hosts

    :expectedresults: The available errata count is retrieved.

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: Medium
    """
    ak_name = setup_content_rhel6[0].name
    org_label = setup_content_rhel6[1].label
    org_id = setup_content_rhel6[1].id
    sub_list = setup_content_rhel6[2]
    rhel6_contenthost.install_katello_ca(target_sat)
    rhel6_contenthost.register_contenthost(org_label, ak_name)
    assert rhel6_contenthost.subscribed
    pool_id = rhel6_contenthost.subscription_manager_get_pool(sub_list=sub_list)
    pool_list = [pool_id[0][0], pool_id[1][0], pool_id[2][0]]
    rhel6_contenthost.subscription_manager_attach_pool(pool_list=pool_list)
    rhel6_contenthost.install_katello_host_tools()
    rhel6_contenthost.enable_repo(constants.REPOS['rhva6']['id'])
    host = rhel6_contenthost.nailgun_host
    for errata in ('security', 'bugfix', 'enhancement'):
        _validate_errata_counts(org_id, host, errata_type=errata, expected_value=0)
    rhel6_contenthost.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    _validate_errata_counts(org_id, host, errata_type='security', expected_value=1)
    rhel6_contenthost.run(f'yum install -y {constants.REAL_0_RH_PACKAGE}')
    _validate_errata_counts(org_id, host, errata_type='bugfix', expected_value=2)


@pytest.mark.upgrade
@pytest.mark.tier3
def test_positive_get_applicable_for_host(setup_content_rhel6, rhel6_contenthost, target_sat):
    """Get applicable errata ids for a host

    :id: 51d44d51-eb3f-4ee4-a1df-869629d427ac

    :Setup:
        1. Errata synced on satellite server.
        2. Some Content hosts present.

    :Steps: GET /api/v2/hosts/:id/errata

    :expectedresults: The available errata is retrieved.

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: Medium
    """
    ak_name = setup_content_rhel6[0].name
    org_label = setup_content_rhel6[1].label
    org_id = setup_content_rhel6[1].id
    rhel6_contenthost.install_katello_ca(target_sat)
    rhel6_contenthost.register_contenthost(org_label, ak_name)
    assert rhel6_contenthost.subscribed
    pool_id = rhel6_contenthost.subscription_manager_get_pool(sub_list=setup_content_rhel6[2])
    pool_list = [pool_id[0][0], pool_id[1][0], pool_id[2][0]]
    rhel6_contenthost.subscription_manager_attach_pool(pool_list=pool_list)
    rhel6_contenthost.install_katello_host_tools()
    rhel6_contenthost.enable_repo(constants.REPOS['rhva6']['id'])
    host = rhel6_contenthost.nailgun_host
    erratum = _fetch_available_errata(org_id, host, expected_amount=0)
    assert len(erratum) == 0
    rhel6_contenthost.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    erratum = _fetch_available_errata(org_id, host, 1)
    assert len(erratum) == 1
    assert CUSTOM_REPO_ERRATA_ID in [errata['errata_id'] for errata in erratum]
    rhel6_contenthost.run(f'yum install -y {constants.REAL_0_RH_PACKAGE}')
    erratum = _fetch_available_errata(org_id, host, 3)
    assert len(erratum) == 3
    assert {constants.REAL_1_ERRATA_ID, constants.REAL_2_ERRATA_ID}.issubset(
        {errata['errata_id'] for errata in erratum}
    )


@pytest.mark.tier3
def test_positive_get_diff_for_cv_envs():
    """Generate a difference in errata between a set of environments
    for a content view

    :id: 96732506-4a89-408c-8d7e-f30c8d469769

    :Setup:

        1. Errata synced on satellite server.
        2. Multiple environments present.

    :Steps: GET /katello/api/compare

    :expectedresults: Difference in errata between a set of environments
        for a content view is retrieved.

    :CaseLevel: System
    """
    org = entities.Organization().create()
    env = entities.LifecycleEnvironment(organization=org).create()
    content_view = entities.ContentView(organization=org).create()
    activation_key = entities.ActivationKey(environment=env, organization=org).create()
    for repo_url in [settings.repos.yum_9.url, CUSTOM_REPO_URL]:
        setup_org_for_a_custom_repo(
            {
                'url': repo_url,
                'organization-id': org.id,
                'content-view-id': content_view.id,
                'lifecycle-environment-id': env.id,
                'activationkey-id': activation_key.id,
            }
        )
    new_env = entities.LifecycleEnvironment(organization=org, prior=env).create()
    cvvs = content_view.read().version[-2:]
    cvvs[-1].promote(data={'environment_ids': new_env.id, 'force': False})
    result = entities.Errata().compare(
        data={'content_view_version_ids': [cvv.id for cvv in cvvs], 'per_page': '9999'}
    )
    cvv2_only_errata = next(
        errata for errata in result['results'] if errata['errata_id'] == CUSTOM_REPO_ERRATA_ID
    )
    assert cvvs[-1].id in cvv2_only_errata['comparison']
    both_cvvs_errata = next(
        errata
        for errata in result['results']
        if errata['errata_id'] in constants.FAKE_9_YUM_SECURITY_ERRATUM
    )
    assert {cvv.id for cvv in cvvs} == set(both_cvvs_errata['comparison'])


@pytest.mark.skip_if_open("BZ:2013093")
@pytest.mark.tier3
def test_positive_incremental_update_required(
    module_org,
    module_lce,
    activation_key,
    module_cv,
    custom_repo,
    rh_repo,
    rhel7_contenthost,
    target_sat,
):
    """Given a set of hosts and errata, check for content view version
    and environments that need updating."

    :id: 6dede920-ba6b-4c51-b782-c6db6ea3ee4f

    :Setup:
        1. Errata synced on satellite server

    :Steps:
        1. Create VM as Content Host, registering to CV with custom errata
        2. Install package in VM so it needs one erratum
        3. Check if incremental_updates required:
            POST /api/hosts/bulk/available_incremental_updates
        4. Assert empty [] result (no incremental update required)
        5. Apply a filter to the CV so errata will be applicable but not installable
        6. Publish the new version
        7. Promote the new version into the same LCE
        8. Check if incremental_updates required:
            POST /api/hosts/bulk/available_incremental_updates
        9. Assert incremental update is suggested


    :expectedresults: Incremental update requirement is detected.

    :parametrized: yes

    :CaseLevel: System

    :BZ: 2013093
    """
    rhel7_contenthost.install_katello_ca(target_sat)
    rhel7_contenthost.register_contenthost(module_org.label, activation_key.name)
    assert rhel7_contenthost.subscribed
    rhel7_contenthost.enable_repo(constants.REPOS['rhst7']['id'])
    rhel7_contenthost.install_katello_agent()
    host = rhel7_contenthost.nailgun_host
    # install package to create demand for an Erratum
    _install_package(
        module_org,
        [rhel7_contenthost],
        [host.id],
        constants.FAKE_1_CUSTOM_PACKAGE,
        via_ssh=True,
        rpm_package_name=constants.FAKE_1_CUSTOM_PACKAGE,
    )
    # Call nailgun to make the API POST to see if any incremental updates are required
    response = entities.Host().bulk_available_incremental_updates(
        data={
            'organization_id': module_org.id,
            'included': {'ids': [host.id]},
            'errata_ids': [settings.repos.yum_6.errata[2]],
        },
    )
    assert not response, 'Incremental update should not be required at this point'
    # Add filter of type include but do not include anything
    # this will hide all RPMs from selected erratum before publishing
    entities.RPMContentViewFilter(
        content_view=module_cv, inclusion=True, name='Include Nothing'
    ).create()
    module_cv.publish()
    module_cv = module_cv.read()
    CV1V = module_cv.version[-1].read()
    # Must promote a CV version into a new Environment before we can add errata
    CV1V.promote(data={'environment_ids': module_lce.id, 'force': False})
    module_cv = module_cv.read()
    # Call nailgun to make the API POST to ensure an incremental update is required
    response = entities.Host().bulk_available_incremental_updates(
        data={
            'organization_id': module_org.id,
            'included': {'ids': [host.id]},
            'errata_ids': [settings.repos.yum_6.errata[2]],
        },
    )
    assert 'next_version' in response[0], 'Incremental update should be suggested'
    'at this point'


def _run_remote_command_on_content_host(module_org, command, vm, return_result=False):
    result = vm.run(command)
    assert result.status == 0
    if return_result:
        return result.stdout


def _set_prerequisites_for_swid_repos(module_org, vm):
    _run_remote_command_on_content_host(
        module_org, f'curl --insecure --remote-name {settings.repos.swid_tools_repo}', vm
    )
    _run_remote_command_on_content_host(module_org, "mv *swid*.repo /etc/yum.repos.d", vm)
    _run_remote_command_on_content_host(module_org, "yum install -y swid-tools", vm)
    _run_remote_command_on_content_host(module_org, "dnf install -y dnf-plugin-swidtags", vm)


def _validate_swid_tags_installed(module_org, vm, module_name):
    result = _run_remote_command_on_content_host(
        module_org, f"swidq -i -n {module_name} | grep 'Name'", vm, return_result=True
    )
    assert module_name in result


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.pit_client
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [{'YumRepository': {'url': settings.repos.swid_tag.url, 'distro': 'rhel8'}}],
    indirect=True,
)
def test_errata_installation_with_swidtags(
    module_org, module_lce, module_repos_collection_with_manifest, rhel8_contenthost, target_sat
):
    """Verify errata installation with swid_tags and swid tags get updated after
    module stream update.

    :id: 43a59b9a-eb9b-4174-8b8e-73d923b1e51e

    :steps:

        1. create product and repository having swid tags
        2. create content view and published it with repository
        3. create activation key and register content host
        4. create rhel8, swid repos on content host
        5. install swid-tools, dnf-plugin-swidtags packages on content host
        6. install older module stream and generate errata, swid tag
        7. assert errata count, swid tags are generated
        8. install errata vis updating module stream
        9. assert errata count and swid tag after module update

    :expectedresults: swid tags should get updated after errata installation via
        module stream update

    :CaseAutomation: Automated

    :parametrized: yes

    :CaseImportance: Critical

    :CaseLevel: System
    """
    module_name = 'kangaroo'
    version = '20180704111719'
    # setup rhel8 and sat_tools_repos
    rhel8_contenthost.create_custom_repos(
        **{
            'baseos': settings.repos.rhel8_os.baseos,
            'appstream': settings.repos.rhel8_os.appstream,
        }
    )
    module_repos_collection_with_manifest.setup_virtual_machine(
        rhel8_contenthost, install_katello_agent=False
    )

    # install older module stream
    rhel8_contenthost.add_rex_key(satellite=target_sat)
    _set_prerequisites_for_swid_repos(module_org, vm=rhel8_contenthost)
    _run_remote_command_on_content_host(
        module_org, f'dnf -y module install {module_name}:0:{version}', rhel8_contenthost
    )
    Host.errata_recalculate({'host-id': rhel8_contenthost.nailgun_host.id})
    # validate swid tags Installed
    before_errata_apply_result = _run_remote_command_on_content_host(
        module_org,
        f"swidq -i -n {module_name} | grep 'File' | grep -o 'rpm-.*.swidtag'",
        rhel8_contenthost,
        return_result=True,
    )
    assert before_errata_apply_result != ''
    host = rhel8_contenthost.nailgun_host
    host = host.read()
    applicable_errata_count = host.content_facet_attributes['errata_counts']['total']
    assert applicable_errata_count == 1

    # apply modular errata
    _run_remote_command_on_content_host(
        module_org, f'dnf -y module update {module_name}', rhel8_contenthost
    )
    _run_remote_command_on_content_host(module_org, 'dnf -y upload-profile', rhel8_contenthost)
    Host.errata_recalculate({'host-id': rhel8_contenthost.nailgun_host.id})
    host = host.read()
    applicable_errata_count -= 1
    assert host.content_facet_attributes['errata_counts']['total'] == applicable_errata_count
    after_errata_apply_result = _run_remote_command_on_content_host(
        module_org,
        f"swidq -i -n {module_name} | grep 'File'| grep -o 'rpm-.*.swidtag'",
        rhel8_contenthost,
        return_result=True,
    )

    # swidtags get updated based on package version
    assert before_errata_apply_result != after_errata_apply_result


"""Section for tests using RHEL8 Content Host.
   The applicability tests using Default Content View are related to the introduction of Pulp3.
   """


@pytest.fixture(scope='module')
def rh_repo_module_manifest(module_manifest_org):
    """Use module manifest org, creates tools repo, syncs and returns RH repo."""
    # enable rhel repo and return its ID
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=module_manifest_org.id,
        product=constants.PRDS['rhel8'],
        repo=constants.REPOS['rhst8']['name'],
        reposet=constants.REPOSET['rhst8'],
        releasever='None',
    )
    # Sync step because repo is not synced by default
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


@pytest.fixture(scope='module')
def rhel8_custom_repo_cv(module_manifest_org):
    """Create repo and publish CV so that packages are in Library"""
    return setup_org_for_a_custom_repo(
        {
            'url': settings.repos.module_stream_1.url,
            'organization-id': module_manifest_org.id,
        }
    )


@pytest.fixture(scope='module')
def rhel8_module_ak(
    module_manifest_org, default_lce, rh_repo_module_manifest, rhel8_custom_repo_cv
):
    rhel8_module_ak = entities.ActivationKey(
        content_view=module_manifest_org.default_content_view,
        environment=entities.LifecycleEnvironment(id=module_manifest_org.library.id),
        organization=module_manifest_org,
    ).create()
    # Ensure tools repo is enabled in the activation key
    rhel8_module_ak.content_override(
        data={
            'content_overrides': [{'content_label': constants.REPOS['rhst8']['id'], 'value': '1'}]
        }
    )
    # Fetch available subscriptions
    subs = entities.Subscription(organization=module_manifest_org).search(
        query={'search': f'{constants.DEFAULT_SUBSCRIPTION_NAME}'}
    )
    assert subs
    # Add default subscription to activation key
    rhel8_module_ak.add_subscriptions(data={'subscription_id': subs[0].id})
    # Add custom subscription to activation key
    product = entities.Product(organization=module_manifest_org).search(
        query={'search': "redhat=false"}
    )
    custom_sub = entities.Subscription(organization=module_manifest_org).search(
        query={'search': f"name={product[0].name}"}
    )
    rhel8_module_ak.add_subscriptions(data={'subscription_id': custom_sub[0].id})
    return rhel8_module_ak


@pytest.mark.tier2
def test_apply_modular_errata_using_default_content_view(
    module_manifest_org,
    default_lce,
    rhel8_contenthost,
    rhel8_module_ak,
    rhel8_custom_repo_cv,
    target_sat,
):
    """
    Registering a RHEL8 system to the default content view with no modules enabled results in
    no modular errata or packages showing as applicable or installable

    Enabling a module on a RHEL8 system assigned to the default content view and installing an
    older package should result in the modular errata and package showing as applicable and
    installable

    :id: 030981dd-19ba-4f8b-9c24-0aee90aaa4c4

    Steps:
        1. Register host with AK, install tools
        2. Assert no errata indicated
        3. Install older version of stream
        4. Assert errata is applicable
        5. Update module stream
        6. Assert errata is no longer applicable

    :expectedresults:  Errata enumeration works with module streams when using default Content View

    :CaseAutomation: Automated

    :parametrized: yes

    :CaseLevel: System
    """
    module_name = 'duck'
    stream = '0'
    version = '20180704244205'

    rhel8_contenthost.install_katello_ca(target_sat)
    rhel8_contenthost.register_contenthost(module_manifest_org.label, rhel8_module_ak.name)
    assert rhel8_contenthost.subscribed
    host = rhel8_contenthost.nailgun_host
    host = host.read()
    # Assert no errata on host, no packages applicable or installable
    errata = _fetch_available_errata(module_manifest_org, host, expected_amount=0)
    assert len(errata) == 0
    rhel8_contenthost.install_katello_host_tools()
    # Install older version of module stream to generate the errata
    result = rhel8_contenthost.execute(
        f'yum -y module install {module_name}:{stream}:{version}',
    )
    assert result.status == 0
    # Check that there is now two errata applicable
    errata = _fetch_available_errata(module_manifest_org, host, 2)
    assert len(errata) == 2
    # Assert that errata package is required
    assert constants.FAKE_3_CUSTOM_PACKAGE in errata[0]['module_streams'][0]['packages']
    # Update module
    result = rhel8_contenthost.execute(
        f'yum -y module update {module_name}:{stream}:{version}',
    )
    assert result.status == 0
    # Check that there is now no errata applicable
    errata = _fetch_available_errata(module_manifest_org, host, 0)
    assert len(errata) == 0
