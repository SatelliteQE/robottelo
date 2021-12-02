"""Test module for Repository UI

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint
from random import shuffle

import pytest
from airgun.session import Session
from nailgun import entities
from navmazing import NavigationTriesExceeded

from robottelo import manifests
from robottelo.api.utils import create_role_permissions
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DOWNLOAD_POLICIES
from robottelo.constants import INVALID_URL
from robottelo.constants import REPO_TYPE
from robottelo.constants import REPOSET
from robottelo.constants import VALID_GPG_KEY_BETA_FILE
from robottelo.constants import VALID_GPG_KEY_FILE
from robottelo.constants.repos import ANSIBLE_GALAXY
from robottelo.datafactory import gen_string
from robottelo.helpers import read_data_file
from robottelo.hosts import get_sat_version
from robottelo.products import SatelliteToolsRepository

# from robottelo.constants.repos import FEDORA26_OSTREE_REPO
# from robottelo.constants.repos import FEDORA27_OSTREE_REPO


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_prod(module_org):
    return entities.Product(organization=module_org).create()


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_create_in_different_orgs(session, module_org):
    """Create repository in two different orgs with same name

    :id: 019c2242-8802-4bae-82c5-accf8f793dbc

    :expectedresults: Repository is created successfully for both
        organizations

    :CaseLevel: Integration
    """
    repo_name = gen_string('alpha')
    org2 = entities.Organization().create()
    prod1 = entities.Product(organization=module_org).create()
    prod2 = entities.Product(organization=org2).create()
    with session:
        for org, prod in [[module_org, prod1], [org2, prod2]]:
            session.organization.select(org_name=org.name)
            session.repository.create(
                prod.name,
                {
                    'name': repo_name,
                    'label': org.label,
                    'repo_type': REPO_TYPE['yum'],
                    'repo_content.upstream_url': settings.repos.yum_1.url,
                },
            )
            assert session.repository.search(prod.name, repo_name)[0]['Name'] == repo_name
            values = session.repository.read(prod.name, repo_name)
            assert values['name'] == repo_name
            assert values['label'] == org.label


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_create_as_non_admin_user(module_org, test_name):
    """Create a repository as a non admin user

    :id: 582949c4-b95f-4d64-b7f0-fb80b3d2bd7e

    :expectedresults: Repository successfully created

    :BZ: 1426393

    :CaseLevel: Integration
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    repo_name = gen_string('alpha')
    user_permissions = {
        None: ['access_dashboard'],
        'Katello::Product': [
            'view_products',
            'create_products',
            'edit_products',
            'destroy_products',
            'sync_products',
        ],
    }
    role = entities.Role().create()
    create_role_permissions(role, user_permissions)
    entities.User(
        login=user_login,
        password=user_password,
        role=[role],
        admin=False,
        default_organization=module_org,
        organization=[module_org],
    ).create()
    product = entities.Product(organization=module_org).create()
    with Session(test_name, user=user_login, password=user_password) as session:
        # ensure that the created user is not a global admin user
        # check administer->organizations page
        with pytest.raises(NavigationTriesExceeded):
            session.organization.create({'name': gen_string('alpha'), 'label': gen_string('alpha')})
        session.repository.create(
            product.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
            },
        )
        assert session.repository.search(product.name, repo_name)[0]['Name'] == repo_name


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_create_yum_repo_same_url_different_orgs(session, module_prod):
    """Create two repos with the same URL in two different organizations.

    :id: f4cb00ed-6faf-4c79-9f66-76cd333299cb

    :expectedresults: Repositories are created and have equal number of packages.

    :CaseLevel: Integration
    """
    # Create first repository
    repo = entities.Repository(product=module_prod, url=settings.repos.yum_0.url).create()
    repo.sync()
    # Create second repository
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    new_repo = entities.Repository(product=product, url=settings.repos.yum_0.url).create()
    new_repo.sync()
    with session:
        # Check packages number in first repository
        assert session.repository.search(module_prod.name, repo.name)[0]['Name'] == repo.name
        repo = session.repository.read(module_prod.name, repo.name)
        repo_packages_count = repo['content_counts']['Packages']
        assert int(repo_packages_count) >= int('1')

        # Check packages number in first repository
        session.organization.select(org.name)
        assert session.repository.search(product.name, new_repo.name)[0]['Name'] == new_repo.name
        new_repo = session.repository.read(product.name, new_repo.name)
        new_repo_packages_count = new_repo['content_counts']['Packages']
        assert int(new_repo_packages_count) >= int('1')
        assert repo_packages_count == new_repo_packages_count


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_create_as_non_admin_user_with_cv_published(module_org, test_name):
    """Create a repository as a non admin user in a product that already
    contain a repository that is used in a published content view.

    :id: 407864eb-50b8-4bc8-bbc7-0e6f8136d89f

    :expectedresults: New repository successfully created by non admin user

    :BZ: 1447829

    :CaseLevel: Integration
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    repo_name = gen_string('alpha')
    user_permissions = {
        None: ['access_dashboard'],
        'Katello::Product': [
            'view_products',
            'create_products',
            'edit_products',
            'destroy_products',
            'sync_products',
        ],
    }
    role = entities.Role().create()
    create_role_permissions(role, user_permissions)
    entities.User(
        login=user_login,
        password=user_password,
        role=[role],
        admin=False,
        default_organization=module_org,
        organization=[module_org],
    ).create()
    prod = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=prod, url=settings.repos.yum_2.url).create()
    repo.sync()
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [repo]
    content_view = content_view.update(['repository'])
    content_view.publish()
    with Session(test_name, user_login, user_password) as session:
        # ensure that the created user is not a global admin user
        # check administer->users page
        with pytest.raises(NavigationTriesExceeded):
            pswd = gen_string('alphanumeric')
            session.user.create(
                {
                    'user.login': gen_string('alphanumeric'),
                    'user.auth': 'INTERNAL',
                    'user.password': pswd,
                    'user.confirm': pswd,
                }
            )
        # ensure that the created user has only the assigned permissions
        # check that host collections menu tab does not exist
        with pytest.raises(NavigationTriesExceeded):
            session.hostcollection.create({'name': gen_string('alphanumeric')})
        session.repository.create(
            prod.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
            },
        )
        assert session.repository.search(prod.name, repo.name)[0]['Name'] == repo.name


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.usefixtures('allow_repo_discovery')
def test_positive_discover_repo_via_existing_product(session, module_org):
    """Create repository via repo-discovery under existing product

    :id: 9181950c-a756-456f-a46a-059e7a2add3c

    :expectedresults: Repository is discovered and created

    :CaseLevel: Integration
    """
    repo_name = 'fakerepo01'
    product = entities.Product(organization=module_org).create()
    with session:
        session.organization.select(org_name=module_org.name)
        session.product.discover_repo(
            {
                'repo_type': 'Yum Repositories',
                'url': settings.repos.repo_discovery.url,
                'discovered_repos.repos': repo_name,
                'create_repo.product_type': 'Existing Product',
                'create_repo.product_content.product_name': product.name,
            }
        )
        assert repo_name in session.repository.search(product.name, repo_name)[0]['Name']


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.usefixtures('allow_repo_discovery')
def test_positive_discover_repo_via_new_product(session, module_org):
    """Create repository via repo discovery under new product

    :id: dc5281f8-1a8a-4a17-b746-728f344a1504

    :expectedresults: Repository is discovered and created

    :CaseLevel: Integration
    """
    product_name = gen_string('alpha')
    repo_name = 'fakerepo01'
    with session:
        session.organization.select(org_name=module_org.name)
        session.product.discover_repo(
            {
                'repo_type': 'Yum Repositories',
                'url': settings.repos.repo_discovery.url,
                'discovered_repos.repos': repo_name,
                'create_repo.product_type': 'New Product',
                'create_repo.product_content.product_name': product_name,
            }
        )
        assert session.product.search(product_name)[0]['Name'] == product_name
        assert repo_name in session.repository.search(product_name, repo_name)[0]['Name']


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.usefixtures('allow_repo_discovery')
def test_positive_discover_module_stream_repo_via_existing_product(session, module_org):
    """Create repository with module streams via repo-discovery under an existing product.

    :id: e7b9e2c4-7ecd-4cde-8f74-961fbac8919c

    :CaseLevel: Integration

    :BZ: 1676642

    :Steps:
        1. Create a product.
        2. From Content > Products, click on the Repo Discovery button.
        3. Enter a url containing a yum repository with module streams, e.g.,
           settings.repos.module_stream_1.url.
        4. Click the Discover button.

    :expectedresults: Repositories are discovered.
    """
    repo_name = gen_string('alpha')
    repo_label = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    with session:
        session.organization.select(org_name=module_org.name)
        session.product.discover_repo(
            {
                'repo_type': 'Yum Repositories',
                'url': settings.repos.module_stream_1.url,
                'discovered_repos.repos': "/",
                'create_repo.product_type': 'Existing Product',
                'create_repo.product_content.product_name': product.name,
                'create_repo.create_repos_table': [
                    {"Repository Name": repo_name, "Repository Label": repo_label}
                ],
            }
        )
        assert repo_name in session.repository.search(product.name, repo_name)[0]['Name']


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync_custom_repo_yum(session, module_org):
    """Create Custom yum repos and sync it via the repos page.

    :id: afa218f4-e97a-4240-a82a-e69538d837a1

    :expectedresults: Sync procedure for specific yum repository is successful

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(url=settings.repos.yum_1.url, product=product).create()
    with session:
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'
        sync_values = session.dashboard.read('SyncOverview')['syncs']
        assert len(sync_values) == 1
        assert sync_values[0]['Product'] == product.name
        assert sync_values[0]['Status'] == 'Syncing Complete.'
        assert 'ago' in sync_values[0]['Finished']


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_sync_custom_repo_docker(session, module_org):
    """Create Custom docker repos and sync it via the repos page.

    :id: 942e0b4f-3524-4f00-812d-bdad306f81de

    :expectedresults: Sync procedure for specific docker repository is
        successful

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=product, content_type=REPO_TYPE['docker']
    ).create()
    with session:
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_resync_custom_repo_after_invalid_update(session, module_org):
    """Create Custom yum repo and sync it via the repos page. Then try to
    change repo url to invalid one and re-sync that repository

    :id: 089b1e41-2017-429a-9c3f-b0291007a78f

    :customerscenario: true

    :expectedresults: Repository URL is not changed to invalid value and resync
        procedure for specific yum repository is successful

    :BZ: 1487173, 1262313

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(url=settings.repos.yum_1.url, product=product).create()
    with session:
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'
        with pytest.raises(AssertionError) as context:
            session.repository.update(
                product.name, repo.name, {'repo_content.upstream_url': INVALID_URL}
            )
        assert 'bad URI(is not URI?)' in str(context.value)
        assert session.repository.search(product.name, repo.name)[0]['Name'] == repo.name
        repo_values = session.repository.read(product.name, repo.name)
        assert repo_values['repo_content']['upstream_url'] == settings.repos.yum_1.url
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_resynchronize_rpm_repo(session, module_prod):
    """Check that repository content is resynced after packages were removed
    from repository

    :id: dc415563-c9b8-4e3c-9d2a-f4ac251c7d35

    :expectedresults: Repository has updated non-zero package count

    :CaseLevel: Integration

    :BZ: 1318004
    """
    repo = entities.Repository(
        url=settings.repos.yum_1.url, content_type=REPO_TYPE['yum'], product=module_prod
    ).create()
    with session:
        result = session.repository.synchronize(module_prod.name, repo.name)
        assert result['result'] == 'success'
        # Check packages count
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert int(repo_values['content_counts']['Packages']) >= 1
        # Remove packages
        session.repository.remove_all_packages(module_prod.name, repo.name)
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert repo_values['content_counts']['Packages'] == '0'
        # Sync it again
        result = session.repository.synchronize(module_prod.name, repo.name)
        assert result['result'] == 'success'
        # Check packages number
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert int(repo_values['content_counts']['Packages']) >= 1


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_end_to_end_custom_yum_crud(session, module_org, module_prod):
    """Perform end to end testing for custom yum repository

    :id: 8baf11c9-019e-4625-a549-ec4cd9312f75

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    repo_name = gen_string('alpha')
    checksum_type = 'sha256'
    new_repo_name = gen_string('alphanumeric')
    new_checksum_type = 'sha1'
    gpg_key = entities.GPGKey(
        content=read_data_file(VALID_GPG_KEY_FILE), organization=module_org
    ).create()
    new_gpg_key = entities.GPGKey(
        content=read_data_file(VALID_GPG_KEY_BETA_FILE), organization=module_org
    ).create()
    with session:
        session.repository.create(
            module_prod.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
                'repo_content.checksum_type': checksum_type,
                'repo_content.gpg_key': gpg_key.name,
                'repo_content.download_policy': DOWNLOAD_POLICIES['immediate'],
            },
        )
        assert session.repository.search(module_prod.name, repo_name)[0]['Name'] == repo_name
        repo_values = session.repository.read(module_prod.name, repo_name)
        assert repo_values['repo_content']['upstream_url'] == settings.repos.yum_1.url
        assert repo_values['repo_content']['metadata_type'] == checksum_type
        assert repo_values['repo_content']['gpg_key'] == gpg_key.name
        assert repo_values['repo_content']['download_policy'] == DOWNLOAD_POLICIES['immediate']
        session.repository.update(
            module_prod.name,
            repo_name,
            {
                'name': new_repo_name,
                'repo_content.upstream_url': settings.repos.yum_2.url,
                'repo_content.metadata_type': new_checksum_type,
                'repo_content.gpg_key': new_gpg_key.name,
                'repo_content.download_policy': DOWNLOAD_POLICIES['immediate'],
            },
        )
        assert not session.repository.search(module_prod.name, repo_name)
        repo_values = session.repository.read(module_prod.name, new_repo_name)
        assert repo_values['name'] == new_repo_name
        assert repo_values['repo_content']['upstream_url'] == settings.repos.yum_2.url
        assert repo_values['repo_content']['metadata_type'] == new_checksum_type
        assert repo_values['repo_content']['gpg_key'] == new_gpg_key.name
        assert repo_values['repo_content']['download_policy'] == DOWNLOAD_POLICIES['immediate']
        session.repository.delete(module_prod.name, new_repo_name)
        assert not session.repository.search(module_prod.name, new_repo_name)


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_end_to_end_custom_module_streams_crud(session, module_org, module_prod):
    """Perform end to end testing for custom module streams yum repository

    :id: ea0a58ae-b280-4bca-8f22-cbed73453604

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    repo_name = gen_string('alpha')
    with session:
        session.repository.create(
            module_prod.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.module_stream_1.url,
            },
        )
        assert session.repository.search(module_prod.name, repo_name)[0]['Name'] == repo_name
        repo_values = session.repository.read(module_prod.name, repo_name)
        assert repo_values['repo_content']['upstream_url'] == settings.repos.module_stream_1.url
        result = session.repository.synchronize(module_prod.name, repo_name)
        assert result['result'] == 'success'
        repo_values = session.repository.read(module_prod.name, repo_name)
        assert int(repo_values['content_counts']['Module Streams']) >= 5
        session.repository.update(
            module_prod.name,
            repo_name,
            {'repo_content.upstream_url': settings.repos.module_stream_0.url},
        )
        repo_values = session.repository.read(module_prod.name, repo_name)
        assert repo_values['repo_content']['upstream_url'] == settings.repos.module_stream_0.url
        session.repository.delete(module_prod.name, repo_name)
        assert not session.repository.search(module_prod.name, repo_name)


@pytest.mark.skip_if_open("BZ:1743271")
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_upstream_with_credentials(session, module_prod):
    """Create repository with upstream username and password update them and then clear them.

    :id: 141a95f3-79c4-48f8-9c95-e4b128045cb3

    :expectedresults:

        1. The custom repository is created with upstream credentials.
        2. The custom repository upstream credentials are updated.
        3. The credentials are cleared.

    :CaseLevel: Integration

    :CaseImportance: High

    :BZ: 1433481, 1743271
    """
    repo_name = gen_string('alpha')
    upstream_username = gen_string('alpha')
    upstream_password = gen_string('alphanumeric')
    new_upstream_username = gen_string('alpha')
    new_upstream_password = gen_string('alphanumeric')
    hidden_password = '*' * 8
    with session:
        session.repository.create(
            module_prod.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
                'repo_content.upstream_username': upstream_username,
                'repo_content.upstream_password': upstream_password,
            },
        )
        assert session.repository.search(module_prod.name, repo_name)[0]['Name'] == repo_name
        repo_values = session.repository.read(module_prod.name, repo_name)
        assert repo_values['repo_content']['upstream_authorization'] == '{} / {}'.format(
            upstream_username, hidden_password
        )
        session.repository.update(
            module_prod.name,
            repo_name,
            {
                'repo_content.upstream_authorization': dict(
                    username=new_upstream_username, password=new_upstream_password
                )
            },
        )
        repo_values = session.repository.read(module_prod.name, repo_name)
        assert repo_values['repo_content']['upstream_authorization'] == '{} / {}'.format(
            new_upstream_username, hidden_password
        )
        session.repository.update(
            module_prod.name, repo_name, {'repo_content.upstream_authorization': {}}
        )
        repo_values = session.repository.read(module_prod.name, repo_name)
        assert not repo_values['repo_content']['upstream_authorization']


# TODO: un-comment when OSTREE functionality is restored in Satellite 7.0
# @pytest.mark.tier2
# @pytest.mark.upgrade
# @pytest.mark.skipif(
#   (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
# def test_positive_end_to_end_custom_ostree_crud(session, module_prod):
#     """Perform end to end testing for custom ostree repository
#
#     :id: 603372aa-60de-44a8-b6c9-3f84c3bbdf05
#
#     :expectedresults: All expected CRUD actions finished successfully
#
#     :CaseLevel: Integration
#
#     :CaseImportance: High
#
#     :BZ: 1467722
#     """
#     repo_name = gen_string('alpha')
#     new_repo_name = gen_string('alphanumeric')
#     with session:
#         session.repository.create(
#             module_prod.name,
#             {
#                 'name': repo_name,
#                 'repo_type': REPO_TYPE['ostree'],
#                 'repo_content.upstream_url': FEDORA26_OSTREE_REPO,
#             },
#         )
#         assert session.repository.search(module_prod.name, repo_name)[0]['Name'] == repo_name
#         session.repository.update(
#             module_prod.name,
#             repo_name,
#             {'name': new_repo_name, 'repo_content.upstream_url': FEDORA27_OSTREE_REPO},
#         )
#         assert not session.repository.search(module_prod.name, repo_name)
#         repo_values = session.repository.read(module_prod.name, new_repo_name)
#         assert repo_values['name'] == new_repo_name
#         assert repo_values['repo_content']['upstream_url'] == FEDORA27_OSTREE_REPO
#         session.repository.delete(module_prod.name, new_repo_name)
#         assert not session.repository.search(module_prod.name, new_repo_name)


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_sync_ansible_collection_gallaxy_repo(session, module_prod):
    """Sync ansible collection repository from ansible gallaxy

    :id: f3212dbd-3b8a-49ad-ba03-58f059150c04

    :expectedresults: All content synced successfully

    :CaseLevel: Integration

    :CaseImportance: High

    """
    repo_name = f'gallaxy-{gen_string("alpha")}'
    requirements = '''
    ---
    collections:
    - name: theforeman.foreman
      version: "2.1.0"
    - name: theforeman.operations
      version: "0.1.0"
    '''
    with session:
        session.repository.create(
            module_prod.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['ansible_collection'],
                'repo_content.requirements': requirements,
                'repo_content.upstream_url': ANSIBLE_GALAXY,
            },
        )
        result = session.repository.synchronize(module_prod.name, repo_name)
        assert result['result'] == 'success'


@pytest.mark.tier2
def test_positive_reposet_disable(session):
    """Enable RH repo, sync it and then disable

    :id: de596c56-1327-49e8-86d5-a1ab907f26aa

    :expectedresults: RH repo was disabled

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    sat_tools_repo = SatelliteToolsRepository(distro=DISTRO_RHEL7, cdn=True)
    repository_name = sat_tools_repo.data['repository']
    with session:
        session.organization.select(org.name)
        session.redhatrepository.enable(
            sat_tools_repo.data['repository-set'],
            sat_tools_repo.data['arch'],
            version=sat_tools_repo.data['releasever'],
        )
        results = session.redhatrepository.search(f'name = "{repository_name}"', category='Enabled')
        assert results[0]['name'] == repository_name
        results = session.sync_status.synchronize(
            [
                (
                    sat_tools_repo.data['product'],
                    sat_tools_repo.data['releasever'],
                    sat_tools_repo.data['arch'],
                    repository_name,
                )
            ]
        )
        assert results and all([result == 'Syncing Complete.' for result in results])
        session.redhatrepository.disable(repository_name)
        assert not session.redhatrepository.search(
            f'name = "{repository_name}"', category='Enabled'
        )


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_reposet_disable_after_manifest_deleted(session):
    """Enable RH repo and sync it. Remove manifest and then disable
    repository

    :id: f22baa8e-80a4-4487-b1bd-f7265555d9a3

    :customerscenario: true

    :expectedresults: RH repo was disabled

    :BZ: 1344391

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    sub = entities.Subscription(organization=org)
    sat_tools_repo = SatelliteToolsRepository(distro=DISTRO_RHEL7, cdn=True)
    repository_name = sat_tools_repo.data['repository']
    repository_name_orphaned = f'{repository_name} (Orphaned)'
    with session:
        session.organization.select(org.name)
        # Enable RH repository
        session.redhatrepository.enable(
            sat_tools_repo.data['repository-set'],
            sat_tools_repo.data['arch'],
            version=sat_tools_repo.data['releasever'],
        )
        results = session.redhatrepository.search(f'name = "{repository_name}"', category='Enabled')
        assert results[0]['name'] == repository_name
        # Sync the repo and verify sync was successful
        results = session.sync_status.synchronize(
            [
                (
                    sat_tools_repo.data['product'],
                    sat_tools_repo.data['releasever'],
                    sat_tools_repo.data['arch'],
                    repository_name,
                )
            ]
        )
        assert results and all([result == 'Syncing Complete.' for result in results])
        # Delete manifest
        sub.delete_manifest(data={'organization_id': org.id})
        # Verify that the displayed repository name is correct
        results = session.redhatrepository.search(f'name = "{repository_name}"', category='Enabled')
        assert results[0]['name'] == repository_name_orphaned
        # Disable the orphaned repository
        session.redhatrepository.disable(repository_name, orphaned=True)
        assert not session.redhatrepository.search(
            f'name = "{repository_name}"', category='Enabled'
        )


@pytest.mark.tier2
def test_positive_delete_random_docker_repo(session, module_org):
    """Create Docker-type repositories on multiple products and
    delete a random repository from a random product.

    :id: a3dce435-c46e-41d7-a2f8-29421f7427f5

    :expectedresults: Random repository can be deleted from random product
        without altering the other products.

    :CaseLevel: Integration
    """
    entities_list = []
    products = [entities.Product(organization=module_org).create() for _ in range(randint(2, 5))]
    for product in products:
        repo = entities.Repository(
            url=CONTAINER_REGISTRY_HUB, product=product, content_type=REPO_TYPE['docker']
        ).create()
        entities_list.append((product.name, repo.name))
    with session:
        # Delete a random repository
        shuffle(entities_list)
        del_entity = entities_list.pop()
        session.repository.delete(*del_entity)
        # Check whether others repositories are not touched
        for product_name, repo_name in entities_list:
            assert session.repository.search(product_name, repo_name)[0]['Name'] == repo_name


@pytest.mark.tier2
def test_positive_recommended_repos(session, module_org):
    """list recommended repositories using
     On/Off 'Recommended Repositories' toggle.

    :id: 1ae197d5-88ba-4bb1-8ecf-4da5013403d7

    :expectedresults:

           1. Shows repositories as per On/Off 'Recommended Repositories'.
           2. Check last Satellite version Capsule/Tools repos do not exist.

    :CaseLevel: Integration

    :BZ: 1776108
    """
    manifests.upload_manifest_locked(module_org.id)
    with session:
        session.organization.select(module_org.name)
        rrepos_on = session.redhatrepository.read(recommended_repo='on')
        assert REPOSET['rhel7'] in [repo['name'] for repo in rrepos_on]
        v = get_sat_version()
        sat_version = f'{v.major}.{v.minor}'
        cap_tool_repos = [
            repo['name']
            for repo in rrepos_on
            if 'Tools' in repo['name'] or 'Capsule' in repo['name']
        ]
        cap_tools_repos = [repo for repo in cap_tool_repos if repo.split()[4] != sat_version]
        assert not cap_tools_repos, 'Tools/Capsule repos do not match with Satellite version'
        rrepos_off = session.redhatrepository.read(recommended_repo='off')
        assert len(rrepos_off) > len(rrepos_on)


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_upload_resigned_rpm():
    """Re-sign and re-upload an rpm that already exists in a repository.

    :id: 75416e72-701a-471c-a0ba-846cf881a1e4

    :expectedresults: New rpm is displayed, old rpm is not displayed in web UI.

    :BZ: 1883722

    :customerscenario: true

    :Steps:
        1. Buld or prepare an unsigned rpm.
        2. Create a gpg key.
        3. Use the gpg key to sign the rpm with sha1.
        4. Create an rpm repository in the Satellite.
        5. Upload the sha1 signed rpm to the repository.
        6. Use the gpg key to re-sign the rpm with sha2 again.
        7. Upload the sha2 signed rpm to the repository.

    :expectedresults: New rpm is displayed, old rpm is not displayed in web UI.
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_remove_srpm_change_checksum():
    """Re-sync a repository that has had an srpm removed and repodata checksum type changed from
    sha1 to sha256.

    :id: 8bd50cd6-34ac-452d-8654-2792a2613921

    :customerscenario: true

    :BZ: 1850914

    :Steps:
        1. Sync a repository that contains rpms and srpms and uses sha1 repodata.
        2. Re-sync the repository after an srpm has been removed and its repodata regenerated
           using sha256.

    :expectedresults: Repository re-syncs successfully, and the removed srpm is no longer visible
        in the UI.
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_positive_repo_discovery_change_ssl():
    """Verify that repository created via repo discovery has expected Verify SSL value.

    :id: 4c3417c8-1aca-4091-bf56-1491e55e4498

    :customerscenario: true

    :BZ: 1789848

    :Steps:
        1. Navigate to Content > Products > click on 'Repo Discovery'.
        2. Set the repository type to 'Yum Repositories'.
        3. Enter an upstream URL to discover and click on 'Discover'.
        4. Select the discovered repository and click on 'Create Selected'.
        5. Select the product or create a product.
        6. Un-check the box for 'Verify SSL'.
        7. Enter a repo name and click on 'Run Repository Creation'.

    :expectedresults: New repository has 'Verify SSL' set to False.
    """
    pass


@pytest.mark.tier1
def test_positive_remove_credentials(session, function_product, function_org, function_location):
    """User can remove the upstream_username and upstream_password from a repository in the UI.

    :id: 1d4fc498-1e89-41ae-830f-d239ce389831

    :BZ: 1802158

    :customerscenario: true

    :Steps:
        1. Create a custom repository, with a repositority type of 'yum' and an upstream username
        and password.
        3. Remove the saved credentials by clicking the delete icon next to the 'Upstream
        Authorization' field in the repository details page.

    :expectedresults: 'Upstream Authorization' value is cleared.
    """
    repo_name = gen_string('alpha')
    upstream_username = gen_string('alpha')
    upstream_password = gen_string('alphanumeric')
    with session:
        session.organization.select(org_name=function_org.name)
        session.location.select(loc_name=function_location.name)
        session.repository.create(
            function_product.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': settings.repos.yum_1.url,
                'repo_content.upstream_username': upstream_username,
                'repo_content.upstream_password': upstream_password,
            },
        )
        session.repository.update(
            function_product.name,
            repo_name,
            {'repo_content.upstream_authorization': False},
        )
        repo_values = session.repository.read(function_product.name, repo_name)
        assert not repo_values['repo_content']['upstream_authorization']


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_sync_status_repo_display():
    """Red Hat repositories displayed correctly on Sync Status page.

    :id: a9798f9d-ceab-4caf-ab2f-86aa0b7bad8e

    :BZ: 1819794

    :customerscenario: true

    :Steps:
        1. Import manifest and enable RHEL 8 repositories.
        2. Navigate to Content > Sync Status.

    :expectedresults: Repositories should be grouped correctly by arch on Sync Status page.
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_search_enabled_kickstart_repos():
    """Red Hat Repositories should show enabled repositories list with search criteria
    'Enabled/Both' and type 'Kickstart'.

    :id: e85a27c1-2600-4f60-af79-c56d49902588

    :customerscenario: true

    :BZ: 1724807, 1829817

    :Steps:
        1. Import a manifest
        2. Navigate to Content > Red Hat Repositories, and enable some kickstart repositories.
        3. In the search bar on the right side, select 'Enabled/Both'.
        4. In the filter below the search button, change 'rpm' to 'kickstart'.
        5. Click on 'Search'

    :expectedresults: Enabled repositories should show the list of enabled kickstart repositories.
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_rpm_metadata_display():
    """RPM dependencies should display correctly in UI.

    :id: 308f2f4e-4382-48c9-b606-2c827f91d280

    :customerscenario: true

    :BZ: 1904369

    :Steps:
        1. Enable and sync a repository, e.g.,
           'Red Hat Satellite Tools 6.9 for RHEL 7 Server RPMs x86_64'.
        2. Navigate to Content > Packages > click on a package in the repository (e.g.,
           'tfm-rubygem-hammer_cli_foreman_tasks-0.0.15-1.el7sat.noarch') > Dependencies.
        3. Verify that the displayed required and provided capabilities displayed match those of
           the rpm, e.g.,
           tfm-rubygem(hammer_cli_foreman) > 0.0.1.1
           tfm-rubygem(hammer_cli_foreman) < 0.3.0.0
           tfm-rubygem(powerbar) < 0.3.0
           tfm-rubygem(powerbar) >= 0.1.0.11

    :expectedresults: Comparison operators (less than, greater than, etc.) should display
        correctly.
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_select_org_in_any_context():
    """When attempting to check Sync Status from 'Any Context' the user
    should be properly routed away from the 'Select An Organization' page

    :id: 6bd94c3d-1a8b-494b-b1ae-40c17532f8e5

    :customerscenario: true

    :BZ: 1860957

    :Steps:
        1. Set "Any Organization" and "Any Location" on top
        2. Click on Content -> "Sync Status"
        3. "Select an Organization" page will come up.
        4. Select organization in dropdown and press Select

    :expectedresults: After pressing Select, user is navigated to Sync Status page and
        the correct organization should be selected.
    """
    pass
