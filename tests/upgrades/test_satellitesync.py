"""Test for Inter Satellite Sync related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: InterSatelliteSync

:Team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.constants import PULP_EXPORT_DIR


class TestSatelliteSync:
    """
    Test Content-view created before upgrade can be exported and imported after upgrade
    """

    @pytest.mark.pre_upgrade
    def test_pre_version_cv_export_import(self, module_org, target_sat, save_test_data):
        """Before Upgrade, Create the content view and publish, and promote it.

        :id: preupgrade-f19e4928-94db-4df6-8ce8-b5e4afe34258

        :steps:

        1. Create a ContentView
        2. Publish and promote the Content View
        3. Check the package count of promoted content view.

        :expectedresults: Before the upgrade, Content view published and promoted, and  package
        count should be greater than 0.
        """
        product = target_sat.api.Product(organization=module_org).create()
        repo = target_sat.api.Repository(
            product=product,
            download_policy='immediate',
        ).create()
        repo.sync()
        cv = target_sat.api.ContentView(organization=module_org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        assert cv.version[0].read().package_count > 0
        save_test_data(
            {
                "product": product.name,
                "org": module_org.name,
                "content_view": cv.name,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_version_cv_export_import)
    def test_post_version_cv_export_import(self, request, target_sat, pre_upgrade_data):
        """After upgrade, content view version import and export works on the existing content
         view(that we created before the upgrade).

        :id: postupgrade-f19e4928-94db-4df6-8ce8-b5e4afe34258

        :parametrized: yes

        :steps:
            1: Export the existing content-view version.
            2: Import the existing content-view version.
            3: Delete the imported and exported content-vew, product, repo and organization.

        :expectedresults: After upgrade,
            1: Content view created before upgrade should be imported and exported successfully.
            2: Imported and Exported content view should be deleted successfully
        """
        org = target_sat.api.Organization().search(
            query={'search': f'name="{pre_upgrade_data.org}"'}
        )[0]
        request.addfinalizer(org.delete)
        product = target_sat.api.Product(organization=org).search(
            query={'search': f'name="{pre_upgrade_data.product}"'}
        )[0]
        request.addfinalizer(product.delete)
        exporting_cv = target_sat.api.ContentView(organization=org).search(
            query={'search': f'name="{pre_upgrade_data.content_view}"'}
        )[0]
        request.addfinalizer(exporting_cv.delete)

        exporting_cvv_id = max(cvv.id for cvv in exporting_cv.version)

        # Export content view
        export = target_sat.cli.ContentExport.completeVersion(
            {'id': exporting_cvv_id, 'organization-id': org.id}
        )
        # Verify export directory is not empty
        assert target_sat.validate_pulp_filepath(org, PULP_EXPORT_DIR) != ''
        exported_packages = target_sat.cli.Package.list(
            {'content-view-version-id': exporting_cvv_id}
        )
        assert len(exported_packages) > 0
        importing_org = target_sat.api.Organization().create()

        # Import files and verify content
        import_path = target_sat.move_pulp_archive(org, export['message'])
        target_sat.cli.ContentImport.version(
            {'organization-id': importing_org.id, 'path': import_path}
        )
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
