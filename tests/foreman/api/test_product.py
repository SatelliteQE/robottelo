"""Unit tests for the ``products`` paths.

An API reference for products can be found on your Satellite:
http://<sat6>/apidoc/v2/products.html

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re

import pytest
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo import manifests
from robottelo import ssh
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import REPO_TYPE
from robottelo.constants import VALID_GPG_KEY_BETA_FILE
from robottelo.constants import VALID_GPG_KEY_FILE
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.helpers import read_data_file


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_create_with_name(request, name, module_org):
    """Create a product providing different valid names

    :id: 3d873b73-6919-4fda-84df-0e26bdf0c1dc

    :parametrized: yes

    :expectedresults: A product is created with expected name.

    :CaseImportance: Critical
    """
    product = entities.Product(name=name, organization=module_org).create()
    assert product.name == name


@pytest.mark.tier1
def test_positive_create_with_label(module_org):
    """Create a product providing label which is different from its name

    :id: 95cf8e05-fd09-422e-bf6f-8b1dde762976

    :expectedresults: A product is created with expected label.

    :CaseImportance: Critical
    """
    label = gen_string('alphanumeric')
    product = entities.Product(label=label, organization=module_org).create()
    assert product.label == label
    assert product.name != label


@pytest.mark.tier1
@pytest.mark.parametrize('description', **parametrized(valid_data_list()))
def test_positive_create_with_description(description, module_org):
    """Create a product providing different descriptions

    :id: f3e2df77-6711-440b-800a-9cebbbec36c5

    :parametrized: yes

    :expectedresults: A product is created with expected description.

    :CaseImportance: Critical
    """
    product = entities.Product(description=description, organization=module_org).create()
    assert product.description == description


@pytest.mark.tier2
def test_positive_create_with_gpg(module_org):
    """Create a product and provide a GPG key.

    :id: 57331c1f-15dd-4c9f-b8fc-3010847b2975

    :expectedresults: A product is created with the specified GPG key.

    :CaseLevel: Integration
    """
    gpg_key = entities.GPGKey(
        content=read_data_file(VALID_GPG_KEY_FILE), organization=module_org
    ).create()
    product = entities.Product(gpg_key=gpg_key, organization=module_org).create()
    assert product.gpg_key.id == gpg_key.id


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(name, module_org):
    """Create a product providing invalid names only

    :id: 76531f53-09ff-4ee9-89b9-09a697526fb1

    :parametrized: yes

    :expectedresults: A product is not created

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        entities.Product(name=name, organization=module_org).create()


@pytest.mark.tier1
def test_negative_create_with_same_name(module_org):
    """Create a product providing a name of already existent entity

    :id: 039269c5-607a-4b70-91dd-b8fed8e50cc6

    :expectedresults: A product is not created

    :CaseImportance: Critical
    """
    name = gen_string('alphanumeric')
    entities.Product(name=name, organization=module_org).create()
    with pytest.raises(HTTPError):
        entities.Product(name=name, organization=module_org).create()


@pytest.mark.tier1
def test_negative_create_with_label(module_org):
    """Create a product providing invalid label

    :id: 30b1a737-07f1-4786-b68a-734e57c33a62

    :expectedresults: A product is not created

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        entities.Product(label=gen_string('utf8'), organization=module_org).create()


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_update_name(name, module_org):
    """Update product name to another valid name.

    :id: 1a9f6e0d-43fb-42e2-9dbd-e880f03b0297

    :parametrized: yes

    :expectedresults: Product name can be updated.

    :CaseImportance: Critical
    """
    product = entities.Product(organization=module_org).create()
    product.name = name
    product = product.update(['name'])
    assert product.name == name


@pytest.mark.tier1
@pytest.mark.parametrize('description', **parametrized(valid_data_list()))
def test_positive_update_description(description, module_org):
    """Update product description to another valid one.

    :id: c960c326-2e9f-4ee7-bdec-35a705305067

    :parametrized: yes

    :expectedresults: Product description can be updated.

    :CaseImportance: Critical
    """
    product = entities.Product(organization=module_org).create()
    product.description = description
    product = product.update(['description'])
    assert product.description == description


@pytest.mark.tier1
def test_positive_update_name_to_original(module_org):
    """Rename Product back to original name

    :id: 3075f17f-4475-4b64-9fbd-1e41ced9142d

    :expectedresults: Product Renamed to original

    :CaseImportance: Critical
    """
    product = entities.Product(organization=module_org).create()
    old_name = product.name

    # Update product name
    new_name = gen_string('alpha')
    product.name = new_name
    product = product.update(['name'])
    assert product.name == new_name

    # Rename product to old name and verify
    product.name = old_name
    product = product.update(['name'])
    assert product.name == old_name


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_update_gpg(module_org):
    """Create a product and update its GPGKey

    :id: 3b08f155-a0d6-4987-b281-dc02e8d5a03e

    :expectedresults: The updated product points to a new GPG key.

    :CaseLevel: Integration
    """
    # Create a product and make it point to a GPG key.
    gpg_key_1 = entities.GPGKey(
        content=read_data_file(VALID_GPG_KEY_FILE), organization=module_org
    ).create()
    product = entities.Product(gpg_key=gpg_key_1, organization=module_org).create()

    # Update the product and make it point to a new GPG key.
    gpg_key_2 = entities.GPGKey(
        content=read_data_file(VALID_GPG_KEY_BETA_FILE), organization=module_org
    ).create()
    product.gpg_key = gpg_key_2
    product = product.update()
    assert product.gpg_key.id == gpg_key_2.id


@pytest.mark.skip_if_open("BZ:1310422")
@pytest.mark.tier2
def test_positive_update_organization(module_org):
    """Create a product and update its organization

    :id: b298957a-2cdb-4f17-a934-098612f3b659

    :expectedresults: The updated product points to a new organization

    :CaseLevel: Integration

    :BZ: 1310422
    """
    product = entities.Product(organization=module_org).create()
    # Update the product and make it point to a new organization.
    new_org = entities.Organization().create()
    product.organization = new_org
    product = product.update()
    assert product.organization.id == new_org.id


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_update_name(name, module_org):
    """Attempt to update product name to invalid one

    :id: 3eb61fa8-3524-4872-8f1b-4e88004f66f5

    :parametrized: yes

    :expectedresults: Product is not updated

    :CaseImportance: Critical
    """
    product = entities.Product(organization=module_org).create()
    with pytest.raises(HTTPError):
        entities.Product(id=product.id, name=name).update(['name'])


@pytest.mark.tier1
def test_negative_update_label(module_org):
    """Attempt to update product label to another one.

    :id: 065cd673-8d10-46c7-800c-b731b06a5359

    :expectedresults: Product is not updated and error is raised

    :CaseImportance: Critical
    """
    product = entities.Product(organization=module_org).create()
    product.label = gen_string('alpha')
    with pytest.raises(HTTPError):
        product.update(['label'])


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_delete(name, module_org):
    """Create product and then delete it.

    :id: 30df95f5-0a4e-41ee-a99f-b418c5c5f2f3

    :parametrized: yes

    :expectedresults: Product is successfully deleted.

    :CaseImportance: Critical
    """
    product = entities.Product(name=name, organization=module_org).create()
    product.delete()
    with pytest.raises(HTTPError):
        product.read()


@pytest.mark.tier1
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync(module_org):
    """Sync product (repository within a product)

    :id: 860e00a1-c370-4bd0-8987-449338071d56

    :expectedresults: Repository within a product is successfully synced.

    :CaseImportance: Critical
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(
        product=product, content_type='yum', url=settings.repos.yum_1.url
    ).create()
    assert repo.read().content_counts['rpm'] == 0
    product.sync()
    assert repo.read().content_counts['rpm'] >= 1


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync_several_repos(module_org):
    """Sync product (all repositories within a product)

    :id: 07918442-b72f-4db5-96b6-975564f3663a

    :expectedresults: All repositories within a product are successfully
        synced.

    :CaseLevel: Integration

    :BZ: 1389543
    """
    product = entities.Product(organization=module_org).create()
    rpm_repo = entities.Repository(
        product=product, content_type='yum', url=settings.repos.yum_1.url
    ).create()
    docker_repo = entities.Repository(
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
def test_positive_filter_product_list():
    """Filter products based on param 'custom/redhat_only'

    :id: e61fb63a-4552-4915-b13d-23ab80138249

    :expectedresults: Able to list the products based on defined filter.

    :CaseLevel: Integration

    :BZ: 1667129
    """
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    # Manifest upload to create RH Product
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)

    custom_products = entities.Product(organization=org).search(query={'custom': True})
    rh_products = entities.Product(organization=org).search(
        query={'redhat_only': True, 'per_page': 1000}
    )

    assert len(custom_products) == 1
    assert product.name == custom_products[0].name
    assert 'Red Hat Beta' not in (prod.name for prod in custom_products)

    assert len(rh_products) > 1
    assert 'Red Hat Beta' in (prod.name for prod in rh_products)
    assert product.name not in (prod.name for prod in rh_products)


@pytest.mark.tier2
def test_positive_assign_http_proxy_to_products():
    """Assign http_proxy to Products and check whether http-proxy is
     used during sync.

    :id: c9d23aa1-3325-4abd-a1a6-d5e75c12b08a

    :expectedresults: HTTP Proxy is assigned to all repos present
        in Products and sync operation uses assigned http-proxy.

    :Assignee: jpathan

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    # create HTTP proxies
    http_proxy_a = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=f"{gen_url(scheme='https')}:{gen_integer(min_value=10, max_value=9999)}",
        organization=[org],
    ).create()

    http_proxy_b = entities.HTTPProxy(
        name=gen_string('alpha', 15),
        url=f"{gen_url(scheme='https')}:{gen_integer(min_value=10, max_value=9999)}",
        organization=[org],
    ).create()
    proxy_fqdn = re.split(r'[:]', http_proxy_b.url)[1].strip("//")

    # Create products and repositories
    product_a = entities.Product(organization=org).create()
    product_b = entities.Product(organization=org).create()
    repo_a1 = entities.Repository(product=product_a, http_proxy_policy='none').create()
    repo_a2 = entities.Repository(
        product=product_a,
        http_proxy_policy='use_selected_http_proxy',
        http_proxy_id=http_proxy_a.id,
    ).create()
    repo_b1 = entities.Repository(product=product_b, http_proxy_policy='none').create()
    repo_b2 = entities.Repository(
        product=product_b, http_proxy_policy='global_default_http_proxy'
    ).create()
    # Add http_proxy to products
    entities.ProductBulkAction().http_proxy(
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

    product_a.sync({'async': True})

    # Verify that proxy FQDN appears in log during sync.
    result = ssh.command(f'grep -F {proxy_fqdn} /var/log/messages')
    assert result.return_code == 0
