"""Tests for http-proxy component.

:Requirement: HttpProxy

:CaseComponent: HTTPProxy

:team: Endeavour

:CaseImportance: High

:CaseAutomation: Automated

"""

import json

from fauxfactory import gen_string
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.constants.repos import ANSIBLE_GALAXY, CUSTOM_FILE_REPO


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize(
    'setup_http_proxy',
    [True, False],
    indirect=True,
    ids=['auth_http_proxy', 'unauth_http_proxy'],
)
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel7',
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': settings.repos.module_stream_1.url},
            'FileRepository': {'url': CUSTOM_FILE_REPO},
            'DockerRepository': {
                'url': settings.container.registry_hub,
                'upstream_name': settings.container.upstream_name,
            },
            'AnsibleRepository': {
                'url': ANSIBLE_GALAXY,
                'requirements': [
                    {'name': 'theforeman.foreman', 'version': '2.1.0'},
                    {'name': 'theforeman.operations', 'version': '0.1.0'},
                ],
            },
        }
    ],
    indirect=True,
)
def test_positive_end_to_end(
    setup_http_proxy, module_target_sat, module_org, module_repos_collection_with_manifest
):
    """End-to-end test for HTTP proxy related scenarios.

    :id: 38df5479-9127-49f3-a30e-26b33655971a

    :customerscenario: true

    :setup:
        1. Create HTTP proxy entity at the Satellite.
        2. Create RH yum repository.
        3. Create custom repo of each content type (yum, file, docker, ansible collection).

    :steps:
        1. Set immediate download policy where applicable for complete sync testing.
        2. For each repo set global default HTTP proxy and sync it.
        3. For each repo set specific HTTP proxy and sync it.
        4. For each repo set no HTTP proxy and sync it.
        5. Refresh manifest through HTTP proxy.
        6. Discover yum type repo through HTTP proxy.
        7. Discover docker type repo through HTTP proxy.

    :expectedresults:
        1. All repository updates and syncs succeed.
        2. Manifest can be refreshed through HTTP proxy.
        3. Yum and docker repos can be discovered through HTTP proxy.

    :BZ: 2011303, 2042473, 2046337

    :parametrized: yes

    :CaseImportance: Critical
    """
    # Set immediate download policy where applicable for complete sync testing
    for repo in module_repos_collection_with_manifest.repos_info:
        if repo['content-type'] in ['yum', 'docker']:
            module_target_sat.api.Repository(id=repo['id'], download_policy='immediate').update()

    # For each repo set global/specific/no HTTP proxy and sync it
    for policy in ['global_default_http_proxy', 'use_selected_http_proxy', 'none']:
        for repo in module_repos_collection_with_manifest.repos_info:
            repo = module_target_sat.api.Repository(
                id=repo['id'],
                http_proxy_policy=policy,
                http_proxy_id=setup_http_proxy[0].id if 'selected' in policy else None,
            ).update()
            assert repo.http_proxy_policy == policy, (
                f'Policy update failed for {repo.content_type} repo with {policy} HTTP policy'
            )
            assert (
                repo.http_proxy_id == setup_http_proxy[0].id
                if 'selected' in policy
                else repo.http_proxy_id is None
            ), f'Proxy id update failed for {repo.content_type} repo with {policy} HTTP policy'
            assert 'success' in module_target_sat.api.Repository(id=repo.id).sync()['result'], (
                f'Sync of a {repo.content_type} repo with {policy} HTTP policy failed'
            )

    # Refresh manifest through HTTP proxy
    res = module_target_sat.api.Subscription().refresh_manifest(
        data={'organization_id': module_org.id}
    )
    assert 'success' in res['result']

    # Discover yum type repo through HTTP proxy
    repo_name = 'fakerepo01'
    yum_repo = module_target_sat.api.Organization(id=module_org.id).repo_discover(
        data={
            "id": module_org.id,
            "url": settings.repos.repo_discovery.url,
            "content_type": "yum",
        }
    )
    assert len(yum_repo['output']) == 1
    assert yum_repo['output'][0] == f'{settings.repos.repo_discovery.url}/{repo_name}/'

    # Discover docker type repo through HTTP proxy
    docker_repo = module_target_sat.api.Organization(id=module_org.id).repo_discover(
        data={
            "id": module_org.id,
            "url": 'quay.io',
            "content_type": "docker",
            "search": 'foreman/foreman',
        }
    )
    assert len(docker_repo['output']) > 0
    assert docker_repo['result'] == 'success'


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.rhel_ver_match('9')
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize(
    'setup_http_proxy',
    [True, False],
    indirect=True,
    ids=['auth_http_proxy', 'unauth_http_proxy'],
)
def test_positive_install_content_with_http_proxy(
    setup_http_proxy, module_target_sat, rhel_contenthost, function_sca_manifest_org
):
    """Attempt to sync and install RH content on a content host via HTTP proxy.

    :id: cce888b5-e023-4ee2-bffe-efa9260224ee

    :setup:
        1. Satellite with or without Global HTTP proxy set.
        2. Unregistered RHEL contenthost.

    :steps:
        1. Create an LCE and CV.
        2. Sync a RH repository, publish it in the CV, promote to the LCE.
        3. Create an AK using the created entities and override the RH repo to Enabled.
        4. Register the content host using the AK via global registration.
        5. Install a package from the RH repository.

    :expectedresults:
        1. RH repos can be synced successfully.
        2. Content host can be registered via AK.
        3. Content can be installed on the content host.

    :customerscenario: true

    :parametrized: yes
    """
    repo_to_use = 'rhsclient9'
    pkg_name = 'katello-host-tools'
    org = function_sca_manifest_org
    lce = module_target_sat.api.LifecycleEnvironment(organization=org).create()
    content_view = module_target_sat.api.ContentView(organization=org).create()
    rh_repo_id = module_target_sat.api_factory.enable_sync_redhat_repo(
        constants.REPOS[repo_to_use], org.id
    )
    rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    assert rh_repo.content_counts['rpm'] >= 1
    content_view = module_target_sat.api.ContentView(
        id=content_view.id, repository=[rh_repo]
    ).update(["repository"])
    content_view.publish()
    content_view = content_view.read()
    content_view.version[-1].promote(data={'environment_ids': lce.id})

    activation_key = module_target_sat.api.ActivationKey(
        content_view=content_view,
        organization=org,
        environment=lce,
    ).create()
    activation_key.content_override(
        data={
            'content_overrides': [
                {'content_label': constants.REPOS[repo_to_use]['id'], 'value': '1'}
            ]
        }
    )

    result = rhel_contenthost.register(
        org=org,
        activation_keys=activation_key.name,
        target=module_target_sat,
        loc=None,
    )
    assert result.status == 0, f'Failed to register the host: {rhel_contenthost.hostname}'
    assert rhel_contenthost.subscribed

    result = rhel_contenthost.execute(f'yum install -y {pkg_name}')
    assert result.status == 0, f'{pkg_name} installation failed with: {result.stderr}'


@pytest.mark.e2e
def test_positive_assign_http_proxy_to_products(target_sat, function_org):
    """Assign http_proxy to Products and check whether http-proxy is
     used during sync.

    :id: c9d23aa1-3325-4abd-a1a6-d5e75c12b08a

    :setup:
        1. Create an Organization.

    :steps:
        1. Create two HTTP proxies.
        2. Create two products and two repos in each product with various HTTP proxy policies.
        3. Set the HTTP proxy through bulk action for both products.
        4. Bulk sync one product.

    :expectedresults:
        1. HTTP Proxy is assigned to all repos present in Products
           and sync operation uses assigned http-proxy and pass.
    """
    # Create two HTTP proxies
    http_proxy_a = target_sat.api.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.un_auth_proxy_url,
        organization=[function_org],
    ).create()
    http_proxy_b = target_sat.api.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.auth_proxy_url,
        username=settings.http_proxy.username,
        password=settings.http_proxy.password,
        organization=[function_org],
    ).create()

    # Create two products and two repos in each product with various HTTP proxy policies
    product_a = target_sat.api.Product(organization=function_org).create()
    product_b = target_sat.api.Product(organization=function_org).create()
    repo_a1 = target_sat.api.Repository(product=product_a, http_proxy_policy='none').create()
    repo_a2 = target_sat.api.Repository(
        product=product_a,
        http_proxy_policy='use_selected_http_proxy',
        http_proxy_id=http_proxy_a.id,
    ).create()
    repo_b1 = target_sat.api.Repository(product=product_b, http_proxy_policy='none').create()
    repo_b2 = target_sat.api.Repository(
        product=product_b, http_proxy_policy='global_default_http_proxy'
    ).create()

    # Set the HTTP proxy through bulk action for both products
    target_sat.api.ProductBulkAction().http_proxy(
        data={
            "ids": [product_a.id, product_b.id],
            "http_proxy_policy": "use_selected_http_proxy",
            "http_proxy_id": http_proxy_b.id,
        }
    )
    for repo in repo_a1, repo_a2, repo_b1, repo_b2:
        r = repo.read()
        assert r.http_proxy_policy == "use_selected_http_proxy"
        assert r.http_proxy_id == http_proxy_b.id
    assert 'success' in product_a.sync()['result'], 'Product sync failed'


def test_positive_sync_proxy_with_certificate(request, target_sat, module_org, module_product):
    """Assign http_proxy with cacert.crt to repository and test
       that http_proxy and cacert are used during sync.

    :id: a9645b7f-228e-4f4d-ab04-610382bd2d0b

    :steps:
        1. Generate new cert files with custom_cert_generate.
        2. Create new http-proxy with path to cacert.
        3. Create new repository, assign http-proxy.
        4. Perform repo sync. Clean up new custom certs.

    :expectedresults: http-proxy with cacert is assigned to repo,
        sync operation uses assigned http-proxy with the cacert.

    :BZ: 2144044

    :customerscenario: true
    """

    @request.addfinalizer
    def _finalize():
        target_sat.custom_certs_cleanup()

    # Cleanup any existing certs that may conflict
    target_sat.custom_certs_cleanup()
    proxy_host = settings.http_proxy.auth_proxy_url.replace('http://', '').replace(':3128', '')
    cacert_path = '/root/cacert.crt'

    # Create and fetch new cerfiticate
    target_sat.custom_cert_generate(proxy_host)

    @request.addfinalizer
    def _finalize():
        target_sat.custom_certs_cleanup()

    cacert = target_sat.execute(f'cat {cacert_path}').stdout
    assert 'END CERTIFICATE' in cacert

    # Create http-proxy and repository
    http_proxy = target_sat.api.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.auth_proxy_url,
        username=settings.http_proxy.username,
        password=settings.http_proxy.password,
        organization=[module_org],
        cacert=cacert_path,
    ).create()
    repo = target_sat.api.Repository(
        product=module_product,
        http_proxy_policy='use_selected_http_proxy',
        http_proxy_id=http_proxy.id,
    ).create()
    module_product.update()

    assert repo.http_proxy_policy == 'use_selected_http_proxy'
    assert repo.http_proxy_id == http_proxy.id

    response = repo.sync()
    assert response.get('errors') is None
    assert repo.read().last_sync is not None
    assert repo.read().content_counts['rpm'] >= 1


def test_refresh_updates_remotes_proxy(module_target_sat, module_org, module_product):
    """Ensure that repo refresh updates the http-proxy of pulp remote.

    :id: ab0f3734-40bd-4524-b8b9-0ab857ca3c3f

    :setup:
        1. Disable pulp CLI safe mode.
        2. Create a product, repo and HTTP proxy.

    :steps:
        1. Get repository remote's href.
        2. Ensure proxy_url matches the one from setup.
        3. Set fake value to proxy_url, ensure it's written.
        4. Refresh repos via rake and ensure the original proxy_url has been restored.

    :expectedresults:
        1. Repo refresh restores remote's original proxy_url value.

    :verifies: SAT-26741

    :customerscenario: true
    """
    sat = module_target_sat

    http_proxy = sat.api.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.un_auth_proxy_url,
        organization=[module_org],
    ).create()

    repo = sat.api.Repository(
        product=module_product,
        http_proxy_policy='use_selected_http_proxy',
        http_proxy_id=http_proxy.id,
    ).create()
    sat.run_repos_refresh()

    # Get repository remote's href.
    href = sat.execute(
        f'echo "::Katello::Repository.find({repo.id}).remote_href" | foreman-rake console'
    ).stdout.split('"')[1]

    # Ensure proxy_url matches the one from setup.
    remote = json.loads(sat.execute(f'pulp rpm remote show --href "{href}"').stdout)
    assert remote['proxy_url'] == http_proxy.url

    # Set fake value to proxy_url, ensure it's written.
    fake_proxy_url = 'http://my.proxy.com:3128'
    sat.execute(f'pulp --force rpm remote update --href "{href}" --proxy-url "{fake_proxy_url}"')
    remote = json.loads(sat.execute(f'pulp rpm remote show --href "{href}"').stdout)
    assert remote['proxy_url'] == fake_proxy_url

    # Refresh repos via rake and ensure the original proxy_url has been restored.
    sat.run_repos_refresh()
    remote = json.loads(sat.execute(f'pulp rpm remote show --href "{href}"').stdout)
    assert remote['proxy_url'] == http_proxy.url
