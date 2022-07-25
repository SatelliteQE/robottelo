"""Test class for InterSatellite Sync

:Requirement: Satellitesync

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: InterSatelliteSync

:Assignee: rmynar

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os.path
import re
from random import randint

import pytest
from fauxfactory import gen_string

from robottelo import manifests
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.content_export import ContentExport
from robottelo.cli.content_import import ContentImport
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.file import File
from robottelo.cli.package import Package
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.settings import Settings
from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import DEFAULT_CV
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants.repos import ANSIBLE_GALAXY

EXPORT_DIR = '/var/lib/pulp/exports/'
IMPORT_DIR = '/var/lib/pulp/imports/'


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
    # Deletes directories created for export/import test
    target_sat.execute(f'rm -rf {EXPORT_DIR}/{function_org.name}')
    target_sat.execute(f'rm -rf {IMPORT_DIR}/{function_org.name}')


@pytest.fixture(scope='function')  # perform the cleanup after each testcase of a module
def export_import_cleanup_module(target_sat, module_org):
    """Deletes export/import dirs of module_org"""
    yield
    # Deletes directories created for export/import test
    target_sat.execute(f'rm -rf {EXPORT_DIR}/{module_org.name}')
    target_sat.execute(f'rm -rf {IMPORT_DIR}/{module_org.name}')


def validate_filepath(sat_obj, org):
    """Checks the existence of certain files in a dir"""
    result = sat_obj.execute(
        fr'find {EXPORT_DIR}{org.name} -type f \( -name "*.json" -o -name "*.tar.gz" \)'
    )
    return result.stdout


def move_pulp_archive(sat_obj, org, export_message):
    """
    Moves exported archive(s) and its metadata into import directory,
    sets ownership, returns import path
    """
    sat_obj.execute(f'mv {EXPORT_DIR}/{org.name} {IMPORT_DIR}')
    sat_obj.execute(f'chown -R pulp:pulp {IMPORT_DIR}')

    # removes everything before export path,
    # replaces EXPORT_PATH by IMPORT_PATH,
    # removes metadata filename
    import_path = os.path.dirname(re.sub(rf'.*{EXPORT_DIR}', IMPORT_DIR, export_message))

    return import_path


@pytest.mark.run_in_one_thread
class TestRepositoryExport:
    """Tests for exporting a repository via CLI"""

    @pytest.mark.tier3
    def test_positive_export_complete_version_custom_repo(
        self, target_sat, export_import_cleanup_module, module_org
    ):
        """Export a custom repository via complete version

        :id: 9c855866-b9b1-4e32-b3eb-7342fdaa7116

        :expectedresults: Repository was successfully exported, exported files are
            present on satellite machine

        :CaseLevel: System
        """
        # setup custom repo
        cv_name = gen_string('alpha')
        product = make_product({'organization-id': module_org.id})
        repo = make_repository(
            {
                'download-policy': 'immediate',
                'organization-id': module_org.id,
                'product-id': product['id'],
            }
        )
        Repository.synchronize({'id': repo['id']})
        # create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export content view
        ContentExport.completeVersion({'id': cvv['id'], 'organization-id': module_org.id})
        # Verify export directory is not empty
        assert validate_filepath(target_sat, module_org) != ''

    @pytest.mark.tier3
    def test_positive_export_incremental_version_custom_repo(
        self, target_sat, export_import_cleanup_module, module_org
    ):
        """Export custom repo via incremental export

        :id: 1b58dca7-c8bb-4893-a306-5882826da559

        :expectedresults: Repository was successfully exported, exported files are
            present on satellite machine

        :CaseLevel: System
        """
        # Create custom product and repository
        cv_name = gen_string('alpha')
        product = make_product({'organization-id': module_org.id})
        repo = make_repository(
            {
                'download-policy': 'immediate',
                'organization-id': module_org.id,
                'product-id': product['id'],
            }
        )
        Repository.synchronize({'id': repo['id']})
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export complete first, then incremental
        ContentExport.completeVersion({'id': cvv['id'], 'organization-id': module_org.id})
        ContentExport.incrementalVersion({'id': cvv['id'], 'organization-id': module_org.id})
        # Verify export directory is not empty
        assert validate_filepath(target_sat, module_org) != ''

    @pytest.mark.tier3
    def test_positive_export_complete_library_custom_repo(
        self, function_org, export_import_cleanup_function, target_sat
    ):
        """Export custom repo via complete library export

        :id: 5f35654b-fc46-48f0-b064-595e04e2bd7e

        :expectedresults: Repository was successfully exported, exported files are
            present on satellite machine

        :CaseLevel: System
        """
        # Create custom product and repository
        cv_name = gen_string('alpha')
        product = make_product({'organization-id': function_org.id})
        repo = make_repository(
            {
                'download-policy': 'immediate',
                'organization-id': function_org.id,
                'product-id': product['id'],
            }
        )
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        # Verify export directory is empty
        assert validate_filepath(target_sat, function_org) == ''
        # Export content view
        ContentExport.completeLibrary({'organization-id': function_org.id})
        # Verify export directory is not empty
        assert validate_filepath(target_sat, function_org) != ''

    @pytest.mark.tier3
    def test_positive_export_incremental_library_custom_repo(
        self, export_import_cleanup_function, function_org, target_sat
    ):
        """Export custom repo via incremental library export

        :id: ba8dc7f3-55c2-4120-ac76-cc825ef0abb8

        :expectedresults: Repository was successfully exported, exported files are
            present on satellite machine

        :CaseLevel: System
        """
        # Create custom product and repository
        cv_name = gen_string('alpha')
        product = make_product({'organization-id': function_org.id})
        repo = make_repository(
            {
                'download-policy': 'immediate',
                'organization-id': function_org.id,
                'product-id': product['id'],
            }
        )
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        # Verify export directory is empty
        assert validate_filepath(target_sat, function_org) == ''
        # Export complete library, then export incremental
        ContentExport.completeLibrary({'organization-id': function_org.id})
        ContentExport.incrementalLibrary({'organization-id': function_org.id})
        # Verify export directory is not empty
        assert validate_filepath(target_sat, function_org) != ''

    @pytest.mark.skip_if_not_set('fake_manifest')
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_export_complete_version_rh_repo(
        self, target_sat, export_import_cleanup_module, module_org
    ):
        """Export RedHat repo via complete version

        :id: e17898db-ca92-4121-a723-0d4b3cf120eb

        :expectedresults: Repository was successfully exported, exported files are
            present on satellite machine

        :CaseLevel: System
        """
        # Enable RH repository
        cv_name = gen_string('alpha')
        with manifests.clone() as manifest:
            target_sat.put(manifest, manifest.filename)
        Subscription.upload({'file': manifest.filename, 'organization-id': module_org.id})
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhva6'],
                'organization-id': module_org.id,
                'product': PRDS['rhel'],
                'releasever': '6Server',
            }
        )
        repo = Repository.info(
            {
                'name': REPOS['rhva6']['name'],
                'organization-id': module_org.id,
                'product': PRDS['rhel'],
            }
        )
        # Update the download policy to 'immediate' and sync
        Repository.update({'download-policy': 'immediate', 'id': repo['id']})
        Repository.synchronize({'id': repo['id']})
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export content view
        ContentExport.completeVersion({'id': cvv['id'], 'organization-id': module_org.id})
        # Verify export directory is not empty
        assert validate_filepath(target_sat, module_org) != ''

    @pytest.mark.skip_if_not_set('fake_manifest')
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_complete_library_rh_repo(
        self, export_import_cleanup_function, function_org, target_sat
    ):
        """Export RedHat repo via complete library

        :id: ffae18bf-6536-4f11-8002-7bf1568bf7f1

        :expectedresults: Repository was successfully exported, exported files are
            present on satellite machine

        :CaseLevel: System
        """
        # Enable RH repository
        cv_name = gen_string('alpha')
        with manifests.clone() as manifest:
            target_sat.put(manifest, manifest.filename)
        Subscription.upload({'file': manifest.filename, 'organization-id': function_org.id})
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhva6'],
                'organization-id': function_org.id,
                'product': PRDS['rhel'],
                'releasever': '6Server',
            }
        )
        repo = Repository.info(
            {
                'name': REPOS['rhva6']['name'],
                'organization-id': function_org.id,
                'product': PRDS['rhel'],
            }
        )
        # Update the download policy to 'immediate' and sync
        Repository.update({'download-policy': 'immediate', 'id': repo['id']})
        Repository.synchronize({'id': repo['id']}, timeout=7200000)
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        # Verify export directory is empty
        assert validate_filepath(target_sat, function_org) == ''
        # Export content view
        ContentExport.completeLibrary({'organization-id': function_org.id})
        # Verify export directory is not empty
        assert validate_filepath(target_sat, function_org) != ''


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
    content_view = make_content_view({'name': cv_name, 'organization-id': module_org.id})
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


def _enable_rhel_content(sat_obj, module_org, repo_name, releasever=None, product=None, sync=True):
    """Enable and/or Synchronize rhel content

    :param organization: The organization directory into which the rhel
        contents will be enabled
    :param bool sync: Syncs contents to repository if true else doesnt
    :return: Repository cli object
    """
    with manifests.clone() as manifest:
        sat_obj.put(manifest, manifest.filename)
    Subscription.upload({'file': manifest.filename, 'organization-id': module_org.id})
    RepositorySet.enable(
        {
            'basearch': 'x86_64',
            'name': REPOSET[repo_name],
            'organization-id': module_org.id,
            'product': PRDS[product],
            'releasever': releasever,
        }
    )
    repo = Repository.info(
        {
            'name': REPOS[repo_name]['name'],
            'organization-id': module_org.id,
            'product': PRDS[product],
        }
    )
    # Update the download policy to 'immediate'
    Repository.update({'download-policy': 'immediate', 'mirror-on-sync': 'no', 'id': repo['id']})
    if sync:
        # Synchronize the repository
        Repository.synchronize({'id': repo['id']}, timeout=7200000)
    repo = Repository.info(
        {
            'name': REPOS[repo_name]['name'],
            'organization-id': module_org.id,
            'product': PRDS[product],
        }
    )
    return repo


def _import_entities(product, repo, cv, mos='no'):
    """Sets same CV, product and repository in importing organization as
    exporting organization

    :param str product: The product name same as exporting product
    :param str repo: The repo name same as exporting repo
    :param str cv: The cv name same as exporting cv
    :param str mos: Mirror on Sync repo, by default 'no' can override to 'yes'
    :returns dictionary with CLI entities created in this function
    """
    importing_org = make_org()
    importing_prod = make_product({'organization-id': importing_org['id'], 'name': product})
    importing_repo = make_repository(
        {
            'name': repo,
            'mirror-on-sync': mos,
            'download-policy': 'immediate',
            'product-id': importing_prod['id'],
        }
    )
    importing_cv = make_content_view({'name': cv, 'organization-id': importing_org['id']})
    ContentView.add_repository(
        {
            'id': importing_cv['id'],
            'organization-id': importing_org['id'],
            'repository-id': importing_repo['id'],
        }
    )
    return {
        'importing_org': importing_org,
        'importing_repo': importing_repo,
        'importing_cv': importing_cv,
    }


class TestContentViewSync:
    """Implements Content View Export Import tests in CLI

    :CaseComponent: ContentViews

    """

    @pytest.mark.tier3
    def test_positive_export_import_cv_end_to_end(
        self,
        class_export_entities,
        config_export_import_settings,
        export_import_cleanup_module,
        target_sat,
        module_org,
    ):
        """Export the CV and import it.  Ensure that all content is same from
            export to import

        :id: b4fb9386-9b6a-4fc5-a8bf-96d7c80af93e

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version via complete version
            5. Import the exported files to satellite
            6. Check that content of export and import matches

        :expectedresults:

            1. CV version custom contents has been exported to directory
            2. All The exported custom contents has been imported in org/satellite

        :CaseAutomation: Automated

        :CaseComponent: ContentViews

        :CaseImportance: High

        :CaseLevel: System
        """
        export_prod_name = import_prod_name = class_export_entities['exporting_prod_name']
        export_repo_name = import_repo_name = class_export_entities['exporting_repo_name']
        export_cvv_id = class_export_entities['exporting_cvv_id']
        import_cv_name = class_export_entities['exporting_cv_name']
        # check packages
        exported_packages = Package.list({'content-view-version-id': export_cvv_id})
        assert len(exported_packages)
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': export_cvv_id, 'organization-id': module_org.id}
        )
        import_path = move_pulp_archive(target_sat, module_org, export['message'])

        # importing portion
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import files and verify content
        ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
        importing_cvv = ContentView.info(
            {'name': import_cv_name, 'organization-id': importing_org['id']}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
        assert len(imported_packages)
        assert len(exported_packages) == len(imported_packages)
        exported_repo = Repository.info(
            {
                'name': export_repo_name,
                'product': export_prod_name,
                'organization-id': module_org.id,
            }
        )
        imported_repo = Repository.info(
            {
                'name': import_repo_name,
                'product': import_prod_name,
                'organization-id': importing_org['id'],
            }
        )
        for item in ['packages', 'source-rpms', 'package-groups', 'errata', 'module-streams']:
            assert exported_repo['content-counts'][item] == imported_repo['content-counts'][item]

    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_export_import_default_org_view(
        self,
        export_import_cleanup_function,
        function_org,
        config_export_import_settings,
        target_sat,
    ):
        """Export Default Organization View version contents in directory and Import them.

        :id: b8a2c878-cfc2-491c-a71f-74108d6bc247

        :bz: 1671319

        :customerscenario: true

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export `Default Organization View version` contents to a directory
                using complete library
            5. Import those contents from some other org/satellite.

        :expectedresults:

            1. Default Organization View version custom contents has been exported to directory
            2. All The exported custom contents has been imported in org/satellite

        :CaseAutomation: Automated

        :CaseComponent: ContentViews

        :CaseImportance: High

        :CaseLevel: System
        """
        importing_cv_name = DEFAULT_CV
        cv_name = gen_string('alpha')
        export_library = 'Export-Library'
        # Create custom repo
        product = make_product({'organization-id': function_org.id})
        repo = make_repository(
            {
                'download-policy': 'immediate',
                'organization-id': function_org.id,
                'product-id': product['id'],
            }
        )
        Repository.synchronize({'id': repo['id']})
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        content_view = ContentView.info(
            {
                'name': cv_name,
                'organization-id': function_org.id,
            }
        )
        # Verify packages
        default_cvv_id = content_view['versions'][0]['id']
        cv_packages = Package.list({'content-view-version-id': default_cvv_id})
        assert len(cv_packages)
        # Verify export directory is empty
        assert validate_filepath(target_sat, function_org) == ''
        # Export complete library
        export = ContentExport.completeLibrary({'organization-id': function_org.id})
        # Verify 'export-library' is created and packages are there
        import_path = move_pulp_archive(target_sat, function_org, export['message'])
        export_lib_cv = ContentView.info(
            {
                'name': export_library,
                'organization-id': function_org.id,
            }
        )
        export_lib_cvv_id = export_lib_cv['versions'][0]['id']
        exported_lib_packages = Package.list({'content-view-version-id': export_lib_cvv_id})
        assert len(cv_packages)
        assert exported_lib_packages == cv_packages
        # importing portion
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import and verify content of library
        ContentImport.library({'organization-id': importing_org['id'], 'path': import_path})
        importing_cvv = ContentView.info(
            {'name': importing_cv_name, 'organization-id': importing_org['id']}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
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

        :CaseAutomation: Automated

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
        assert validate_filepath(target_sat, module_org) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': exporting_cvv_id, 'organization-id': module_org.id}
        )
        import_path = move_pulp_archive(target_sat, module_org, export['message'])

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
        class_export_entities,
        export_import_cleanup_module,
        config_export_import_settings,
        target_sat,
        module_org,
    ):
        """Export promoted CV version contents in directory and Import them.

        :id: 315ef1f0-e2ad-43ec-adff-453fb71654a7

        :steps:

            1. Create product and repository with contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Promote the CV.
            5. Export CV version contents to a directory
            6. Import those contents from some other org/satellite.

        :expectedresults:

            1. Promoted CV version contents has been exported to directory
            2. Promoted CV version contents has been imported successfully
            3. The imported CV should only be published and not promoted

        :CaseLevel: System
        """
        import_cv_name = class_export_entities['exporting_cv_name']
        export_cv_id = class_export_entities['exporting_cv']['id']
        export_cvv_id = class_export_entities['exporting_cvv_id']
        env = make_lifecycle_environment({'organization-id': module_org.id})
        ContentView.version_promote(
            {
                'id': export_cvv_id,
                'to-lifecycle-environment-id': env['id'],
            }
        )
        promoted_cvv_id = ContentView.info({'id': export_cv_id})['versions'][-1]['id']
        # check packages
        exported_packages = Package.list({'content-view-version-id': promoted_cvv_id})
        assert len(exported_packages)
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': export_cvv_id, 'organization-id': module_org.id}
        )
        import_path = move_pulp_archive(target_sat, module_org, export['message'])

        # importing portion
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        # Move export files to import location and set permission

        # Import and verify content
        ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
        importing_cv_id = ContentView.info(
            {'name': import_cv_name, 'organization-id': importing_org['id']}
        )
        importing_cvv_id = ContentView.info(
            {'name': import_cv_name, 'organization-id': importing_org['id']}
        )['versions']
        assert len(importing_cvv_id) >= 1
        imported_packages = Package.list({'content-view-version-id': importing_cvv_id[0]['id']})
        assert len(imported_packages)
        assert len(exported_packages) == len(imported_packages)
        # Verify the LCE is in Library
        lce = importing_cv_id['lifecycle-environments'][0]['name']
        assert lce == 'Library'

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_export_import_redhat_cv(
        self,
        export_import_cleanup_function,
        config_export_import_settings,
        function_org,
        target_sat,
    ):
        """Export CV version redhat contents in directory and Import them

        :id: f6bd7fa9-396e-44ac-92a3-ab87ce1a7ef5

        :steps:

            1. Enable product and repository with redhat contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite.

        :expectedresults:

            1. CV version redhat contents has been exported to directory
            2. All The exported redhat contents has been imported in org/satellite

        :BZ: 1655239

        :CaseAutomation: Automated

        :CaseComponent: ContentViews

        :CaseImportance: High

        :CaseLevel: System
        """
        # Setup rhel repo
        cv_name = gen_string('alpha')
        with manifests.clone() as manifest:
            target_sat.put(manifest, manifest.filename)
        Subscription.upload({'file': manifest.filename, 'organization-id': function_org.id})
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhva6'],
                'organization-id': function_org.id,
                'product': PRDS['rhel'],
                'releasever': '6Server',
            }
        )
        repo = Repository.info(
            {
                'name': REPOS['rhva6']['name'],
                'organization-id': function_org.id,
                'product': PRDS['rhel'],
            }
        )
        # Update the download policy to 'immediate' and sync
        Repository.update({'download-policy': 'immediate', 'id': repo['id']})
        Repository.synchronize({'id': repo['id']}, timeout=7200000)
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert validate_filepath(target_sat, function_org) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_org.id}
        )
        import_path = move_pulp_archive(target_sat, function_org, export['message'])
        exported_packages = Package.list({'content-view-version-id': cvv['id']})
        assert len(exported_packages)

        # importing portion
        importing_org = make_org()
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        manifests.upload_manifest_locked(
            importing_org['id'], interface=manifests.INTERFACE_CLI, timeout=7200000
        )
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
        # Import file and verify content
        importing_cvv = ContentView.info({'name': cv_name, 'organization-id': importing_org['id']})[
            'versions'
        ]
        assert len(importing_cvv) >= 1
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
        assert len(imported_packages)
        assert len(exported_packages) == len(imported_packages)
        exported_repo = Repository.info(
            {
                'name': repo['name'],
                'product': repo['product']['name'],
                'organization-id': function_org.id,
            }
        )
        imported_repo = Repository.info(
            {
                'name': repo['name'],
                'product': repo['product']['name'],
                'organization-id': importing_org['id'],
            }
        )
        for item in ['packages', 'source-rpms', 'package-groups', 'errata', 'module-streams']:
            assert exported_repo['content-counts'][item] == imported_repo['content-counts'][item]

    @pytest.mark.tier4
    def test_positive_export_import_redhat_cv_with_huge_contents(
        self,
        export_import_cleanup_function,
        config_export_import_settings,
        target_sat,
        function_org,
    ):
        """Export CV version redhat contents in directory and Import them

        :id: 05eb185f-e526-466c-9c14-702dde1d49de

        :steps:

            1. Enable product and repository with redhat repository having huge contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite.

        :expectedresults:

            1. CV version redhat contents has been exported to directory
            2. All The exported redhat contents has been imported in org/satellite

        :BZ: 1655239

        :CaseAutomation: Automated

        :CaseComponent: ContentViews

        :CaseImportance: Critical

        :CaseLevel: Acceptance
        """
        cv_name = gen_string('alpha')

        with manifests.clone() as manifest:
            target_sat.put(manifest, manifest.filename)
        Subscription.upload({'file': manifest.filename, 'organization-id': function_org.id})
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhscl7'],
                'organization-id': function_org.id,
                'product': PRDS['rhscl'],
                'releasever': '7Server',
            }
        )
        repo = Repository.info(
            {
                'name': REPOS['rhscl7']['name'],
                'organization-id': function_org.id,
                'product': PRDS['rhscl'],
            }
        )
        # Update the download policy to 'immediate' and sync
        Repository.update({'download-policy': 'immediate', 'id': repo['id']})
        Repository.synchronize({'id': repo['id']}, timeout=7200000)
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Export cv
        export = ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_org.id}, timeout=7200000
        )
        import_path = move_pulp_archive(target_sat, function_org, export['message'])
        exported_packages = Package.list({'content-view-version-id': cvv['id']})
        assert len(exported_packages)
        # importing portion
        importing_org = make_org()
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import and verify content
        manifests.upload_manifest_locked(
            importing_org['id'], interface=manifests.INTERFACE_CLI, timeout=7200000
        )
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        ContentImport.version(
            {'organization-id': importing_org['id'], 'path': import_path}, timeout=7200000
        )
        importing_cvv = ContentView.info({'name': cv_name, 'organization-id': importing_org['id']})[
            'versions'
        ]
        assert len(importing_cvv) >= 1
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
        assert len(imported_packages)
        assert len(exported_packages) == len(imported_packages)
        exported_repo = Repository.info(
            {
                'name': repo['name'],
                'product': repo['product']['name'],
                'organization-id': function_org.id,
            }
        )
        imported_repo = Repository.info(
            {
                'name': repo['name'],
                'product': repo['product']['name'],
                'organization-id': importing_org['id'],
            }
        )
        for item in ['packages', 'source-rpms', 'package-groups', 'errata', 'module-streams']:
            assert exported_repo['content-counts'][item] == imported_repo['content-counts'][item]

    @pytest.mark.tier2
    def test_negative_import_same_cv_twice(
        self,
        class_export_entities,
        export_import_cleanup_function,
        config_export_import_settings,
        target_sat,
        module_org,
    ):
        """Import the same cv twice

        :id: 15a7ddd3-c1a5-4b22-8460-6cb2b8ea4ef9

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite.
            6. Attempt to reimport the same contents

        :expectedresults:

            1. Reimporting the contents with same version fails
            2. Satellite displays an error message
        """
        export_cvv_id = class_export_entities['exporting_cvv_id']
        export_cv_name = class_export_entities['exporting_cv_name']
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': export_cvv_id, 'organization-id': module_org.id}
        )
        import_path = move_pulp_archive(target_sat, module_org, export['message'])

        # importing portion
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import section
        ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
        with pytest.raises(CLIReturnCodeError) as error:
            ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
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
        import_path = f'{IMPORT_DIR}{export_folder}'
        # Import section
        with pytest.raises(CLIReturnCodeError) as error:
            ContentImport.version({'organization-id': module_org.id, 'path': import_path})
        assert (
            f'''Error: Unable to find '{import_path}/metadata.json'. '''
            'If the metadata.json file is at a different location provide it to the '
            '--metadata-file option'
        ) in error.value.message

    @pytest.mark.skip_if_open("BZ:1998626")
    @pytest.mark.skip_if_open("BZ:2067275")
    @pytest.mark.tier2
    def test_negative_export_cv_with_on_demand_repo(
        self, export_import_cleanup_function, module_org
    ):
        """Exporting CV version having on_demand repo throws error

        :id: f8b86d0e-e1a7-4e19-bb82-6de7d16c6676

        :steps:

            1. Create product and on-demand repository with custom contents
            2. Sync the repository
            3. Create CV with above product and publish
            4. Attempt to export CV version contents to a directory

        :expectedresults:

            1. Export fails with error '"message": "NOTE: Unable to fully
                export this version because it contains repositories without the
                'immediate' download policy. Update the download policy and sync
                affected repositories. Once synced, republish the content view and
                export the generated version."'
        """
        exporting_prod = gen_string('alpha')
        product = make_product({'organization-id': module_org.id, 'name': exporting_prod})
        exporting_repo = gen_string('alpha')
        repo = make_repository(
            {'name': exporting_repo, 'download-policy': 'on_demand', 'product-id': product['id']}
        )
        Repository.synchronize({'id': repo['id']})
        exporting_cv = gen_string('alpha')
        cv_dict, exporting_cvv_id = _create_cv(exporting_cv, repo, module_org)
        cv_name = cv_dict['name']
        cv_version = cv_dict['versions'][0]['version']
        with pytest.raises(CLIReturnCodeError) as error:
            ContentExport.completeVersion(
                {'id': exporting_cvv_id, 'organization-id': module_org.id}
            )
            ContentExport.completeVersion({'id': repo.id, 'organization-id': module_org.id})
        assert (
            'Could not export the content view:\n  '
            f'''Error: Ensure the content view version '{cv_name} {cv_version}' '''
            'has at least one repository.'
        ) in error.value.message

    @pytest.mark.tier2
    def test_positive_create_custom_major_minor_cv_version(self):
        """CV can published with custom major and minor versions

        :id: 6697cd22-253a-4bdc-a108-7e0af22caaf4

        :steps:

            1. Create product and repository with custom contents
            2. Sync the repository
            3. Create CV with above repository
            4. Publish the CV with custom major and minor versions

        :expectedresults:

            1. CV version with custom major and minor versions is created

        :CaseLevel: System
        """
        org = make_org()
        major = randint(1, 1000)
        minor = randint(1, 1000)
        content_view = make_content_view(
            {'name': gen_string('alpha'), 'organization-id': org['id']}
        )
        ContentView.publish({'id': content_view['id'], 'major': major, 'minor': minor})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]['version']
        assert cvv.split('.')[0] == str(major)
        assert cvv.split('.')[1] == str(minor)

    @pytest.mark.tier3
    def test_postive_export_cv_with_mixed_content_repos(
        self, class_export_entities, export_import_cleanup_module, target_sat, module_org
    ):
        """Exporting CV version having yum and non-yum(docker) is successful

        :id: ffcdbbc6-f787-4978-80a7-4b44c389bf49

        :steps:

            1. Create product with yum and non-yum(docker) repos
            2. Sync the repositories
            3. Create CV with above product and publish
            4. Export CV version contents to a directory

        :expectedresults:
            1. Export will succeed, however the export wont contain non-yum repo.
            No warning is printed (see BZ 1775383)

        :BZ: 1726457

        :customerscenario: true

        """
        product = make_product(
            {
                'organization-id': module_org.id,
                'name': gen_string('alpha'),
            }
        )
        nonyum_repo = make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': 'quay/busybox',
                'organization-id': module_org.id,
                'product-id': product['id'],
                'url': CONTAINER_REGISTRY_HUB,
            },
        )
        Repository.synchronize({'id': nonyum_repo['id']})
        yum_repo = make_repository(
            {
                'name': gen_string('alpha'),
                'download-policy': 'immediate',
                'mirror-on-sync': 'no',
                'product-id': product['id'],
            }
        )
        Repository.synchronize({'id': yum_repo['id']})
        content_view = make_content_view({'organization-id': module_org.id})
        # Add docker and yum repo
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': nonyum_repo['id'],
            }
        )
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': yum_repo['id'],
            }
        )
        ContentView.publish({'id': content_view['id']})
        exporting_cv_id = ContentView.info({'id': content_view['id']})
        assert len(exporting_cv_id['versions']) == 1
        exporting_cvv_id = exporting_cv_id['versions'][0]
        # check packages
        exported_packages = Package.list({'content-view-version-id': exporting_cvv_id['id']})
        assert len(exported_packages)
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export cv
        ContentExport.completeVersion(
            {'id': exporting_cvv_id['id'], 'organization-id': module_org.id}
        )
        # Verify export directory is not empty
        assert validate_filepath(target_sat, module_org) != ''

    @pytest.mark.tier3
    def test_postive_import_export_cv_with_file_content(
        self, target_sat, config_export_import_settings, export_import_cleanup_module, module_org
    ):
        """Exporting and Importing cv with file content

        :id: d00739f0-dedf-4303-8929-889dc23260a4

        :steps:

            1. Create custom product and custom repo with file type
            2. Sync repo
            3. Create cv and add file repo created in step 1 and publish
            4. Export cv and import cv into another satellite
            5. Check imported cv has files in it

        :expectedresults:  Imported cv should have the files present in the cv of
            the imported system
        """
        # setup custom repo
        cv_name = import_cv_name = gen_string('alpha')
        product = make_product({'organization-id': module_org.id})
        file_repo = make_repository(
            {
                'organization-id': module_org.id,
                'product-id': product['id'],
                'content-type': 'file',
                'url': settings.repos.file_type_repo.url,
            }
        )
        Repository.synchronize({'id': file_repo['id']})
        # create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': module_org.id,
                'repository-id': file_repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        exporting_cv_id = ContentView.info({'id': cv['id']})
        assert len(exporting_cv_id['versions']) == 1
        exporting_cvv_id = exporting_cv_id['versions'][0]['id']
        # check files
        exported_files = File.list({'content-view-version-id': exporting_cvv_id})
        assert len(exported_files)
        # Verify export directory is empty
        assert validate_filepath(target_sat, module_org) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': exporting_cvv_id, 'organization-id': module_org.id}
        )
        import_path = move_pulp_archive(target_sat, module_org, export['message'])

        # importing portion
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import files and verify content
        ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
        importing_cvv = ContentView.info(
            {'name': import_cv_name, 'organization-id': importing_org['id']}
        )['versions']
        assert len(importing_cvv) >= 1
        imported_files = File.list({'content-view-version-id': importing_cvv[0]['id']})
        assert len(imported_files)
        assert len(exported_files) == len(imported_files)

    @pytest.mark.tier3
    def test_postive_import_export_ansible_collection_repo(
        self,
        target_sat,
        config_export_import_settings,
        export_import_cleanup_function,
        function_org,
    ):
        """Exporting and Importing library with ansible collection

        :id: 71dd1e1a-caad-48be-a180-206c8aa78639

        :steps:

            1. Create custom product and custom repo with ansible collection
            2. Sync repo
            3. Export library and import into another satellite
            4. Check imported library has ansible collection in it

        :expectedresults:  Imported library should have the ansible collection present in the
            imported product
        """
        # setup ansible_collection product and repo
        export_product = make_product({'organization-id': function_org.id})
        ansible_repo = make_repository(
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
        Repository.synchronize({'id': ansible_repo['id']})
        # Export library
        export = ContentExport.completeLibrary({'organization-id': function_org.id})
        import_path = move_pulp_archive(target_sat, function_org, export['message'])

        # importing portion
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})

        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''
        # Import files and verify content
        ContentImport.library({'organization-id': importing_org['id'], 'path': import_path})
        assert Product.list({'organization-id': importing_org['id']})
        import_product = Product.info(
            {
                'organization-id': importing_org['id'],
                'id': Product.list({'organization-id': importing_org['id']})[0]['id'],
            }
        )
        assert import_product['name'] == export_product['name']
        assert len(import_product['content']) == 1
        assert import_product['content'][0]['content-type'] == "ansible_collection"

    @pytest.mark.skip_if_not_set('fake_manifest')
    @pytest.mark.tier3
    def test_negative_import_redhat_cv_without_manifest(
        self,
        export_import_cleanup_function,
        config_export_import_settings,
        function_org,
        target_sat,
    ):
        """Redhat content can't be imported into satellite/organization without manifest

        :id: b0f5f95b-3f9f-4827-84f1-b66517dc34f1

        :steps:

            1. Enable product and repository with redhat contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents to other org without manifest.

        :expectedresults:

            1. Import fails with message "Could not import the archive.:
               No manifest found. Import a manifest with the appropriate subscriptions before
               importing content."

        """
        # Setup rhel repo
        cv_name = gen_string('alpha')
        with manifests.clone() as manifest:
            target_sat.put(manifest, manifest.filename)
        Subscription.upload({'file': manifest.filename, 'organization-id': function_org.id})
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhva6'],
                'organization-id': function_org.id,
                'product': PRDS['rhel'],
                'releasever': '6Server',
            }
        )
        repo = Repository.info(
            {
                'name': REPOS['rhva6']['name'],
                'organization-id': function_org.id,
                'product': PRDS['rhel'],
            }
        )
        # Update the download policy to 'immediate' and sync
        Repository.update({'download-policy': 'immediate', 'id': repo['id']})
        Repository.synchronize({'id': repo['id']}, timeout=7200000)
        # Create cv and publish
        cv = make_content_view({'name': cv_name, 'organization-id': function_org.id})
        ContentView.add_repository(
            {
                'id': cv['id'],
                'organization-id': function_org.id,
                'repository-id': repo['id'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        cvv = cv['versions'][0]
        # Verify export directory is empty
        assert validate_filepath(target_sat, function_org) == ''
        # Export cv
        export = ContentExport.completeVersion(
            {'id': cvv['id'], 'organization-id': function_org.id}
        )
        import_path = move_pulp_archive(target_sat, function_org, export['message'])
        # check that files are present in import_path
        result = target_sat.execute(f'ls {import_path}')
        assert result.stdout != ''

        # importing portion
        importing_org = make_org()
        # set disconnected mode
        Settings.set({'name': 'subscription_connection_enabled', 'value': "No"})
        with pytest.raises(CLIReturnCodeError) as error:
            ContentImport.version({'organization-id': importing_org['id'], 'path': import_path})
        assert (
            'Could not import the archive.:\n  No manifest found. Import a manifest with the '
            'appropriate subscriptions before importing content.'
        ) in error.value.message


class TestInterSatelliteSync:
    """Implements InterSatellite Sync tests in CLI"""

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_negative_export_cv(self):
        """Export whole CV version contents is aborted due to insufficient
        memory.

        :id: 4fa58c0c-95d2-45f5-a7fc-c5f3312a989c

        :steps: Attempt to Export whole CV version contents to a directory
            which has less memory available than contents size.

        :expectedresults: The export CV version contents has been aborted due
            to insufficient memory.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_export_import_cv_iso(self):
        """Export CV version contents in directory as iso and Import it.

        :id: 5c39afd4-09d6-43c5-8d50-edc98105b7db

        :steps:

            1. Export whole CV version contents as ISO
            2. Import these copied ISO to some other org/satellite.

        :expectedresults:

            1. CV version has been exported to directory as ISO in specified in
               settings.
            2. The exported ISO has been imported in org/satellite.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_negative_export_cv_iso(self):
        """Export whole CV version to iso is aborted due to insufficient
        memory.

        :id: ef84ffbd-c7cf-4d9a-9944-3c3b06a18872

        :steps: Attempt to Export whole CV version as iso to a directory which
            has less memory available than contents size.

        :expectedresults: The export CV version to iso has been aborted due to
            insufficient memory.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_negative_export_cv_iso_max_size(self):
        """Export whole CV version to iso is aborted due to inadequate maximum
        iso size.

        :id: 93fe1cef-254b-484d-a628-bec56b356234

        :steps: Attempt to Export whole CV version as iso with mb size less
            than required.

        :expectedresults: The export CV version to iso has been aborted due to
            maximum size is not enough to contain the CV version contents.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_export_cv_iso_max_size(self):
        """CV version exported to iso in maximum iso size.

        :id: 7ec91557-bafc-490d-b760-573a07389be5

        :steps: Attempt to Export whole CV version as iso with mb size more
            than required.

        :expectedresults: CV version has been exported to iso successfully.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_export_import_cv_incremental(self):
        """Export and Import CV version contents incrementally.

        :id: 3c4dfafb-fabf-406e-bca8-7af1ab551135

        :steps:
            1. In upstream, Export CV version contents to a directory specified
               in settings.
            2. In downstream, Import these copied contents from some other
               org/satellite.
            3. In upstream, Add new packages to the CV.
            4. Export the CV incrementally from the last date time.
            5. In downstream, Import the CV incrementally.

        :expectedresults:
            1. On incremental export, only the new packages are exported.
            2. New directory of incremental export with new packages is
               created.
            3. On incremental import, only the new packages are imported.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_negative_export_import_cv_incremental(self):
        """No new incremental packages exported or imported.

        :id: 90692d59-788c-4e18-add1-33db04204a4b

        :steps:
            1. In upstream, Export CV version contents to a directory specified
               in settings.
            2. In downstream, Import these copied contents from some other
               org/satellite.
            3. In upstream, Don't add any new packages to the CV.
            4. Export the CV incrementally from the last date time.
            5. In downstream, Import the CV incrementally.

        :expectedresults:
            1. An Empty packages directory created on incremental export.
            2. On incremental import, no new packages are imported.

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
    @pytest.mark.upgrade
    def test_positive_export_import_kickstart_tree(self):
        """kickstart tree is exported to specified location.

        :id: bb9e77ed-fbbb-4e43-b118-2ddcb7c6341f

        :steps:

            1. Export the full kickstart tree.
            2. Copy exported kickstart tree contents to
               /var/www/html/pub/export.
            3. Import above exported kickstart tree from other org/satellite.

        :expectedresults:

            1. Whole kickstart tree contents has been exported to directory
               specified in settings.
            2. All The exported contents has been imported in org/satellite.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_negative_import_kickstart_tree(self):
        """Export whole kickstart tree in directory and Import nothing.

        :id: 55ddf6a6-b99a-4986-bdd3-7a5384f06915

        :steps:

            1. Export whole kickstart tree contents to a directory specified in
               settings.
            2. Dont copy exported contents to /var/www/html/pub/export
               directory.
            3. Attempt to import these not copied contents from some other
               org/satellite.

        :expectedresults:

            1. Whole kickstart tree has been exported to directory specified in
               settings.
            2. The exported contents are not imported due to non availability.
            3. Error is thrown for non availability of kickstart tree to
               import.

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_negative_export_kickstart_tree(self):
        """Export whole kickstart tree contents is aborted due to insufficient
        memory.

        :id: 5f681f43-bac8-4196-9b3c-8b66b9c149f9

        :steps: Attempt to Export whole kickstart tree contents to a directory
            which has less memory available than contents size.

        :expectedresults: The export kickstart tree has been aborted due to
            insufficient memory.

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
    def test_positive_export_import_redhat_mix_cv(self):
        """Export CV version having Red Hat and custom repo in directory
        and Import them.

        :id: a38cf67d-563c-46f0-a263-4825b26faf2b

        :steps:

            1. Export whole CV version having mixed repos to a path accessible
               over HTTP.
            2. Import the Red Hat repository by defining the CDN URL from the
               exported HTTP URL.
            3. Import custom repo by creating new repo and setting yum repo url
               to exported HTTP url.

        :expectedresults: Both custom and Red Hat repos are imported
            successfully.

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
