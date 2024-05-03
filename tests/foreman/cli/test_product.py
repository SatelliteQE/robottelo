"""Test class for Product CLI

:Requirement: Repositories

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

from fauxfactory import gen_alphanumeric, gen_integer, gen_string, gen_url
import pytest

from robottelo.config import settings
from robottelo.constants import FAKE_0_YUM_REPO_PACKAGES_COUNT
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
    valid_labels_list,
)


@pytest.mark.tier1
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_CRUD(module_org, target_sat):
    """Check if product can be created, updated, synchronized and deleted

    :id: 9d7b5ec8-59d0-4371-b5d2-d43145e4e2db

    :expectedresults: Product is created, updated, synchronized and deleted

    :BZ: 1422552

    :CaseImportance: Critical
    """
    desc = list(valid_data_list().values())[0]
    gpg_key = target_sat.cli_factory.make_content_credential({'organization-id': module_org.id})
    name = list(valid_data_list().values())[0]
    label = valid_labels_list()[0]
    sync_plan = target_sat.cli_factory.sync_plan({'organization-id': module_org.id})
    product = target_sat.cli_factory.make_product(
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
    new_gpg_key = target_sat.cli_factory.make_content_credential({'organization-id': module_org.id})
    new_sync_plan = target_sat.cli_factory.sync_plan({'organization-id': module_org.id})
    new_prod_name = gen_string('alpha', 8)
    target_sat.cli.Product.update(
        {
            'description': desc,
            'id': product['id'],
            'gpg-key-id': new_gpg_key['id'],
            'sync-plan-id': new_sync_plan['id'],
            'name': new_prod_name,
        }
    )
    product = target_sat.cli.Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['name'] == new_prod_name
    assert product['description'] == desc
    assert product['gpg']['gpg-key-id'] == new_gpg_key['id']
    assert product['gpg']['gpg-key-id'] != gpg_key['id']
    assert product['sync-plan-id'] == new_sync_plan['id']
    assert product['sync-plan-id'] != sync_plan['id']

    # synchronize
    repo = target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product['id'],
            'url': settings.repos.yum_0.url,
        },
    )
    target_sat.cli.Product.synchronize({'id': product['id'], 'organization-id': module_org.id})
    packages = target_sat.cli.Package.list({'product-id': product['id']})
    repo = target_sat.cli.Repository.info({'id': repo['id']})
    assert int(repo['content-counts']['packages']) == len(packages)
    assert len(packages) == FAKE_0_YUM_REPO_PACKAGES_COUNT

    # delete
    target_sat.cli.Product.remove_sync_plan({'id': product['id']})
    product = target_sat.cli.Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert len(product['sync-plan-id']) == 0
    target_sat.cli.Product.delete({'id': product['id']})
    target_sat.wait_for_tasks(
        search_query="label = Actions::Katello::Product::Destroy"
        f" and resource_id = {product['id']}",
        max_tries=10,
    )
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Product.info({'id': product['id'], 'organization-id': module_org.id})


@pytest.mark.tier2
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(name, module_org, module_target_sat):
    """Check that only valid names can be used

    :id: 2da26ab2-8d79-47ea-b4d2-defcd98a0649

    :parametrized: yes

    :expectedresults: Product is not created

    :CaseImportance: High
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.make_product({'name': name, 'organization-id': module_org.id})


@pytest.mark.tier2
@pytest.mark.parametrize(
    'label', **parametrized([gen_string(e, 15) for e in ('latin1', 'utf8', 'html')])
)
def test_negative_create_with_label(label, module_org, module_target_sat):
    """Check that only valid labels can be used

    :id: 7cf970aa-48dc-425b-ae37-1e15dfab0626

    :parametrized: yes

    :expectedresults: Product is not created

    :CaseImportance: High
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.make_product(
            {
                'label': label,
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            },
        )


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_product_list_with_default_settings(module_org, target_sat):
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
    non_default_org = target_sat.cli_factory.make_org()
    default_product = target_sat.cli_factory.make_product(
        {'name': default_product_name, 'organization-id': org_id}
    )
    non_default_product = target_sat.cli_factory.make_product(
        {'name': non_default_product_name, 'organization-id': non_default_org['id']}
    )
    for product in default_product, non_default_product:
        target_sat.cli_factory.make_repository(
            {
                'organization-id': org_id,
                'product-id': product['id'],
                'url': settings.repos.yum_0.url,
            },
        )

    target_sat.cli.Defaults.add({'param-name': 'organization_id', 'param-value': org_id})
    result = target_sat.cli.Defaults.list(per_page=False)
    assert any([res['value'] == org_id for res in result if res['parameter'] == 'organization_id'])

    try:
        # Verify --organization-id is not required to pass if defaults are set
        result = target_sat.cli.Product.list()
        assert any([res['name'] == default_product_name for res in result])
        result = target_sat.cli.Repository.list()
        assert any([res['product'] == default_product_name for res in result])

        # verify that defaults setting should not affect other entities
        product_list = target_sat.cli.Product.list({'organization-id': non_default_org['id']})
        assert non_default_product_name == product_list[0]['name']
        repository_list = target_sat.cli.Repository.list({'organization-id': non_default_org['id']})
        assert non_default_product_name == repository_list[0]['product']

    finally:
        target_sat.cli.Defaults.delete({'param-name': 'organization_id'})
        result = target_sat.cli.Defaults.list(per_page=False)
        assert not [res for res in result if res['parameter'] == 'organization_id']


@pytest.mark.tier2
@pytest.mark.skip_if_open('BZ:1999541')
def test_positive_product_sync_state(module_org, module_target_sat):
    """hammer product info shows correct sync state.

    :id: 58af6239-85d7-4b8b-bd2d-ab4cd4f29840

    :BZ: 1803207,1999541

    :customerscenario: true

    :steps:
        1. Sync a custom repository that fails.
        2. Run `hammer product info --product-id <id>`.
        3. Successfully sync another repository under the same product.
        4. Run `hammer product info --product-id <id>` again.


    :expectedresults: hammer should show 'Sync Incomplete' in both cases.
    """
    product = module_target_sat.cli_factory.make_product({'organization-id': module_org.id})
    repo_a1 = module_target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product['id'],
            'name': gen_string('alpha'),
            'url': f'{gen_url(scheme="https")}:{gen_integer(min_value=10, max_value=9999)}',
        }
    )

    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Repository.synchronize({'id': repo_a1['id']})

    product_info = module_target_sat.cli.Product.info(
        {'id': product['id'], 'organization-id': module_org.id}
    )
    product_list = module_target_sat.cli.Product.list({'organization-id': module_org.id})
    assert product_info['sync-state-(last)'] in [p.get('sync-state') for p in product_list]

    repo_a2 = module_target_sat.cli_factory.make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product['id'],
            'name': gen_string('alpha'),
            'url': settings.repos.yum_0.url,
        },
    )

    module_target_sat.cli.Repository.synchronize({'id': repo_a2['id']})
    product_info = module_target_sat.cli.Product.info(
        {'id': product['id'], 'organization-id': module_org.id}
    )
    product_list = module_target_sat.cli.Product.list({'organization-id': module_org.id})
    assert product_info['sync-state-(last)'] in [p.get('sync-state') for p in product_list]
