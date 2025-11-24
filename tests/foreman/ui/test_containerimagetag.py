"""WebUI tests for the Docker Image Tags feature.

:Requirement: Docker Image Tag

:CaseAutomation: Automated

:CaseComponent: ContainerImageManagement

:team: Artemis

:CaseImportance: High

"""

from fauxfactory import gen_alpha
from box import Box
import pytest

from robottelo.config import settings
from robottelo.constants import (
    BOOTABLE_REPO,
    DEFAULT_CV,
    ENVIRONMENT,
    FLATPAK_REMOTES,
    FLATPAK_RHEL_RELEASE_VER,
    REPO_TYPE,
)


@pytest.fixture(scope="module")
def module_org(module_target_sat):
    return module_target_sat.api.Organization().create()


@pytest.fixture(scope="module")
def module_product(module_org, module_target_sat):
    return module_target_sat.api.Product(organization=module_org).create()


@pytest.fixture(scope="module")
def module_repository(module_product, module_target_sat):
    repo = module_target_sat.api.Repository(
        content_type=REPO_TYPE['docker'],
        docker_upstream_name=settings.container.upstream_name,
        product=module_product,
        url=settings.container.registry_hub,
    ).create()
    repo.sync(timeout=1440)
    return repo


@pytest.fixture(scope="module")
def synced_container_and_flatpak_repos(module_org, module_product, module_target_sat):
    container_repos = []
    container_upstream_names = [
        settings.container.upstream_name,
        'busybox',
        'alpine',
    ]

    for upstream_name in container_upstream_names:
        repo = module_target_sat.api.Repository(
            content_type=REPO_TYPE['docker'],
            docker_upstream_name=upstream_name,
            product=module_product,
            url=settings.container.registry_hub,
        ).create()
        repo.sync(timeout=1800)
        repo = repo.read()
        container_repos.append(repo)

    flatpak_repos = []
    flatpak_remote = module_target_sat.cli.FlatpakRemote().create(
        {
            'organization-id': module_org.id,
            'url': FLATPAK_REMOTES['Fedora']['url'],
            'name': 'test_flatpak_remote',
        }
    )

    module_target_sat.cli.FlatpakRemote().scan({'id': flatpak_remote['id']})
    scanned_repos = module_target_sat.cli.FlatpakRemote().repository_list(
        {'flatpak-remote-id': flatpak_remote['id']}
    )

    ver = FLATPAK_RHEL_RELEASE_VER
    repo_names = [f'rhel{ver}/firefox-flatpak', f'rhel{ver}/flatpak-runtime']
    remote_repos = [r for r in scanned_repos if r['name'] in repo_names]

    if len(remote_repos) > 0:
        for repo in remote_repos[:2]:
            module_target_sat.cli.FlatpakRemote().repository_mirror(
                {
                    'flatpak-remote-id': flatpak_remote['id'],
                    'id': repo['id'],
                    'product-id': module_product.id,
                }
            )

        local_repos = [
            r
            for r in module_target_sat.cli.Repository.list({'product-id': module_product.id})
            if r['name'] in repo_names
        ]

        for repo in local_repos:
            module_target_sat.cli.Repository.update(
                {'id': repo['id'], 'download-policy': 'immediate'}
            )
            module_target_sat.cli.Repository.synchronize({'id': repo['id']})
            synced_repo = module_target_sat.cli.Repository.info({'id': repo['id']})
            flatpak_repos.append(synced_repo)

    return Box(container_repos=container_repos, flatpak_repos=flatpak_repos)


def test_positive_search(session, module_org, module_product, module_repository):
    """Search for a docker image tag and reads details of it

    :id: 28640396-c44d-4487-9d6d-3d5f2ed599d7

    :expectedresults: The docker image tag can be searched and found,
        details are read

    :BZ: 2009069, 2242515
    """
    with session:
        session.organization.select(org_name=module_org.name)
        search = session.containerimagetag.search('latest')
        assert module_product.name in [i['Product Name'] for i in search]
        values = session.containerimagetag.read('latest')
        assert module_product.name == values['details']['product']
        assert values['lce']['table'][0]['Environment'] == ENVIRONMENT
        repo_line = next(
            (item for item in values['repos']['table'] if item['Name'] == module_repository.name),
            None,
        )
        assert module_product.name == repo_line['Product']
        assert repo_line['Content View'] == DEFAULT_CV
        assert 'Success' in repo_line['Last Sync']


@pytest.mark.parametrize('setting_update', ['lab_features=True'], indirect=True)
def test_synced_repo_labels_annotations_read(
    function_org, function_product, setting_update, target_sat
):
    """Create and sync a container repository, and read it's labels and annotations modal

    :id: 67b4a316-d476-4bfd-84b3-06d182771816

    :parametrized: yes

    :steps:
        1. Sync a docker Repository
        2. Read the docker_manifest_list and docker_manifests information
        3. Navigate to the Container Images feature.
        4. Read the manifest labels and annotations modal for a child manifest.

    :expectedresults: The child manifest details are listed correctly.

    :Verifies: SAT-38203
    """
    repo = target_sat.api.Repository(
        name=gen_alpha(),
        content_type='docker',
        docker_upstream_name=BOOTABLE_REPO['upstream_name'],
        product=function_product,
        url=settings.container.pulp.registry_hub,
    ).create()
    repo.sync()
    repo = repo.read()
    assert repo.content_counts['docker_manifest'] > 0
    manifest_list = target_sat.api.Repository(id=repo.id).docker_manifest_lists()['results'][0]
    manifest = target_sat.api.Repository(id=repo.id).docker_manifests()['results'][0]
    label_list = []
    annotation_list = []
    for label in manifest['labels'].items():
        label_list.append(f'{label[0]}={label[1]}')
    for annotation in manifest['annotations'].items():
        annotation_list.append(f'{annotation[0]}={annotation[1]}')

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        # Verify manifest list modal info
        manifest_modal_info = session.containerimages.read_labels_and_annotations(
            manifest_list['tags'][0]['name'], manifest['digest']
        )
        # Verify info in the Modal
        assert (
            manifest_modal_info['label_annotation_count']
            == f"{(len(label_list) + len(annotation_list))} labels and annotations"
        )
        assert manifest['digest'] == manifest_modal_info['sha_hash']
        for label in label_list:
            assert label in manifest_modal_info['labels_and_annotations']
        for annotation in annotation_list:
            assert annotation in manifest_modal_info['labels_and_annotations']


def test_synced_container_pullable_paths(function_org, function_product, target_sat):
    """Create and sync a container repository, and read it's pullable paths information

    :id: 1df694e6-c2b0-4d85-82c4-d4d43c7c2fc3

    :steps:
        1. Sync a docker Repository
        2. Read the docker_manifest_list information
        3. Navigate to the Container Images table.
        4. Read the pullable paths information for a manifest list in the Synced Containers table, through the modal.
        5. Read the pullable paths information through the and Manifest Details page.

    :expectedresults: The pullable path information is correct, and consistent, across both locations.

    :Verifies: SAT-39827
    """
    repo = target_sat.api.Repository(
        name=gen_alpha(),
        content_type='docker',
        docker_upstream_name=BOOTABLE_REPO['upstream_name'],
        product=function_product,
        url=settings.container.pulp.registry_hub,
    ).create()
    repo.sync()
    repo = repo.read()
    assert repo.content_counts['docker_manifest'] > 0
    manifest_list = target_sat.api.Repository(id=repo.id).docker_manifest_lists()['results'][0]
    pullable_path = f"{repo.full_path}:{manifest_list['tags'][0]['name']}"
    default_cv_version = function_org.default_content_view.read().version[0].read()
    lce = default_cv_version.environment[0].read()

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        # Verify manifest list information
        pullable_paths_info = session.containerimages.read_pullable_paths(
            manifest_list['tags'][0]['name'], manifest_list['digest']
        )
        assert pullable_path == pullable_paths_info['Pullable path']
        assert repo.name == pullable_paths_info['Repository']
        assert lce.name == pullable_paths_info['Environment']
        assert default_cv_version.name == pullable_paths_info['Content view']


def test_positive_verify_synced_container_image_tags(
    session, synced_container_and_flatpak_repos, module_org, module_product, module_target_sat
):
    """Verify synced container image tags

    :id: 3116c317-edf9-48a0-9b3b-31b52c18f036

    :expectedresults: The container image tags are synced and visible in the Container Images page
    """
    # Update lab_features setting to true
    setting_entity = module_target_sat.api.Setting().search(query={'search': 'name=lab_features'})[
        0
    ]
    original_value = setting_entity.value
    setting_entity.value = 'true'
    setting_entity.update({'value'})

    try:
        with session:
            session.organization.select(org_name=module_org.name)
            # Navigate to Container Images page
            table_data = session.containerimages.read_synced_table()
            # Verify that the table contains data
            assert len(table_data) > 0, 'Container images table should contain synced images'
            # Verify that synced container images are present in the table
            # Check that at least one entry has the correct product name
            product_names = [row.get('Product', '') for row in table_data]
            assert module_product.name in product_names, (
                f'Product {module_product.name} should be present in the synced container images table'
            )
            # Verify table structure - check that expected columns are present
            if table_data:
                expected_columns = ['Tag', 'Manifest digest', 'Type', 'Product']
                for column in expected_columns:
                    assert column in table_data[0], f'Table should contain {column} column'

    finally:
        # Restore original setting value
        setting_entity.value = original_value
        setting_entity.update({'value'})