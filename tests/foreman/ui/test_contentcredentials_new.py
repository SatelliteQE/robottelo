"""Test class for the React-based Content Credentials list page UI

:Requirement: ContentCredentials

:CaseAutomation: Automated

:CaseComponent: ContentCredentials

:team: Artemis

:CaseImportance: High

"""

import pytest

from robottelo.constants import CONTENT_CREDENTIALS_TYPES, DataFile
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def gpg_content():
    return DataFile.VALID_GPG_KEY_FILE.read_text()


@pytest.mark.e2e
def test_positive_list_content_credentials(session, target_sat, module_org, gpg_content):
    """Verify content credentials are listed on the React-based list page.

    :id: a1f3c7e2-8b4d-4f6a-9c2e-1d3b5a7f9e0c

    :steps:
        1. Create a GPG key content credential via API
        2. Navigate to the new content credentials list page
        3. Read all table rows

    :expectedresults: The created content credential appears in the table
        with correct Name and Type columns.
    """
    name = gen_string('alpha')
    target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    with session:
        session.organization.select(module_org.name)
        table_data = session.contentcredential_new.read_table()
        credential_names = [row['Name'] for row in table_data]
        assert name in credential_names
        matching = [row for row in table_data if row['Name'] == name]
        assert len(matching) == 1
        assert matching[0]['Type'] == CONTENT_CREDENTIALS_TYPES['gpg']


def test_positive_search_content_credential(session, target_sat, module_org, gpg_content):
    """Search for a content credential by name on the React-based list page.

    :id: b2e4d8f3-9c5a-4e7b-a1d3-2f6c8b0e4a7d

    :steps:
        1. Create a GPG key content credential via API
        2. Navigate to the new content credentials list page
        3. Search by the credential name

    :expectedresults: Only the matching content credential is returned.
    """
    name = gen_string('alpha')
    target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    with session:
        session.organization.select(module_org.name)
        results = session.contentcredential_new.search(name)
        assert len(results) >= 1
        assert results[0]['Name'] == name


def test_positive_search_no_results(session, module_org):
    """Search for a non-existent content credential returns no results.

    :id: c3f5e9a4-0d6b-4f8c-b2e4-3a7d9c1f5b8e

    :steps:
        1. Navigate to the new content credentials list page
        2. Search for a name that does not exist

    :expectedresults: No results are returned.
    """
    with session:
        session.organization.select(module_org.name)
        results = session.contentcredential_new.search(gen_string('alpha'))
        assert len(results) == 0


def test_positive_table_columns(session, target_sat, module_org, gpg_content):
    """Verify the React-based list page displays all expected columns.

    :id: d4a6f0b5-1e7c-4a9d-c3f5-4b8e0d2a6c9f

    :steps:
        1. Create a GPG key content credential with an associated product
        2. Navigate to the new content credentials list page
        3. Read the table data

    :expectedresults: Each row contains Name, Organization, Type, Products,
        Repositories, and Alternate Content Sources columns.
    """
    name = gen_string('alpha')
    gpg_key = target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    product = target_sat.api.Product(gpg_key=gpg_key, organization=module_org).create()
    target_sat.api.Repository(product=product).create()
    with session:
        session.organization.select(module_org.name)
        results = session.contentcredential_new.search(name)
        assert len(results) == 1
        row = results[0]
        expected_columns = {
            'Name',
            'Organization',
            'Type',
            'Products',
            'Repositories',
            'Alternate Content Sources',
        }
        assert expected_columns.issubset(set(row.keys()))
        assert row['Name'] == name
        assert row['Organization'] == module_org.name
        assert row['Type'] == CONTENT_CREDENTIALS_TYPES['gpg']
        assert row['Products'] == '1'
        assert row['Repositories'] == '1'


def test_positive_list_multiple_types(session, target_sat, module_org, gpg_content):
    """Verify multiple content credentials of different types are listed.

    :id: e5b7a1c6-2f8d-4b0e-d4a6-5c9f1e3b7d0a

    :steps:
        1. Create a GPG key content credential via API
        2. Create an SSL certificate content credential via API
        3. Navigate to the new content credentials list page
        4. Read the table

    :expectedresults: Both credentials appear with their respective types.
    """
    gpg_name = gen_string('alpha')
    ssl_name = gen_string('alpha')
    target_sat.api.GPGKey(
        content=gpg_content, name=gpg_name, organization=module_org
    ).create()
    target_sat.api.ContentCredential(
        content=gpg_content,
        name=ssl_name,
        organization=module_org,
        content_type='cert',
    ).create()
    with session:
        session.organization.select(module_org.name)
        gpg_results = session.contentcredential_new.search(gpg_name)
        assert len(gpg_results) >= 1
        assert gpg_results[0]['Type'] == CONTENT_CREDENTIALS_TYPES['gpg']
        ssl_results = session.contentcredential_new.search(ssl_name)
        assert len(ssl_results) >= 1
        assert ssl_results[0]['Type'] == CONTENT_CREDENTIALS_TYPES['ssl']


def test_positive_search_scoped(session, target_sat, module_org, gpg_content):
    """Search for a content credential using scoped search on the React page.

    :id: f6c8b2d7-3a9e-4c1f-e5b7-6d0a2f4c8e1b

    :steps:
        1. Create a GPG key content credential via API
        2. Navigate to the new content credentials list page
        3. Search using name = "<name>" scoped syntax

    :expectedresults: The matching content credential is found.
    """
    name = gen_string('alpha')
    target_sat.api.GPGKey(
        content=gpg_content, name=name, organization=module_org
    ).create()
    with session:
        session.organization.select(module_org.name)
        results = session.contentcredential_new.search(f'name = "{name}"')
        assert len(results) == 1
        assert results[0]['Name'] == name
