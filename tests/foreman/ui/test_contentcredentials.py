"""Test class for Content Credentials UI

:Requirement: ContentCredentials

:CaseAutomation: Automated

:CaseComponent: ContentCredentials

:team: Artemis

:CaseImportance: High

"""

import pytest

from robottelo.config import settings
from robottelo.constants import CONTENT_CREDENTIALS_TYPES, DataFile
from robottelo.utils.datafactory import gen_string

empty_message = 'This content credential is not currently being used by any products.'


@pytest.fixture(scope='module', autouse=True)
def enable_lab_features(module_target_sat):
    """Enable lab features setting for the duration of the module.

    The Content Credentials React page lives under /labs until fully promoted.
    TODO: Remove this fixture once the page is moved out of /labs.
    """
    original = module_target_sat.update_setting('lab_features', True)
    yield
    module_target_sat.update_setting('lab_features', original)


@pytest.fixture(scope='module')
def gpg_content():
    return DataFile.VALID_GPG_KEY_FILE.read_text()


@pytest.fixture(scope='module')
def gpg_path():
    return DataFile.VALID_GPG_KEY_FILE


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.stubbed
def test_positive_end_to_end(session, target_sat, module_org, gpg_content):
    """Perform end to end testing for gpg key component

    :id: d1a8cc1b-a072-465b-887d-5bca0acd21c3

    :expectedresults: All expected CRUD actions finished successfully

    :CaseAutomation: NotAutomated

    Note: create() is not yet implemented in the React UI.
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        # Create new gpg key with valid content
        session.contentcredential.create(
            {
                'name': name,
                'content_type': CONTENT_CREDENTIALS_TYPES['gpg'],
                'content': gpg_content,
            }
        )
        assert session.contentcredential.search(name)[0]['Name'] == name
        gpg_key = target_sat.api.ContentCredential(organization=module_org).search(
            query={'search': f'name="{name}"'}
        )[0]
        product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
        repo = target_sat.api.Repository(product=product).create()
        values = session.contentcredential.read(name)
        assert values['details']['name'] == name
        assert values['details']['content_type'] == CONTENT_CREDENTIALS_TYPES['gpg']
        # transform string for comparison
        transformed_string = gpg_content.replace('\n', ' ')
        transformed_string = transformed_string.replace('  ', ' ')
        transformed_string = transformed_string.rstrip()
        assert values['details']['content'] == transformed_string
        assert values['details']['products'] == '1'
        assert values['details']['repos'] == '1'
        assert values['products']['table'][0]['Name'] == product.name
        assert values['repositories']['table'][0]['Name'] == repo.name
        # Update gpg key with new name
        session.contentcredential.update(name, {'details.name': new_name})
        assert session.contentcredential.search(new_name)[0]['Name'] == new_name
        # Delete repo and product dependent on the gpg key
        repo.delete()
        product.delete()
        # Delete gpg key
        session.contentcredential.delete(new_name)
        assert session.contentcredential.search(new_name)[0]['Name'] != new_name


@pytest.mark.stubbed
def test_positive_search_scoped(session, target_sat, gpg_content, module_org):
    """Search for gpgkey by organization id parameter

    :id: e1e04f68-5d4f-43f6-a9c1-b9f566fcbc92

    :customerscenario: true

    :expectedresults: correct gpg key is found

    :BZ: 1259374

    :CaseAutomation: NotAutomated

    Note: create() is not yet implemented in the React UI.
    """
    name = gen_string('alpha')
    with session:
        session.organization.select(module_org.name)
        session.contentcredential.create(
            {
                'name': name,
                'content_type': CONTENT_CREDENTIALS_TYPES['gpg'],
                'content': gpg_content,
            }
        )
        assert (
            session.contentcredential.search(f'organization_id = {module_org.id}')[0]['Name']
            == name
        )


def test_positive_add_empty_product(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate
    it with empty (no repos) custom product

    :id: e18ae9f5-43d9-4049-92ca-1eafaca05096

    :expectedresults: gpg key is associated with product
    """
    prod_name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(content=gpg_content, organization=module_org).create()
    with session:
        session.product.create({'name': prod_name, 'gpg_key': gpg_key.name})
        values = session.contentcredential.read(gpg_key.name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == prod_name
        assert values['products']['table'][0]['Used as'] == CONTENT_CREDENTIALS_TYPES['gpg']


@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_product_with_repo(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has one repository

    :id: 7514b33a-da75-43bd-a84b-5a805c84511d

    :expectedresults: gpg key is associated with product as well as with
        the repository
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product
    product = target_sat.api.Product(organization=module_org).create()
    # Creates new repository without GPGKey
    repo = target_sat.api.Repository(url=settings.repos.yum_1.url, product=product).create()
    with session:
        values = session.contentcredential.read(name)
        assert values['products']['empty_state'] == empty_message
        # Associate gpg key with a product
        session.product.update(product.name, {'details.gpg_key': gpg_key.name})
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name
        assert values['repositories']['table'][0]['Product'] == product.name
        assert values['repositories']['table'][0]['Type'] == 'yum'
        assert values['repositories']['table'][0]['Used as'] == CONTENT_CREDENTIALS_TYPES['gpg']


@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_product_with_repos(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has more than one repository

    :id: 0edffad7-0ab4-4bef-b16b-f6c8de55b0dc

    :expectedresults: gpg key is properly associated with repositories
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product and associate GPGKey with it
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    # Creates new repository_1 without GPGKey
    repo1 = target_sat.api.Repository(product=product, url=settings.repos.yum_1.url).create()
    # Creates new repository_2 without GPGKey
    repo2 = target_sat.api.Repository(product=product, url=settings.repos.yum_2.url).create()
    with session:
        values = session.contentcredential.read(name)
        assert len(values['repositories']['table']) == 2
        assert {repo1.name, repo2.name} == {
            repo['Name'] for repo in values['repositories']['table']
        }


def test_positive_add_repo_from_product_with_repo(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has one repository

    :id: 5d78890f-4130-4dc3-9cfe-48999149422f

    :expectedresults: gpg key is associated with the repository but not
        with the product
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product
    product = target_sat.api.Product(organization=module_org).create()
    # Creates new repository
    repo = target_sat.api.Repository(url=settings.repos.yum_1.url, product=product).create()
    with session:
        values = session.contentcredential.read(name)
        assert values['products']['empty_state'] == empty_message
        # Associate gpg key with repository
        session.repository.update(product.name, repo.name, {'repo_content.gpg_key': gpg_key.name})
        values = session.contentcredential.read(name)
        assert values['products']['empty_state'] == empty_message
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name
        assert values['repositories']['table'][0]['Product'] == product.name


@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_repo_from_product_with_repos(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has more than one repository

    :id: 1fb38e01-4c04-4609-842d-069f96157317

    :expectedresults: gpg key is associated with one of the repositories
        but not with the product
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product without selecting GPGkey
    product = target_sat.api.Product(organization=module_org).create()
    # Creates new repository with GPGKey
    repo1 = target_sat.api.Repository(
        url=settings.repos.yum_1.url, product=product, gpg_key=gpg_key
    ).create()
    # Creates new repository without GPGKey
    target_sat.api.Repository(url=settings.repos.yum_2.url, product=product).create()
    with session:
        values = session.contentcredential.read(name)
        assert values['products']['empty_state'] == empty_message
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo1.name


@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_product_and_search(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key
    then associate it with custom product that has one repository
    After search and select product through gpg key interface

    :id: 0bef0c1b-4811-489e-89e9-609d57fc45ee

    :customerscenario: true

    :expectedresults: Associated product can be found and selected through
        gpg key 'Product' tab

    :BZ: 1411800
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product and associate GPGKey with it
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    # Creates new repository without GPGKey
    repo = target_sat.api.Repository(url=settings.repos.yum_1.url, product=product).create()
    with session:
        values = session.contentcredential.read(gpg_key.name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name
        product_values = session.contentcredential.get_product_details(gpg_key.name, product.name)
        assert product_values['details']['name'] == product.name
        assert product_values['details']['gpg_key'] == gpg_key.name
        assert product_values['details']['repos_count'] == '1'


@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.usefixtures('allow_repo_discovery')
@pytest.mark.stubbed
def test_positive_update_key_for_product_using_repo_discovery(session, gpg_path):
    """Create gpg key with valid name and valid content then associate it with custom product
    using Repo discovery method then update the key

    :id: 49279be8-cbea-477e-a1ff-c07171e7084e

    :expectedresults: gpg key is associated with product as well as with
        repository before/after update

    :BZ: 1210180, 1461804

    :CaseAutomation: NotAutomated

    Note: create() is not yet implemented in the React UI.
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    product_name = gen_string('alpha')
    repo_name = 'fakerepo01'
    with session:
        session.contentcredential.create(
            {
                'name': name,
                'content_type': CONTENT_CREDENTIALS_TYPES['gpg'],
                'upload_file': gpg_path,
            }
        )
        assert session.contentcredential.search(name)[0]['Name'] == name
        session.product.discover_repo(
            {
                'repo_type': 'Yum Repositories',
                'url': settings.repos.repo_discovery.url,
                'discovered_repos.repos': repo_name,
                'create_repo.product_type': 'New Product',
                'create_repo.product_content.product_name': product_name,
                'create_repo.product_content.gpg_key': name,
            }
        )
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product_name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'].split(' ')[-1] == repo_name
        product_values = session.product.read(product_name)
        assert product_values['details']['gpg_key'] == name
        session.contentcredential.update(name, {'details.name': new_name})
        values = session.contentcredential.read(new_name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product_name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'].split(' ')[-1] == repo_name
        product_values = session.product.read(product_name)
        assert product_values['details']['gpg_key'] == new_name


def test_positive_update_key_for_empty_product(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with empty (no repos) custom product then update the key

    :id: 519817c3-9b67-4859-8069-95987ebf9453

    :expectedresults: gpg key is associated with product before/after
        update
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product and associate GPGKey with it
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    with session:
        values = session.contentcredential.read(name)
        # Assert that GPGKey is associated with product
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        session.contentcredential.update(name, {'details.name': new_name})
        values = session.contentcredential.read(new_name)
        # Assert that GPGKey is still associated with product
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name


@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_update_key_for_product_with_repo(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has one repository then update the key

    :id: 02cb0601-6aa2-4589-b61e-3d3785a7e100

    :expectedresults: gpg key is associated with product as well as with
        repository after update
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product and associate GPGKey with it
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    # Creates new repository without GPGKey
    repo = target_sat.api.Repository(product=product, url=settings.repos.yum_1.url).create()
    with session:
        session.contentcredential.update(name, {'details.name': new_name})
        values = session.contentcredential.read(new_name)
        # Assert that GPGKey is still associated with product
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name


@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_update_key_for_product_with_repos(session, target_sat, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has more than one repository then update the
    key

    :id: 3ca4d9ff-8032-4c2a-aed9-00ac2d1352d1

    :expectedresults: gpg key is associated with product as well as with
        repositories after update
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product and associate GPGKey with it
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    # Creates new repository_1 without GPGKey
    repo1 = target_sat.api.Repository(product=product, url=settings.repos.yum_1.url).create()
    # Creates new repository_2 without GPGKey
    repo2 = target_sat.api.Repository(product=product, url=settings.repos.yum_2.url).create()
    with session:
        session.contentcredential.update(name, {'details.name': new_name})
        values = session.contentcredential.read(new_name)
        assert len(values['repositories']['table']) == 2
        assert {repo1.name, repo2.name} == {
            repo['Name'] for repo in values['repositories']['table']
        }


@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_update_key_for_repo_from_product_with_repo(
    session, target_sat, module_org, gpg_content
):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has one repository then update
    the key

    :id: 9827306e-76d7-4aef-8074-e97fc39d3bbb

    :expectedresults: gpg key is associated with repository after update
        but not with product.
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product without selecting GPGkey
    product = target_sat.api.Product(organization=module_org).create()
    # Creates new repository with GPGKey
    repo = target_sat.api.Repository(
        gpg_key=gpg_key, product=product, url=settings.repos.yum_1.url
    ).create()
    with session:
        session.contentcredential.update(name, {'details.name': new_name})
        values = session.contentcredential.read(new_name)
        # Assert that after update GPGKey is not associated with product
        assert values['products']['empty_state'] == empty_message
        # Assert that after update GPGKey is still associated
        # with repository
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name


@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_update_key_for_repo_from_product_with_repos(
    session, target_sat, module_org, gpg_content
):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has more than one repository
    then update the key

    :id: d4f2fa16-860c-4ad5-b04f-8ce24b5618e9

    :expectedresults: gpg key is associated with single repository
        after update but not with product
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    # Creates new product without selecting GPGkey
    product = target_sat.api.Product(organization=module_org).create()
    # Creates new repository_1 with GPGKey
    repo1 = target_sat.api.Repository(
        url=settings.repos.yum_1.url, product=product, gpg_key=gpg_key
    ).create()
    # Creates new repository_2 without GPGKey
    target_sat.api.Repository(product=product, url=settings.repos.yum_2.url).create()
    with session:
        session.contentcredential.update(name, {'details.name': new_name})
        values = session.contentcredential.read(new_name)
        assert values['products']['empty_state'] == empty_message
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo1.name


@pytest.mark.e2e
def test_positive_react_list_table(session, target_sat, module_org, gpg_content):
    """Verify multiple content credentials of different types are listed on the React UI.

    :id: 32b37ca2-d7bf-40d0-a5e6-8d3db6ae6d39

    :steps:
        1. Create a GPG key content credential via API
        2. Create an SSL certificate content credential via API
        3. Create a GPG key with product and repository associations
        4. Navigate to the new content credentials list page
        5. Search and verify each credential

    :expectedresults:
        1. All credentials appear with their respective types
        2. Table contains all expected columns
        3. Product and repository counts are accurate
        4. Search functionality works correctly
    """
    # Create GPG key credential
    gpg_name = gen_string('alphanumeric')
    target_sat.api.GPGKey(content=gpg_content, name=gpg_name, organization=module_org).create()

    # Create SSL certificate credential
    ssl_name = gen_string('alphanumeric')
    target_sat.api.ContentCredential(
        content=gpg_content,
        name=ssl_name,
        organization=module_org,
        content_type='cert',
    ).create()

    # Create GPG key with product and repository for column validation
    gpg_with_product_name = gen_string('alphanumeric')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=gpg_with_product_name, organization=module_org
    ).create()
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    target_sat.api.Repository(product=product).create()

    with session:
        session.organization.select(module_org.name)

        # Verify GPG key type
        gpg_results = session.contentcredential.search(gpg_name)
        assert len(gpg_results) == 1
        assert gpg_results[0]['Type'] == CONTENT_CREDENTIALS_TYPES['gpg']

        # Verify SSL certificate type
        ssl_results = session.contentcredential.search(ssl_name)
        assert len(ssl_results) == 1
        assert ssl_results[0]['Type'] == CONTENT_CREDENTIALS_TYPES['ssl']

        # Verify table columns and counts
        results = session.contentcredential.search(gpg_with_product_name)
        assert len(results) == 1
        row = results[0]
        expected_columns = {
            'Name',
            'Organization',
            'Type',
            'Products',
            'Repositories',
            'Alternate content sources',
        }
        assert expected_columns.issubset(set(row.keys()))
        assert row['Name'] == gpg_with_product_name
        assert row['Organization'] == module_org.name
        assert row['Type'] == CONTENT_CREDENTIALS_TYPES['gpg']
        assert row['Products'] == '1'
        assert row['Repositories'] == '1'


def test_positive_update_content(session, target_sat, module_org, gpg_content):
    """Update content credential content via inline editing.

    :id: 5c660e76-d5ee-4e90-875c-1419164f277e

    :steps:
        1. Create a GPG key via API
        2. Navigate to details page
        3. Update the content field
        4. Verify the change

    :expectedresults: Content is updated successfully
    """
    name = gen_string('alpha')
    new_content = DataFile.VALID_GPG_KEY_BETA_FILE.read_text()

    target_sat.api.GPGKey(content=gpg_content, name=name, organization=module_org).create()

    with session:
        session.organization.select(module_org.name)
        session.contentcredential.update(name, {'content': new_content})

        values = session.contentcredential.read(name)
        # Content should be updated
        assert values['details']['content'] != gpg_content


def test_positive_read_products_tab_multiple(session, target_sat, module_org, gpg_content):
    """Read products tab with multiple associated products.

    :id: 62962c46-648e-4c28-8ffb-befc075d7153

    :steps:
        1. Create a GPG key via API
        2. Create multiple products associated with the GPG key
        3. Navigate to details page
        4. Read products tab

    :expectedresults: Products tab shows all associated products
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()

    product1 = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    product2 = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()

    with session:
        session.organization.select(module_org.name)
        values = session.contentcredential.read(name)

        products_table = values.get('products', {}).get('table', [])
        assert len(products_table) == 2
        product_names = {row['Name'] for row in products_table}
        assert {product1.name, product2.name} == product_names


def test_positive_filter_products(session, target_sat, module_org, gpg_content):
    """Filter products by name in the products tab.

    :id: c96b6950-3399-46d5-9da7-b1f7bbecedcd

    :steps:
        1. Create a GPG key via API
        2. Create multiple products with different names
        3. Navigate to details page
        4. Filter products by name

    :expectedresults: Only matching products are returned
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()

    search_term = gen_string('alpha', 5)
    product1 = target_sat.api.Product(
        name=f'{search_term}-product', gpg_key=gpg_key, organization=module_org
    ).create()
    # Create another product without search term to test filtering
    target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()

    with session:
        session.organization.select(module_org.name)

        # Filter by search term
        filtered_products = session.contentcredential.get_product_details(name, filter=search_term)

        # Should only return product1
        assert len(filtered_products) == 1
        assert any(p['Name'] == product1.name for p in filtered_products)


def test_positive_filter_repositories(session, target_sat, module_org, gpg_content):
    """Filter repositories by name in the repositories tab.

    :id: 0d439d5e-d542-4763-b684-0d8b61ccb7d4

    :steps:
        1. Create a GPG key via API
        2. Create a product with multiple repositories
        3. Navigate to details page
        4. Filter repositories by name

    :expectedresults: Only matching repositories are returned
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()

    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()

    search_term = gen_string('alpha', 5)
    repo1 = target_sat.api.Repository(
        name=f'{search_term}-repo', product=product, url=settings.repos.yum_1.url
    ).create()
    # Create another repository without search term to test filtering
    target_sat.api.Repository(product=product, url=settings.repos.yum_2.url).create()

    with session:
        session.organization.select(module_org.name)

        # Filter by search term
        filtered_repos = session.contentcredential.get_repository_details(name, filter=search_term)

        # Should only return repo1
        assert len(filtered_repos) == 1
        assert any(r['Name'] == repo1.name for r in filtered_repos)


def test_positive_read_acs_tab_empty(session, target_sat, module_org, gpg_content):
    """Read alternate content sources tab when none are associated.

    :id: 68c55706-cb6e-43b1-a6fd-df2302c9410b

    :steps:
        1. Create a GPG key via API (no associated ACS)
        2. Navigate to details page
        3. Read ACS tab

    :expectedresults: ACS tab shows empty state message
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()

    with session:
        session.organization.select(module_org.name)
        acs = session.contentcredential.get_acs_details(gpg_key.name)

        # When no ACS are associated, empty state card is shown instead of table
        assert len(acs) == 0


def test_positive_counts_reflect_associations(session, target_sat, module_org, gpg_content):
    """Verify product and repository counts in details tab.

    :id: 8a31ce9b-ed9b-4653-a733-5cd5de7d1d51

    :steps:
        1. Create a GPG key via API
        2. Create 2 products and 3 repositories
        3. Navigate to details page
        4. Check counts in details tab

    :expectedresults: Counts accurately reflect the number of associations
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()

    # Create 2 products
    product1 = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    product2 = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()

    # Create 3 repositories
    target_sat.api.Repository(product=product1).create()
    target_sat.api.Repository(product=product1).create()
    target_sat.api.Repository(product=product2).create()

    with session:
        session.organization.select(module_org.name)
        values = session.contentcredential.read(name)

        assert values['details']['products'] == '2'
        assert values['details']['repositories'] == '3'


def test_positive_breadcrumb_navigation(session, target_sat, module_org, gpg_content):
    """Verify breadcrumb is displayed on details page.

    :id: bc1293dc-24e7-4321-bb7b-f74940e6b622

    :steps:
        1. Create a GPG key via API
        2. Navigate to details page
        3. Check breadcrumb presence

    :expectedresults: Breadcrumb is displayed correctly
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()

    with session:
        session.organization.select(module_org.name)
        view = session.contentcredential.navigate_to(
            session.contentcredential, 'Edit', entity_name=gpg_key.name
        )

        assert view.page_breadcrumb.is_displayed
        assert view.is_displayed
