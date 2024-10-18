"""Unit tests for the ``products`` paths.

An API reference for products can be found on your Satellite:
http://<sat6>/apidoc/v2/products.html

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
    REPO_TYPE,
    DataFile,
)
from robottelo.utils import datafactory
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
)


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(name, module_org, module_target_sat):
    """Create a product providing invalid names only

    :id: 76531f53-09ff-4ee9-89b9-09a697526fb1

    :parametrized: yes

    :expectedresults: A product is not created

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        module_target_sat.api.Product(name=name, organization=module_org).create()


@pytest.mark.tier1
def test_negative_create_with_same_name(module_org, module_target_sat):
    """Create a product providing a name of already existent entity

    :id: 039269c5-607a-4b70-91dd-b8fed8e50cc6

    :expectedresults: A product is not created

    :CaseImportance: Critical
    """
    name = gen_string('alphanumeric')
    module_target_sat.api.Product(name=name, organization=module_org).create()
    with pytest.raises(HTTPError):
        module_target_sat.api.Product(name=name, organization=module_org).create()


@pytest.mark.tier1
def test_negative_create_with_label(module_org, module_target_sat):
    """Create a product providing invalid label

    :id: 30b1a737-07f1-4786-b68a-734e57c33a62

    :expectedresults: A product is not created

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        module_target_sat.api.Product(label=gen_string('utf8'), organization=module_org).create()


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_create_product_and_update_gpg(module_org, module_target_sat):
    """Create a product with GPG key and update it with new GPGKey

    :id: 90bfd250-4446-4e7b-a85e-bafd69f527e5

    :expectedresults: A product is created with GPG key and updated product will point to a new GPG key.
    """
    # Create a product and make it point to a GPG key.
    gpg_key_1 = module_target_sat.api.GPGKey(
        content=DataFile.VALID_GPG_KEY_FILE.read_text(),
        organization=module_org,
    ).create()
    product = module_target_sat.api.Product(gpg_key=gpg_key_1, organization=module_org).create()
    assert product.gpg_key.id == gpg_key_1.id

    # Update the product and make it point to a new GPG key.
    gpg_key_2 = module_target_sat.api.GPGKey(
        content=DataFile.VALID_GPG_KEY_BETA_FILE.read_text(),
        organization=module_org,
    ).create()
    product.gpg_key = gpg_key_2
    product = product.update()
    assert product.gpg_key.id == gpg_key_2.id


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_update_name(name, module_org, module_target_sat):
    """Attempt to update product name to invalid one

    :id: 3eb61fa8-3524-4872-8f1b-4e88004f66f5

    :parametrized: yes

    :expectedresults: Product is not updated

    :CaseImportance: Critical
    """
    product = module_target_sat.api.Product(organization=module_org).create()
    with pytest.raises(HTTPError):
        module_target_sat.api.Product(id=product.id, name=name).update(['name'])


@pytest.mark.tier1
def test_negative_update_label(module_org, module_target_sat):
    """Attempt to update product label to another one.

    :id: 065cd673-8d10-46c7-800c-b731b06a5359

    :expectedresults: Product is not updated and error is raised

    :CaseImportance: Critical
    """
    product = module_target_sat.api.Product(organization=module_org).create()
    product.label = gen_string('alpha')
    with pytest.raises(HTTPError):
        product.update(['label'])


@pytest.mark.tier1
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync(module_org, module_target_sat):
    """Sync product (repository within a product)

    :id: 860e00a1-c370-4bd0-8987-449338071d56

    :expectedresults: Repository within a product is successfully synced.

    :CaseImportance: Critical
    """
    product = module_target_sat.api.Product(organization=module_org).create()
    repo = module_target_sat.api.Repository(
        product=product, content_type='yum', url=settings.repos.yum_1.url
    ).create()
    assert repo.read().content_counts['rpm'] == 0
    product.sync()
    assert repo.read().content_counts['rpm'] >= 1


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync_several_repos(module_org, module_target_sat):
    """Sync product (all repositories within a product)

    :id: 07918442-b72f-4db5-96b6-975564f3663a

    :expectedresults: All repositories within a product are successfully
        synced.

    :BZ: 1389543
    """
    product = module_target_sat.api.Product(organization=module_org).create()
    rpm_repo = module_target_sat.api.Repository(
        product=product, content_type='yum', url=settings.repos.yum_1.url
    ).create()
    docker_repo = module_target_sat.api.Repository(
        content_type=REPO_TYPE['docker'],
        docker_upstream_name=CONTAINER_UPSTREAM_NAME,
        product=product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()
    assert rpm_repo.read().content_counts['rpm'] == 0
    assert docker_repo.read().content_counts['docker_tag'] == 0

    product.sync()
    assert rpm_repo.read().content_counts['rpm'] >= 1
    assert docker_repo.read().content_counts['docker_tag'] >= 1


@pytest.mark.tier2
def test_positive_filter_product_list(module_sca_manifest_org, module_target_sat):
    """Filter products based on param 'custom/redhat_only'

    :id: e61fb63a-4552-4915-b13d-23ab80138249

    :expectedresults: Able to list the products based on defined filter.

    :BZ: 1667129
    """
    org = module_sca_manifest_org
    product = module_target_sat.api.Product(organization=org).create()
    custom_products = module_target_sat.api.Product(organization=org).search(query={'custom': True})
    rh_products = module_target_sat.api.Product(organization=org).search(
        query={'redhat_only': True, 'per_page': 1000}
    )

    assert product.name in (custom_prod.name for custom_prod in custom_products)
    assert 'Red Hat Beta' not in (prod.name for prod in custom_products)

    assert len(rh_products) > 1
    assert 'Red Hat Beta' in (prod.name for prod in rh_products)
    assert product.name not in (prod.name for prod in rh_products)


@pytest.mark.e2e
@pytest.mark.tier1
def test_positive_product_end_to_end(module_target_sat, module_org):
    """Product scenario with all possible crud operations

    :id: 41abdd24-9c2a-47b8-b595-1b56c05527c9

    :expectedresults: A product crud operation executed successfully

    :CaseImportance: Critical
    """

    # Create product with name, label, description
    original_name = gen_string('alphanumeric')
    label = gen_string('alphanumeric')
    description = gen_string('alphanumeric')
    product = module_target_sat.api.Product(
        name=original_name, label=label, organization=module_org, description=description
    ).create()
    assert product.name == original_name
    assert product.label == label
    assert product.description == description

    # Update product name, description
    new_name_list = list(datafactory.valid_data_list().values())
    for new_name in new_name_list:
        product.name = new_name
        product = product.update(['name'])
        assert product.name == new_name
    # Rename product to original name and verify
    product.name = original_name
    product = product.update(['name'])
    assert product.name == original_name

    new_desc_list = list(datafactory.valid_data_list().values())
    for new_desc in new_desc_list:
        product.description = new_desc
        product = product.update(['description'])
        assert product.description == new_desc

    # Delete product
    product.delete()
    with pytest.raises(HTTPError):
        product.read()
