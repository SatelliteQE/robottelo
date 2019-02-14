# -*- encoding: utf-8 -*-
"""Test class for Content Credentials UI

:Requirement: ContentCredentials

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.constants import (
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    REPO_DISCOVERY_URL,
    VALID_GPG_KEY_FILE,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade
from robottelo.helpers import get_data_file, read_data_file


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def gpg_content():
    return read_data_file(VALID_GPG_KEY_FILE)


@fixture(scope='module')
def gpg_path():
    return get_data_file(VALID_GPG_KEY_FILE)


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, gpg_content):
    """Perform end to end testing for gpg key component

    :id: d1a8cc1b-a072-465b-887d-5bca0acd21c3

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        # Create new gpg key with valid content
        session.contentcredential.create({
            'name': name,
            'content_type': 'GPG Key',
            'content': gpg_content
        })
        assert session.contentcredential.search(name)[0]['Name'] == name
        gpg_key = entities.ContentCredential(organization=module_org).search(
            query={'search': 'name="{}"'.format(name)})[0]
        product = entities.Product(gpg_key=gpg_key, organization=module_org).create()
        repo = entities.Repository(product=product).create()
        values = session.contentcredential.read(name)
        assert values['details']['name'] == name
        assert values['details']['content_type'] == 'GPG Key'
        # transform string for comparison
        transformed_string = gpg_content.replace('\n', ' ')
        transformed_string = transformed_string.replace('  ', ' ')
        assert values['details']['content'] == transformed_string
        assert values['details']['products'] == '1'
        assert values['details']['repos'] == '1'
        assert values['products']['table'][0]['Name'] == product.name
        assert values['repositories']['table'][0]['Name'] == repo.name
        # Update gpg key with new name
        session.contentcredential.update(
            name,
            {'details.name': new_name},
        )
        assert session.contentcredential.search(new_name)[0]['Name'] == new_name
        # Delete gpg key
        session.contentcredential.delete(new_name)
        assert not session.contentcredential.search(new_name)


@tier2
def test_positive_add_empty_product(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate
    it with empty (no repos) custom product

    :id: e18ae9f5-43d9-4049-92ca-1eafaca05096

    :expectedresults: gpg key is associated with product

    :CaseLevel: Integration
    """
    prod_name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        organization=module_org,
    ).create()
    with session:
        session.product.create(
            {'name': prod_name, 'gpg_key': gpg_key.name})
        values = session.contentcredential.read(gpg_key.name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == prod_name
        assert values['products']['table'][0]['Used as'] == 'GPG Key'


@tier2
def test_positive_add_product_with_repo(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has one repository

    :id: 7514b33a-da75-43bd-a84b-5a805c84511d

    :expectedresults: gpg key is associated with product as well as with
        the repository

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product
    product = entities.Product(organization=module_org).create()
    # Creates new repository without GPGKey
    repo = entities.Repository(
        url=FAKE_1_YUM_REPO,
        product=product,
    ).create()
    with session:
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 0
        assert len(values['repositories']['table']) == 0
        # Associate gpg key with a product
        session.product.update(
            product.name, {'details.gpg_key': gpg_key.name}
        )
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name
        assert (
            values['repositories']['table'][0]['Product'] ==
            product.name
        )
        assert values['repositories']['table'][0]['Type'] == 'yum'
        assert (
            values['repositories']['table'][0]['Used as'] ==
            'GPG Key'
        )


@tier2
def test_positive_add_product_with_repos(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has more than one repository

    :id: 0edffad7-0ab4-4bef-b16b-f6c8de55b0dc

    :expectedresults: gpg key is properly associated with repositories

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product and associate GPGKey with it
    product = entities.Product(
        gpg_key=gpg_key,
        organization=module_org,
    ).create()
    # Creates new repository_1 without GPGKey
    repo1 = entities.Repository(
        product=product,
        url=FAKE_1_YUM_REPO,
    ).create()
    # Creates new repository_2 without GPGKey
    repo2 = entities.Repository(
        product=product,
        url=FAKE_2_YUM_REPO,
    ).create()
    with session:
        values = session.contentcredential.read(name)
        assert len(values['repositories']['table']) == 2
        assert (
            {repo1.name, repo2.name} ==
            set([
                repo['Name']
                for repo
                in values['repositories']['table']
            ])
        )


@tier2
def test_positive_add_repo_from_product_with_repo(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has one repository

    :id: 5d78890f-4130-4dc3-9cfe-48999149422f

    :expectedresults: gpg key is associated with the repository but not
        with the product

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product
    product = entities.Product(organization=module_org).create()
    # Creates new repository
    repo = entities.Repository(
        url=FAKE_1_YUM_REPO,
        product=product,
    ).create()
    with session:
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 0
        assert len(values['repositories']['table']) == 0
        # Associate gpg key with repository
        session.repository.update(
            product.name, repo.name, {'repo_content.gpg_key': gpg_key.name}
        )
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 0
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name
        assert (
            values['repositories']['table'][0]['Product'] ==
            product.name
        )


@tier2
def test_positive_add_repo_from_product_with_repos(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has more than one repository

    :id: 1fb38e01-4c04-4609-842d-069f96157317

    :expectedresults: gpg key is associated with one of the repositories
        but not with the product

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product without selecting GPGkey
    product = entities.Product(organization=module_org).create()
    # Creates new repository with GPGKey
    repo1 = entities.Repository(
        url=FAKE_1_YUM_REPO,
        product=product,
        gpg_key=gpg_key,
    ).create()
    # Creates new repository without GPGKey
    entities.Repository(
        url=FAKE_2_YUM_REPO,
        product=product,
    ).create()
    with session:
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 0
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo1.name


@tier2
@upgrade
def test_positive_add_product_using_repo_discovery(session, gpg_path):
    """Create gpg key with valid name and valid gpg key
    then associate it with custom product using Repo discovery method

    :id: 7490a5a6-8575-45eb-addc-298ed3b62649

    :expectedresults: gpg key is associated with product as well as with
        the repositories

    :BZ: 1210180, 1461804, 1595792

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    product_name = gen_string('alpha')
    repo_name = 'fakerepo01'
    with session:
        session.contentcredential.create({
            'name': name,
            'content_type': 'GPG Key',
            'upload_file': gpg_path
        })
        assert session.contentcredential.search(name)[0]['Name'] == name
        session.product.discover_repo({
            'repo_type': 'Yum Repositories',
            'url': REPO_DISCOVERY_URL,
            'discovered_repos.repos': repo_name,
            'create_repo.product_type': 'New Product',
            'create_repo.product_content.product_name': product_name,
            'create_repo.product_content.gpg_key': name,
        })
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product_name
        assert len(values['repositories']['table']) == 1
        assert (values['repositories']['table'][0]['Name'].split(' ')[-1]
                == repo_name)


@tier2
@upgrade
def test_positive_update_key_for_product_using_repo_discovery(session, gpg_path):
    """Create gpg key with valid name and valid content then associate it with custom product
    using Repo discovery method then update the key

    :id: 49279be8-cbea-477e-a1ff-c07171e7084e

    :expectedresults: gpg key is associated with product as well as with
        repository before/after update

    :BZ: 1210180, 1461804

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    product_name = gen_string('alpha')
    repo_name = 'fakerepo01'
    with session:
        session.contentcredential.create({
            'name': name,
            'content_type': 'GPG Key',
            'upload_file': gpg_path
        })
        assert session.contentcredential.search(name)[0]['Name'] == name
        session.product.discover_repo({
            'repo_type': 'Yum Repositories',
            'url': REPO_DISCOVERY_URL,
            'discovered_repos.repos': repo_name,
            'create_repo.product_type': 'New Product',
            'create_repo.product_content.product_name': product_name,
            'create_repo.product_content.gpg_key': name,
        })
        values = session.contentcredential.read(name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product_name
        assert len(values['repositories']['table']) == 1
        assert (values['repositories']['table'][0]['Name'].split(' ')[-1]
                == repo_name)
        product_values = session.product.read(product_name)
        assert product_values['details']['gpg_key'] == name
        session.contentcredential.update(
            name,
            {'details.name': new_name},
        )
        values = session.contentcredential.read(new_name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product_name
        assert len(values['repositories']['table']) == 1
        assert (values['repositories']['table'][0]['Name'].split(' ')[-1]
                == repo_name)
        product_values = session.product.read(product_name)
        assert product_values['details']['gpg_key'] == new_name


@tier2
@upgrade
def test_positive_delete_key_for_product_using_repo_discovery(session, gpg_path):
    """Create gpg key with valid name and valid gpg then associate
    it with custom product using Repo discovery method then delete it

    :id: 513ae138-84d9-4c43-8d4e-7b9fb797208d

    :expectedresults: gpg key is associated with product as well as with
        the repositories during creation but removed from product after
        deletion

    :BZ: 1210180, 1461804

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    product_name = gen_string('alpha')
    repo_name = 'fakerepo01'
    with session:
        session.contentcredential.create({
            'name': name,
            'content_type': 'GPG Key',
            'upload_file': gpg_path
        })
        assert session.contentcredential.search(name)[0]['Name'] == name
        session.product.discover_repo({
            'repo_type': 'Yum Repositories',
            'url': REPO_DISCOVERY_URL,
            'discovered_repos.repos': repo_name,
            'create_repo.product_type': 'New Product',
            'create_repo.product_content.product_name': product_name,
            'create_repo.product_content.gpg_key': name,
        })
        product_values = session.product.read(product_name)
        assert product_values['details']['gpg_key'] == name
        session.contentcredential.delete(name)
        product_values = session.product.read(product_name)
        assert product_values['details']['gpg_key'] == ''


@tier2
def test_positive_update_key_for_empty_product(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with empty (no repos) custom product then update the key

    :id: 519817c3-9b67-4859-8069-95987ebf9453

    :expectedresults: gpg key is associated with product before/after
        update

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product and associate GPGKey with it
    product = entities.Product(
        gpg_key=gpg_key,
        organization=module_org,
    ).create()
    with session:
        values = session.contentcredential.read(name)
        # Assert that GPGKey is associated with product
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        session.contentcredential.update(
            name,
            {'details.name': new_name},
        )
        values = session.contentcredential.read(new_name)
        # Assert that GPGKey is still associated with product
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name


@tier2
def test_positive_update_key_for_product_with_repo(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has one repository then update the key

    :id: 02cb0601-6aa2-4589-b61e-3d3785a7e100

    :expectedresults: gpg key is associated with product as well as with
        repository after update

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product and associate GPGKey with it
    product = entities.Product(
        gpg_key=gpg_key,
        organization=module_org,
    ).create()
    # Creates new repository without GPGKey
    repo = entities.Repository(
        product=product,
        url=FAKE_1_YUM_REPO,
    ).create()
    with session:
        session.contentcredential.update(
            name,
            {'details.name': new_name},
        )
        values = session.contentcredential.read(new_name)
        # Assert that GPGKey is still associated with product
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name


@tier2
@upgrade
def test_positive_update_key_for_product_with_repos(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    with custom product that has more than one repository then update the
    key

    :id: 3ca4d9ff-8032-4c2a-aed9-00ac2d1352d1

    :expectedresults: gpg key is associated with product as well as with
        repositories after update

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product and associate GPGKey with it
    product = entities.Product(
        gpg_key=gpg_key,
        organization=module_org,
    ).create()
    # Creates new repository_1 without GPGKey
    repo1 = entities.Repository(
        product=product,
        url=FAKE_1_YUM_REPO,
    ).create()
    # Creates new repository_2 without GPGKey
    repo2 = entities.Repository(
        product=product,
        url=FAKE_2_YUM_REPO,
    ).create()
    with session:
        session.contentcredential.update(
            name,
            {'details.name': new_name},
        )
        values = session.contentcredential.read(new_name)
        assert len(values['repositories']['table']) == 2
        assert (
            {repo1.name, repo2.name} ==
            set([
                repo['Name']
                for repo
                in values['repositories']['table']])
        )


@tier2
def test_positive_update_key_for_repo_from_product_with_repo(
        session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has one repository then update
    the key

    :id: 9827306e-76d7-4aef-8074-e97fc39d3bbb

    :expectedresults: gpg key is associated with repository after update
        but not with product.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product without selecting GPGkey
    product = entities.Product(
        organization=module_org,
    ).create()
    # Creates new repository with GPGKey
    repo = entities.Repository(
        gpg_key=gpg_key,
        product=product,
        url=FAKE_1_YUM_REPO,
    ).create()
    with session:
        session.contentcredential.update(
            name,
            {'details.name': new_name},
        )
        values = session.contentcredential.read(new_name)
        # Assert that after update GPGKey is not associated with product
        assert len(values['products']['table']) == 0
        # Assert that after update GPGKey is still associated
        # with repository
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name


@tier2
@upgrade
def test_positive_update_key_for_repo_from_product_with_repos(
        session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then associate it
    to repository from custom product that has more than one repository
    then update the key

    :id: d4f2fa16-860c-4ad5-b04f-8ce24b5618e9

    :expectedresults: gpg key is associated with single repository
        after update but not with product

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    gpg_key = entities.GPGKey(
        content=gpg_content,
        name=name,
        organization=module_org,
    ).create()
    # Creates new product without selecting GPGkey
    product = entities.Product(
        organization=module_org,
    ).create()
    # Creates new repository_1 with GPGKey
    repo1 = entities.Repository(
        url=FAKE_1_YUM_REPO,
        product=product,
        gpg_key=gpg_key,
    ).create()
    # Creates new repository_2 without GPGKey
    entities.Repository(
        product=product,
        url=FAKE_2_YUM_REPO,
    ).create()
    with session:
        session.contentcredential.update(
            name,
            {'details.name': new_name},
        )
        values = session.contentcredential.read(new_name)
        assert len(values['products']['table']) == 0
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo1.name


@tier2
def test_positive_delete_key_for_empty_product(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then
    associate it with empty (no repos) custom product then delete it

    :id: b9766403-61b2-4a88-a744-a25d53d577fb

    :expectedresults: gpg key is associated with product during creation
        but removed from product after deletion

    :CaseLevel: Integration
    """
    gpg_key = entities.GPGKey(
        content=gpg_content,
        organization=module_org,
    ).create()
    # Creates new product and associate GPGKey with it
    product = entities.Product(
        gpg_key=gpg_key,
        name=gen_string('alpha'),
        organization=module_org,
    ).create()
    with session:
        # Assert that GPGKey is associated with product
        gpg_values = session.contentcredential.read(gpg_key.name)
        assert len(gpg_values['products']['table']) == 1
        assert gpg_values['products']['table'][0]['Name'] == product.name
        product_values = session.product.read(product.name)
        assert product_values['details']['gpg_key'] == gpg_key.name
        session.contentcredential.delete(gpg_key.name)
        # Assert GPGKey isn't associated with product
        product_values = session.product.read(product.name)
        assert not product_values['details']['gpg_key']


@tier2
def test_positive_delete_key_for_product_with_repo(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then
    associate it with custom product that has one repository then delete it

    :id: 75057dd2-9083-47a8-bea7-4f073bdb667e

    :expectedresults: gpg key is associated with product as well as with
        the repository during creation but removed from product after
        deletion

    :CaseLevel: Integration
    """
    gpg_key = entities.GPGKey(
        content=gpg_content,
        organization=module_org,
    ).create()
    # Creates new product and associate GPGKey with it
    product = entities.Product(
        gpg_key=gpg_key,
        name=gen_string('alpha'),
        organization=module_org,
    ).create()
    # Creates new repository without GPGKey
    repo = entities.Repository(
        name=gen_string('alpha'),
        url=FAKE_1_YUM_REPO,
        product=product,
    ).create()
    with session:
        # Assert that GPGKey is associated with product
        values = session.contentcredential.read(gpg_key.name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name
        repo_values = session.repository.read(product.name, repo.name)
        assert repo_values['repo_content']['gpg_key'] == gpg_key.name
        session.contentcredential.delete(gpg_key.name)
        # Assert GPGKey isn't associated with product and repository
        product_values = session.product.read(product.name)
        assert not product_values['details']['gpg_key']
        repo_values = session.repository.read(product.name, repo.name)
        assert not repo_values['repo_content']['gpg_key']


@tier2
@upgrade
def test_positive_delete_key_for_product_with_repos(session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then
    associate it with custom product that has more than one repository then
    delete it

    :id: cb5d4efd-863a-4b8e-b1f8-a0771e90ff5e

    :expectedresults: gpg key is associated with product as well as with
        repositories during creation but removed from product after
        deletion

    :CaseLevel: Integration
    """
    gpg_key = entities.GPGKey(
        content=gpg_content,
        organization=module_org,
    ).create()
    # Creates new product and associate GPGKey with it
    product = entities.Product(
        gpg_key=gpg_key,
        name=gen_string('alpha'),
        organization=module_org,
    ).create()
    # Creates new repository_1 without GPGKey
    repo1 = entities.Repository(
        name=gen_string('alpha'),
        product=product,
        url=FAKE_1_YUM_REPO,
    ).create()
    # Creates new repository_2 without GPGKey
    repo2 = entities.Repository(
        name=gen_string('alpha'),
        product=product,
        url=FAKE_2_YUM_REPO,
    ).create()
    with session:
        # Assert that GPGKey is associated with product
        values = session.contentcredential.read(gpg_key.name)
        assert len(values['products']['table']) == 1
        assert values['products']['table'][0]['Name'] == product.name
        assert len(values['repositories']['table']) == 2
        assert (
            {repo1.name, repo2.name} ==
            set([
                repo['Name']
                for repo
                in values['repositories']['table']])
        )
        session.contentcredential.delete(gpg_key.name)
        # Assert GPGKey isn't associated with product and repositories
        product_values = session.product.read(product.name)
        assert not product_values['details']['gpg_key']
        for repo in [repo1, repo2]:
            repo_values = session.repository.read(product.name, repo.name)
            assert not repo_values['repo_content']['gpg_key']


@tier2
def test_positive_delete_key_for_repo_from_product_with_repo(
        session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then
    associate it to repository from custom product that has one repository
    then delete the key

    :id: 92ba492e-79af-48fe-84cb-763102b42fa7

    :expectedresults: gpg key is associated with single repository during
        creation but removed from repository after deletion

    :CaseLevel: Integration
    """
    gpg_key = entities.GPGKey(
        content=gpg_content,
        organization=module_org,
    ).create()
    # Creates new product without selecting GPGkey
    product = entities.Product(
        name=gen_string('alpha'),
        organization=module_org,
    ).create()
    # Creates new repository with GPGKey
    repo = entities.Repository(
        name=gen_string('alpha'),
        url=FAKE_1_YUM_REPO,
        product=product,
        gpg_key=gpg_key,
    ).create()
    with session:
        # Assert that GPGKey is associated with product
        values = session.contentcredential.read(gpg_key.name)
        assert len(values['products']['table']) == 0
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo.name
        repo_values = session.repository.read(product.name, repo.name)
        assert repo_values['repo_content']['gpg_key'] == gpg_key.name
        session.contentcredential.delete(gpg_key.name)
        # Assert GPGKey isn't associated with repository
        repo_values = session.repository.read(product.name, repo.name)
        assert not repo_values['repo_content']['gpg_key']


@tier2
@upgrade
def test_positive_delete_key_for_repo_from_product_with_repos(
        session, module_org, gpg_content):
    """Create gpg key with valid name and valid gpg key then
    associate it to repository from custom product that has more than
    one repository then delete the key

    :id: 5f204a44-bf7b-4a9c-9974-b701e0d38860

    :expectedresults: gpg key is associated with single repository but not
        with product during creation but removed from repository after
        deletion

    :BZ: 1461804

    :CaseLevel: Integration
    """
    # Creates New GPGKey
    gpg_key = entities.GPGKey(
        content=gpg_content,
        organization=module_org,
    ).create()
    # Creates new product without GPGKey association
    product = entities.Product(
        name=gen_string('alpha'),
        organization=module_org,
    ).create()
    # Creates new repository_1 with GPGKey association
    repo1 = entities.Repository(
        gpg_key=gpg_key,
        name=gen_string('alpha'),
        product=product,
        url=FAKE_1_YUM_REPO,
    ).create()
    repo2 = entities.Repository(
        name=gen_string('alpha'),
        product=product,
        url=FAKE_2_YUM_REPO,
        # notice that we're not making this repo point to the GPG key
    ).create()
    with session:
        # Assert that GPGKey is associated with product
        values = session.contentcredential.read(gpg_key.name)
        assert len(values['products']['table']) == 0
        assert len(values['repositories']['table']) == 1
        assert values['repositories']['table'][0]['Name'] == repo1.name
        repo_values = session.repository.read(product.name, repo1.name)
        assert repo_values['repo_content']['gpg_key'] == gpg_key.name
        repo_values = session.repository.read(product.name, repo2.name)
        assert not repo_values['repo_content']['gpg_key']
        session.contentcredential.delete(gpg_key.name)
        # Assert GPGKey isn't associated with repositories
        for repo in [repo1, repo2]:
            repo_values = session.repository.read(product.name, repo.name)
            assert not repo_values['repo_content']['gpg_key']
