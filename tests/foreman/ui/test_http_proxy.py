"""Tests for http-proxy UI component.

:Requirement: HttpProxy

:CaseLevel: Acceptance

:CaseComponent: Repositories

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import pytest
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import REPO_TYPE


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_loc():
    return entities.Location().create()


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_create_update_delete(session, module_org, module_loc):
    """Create new http-proxy with attributes, update and delete it.

    :id: 0c7cdf3d-778f-427a-9a2f-42ad7c23aa15

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    http_proxy_name = gen_string('alpha', 15)
    updated_proxy_name = gen_string('alpha', 15)
    http_proxy_url = '{}:{}'.format(
        gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999)
    )
    password = gen_string('alpha', 15)
    username = gen_string('alpha', 15)

    with session:
        session.http_proxy.create(
            {
                'http_proxy.name': http_proxy_name,
                'http_proxy.url': http_proxy_url,
                'http_proxy.username': username,
                'http_proxy.password': password,
                'locations.resources.assigned': [module_loc.name],
                'organizations.resources.assigned': [module_org.name],
            }
        )
        assert session.http_proxy.search(http_proxy_name)[0]['Name'] == http_proxy_name
        http_proxy_values = session.http_proxy.read(http_proxy_name)
        assert http_proxy_values['http_proxy']['name'] == http_proxy_name
        assert http_proxy_values['http_proxy']['url'] == http_proxy_url
        assert http_proxy_values['http_proxy']['username'] == username
        assert http_proxy_values['locations']['resources']['assigned'][0] == module_loc.name
        assert http_proxy_values['organizations']['resources']['assigned'][0] == module_org.name
        # Update http_proxy with new name
        session.http_proxy.update(http_proxy_name, {'http_proxy.name': updated_proxy_name})
        assert session.http_proxy.search(updated_proxy_name)[0]['Name'] == updated_proxy_name
        # Delete http_proxy
        session.http_proxy.delete(updated_proxy_name)
        assert not entities.HTTPProxy().search(query={'search': f'name={updated_proxy_name}'})


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_assign_http_proxy_to_products_repositories(session, module_org, module_loc):
    """Assign HTTP Proxy to Products and Repositories.

    :id: 2b803f9c-8d5d-4467-8eba-18244ebc0201

    :expectedresults: HTTP Proxy is assigned to all repos present
        in Products.

    :CaseImportance: Critical
    """
    # create HTTP proxies
    http_proxy_a = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.un_auth_proxy_url,
        organization=[module_org.id],
        location=[module_loc.id],
    ).create()
    http_proxy_b = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.auth_proxy_url,
        username=settings.http_proxy.username,
        password=settings.http_proxy.password,
        organization=[module_org.id],
        location=[module_loc.id],
    ).create()
    # Create products
    product_a = entities.Product(
        organization=module_org.id,
    ).create()
    product_b = entities.Product(
        organization=module_org.id,
    ).create()
    # Create repositories from UI.
    with session:
        repo_a1_name = gen_string('alpha')
        session.repository.create(
            product_a.name,
            {
                'name': repo_a1_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
                'repo_content.http_proxy_policy': 'No HTTP Proxy',
            },
        )
        repo_a1_values = session.repository.read(product_a.name, repo_a1_name)
        assert repo_a1_values['repo_content']['http_proxy_policy'] == 'No HTTP Proxy'
        repo_a2_name = gen_string('alpha')
        session.repository.create(
            product_a.name,
            {
                'name': repo_a2_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
                'repo_content.http_proxy_policy': 'Use specific HTTP Proxy',
                'repo_content.proxy_policy.http_proxy': http_proxy_a.name,
            },
        )
        repo_a2_values = session.repository.read(product_a.name, repo_a2_name)
        expected_policy = f'Use specific HTTP Proxy ({http_proxy_a.name})'
        assert repo_a2_values['repo_content']['http_proxy_policy'] == expected_policy
        repo_b1_name = gen_string('alpha')
        session.repository.create(
            product_b.name,
            {
                'name': repo_b1_name,
                'repo_type': REPO_TYPE['puppet'],
                'repo_content.upstream_url': settings.repos.puppet_0.url,
                'repo_content.http_proxy_policy': 'Global Default',
            },
        )
        repo_b1_values = session.repository.read(product_b.name, repo_b1_name)
        assert 'Global Default' in repo_b1_values['repo_content']['http_proxy_policy']
        repo_b2_name = gen_string('alpha')
        session.repository.create(
            product_b.name,
            {
                'name': repo_b2_name,
                'repo_type': REPO_TYPE['puppet'],
                'repo_content.upstream_url': settings.repos.puppet_0.url,
                'repo_content.http_proxy_policy': 'No HTTP Proxy',
            },
        )
        # Add http_proxy to products
        session.product.search('')
        session.product.manage_http_proxy(
            [product_a.name, product_b.name],
            {
                'http_proxy_policy': 'Use specific HTTP Proxy',
                'proxy_policy.http_proxy': http_proxy_b.name,
            },
        )
        # Verify that Http Proxy is updated for all repos of product_a and product_b.
        proxy_policy = 'Use specific HTTP Proxy ({})'
        repo_a1_values = session.repository.read(product_a.name, repo_a1_name)
        assert repo_a1_values['repo_content']['http_proxy_policy'] == proxy_policy.format(
            http_proxy_b.name
        )
        repo_a2_values = session.repository.read(product_a.name, repo_a2_name)
        assert repo_a2_values['repo_content']['http_proxy_policy'] == proxy_policy.format(
            http_proxy_b.name
        )
        repo_b1_values = session.repository.read(product_b.name, repo_b1_name)
        assert repo_b1_values['repo_content']['http_proxy_policy'] == proxy_policy.format(
            http_proxy_b.name
        )
        repo_b2_values = session.repository.read(product_b.name, repo_b2_name)
        assert repo_b2_values['repo_content']['http_proxy_policy'] == proxy_policy.format(
            http_proxy_b.name
        )
