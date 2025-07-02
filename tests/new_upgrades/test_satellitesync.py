"""Test for Inter Satellite Sync related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: InterSatelliteSync

:Team: Phoenix-content

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.config import settings
from robottelo.constants import PULP_EXPORT_DIR
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def version_cv_export_import_setup(content_upgrade_shared_satellite, upgrade_action):
    """Before upgrade, create the content view and publish, and promote it.

    :steps:
        1. Create a ContentView
        2. Publish and promote the Content View
        3. Check the package count of promoted content view.

    :expectedresults: Before the upgrade, Content view published and promoted, and package
        count should be greater than 0.
    """
    target_sat = content_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'sat_sync_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        product = target_sat.api.Product(name=f'{test_name}_prod', organization=org.id).create()
        repo = target_sat.api.Repository(
            name=f'{test_name}_repo',
            content_type='yum',
            product=product,
            download_policy='immediate',
            url=settings.repos.yum_1.url,
        ).create()
        repo.sync()
        cv = target_sat.publish_content_view(org, repo, f'{test_name}_content_view')
        assert cv.version[0].read().package_count > 0
        test_data = Box(
            {
                "test_name": test_name,
                "satellite": target_sat,
                "org": org,
                "content_view": cv,
            }
        )
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.content_upgrades
def test_post_version_cv_export_import(version_cv_export_import_setup):
    """After upgrade, content view version import and export works on the existing content
     view (that we created before the upgrade).

    :id: f19e4928-94db-4df6-8ce8-b5e4afe34258

    :parametrized: yes

    :steps:
        1: Export the existing content-view version.
        2: Import the exported content-view version.
        3: Delete the imported and exported content views from the LCE.

    :expectedresults: After upgrade,
        1: Content view created before upgrade should be imported and exported successfully.
        2: Imported and Exported content view should be deleted successfully
    """
    target_sat = version_cv_export_import_setup.satellite
    test_name = version_cv_export_import_setup.test_name
    org = version_cv_export_import_setup.org
    exporting_cv = version_cv_export_import_setup.content_view
    exporting_cvv_id = max(cvv.id for cvv in exporting_cv.version)
    # Export content view
    export = target_sat.cli.ContentExport.completeVersion(
        {'id': exporting_cvv_id, 'organization-id': org.id}
    )
    # Verify export directory is not empty
    assert target_sat.validate_pulp_filepath(org, PULP_EXPORT_DIR) != ''
    exported_packages = target_sat.cli.Package.list({'content-view-version-id': exporting_cvv_id})
    assert len(exported_packages) > 0
    importing_org = target_sat.api.Organization(name=f'{test_name}_importing_org').create()
    # Import files and verify content
    import_path = target_sat.move_pulp_archive(org, export['message'])
    target_sat.cli.ContentImport.version({'organization-id': importing_org.id, 'path': import_path})
    importing_cv = target_sat.cli.ContentView.info(
        {'name': exporting_cv.name, 'organization-id': importing_org.id}
    )
    importing_cvv = importing_cv['versions']
    assert len(importing_cvv) >= 1
    imported_packages = target_sat.cli.Package.list(
        {'content-view-version-id': importing_cvv[0]['id']}
    )
    assert len(imported_packages)
    assert len(exported_packages) == len(imported_packages)
    importing_cv = target_sat.api.ContentView(organization=importing_org).search(
        query={'search': f'name="{exporting_cv.name}"'}
    )[0]
    exporting_cv_json = exporting_cv.read_json()
    importing_cv_json = importing_cv.read_json()
    exporting_cv_env_id = exporting_cv_json['environments'][0]['id']
    importing_cv_env_id = importing_cv_json['environments'][0]['id']
    assert exporting_cv.delete_from_environment(exporting_cv_env_id)
    assert importing_cv.delete_from_environment(importing_cv_env_id)
