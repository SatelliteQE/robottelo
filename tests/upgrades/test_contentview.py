"""Test for Content View related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ContentViews

:Team: Phoenix

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import DataFile
from robottelo.constants import RPM_TO_UPLOAD


class TestContentView:
    """The test class contains the pre-upgrade and post-upgrade scenario to test the behavior of
    content view before and after the upgrade.
    """

    @pytest.mark.pre_upgrade
    def test_cv_preupgrade_scenario(self, request, target_sat):
        """Pre-upgrade scenario that creates content-view with various repositories.

        :id: preupgrade-a4ebbfa1-106a-4962-9c7c-082833879ae8

        :steps:
          1. Create custom repositories of yum and file type.
          2. Create content-view.
          3. Add yum and file repositories in the content view.
          4. Publish the content-view.

        :expectedresults: Content-view created with various repositories.
        """
        test_name = request.node.name
        org = entities.Organization(name=f'{request.node.name}_org').create()
        product = entities.Product(organization=org, name=f'{request.node.name}_prod').create()
        yum_repository = entities.Repository(
            product=product, name=f'{test_name}_yum_repo', url=settings.repos.yum_1.url
        ).create()
        entities.Repository.sync(yum_repository)
        file_repository = entities.Repository(
            product=product, name=f'{test_name}_file_repo', content_type="file"
        ).create()

        remote_file_path = f"/tmp/{RPM_TO_UPLOAD}"

        target_sat.put(DataFile.RPM_TO_UPLOAD, remote_file_path)
        file_repository.upload_content(files={'content': DataFile.RPM_TO_UPLOAD.read_bytes()})
        assert RPM_TO_UPLOAD in file_repository.files()["results"][0]['name']
        cv = entities.ContentView(name=f"{test_name}_cv", organization=org).create()
        cv.repository = [yum_repository, file_repository]
        cv.update(['repository'])
        cv.publish()
        assert len(cv.read_json()['versions']) == 1

    @pytest.mark.post_upgrade(depend_on=test_cv_preupgrade_scenario)
    def test_cv_postupgrade_scenario(self, request, dependent_scenario_name):
        """After upgrade, the existing content-view(created before upgrade) should be updated.

        :id: postupgrade-a4ebbfa1-106a-4962-9c7c-082833879ae8

        :steps:
          1. Check yum and file repository which was added in CV before upgrade.
          2. Check the content view which was was created before upgrade.
          3. Remove yum repository from existing CV.
          4. Create new yum repository in existing CV.
          5. Publish content-view

        :expectedresults: After upgrade,
          1. All the repositories should be intact.
          2. Content view created before upgrade should be intact.
          3. The new repository should be added/updated to the CV.

        """
        pre_test_name = dependent_scenario_name
        org = entities.Organization().search(query={'search': f'name="{pre_test_name}_org"'})[0]
        request.addfinalizer(org.delete)
        product = entities.Product(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_prod"'}
        )[0]
        request.addfinalizer(product.delete)
        cv = entities.ContentView(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_cv"'}
        )[0]
        yum_repo = entities.Repository(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_yum_repo"'}
        )[0]
        request.addfinalizer(yum_repo.delete)
        file_repo = entities.Repository(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_file_repo"'}
        )[0]
        request.addfinalizer(file_repo.delete)
        request.addfinalizer(cv.delete)
        cv.repository = []
        cv.update(['repository'])
        assert len(cv.read_json()['repositories']) == 0

        yum_repository2 = entities.Repository(
            product=product, name=f'{pre_test_name}_yum_repos2', url=settings.repos.yum_2.url
        ).create()
        yum_repository2.sync()
        cv.repository = [yum_repository2]
        cv.update(['repository'])
        assert cv.read_json()['repositories'][0]['name'] == yum_repository2.name

        cv.publish()
        assert len(cv.read_json()['versions']) == 2
        content_view_json = cv.read_json()['environments'][0]
        cv.delete_from_environment(content_view_json['id'])
        assert len(cv.read_json()['environments']) == 0
