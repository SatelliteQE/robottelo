"""Test class for InterSatellite Sync

:Requirement: Satellitesync

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: InterSatelliteSync

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
from time import sleep

from fauxfactory import gen_string
from manifester import Manifester
import pytest
from wait_for import wait_for

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.content_export import ContentExport
from robottelo.cli.content_import import ContentImport
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    make_content_view,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.package import Package
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.cli.settings import Settings
from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
    DEFAULT_ARCHITECTURE,
    DEFAULT_CV,
    EXPORT_LIBRARY_NAME,
    PULP_EXPORT_DIR,
    PULP_IMPORT_DIR,
    REPO_TYPE,
    REPOS,
    DataFile,
)
from robottelo.constants.repos import ANSIBLE_GALAXY


@pytest.fixture(scope='class')
def config_export_import_settings():
    """Check settings and set download policy for export.  Reset to original state after import"""
    download_policy_value = Settings.info({'name': 'default_download_policy'})['value']
    rh_download_policy_value = Settings.info({'name': 'default_redhat_download_policy'})['value']
    subs_conn_enabled_value = Settings.info({'name': 'subscription_connection_enabled'})['value']
    Settings.set({'name': 'default_redhat_download_policy', 'value': 'immediate'})
    yield
    Settings.set({'name': 'default_download_policy', 'value': download_policy_value})
    Settings.set({'name': 'default_redhat_download_policy', 'value': rh_download_policy_value})
    Settings.set({'name': 'subscription_connection_enabled', 'value': subs_conn_enabled_value})


@pytest.fixture(scope='function')
def export_import_cleanup_function(target_sat, function_org):
    """Deletes export/import dirs of function org"""
    yield
    target_sat.execute(
        f'rm -rf {PULP_EXPORT_DIR}/{function_org.name} {PULP_IMPORT_DIR}/{function_org.name}'
    )


@pytest.fixture(scope='function')  # perform the cleanup after each testcase of a module
def export_import_cleanup_module(target_sat, module_org):
    """Deletes export/import dirs of module_org"""
    yield
    target_sat.execute(
        f'rm -rf {PULP_EXPORT_DIR}/{module_org.name} {PULP_IMPORT_DIR}/{module_org.name}'
    )


@pytest.fixture(scope='function')
def function_import_org(target_sat):
    """Creates an Organization for content import."""
    org = target_sat.api.Organization().create()
    yield org


@pytest.fixture(scope='function')
def function_import_org_with_manifest(target_sat, function_import_org):
    """Creates and sets an Organization with a brand-new manifest for content import."""
    with Manifester(manifest_category=settings.manifest.golden_ticket) as manifest:
        target_sat.upload_manifest(function_import_org.id, manifest)
    yield function_import_org


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
    yield repo


@pytest.fixture(scope='function')
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
    yield repo


@pytest.fixture(scope='function')
def function_synced_rhel_repo(request, target_sat, function_sca_manifest_org):
    """Enable and synchronize rhel content with immediate policy"""
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
    target_sat.cli.Repository.synchronize({'id': repo['id']}, timeout=7200000)
    repo = target_sat.cli.Repository.info(
        {
            'organization-id': function_sca_manifest_org.id,
            'name': repo_dict['name'],
            'product': repo_dict['product'],
        }
    )
    return repo


@pytest.fixture(scope='function')
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
    yield repo


@pytest.fixture(scope='function')
def function_synced_docker_repo(target_sat, function_org):
    product = target_sat.cli_factory.make_product({'organization-id': function_org.id})
    repo = target_sat.cli_factory.make_repository(
        {
            'organization-id': function_org.id,
            'product-id': product['id'],
            'content-type': REPO_TYPE['docker'],
            'download-policy': 'immediate',
            'url': CONTAINER_REGISTRY_HUB,
            'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
        }
    )
    target_sat.cli.Repository.synchronize({'id': repo['id']})
    yield repo


@pytest.fixture(scope='function')
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
    yield repo


@pytest.mark.run_in_one_thread
class TestRepositoryExport:
    """Tests for exporting a repository via CLI"""

    @pytest.mark.tier3
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

        :CaseLevel: System

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

    @pytest.mark.tier3
    def test_positive_export_library_custom_repo(
        self, target_sat, export_import_cleanup_function, function_org, function_synced_custom_repo
    ):
        """Export custom repo via complete and incremental library export.

        :id: ba8dc7f3-55c2-4120-ac76-cc825ef0abb8

        :setup:
            1. Product with synced custom repository.

        :steps:
            1. Create a CV, add the product and publish it.
            2. Export complete library.
            3. Export incremental library.

        :expectedresults:
            1. Complete export succeeds, exported files are present on satellite machine.
            2. Incremental export succeeds, exported files are present on satellite machine.

        :CaseLevel: System
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
        target_sat.cli.ContentExport.completeLibrary({'organization-id': function_org.id})
        assert '1.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)
        # Export incremental and check the export directory
        target_sat.cli.ContentExport.incrementalLibrary({'organization-id': function_org.id})
        assert '2.0' in target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR)

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'function_synced_rhel_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_export_complete_library_rh_repo(
        self,
        target_sat,
        export_import_cleanup_function,
        function_sca_manifest_org,
        function_synced_rhel_repo,
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

        :CaseLevel: System
        """
        # Create cv and publish
        cv_name = gen_string('alpha')
        cv = make_content_view({'name': cv_name, 'organization-id': function_sca_manifest_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_sca_manifest_org.id,
                'repository-id': function_synced_rhel_repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) == ''
        # Export content view
        ContentExport.completeLibrary({'organization-id': function_sca_manifest_org.id})
        # Verify export directory is not empty
        assert target_sat.validate_pulp_filepath(function_sca_manifest_org, PULP_EXPORT_DIR) != ''

    @pytest.mark.tier3
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

    @pytest.mark.tier3
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
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
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
def class_export_entities(module_org):
    """Setup custom repos for export"""
    exporting_prod_name = gen_string('alpha')
    product = make_product({'organization-id': module_org.id, 'name': exporting_prod_name})
    exporting_repo_name = gen_string('alpha')
    exporting_repo = make_repository(
        {
            'name': exporting_repo_name,
            'mirror-on-sync': 'no',
            'download-policy': 'immediate',
            'product-id': product['id'],
        }
    )
    Repository.synchronize({'id': exporting_repo['id']})
    exporting_cv_name = gen_string('alpha')
    exporting_cv, exporting_cvv_id = _create_cv(exporting_cv_name, exporting_repo, module_org)
    return {
        'exporting_org': module_org,
        'exporting_prod_name': exporting_prod_name,
        'exporting_repo_name': exporting_repo_name,
        'exporting_repo': exporting_repo,
        'exporting_cv_name': exporting_cv_name,
        'exporting_cv': exporting_cv,
        'exporting_cvv_id': exporting_cvv_id,
    }


def _create_cv(cv_name, repo, module_org, publish=True):
    """Creates CV and/or publishes in organization with given name and repository

    :param cv_name: The name of CV to create
    :param repo: The repository directory
    :param organization: The organization directory
    :param publish: Publishes the CV if True else doesnt
    :return: The directory of CV and Content View ID
    """
    description = gen_string('alpha')
    content_view = make_content_view(
        {'name': cv_name, 'description': description, 'organization-id': module_org.id}
    )
    ContentView.add_repository(
        {
            'id': content_view['id'],
            'organization-id': module_org.id,
            'repository-id': repo['id'],
        }
    )
    content_view = ContentView.info({'name': cv_name, 'organization-id': module_org.id})
    cvv_id = None
    if publish:
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv_id = content_view['versions'][0]['id']
    return content_view, cvv_id


class TestContentViewSync:
    """Implements Content View Export Import tests in CLI"""

    @pytest.mark.tier3
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

        :CaseImportance: High

        :CaseLevel: System

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
        for item in ['packages', 'source-rpms', 'package-groups', 'errata', 'module-streams']:
            assert exported_repo['content-counts'][item] == imported_repo['content-counts'][item]

    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'function_synced_rhel_repo',
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
        function_synced_rhel_repo,
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

        :CaseLevel: System

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
                'repository-id': function_synced_rhel_repo['id'],
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

    @pytest.mark.tier3
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

        :CaseImportance: High

        :CaseLevel: System
        """
        exporting_cv_name = importing_cvv = gen_string('alpha')
        exporting_cv, exporting_cvv = _create_cv(
            exporting_cv_name,
            class_export_entities['exporting_repo'],
            class_export_entities['exporting_org'],
            False,
        )
        filter_name = gen_string('alphanumeric')
        ContentView.filter.create(
            {
                'name': filter_name,
                'content-view-id': exporting_cv['id'],
                'inclusion': 'yes',
                'type': 'rpm',
            }
        )
        ContentView.filter.rule.create(
            {
                'name': 'cat',
                'content-view-filter': filter_name,
                'content-view-id': exporting_cv['id'],
            }
        )
        ContentView.publish(
            {
                'id': exporting_cv['id'],
                'organization-id': class_export_entities['exporting_org'].id,
            }
        )
        exporting_cv = ContentView.info({'id': exporting_cv['id']})
        exporting_cvv_id = exporting_cv['versions'][0]['id']
        # Check presence of 1 rpm due to filter
        export_packages = Package.list({'content-view-version-id': exporting_cvv_id})
        assert len(export_packages) == 1
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(module_org, PULP_EXPORT_DIR) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': exporting_cvv_id, 'organization-id': module_org.id}
        )
        import_path = target_sat.move_pulp_archive(module_org, export['message'])

        # Import section
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import file and verify content
        ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
        importing_cvv = ContentView.info(
            {'name': importing_cvv, 'organization-id': importing_org['id']}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
        assert len(imported_packages) == 1
        assert len(export_packages) == len(imported_packages)

    @pytest.mark.tier1
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

        :CaseLevel: System
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

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.e2e
    @pytest.mark.parametrize(
        'function_synced_rhel_repo',
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
        function_synced_rhel_repo,
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

        :CaseImportance: High

        :CaseLevel: System
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
                'repository-id': function_synced_rhel_repo['id'],
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
            timeout=7200000,
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
            timeout=7200000,
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
                'name': function_synced_rhel_repo['name'],
                'product': function_synced_rhel_repo['product']['name'],
                'organization-id': function_sca_manifest_org.id,
            }
        )
        imported_repo = target_sat.cli.Repository.info(
            {
                'name': function_synced_rhel_repo['name'],
                'product': function_synced_rhel_repo['product']['name'],
                'organization-id': function_import_org_with_manifest.id,
            }
        )
        for item in ['packages', 'source-rpms', 'package-groups', 'errata', 'module-streams']:
            assert exported_repo['content-counts'][item] == imported_repo['content-counts'][item]

    @pytest.mark.tier2
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

    @pytest.mark.tier2
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

    @pytest.mark.tier2
    def test_negative_import_invalid_path(self, module_org):
        """Import cv that doesn't exist in path

        :id: 4cc69666-407f-4d66-b3d2-8fe2ed135a5f

        :steps:

            1. Import a cv with a path that doesn't exist

        :expectedresults:

            1. Error 'Unable to sync repositories, no library repository found' should be
                displayed
        """
        export_folder = gen_string('alpha')
        import_path = f'{PULP_IMPORT_DIR}{export_folder}'
        # Import section
        with pytest.raises(CLIReturnCodeError) as error:
            ContentImport.version({'organization-id': module_org.id, 'path': import_path})
        assert (
            f'''Error: Unable to find '{import_path}/metadata.json'. '''
            'If the metadata.json file is at a different location provide it to the '
            '--metadata-file option'
        ) in error.value.message

    @pytest.mark.tier3
    def test_postive_export_cv_with_mixed_content_repos(
        self,
        export_import_cleanup_function,
        target_sat,
        function_org,
        function_synced_custom_repo,
        function_synced_file_repo,
        function_synced_docker_repo,
        function_synced_AC_repo,
    ):
        """Exporting CV version having yum and non-yum(docker) is successful

        :id: ffcdbbc6-f787-4978-80a7-4b44c389bf49

        :setup:
            1. Synced repositories of each content type: yum, file, docker, AC

        :steps:
            1. Create CV, add all setup repos and publish.
            2. Export CV version contents to a directory.

        :expectedresults:
            1. Export succeeds and content is exported.

        :BZ: 1726457

        :customerscenario: true

        """
        content_view = target_sat.cli_factory.make_content_view(
            {'organization-id': function_org.id}
        )
        repos = [
            function_synced_custom_repo,
            function_synced_file_repo,
            function_synced_docker_repo,
            function_synced_AC_repo,
        ]
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
        # check packages
        exported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': exporting_cvv['id']}
        )
        assert len(exported_packages)
        # Verify export directory is empty
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) == ''
        # Export cv
        target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv['id'], 'organization-id': function_org.id}
        )
        # Verify export directory is not empty
        assert target_sat.validate_pulp_filepath(function_org, PULP_EXPORT_DIR) != ''

    @pytest.mark.tier3
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
            3. Create CV, add the file repo and publish.
            4. Export the CV and import it into another organization.
            5. Check the imported CV has files in it.

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

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'function_synced_rhel_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_export_rerun_failed_import(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_synced_rhel_repo,
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
                'repository-id': function_synced_rhel_repo['id'],
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

    @pytest.mark.tier3
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
                'id': Product.list({'organization-id': function_import_org.id})[0]['id'],
            }
        )
        assert import_product['name'] == export_product['name']
        assert len(import_product['content']) == 1
        assert import_product['content'][0]['content-type'] == "ansible_collection"

    @pytest.mark.tier3
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

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'function_synced_rhel_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_negative_import_redhat_cv_without_manifest(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_synced_rhel_repo,
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
                'repository-id': function_synced_rhel_repo['id'],
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

    @pytest.mark.tier2
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

        :bz: 2030101

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

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'function_synced_rhel_repo',
        ['rhae2'],
        indirect=True,
    )
    def test_positive_export_incremental_syncable_check_content(
        self,
        target_sat,
        export_import_cleanup_function,
        config_export_import_settings,
        function_sca_manifest_org,
        function_synced_rhel_repo,
    ):
        """Export complete and incremental CV version in syncable format and assert that all
        files referenced in the repomd.xml (including productid) are present in the exports.

        :id: 6ff771cd-39ef-4865-8ae8-629f4baf5f98

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

        :CaseLevel: System

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
                'repository-id': function_synced_rhel_repo['id'],
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


class TestInterSatelliteSync:
    """Implements InterSatellite Sync tests in CLI"""

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_export_import_cv_incremental(self):
        """Export and Import CV version contents incrementally.

        :id: 3c4dfafb-fabf-406e-bca8-7af1ab551135

        :steps:
            1. In upstream, Export CV version contents to a directory specified in settings.
            2. In downstream, Import these copied contents from some other org/satellite.
            3. In upstream, don't add any new packages to the CV.
            4. Export the CV incrementally.
            5. In downstream, Import the CV incrementally.
            6. In upstream, add new packages to the CV.
            7. Export the CV incrementally.
            8. In downstream, Import the CV incrementally.

        :expectedresults:
            1. On incremental export, only the new packages are exported.
            2. New directory of incremental export with new packages is created.
            3. On first incremental import, no new packages are imported.
            4. On second incremental import, only the new packages are imported.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_reimport_repo(self):
        """Packages missing from upstream are removed from downstream on reimport.

        :id: b3a71405-d8f0-4085-b728-8fc3513611c8

        :steps:

            1. From upstream Export repo fully and import it in downstream.
            2. In upstream delete some packages from repo.
            3. Re-export the full repo.
            4. In downstream, reimport the repo re-exported.

        :expectedresults: Deleted packages from upstream are removed from
            downstream.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_negative_export_repo_from_future_datetime(self):
        """Incremental export fails with future datetime.

        :id: 1e8bc352-198f-4d59-b437-1b184141fab4

        :steps: Export the repo incrementally from the future date time.

        :expectedresults: Error is raised for attempting to export from future
            datetime.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_export_redhat_incremental_yum_repo(self):
        """Export Red Hat YUM repo in directory incrementally.

        :id: be054636-629a-40a0-b414-da3964154bd1

        :steps:

            1. Export whole Red Hat YUM repo.
            2. Add some packages to the earlier exported yum repo.
            3. Incrementally export the yum repo from last exported date.

        :expectedresults: Red Hat YUM repo contents have been exported
            incrementally in separate directory.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_export_import_redhat_incremental_yum_repo(self):
        """Import the exported YUM repo contents incrementally.

        :id: 318560d7-71f5-4646-ab5c-12a2ec22d031

        :steps:

            1. First, Export and Import whole Red Hat YUM repo.
            2. Add some packages to the earlier exported yum repo.
            3. Incrementally export the Red Hat YUM repo from last exported
               date.
            4. Import the exported YUM repo contents incrementally.

        :expectedresults: YUM repo contents have been imported incrementally.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_install_package_from_imported_repos(self):
        """Install packages in client from imported repo of Downstream satellite.

        :id: a81ffb55-398d-4ad0-bcae-5ed48f504ded

        :steps:

            1. Export whole Red Hat YUM repo to a path accessible over HTTP.
            2. Import the Red Hat repository by defining the CDN URL from the
               exported HTTP URL.
            3. In downstream satellite create CV, AK with this imported repo.
            4. Register/Subscribe a client with a downstream satellite.
            5. Attempt to install a package on a client from imported repo of
               downstream.

        :expectedresults: The package is installed on client from imported repo
            of downstream satellite.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """
