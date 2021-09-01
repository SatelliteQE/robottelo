"""Test class for Product CLI

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string

from robottelo.api.utils import wait_for_tasks
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.defaults import Defaults
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_gpg_key
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_sync_plan
from robottelo.cli.http_proxy import HttpProxy
from robottelo.cli.package import Package
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.config import settings
from robottelo.constants import FAKE_0_YUM_REPO_PACKAGES_COUNT
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_labels_list


@pytest.mark.tier1
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_CRUD(module_org):
    """Check if product can be created, updated, synchronized and deleted

    :id: 9d7b5ec8-59d0-4371-b5d2-d43145e4e2db

    :expectedresults: Product is created, updated, synchronized and deleted

    :BZ: 1422552

    :CaseImportance: Critical
    """
    desc = list(valid_data_list().values())[0]
    gpg_key = make_gpg_key({'organization-id': module_org.id})
    name = list(valid_data_list().values())[0]
    label = valid_labels_list()[0]
    sync_plan = make_sync_plan({'organization-id': module_org.id})
    product = make_product(
        {
            'description': desc,
            'gpg-key-id': gpg_key['id'],
            'label': label,
            'name': name,
            'organization-id': module_org.id,
            'sync-plan-id': sync_plan['id'],
        },
    )
    assert product['name'] == name
    assert len(product['label']) > 0
    assert product['label'] == label
    assert product['description'] == desc
    assert product['gpg']['gpg-key-id'] == gpg_key['id']
    assert product['sync-plan-id'] == sync_plan['id']

    # update
    desc = list(valid_data_list().values())[0]
    new_gpg_key = make_gpg_key({'organization-id': module_org.id})
    new_sync_plan = make_sync_plan({'organization-id': module_org.id})
    new_prod_name = gen_string('alpha', 8)
    Product.update(
        {
            'description': desc,
            'id': product['id'],
            'gpg-key-id': new_gpg_key['id'],
            'sync-plan-id': new_sync_plan['id'],
            'name': new_prod_name,
        }
    )
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['name'] == new_prod_name
    assert product['description'] == desc
    assert product['gpg']['gpg-key-id'] == new_gpg_key['id']
    assert product['gpg']['gpg-key-id'] != gpg_key['id']
    assert product['sync-plan-id'] == new_sync_plan['id']
    assert product['sync-plan-id'] != sync_plan['id']

    # synchronize
    repo = make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product['id'],
            'url': settings.repos.yum_0.url,
        },
    )
    Product.synchronize({'id': product['id'], 'organization-id': module_org.id})
    packages = Package.list({'product-id': product['id']})
    repo = Repository.info({'id': repo['id']})
    assert int(repo['content-counts']['packages']) == len(packages)
    assert len(packages) == FAKE_0_YUM_REPO_PACKAGES_COUNT

    # delete
    Product.remove_sync_plan({'id': product['id']})
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert len(product['sync-plan-id']) == 0
    Product.delete({'id': product['id']})
    wait_for_tasks(
        search_query="label = Actions::Katello::Product::Destroy"
        f" and resource_id = {product['id']}",
        max_tries=10,
    )
    with pytest.raises(CLIReturnCodeError):
        Product.info({'id': product['id'], 'organization-id': module_org.id})


@pytest.mark.tier2
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(name, module_org):
    """Check that only valid names can be used

    :id: 2da26ab2-8d79-47ea-b4d2-defcd98a0649

    :parametrized: yes

    :expectedresults: Product is not created

    :CaseImportance: High
    """
    with pytest.raises(CLIFactoryError):
        make_product({'name': name, 'organization-id': module_org.id})


@pytest.mark.tier2
@pytest.mark.parametrize(
    'label', **parametrized([gen_string(e, 15) for e in ('latin1', 'utf8', 'html')])
)
def test_negative_create_with_label(label, module_org):
    """Check that only valid labels can be used

    :id: 7cf970aa-48dc-425b-ae37-1e15dfab0626

    :parametrized: yes

    :expectedresults: Product is not created

    :CaseImportance: High
    """
    with pytest.raises(CLIFactoryError):
        make_product(
            {
                'label': label,
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            },
        )


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_product_list_with_default_settings(module_org, default_sat):
    """Listing product of an organization apart from default organization using hammer
     does not return output if a defaults settings are applied on org.

    :id: d5c5edac-b19c-4277-92fe-28d9b9fa43ef

    :BZ: 1745575

    :customerscenario: true

    :expectedresults: product/reporsitory list should work as expected.

    """
    org_id = str(module_org.id)
    default_product_name = gen_string('alpha')
    non_default_product_name = gen_string('alpha')
    non_default_org = make_org()
    default_product = make_product({'name': default_product_name, 'organization-id': org_id})
    non_default_product = make_product(
        {'name': non_default_product_name, 'organization-id': non_default_org['id']}
    )
    for product in default_product, non_default_product:
        make_repository(
            {
                'organization-id': org_id,
                'product-id': product['id'],
                'url': settings.repos.yum_0.url,
            },
        )

    Defaults.add({'param-name': 'organization_id', 'param-value': org_id})
    result = default_sat.cli.Defaults.list(per_page=False)
    assert any([res['value'] == org_id for res in result if res['parameter'] == 'organization_id'])

    try:
        # Verify --organization-id is not required to pass if defaults are set
        result = default_sat.cli.Product.list()
        assert any([res['name'] == default_product_name for res in result])
        result = default_sat.cli.Repository.list()
        assert any([res['product'] == default_product_name for res in result])

        # verify that defaults setting should not affect other entities
        product_list = Product.list({'organization-id': non_default_org['id']})
        assert non_default_product_name == product_list[0]['name']
        repository_list = Repository.list({'organization-id': non_default_org['id']})
        assert non_default_product_name == repository_list[0]['product']

    finally:
        Defaults.delete({'param-name': 'organization_id'})
        result = default_sat.cli.Defaults.list(per_page=False)
        assert not [res for res in result if res['parameter'] == 'organization_id']


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_assign_http_proxy_to_products(module_org):
    """Assign http_proxy to Products and perform product sync.

    :id: 6af7b2b8-15d5-4d9f-9f87-e76b404a966f

    :expectedresults: HTTP Proxy is assigned to all repos present
        in Products and sync operation performed successfully.

    :Assignee: jpathan

    :CaseImportance: Critical
    """
    # create HTTP proxies
    http_proxy_a = HttpProxy.create(
        {
            'name': gen_string('alpha', 15),
            'url': settings.http_proxy.un_auth_proxy_url,
            'organization-id': module_org.id,
        },
    )
    http_proxy_b = HttpProxy.create(
        {
            'name': gen_string('alpha', 15),
            'url': settings.http_proxy.auth_proxy_url,
            'username': settings.http_proxy.username,
            'password': settings.http_proxy.password,
            'organization-id': module_org.id,
        },
    )
    # Create products and repositories
    product_a = make_product({'organization-id': module_org.id})
    product_b = make_product({'organization-id': module_org.id})
    repo_a1 = make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_a['id'],
            'url': settings.repos.yum_0.url,
            'http-proxy-policy': 'none',
        },
    )
    repo_a2 = make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_a['id'],
            'url': settings.repos.yum_0.url,
            'http-proxy-policy': 'use_selected_http_proxy',
            'http-proxy-id': http_proxy_a['id'],
        },
    )
    repo_b1 = make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_b['id'],
            'url': settings.repos.yum_0.url,
            'http-proxy-policy': 'none',
        },
    )
    repo_b2 = make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product_b['id'],
            'url': settings.repos.yum_0.url,
        },
    )
    # Add http_proxy to products
    Product.update_proxy(
        {
            'ids': f"{product_a['id']},{product_b['id']}",
            'http-proxy-policy': 'use_selected_http_proxy',
            'http-proxy-id': http_proxy_b['id'],
        }
    )
    # Perform sync and verify packages count
    Product.synchronize({'id': product_a['id'], 'organization-id': module_org.id})
    Product.synchronize({'id': product_b['id'], 'organization-id': module_org.id})

    for repo in repo_a1, repo_a2, repo_b1, repo_b2:
        r = Repository.info({'id': repo['id']})
        assert r['http-proxy']['http-proxy-policy'] == 'use_selected_http_proxy'
        assert r['http-proxy']['id'] == http_proxy_b['id']
        assert int(r['content-counts']['packages']) == FAKE_0_YUM_REPO_PACKAGES_COUNT

    Product.update_proxy(
        {'ids': f"{product_a['id']},{product_b['id']}", 'http-proxy-policy': 'none'}
    )

    for repo in repo_a1, repo_a2, repo_b1, repo_b2:
        r = Repository.info({'id': repo['id']})
        assert r['http-proxy']['http-proxy-policy'] == 'none'


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_product_sync_state():
    """hammer product info shows correct sync state.

    :id: 58af6239-85d7-4b8b-bd2d-ab4cd4f29840

    :BZ: 1803207

    :customerscenario: true

    :Steps:
        1. Sync a custom repository that fails.
        2. Run `hammer product info --product-id <id>`.
        3. Successfully sync another repository under the same product.
        4. Run `hammer product info --product-id <id>` again.

    :expectedresults: hammer should show 'Sync Incomplete' in both cases.
    """
    pass
