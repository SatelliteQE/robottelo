"""Test class for GPG Key CLI.
The gpg sub-command was deprecated in favour of content-credential in
Satellite 6.8

:Requirement: ContentCredential

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentCredentials

:Assignee: spusater

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from tempfile import mkstemp

import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_choice
from fauxfactory import gen_integer
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.content_credentials import ContentCredential
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_content_credential
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DataFile
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list

VALID_GPG_KEY_FILE_PATH = DataFile.VALID_GPG_KEY_FILE


def create_gpg_key_file(content=None):
    """Creates a fake GPG Key file and returns its path or None if an error
    happens.
    """

    (_, key_filename) = mkstemp(text=True)
    if not content:
        content = gen_alphanumeric(gen_integer(20, 50))
    with open(key_filename, "w") as gpg_key_file:
        gpg_key_file.write(content)
        return key_filename

    return None


search_key = 'name'


@pytest.mark.build_sanity
@pytest.mark.tier1
def test_verify_gpg_key_content_displayed(module_org):
    """content-credential info should display key content

    :id: 0ee87ee0-8bf1-4d15-b5f9-0ac364e61155

    :expectedresults: content-credentials info should display key content

    :CaseImportance: Critical
    """
    # Setup a new key file
    content = gen_alphanumeric()
    key_path = create_gpg_key_file(content=content)
    assert key_path, 'GPG Key file must be created'
    gpg_key = make_content_credential(
        {'path': key_path, 'name': gen_string('alpha'), 'organization-id': module_org.id}
    )
    assert gpg_key['content'] == content


@pytest.mark.tier1
def test_positive_get_info_by_name(module_org):
    """Create single gpg key and get its info by name

    :id: 890456ea-0b31-4386-9231-f47572f26d08

    :expectedresults: specific information for GPG key matches the creation
        name

    :CaseImportance: Critical
    """
    name = gen_string('utf8')
    gpg_key = make_content_credential(
        {'key': VALID_GPG_KEY_FILE_PATH, 'name': name, 'organization-id': module_org.id}
    )
    gpg_key = ContentCredential.info({'name': gpg_key['name'], 'organization-id': module_org.id})
    assert gpg_key['name'] == name


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_default_org(name, module_org, default_org):
    """Create gpg key with valid name and valid gpg key via file
    import using the default created organization

    :id: 4265dfd1-dc64-4119-8a64-8724b09d6fb7

    :parametrized: yes

    :expectedresults: gpg key is created

    :CaseImportance: Critical
    """
    org = Org.info({'name': DEFAULT_ORG})
    gpg_key = make_content_credential(
        {'key': VALID_GPG_KEY_FILE_PATH, 'name': name, 'organization-id': org['id']}
    )
    # Can we find the new object?
    result = ContentCredential.exists(
        {'organization-id': org['id']}, (search_key, gpg_key[search_key])
    )
    assert gpg_key[search_key] == result[search_key]


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_custom_org(name, module_org):
    """Create gpg key with valid name and valid gpg key via file
    import using a new organization

    :id: 10dd9fc0-e088-4cf1-9fb6-24fe04df2895

    :parametrized: yes

    :expectedresults: gpg key is created

    :CaseImportance: Critical
    """
    gpg_key = make_content_credential(
        {
            'key': VALID_GPG_KEY_FILE_PATH,
            'name': name,
            'organization-id': module_org.id,
        }
    )
    # Can we find the new object?
    result = ContentCredential.exists(
        {'organization-id': module_org.id},
        (search_key, gpg_key[search_key]),
    )
    assert gpg_key[search_key] == result[search_key]


@pytest.mark.tier1
def test_negative_create_with_same_name(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then try to create new one with same name

    :id: 8751745c-5cf6-42f7-8fbd-6c23119da486

    :expectedresults: gpg key is not created

    :CaseImportance: Critical
    """
    name = gen_string('alphanumeric')
    gpg_key = make_content_credential({'name': name, 'organization-id': module_org.id})
    # Can we find the new object?
    result = ContentCredential.exists(
        {'organization-id': module_org.id}, (search_key, gpg_key[search_key])
    )
    assert gpg_key[search_key] == result[search_key]
    with pytest.raises(CLIFactoryError):
        make_content_credential({'name': name, 'organization-id': module_org.id})


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_negative_create_with_no_gpg_key(name, module_org):
    """Create gpg key with valid name and no gpg key

    :id: bbfd5306-cfe7-40c1-a3a2-35834108163c

    :parametrized: yes

    :expectedresults: gpg key is not created

    :CaseImportance: Critical
    """
    with pytest.raises(CLIReturnCodeError):
        ContentCredential.create({'name': name, 'organization-id': module_org.id})


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_create_with_invalid_name(name, module_org):
    """Create gpg key with invalid name and valid gpg key via
    file import

    :id: fbbaf8a5-1570-4910-9f6a-baa35b15d2ad

    :parametrized: yes

    :expectedresults: gpg key is not created

    :CaseImportance: Critical
    """
    with pytest.raises(CLIFactoryError):
        # factory will provide a valid key
        make_content_credential({'name': name, 'organization-id': module_org.id})


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete(name, module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then delete it

    :id: 9640cabc-e0c3-41a0-b4de-99b06bf51c02

    :parametrized: yes

    :expectedresults: gpg key is deleted

    :CaseImportance: Critical
    """
    gpg_key = make_content_credential({'name': name, 'organization-id': module_org.id})
    result = ContentCredential.exists(
        {'organization-id': module_org.id},
        (search_key, gpg_key[search_key]),
    )
    assert gpg_key[search_key] == result[search_key]
    ContentCredential.delete({'name': name, 'organization-id': module_org.id})
    result = ContentCredential.exists(
        {'organization-id': module_org.id},
        (search_key, gpg_key[search_key]),
    )
    assert (len(result)) == 0


@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_name(new_name, module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then update its name

    :id: f3bb254d-f831-4f86-944a-26d9a36bd906

    :parametrized: yes

    :expectedresults: gpg key is updated

    :CaseImportance: Critical
    """
    gpg_key = make_content_credential({'organization-id': module_org.id})
    ContentCredential.update(
        {
            'name': gpg_key['name'],
            'new-name': new_name,
            'organization-id': module_org.id,
        }
    )
    gpg_key = ContentCredential.info({'name': new_name, 'organization-id': module_org.id})


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_key(name, module_org, target_sat):
    """Create gpg key with valid name and valid gpg key via file
    import then update its gpg key file

    :id: d3a72892-3414-4178-98b7-e0780d9b6587

    :parametrized: yes

    :expectedresults: gpg key is updated

    :CaseImportance: Critical
    """
    gpg_key = make_content_credential({'organization-id': module_org.id})
    content = gen_alphanumeric(gen_integer(20, 50))
    assert gpg_key['content'] != content
    local_key = create_gpg_key_file(content)
    assert gpg_key, 'GPG Key file must be created'
    key = f'/tmp/{gen_alphanumeric()}'
    target_sat.put(local_key, key)
    ContentCredential.update(
        {'path': key, 'name': gpg_key['name'], 'organization-id': module_org.id}
    )
    gpg_key = ContentCredential.info({'name': gpg_key['name'], 'organization-id': module_org.id})
    assert gpg_key['content'] == content


@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_update_name(new_name, module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then fail to update its name

    :id: 98cda40a-49d0-42ce-91a6-31fa7b7f330b

    :parametrized: yes

    :expectedresults: gpg key is not updated

    :CaseImportance: Critical
    """
    gpg_key = make_content_credential({'organization-id': module_org.id})
    with pytest.raises(CLIReturnCodeError):
        ContentCredential.update(
            {
                'name': gpg_key['name'],
                'new-name': new_name,
                'organization-id': module_org.id,
            }
        )


@pytest.mark.tier2
def test_positive_add_empty_product(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with empty (no repos) custom product

    :id: 61c700db-43ab-4b8c-8527-f4cfc085afaa

    :expectedresults: gpg key is associated with product

    :CaseLevel: Integration
    """
    gpg_key = make_content_credential({'organization-id': module_org.id})
    product = make_product({'gpg-key-id': gpg_key['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] == gpg_key['name']


@pytest.mark.tier2
def test_positive_add_product_with_repo(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with custom product that has one repository

    :id: f315eadd-e65b-4952-912f-f640867ad656

    :expectedresults: gpg key is associated with product as well as with
        the repository

    :CaseLevel: Integration
    """
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    Product.update(
        {'gpg-key-id': gpg_key['id'], 'id': product['id'], 'organization-id': module_org.id}
    )
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    repo = Repository.info({'id': repo['id']})
    assert product['gpg']['gpg-key-id'] == gpg_key['id']
    assert repo['gpg-key']['id'] == gpg_key['id']


@pytest.mark.tier2
def test_positive_add_product_with_repos(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with custom product that has more than one
    repository

    :id: 76683f3e-7705-4719-996e-c026839053bb

    :expectedresults: gpg key is associated with product as well as with
        the repositories

    :CaseLevel: Integration
    """
    product = make_product({'organization-id': module_org.id})
    repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
    gpg_key = make_content_credential({'organization-id': module_org.id})
    Product.update(
        {'gpg-key-id': gpg_key['id'], 'id': product['id'], 'organization-id': module_org.id}
    )
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key-id'] == gpg_key['id']
    for repo in repos:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key']['id'] == gpg_key['id']


@pytest.mark.tier2
def test_positive_add_repo_from_product_with_repo(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it to repository from custom product that has
    one repository

    :id: da568a0e-69b1-498e-a747-6881aac7409e

    :expectedresults: gpg key is associated with the repository but not
        with the product

    :CaseLevel: Integration
    """
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    Repository.update(
        {'gpg-key-id': gpg_key['id'], 'id': repo['id'], 'organization-id': module_org.id}
    )
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    repo = Repository.info({'id': repo['id']})
    assert repo['gpg-key']['id'] == gpg_key['id']
    assert product['gpg'].get('gpg-key-id') != gpg_key['id']


@pytest.mark.tier2
def test_positive_add_repo_from_product_with_repos(module_org):
    """Create gpg key via file import and associate with custom repo

    GPGKey should contain valid name and valid key and should be associated
    to one repository from custom product. Make sure custom product should
    have more than one repository.

    :id: e3019a61-ec32-4044-9087-e420b8db4e09

    :expectedresults: gpg key is associated with the repository

    :CaseLevel: Integration
    """
    product = make_product({'organization-id': module_org.id})
    repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
    gpg_key = make_content_credential({'organization-id': module_org.id})
    Repository.update(
        {'gpg-key-id': gpg_key['id'], 'id': repos[0]['id'], 'organization-id': module_org.id}
    )
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg'].get('gpg-key-id') != gpg_key['id']
    # First repo should have a valid gpg key assigned
    repo = Repository.info({'id': repos.pop(0)['id']})
    assert repo['gpg-key']['id'] == gpg_key['id']
    # The rest of repos should not
    for repo in repos:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key'].get('id') != gpg_key['id']


@pytest.mark.tier2
def test_positive_update_key_for_empty_product(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with empty (no repos) custom product then
    update the key

    :id: 13aa6e0c-4255-483a-af33-ea7e82ee7766

    :expectedresults: gpg key is associated with product before/after
        update

    :CaseLevel: Integration
    """
    # Create a product and a gpg key
    product = make_product({'organization-id': module_org.id})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Associate gpg key with a product
    Product.update(
        {'gpg-key-id': gpg_key['id'], 'id': product['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] == gpg_key['name']
    # Update the gpg key
    new_name = gen_choice(list(valid_data_list().values()))
    ContentCredential.update(
        {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    # Verify changes are reflected in the gpg key
    gpg_key = ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    assert gpg_key['name'] == new_name
    # Verify changes are reflected in the product
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] == new_name


@pytest.mark.tier2
def test_positive_update_key_for_product_with_repo(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with custom product that has one repository
    then update the key

    :id: 1f8f943c-a611-4ed2-9d8a-770f60a549a7

    :expectedresults: gpg key is associated with product before/after
        update as well as with the repository

    :CaseLevel: Integration
    """
    # Create a product and a gpg key
    product = make_product({'organization-id': module_org.id})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Create a repository and assign it to the product
    repo = make_repository({'product-id': product['id']})
    # Associate gpg key with a product
    Product.update(
        {'gpg-key-id': gpg_key['id'], 'id': product['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    repo = Repository.info({'id': repo['id']})
    assert product['gpg']['gpg-key'] == gpg_key['name']
    assert repo['gpg-key'].get('name') == gpg_key['name']
    # Update the gpg key
    new_name = gen_choice(list(valid_data_list().values()))
    ContentCredential.update(
        {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    # Verify changes are reflected in the gpg key
    gpg_key = ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    assert gpg_key['name'] == new_name
    # Verify changes are reflected in the product
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] == new_name
    # Verify changes are reflected in the repository
    repo = Repository.info({'id': repo['id']})
    assert repo['gpg-key'].get('id') == gpg_key['id']


@pytest.mark.tier2
def test_positive_update_key_for_product_with_repos(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with custom product that has more than one
    repository then update the key

    :id: 8aa3dc75-6257-48ae-b3f9-c617e323b47a

    :expectedresults: gpg key is associated with product before/after
        update as well as with the repositories

    :CaseLevel: Integration
    """
    # Create a product and a gpg key
    product = make_product({'organization-id': module_org.id})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Create repositories and assign them to the product
    repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
    # Associate gpg key with a product
    Product.update(
        {'gpg-key-id': gpg_key['id'], 'id': product['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] == gpg_key['name']
    for repo in repos:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key'].get('name') == gpg_key['name']
    # Update the gpg key
    new_name = gen_choice(list(valid_data_list().values()))
    ContentCredential.update(
        {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    # Verify changes are reflected in the gpg key
    gpg_key = ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    assert gpg_key['name'] == new_name
    # Verify changes are reflected in the product
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] == new_name
    # Verify changes are reflected in the repositories
    for repo in repos:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key'].get('name') == new_name


@pytest.mark.tier2
def test_positive_update_key_for_repo_from_product_with_repo(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it to repository from custom product that has
    one repository then update the key

    :id: 2fee5f35-6e0e-4b7c-8a8a-46ee1e77919d

    :expectedresults: gpg key is associated with the repository
        before/after update, but not with the product

    :CaseLevel: Integration
    """
    # Create a product and a gpg key
    product = make_product({'organization-id': module_org.id})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Create repository, assign product and gpg-key
    repo = make_repository({'gpg-key-id': gpg_key['id'], 'product-id': product['id']})
    # Verify gpg key was associated
    assert repo['gpg-key'].get('name') == gpg_key['name']
    # Update the gpg key
    new_name = gen_choice(list(valid_data_list().values()))
    ContentCredential.update(
        {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    # Verify changes are reflected in the gpg key
    gpg_key = ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    assert gpg_key['name'] == new_name
    # Verify changes are reflected in the repositories
    repo = Repository.info({'id': repo['id']})
    assert repo['gpg-key'].get('name') == new_name
    # Verify gpg key wasn't added to the product
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] != new_name


@pytest.mark.tier2
def test_positive_update_key_for_repo_from_product_with_repos(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it to repository from custom product that has
    more than one repository then update the key

    :id: c548ed4f-7f2d-456f-a644-7597644f6457

    :expectedresults: gpg key is associated with a single repository
        before/after update and not associated with product or other
        repositories

    :CaseLevel: Integration
    """
    # Create a product and a gpg key
    product = make_product({'organization-id': module_org.id})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Create repositories and assign them to the product
    repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
    # Associate gpg key with a single repository
    Repository.update(
        {'gpg-key-id': gpg_key['id'], 'id': repos[0]['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated
    repos[0] = Repository.info({'id': repos[0]['id']})
    assert repos[0]['gpg-key']['name'] == gpg_key['name']
    # Update the gpg key
    new_name = gen_choice(list(valid_data_list().values()))
    ContentCredential.update(
        {'name': gpg_key['name'], 'new-name': new_name, 'organization-id': module_org.id}
    )
    # Verify changes are reflected in the gpg key
    gpg_key = ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    assert gpg_key['name'] == new_name
    # Verify changes are reflected in the associated repository
    repos[0] = Repository.info({'id': repos[0]['id']})
    assert repos[0]['gpg-key'].get('name') == new_name
    # Verify changes are not reflected in the product
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] != new_name
    # Verify changes are not reflected in the rest of repositories
    for repo in repos[1:]:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key'].get('name') != new_name


@pytest.mark.tier2
def test_positive_delete_key_for_empty_product(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with empty (no repos) custom product
    then delete it

    :id: 238a80f8-983a-4fd5-a168-6ef9442e2b1c

    :expectedresults: gpg key is associated with product during creation
        but removed from product after deletion

    :CaseLevel: Integration
    """
    # Create a product and a gpg key
    gpg_key = make_content_credential({'organization-id': module_org.id})
    product = make_product({'gpg-key-id': gpg_key['id'], 'organization-id': module_org.id})
    # Verify gpg key was associated
    assert product['gpg']['gpg-key'] == gpg_key['name']
    # Delete the gpg key
    ContentCredential.delete({'name': gpg_key['name'], 'organization-id': module_org.id})
    # Verify gpg key was actually deleted
    with pytest.raises(CLIReturnCodeError):
        ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    # Verify gpg key was disassociated from the product
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] != gpg_key['name']


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_key_for_product_with_repo(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with custom product that has one repository
    then delete it

    :id: 1e98e588-8b5d-475c-ad84-5d566df5619c

    :expectedresults: gpg key is associated with product but and its
        repository during creation but removed from product and repository
        after deletion

    :CaseLevel: Integration
    """
    # Create product, repository and gpg key
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Associate gpg key with a product
    Product.update(
        {'gpg-key-id': gpg_key['id'], 'id': product['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated both with product and its repository
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    repo = Repository.info({'id': repo['id']})
    assert product['gpg']['gpg-key'] == gpg_key['name']
    assert repo['gpg-key'].get('name') == gpg_key['name']
    # Delete the gpg key
    ContentCredential.delete({'name': gpg_key['name'], 'organization-id': module_org.id})
    # Verify gpg key was actually deleted
    with pytest.raises(CLIReturnCodeError):
        ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    # Verify gpg key was disassociated from the product and its repository
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    repo = Repository.info({'id': repo['id']})
    assert product['gpg']['gpg-key'] != gpg_key['name']
    assert repo['gpg-key'].get('name') != gpg_key['name']


@pytest.mark.tier2
def test_positive_delete_key_for_product_with_repos(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it with custom product that has more than one
    repository then delete it

    :id: 3848441f-746a-424c-afc3-4d5a15888af8

    :expectedresults: gpg key is associated with product and its
        repositories during creation but removed from the product and the
        repositories after deletion

    :CaseLevel: Integration
    """
    # Create product, repositories and gpg key
    product = make_product({'organization-id': module_org.id})
    repos = [make_repository({'product-id': product['id']}) for _ in range(gen_integer(2, 5))]
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Associate gpg key with a product
    Product.update(
        {'gpg-key-id': gpg_key['id'], 'id': product['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated with product and its repositories
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] == gpg_key['name']
    for repo in repos:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key'].get('name') == gpg_key['name']
    # Delete the gpg key
    ContentCredential.delete({'name': gpg_key['name'], 'organization-id': module_org.id})
    # Verify gpg key was actually deleted
    with pytest.raises(CLIReturnCodeError):
        ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    # Verify gpg key was disassociated from the product and its
    # repositories
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] != gpg_key['name']
    for repo in repos:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key'].get('name') != gpg_key['name']


@pytest.mark.tier2
def test_positive_delete_key_for_repo_from_product_with_repo(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it to repository from custom product that has
    one repository then delete the key

    :id: 2555b08f-8cee-4e84-8f4d-9b46743f5758

    :expectedresults: gpg key is associated with the single repository but
        not the product during creation and was removed from repository
        after deletion

    :CaseLevel: Integration
    """
    # Create product, repository and gpg key
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Associate gpg key with a repository
    Repository.update(
        {'gpg-key-id': gpg_key['id'], 'id': repo['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated with the repository but not with the
    # product
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    repo = Repository.info({'id': repo['id']})
    assert product['gpg']['gpg-key'] != gpg_key['name']
    assert repo['gpg-key'].get('name') == gpg_key['name']
    # Delete the gpg key
    ContentCredential.delete({'name': gpg_key['name'], 'organization-id': module_org.id})
    # Verify gpg key was actually deleted
    with pytest.raises(CLIReturnCodeError):
        ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    # Verify gpg key was disassociated from the repository
    repo = Repository.info({'id': repo['id']})
    assert repo['gpg-key'].get('name') != gpg_key['name']


@pytest.mark.tier2
def test_positive_delete_key_for_repo_from_product_with_repos(module_org):
    """Create gpg key with valid name and valid gpg key via file
    import then associate it to repository from custom product that has
    more than one repository then delete the key

    :id: 7d6a278b-1063-4e72-bc32-ca60bd17bb84

    :expectedresults: gpg key is associated with a single repository but
        not the product during creation and removed from repository after
        deletion

    :CaseLevel: Integration
    """
    # Create product, repositories and gpg key
    product = make_product({'organization-id': module_org.id})
    repos = []
    for _ in range(gen_integer(2, 5)):
        repos.append(make_repository({'product-id': product['id']}))
    gpg_key = make_content_credential({'organization-id': module_org.id})
    # Associate gpg key with a repository
    Repository.update(
        {'gpg-key-id': gpg_key['id'], 'id': repos[0]['id'], 'organization-id': module_org.id}
    )
    # Verify gpg key was associated with the repository
    repos[0] = Repository.info({'id': repos[0]['id']})
    assert repos[0]['gpg-key']['name'] == gpg_key['name']
    # Delete the gpg key
    ContentCredential.delete({'name': gpg_key['name'], 'organization-id': module_org.id})
    # Verify gpg key was actually deleted
    with pytest.raises(CLIReturnCodeError):
        ContentCredential.info({'id': gpg_key['id'], 'organization-id': module_org.id})
    # Verify gpg key is not associated with any repository or the product
    # itself
    product = Product.info({'id': product['id'], 'organization-id': module_org.id})
    assert product['gpg']['gpg-key'] != gpg_key['name']
    for repo in repos:
        repo = Repository.info({'id': repo['id']})
        assert repo['gpg-key'].get('name') != gpg_key['name']


@pytest.mark.tier1
def test_positive_list(module_org):
    """Create gpg key and list it

    :id: ca69e23b-ca96-43dd-89a6-55b0e4ea322d

    :expectedresults: gpg key is in the list

    :CaseImportance: Critical
    """
    gpg_key = make_content_credential(
        {'key': VALID_GPG_KEY_FILE_PATH, 'organization-id': module_org.id}
    )
    gpg_keys_list = ContentCredential.list({'organization-id': module_org.id})
    assert gpg_key['id'] in [gpg['id'] for gpg in gpg_keys_list]


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_search(name, module_org):
    """Create gpg key and search for it

    :id: f72648f1-b468-4662-9653-3464e7d0c349

    :parametrized: yes

    :expectedresults: gpg key can be found

    :CaseImportance: Critical
    """
    gpg_key = make_content_credential(
        {
            'key': VALID_GPG_KEY_FILE_PATH,
            'name': name,
            'organization-id': module_org.id,
        }
    )
    # Can we find the new object?
    result = ContentCredential.exists(
        {'organization-id': module_org.id}, search=('name', gpg_key['name'])
    )
    assert gpg_key['name'] == result['name']
