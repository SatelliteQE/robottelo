"""Test for Inter Satellite Sync related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: InterSatelliteSync

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.cli.contentview import ContentView
from robottelo.cli.package import Package


class TestSatelliteSync:
    """
    Test Content-view created before upgrade can be exported and imported after upgrade

    :id: f19e4928-94db-4df6-8ce8-b5e4afe34258

    :steps:

        1. Create a ContentView
        2. Publish and promote the Content View
        3. Check the package count of promoted content view.
        4. Upgrade the satellite
        5. After upgrade, Export the existing content-view version.
        6. Import the existing content-view version.
        7. Delete the imported and exported content-vew, product, repo and organization.

    :expectedresults:

        1. Before the upgrade, Content view published and promoted, and  package
        count should be greater than 0.
        2. After upgrade, Content view created before upgrade should be imported
        and exported successfully.
        3. Imported and Exported content view should be deleted successfully.
    """

    @pytest.mark.pre_upgrade
    def test_pre_version_cv_export_import(self, request):
        """Before Upgrade, Create the content view and publish, and promote it."""
        test_name = request.node.name
        org = entities.Organization(name=f"{test_name}_org").create()
        product = entities.Product(organization=org, name=f"{test_name}_prod").create()
        repo = entities.Repository(
            product=product,
            name=f"{test_name}_repo",
            mirror_on_sync=False,
            download_policy='immediate',
        ).create()
        repo.sync()
        cv = entities.ContentView(name=f"{test_name}_cv", organization=org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        assert cv.version[0].read().package_count > 0

    @pytest.mark.post_upgrade(depend_on=test_pre_version_cv_export_import)
    @pytest.mark.parametrize(
        'set_importing_org',
        [
            (
                "test_pre_version_cv_export_import_prod",
                "test_pre_version_cv_export_import_repo",
                "test_pre_version_cv_export_import_cv",
                "no",
            )
        ],
        indirect=True,
    )
    def test_post_version_cv_export_import(
        self, request, set_importing_org, dependent_scenario_name, default_sat
    ):
        """After upgrade, content view version import and export works on the existing content
        view(that we created before the upgrade)."""
        pre_test_name = dependent_scenario_name
        export_base = '/var/lib/pulp/katello-export/'
        org = entities.Organization().search(query={'search': f'name="{pre_test_name}_org"'})[0]
        request.addfinalizer(org.delete)
        product = entities.Product(organization=org).search(
            query={'search': f'name="{pre_test_name}_prod"'}
        )[0]
        request.addfinalizer(product.delete)
        exporting_cv = entities.ContentView(organization=org).search(
            query={'search': f'name="{pre_test_name}_cv"'}
        )[0]
        request.addfinalizer(exporting_cv.delete)

        exporting_cvv_id = max(cvv.id for cvv in exporting_cv.version)
        exporting_cvv_version = entities.ContentViewVersion(id=exporting_cvv_id).read().version

        ContentView.version_export({'export-dir': f'{export_base}', 'id': exporting_cvv_id})
        exported_tar = f'{export_base}/export-{exporting_cv.name}-{exporting_cvv_version}.tar'

        result = default_sat.execute(f'[ -f {exported_tar} ]')
        assert result.status == 0

        exported_packages = Package.list({'content-view-version-id': exporting_cvv_id})
        assert len(exported_packages) > 0
        importing_cv, importing_org = set_importing_org
        ContentView.version_import(
            {'export-tar': f'{exported_tar}', 'organization-id': importing_org.id}
        )
        importing_cvv = importing_cv.read().version
        assert len(importing_cvv) == 1
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0].id})
        assert len(imported_packages) > 0
        assert len(exported_packages) == len(imported_packages)
        default_sat.execute(f'rm -rf {export_base}/*')
        exporting_cv_json = exporting_cv.read_json()
        importing_cv_json = importing_cv.read_json()
        exporting_cv_env_id = exporting_cv_json['environments'][0]['id']
        importing_cv_env_id = importing_cv_json['environments'][0]['id']
        assert exporting_cv.delete_from_environment(exporting_cv_env_id)
        assert importing_cv.delete_from_environment(importing_cv_env_id)
