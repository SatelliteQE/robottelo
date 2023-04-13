"""Unit tests for the ``gpgkeys`` paths.

:Requirement: ContentCredential

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentCredentials

:team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from copy import copy

import pytest
from fauxfactory import gen_string
from nailgun import entities
from requests import HTTPError

from robottelo.constants import DataFile
from robottelo.utils.datafactory import invalid_values_list
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_data_list

key_content = DataFile.VALID_GPG_KEY_FILE.read_text()


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_name(module_org, name):
    """Create a GPG key with valid name.

    :id: 741d969b-28ef-481f-bcf7-ed4cd920b030

    :parametrized: yes

    :expectedresults: A GPG key is created with the given name.

    :CaseImportance: Critical
    """
    gpg_key = entities.GPGKey(organization=module_org, name=name).create()
    assert name == gpg_key.name


@pytest.mark.tier1
def test_positive_create_with_content(module_org):
    """Create a GPG key with valid name and valid gpg key text.

    :id: cfa6690e-fed7-49cf-94f9-fd2deed941c0

    :expectedresults: A GPG key is created with the expected content.

    :CaseImportance: Critical
    """
    gpg_key = entities.GPGKey(organization=module_org, content=key_content).create()
    assert key_content == gpg_key.content


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_create_name(module_org, name):
    """Attempt to create GPG key with invalid names only.

    :id: 904a3ed0-7d50-495e-a700-b4f1ae913599

    :parametrized: yes

    :expectedresults: A GPG key is not created and 422 error is raised.

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError) as error:
        entities.GPGKey(organization=module_org, name=name).create()
    assert error.value.response.status_code == 422
    assert 'Validation failed:' in error.value.response.text


@pytest.mark.tier1
def test_negative_create_with_same_name(module_org):
    """Attempt to create a GPG key providing a name of already existent
    entity

    :id: 78299f13-5977-4409-9bc7-844e54349926

    :expectedresults: A GPG key is not created and 422 error is raised.

    :CaseImportance: Critical
    """
    name = gen_string('alphanumeric')
    entities.GPGKey(organization=module_org, name=name).create()
    with pytest.raises(HTTPError) as error:
        entities.GPGKey(organization=module_org, name=name).create()
    assert error.value.response.status_code == 422
    assert 'Validation failed:' in error.value.response.text


@pytest.mark.tier1
def test_negative_create_with_content(module_org):
    """Attempt to create GPG key with empty content.

    :id: fc79c840-6bcb-4d97-9145-c0008d5b028d

    :expectedresults: A GPG key is not created and 422 error is raised.

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError) as error:
        entities.GPGKey(organization=module_org, content='').create()
    assert error.value.response.status_code == 422
    assert 'Validation failed:' in error.value.response.text


@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_name(module_org, new_name):
    """Update GPG key name to another valid name.

    :id: 9868025d-5346-42c9-b850-916ce37a9541

    :parametrized: yes

    :expectedresults: The GPG key name can be updated.

    :CaseImportance: Critical
    """
    gpg_key = entities.GPGKey(organization=module_org).create()
    gpg_key.name = new_name
    gpg_key = gpg_key.update(['name'])
    assert new_name == gpg_key.name


@pytest.mark.tier1
def test_positive_update_content(module_org):
    """Update GPG key content text to another valid one.

    :id: 62fdaf55-c931-4be6-9857-68cc816046ad

    :expectedresults: The GPG key content text can be updated.

    :CaseImportance: Critical
    """
    gpg_key = entities.GPGKey(
        organization=module_org,
        content=DataFile.VALID_GPG_KEY_BETA_FILE.read_text(),
    ).create()
    gpg_key.content = key_content
    gpg_key = gpg_key.update(['content'])
    assert key_content == gpg_key.content


@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_update_name(module_org, new_name):
    """Attempt to update GPG key name to invalid one

    :id: 1a43f610-8969-4f08-967f-fb6af0fca31b

    :parametrized: yes

    :expectedresults: GPG key is not updated and 422 error is raised.

    :CaseImportance: Critical
    """
    gpg_key = entities.GPGKey(organization=module_org).create()
    gpg_key.name = new_name
    with pytest.raises(HTTPError) as error:
        gpg_key.update(['name'])
    assert error.value.response.status_code == 422
    assert 'Validation failed:' in error.value.response.text


@pytest.mark.tier1
def test_negative_update_same_name(module_org):
    """Attempt to update GPG key name to the name of existing GPG key
    entity

    :id: e294e3b2-1125-4ad9-969a-eb3f1966419e

    :expectedresults: GPG key is not updated and 422 error is raised.

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    entities.GPGKey(organization=module_org, name=name).create()
    new_gpg_key = entities.GPGKey(organization=module_org).create()
    new_gpg_key.name = name
    with pytest.raises(HTTPError) as error:
        new_gpg_key.update(['name'])
    assert error.value.response.status_code == 422
    assert 'Validation failed:' in error.value.response.text


@pytest.mark.tier1
def test_negative_update_content(module_org):
    """Attempt to update GPG key content to invalid one

    :id: fee30ef8-370a-4fdd-9e45-e7ab95dade8b

    :expectedresults: GPG key is not updated and 422 error is raised.

    :CaseImportance: Critical
    """
    gpg_key = entities.GPGKey(organization=module_org, content=key_content).create()
    gpg_key.content = ''
    with pytest.raises(HTTPError) as error:
        gpg_key.update(['content'])
    assert key_content == gpg_key.read().content
    assert error.value.response.status_code == 422
    assert 'Validation failed:' in error.value.response.text


@pytest.mark.tier1
def test_positive_delete(module_org):
    """Create a GPG key with different names and then delete it.

    :id: b06d211f-2827-40f7-b627-8b1fbaee2eb4

    :expectedresults: The GPG key deleted successfully.

    :CaseImportance: Critical
    """
    gpg_key = entities.GPGKey(organization=module_org).create()
    gpg_key.delete()
    with pytest.raises(HTTPError):
        gpg_key.read()


@pytest.mark.tier3
def test_positive_block_delete_key_in_use(module_org, target_sat):
    """Create a GPG key with valid content. Create a new product and
        associated repository, assigning the GPG key to both. Attempt to delete the
        GPG key in use.

    :id: b79fd3ff-8cdb-4cdd-94e5-76de742ec967

    :expectedresults: Blocked deletion of gpg key in use, it remains
        unmodified, is still associated with product and repo.

    :BZ: 2052904

    :customerscenario: true

    :CaseImportance: Critical
    """
    gpg_key = target_sat.api.GPGKey(organization=module_org, content=key_content).create()
    gpg_copy = copy(gpg_key)
    # Create new product with gpg, and a single associated repository
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    repo = target_sat.api.Repository(product=product).create()
    product.sync()

    # Assert the same gpg key is associated with new product and repo
    assert product.gpg_key.id == gpg_key.id
    assert repo.gpg_key.id == gpg_key.id
    assert product.gpg_key.id == repo.gpg_key.id

    # Attempt to delete gpg in use, capturing api response without raising exception
    response = gpg_key.delete_raw()
    assert response.status_code == 500
    assert 'Cannot delete record because of dependent root_repositories' in str(
        response.json().get('errors')
    )

    # Assert gpg matches unmodified copy
    assert gpg_key.id == gpg_copy.id
    assert gpg_key.organization == gpg_copy.organization
    assert gpg_key.content == gpg_copy.content
    # Assert gpg remains associated with product and repo
    assert product.gpg_key.id == repo.gpg_key.id
    assert product.gpg_key.id == gpg_key.id
    assert repo.gpg_key.id == gpg_key.id
