"""Test class for InterSatellite Sync

:Requirement: Satellitesync

:CaseAutomation: Automated

:CaseComponent: InterSatelliteSync

:team: Phoenix-content

:CaseImportance: High

"""

from datetime import UTC, datetime
import os
from time import sleep

from fauxfactory import gen_string
from manifester import Manifester
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_CV,
    ENVIRONMENT,
    EXPORT_LIBRARY_NAME,
    FLATPAK_RHEL_RELEASE_VER,
    PULP_EXPORT_DIR,
    PULP_IMPORT_DIR,
    REPO_TYPE,
    REPOS,
    DataFile,
)
from robottelo.constants.repos import ANSIBLE_GALAXY
from robottelo.exceptions import CLIReturnCodeError


@pytest.fixture(scope='class')
def config_export_import_settings(module_target_sat):
    """Check settings and set download policy for export.  Reset to original state after import"""
    download_policy_value = module_target_sat.cli.Settings.info(
        {'name': 'default_download_policy'}
    )['value']
    rh_download_policy_value = module_target_sat.cli.Settings.info(
        {'name': 'default_redhat_download_policy'}
    )['value']
    subs_conn_enabled_value = module_target_sat.cli.Settings.info(
        {'name': 'subscription_connection_enabled'}
    )['value']
    module_target_sat.cli.Settings.set(
        {'name': 'default_redhat_download_policy', 'value': 'immediate'}
    )
    yield
    module_target_sat.cli.Settings.set(
        {'name': 'default_download_policy', 'value': download_policy_value}
    )
    module_target_sat.cli.Settings.set(
        {'name': 'default_redhat_download_policy', 'value': rh_download_policy_value}
    )
    module_target_sat.cli.Settings.set(
        {'name': 'subscription_connection_enabled', 'value': subs_conn_enabled_value}
    )


@pytest.fixture
def export_import_cleanup_function(target_sat, function_org):
    """Deletes export/import dirs of function org"""
    yield
    target_sat.execute(
        f'rm -rf {PULP_EXPORT_DIR}/{function_org.name} {PULP_IMPORT_DIR}/{function_org.name}'
    )


@pytest.fixture  # perform the cleanup after each testcase of a module
def export_import_cleanup_module(target_sat, module_org):
    """Deletes export/import dirs of module_org"""
    yield
    target_sat.execute(
        f'rm -rf {PULP_EXPORT_DIR}/{module_org.name} {PULP_IMPORT_DIR}/{module_org.name}'
    )


@pytest.fixture
def function_import_org(target_sat):
    """Creates an Organization for content import."""
    return target_sat.api.Organization().create()


@pytest.fixture
def function_import_org_with_manifest(target_sat, function_import_org):
    """Creates and sets an Organization with a brand-new manifest for content import."""
    with Manifester(manifest_category=settings.manifest.golden_ticket) as manifest:
        target_sat.upload_manifest(function_import_org.id, manifest.content)
    return function_import_org


@pytest.fixture(scope='module')
def module_synced_custom_repo(module_target_sat, module_org, module_product):
    repo = module_target_sat.cli_factory.make_repository(
        {
            'content-type': 'yum',
            'download-policy': 'immediate',
            'organization-id': module_org.id,
            'product-id': module_product.id,
        }
    )
    module_target_sat.cli.Repository.synchronize({'id': repo['id']})
    return repo


@pytest.fixture
def function_synced_custom_repo(target_sat, function_org, function_product):
    repo = target_sat.cli_factory.make_repository(
        {
            'content-type': 'yum',
            'download-policy': 'immediate',
            'organization-id': function_org.id,
            'product-id': function_product.id,
        }
    )
    target_sat.cli.Repository.synchronize({'id': repo['id']})
    return repo


@pytest.fixture
def function_synced_rh_repo(request, target_sat, function_sca_manifest_org):
    """Enable and synchronize RH repo with immediate policy"""
    repo_dict = (
        REPOS['kickstart'][request.param.replace('kickstart', '')[1:]]
        if 'kickstart' in request.param
        else REPOS[request.param]
    )
    target_sat.cli.RepositorySet.enable(
        {
            'organization-id': function_sca_manifest_org.id,
            'name': repo_dict['reposet'],
            'product': repo_dict['product'],
            'releasever': repo_dict.get('releasever', None) or repo_dict.get('version', None),
            'basearch': DEFAULT_ARCHITECTURE,
        }
    )
    repo = target_sat.cli.Repository.info(
        {
            'organization-id': function_sca_manifest_org.id,
            'name': repo_dict['name'],
            'product': repo_dict['product'],
        }
    )
    # Update the download policy to 'immediate' and sync
    target_sat.cli.Repository.update({'download-policy': 'immediate', 'id': repo['id']})
    target_sat.cli.Repository.synchronize({'id': repo['id']}, timeout='2h')
    return target_sat.cli.Repository.info(
        {
            'organization-id': function_sca_manifest_org.id,
            'name': repo_dict['name'],
            'product': repo_dict['product'],
        }
    )


@pytest.fixture
def function_synced_file_repo(target_sat, function_org, function_product):
    repo = target_sat.cli_factory.make_repository(
        {
            'organization-id': function_org.id,
            'product-id': function_product.id,
            'content-type': 'file',
            'url': settings.repos.file_type_repo.url,
        }
    )
    target_sat.cli.Repository.synchronize({'id': repo['id']})
    return repo


@pytest.fixture
def function_synced_large_file_repo(target_sat, function_org, function_product):
    repo = target_sat.cli_factory.make_repository(
        {
            'organization-id': function_org.id,
            'product-id': function_product.id,
            'content-type': 'file',
            'url': settings.repos.large_file_type_repo.url,
        }
    )
    target_sat.cli.Repository.synchronize({'id': repo['id']}, timeout='2h')
    return repo


@pytest.fixture
def function_synced_docker_repo(target_sat, function_org, function_product):
    repo = target_sat.cli_factory.make_repository(
        {
            'organization-id': function_org.id,
            'product-id': function_product.id,
            'content-type': REPO_TYPE['docker'],
            'download-policy': 'immediate',
            'url': settings.container.registry_hub,
            'docker-upstream-name': settings.container.upstream_name,
        }
    )
    target_sat.cli.Repository.synchronize({'id': repo['id']})
    return repo


@pytest.fixture
def function_synced_flatpak_repos(
    target_sat, function_org, function_flatpak_remote, function_product
):
    ver = FLATPAK_RHEL_RELEASE_VER
    repo_names = [f'rhel{ver}/firefox-flatpak', f'rhel{ver}/flatpak-runtime']  # runtime=dependency
    remote_repos = [r for r in function_flatpak_remote.repos if r['name'] in repo_names]
    for repo in remote_repos:
        target_sat.cli.FlatpakRemote().repository_mirror(
            {
                'flatpak-remote-id': function_flatpak_remote.remote['id'],
                'id': repo['id'],  # or by name
                'product-id': function_product.id,
            }
        )

    local_repos = [
        r
        for r in target_sat.cli.Repository.list({'product-id': function_product.id})
        if r['name'] in repo_names
    ]
    for repo in local_repos:
        target_sat.cli.Repository.update({'id': repo['id'], 'download-policy': 'immediate'})
        target_sat.cli.Repository.synchronize({'id': repo['id']})

    return [target_sat.cli.Repository.info({'id': repo['id']}) for repo in local_repos]


@pytest.fixture
def function_synced_AC_repo(target_sat, function_org, function_product):
    repo = target_sat.cli_factory.make_repository(
        {
            'organization-id': function_org.id,
            'product-id': function_product.id,
            'content-type': 'ansible_collection',
            'url': ANSIBLE_GALAXY,
            'ansible-collection-requirements': '{collections: [ \
                    { name: theforeman.foreman, version: "2.1.0" }, \
                    { name: theforeman.operations, version: "0.1.0"} ]}',
        }
    )
    target_sat.cli.Repository.synchronize({'id': repo['id']})
    return repo


@pytest.fixture
def function_restrictive_umask(target_sat):
    new_mask = '077'
    mask_override = f'umask {new_mask} # {gen_string("alpha")}'
    target_sat.execute(f'echo "{mask_override}" >> /etc/bashrc')
    assert new_mask in target_sat.execute('umask').stdout, f'Failed to set new umask to {new_mask}'
    yield
    target_sat.execute(f'sed -i "/{mask_override}/d" /etc/bashrc')


@pytest.fixture
def function_exporter_user(target_sat, function_org):
    password = gen_string('alphanumeric')
    role = target_sat.api.Role().search(query={'search': 'name="Content Exporter"'})[0]
    user = target_sat.api.User(
        login=gen_string('alpha'),
        password=password,
        admin=False,
        role=[role],
        organization=[function_org],
    ).create()
    user.password = password
    yield user
    user.delete()


@pytest.fixture(scope='module')
def module_import_sat(module_satellite_host):
    """Provides a separate Satellite instance for imports."""
    return module_satellite_host


@pytest.fixture
def function_import_org_at_isat(module_import_sat):
    """Creates an Organization for content import."""
    return module_import_sat.api.Organization().create()


@pytest.fixture
def complete_export_import_cleanup(target_sat, module_import_sat):
    """Deletes all export/import dirs at both, export and import, Satellites."""
    yield
    target_sat.execute(f'rm -rf {PULP_EXPORT_DIR}* {PULP_IMPORT_DIR}*')
    module_import_sat.execute(f'rm -rf {PULP_EXPORT_DIR}* {PULP_IMPORT_DIR}*')


@pytest.mark.run_in_one_thread
class TestRepositoryExport:
    """Tests for exporting a repository via CLI"""

    def test_positive_export_version_custom_repo(
        self, target_sat, export_import_cleanup_module, module_org, module_synced_custom_repo
    ):
        """Export custom repo via complete and incremental CV version export.

        :id: 1b58dca7-c8bb-4893-a306-5882826da559

        :setup:
            1. Product with synced custom repository.

        :steps:
            1. Create a CV, add the product and publish it.
            2. Export complete CV version.
            3. Publish new CV version.
            4. Export incremental CV version.

        :expectedresults:
            1. Complete export succeeds, exported files are present on satellite machine.
            2. Incremental export succeeds, exported files are present on satellite machine.

        :BZ: 1944733

        :customerscenario: true
        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': module_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_org.id,
                'repository-id': module_synced_custom_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''
        # Export complete and check the export directory
        target_sat.cli.ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': module_org.id}
        )
        assert '1.0' in target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR)
        # Publish new CV version, export incremental and check the export directory
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 2
        cvv = max(cv['versions'], key=lambda x: int(x['id']))
        target_sat.cli.ContentExport.incrementalVersion(
            {'id': cvv['id'], 'organization-id': module_org.id}
        )
        assert '2.0' in target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR)

    def test_positive_export_library_custom_repo(
        self,
        target_sat,
        export_import_cleanup_function,
        function_org,
        function_synced_custom_repo,
        function_exporter_user,
    ):
        """Export custom repo via complete and incremental library export using a non-admin user
        with the "Content Exporter" role.

        :id: ba8dc7f3-55c2-4120-ac76-cc825ef0abb8

        :setup:
            1. Product with synced custom repository.
            2. Non-admin user with the "Content Exporter" role.

        :steps:
            1. Create a CV, add the product and publish it.
            2. Export complete library.
            3. Export incremental library.

        :expectedresults:
            1. Complete export succeeds, exported files are present on satellite machine.
            2. Incremental export succeeds, exported files are present on satellite machine.

        :Verifies: SAT-24884

        :customerscenario: true
        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': function_synced_custom_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        # Export complete and check the export directory
        target_sat.cli.ContentExport.with_user(
            username=function_exporter_user.login, password=function_exporter_user.password
        ).completeLibrary({'organization-id': function_org.id})
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)
        # Export incremental and check the export directory
        target_sat.cli.ContentExport.with_user(
            username=function_exporter_user.login, password=function_exporter_user.password
        ).incrementalLibrary({'organization-id': function_org.id})
        assert '2.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_export_complete_library_rh_repo(
        self,
        target_sat,
        export_import_cleanup_function,
        function_sca_manifest_org,
        function_synced_rh_repo,
    ):
        """Export RedHat repo via complete library

        :id: ffae18bf-6536-4f11-8002-7bf1568bf7f1

        :parametrized: yes

        :setup:
            1. Enabled and synced RH repository.

        :steps:
            1. Create CV with the RH repo and publish.
            2. Export CV version contents to a directory.

        :expectedresults:
            1. Repository was successfully exported, exported files are present on satellite machine

        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_sca_manifest_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_rh_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export content view
        target_sat.cli.ContentExport.completeLibrary(
            {'organization-id': function_sca_manifest_org.id}
        )
        # Verify export directory is not empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) != ''

    @pytest.mark.upgrade
    def test_positive_export_repository_docker(
        self, target_sat, export_import_cleanup_function, function_org, function_synced_docker_repo
    ):
        """Export docker repo via complete and incremental repository.

        :id: 3c666ffd-d287-4006-b3a0-66d892fe4250

        :setup:
            1. Have a synchronized docker-type repo with immediate download policy.

        :steps:
            1. Export complete repository.
            2. Export incremental repository.

        :expectedresults:
            1. Export path is created (with expected files) for complete export.
            2. Export path is created (with expected files) for incremental export.

        :BZ: 1650468

        :customerscenario: true
        """
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        # Export complete and check the export directory
        target_sat.cli.ContentExport.completeRepository({'id': function_synced_docker_repo['id']})
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)
        # Export incremental and check the export directory
        target_sat.cli.ContentExport.incrementalRepository(
            {'id': function_synced_docker_repo['id']}
        )
        assert '2.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

    @pytest.mark.upgrade
    def test_positive_export_version_docker(
        self, target_sat, export_import_cleanup_function, function_org, function_synced_docker_repo
    ):
        """Export CV with docker repo via complete and incremental version.

        :id: ddff4560-cd39-4ecc-a538-09aad9f64a73

        :setup:
            1. Have a synchronized docker-type repo with immediate download policy.

        :steps:
            1. Create a CV, add the docker repository and publish it.
            2. Export complete version of the CV.
            3. Publish new version of the CV.
            4. Export incremental version of the CV.

        :expectedresults:
            1. Export path is created (with expected files) for complete CVV export.
            2. Export path is created (with expected files) for incremental CVV export.

        :BZ: 1650468

        :customerscenario: true
        """
        # Create CV and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': function_synced_docker_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        # Export complete and check the export directory
        target_sat.cli.ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_org.id}
        )
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)
        # Publish new CVV, export incremental and check the export directory
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 2
        cvv = max(cv['versions'], key=lambda x: int(x['id']))
        target_sat.cli.ContentExport.incrementalVersion(
            {'id': cvv['id'], 'organization-id': function_org.id}
        )
        assert '2.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)


@pytest.fixture(scope='class')
def class_export_entities(module_org, module_target_sat):
    """Setup custom repos for export"""
    exporting_prod_name = gen_string('alpha')
    product = module_target_sat.cli_factory.make_product(
        {'organization-id': module_org.id, 'name': exporting_prod_name}
    )
    exporting_repo_name = gen_string('alpha')
    exporting_repo = module_target_sat.cli_factory.make_repository(
        {
            'name': exporting_repo_name,
            'mirroring-policy': 'mirror_content_only',
            'download-policy': 'immediate',
            'product-id': product['id'],
        }
    )
    module_target_sat.cli.Repository.synchronize({'id': exporting_repo['id']})
    exporting_cv_name = gen_string('alpha')
    exporting_cv, exporting_cvv_id = _create_cv(
        exporting_cv_name, exporting_repo, module_org, module_target_sat
    )
    return {
        'exporting_org': module_org,
        'exporting_prod_name': exporting_prod_name,
        'exporting_repo_name': exporting_repo_name,
        'exporting_repo': exporting_repo,
        'exporting_cv_name': exporting_cv_name,
        'exporting_cv': exporting_cv,
        'exporting_cvv_id': exporting_cvv_id,
    }


def _create_cv(cv_name, repo, module_org, sat, publish=True):
    """Creates CV and/or publishes in organization with given name and repository

    :param cv_name: The name of CV to create
    :param repo: The repository directory
    :param organization: The organization directory
    :param publish: Publishes the CV if True else doesn't
    :return: The directory of CV and Content View ID
    """
    description = gen_string('alpha')
    content_view = sat.cli_factory.make_content_view(
        {'name': cv_name, 'description': description, 'organization-id': module_org.id}
    )
    sat.cli.ContentView.add_repository(
        {
            'id': content_view['id'],
            'organization-id': module_org.id,
            'repository-id': repo['id'],
        }
    )
    content_view = sat.cli.ContentView.info({'name': cv_name, 'organization-id': module_org.id})
    cvv_id = None
    if publish:
        sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = sat.cli.ContentView.info({'id': content_view['id']})
        cvv_id = content_view['versions'][0]['id']
    return content_view, cvv_id


class TestContentViewSync:
    """Implements Content View Export Import tests in CLI"""

    @pytest.mark.e2e
    def test_positive_export_import_cv_end_to_end(
        self,
        target_sat,
        class_export_entities,
        config_export_import_settings,
        export_import_cleanup_module,
        module_org,
        function_import_org,
    ):
        """Export the CV and import it. Ensure that all content is same from export to import.

        :id: b4fb9386-9b6a-4fc5-a8bf-96d7c80af93e

        :setup:
            1. Product with synced custom repository, published in a CV.

        :steps:
            1. Export CV version via complete version
            2. Import the exported files to satellite
            3. Check that content of export and import matches

        :expectedresults:
            1. CV version custom contents has been exported to directory.
            2. All The exported custom contents has been imported in org/satellite.

        :BZ: 1832858

        :customerscenario: true
        """
        export_prod_name = import_prod_name = class_export_entities['exporting_prod_name']
        export_repo_name = import_repo_name = class_export_entities['exporting_repo_name']
        export_cvv_id = class_export_entities['exporting_cvv_id']
        export_cv_description = class_export_entities['exporting_cv']['description']
        import_cv_name = class_export_entities['exporting_cv_name']
        # Check packages
        exported_packages = target_sat.cli.Package.list({'content-view-version-id': export_cvv_id})
        assert len(exported_packages)
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': export_cvv_id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])
        # Check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import files and verify content
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        importing_cv = target_sat.cli.ContentView.info(
            {'name': import_cv_name, 'organization-id': function_import_org.id}
        )
        importing_cvv = importing_cv['versions']
        assert importing_cv['description'] == export_cv_description
        assert len(importing_cvv) >= 1
        imported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': importing_cvv[0]['id']}
        )
        assert len(imported_packages)
        assert len(exported_packages) == len(imported_packages)
        exported_repo = target_sat.cli.Repository.info(
            {
                'name': export_repo_name,
                'product': export_prod_name,
                'organization-id': module_org.id,
            }
        )
        imported_repo = target_sat.cli.Repository.info(
            {
                'name': import_repo_name,
                'product': import_prod_name,
                'organization-id': function_import_org.id,
            }
        )
        assert exported_repo['content-counts'] == imported_repo['content-counts'], (
            'Exported and imported counts do not match'
        )

    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_export_import_default_org_view(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_import_org_with_manifest,
        function_synced_custom_repo,
        function_synced_rh_repo,
    ):
        """Export Default Organization View version contents in directory and Import them.

        :id: b8a2c878-cfc2-491c-a71f-74108d6bc247

        :parametrized: yes

        :setup:
            1. Product with synced custom repository.
            2. Enabled and synced RH repository.

        :steps:
            1. Create CV with the custom and RH repository.
            2. Export `Default Organization View version` contents using complete library.
            3. Import those contents from some other org/satellite.

        :expectedresults:
            1. Default Organization View version custom contents has been exported.
            2. All the exported custom contents has been imported in org/satellite.

        :BZ: 1671319

        :customerscenario: true
        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_sca_manifest_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_custom_repo['id'],
            }
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_rh_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        content_view = target_sat.cli.ContentView.info(
            {
                'name': cv_name,
                'organization-id': function_sca_manifest_org.id,
            }
        )
        # Verify packages
        default_cvv_id = content_view['versions'][0]['id']
        cv_packages = target_sat.cli.Package.list({'content-view-version-id': default_cvv_id})
        assert len(cv_packages)
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export complete library
        export = target_sat.cli.ContentExport.completeLibrary(
            {'organization-id': function_sca_manifest_org.id}
        )
        # Verify 'export-library' is created and packages are there
        import_path = target_sat.move_pulp_archive(function_sca_manifest_org, export['message'])
        export_lib_cv = target_sat.cli.ContentView.info(
            {
                'name': EXPORT_LIBRARY_NAME,
                'organization-id': function_sca_manifest_org.id,
            }
        )
        export_lib_cvv_id = export_lib_cv['versions'][0]['id']
        exported_lib_packages = target_sat.cli.Package.list(
            {'content-view-version-id': export_lib_cvv_id}
        )
        assert len(exported_lib_packages)
        assert exported_lib_packages == cv_packages
        # Import and verify content of library
        target_sat.cli.Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        target_sat.cli.ContentImport.library(
            {'organization-id': function_import_org_with_manifest.id, 'path': import_path}
        )
        importing_cvv = target_sat.cli.ContentView.info(
            {'name': DEFAULT_CV, 'organization-id': function_import_org_with_manifest.id}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': importing_cvv[0]['id']}
        )
        assert len(imported_packages)
        assert len(cv_packages) == len(imported_packages)

    def test_positive_export_import_filtered_cvv(
        self,
        class_export_entities,
        export_import_cleanup_module,
        config_export_import_settings,
        target_sat,
        module_org,
    ):
        """CV Version with filtered contents is the only one that gets exported and imported

        :id: 2992e0ae-173d-4589-817d-1a11455dfc43

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product.
            4. Create a filter and filter-rule.
            5. Publish the above filtered content-view.
            6. Export Filtered CV version contents to a directory
            7. Import those contents from some other org/satellite.

        :expectedresults:

            1. Filtered CV version custom contents has been exported to directory
            2. Filtered exported custom contents has been imported in org/satellite

        """
        exporting_cv_name = importing_cvv = gen_string('alpha')
        exporting_cv, exporting_cvv = _create_cv(
            exporting_cv_name,
            class_export_entities['exporting_repo'],
            class_export_entities['exporting_org'],
            target_sat,
        )
        filter_name = gen_string('alphanumeric')
        target_sat.cli.ContentView.filter.create(
            {
                'name': filter_name,
                'content-view-id': exporting_cv['id'],
                'inclusion': 'yes',
                'type': 'rpm',
            }
        )
        target_sat.cli.ContentView.filter.rule.create(
            {
                'name': 'cat',
                'content-view-filter': filter_name,
                'content-view-id': exporting_cv['id'],
            }
        )
        target_sat.cli.ContentView.publish(
            {
                'id': exporting_cv['id'],
                'organization-id': class_export_entities['exporting_org'].id,
            }
        )
        exporting_cv = target_sat.cli.ContentView.info({'id': exporting_cv['id']})
        exporting_cvv_id = max(exporting_cv['versions'], key=lambda x: int(x['id']))['id']
        # Check presence of 1 rpm due to filter
        export_packages = target_sat.cli.Package.list({'content-view-version-id': exporting_cvv_id})
        assert len(export_packages) == 1
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv_id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])

        # Import section
        importing_org = target_sat.cli_factory.make_org()
        # set disconnected mode
        target_sat.cli.Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import file and verify content
        target_sat.cli.ContentImport.version(
            {'organization-id': importing_org['id'], 'path': import_path}
        )
        importing_cvv = target_sat.cli.ContentView.info(
            {'name': importing_cvv, 'organization-id': importing_org['id']}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': importing_cvv[0]['id']}
        )
        assert len(imported_packages) == 1
        assert len(export_packages) == len(imported_packages)

    @pytest.mark.upgrade
    def test_positive_export_import_promoted_cv(
        self,
        target_sat,
        class_export_entities,
        export_import_cleanup_module,
        config_export_import_settings,
        module_org,
        function_import_org,
    ):
        """Export promoted CV version contents in directory and Import them.

        :id: 315ef1f0-e2ad-43ec-adff-453fb71654a7

        :setup:
            1. Product with synced custom repository, published in a CV.

        :steps:
            1. Promote the CV.
            2. Export CV version contents to a directory.
            3. Import those contents from some other org/satellite.

        :expectedresults:
            1. Promoted CV version contents has been exported to directory.
            2. Promoted CV version contents has been imported successfully.
            3. The imported CV should only be published and not promoted.

        """
        import_cv_name = class_export_entities['exporting_cv_name']
        export_cv_id = class_export_entities['exporting_cv']['id']
        export_cvv_id = class_export_entities['exporting_cvv_id']
        env = target_sat.cli_factory.make_lifecycle_environment({'organization-id': module_org.id})
        target_sat.cli.ContentView.version_promote(
            {
                'id': export_cvv_id,
                'to-lifecycle-environment-id': env['id'],
            }
        )
        promoted_cvv_id = target_sat.cli.ContentView.info({'id': export_cv_id})['versions'][-1][
            'id'
        ]
        # Check packages
        exported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': promoted_cvv_id}
        )
        assert len(exported_packages)
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': export_cvv_id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])
        # Import and verify content
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        importing_cv_id = target_sat.cli.ContentView.info(
            {'name': import_cv_name, 'organization-id': function_import_org.id}
        )
        importing_cvv_id = target_sat.cli.ContentView.info(
            {'name': import_cv_name, 'organization-id': function_import_org.id}
        )['versions']
        assert len(importing_cvv_id) >= 1
        imported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': importing_cvv_id[0]['id']}
        )
        assert len(imported_packages)
        assert len(exported_packages) == len(imported_packages)
        # Verify the LCE is in Library
        lce = importing_cv_id['lifecycle-environments'][0]['name']
        assert lce == 'Library'

    @pytest.mark.upgrade
    @pytest.mark.e2e
    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['kickstart-rhel7', 'kickstart-rhel8_bos', 'rhscl7'],
        indirect=True,
    )
    def test_positive_export_import_redhat_cv(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_import_org_with_manifest,
        function_synced_rh_repo,
    ):
        """Export CV version with RedHat contents in directory and import them.

        :id: f6bd7fa9-396e-44ac-92a3-ab87ce1a7ef5

        :parametrized: yes

        :setup:
            1. Enabled and synced RH repository.

        :steps:
            1. Create CV with the RH repo and publish.
            2. Export CV version contents to a directory.
            3. Import those contents from some other org/satellite.

        :expectedresults:
            1. CV version redhat contents has been exported to directory.
            2. All the exported redhat contents has been imported in org/satellite.

        :BZ: 1655239, 2040870

        :customerscenario: true

        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_sca_manifest_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_rh_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_sca_manifest_org.id},
            timeout='2h',
        )
        # Verify export directory is not empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) != ''

        import_path = target_sat.move_pulp_archive(function_sca_manifest_org, export['message'])
        exported_packages = target_sat.cli.Package.list({'content-view-version-id': cvv['id']})
        assert len(exported_packages)
        # Import and verify content
        target_sat.cli.Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org_with_manifest.id, 'path': import_path},
            timeout='2h',
        )
        importing_cvv = target_sat.cli.ContentView.info(
            {'name': cv_name, 'organization-id': function_import_org_with_manifest.id}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': importing_cvv[0]['id']}
        )
        assert len(imported_packages)
        assert len(exported_packages) == len(imported_packages)
        exported_repo = target_sat.cli.Repository.info(
            {
                'name': function_synced_rh_repo['name'],
                'product': function_synced_rh_repo['product']['name'],
                'organization-id': function_sca_manifest_org.id,
            }
        )
        imported_repo = target_sat.cli.Repository.info(
            {
                'name': function_synced_rh_repo['name'],
                'product': function_synced_rh_repo['product']['name'],
                'organization-id': function_import_org_with_manifest.id,
            }
        )
        assert exported_repo['content-counts'] == imported_repo['content-counts'], (
            'Exported and imported counts do not match'
        )

    def test_positive_export_cv_with_on_demand_repo(
        self, export_import_cleanup_module, target_sat, module_org
    ):
        """Exporting CV version skips on_demand repo

        :id: c366ace5-1fde-4ae7-9e84-afe58c06c0ca

        :steps:
            1. Create product
            2. Create repos with immediate and on_demand download policy
            3. Sync the repositories
            4. Create CV with above product and publish
            5. Attempt to export CV version with 'fail-on-missing' option
            6. Attempt to export CV version without 'fail-on-missing' option

        :expectedresults:
            1. Export fails when 'fail-on-missing' option is used
            2. Export passes otherwise with warning and skips the on_demand repo
        """
        # Create custom product
        product = target_sat.cli_factory.make_product(
            {'organization-id': module_org.id, 'name': gen_string('alpha')}
        )

        # Create repositories and sync them
        repo_ondemand = target_sat.cli_factory.make_repository(
            {
                'content-type': 'yum',
                'download-policy': 'on_demand',
                'organization-id': module_org.id,
                'product-id': product['id'],
            }
        )
        repo_immediate = target_sat.cli_factory.make_repository(
            {
                'content-type': 'yum',
                'download-policy': 'immediate',
                'organization-id': module_org.id,
                'product-id': product['id'],
            }
        )
        target_sat.cli.Repository.synchronize({'id': repo_ondemand['id']})
        target_sat.cli.Repository.synchronize({'id': repo_immediate['id']})

        # Create cv and publish
        cv = target_sat.cli_factory.make_content_view(
            {'name': gen_string('alpha'), 'organization-id': module_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_org.id,
                'repository-id': repo_ondemand['id'],
            }
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_org.id,
                'repository-id': repo_immediate['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})

        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''

        # Attempt to export CV version with 'fail-on-missing' option
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.ContentExport.completeVersion(
                {
                    'organization-id': module_org.id,
                    'content-view-id': cv['id'],
                    'version': '1.0',
                    'fail-on-missing-content': True,
                },
                output_format='base',  # json output can't be parsed - BZ#1998626
            )

        # Export is not generated
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''

        # Attempt to export CV version without 'fail-on-missing' option
        result = target_sat.cli.ContentExport.completeVersion(
            {
                'organization-id': module_org.id,
                'content-view-id': cv['id'],
                'version': '1.0',
            },
            output_format='base',  # json output can't be parsed - BZ#1998626
        )

        # Warning is shown
        assert (
            """NOTE: Unable to fully export this version because it contains repositories """
            """without the 'immediate' download policy. Update the download policy and sync """
            """affected repositories. Once synced republish the content view and export the """
            """generated version."""
        ) in result
        assert repo_ondemand['name'] in result  # on_demand repo is listed as skipped
        assert repo_immediate['name'] not in result  # immediate repo is not listed

        # Export is generated
        assert "Generated" in result
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) != ''

    def test_negative_import_same_cv_twice(
        self,
        target_sat,
        class_export_entities,
        export_import_cleanup_module,
        config_export_import_settings,
        module_org,
        function_import_org,
    ):
        """Import the same CV twice.

        :id: 15a7ddd3-c1a5-4b22-8460-6cb2b8ea4ef9

        :setup:
            1. Product with synced custom repository, published in a CV.

        :steps:
            1. Export CV version contents to a directory.
            2. Import those contents from some other org/satellite.
            3. Attempt to reimport the same contents.

        :expectedresults:
            1. Reimporting the contents with same version fails.
            2. Satellite displays an error message.
        """
        export_cvv_id = class_export_entities['exporting_cvv_id']
        export_cv_name = class_export_entities['exporting_cv_name']
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': export_cvv_id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])
        # Check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import section
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        with pytest.raises(CLIReturnCodeError) as error:
            target_sat.cli.ContentImport.version(
                {'organization-id': function_import_org.id, 'path': import_path}
            )
        assert (
            f"Content View Version specified in the metadata - '{export_cv_name} 1.0' "
            'already exists. If you wish to replace the existing version, '
            f'delete {export_cv_name} 1.0 and try again.'
        ) in error.value.message

    def test_negative_import_invalid_path(self, module_org, module_target_sat):
        """Import cv that doesn't exist in path

        :id: 4cc69666-407f-4d66-b3d2-8fe2ed135a5f

        :steps:
            1. Import a CV with a path that doesn't exist.

        :expectedresults:
            1. Error 'Unable to sync repositories, no library repository found' should be displayed.
        """
        export_folder = gen_string('alpha')
        import_path = f'{PULP_IMPORT_DIR}{export_folder}'
        # Import section
        with pytest.raises(CLIReturnCodeError) as error:
            module_target_sat.cli.ContentImport.version(
                {'organization-id': module_org.id, 'path': import_path}
            )
        assert (
            f'''Error: Unable to find '{import_path}/metadata.json'. '''
            'If the metadata.json file is at a different location provide it to the '
            '--metadata-file option'
        ) in error.value.message

    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_negative_import_incomplete_archive(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_synced_rh_repo,
        function_sca_manifest_org,
        function_import_org_with_manifest,
    ):
        """Try to import an incomplete export archive (mock interrupted transfer).

        :id: c3b898bb-c6c8-402d-82f9-b15774d9f0fc

        :parametrized: yes

        :setup:
            1. Enabled and synced RH repository.

        :steps:
            1. Create CV with the setup repo, publish it and export.
            2. Corrupt the export archive so that it's incomplete.
            3. Try to import the incomplete archive.
            4. Verify no content is imported and the import CV can be deleted.

        :expectedresults:
            1. The import should fail.
            2. No content should be added, the empty import CV can be deleted.
        """
        # Create CV with the setup repo, publish it and export
        cv = target_sat.cli_factory.make_content_view(
            {
                'organization-id': function_sca_manifest_org.id,
                'repository-ids': [function_synced_rh_repo['id']],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_sca_manifest_org.id}
        )
        assert '1.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )

        # Corrupt the export archive so that it's incomplete
        tar_files = target_sat.execute(
            f'find {PULP_EXPORT_DIR}{function_sca_manifest_org.name}/{cv["name"]}/ -name *.tar'
        ).stdout.splitlines()
        assert len(tar_files) == 1, 'Expected just one tar file in the export'

        size = int(target_sat.execute(f'du -b {tar_files[0]}').stdout.split()[0])
        assert size > 0, 'Export tar should not be empty'

        res = target_sat.execute(f'truncate -s {size // 2} {tar_files[0]}')
        assert res.status == 0, 'Truncation of the tar file failed'

        # Try to import the incomplete archive
        import_path = target_sat.move_pulp_archive(function_sca_manifest_org, export['message'])
        with pytest.raises(CLIReturnCodeError) as error:
            target_sat.cli.ContentImport.version(
                {'organization-id': function_import_org_with_manifest.id, 'path': import_path}
            )
        assert '1 subtask(s) failed' in error.value.message
        target_sat.wait_for_tasks(
            search_query=(
                'Actions::Katello::ContentView::Remove and '
                f'organization_id = {function_import_org_with_manifest.id}'
            ),
            max_tries=5,
            poll_rate=10,
        )

        # Verify no content is imported and the import CV can be deleted
        imported_cv = target_sat.cli.ContentView.info(
            {'name': cv['name'], 'organization-id': function_import_org_with_manifest.id}
        )
        assert len(imported_cv['versions']) == 0, 'There should be no CV version imported'

        target_sat.cli.ContentView.delete({'id': imported_cv['id']})
        with pytest.raises(CLIReturnCodeError) as error:
            target_sat.cli.ContentView.info(
                {'name': cv['name'], 'organization-id': function_import_org_with_manifest.id}
            )
        assert 'content_view not found' in error.value.message, 'The imported CV should be gone'

    @pytest.mark.e2e
    @pytest.mark.rhel_ver_match('9')
    @pytest.mark.parametrize('function_flatpak_remote', ['RedHat'], indirect=True)
    def test_postive_export_import_cv_with_mixed_content_repos(
        self,
        request,
        complete_export_import_cleanup,
        target_sat,
        function_org,
        function_product,
        function_synced_custom_repo,
        function_synced_file_repo,
        function_synced_docker_repo,
        function_synced_flatpak_repos,
        function_synced_AC_repo,
        module_import_sat,
        function_import_org_at_isat,
        module_flatpak_contenthost,
    ):
        """Export and import CV with mixed content types in the exportable format,
        consume it from the import.

        :id: ffcdbbc6-f787-4978-80a7-4b44c389bf49

        :setup:
            1. Synced repositories of each content type: yum, file, docker, flatpak, AC

        :steps:
            1. Create CV, add all setup repos and publish.
            2. Export CV version contents to a directory.
            3. Import the exported CV, check the content.
            4. Register a contenthost using AK.
            5. Configure the contenthost via REX to use import Sat's flatpak index.
            6. Consume the imported content for each content type.

        :expectedresults:
            1. Export succeeds and content is exported.
            2. Import succeeds, content is imported and matches the export.
            3. Imported content is consumable at the registered host.

        :BZ: 1726457

        :customerscenario: true

        """
        # Create CV, add all setup repos and publish.
        content_view = target_sat.cli_factory.make_content_view(
            {'organization-id': function_org.id}
        )
        repos = [
            function_synced_custom_repo,
            function_synced_file_repo,
            function_synced_docker_repo,
            function_synced_AC_repo,
        ]
        repos.extend(function_synced_flatpak_repos)
        for repo in repos:
            target_sat.cli.ContentView.add_repository(
                {
                    'id': content_view['id'],
                    'organization-id': function_org.id,
                    'repository-id': repo['id'],
                }
            )
        target_sat.cli.ContentView.publish({'id': content_view['id']})
        exporting_cv = target_sat.cli.ContentView.info({'id': content_view['id']})
        assert len(exporting_cv['versions']) == 1
        exporting_cvv = target_sat.cli.ContentView.version_info(
            {'id': exporting_cv['versions'][0]['id']}
        )
        assert len(exporting_cvv['repositories']) == len(repos)
        exported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': exporting_cvv['id']}
        )
        exported_files = target_sat.cli.File.list({'content-view-version-id': exporting_cvv['id']})

        # Export CV version contents in exportable format.
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv['id'], 'organization-id': function_org.id}
        )
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) != ''

        # Import the exported CV, check the content.
        import_path = target_sat.move_pulp_archive(
            function_org, export['message'], target=module_import_sat
        )
        module_import_sat.cli.ContentImport.version(
            {'organization-id': function_import_org_at_isat.id, 'path': import_path}
        )
        importing_cv = module_import_sat.cli.ContentView.info(
            {'name': exporting_cv['name'], 'organization-id': function_import_org_at_isat.id}
        )
        assert all([exporting_cv[key] == importing_cv[key] for key in ['label', 'name']]), (
            'Imported CV name/label does not match the export'
        )
        assert len(exporting_cv['versions']) == len(importing_cv['versions']) == 1, (
            'CV versions count does not match'
        )

        importing_cvv = module_import_sat.cli.ContentView.version_info(
            {'id': importing_cv['versions'][0]['id']}
        )
        assert (
            len(exporting_cvv['repositories']) == len(importing_cvv['repositories']) == len(repos)
        ), 'Repositories count does not match'

        imported_packages = module_import_sat.cli.Package.list(
            {'content-view-version-id': importing_cvv['id']}
        )
        imported_files = module_import_sat.cli.File.list(
            {'content-view-version-id': importing_cvv['id']}
        )
        assert set(f['filename'] for f in exported_packages) == set(
            f['filename'] for f in imported_packages
        ), 'Imported RPMs do not match the export'
        assert set(f['name'] for f in exported_files) == set(f['name'] for f in imported_files), (
            'Imported Files do not match the export'
        )

        for repo in repos:
            exp = target_sat.cli.Repository.info(
                {
                    'organization-id': function_org.id,
                    'product': repo['product']['name'],
                    'name': repo['name'],
                }
            )
            imp = module_import_sat.cli.Repository.info(
                {
                    'organization-id': function_import_org_at_isat.id,
                    'product': repo['product']['name'],
                    'name': repo['name'],
                }
            )
            for key in ['label', 'description', 'content-type', 'content-counts']:
                assert exp[key] == imp[key], (
                    f'"{key}" of the {imp["content-type"]} repo differs: {exp[key]} ≠ {imp[key]}'
                )

        # Register a content host using AK.
        ak = module_import_sat.cli.ActivationKey.create(
            {
                'name': gen_string('alpha'),
                'organization-id': function_import_org_at_isat.id,
                'lifecycle-environment': 'Library',
                'content-view': importing_cv['name'],
            }
        )
        module_import_sat.cli.ActivationKey.content_override(
            {
                'id': ak['id'],
                'content-label': '_'.join(
                    [
                        function_import_org_at_isat.name,
                        function_product.name,
                        function_synced_custom_repo.name,
                    ]
                ),
                'value': 'true',
            }
        )
        res = module_flatpak_contenthost.register(
            function_import_org_at_isat, None, ak['name'], module_import_sat, force=True
        )
        assert res.status == 0, (
            f'Failed to register host: {module_flatpak_contenthost.hostname}\n'
            f'StdOut: {res.stdout}\nStdErr: {res.stderr}'
        )
        assert module_flatpak_contenthost.subscribed

        # Configure the contenthost via REX to use Satellite's flatpak index.
        remote_name = f'ISS-remote-{gen_string("alpha")}'
        job = module_import_sat.cli_factory.job_invocation(
            {
                'organization': function_import_org_at_isat.name,
                'job-template': 'Flatpak - Set up remote on host',
                'inputs': (
                    f'Remote Name={remote_name}, '
                    f'Flatpak registry URL={settings.server.scheme}://{module_import_sat.hostname}/pulpcore_registry/, '
                    f'Username={settings.server.admin_username}, '
                    f'Password={settings.server.admin_password}'
                ),
                'search-query': f"name = {module_flatpak_contenthost.hostname}",
            }
        )
        res = module_import_sat.cli.JobInvocation.info({'id': job.id})
        assert 'succeeded' in res['status']
        request.addfinalizer(
            lambda: module_flatpak_contenthost.execute(f'flatpak remote-delete {remote_name}')
        )

        # Consume the imported content for each content type.
        #  Flatpak
        res = module_flatpak_contenthost.execute('flatpak remotes')
        assert remote_name in res.stdout

        app_name = 'firefox'
        res = module_flatpak_contenthost.execute('flatpak remote-ls')
        assert app_name in res.stdout

        job = module_import_sat.cli_factory.job_invocation(
            {
                'organization': function_import_org_at_isat.name,
                'job-template': 'Flatpak - Install application on host',
                'inputs': (
                    f'Flatpak remote name={remote_name}, Application name={app_name}, '
                    'Launch a session bus instance=true'
                ),
                'search-query': f"name = {module_flatpak_contenthost.hostname}",
            },
            timeout='800s',
        )
        res = module_import_sat.cli.JobInvocation.info({'id': job.id})
        assert 'succeeded' in res['status']
        request.addfinalizer(
            lambda: module_flatpak_contenthost.execute(
                f'flatpak uninstall {remote_name} {app_name} com.redhat.Platform -y'
            )
        )

        #  Yum
        res = module_flatpak_contenthost.execute('dnf install -y cheetah')
        assert res.status == 0

        #  File
        repo_url = module_import_sat.get_published_repo_url(
            org=function_import_org_at_isat.label,
            prod=function_product.label,
            repo=function_synced_file_repo.label,
            lce='Library',
            cv=importing_cv['label'],
        )
        res = module_flatpak_contenthost.execute(f'curl {repo_url}test.txt')
        assert 'Hello, World!' in res.stdout, 'Expected world-wide greeting'

        #  Docker
        res = module_flatpak_contenthost.execute(
            f'podman login -u {settings.server.admin_username}'
            f' -p {settings.server.admin_password} {module_import_sat.hostname}'
        )
        assert res.status == 0

        repo_path = f'{function_import_org_at_isat.label}/library/{importing_cv["label"]}/{function_product.label}/{function_synced_docker_repo.label}'.lower()
        res = module_flatpak_contenthost.execute(
            f'podman search {module_import_sat.hostname}/{repo_path}'
        )
        assert repo_path in res.stdout
        res = module_flatpak_contenthost.execute(
            f'podman pull {module_import_sat.hostname}/{repo_path}'
        )
        assert res.status == 0
        res = module_flatpak_contenthost.execute('podman images')
        assert repo_path in res.stdout

        #  AC
        api_path = f'https://{module_import_sat.hostname}/pulp_ansible/galaxy/{function_import_org_at_isat.label}/Library/custom/{function_product.label}/{function_synced_AC_repo.label}'
        res = target_sat.execute(
            f'ansible-galaxy collection install -c -f -s {api_path} theforeman.foreman'
        )
        assert res.status == 0
        assert 'installed successfully' in res.stdout

    def test_postive_export_import_cv_with_mixed_content_syncable(
        self,
        export_import_cleanup_function,
        target_sat,
        function_org,
        function_synced_custom_repo,
        function_synced_file_repo,
        function_import_org,
    ):
        """Export and import CV with mixed content in the syncable format.

        :id: cb1aecac-d48a-4154-9ca7-71788674148f

        :setup:
            1. Synced repositories of syncable-supported content types: yum, file

        :steps:
            1. Create CV, add all setup repos and publish.
            2. Export CV version contents in syncable format.
            3. Import the syncable export, check the content.

        :expectedresults:
            1. Export succeeds and content is exported.
            2. Import succeeds, content is imported and matches the export.
        """
        # Create CV, add all setup repos and publish
        cv = target_sat.cli_factory.make_content_view({'organization-id': function_org.id})
        repos = [
            function_synced_custom_repo,
            function_synced_file_repo,
        ]
        for repo in repos:
            target_sat.cli.ContentView.add_repository(
                {
                    'id': cv['id'],
                    'organization-id': function_org.id,
                    'repository-id': repo['id'],
                }
            )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        exporting_cv = target_sat.cli.ContentView.info({'id': cv['id']})
        exporting_cvv = target_sat.cli.ContentView.version_info(
            {'id': exporting_cv['versions'][0]['id']}
        )
        exported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': exporting_cvv['id']}
        )
        exported_files = target_sat.cli.File.list({'content-view-version-id': exporting_cvv['id']})

        # Export CV version contents in syncable format
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv['id'], 'organization-id': function_org.id, 'format': 'syncable'}
        )
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) != ''

        # Import the syncable export
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        importing_cv = target_sat.cli.ContentView.info(
            {'name': exporting_cv['name'], 'organization-id': function_import_org.id}
        )
        assert all([exporting_cv[key] == importing_cv[key] for key in ['label', 'name']]), (
            'Imported CV name/label does not match the export'
        )
        assert len(exporting_cv['versions']) == len(importing_cv['versions']) == 1, (
            'CV versions count does not match'
        )

        importing_cvv = target_sat.cli.ContentView.version_info(
            {'id': importing_cv['versions'][0]['id']}
        )
        assert (
            len(exporting_cvv['repositories']) == len(importing_cvv['repositories']) == len(repos)
        ), 'Repositories count does not match'

        imported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': importing_cvv['id']}
        )
        imported_files = target_sat.cli.File.list({'content-view-version-id': importing_cvv['id']})
        assert exported_packages == imported_packages, 'Imported RPMs do not match the export'
        assert exported_files == imported_files, 'Imported Files do not match the export'

    def test_postive_export_cv_syncable_with_permissions(
        self,
        request,
        export_import_cleanup_function,
        target_sat,
        function_restrictive_umask,
        function_org,
        function_synced_custom_repo,
        function_synced_file_repo,
    ):
        """Export CV with mixed content in syncable format with restrictive umask
        and check the exported files permissions stay sufficient for import.

        :id: f0d83ca5-2213-4649-a248-3de4f131df68

        :setup:
            1. Synced repositories of syncable-supported content types: yum, file
            2. Restrictive umask (0077) is set for non-login shell.

        :steps:
            1. Create CV, add all setup repos and publish.
            2. Export CV version contents in syncable format.
            3. Check the permissions of exported files.

        :expectedresults:
            1. Exported files have sufficient permissions for import.

        :BZ: 2233162

        :customerscenario: true
        """
        # Create CV, add all setup repos and publish
        cv = target_sat.cli_factory.make_content_view({'organization-id': function_org.id})
        repos = [
            function_synced_custom_repo,
            function_synced_file_repo,
        ]
        for repo in repos:
            target_sat.cli.ContentView.add_repository(
                {
                    'id': cv['id'],
                    'organization-id': function_org.id,
                    'repository-id': repo['id'],
                }
            )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        exporting_cv = target_sat.cli.ContentView.info({'id': cv['id']})
        exporting_cvv = target_sat.cli.ContentView.version_info(
            {'id': exporting_cv['versions'][0]['id']}
        )

        # Export CV version contents in syncable format
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv['id'], 'organization-id': function_org.id, 'format': 'syncable'}
        )

        # Check the permissions of exported files
        paths = target_sat.validate_pulp_filepath(
            function_org, PULP_EXPORT_DIR, file_names='*'
        ).split()
        assert len(paths) > 0, 'Nothing found at export path'
        assert all(
            [
                '644' in target_sat.execute(f'stat -c %a {path}').stdout
                for path in paths
                if 'metadata.json' not in path
            ]
        ), 'Unexpected permission for one or more exported files'

    def test_postive_export_import_cv_with_file_content(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_org,
        function_synced_file_repo,
        function_import_org,
    ):
        """Exporting and Importing cv with file content

        :id: d00739f0-dedf-4303-8929-889dc23260a4

        :setup:
            1. Product with synced file-type repository.

        :steps:
            1. Create CV, add the file repo and publish.
            2. Export the CV and import it into another organization.
            3. Check the imported CV has files in it.

        :expectedresults:
            1. Imported CV should have the files present.

        :BZ: 1995827

        :customerscenario: true
        """
        # Create CV, add the file repo and publish.
        cv_name = import_cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': function_synced_file_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        exporting_cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(exporting_cv['versions']) == 1
        exporting_cvv_id = exporting_cv['versions'][0]['id']
        # check files
        exported_files = target_sat.cli.File.list({'content-view-version-id': exporting_cvv_id})
        assert len(exported_files)
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        # Export the CV
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv_id, 'organization-id': function_org.id}
        )
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        # Check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import files and verify content
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        importing_cvv = target_sat.cli.ContentView.info(
            {'name': import_cv_name, 'organization-id': function_import_org.id}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_files = target_sat.cli.File.list(
            {'content-view-version-id': importing_cvv[0]['id']}
        )
        assert len(imported_files)
        assert len(exported_files) == len(imported_files)

    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhs9'],
        indirect=True,
    )
    def test_positive_export_rerun_failed_import(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_synced_rh_repo,
        function_sca_manifest_org,
        function_import_org_with_manifest,
    ):
        """Verify that import can be rerun successfully after failed import.

        :id: 73e7cece-9a93-4203-9c2c-813d5a8d7700

        :parametrized: yes

        :setup:
            1. Enabled and synced RH repository.

        :steps:
            1. Create CV, add repo from the setup, publish it and run export.
            2. Start import of the CV into another organization and kill it before it's done.
            3. Rerun the import again, let it finish and check the CVV was imported.

        :expectedresults:
            1. First import should fail, no CVV should be added.
            2. Second import should succeed without errors and should contain the CVV.

        :CaseImportance: Medium

        :BZ: 2058905

        :customerscenario: true
        """
        # Create CV and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_sca_manifest_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_rh_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export the CV
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_sca_manifest_org.id}
        )
        import_path = target_sat.move_pulp_archive(function_sca_manifest_org, export['message'])
        assert target_sat.execute(f'ls {import_path}').stdout != ''
        # Run the import asynchronously
        task_id = target_sat.cli.ContentImport.version(
            {
                'organization-id': function_import_org_with_manifest.id,
                'path': import_path,
                'async': True,
            }
        )['id']
        # Wait for the CV creation on import and make the import fail
        wait_for(
            lambda: target_sat.cli.ContentView.info(
                {'name': cv_name, 'organization-id': function_import_org_with_manifest.id}
            )
        )
        timestamp = datetime.now(UTC)
        target_sat.cli.Service.restart()
        sleep(30)
        # Assert that the initial import task did not succeed and CVV was removed
        assert (
            target_sat.api.ForemanTask()
            .search(
                query={'search': f'Actions::Katello::ContentViewVersion::Import and id = {task_id}'}
            )[0]
            .result
            != 'success'
        )
        target_sat.wait_for_tasks(
            search_query=f'label = Actions::Katello::ContentView::Remove and started_at >= "{timestamp}"',
            search_rate=10,
            max_tries=6,
        )
        importing_cvv = target_sat.cli.ContentView.info(
            {'name': cv_name, 'organization-id': function_import_org_with_manifest.id}
        )['versions']
        assert len(importing_cvv) == 0
        # Rerun the import and let it finish
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org_with_manifest.id, 'path': import_path}
        )
        importing_cvv = target_sat.cli.ContentView.info(
            {'name': cv_name, 'organization-id': function_import_org_with_manifest.id}
        )['versions']
        assert len(importing_cvv) == 1

    def test_postive_export_import_ansible_collection_repo(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_org,
        function_import_org,
    ):
        """Exporting and Importing library with ansible collection

        :id: 71dd1e1a-caad-48be-a180-206c8aa78639

        :steps:
            1. Create custom product and custom repo with ansible collection.
            2. Sync the repo.
            3. Export library and import into another satellite.
            4. Check imported library has ansible collection in it.

        :expectedresults:
            1. Imported library should have the ansible collection present in the imported product.

        :BlockedBy: SAT-23051

        :Verifies: SAT-23051
        """
        # setup ansible_collection product and repo
        export_product = target_sat.cli_factory.make_product({'organization-id': function_org.id})
        ansible_repo = target_sat.cli_factory.make_repository(
            {
                'organization-id': function_org.id,
                'product-id': export_product['id'],
                'content-type': 'ansible_collection',
                'url': ANSIBLE_GALAXY,
                'ansible-collection-requirements': '{collections: [ \
                        { name: theforeman.foreman, version: "2.1.0" }, \
                        { name: theforeman.operations, version: "0.1.0"} ]}',
            }
        )
        target_sat.cli.Repository.synchronize({'id': ansible_repo['id']})
        # Export library
        export = target_sat.cli.ContentExport.completeLibrary({'organization-id': function_org.id})
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        # Check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import files and verify content
        target_sat.cli.ContentImport.library(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        assert target_sat.cli.Product.list({'organization-id': function_import_org.id})
        import_product = target_sat.cli.Product.info(
            {
                'organization-id': function_import_org.id,
                'id': target_sat.cli.Product.list({'organization-id': function_import_org.id})[0][
                    'id'
                ],
            }
        )
        assert import_product['name'] == export_product['name']
        assert len(import_product['content']) == 1
        assert import_product['content'][0]['content-type'] == "ansible_collection"

    def test_postive_export_import_repo_with_GPG(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_org,
        function_synced_custom_repo,
        function_import_org,
    ):
        """Test export and import of a repository with GPG key

        :id: a5b455aa-e87e-4ae5-a1c7-4c8e6c7f7af5

        :setup:
            1. Product with synced custom repository.

        :steps:
            1. Create a GPG key and add it to the setup repository.
            2. Export the repository and import it into another organization.

        :expectedresults:
            1. Export and import succeeds without any errors.
            2. GPG key is imported to the importing org too.

        :CaseImportance: Medium

        :BZ: 2178645, 2090390

        :customerscenario: true
        """
        # Create a GPG key and add it to the setup repository.
        gpg_key = target_sat.api.GPGKey(
            organization=function_org,
            content=DataFile.VALID_GPG_KEY_FILE.read_text(),
        ).create()
        target_sat.cli.Repository.update(
            {'id': function_synced_custom_repo.id, 'gpg-key-id': gpg_key.id}
        )
        # Export the repository and import it into another organization.
        export = target_sat.cli.ContentExport.completeRepository(
            {'id': function_synced_custom_repo.id}
        )
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        target_sat.cli.ContentImport.repository(
            {
                'organization-id': function_import_org.id,
                'path': import_path,
            }
        )
        # Check the imported repo has the GPG key assigned.
        imported_repo = target_sat.cli.Repository.info(
            {
                'name': function_synced_custom_repo.name,
                'product': function_synced_custom_repo.product.name,
                'organization-id': function_import_org.id,
            }
        )
        assert int(imported_repo['content-counts']['packages'])
        assert imported_repo['gpg-key']['name'] == gpg_key.name
        # Check the GPG key is imported to the importing org too.
        imported_gpg = target_sat.cli.ContentCredential.info(
            {'organization-id': function_import_org.id, 'name': gpg_key.name}
        )
        assert imported_gpg
        assert imported_gpg['content'] == gpg_key.content

    def test_postive_export_import_chunked_repo(
        self,
        target_sat,
        config_export_import_settings,
        complete_export_import_cleanup,
        function_org,
        function_synced_custom_repo,
        module_import_sat,
        function_import_org_at_isat,
    ):
        """Test import of a repository exported in chunks bigger than repo size.

        :id: bc27eebf-4749-4dd3-a9d5-c662f43e835b

        :setup:
            1. Product with synced custom repository.

        :steps:
            1. Export the repository using chunks and import it into another organization.
            2. Check the imported content counts.

        :expectedresults:
            1. Export and import succeeds without any errors.

        :CaseImportance: Medium

        :Verifies: SAT-23573, SAT-26458

        :customerscenario: true
        """
        # Export the repository using chunks and import it into another organization.
        export = target_sat.cli.ContentExport.completeRepository(
            {'id': function_synced_custom_repo.id, 'chunk-size-gb': 1}
        )
        import_path = target_sat.move_pulp_archive(
            function_org, export['message'], target=module_import_sat
        )
        module_import_sat.cli.ContentImport.repository(
            {
                'organization-id': function_import_org_at_isat.id,
                'path': import_path,
            }
        )
        # Check the imported content counts.
        exported_repo = target_sat.cli.Repository.info(
            {
                'name': function_synced_custom_repo.name,
                'product': function_synced_custom_repo.product.name,
                'organization-id': function_org.id,
            }
        )
        imported_repo = module_import_sat.cli.Repository.info(
            {
                'name': function_synced_custom_repo.name,
                'product': function_synced_custom_repo.product.name,
                'organization-id': function_import_org_at_isat.id,
            }
        )
        assert exported_repo['content-counts'] == imported_repo['content-counts'], (
            'Unexpected package count after import'
        )

    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_negative_import_redhat_cv_without_manifest(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_synced_rh_repo,
    ):
        """Redhat content can't be imported into satellite/organization without manifest

        :id: b0f5f95b-3f9f-4827-84f1-b66517dc34f1

        :parametrized: yes

        :setup:
            1. Enabled and synced RH repository.

        :steps:
            1. Create CV with the RH repo and publish.
            2. Export CV version contents to a directory.
            3. Import those contents to other org without manifest.

        :expectedresults:
            1. Import fails with message "Could not import the archive.:
               No manifest found. Import a manifest with the appropriate subscriptions before
               importing content."
        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_sca_manifest_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_rh_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_sca_manifest_org.id}
        )
        import_path = target_sat.move_pulp_archive(function_sca_manifest_org, export['message'])
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''

        # importing portion
        importing_org = target_sat.cli_factory.make_org()
        # set disconnected mode
        target_sat.cli.Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        with pytest.raises(CLIReturnCodeError) as error:
            target_sat.cli.ContentImport.version(
                {'organization-id': importing_org['id'], 'path': import_path}
            )
        assert (
            'Could not import the archive.:\n  No manifest found. Import a manifest with the '
            'appropriate subscriptions before importing content.'
        ) in error.value.message

    def test_positive_import_content_for_disconnected_sat_with_existing_content(
        self,
        target_sat,
        class_export_entities,
        config_export_import_settings,
        module_org,
        function_import_org,
    ):
        """Import a content view into a disconnected satellite for an existing content view

        :id: 22c077dc-0041-4c6c-9da5-fd58e5497ae8

        :setup:
            1. Product with synced custom repository, published in a CV.

        :steps:
            1. Run complete export of the CV from setup.
            2. On Disconnected satellite, create a CV with the same name as setup CV and with
               'import-only' set to False and run the import command.
            3. On Disconnected satellite, create a CV with the same name as setup CV and with
               'import-only' set to True and run the import command.

        :expectedresults:
            1. Import should fail with correct message when existing CV has 'import-only' set False.
            2. Import should succeed when existing CV has 'import-only' set True.

        :BZ: 2030101

        :customerscenario: true
        """
        export_cvv_id = class_export_entities['exporting_cvv_id']
        export_cv_name = class_export_entities['exporting_cv_name']
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': export_cvv_id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])
        # Check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import section
        # Create cv with 'import-only' set to False
        cv = target_sat.cli_factory.make_content_view(
            {
                'name': export_cv_name,
                'import-only': False,
                'organization-id': function_import_org.id,
            }
        )
        with pytest.raises(CLIReturnCodeError) as error:
            target_sat.cli.ContentImport.version(
                {'organization-id': function_import_org.id, 'path': import_path}
            )
        assert (
            f"Unable to import in to Content View specified in the metadata - '{export_cv_name}'. "
            "The 'import_only' attribute for the content view is set to false. To mark this "
            "Content View as importable, have your system administrator run the following command "
            f"on the server. \n  foreman-rake katello:set_content_view_import_only ID={cv.id}"
        ) in error.value.message
        target_sat.cli.ContentView.remove({'id': cv.id, 'destroy-content-view': 'yes'})

        # Create cv with 'import-only' set to True
        target_sat.cli_factory.make_content_view(
            {'name': export_cv_name, 'import-only': True, 'organization-id': function_import_org.id}
        )
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        importing_cvv = target_sat.cli.ContentView.info(
            {'name': export_cv_name, 'organization-id': function_import_org.id}
        )['versions']
        assert len(importing_cvv) >= 1

    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_export_incremental_syncable_check_content(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_synced_rh_repo,
    ):
        """Export complete and incremental CV version in syncable format and assert that all
        files referenced in the repomd.xml (including productid) are present in the exports.

        :id: 6ff771cd-39ef-4865-8ae8-629f4baf5f98

        :parametrized: yes

        :setup:
            1. Enabled and synced RH repository.

        :steps:
            1. Create a CV, add the product and publish it.
            2. Export complete syncable CV version.
            3. Publish new CV version.
            4. Export incremental syncable CV version.
            5. Verify the exports contain all files listed in the repomd.xml.

        :expectedresults:
            1. Complete and incremental export succeed.
            2. All files referenced in the repomd.xml files are present in the exports.

        :BZ: 2212523

        :customerscenario: true
        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = target_sat.cli_factory.make_content_view(
            {'name': cv_name, 'organization-id': function_sca_manifest_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_rh_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export complete and check the export directory
        target_sat.cli.ContentExport.completeVersion({'id': cvv['id'], 'format': 'syncable'})
        assert '1.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )
        # Publish new CV version, export incremental and check the export directory
        target_sat.cli.ContentView.publish({'id': cv['id']})
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 2
        cvv = max(cv['versions'], key=lambda x: int(x['id']))
        target_sat.cli.ContentExport.incrementalVersion({'id': cvv['id'], 'format': 'syncable'})
        assert '2.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )
        # Verify that the content referenced in repomd.xml files is present in both exports
        repomd_files = target_sat.execute(
            f'find {PULP_EXPORT_DIR}{function_sca_manifest_org.name}/{cv_name}/ -name repomd.xml'
        ).stdout.splitlines()
        assert len(repomd_files) == 2, 'Unexpected count of exports identified.'
        for repomd in repomd_files:
            repodata_dir = os.path.split(repomd)[0]
            repomd_refs = set(
                target_sat.execute(
                    f'''grep -oP '(?<=<location href="repodata/).*?(?=\")' {repomd}'''
                ).stdout.splitlines()
            )
            drive_files = set(target_sat.execute(f'ls {repodata_dir}').stdout.splitlines())
            assert repomd_refs.issubset(drive_files), (
                'These files are listed in repomd.xml but missing on drive: '
                f'{repomd_refs - drive_files}'
            )

    def test_postive_export_import_with_long_name(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_module,
        module_org,
        function_import_org,
    ):
        """Export and import content entities (product, repository, CV) with a long name.

        :id: 66d676ab-4e06-446b-b893-e236b26d37d9

        :steps:
            1. Create product and repository with a long name, sync it.
            2. Export the repository, import it and verify the prod and repo names match the export.
            3. Verify the imported content matches the export.
            4. Create CV with a long name, add the repo and publish.
            5. Export the CV, import it and verify its name matches the export.
            6. Verify the imported content matches the export.

        :expectedresults:
            1. Exports and imports should succeed without any errors and names
               and content of imported entities should match the export.

        :BZ: 2124275, 2053329

        :customerscenario: true
        """
        # Create product and repository with a long name, sync it.
        product = target_sat.cli_factory.make_product(
            {'name': gen_string('alpha', 128), 'organization-id': module_org.id}
        )
        repo = target_sat.cli_factory.make_repository(
            {
                'name': gen_string('alpha', 128),
                'content-type': 'yum',
                'download-policy': 'immediate',
                'organization-id': module_org.id,
                'product-id': product.id,
            }
        )
        target_sat.cli.Repository.synchronize({'id': repo.id})
        exported_packages = target_sat.cli.Package.list({'repository-id': repo.id})

        # Export the repository, import it and verify the prod and repo names match the export.
        export = target_sat.cli.ContentExport.completeRepository(
            {'id': repo.id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])
        target_sat.cli.ContentImport.repository(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        import_repo = target_sat.cli.Repository.info(
            {
                'organization-id': function_import_org.id,
                'name': repo.name,
                'product': product.name,
            }
        )

        # Verify the imported content matches the export.
        imported_packages = target_sat.cli.Package.list({'repository-id': import_repo['id']})
        assert imported_packages == exported_packages, 'Imported content does not match the export'

        # Create CV with a long name, add the repo and publish.
        exporting_cv = target_sat.cli_factory.make_content_view(
            {'name': gen_string('alpha', 128), 'organization-id': module_org.id}
        )
        target_sat.cli.ContentView.add_repository(
            {
                'id': exporting_cv.id,
                'organization-id': module_org.id,
                'repository-id': repo.id,
            }
        )
        target_sat.cli.ContentView.publish({'id': exporting_cv['id']})
        exporting_cv = target_sat.cli.ContentView.info({'id': exporting_cv['id']})
        assert len(exporting_cv['versions']) == 1
        exporting_cvv_id = exporting_cv['versions'][0]['id']

        # Export the CV, import it and verify its name matches the export.
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv_id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        importing_cv = target_sat.cli.ContentView.info(
            {'name': exporting_cv['name'], 'organization-id': function_import_org.id}
        )
        assert len(importing_cv['versions']) == 1

        # Verify the imported content matches the export.
        imported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': importing_cv['versions'][0]['id']}
        )
        assert exported_packages == imported_packages

    def test_postive_export_import_large_cv(
        self,
        request,
        export_import_cleanup_function,
        target_sat,
        function_org,
        function_synced_large_file_repo,
        function_import_org,
    ):
        """Export and import CV with 100k files and check both operations succeeded.

        :id: 07a4cf36-27be-4b71-83e1-51637222d080

        :setup:
            1. Synced repository with 100k files inside.

        :steps:
            1. Create CV, add the repository and publish.
            2. Export the CV version, assert it succeeds.
            3. Import the exported CV, check the files count.

        :expectedresults:
            1. The export succeeds without errors.
            2. The import succeeds and contains all exported files.

        :Verifies: SAT-25194

        :customerscenario: true
        """
        # Create CV, add the repository and publish
        cv = target_sat.cli_factory.make_content_view({'organization-id': function_org.id})
        target_sat.cli.ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': function_synced_large_file_repo['id'],
            }
        )
        target_sat.cli.ContentView.publish({'id': cv['id']})
        exporting_cv = target_sat.cli.ContentView.info({'id': cv['id']})
        exporting_cvv = target_sat.cli.ContentView.version_info(
            {'id': exporting_cv['versions'][0]['id']}
        )

        # Export the CV version, assert it succeeds
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv['id'], 'organization-id': function_org.id}, timeout='10m'
        )
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

        # Import the exported CV, check the files count.
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path}, timeout='90m'
        )
        importing_cv = target_sat.cli.ContentView.info(
            {'name': exporting_cv['name'], 'organization-id': function_import_org.id}
        )
        assert len(importing_cv['versions']) == 1
        assert (
            target_sat.api.ContentViewVersion(id=importing_cv['versions'][0]['id'])
            .read()
            .file_count
            == settings.repos.large_file_type_repo.files_count
        ), 'Imported files count did not meet the expectation'


class TestInterSatelliteSync:
    """Implements InterSatellite Sync tests in CLI"""

    @pytest.mark.stubbed
    @pytest.mark.upgrade
    def test_positive_reimport_repo(self):
        """Packages missing from upstream are removed from downstream on reimport.

        :id: b3a71405-d8f0-4085-b728-8fc3513611c8

        :steps:
            1. From upstream Export repo fully and import it in downstream.
            2. In upstream delete some packages from repo.
            3. Re-export the full repo.
            4. In downstream, reimport the repo re-exported.

        :expectedresults:
            1. Deleted packages from upstream are removed from downstream.

        :CaseAutomation: NotAutomated

        """

    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_export_repo_incremental_with_history_id(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_synced_rh_repo,
    ):
        """Test incremental export with history id.

        :id: 1e8bc352-198f-4d59-b437-1b184141fab4

        :parametrized: yes

        :setup:
            1. Enabled and synced RH repository.

        :steps:
            1. Run repo complete export, ensure it's listed in history.
            2. Run incremental export using history id of the complete export,
               ensure it's listed in history.
            3. Run incremental export using non-existent history id.

        :expectedresults:
            1. First (complete) export succeeds and can be listed including history id.
            2. Second (incremental) export succeeds and can be listed including history id.
            3. Third (incremental) export fails when wrong id is provided.

        """
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''

        # Run repo complete export, ensure it's listed in history.
        target_sat.cli.ContentExport.completeRepository({'id': function_synced_rh_repo['id']})
        assert '1.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )

        history = target_sat.cli.ContentExport.list(
            {'organization-id': function_sca_manifest_org.id}
        )
        assert len(history) == 1, 'Expected just one item in the export history'

        # Run incremental export using history id of the complete export,
        # ensure it's listed in history.
        target_sat.cli.ContentExport.incrementalRepository(
            {'id': function_synced_rh_repo['id'], 'from-history-id': history[0]['id']}
        )
        assert '2.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )

        history = target_sat.cli.ContentExport.list(
            {'organization-id': function_sca_manifest_org.id}
        )
        assert len(history) == 2, 'Expected two items in the export history'
        assert int(history[1]['id']) == int(history[0]['id']) + 1, 'Inconsistent history spotted'

        # Run incremental export using non-existent history id.
        next_id = int(history[1]['id']) + 1
        with pytest.raises(CLIReturnCodeError) as error:
            target_sat.cli.ContentExport.incrementalRepository(
                {'id': function_synced_rh_repo['id'], 'from-history-id': next_id}
            )
        assert (
            f"Couldn't find Katello::ContentViewVersionExportHistory with 'id'={next_id}"
            in error.value.message
        ), 'Unexpected error message'

    @pytest.mark.upgrade
    def test_positive_export_import_incremental_yum_repo(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_org,
        function_import_org,
        function_synced_custom_repo,
    ):
        """Export and import custom YUM repo contents incrementally.

        :id: 318560d7-71f5-4646-ab5c-12a2ec22d031

        :setup:
            1. Enabled and synced custom yum repository.

        :steps:
            1. First, export and import whole custom YUM repo.
            2. Add some packages to the earlier exported YUM repo.
            3. Incrementally export the custom YUM repo.
            4. Import the exported YUM repo contents incrementally.

        :expectedresults:
            1. Complete export and import succeeds, product and repository is created
               in the importing organization and content counts match.
            2. Incremental export and import succeeds, content counts match the updated counts.

        """
        export_cc = target_sat.cli.Repository.info({'id': function_synced_custom_repo.id})[
            'content-counts'
        ]

        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        # Export complete and check the export directory
        export = target_sat.cli.ContentExport.completeRepository(
            {'id': function_synced_custom_repo['id']}
        )
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

        # Run import and verify the product and repo is created
        # in the importing org and the content counts match.
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        target_sat.cli.ContentImport.repository(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        import_repo = target_sat.cli.Repository.info(
            {
                'organization-id': function_import_org.id,
                'name': function_synced_custom_repo.name,
                'product': function_synced_custom_repo.product.name,
            }
        )
        assert import_repo['content-counts'] == export_cc, 'Import counts do not match the export.'

        # Upload custom content into the repo
        with open(DataFile.RPM_TO_UPLOAD, 'rb') as handle:
            result = target_sat.api.Repository(id=function_synced_custom_repo.id).upload_content(
                files={'content': handle}
            )
            assert 'success' in result['status']

        # Export incremental and check the export directory
        export = target_sat.cli.ContentExport.incrementalRepository(
            {'id': function_synced_custom_repo['id']}
        )
        assert '2.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

        # Run the import and verify the content counts match the updated counts.
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        target_sat.cli.ContentImport.repository(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        import_repo = target_sat.cli.Repository.info(
            {
                'organization-id': function_import_org.id,
                'name': function_synced_custom_repo.name,
                'product': function_synced_custom_repo.product.name,
            }
        )
        export_cc['packages'] = str(int(export_cc['packages']) + 1)
        assert import_repo['content-counts'] == export_cc, 'Import counts do not match the export.'

    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_export_import_mismatch_label(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_import_org_with_manifest,
        function_synced_rh_repo,
    ):
        """Export and import repo with mismatched label

        :id: eb2f3e8e-3ee6-4713-80ab-3811a098e079

        :parametrized: yes

        :setup:
            1. Enabled and synced RH yum repository.

        :steps:
            1. Export and import a RH yum repo, verify it was imported.
            2. Export the repo again and change the repository label.
            3. Import the changed repository again, it should succeed without errors.

        :expectedresults:
            1. All exports and imports succeed.

        :CaseImportance: Medium

        :BZ: 2092039

        :customerscenario: true
        """
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export the repository and check the export directory
        export = target_sat.cli.ContentExport.completeRepository(
            {'id': function_synced_rh_repo['id']}
        )
        assert '1.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )

        # Run import and verify the product and repo is created in the importing org
        import_path = target_sat.move_pulp_archive(function_sca_manifest_org, export['message'])
        target_sat.cli.ContentImport.repository(
            {'organization-id': function_import_org_with_manifest.id, 'path': import_path},
            timeout='5m',
        )
        import_repo = target_sat.cli.Repository.info(
            {
                'name': function_synced_rh_repo['name'],
                'product': function_synced_rh_repo['product']['name'],
                'organization-id': function_sca_manifest_org.id,
            }
        )
        assert import_repo

        # Export again and check the export directory
        export = target_sat.cli.ContentExport.completeRepository(
            {'id': function_synced_rh_repo['id']}
        )
        assert '2.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )

        # Change the repo label in metadata.json and run the import again
        import_path = target_sat.move_pulp_archive(function_sca_manifest_org, export['message'])
        target_sat.execute(
            f'''sed -i 's/"label":"{function_synced_rh_repo['label']}"/'''
            f'''"label":"{gen_string("alpha")}"/g' {import_path}/metadata.json'''
        )
        target_sat.cli.ContentImport.repository(
            {'organization-id': function_import_org_with_manifest.id, 'path': import_path},
            timeout='5m',
        )

        # Verify that both import tasks succeeded
        tasks = target_sat.cli.Task.list_tasks(
            {'search': f"Import Repository organization '{function_import_org_with_manifest.name}'"}
        )
        assert len(tasks) == 2, f'Expected 2 import tasks in this Org but found {len(tasks)}'
        assert all(['success' in task['result'] for task in tasks]), (
            'Not every import task succeeded'
        )

    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_custom_cdn_with_credential(
        self,
        request,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_synced_rh_repo,
        satellite_host,
        function_sca_manifest,
    ):
        """Export and sync repository using custom cert for custom CDN.

        :id: de1f4b06-267a-4bad-9a90-665f2906ef5f

        :parametrized: yes

        :setup:
            1. Upstream Satellite with enabled and synced RH yum repository.
            2. Downstream Satellite to sync from Upstream Satellite.

        :steps:
            On the Upstream Satellite:
                1. Export the repository in syncable format and move it
                   to /var/www/html/pub/repos to mimic custom CDN.
            On the Downstream Satellite:
                2. Create new Organization, import manifest.
                3. Create Content Credentials with Upstream Satellite's katello-server-ca.crt.
                4. Set the CDN configuration to custom CDN and use the url and CC from above.
                5. Enable and sync the repository.

        :expectedresults:
            1. Repository can be enabled and synced from Upstream to Downstream Satellite.

        :BZ: 2112098

        :customerscenario: true
        """
        meta_file = 'metadata.json'
        crt_file = 'source.crt'
        pub_dir = '/var/www/html/pub/repos'
        request.addfinalizer(lambda: target_sat.execute(f'rm -rf {pub_dir}'))

        # Export the repository in syncable format and move it
        # to /var/www/html/pub/repos to mimic custom CDN.
        target_sat.cli.ContentExport.completeRepository(
            {'id': function_synced_rh_repo['id'], 'format': 'syncable'}
        )
        assert '1.0' in target_sat.validate_pulp_filepath(
            function_sca_manifest_org, PULP_EXPORT_DIR
        )
        exp_dir = target_sat.execute(
            f'find {PULP_EXPORT_DIR}{function_sca_manifest_org.name}/ -name {meta_file}'
        ).stdout.splitlines()
        assert len(exp_dir) == 1
        exp_dir = exp_dir[0].replace(meta_file, '')

        assert target_sat.execute(f'mv {exp_dir} {pub_dir}').status == 0
        target_sat.execute(f'semanage fcontext -a -t httpd_sys_content_t "{pub_dir}(/.*)?"')
        target_sat.execute(f'restorecon -R {pub_dir}')

        # Create new Organization, import manifest.
        import_org = satellite_host.api.Organization().create()
        satellite_host.upload_manifest(import_org.id, function_sca_manifest.content)

        # Create Content Credentials with Upstream Satellite's katello-server-ca.crt.
        satellite_host.execute(
            f'curl -o {crt_file} http://{target_sat.hostname}/pub/katello-server-ca.crt'
        )
        cc = satellite_host.cli.ContentCredential.create(
            {
                'name': gen_string('alpha'),
                'organization-id': import_org.id,
                'path': crt_file,
                'content-type': 'cert',
            }
        )
        assert cc, 'No content credential created'

        # Set the CDN configuration to custom CDN and use the url and CC from above.
        res = satellite_host.cli.Org.configure_cdn(
            {
                'id': import_org.id,
                'type': 'custom_cdn',
                'ssl-ca-credential-id': cc['id'],
                'url': f'https://{target_sat.hostname}/pub/repos/',
            }
        )
        assert 'Updated CDN configuration' in res

        # Enable and sync the repository.
        reposet = satellite_host.cli.RepositorySet.list(
            {
                'organization-id': import_org.id,
                'search': f'content_label={function_synced_rh_repo["content-label"]}',
            }
        )
        assert len(reposet) == 1, (
            f'Expected just one reposet for "{function_synced_rh_repo["content-label"]}"'
        )
        res = satellite_host.cli.RepositorySet.enable(
            {
                'organization-id': import_org.id,
                'id': reposet[0]['id'],
                'basearch': DEFAULT_ARCHITECTURE,
            }
        )
        assert 'Repository enabled' in str(res)

        repos = satellite_host.cli.Repository.list({'organization-id': import_org.id})
        assert len(repos) == 1, 'Expected 1 repo enabled'
        repo = repos[0]
        satellite_host.cli.Repository.synchronize({'id': repo['id']})

        repo = satellite_host.cli.Repository.info({'id': repo['id']})
        assert f'{target_sat.hostname}/pub/repos/' in repo['url'], (
            'Enabled repo does not point to the upstream Satellite'
        )
        assert 'Success' in repo['sync']['status'], 'Sync did not succeed'
        assert repo['content-counts'] == function_synced_rh_repo['content-counts'], (
            'Content counts do not match'
        )

    @pytest.mark.e2e
    @pytest.mark.pit_server
    @pytest.mark.pit_client
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    def test_positive_export_import_consume_incremental_yum_repo(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_org,
        function_import_org,
        function_synced_custom_repo,
        rhel_contenthost,
    ):
        """Export and import custom repo incrementally and consume it on a content host.

        :id: f5515168-c3c9-4351-9f83-ba6265689db3

        :setup:
            1. Enabled and synced custom yum repository.

        :steps:
            1. Create a CV with the yum repository.
            2. Add exclude RPM filter to filter out one package, publish version 1 and export it.
            3. On the importing side import version 1, check the package count.
            4. Create an AK with the imported CV, register the content host and check
               the package count available to install. Filtered package should be missing.
            5. Update the filter so no package is left behind, publish version 2 and export it.
            6. Import version 2, check the package count.
            7. Check the package count available to install on the content host.
            8. Install the package.

        :expectedresults:
            1. More packages available for install after version 2 imported.
            2. Packages can be installed successfully.

        :BZ: 2173756

        :customerscenario: true
        """
        # Create a CV with the RH yum repository.
        exp_cv = target_sat.cli_factory.make_content_view(
            {
                'organization-id': function_org.id,
                'repository-ids': [function_synced_custom_repo['id']],
            }
        )

        # Add exclude RPM filter to filter out one package, publish version 1 and export it.
        filtered_pkg = 'dog'
        cvf = target_sat.cli_factory.make_content_view_filter(
            {'content-view-id': exp_cv['id'], 'type': 'rpm'}
        )
        cvf_rule = target_sat.cli_factory.content_view_filter_rule(
            {'content-view-filter-id': cvf['filter-id'], 'name': filtered_pkg}
        )
        target_sat.cli.ContentView.publish({'id': exp_cv['id']})
        exp_cv = target_sat.cli.ContentView.info({'id': exp_cv['id']})
        assert len(exp_cv['versions']) == 1
        cvv_1 = exp_cv['versions'][0]
        pkg_cnt_1 = target_sat.api.ContentViewVersion(id=cvv_1['id']).read().package_count
        export_1 = target_sat.cli.ContentExport.completeVersion({'id': cvv_1['id']})
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

        # On the importing side import version 1, check the package count.
        import_path1 = target_sat.move_pulp_archive(function_org, export_1['message'])
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path1}
        )
        imp_cv = target_sat.cli.ContentView.info(
            {'name': exp_cv['name'], 'organization-id': function_import_org.id}
        )
        assert len(imp_cv['versions']) == 1
        imp_cvv = imp_cv['versions'][0]
        assert target_sat.api.ContentViewVersion(id=imp_cvv['id']).read().package_count == pkg_cnt_1

        # Create an AK with the imported CV, register the content host and check
        # the package count available to install. Filtered package should be missing.
        ak = target_sat.cli_factory.make_activation_key(
            {
                'content-view': exp_cv['name'],
                'lifecycle-environment': ENVIRONMENT,
                'organization-id': function_import_org.id,
            }
        )
        repo_content_label = target_sat.cli.Repository.info(
            {
                'name': function_synced_custom_repo['name'],
                'product': function_synced_custom_repo['product']['name'],
                'organization-id': function_import_org.id,
            }
        )['content-label']
        target_sat.cli.ActivationKey.content_override(
            {
                'id': ak.id,
                'content-label': repo_content_label,
                'value': 'true',
            }
        )
        res = rhel_contenthost.register(function_import_org, None, ak.name, target_sat)
        assert res.status == 0, (
            f'Failed to register host: {rhel_contenthost.hostname}\n'
            f'StdOut: {res.stdout}\nStdErr: {res.stderr}'
        )
        assert rhel_contenthost.subscribed
        res = rhel_contenthost.execute('dnf clean all && dnf repolist -v')
        assert res.status == 0
        assert f'Repo-available-pkgs: {pkg_cnt_1}' in res.stdout, (
            'Package count available on the host did not meet the expectation'
        )

        res = rhel_contenthost.execute(f'dnf -y install {filtered_pkg}')
        assert res.status, 'Installation of filtered package succeeded unexpectedly'
        assert f'No match for argument: {filtered_pkg}' in res.stdout

        # Update the filter so that no package is left behind, publish version 2 and export it.
        target_sat.cli.ContentView.filter.rule.update(
            {
                'content-view-filter-id': cvf['filter-id'],
                'id': cvf_rule['rule-id'],
                'name': gen_string('alpha'),
            }
        )
        target_sat.cli.ContentView.publish({'id': exp_cv['id']})
        exp_cv = target_sat.cli.ContentView.info({'id': exp_cv['id']})
        assert len(exp_cv['versions']) == 2
        cvv_2 = max(exp_cv['versions'], key=lambda x: int(x['id']))
        pkg_cnt_2 = target_sat.api.ContentViewVersion(id=cvv_2['id']).read().package_count
        assert pkg_cnt_2 > pkg_cnt_1
        export_2 = target_sat.cli.ContentExport.incrementalVersion({'id': cvv_2['id']})
        assert '2.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

        # Import version 2, check the package count.
        import_path2 = target_sat.move_pulp_archive(function_org, export_2['message'])
        target_sat.cli.ContentImport.version(
            {'organization-id': function_import_org.id, 'path': import_path2}
        )
        imp_cv = target_sat.cli.ContentView.info(
            {'name': exp_cv['name'], 'organization-id': function_import_org.id}
        )
        assert len(imp_cv['versions']) == 2
        imp_cvv = max(imp_cv['versions'], key=lambda x: int(x['id']))

        # Get actual package count from export organization
        package_count = int(
            target_sat.cli.Repository.info(
                {
                    'name': function_synced_custom_repo['name'],
                    'product': function_synced_custom_repo['product']['name'],
                    'organization-id': function_org.id,
                }
            )['content-counts']['packages']
        )
        assert (
            target_sat.api.ContentViewVersion(id=imp_cvv['id']).read().package_count
            == pkg_cnt_2
            == package_count
        ), 'Unexpected package count after second import'

        # Check the package count available to install on the content host.
        res = rhel_contenthost.execute('dnf clean all && dnf repolist -v')
        assert res.status == 0
        assert f'Repo-available-pkgs: {pkg_cnt_2}' in res.stdout, (
            'Package count available on the host did not meet the expectation'
        )

        # Install the package.
        res = rhel_contenthost.execute(f'dnf -y install {filtered_pkg}')
        assert res.status == 0, f'Installation from the import failed:\n{res.stdout}'


@pytest.fixture(scope='module')
def module_downstream_sat(module_satellite_host):
    """Provides Downstream Satellite."""
    module_satellite_host.cli.Settings.set(
        {'name': 'subscription_connection_enabled', 'value': 'No'}
    )
    return module_satellite_host


@pytest.fixture
def function_downstream_org(module_downstream_sat, function_sca_manifest):
    """Provides organization with manifest on Downstream Satellite."""
    org = module_downstream_sat.api.Organization().create()
    module_downstream_sat.upload_manifest(org.id, function_sca_manifest.content)
    return org


def _set_downstream_org(
    downstream_sat,
    upstream_sat,
    downstream_org,
    upstream_org='Default_Organization',
    username=settings.server.admin_username,
    password=settings.server.admin_password,
    lce_label=None,
    cv_label=None,
):
    """Configures Downstream organization to sync from particular Upstream organization.

    :param downstream_sat: Downstream Satellite instance.
    :param upstream_sat: Upstream Satellite instance.
    :param downstream_org: Downstream organization to be configured.
    :param upstream_org: Upstream organization to sync CDN content from,
                         default: Default_Organization
    :param username: Username for authentication, default: admin username from settings.
    :param password: Password for authentication, default: admin password from settings.
    :param lce_label: Upstream Lifecycle Environment, default: Library
    :param cv_label: Upstream Content View Label, default: Default_Organization_View.
    :return: True if succeeded.
    """
    # Create Content Credentials with Upstream Satellite's katello-server-ca.crt.
    crt_file = f'{upstream_sat.hostname}.crt'
    downstream_sat.execute(
        f'curl -o {crt_file} http://{upstream_sat.hostname}/pub/katello-server-ca.crt'
    )
    cc = downstream_sat.cli.ContentCredential.create(
        {
            'name': upstream_sat.hostname,
            'organization-id': downstream_org.id,
            'path': crt_file,
            'content-type': 'cert',
        }
    )
    # Set the CDN configuration to Network Sync.
    res = downstream_sat.cli.Org.configure_cdn(
        {
            'id': downstream_org.id,
            'type': 'network_sync',
            'url': f'https://{upstream_sat.hostname}/',
            'username': username,
            'password': password,
            'upstream-organization-label': upstream_org.label,
            'upstream-lifecycle-environment-label': lce_label,
            'upstream-content-view-label': cv_label,
            'ssl-ca-credential-id': cc['id'],
        }
    )
    return 'Updated CDN configuration' in res


class TestNetworkSync:
    """Implements Network Sync scenarios."""

    @pytest.mark.pit_server
    @pytest.mark.parametrize(
        'function_synced_rh_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_network_sync_rh_repo(
        self,
        target_sat,
        function_sca_manifest_org,
        function_synced_rh_repo,
        module_downstream_sat,
        function_downstream_org,
    ):
        """Sync a RH repo from Upstream to Downstream Satellite

        :id: fdb58c18-0a64-418b-990d-2233381fee8f

        :parametrized: yes

        :setup:
            1. Enabled and synced RH yum repository at Upstream Sat.
            2. Organization with manifest at Downstream Sat.

        :steps:
            1. Set the Downstream org to sync from Upstream org.
            2. Enable and sync the repository from Upstream to Downstream.

        :expectedresults:
            1. Repository can be enabled and synced.

        :BZ: 2213128

        :customerscenario: true

        """
        assert _set_downstream_org(
            downstream_sat=module_downstream_sat,
            upstream_sat=target_sat,
            downstream_org=function_downstream_org,
            upstream_org=function_sca_manifest_org,
        ), 'Downstream org configuration failed'

        # Enable and sync the repository.
        reposet = module_downstream_sat.cli.RepositorySet.list(
            {
                'organization-id': function_downstream_org.id,
                'search': f'content_label={function_synced_rh_repo["content-label"]}',
            }
        )
        assert len(reposet) == 1, (
            f'Expected just one reposet for "{function_synced_rh_repo["content-label"]}"'
        )
        res = module_downstream_sat.cli.RepositorySet.enable(
            {
                'organization-id': function_downstream_org.id,
                'id': reposet[0]['id'],
                'basearch': DEFAULT_ARCHITECTURE,
            }
        )
        assert 'Repository enabled' in str(res), 'Repository enable failed'

        repos = module_downstream_sat.cli.Repository.list(
            {'organization-id': function_downstream_org.id}
        )
        assert len(repos) == 1, 'Expected 1 repo enabled'
        repo = repos[0]
        module_downstream_sat.cli.Repository.synchronize({'id': repo['id']})

        repo = module_downstream_sat.cli.Repository.info({'id': repo['id']})
        assert 'Success' in repo['sync']['status'], 'Sync did not succeed'
        assert repo['content-counts'] == function_synced_rh_repo['content-counts'], (
            'Content counts do not match'
        )


class TestPodman:
    """Tests specific to using podman push/pull on Satellite

    :CaseComponent: Repositories

    :team: Phoenix-content
    """

    @pytest.fixture(scope='class')
    def enable_podman(module_product, module_target_sat):
        """Enable base_os and appstream repos on the sat through cdn registration and install podman."""
        module_target_sat.register_to_cdn()
        if module_target_sat.os_version.major > 7:
            module_target_sat.enable_repo(module_target_sat.REPOS['rhel_bos']['id'])
            module_target_sat.enable_repo(module_target_sat.REPOS['rhel_aps']['id'])
        else:
            module_target_sat.enable_repo(module_target_sat.REPOS['rhscl']['id'])
            module_target_sat.enable_repo(module_target_sat.REPOS['rhel']['id'])
        result = module_target_sat.execute(
            'dnf install -y --disableplugin=foreman-protector podman'
        )
        assert result.status == 0

    def test_postive_export_import_podman_repo(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_org,
        function_product,
        function_import_org,
        enable_podman,
    ):
        """Test import of a repo created via Podman push

        :id: d44f494c-918f-4cf0-8eae-5b382505e371

        :steps:
            1. Export the repository.
            2. Import the repository, and compare tag and container counts.

        :expectedresults:
            1. Export and import succeeds without any errors.

        :CaseImportance: Medium

        :Verifies: SAT-25265
        """
        REPO_NAME = 'fedora'
        result = target_sat.execute(f'podman pull registry.fedoraproject.org/{REPO_NAME}')
        assert result.status == 0
        large_image_id = target_sat.execute(f'podman images {REPO_NAME} -q')
        assert large_image_id
        large_repo_cmd = f'{(function_org.label)}/{(function_product.label)}/{REPO_NAME}'.lower()
        target_sat.execute(
            f'podman push --creds admin:changeme {large_image_id.stdout.strip()} {target_sat.hostname}/{large_repo_cmd}'
        )
        repo = target_sat.cli.Repository.info(
            {
                'organization-id': function_org.id,
                'id': target_sat.cli.Repository.list({'organization-id': function_org.id})[0]['id'],
            }
        )
        assert repo['content-counts']['container-tags'] == '1'
        assert repo['content-counts']['container-manifests'] == '1'
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        export = target_sat.cli.ContentExport.completeRepository({'id': repo['id']})
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)
        import_path = target_sat.move_pulp_archive(function_org, export['message'])
        # Check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import files and verify content
        target_sat.cli.ContentImport.library(
            {'organization-id': function_import_org.id, 'path': import_path}
        )
        assert target_sat.cli.Product.list({'organization-id': function_import_org.id})
        import_repo = target_sat.cli.Repository.info(
            {
                'organization-id': function_import_org.id,
                'id': target_sat.cli.Repository.list({'organization-id': function_import_org.id})[
                    0
                ]['id'],
            }
        )
        assert import_repo['name'] == repo['name']
        assert import_repo['content-type'] == repo['content-type']
        assert (
            import_repo['content-counts']['container-tags']
            == repo['content-counts']['container-tags']
        )
        assert (
            import_repo['content-counts']['container-manifests']
            == repo['content-counts']['container-manifests']
        )
