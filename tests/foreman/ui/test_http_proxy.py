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


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_create_update_delete(session, module_org, module_location):
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
                'locations.resources.assigned': [module_location.name],
                'organizations.resources.assigned': [module_org.name],
            }
        )
        assert session.http_proxy.search(http_proxy_name)[0]['Name'] == http_proxy_name
        http_proxy_values = session.http_proxy.read(http_proxy_name)
        assert http_proxy_values['http_proxy']['name'] == http_proxy_name
        assert http_proxy_values['http_proxy']['url'] == http_proxy_url
        assert http_proxy_values['http_proxy']['username'] == username
        assert http_proxy_values['locations']['resources']['assigned'][0] == module_location.name
        assert http_proxy_values['organizations']['resources']['assigned'][0] == module_org.name
        # Update http_proxy with new name
        session.http_proxy.update(http_proxy_name, {'http_proxy.name': updated_proxy_name})
        assert session.http_proxy.search(updated_proxy_name)[0]['Name'] == updated_proxy_name
        # Delete http_proxy
        session.http_proxy.delete(updated_proxy_name)
        assert not entities.HTTPProxy().search(query={'search': f'name={updated_proxy_name}'})


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_assign_http_proxy_to_products_repositories(session, module_org, module_location):
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
        location=[module_location.id],
    ).create()
    http_proxy_b = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.auth_proxy_url,
        username=settings.http_proxy.username,
        password=settings.http_proxy.password,
        organization=[module_org.id],
        location=[module_location.id],
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
                'repo_content.upstream_url': settings.repos.yum_0.url,
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
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_0.url,
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
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
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


@pytest.mark.tier1
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('setting_update', ['content_default_http_proxy'], indirect=True)
def test_set_default_http_proxy(session, module_org, module_location, setting_update):
    """Setting "Default HTTP proxy" to "no global default".

    :id: e93733e1-5c05-4b7f-89e4-253b9ce55a5a

    :Steps:
        1. Navigate to Infrastructure > Http Proxies
        2. Create a Http Proxy
        3. GoTo to Administer > Settings > content tab
        4. Update the "Default HTTP Proxy" with created above.
        5. Update "Default HTTP Proxy" to "no global default".

    :BZ: 1918167, 1913290

    :parametrized: yes

    :expectedresults: Setting "Default HTTP Proxy" to "no global default" result in success.'''

    :CaseImportance: Medium

    :CaseLevel: Acceptance
    """

    property_name = setting_update.name

    http_proxy_a = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.un_auth_proxy_url,
        organization=[module_org.id],
        location=[module_location.id],
    ).create()

    with session:
        session.settings.update(
            f'name = {property_name}', f'{http_proxy_a.name} ({http_proxy_a.url})'
        )
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == f'{http_proxy_a.name} ({http_proxy_a.url})'

        session.settings.update(f'name = {property_name}', "no global default")
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == "Empty"


@pytest.mark.tier1
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('setting_update', ['content_default_http_proxy'], indirect=True)
def test_check_http_proxy_value_repository_details(
    session, function_org, function_location, function_product, setting_update
):

    """Deleted Global Http Proxy is reflected in repository details page".

    :id: 3f64255a-ef6c-4acb-b99b-e5579133b564

    :Steps:
        1. Create Http Proxy (Go to Infrastructure > Http Proxies > New Http Proxy)
        2. GoTo to Administer > Settings > content tab
        3. Update the "Default HTTP Proxy" with created above.
        4. Create repository with Global Default Http Proxy.
        5. Delete the Http Proxy

    :BZ: 1820193

    :parametrized: yes

    :expectedresults:
        1. After deletion of  "Default Http Proxy" its field on settings page should be
            set to no global defult
        2. "HTTP Proxy" field  in repository details page should be set to Global Default (None).

    :CaseImportance: Medium

    :CaseLevel: Acceptance
    """

    property_name = setting_update.name
    repo_name = gen_string('alpha')
    http_proxy_a = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=settings.http_proxy.un_auth_proxy_url,
        organization=[function_org.id],
        location=[function_location.id],
    ).create()

    with session:
        session.organization.select(org_name=function_org.name)
        session.location.select(loc_name=function_location.name)
        session.settings.update(
            f'name = {property_name}', f'{http_proxy_a.name} ({http_proxy_a.url})'
        )
        session.repository.create(
            function_product.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_0.url,
            },
        )
        session.http_proxy.delete(http_proxy_a.name)
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == "Empty"
        session.repository.search(function_product.name, repo_name)[0]['Name']
        repo_values = session.repository.read(function_product.name, repo_name)
        assert repo_values['repo_content']['http_proxy_policy'] == 'Global Default (None)'


@pytest.mark.tier3
@pytest.mark.run_in_one_thread
@pytest.mark.stubbed
def test_http_proxy_containing_special_characters():
    """Test Manifest refresh and redhat repository sync with http proxy special
        characters in password.

    :id: 16082c6a-9320-4a9a-bd6c-5687b099c940

    :customerscenario: true

    :Steps:
        1. Navigate to Infrastructure > Http Proxies
        2. Create HTTP Proxy with special characters in password.
        3. Go To to Administer > Settings > content tab
        4. Fill the details related to HTTP Proxy and click on "Test connection" button.
        5. Update the "Default HTTP Proxy" with created above.
        6. Refresh manifest.
        7. Enable and sync any redhat repositories.

    :BZ: 1844840

    :expectedresults:
        1. "Test connection" button workes as expected.
        2. Manifest refresh, repository enable/disable and repository sync operation
            finished successfully.

    :CaseImportance: High
    """
