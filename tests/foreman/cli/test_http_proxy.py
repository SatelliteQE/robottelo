"""Tests for http-proxy hammer command.

:Requirement: HttpProxy

:CaseComponent: HTTPProxy

:team: Phoenix-content

:CaseImportance: High

:CaseAutomation: Automated

"""

from fauxfactory import gen_integer, gen_string, gen_url
import pytest

from robottelo.config import settings
from robottelo.constants import FAKE_0_YUM_REPO_PACKAGES_COUNT
from robottelo.exceptions import CLIReturnCodeError


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_update_delete(module_org, module_location, target_sat):
    """Create new http-proxy with attributes, update and delete it.

    :id: 6045010f-b43b-46f0-b80f-21505fa021c8

    :BZ: 1774325

    :steps:

        1. hammer http-proxy create <args>
        2. hammer http-proxy update <args>
        3. hammer http-proxy delete <args>

    :expectedresults: CRUD operations related to http-proxy hammer command are successful.

    :CaseImportance: Critical
    """
    name = gen_string('alpha', 15)
    url = f'{gen_url(scheme="https")}:{gen_integer(min_value=10, max_value=9999)}'
    password = gen_string('alpha', 15)
    username = gen_string('alpha', 15)

    updated_name = gen_string('alpha', 15)
    updated_url = f'{gen_url(scheme="https")}:{gen_integer(min_value=10, max_value=9999)}'
    updated_password = gen_string('alpha', 15)
    updated_username = gen_string('alpha', 15)

    # Create
    http_proxy = target_sat.cli.HttpProxy.create(
        {
            'name': name,
            'url': url,
            'username': username,
            'password': password,
            'organization-id': module_org.id,
            'location-id': module_location.id,
        }
    )
    assert http_proxy['name'] == name
    assert http_proxy['url'] == url
    assert http_proxy['username'] == username

    # Update
    target_sat.cli.HttpProxy.update(
        {
            'name': name,
            'new-name': updated_name,
            'url': updated_url,
            'username': updated_username,
            'password': updated_password,
        }
    )
    updated_http_proxy = target_sat.cli.HttpProxy.info({'id': http_proxy['id']})
    assert updated_http_proxy['name'] == updated_name
    assert updated_http_proxy['url'] == updated_url
    assert updated_http_proxy['username'] == updated_username

    # Delete
    target_sat.cli.HttpProxy.delete({'id': updated_http_proxy['id']})
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.HttpProxy.info({'id': updated_http_proxy['id']})


@pytest.mark.tier3
@pytest.mark.run_in_one_thread
@pytest.mark.stubbed
def test_insights_client_registration_with_http_proxy():
    """Verify that insights-client registration work with http proxy.

    :id: 5158d5c1-2b88-4c05-914b-f1c53656ffc2

    :customerscenario: true

    :steps:
        1. Create HTTP Proxy.
        2. Set created proxy as "Default HTTP Proxy" in settings.
        3. Edit /etc/resolv.conf and comment out all entries so that
            satellite can not directly communicate outside. Ensure that
            NetworkManger won't change it.
        4. Register a host with satellite.
        5. Register host with insights.
        6. Try insights-client register/unregister/test-connection/status

    :BZ: 1959932

    :expectedresults:
        1. insights-client register/unregister/test-connection/status
            works with http proxy set.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.tier2
@pytest.mark.run_in_one_thread
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.skipif((not settings.http_proxy.UN_AUTH_PROXY_URL), reason='Missing un_auth_proxy_url')
def test_positive_set_content_default_http_proxy(block_fake_repo_access, target_sat):
    """An http proxy can be set to be the global default for repositories.

    :id: c12868eb-98f1-4763-a168-281ac44d9ff5

    :steps:
            1. Create a product with repo.
            2. Create an un-authenticated proxy.
            3. Set the proxy to be the global default proxy.
            4. Sync a repo.

    :expectedresults:  Repo is synced
    """
    org = target_sat.api.Organization().create()
    proxy_name = gen_string('alpha', 15)
    proxy_url = settings.http_proxy.un_auth_proxy_url
    product = target_sat.api.Product(organization=org).create()
    rpm_repo = target_sat.api.Repository(
        product=product, content_type='yum', url=settings.repos.yum_1.url
    ).create()

    # Create un-auth HTTP proxy
    http_proxy = target_sat.cli.HttpProxy.create(
        {
            'name': proxy_name,
            'url': proxy_url,
            'organization-id': org.id,
        }
    )
    assert http_proxy['name'] == proxy_name
    assert http_proxy['url'] == proxy_url
    # Set the proxy to be the global default
    proxy_settings = target_sat.cli.Settings.set(
        {
            'name': 'content_default_http_proxy',
            'value': proxy_name,
        }
    )
    assert proxy_settings
    # Sync to check proxy works
    assert rpm_repo.read().content_counts['rpm'] == 0
    product.sync()
    assert rpm_repo.read().content_counts['rpm'] >= 1


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_environment_variable_unset_set():
    """Verify that satellite installer unsets and then sets back the environment variables

    :id: 596d753b-660b-49cb-b663-ff3cec439564

    :BZ: 1886040

    :customerscenario: true

    :steps:
        1. Export any environment variable from
           [http_proxy, https_proxy, ssl_cert_file, HTTP_PROXY, HTTPS_PROXY, SSL_CERT_FILE]
        2. satellite-installer

    :expectedresults: satellite-installer unsets system proxy and SSL environment variables
                      only for the duration of install and sets back those in the end.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.e2e
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_assign_http_proxy_to_products(module_org, module_target_sat):
    """Assign http_proxy to Products and perform product sync.

    :id: 6af7b2b8-15d5-4d9f-9f87-e76b404a966f

    :steps:
        1. Create two HTTP proxies.
        2. Create two products and two repos in each product with various HTTP proxy policies.
        3. Set the HTTP proxy through bulk action for both products to the selected proxy.
        4. Bulk sync both products and verify packages counts.
        5. Set the HTTP proxy through bulk action for both products to None.

    :expectedresults:
        1. HTTP Proxy is assigned to all repos present in Products
           and sync operation uses assigned http-proxy and pass.

    :expectedresults:
        1. HTTP Proxy is assigned to all repos present in Products
           and sync operation performed successfully.
    """
    # Create two HTTP proxies
    http_proxy_a = module_target_sat.cli.HttpProxy.create(
        {
            'name': gen_string('alpha', 15),
            'url': settings.http_proxy.un_auth_proxy_url,
            'organization-id': module_org.id,
        },
    )
    http_proxy_b = module_target_sat.cli.HttpProxy.create(
        {
            'name': gen_string('alpha', 15),
            'url': settings.http_proxy.auth_proxy_url,
            'username': settings.http_proxy.username,
            'password': settings.http_proxy.password,
            'organization-id': module_org.id,
        },
    )

    # Create two products and two repos in each product with various HTTP proxy policies
    product_a = module_target_sat.cli_factory.make_product({'organization-id': module_org.id})
    product_b = module_target_sat.cli_factory.make_product({'organization-id': module_org.id})
    repo_a1 = module_target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_a['id'],
            'url': settings.repos.yum_0.url,
            'http-proxy-policy': 'none',
        },
    )
    repo_a2 = module_target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_a['id'],
            'url': settings.repos.yum_0.url,
            'http-proxy-policy': 'use_selected_http_proxy',
            'http-proxy-id': http_proxy_a['id'],
        },
    )
    repo_b1 = module_target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_b['id'],
            'url': settings.repos.yum_0.url,
            'http-proxy-policy': 'none',
        },
    )
    repo_b2 = module_target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_b['id'],
            'url': settings.repos.yum_0.url,
        },
    )

    # Set the HTTP proxy through bulk action for both products to the selected proxy
    res = module_target_sat.cli.Product.update_proxy(
        {
            'ids': f"{product_a['id']},{product_b['id']}",
            'http-proxy-policy': 'use_selected_http_proxy',
            'http-proxy-id': http_proxy_b['id'],
        }
    )
    assert 'Product proxy updated' in res
    module_target_sat.wait_for_tasks(
        search_query=(
            f'Actions::Katello::Repository::Update and organization_id = {module_org.id}'
        ),
        max_tries=5,
        poll_rate=10,
    )
    for repo in repo_a1, repo_a2, repo_b1, repo_b2:
        result = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert result['http-proxy']['http-proxy-policy'] == 'use_selected_http_proxy'
        assert result['http-proxy']['id'] == http_proxy_b['id']

    # Bulk sync both products and verify packages counts
    module_target_sat.cli.Product.synchronize(
        {'id': product_a['id'], 'organization-id': module_org.id}
    )
    module_target_sat.cli.Product.synchronize(
        {'id': product_b['id'], 'organization-id': module_org.id}
    )
    for repo in repo_a1, repo_a2, repo_b1, repo_b2:
        info = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert int(info['content-counts']['packages']) == FAKE_0_YUM_REPO_PACKAGES_COUNT

    # Set the HTTP proxy through bulk action for both products to None
    res = module_target_sat.cli.Product.update_proxy(
        {'ids': f"{product_a['id']},{product_b['id']}", 'http-proxy-policy': 'none'}
    )
    assert 'Product proxy updated' in res
    module_target_sat.wait_for_tasks(
        search_query=(
            f'Actions::Katello::Repository::Update and organization_id = {module_org.id}'
        ),
        max_tries=5,
        poll_rate=10,
    )
    for repo in repo_a1, repo_a2, repo_b1, repo_b2:
        result = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert result['http-proxy']['http-proxy-policy'] == 'none'
