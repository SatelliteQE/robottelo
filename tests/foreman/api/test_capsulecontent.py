"""Content Management related tests, which exercise katello with pulp
interactions and use capsule.

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Phoenix-content

:CaseImportance: High

"""

from datetime import UTC, datetime, timedelta
import re
from time import sleep

from nailgun import client
from nailgun.config import ServerConfig
from nailgun.entity_mixins import call_entity_method_with_timeout
import pytest
import requests
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import (
    ENVIRONMENT,
    FAKE_1_YUM_REPOS_COUNT,
    FAKE_3_YUM_REPO_RPMS,
    FAKE_3_YUM_REPOS_COUNT,
    FAKE_FILE_LARGE_COUNT,
    FAKE_FILE_LARGE_URL,
    FAKE_FILE_NEW_NAME,
    FLATPAK_ENDPOINTS,
    KICKSTART_CONTENT,
    PRDS,
    PULP_ARTIFACT_DIR,
    REPOS,
    REPOSET,
    RPM_TO_UPLOAD,
    DataFile,
)
from robottelo.constants.repos import ANSIBLE_GALAXY, CUSTOM_FILE_REPO
from robottelo.content_info import (
    get_repo_files_by_url,
    get_repomd,
    get_repomd_revision,
)
from robottelo.utils.datafactory import gen_string
from robottelo.utils.issue_handlers import is_open


@pytest.fixture(scope="module")
def add_proxy_cli_config(module_target_sat, module_capsule_configured):
    """Adds an entry in the pulp cli config for executing pulp commands on the capsule, then removes it."""
    PROXY_CONFIG = '\n[cli-proxy]\ncert = "/etc/foreman/client_cert.pem"\nkey = "/etc/foreman/client_key.pem"\nbase_url = "https://{module_capsule_configured.fqdn}"'
    module_target_sat.execute(f"""echo -e {PROXY_CONFIG} >> .config/pulp/cli.toml""")
    yield
    module_target_sat.execute("sed -i '/cli-proxy/, +3 d' .config/pulp/cli.toml")


@pytest.fixture
def default_non_admin_user(target_sat, default_org, default_location):
    """Non-admin user with no roles assigned in the Default org/loc."""
    password = gen_string('alphanumeric')
    user = target_sat.api.User(
        login=gen_string('alpha'),
        password=password,
        organization=[default_org],
        location=[default_location],
    ).create()
    user.password = password
    yield user
    user.delete()


@pytest.fixture(scope='module')
def module_autosync_setting(request, module_target_sat, module_capsule_configured):
    """Set capsule autosync setting"""
    setting_entity = module_target_sat.api.Setting().search(
        query={'search': 'name=foreman_proxy_content_auto_sync'}
    )[0]
    original_autosync = setting_entity.value
    setting_entity.value = request.param
    setting_entity.update({'value'})
    yield
    setting_entity.value = original_autosync
    setting_entity.update({'value'})


@pytest.mark.run_in_one_thread
class TestCapsuleContentManagement:
    """Content Management related tests, which exercise katello with pulp
    interactions and use capsule.
    """

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_uploaded_content_library_sync(
        self,
        module_capsule_configured,
        function_org,
        function_product,
        function_lce_library,
        target_sat,
    ):
        """Ensure custom repo with no upstream url and manually uploaded
        content after publishing to Library is synchronized to capsule
        automatically

        :id: f5406312-dd31-4551-9f03-84eb9c3415f5

        :customerscenario: true

        :BZ: 1340686

        :expectedresults: custom content is present on external capsule
        """
        repo = target_sat.api.Repository(product=function_product, url=None).create()
        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce_library.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results']) >= 1
        assert function_lce_library.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()

        # Upload custom content into the repo
        with open(DataFile.RPM_TO_UPLOAD, 'rb') as handle:
            repo.upload_content(files={'content': handle})

        assert repo.read().content_counts['rpm'] == 1

        timestamp = datetime.now(UTC).replace(microsecond=0)
        # Publish new version of the content view
        cv.publish()
        # query sync status as publish invokes sync, task succeeds
        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cv = cv.read()
        assert len(cv.version) == 1

        # Verify the RPM published on Capsule
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            lce=function_lce_library.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert len(caps_files) == 1
        assert caps_files[0] == RPM_TO_UPLOAD

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_checksum_sync(
        self, module_capsule_configured, function_org, function_product, function_lce, target_sat
    ):
        """Synchronize repository to capsule, update repository's checksum
        type, trigger capsule sync and make sure checksum type was updated on
        capsule

        :id: eb07bdf3-6cd8-4a2f-919b-8dfc84e16115

        :customerscenario: true

        :BZ: 1288656, 1664288, 1732066, 2001052

        :expectedresults: checksum type is updated in repodata of corresponding
            repository on capsule

        :CaseImportance: Critical
        """
        original_checksum = 'sha256'
        new_checksum = 'sha512'
        # Create repository with sha256 checksum type
        repo = target_sat.api.Repository(
            product=function_product,
            checksum_type=original_checksum,
            mirroring_policy='additive',
            download_policy='immediate',
        ).create()
        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results']) >= 1
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Sync, publish and promote a repo
        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        repo.sync()
        repo = repo.read()
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})
        module_capsule_configured.wait_for_sync(start_time=timestamp)

        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Verify repodata's checksum type is sha256, not sha512 on capsule
        repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            prod=function_product.label,
            repo=repo.label,
            lce=function_lce.label,
            cv=cv.label,
        )
        repomd = get_repomd(repo_url)
        checksum_types = re.findall(r'(?<=checksum type=").*?(?=")', repomd)
        assert new_checksum not in checksum_types
        assert original_checksum in checksum_types

        # Update repo's checksum type to sha512
        repo.checksum_type = new_checksum
        repo = repo.update(['checksum_type'])

        # Sync, publish, and promote repo
        repo.sync()
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 2

        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Verify repodata's checksum type has updated to sha512 on capsule
        repomd = get_repomd(repo_url)
        checksum_types = re.findall(r'(?<=checksum type=").*?(?=")', repomd)
        assert new_checksum in checksum_types
        assert original_checksum not in checksum_types

    @pytest.mark.e2e
    @pytest.mark.pit_client
    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_updated_repo(
        self,
        target_sat,
        module_capsule_configured,
        function_org,
        function_product,
        function_lce,
    ):
        """Sync a custom repo with no upstream url but uploaded content to the Capsule via
        promoted CV, update content of the repo, publish and promote the CV again, resync
        the Capsule.

        :id: ddbecc80-17d9-47f6-979e-111ebd74cb90

        :setup:
            1. Have a custom product, repo without upstream url and LCE created.

        :steps:
            1. Associate the LCE with the Capsule.
            2. Upload some content to the repository.
            3. Create, publish and promote CV with the repository to the Capsule's LCE.
            4. Upload more content to the repository.
            5. Publish new version and promote it to the Capsule's LCE.
            6. Check the Capsule sync result.
            7. Check the content.

        :expectedresults:
            1. Capsule is synced successfully.
            2. Content is present at the Capsule side.

        :customerscenario: true

        :BZ: 2025494
        """
        repo = target_sat.api.Repository(url=None, product=function_product).create()

        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Upload custom content into the repo
        with open(DataFile.RPM_TO_UPLOAD, 'rb') as handle:
            repo.upload_content(files={'content': handle})

        assert repo.read().content_counts['rpm'] == 1

        # Create, publish and promote CV with the repository to the Capsule's LCE
        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Upload more content to the repository
        with open(DataFile.SRPM_TO_UPLOAD, 'rb') as handle:
            repo.upload_content(files={'content': handle})

        assert repo.read().content_counts['rpm'] == 2

        # Publish new version and promote it to the Capsule's LCE.
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 2

        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Check the content is synced on the Capsule side properly
        sat_repo_url = target_sat.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        sat_files = get_repo_files_by_url(sat_repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert sat_files == caps_files
        assert len(caps_files) == 2

    @pytest.mark.e2e
    @pytest.mark.pit_client
    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_capsule_sync(
        self,
        target_sat,
        module_capsule_configured,
        function_org,
        function_product,
        function_lce,
    ):
        """Create repository, add it to lifecycle environment, assign lifecycle
        environment with a capsule, sync repository, sync it once again, update
        repository (add 1 new package), sync repository once again.

        :id: 35513099-c918-4a8e-90d0-fd4c87ad2f82

        :customerscenario: true

        :BZ: 1394354, 1439691

        :expectedresults:

            1. Repository sync triggers capsule sync
            2. After syncing capsule contains same repo content as satellite
            3. Syncing repository which has no changes for a second time does
               not trigger any new publish task
            4. Repository revision on capsule remains exactly the same after
               second repo sync with no changes
            5. Syncing repository which was updated will update the content on
               capsule
        """
        repo_url = settings.repos.yum_1.url
        repo = target_sat.api.Repository(product=function_product, url=repo_url).create()
        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # prior to trigger (promoting), assert no active sync tasks
        active_tasks = module_capsule_configured.nailgun_capsule.content_get_sync(
            synchronous=True, timeout=600
        )['active_sync_tasks']
        assert len(active_tasks) == 0
        # Promote content view to lifecycle environment,
        # invoking capsule sync task(s)
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Content of the published content view in
        # lifecycle environment should equal content of the
        # repository
        assert repo.content_counts['rpm'] == cvv.package_count

        # Assert that the content published on the capsule is exactly the
        # same as in repository on satellite
        sat_repo_url = target_sat.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        sat_files = get_repo_files_by_url(sat_repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert sat_files == caps_files

        lce_revision_capsule = get_repomd_revision(caps_repo_url)

        # Sync repository for a second time
        result = repo.sync()
        # Assert that the task summary contains a message that says the
        # sync was skipped because content had not changed
        assert result['result'] == 'success'
        assert 'Skipping Sync (no change from previous sync)' in result['humanized']['output']

        # Publish a new version of content view
        cv.publish()
        cv = cv.read()
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        # Promote new content view version to lifecycle environment,
        # capsule sync task(s) invoked and succeed
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2
        # Assert that the value of repomd revision of repository in
        # lifecycle environment on the capsule has not changed
        new_lce_revision_capsule = get_repomd_revision(caps_repo_url)
        assert lce_revision_capsule == new_lce_revision_capsule

        # Update a repository with 1 new rpm
        with open(DataFile.RPM_TO_UPLOAD, 'rb') as handle:
            repo.upload_content(files={'content': handle})

        # Publish and promote the repository
        repo = repo.read()
        cv.publish()
        cv = cv.read()
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()

        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Assert that packages count in the repository is updated
        assert repo.content_counts['rpm'] == (FAKE_1_YUM_REPOS_COUNT + 1)

        # Assert that the content of the published content view in
        # lifecycle environment is exactly the same as content of the
        # repository
        assert repo.content_counts['rpm'] == cvv.package_count

        # Assert that the content published on the capsule is exactly the
        # same as in the repository
        sat_files = get_repo_files_by_url(sat_repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert sat_files == caps_files

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_iso_library_sync(
        self, module_capsule_configured, module_sca_manifest_org, module_target_sat
    ):
        """Ensure RH repo with ISOs after publishing to Library is synchronized
        to capsule automatically

        :id: 221a2d41-0fef-46dd-a804-fdedd7187163

        :customerscenario: true

        :BZ: 1303102, 1480358, 1303103, 1734312

        :expectedresults: ISOs are present on external capsule
        """
        # Enable & sync RH repository with ISOs
        rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_sca_manifest_org.id,
            product=PRDS['rhsc'],
            repo=REPOS['rhsc7_iso']['name'],
            reposet=REPOSET['rhsc7_iso'],
            releasever=None,
        )
        rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
        call_entity_method_with_timeout(rh_repo.sync, timeout=2500)
        # Find "Library" lifecycle env for specific organization
        lce = module_target_sat.api.LifecycleEnvironment(
            organization=module_sca_manifest_org
        ).search(query={'search': f'name={ENVIRONMENT}'})[0]

        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results']) >= 1
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = module_target_sat.api.ContentView(
            organization=module_sca_manifest_org, repository=[rh_repo]
        ).create()
        # Publish new version of the content view
        timestamp = datetime.now(UTC)
        cv.publish()

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cv = cv.read()
        assert len(cv.version) == 1

        # Verify ISOs are present on satellite
        sat_isos = get_repo_files_by_url(rh_repo.full_path, extension='iso')
        assert len(sat_isos) == 4

        # Verify all the ISOs are present on capsule
        caps_path = (
            f'{module_capsule_configured.url}/pulp/content/{module_sca_manifest_org.label}'
            f'/{lce.label}/{cv.label}/content/dist/rhel/server/7/7Server/x86_64/sat-capsule/6.4/'
            'iso/'
        )
        caps_isos = get_repo_files_by_url(caps_path, extension='iso')
        assert len(caps_isos) == 4
        assert set(sat_isos) == set(caps_isos)

    @pytest.mark.build_sanity
    @pytest.mark.order(after="tests/foreman/installer/test_installer.py::test_capsule_installation")
    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_on_demand_sync(
        self,
        target_sat,
        module_capsule_configured,
        function_org,
        function_product,
        function_lce,
    ):
        """Create a repository with 'on_demand' policy, add it to a CV,
        promote to an 'on_demand' Capsule's LCE, download a published package,
        assert it matches the source.

        :id: ba470269-a7ad-4181-bc7c-8e17a177ca20

        :expectedresults:

            1. A custom yum repository is successfully synced and ContentView published
            2. The ContentView is successfully promoted to the Capsule's LCE and the content
               is automatically synced to the Capsule
            3. Package is successfully downloaded from the Capsule, its checksum matches
               the original package from the upstream repo
        """
        repo_url = settings.repos.yum_3.url
        packages_count = FAKE_3_YUM_REPOS_COUNT
        package = FAKE_3_YUM_REPO_RPMS[0]
        repo = target_sat.api.Repository(
            download_policy='on_demand',
            mirroring_policy='mirror_complete',
            product=function_product,
            url=repo_url,
        ).create()
        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Update capsule's download policy to on_demand
        module_capsule_configured.update_download_policy('on_demand')

        # Create a content view with the repository
        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Verify packages on Capsule match the source
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        source_files = get_repo_files_by_url(repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert source_files == caps_files
        assert len(caps_files) == packages_count

        # Download a package from the Capsule and get its md5 checksum
        published_package_md5 = target_sat.checksum_by_url(f'{caps_repo_url}/{package}')
        # Get md5 checksum of source package
        package_md5 = target_sat.checksum_by_url(f'{repo_url}/{package}')
        # Assert checksums are matching
        assert package_md5 == published_package_md5

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_update_with_immediate_sync(
        self,
        target_sat,
        module_capsule_configured,
        function_org,
        function_product,
        function_lce,
    ):
        """Create a repository with on_demand download policy, associate it
        with capsule, sync repo, update download policy to immediate, sync once
        more.

        :id: 511b531d-1fbe-4d64-ae31-0f9eb6625e7f

        :customerscenario: true

        :BZ: 1315752

        :expectedresults: content was successfully synchronized - capsule
            filesystem contains valid links to packages
        """
        repo_url = settings.repos.yum_1.url
        packages_count = FAKE_1_YUM_REPOS_COUNT
        repo = target_sat.api.Repository(
            download_policy='on_demand',
            mirroring_policy='mirror_complete',
            product=function_product,
            url=repo_url,
        ).create()
        # Update capsule's download policy to on_demand to match repository's policy
        module_capsule_configured.update_download_policy('on_demand')
        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Update download policy to 'immediate'
        repo.download_policy = 'immediate'
        repo = repo.update(['download_policy'])

        assert repo.download_policy == 'immediate'

        # Update capsule's download policy as well
        module_capsule_configured.update_download_policy('immediate')

        # Sync repository once again
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 2

        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Verify the count of RPMs published on Capsule
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert len(caps_files) == packages_count

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_capsule_pub_url_accessible(self, module_capsule_configured):
        """Ensure capsule pub url is accessible

        :id: 311eaa2a-146b-4d18-95db-4fbbe843d5b2

        :customerscenario: true

        :expectedresults: capsule pub url is accessible

        :BZ: 1463810, 2122780
        """
        https_pub_url = f'https://{module_capsule_configured.hostname}/pub'
        http_pub_url = f'http://{module_capsule_configured.hostname}/pub'
        for url in [http_pub_url, https_pub_url]:
            response = client.get(url, verify=False)
            assert response.ok
            assert b'katello-server-ca.crt' in response.content

    @pytest.mark.upgrade
    @pytest.mark.parametrize('endpoint', ['pulpcore', 'katello'])
    def test_flatpak_endpoint(self, target_sat, module_capsule_configured, endpoint):
        """Ensure the Capsules's local flatpak index endpoint is up after install or upgrade.

        :id: 5676fbbb-75be-4660-a09e-65cafdfb221a

        :parametrized: yes

        :steps:
            1. Hit Capsule's local flatpak index endpoint per parameter.

        :expectedresults:
            1. HTTP 200
        """
        ep = FLATPAK_ENDPOINTS[endpoint].format(module_capsule_configured.hostname)
        rq = requests.get(ep, verify=settings.server.verify_ca)
        assert rq.ok, f'Expected 200 but got {rq.status_code} from {endpoint} registry index'

    @pytest.mark.e2e
    @pytest.mark.skip_if_not_set('capsule')
    @pytest.mark.parametrize('distro', ['rhel7', 'rhel8_bos', 'rhel9_bos', 'rhel10_bos'])
    def test_positive_sync_kickstart_repo(
        self, target_sat, module_capsule_configured, function_sca_manifest_org, distro
    ):
        """Sync kickstart repository to the capsule.

        :id: bc97b53f-f79b-42f7-8014-b0641435bcfc

        :parametrized: yes

        :steps:
            1. Sync a kickstart repository to Satellite.
            2. Publish it in a CV, promote to Capsule's LCE.
            3. Check it is synced to Capsule without errors.
            4. Check for kickstart content on Satellite and Capsule.

        :expectedresults:
            1. The kickstart repo is successfully synced to the Capsule.

        :BZ: 1992329
        """
        repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=function_sca_manifest_org.id,
            product=REPOS['kickstart'][distro]['product'],
            reposet=REPOS['kickstart'][distro]['reposet'],
            repo=REPOS['kickstart'][distro]['name'],
            releasever=REPOS['kickstart'][distro]['version'],
        )
        repo = target_sat.api.Repository(id=repo_id).read()
        lce = target_sat.api.LifecycleEnvironment(organization=function_sca_manifest_org).create()
        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Update capsule's download policy to on_demand
        module_capsule_configured.update_download_policy('on_demand')

        # Create a content view with the repository
        cv = target_sat.api.ContentView(
            organization=function_sca_manifest_org, repository=[repo]
        ).create()
        # Sync repository
        repo.sync(timeout='10m')
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2
        # Check for kickstart content on SAT and CAPS
        tail = None
        if distro == 'rhel7':
            tail = f'rhel/server/7/{REPOS["kickstart"][distro]["version"]}/x86_64/kickstart'
        elif 'beta' in distro:
            tail = f'{distro.split("_")[0]}/{REPOS["kickstart"][distro]["version"]}/beta/x86_64/baseos/kickstart'
        else:
            tail = f'{distro.split("_")[0]}/{REPOS["kickstart"][distro]["version"]}/x86_64/baseos/kickstart'  # noqa:E501
        url_base = (
            f'pulp/content/{function_sca_manifest_org.label}/{lce.label}/{cv.label}/'
            f'content/dist/{tail}'
        )
        # Check kickstart specific files
        for file in KICKSTART_CONTENT:
            sat_file = target_sat.checksum_by_url(f'{target_sat.url}/{url_base}/{file}')
            caps_file = target_sat.checksum_by_url(
                f'{module_capsule_configured.url}/{url_base}/{file}'
            )
            assert sat_file == caps_file

        # Check packages
        sat_pkg_url = f'{target_sat.url}/{url_base}/Packages/'
        caps_pkg_url = f'{module_capsule_configured.url}/{url_base}/Packages/'
        sat_pkgs = get_repo_files_by_url(sat_pkg_url)
        caps_pkgs = get_repo_files_by_url(caps_pkg_url)
        assert len(caps_pkgs)
        assert sat_pkgs == caps_pkgs

    @pytest.mark.e2e
    @pytest.mark.pit_client
    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_container_repo_end_to_end(
        self,
        target_sat,
        module_capsule_configured,
        module_container_contenthost,
        function_org,
        function_product,
        function_lce,
    ):
        """Sync container repositories with schema1, schema2,
        and both of them to the capsule and pull them to a
        content host.

        :id: 8fab295c-a9bf-4c00-b800-f721ae8f29fe

        :steps:
            1. Sync container repositories to Satellite.
            2. Publish them in a CV, promote to Capsule's LCE.
            3. Check the Capsule is synced without errors.
            4. Pull the image from the Capsule to a host.

        :expectedresults:
            1. The container repo is successfully synced to the Capsule.
            2. The image is successfully pulled from Capsule to a host.

        :parametrized: yes

        :BZ: 2125244, 2148813

        :Verifies: SAT-25813

        :customerscenario: true
        """
        upstream_names = [
            'quay/busybox',  # schema 1
            'foreman/busybox-test',  # schema 2
            'foreman/foreman',  # schema 1+2
        ]
        repos = []

        for ups_name in upstream_names:
            repo = target_sat.api.Repository(
                content_type='docker',
                docker_upstream_name=ups_name,
                product=function_product,
                url='https://quay.io',
            ).create()
            repo.sync(timeout='20m')
            repos.append(repo)

        # Associate LCE with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create and publish a content view with all repositories
        cv = target_sat.api.ContentView(organization=function_org, repository=repos).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        # Promote the latest CV version into capsule's LCE
        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Pull the images from capsule to the content host
        repo_paths = [
            f'{function_org.label}/{function_lce.label}/{cv.label}/{function_product.label}/{repo.label}'.lower()
            for repo in repos
        ]

        for con_client in settings.container.clients:
            result = module_container_contenthost.execute(
                f'{con_client} login -u {settings.server.admin_username}'
                f' -p {settings.server.admin_password} {module_capsule_configured.hostname}'
            )
            assert result.status == 0

            for path in repo_paths:
                result = module_container_contenthost.execute(
                    f'{con_client} search {module_capsule_configured.hostname}/{path}'
                )
                assert result.status == 0
                if not is_open('SAT-25813'):
                    assert f'{module_capsule_configured.hostname}/{path}' in result.stdout

                result = module_container_contenthost.execute(
                    f'{con_client} pull {module_capsule_configured.hostname}/{path}'
                )
                assert result.status == 0
                result = module_container_contenthost.execute(f'{con_client} images')
                assert f'{module_capsule_configured.hostname}/{path}' in result.stdout

                result = module_container_contenthost.execute(
                    f'{con_client} rmi {module_capsule_configured.hostname}/{path}'
                )
                assert result.status == 0

            result = module_container_contenthost.execute(
                f'{con_client} logout {module_capsule_configured.hostname}'
            )
            assert result.status == 0

        # Inspect the images with skopeo (BZ#2148813)
        result = module_capsule_configured.execute('yum -y install skopeo')
        assert result.status == 0

        target_sat.api.LifecycleEnvironment(
            id=function_lce.id, registry_unauthenticated_pull='true'
        ).update(['registry_unauthenticated_pull'])

        sleep(20)

        skopeo_cmd = 'skopeo --debug inspect docker://'
        for path in repo_paths:
            result = module_capsule_configured.execute(
                f'{skopeo_cmd}{target_sat.hostname}/{path}:latest'
            )
            assert result.status == 0
            result = module_capsule_configured.execute(
                f'{skopeo_cmd}{module_capsule_configured.hostname}/{path}:latest'
            )
            assert result.status == 0

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_collection_repo(
        self,
        request,
        target_sat,
        module_capsule_configured,
        function_product,
        function_lce_library,
    ):
        """Sync ansible-collection repo to the Capsule, consume it on a host.

        :id: cfca7b28-fb70-429a-9aa2-db0d8aaf99bc

        :steps:
            1. Create an ansible-collection type repository.
            2. Sync the repository to the Capsule through the Library LCE.
               (CVs are unsupported yet)
            3. Check the Capsule is synced without errors.
            4. Try to install the collections from the Capsule on a Content Host.

        :expectedresults:
            1. The ansible-collection repo is successfully synced to the Capsule.
            2. The collection is successfully installed on the Content Host.

        :parametrized: yes

        :BZ: 2121583
        """
        requirements = '''
        ---
        collections:
        - name: theforeman.foreman
          version: "2.1.0"
        - name: theforeman.operations
          version: "0.1.0"
        '''
        repo = target_sat.api.Repository(
            content_type='ansible_collection',
            ansible_collection_requirements=requirements,
            product=function_product,
            url=ANSIBLE_GALAXY,
        ).create()

        # Associate the Library LCE with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce_library.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert function_lce_library.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Sync the repo
        timestamp = datetime.now(UTC)
        repo.sync(timeout=600)
        repo = repo.read()
        assert repo.content_counts['ansible_collection'] == 2

        module_capsule_configured.wait_for_sync(start_time=timestamp)

        repo_path = repo.full_path.replace(target_sat.hostname, module_capsule_configured.hostname)
        coll_path = './collections'
        cfg_path = './ansible.cfg'
        cfg = (
            '[defaults]\n'
            f'collections_paths = {coll_path}\n\n'
            '[galaxy]\n'
            'server_list = capsule_galaxy\n\n'
            '[galaxy_server.capsule_galaxy]\n'
            f'url={repo_path}\n'
        )

        request.addfinalizer(lambda: target_sat.execute(f'rm -rf {cfg_path} {coll_path}'))

        # Try to install collections from the Capsule
        target_sat.execute(f'echo "{cfg}" > {cfg_path}')
        result = target_sat.execute(
            'ansible-galaxy collection install theforeman.foreman theforeman.operations'
        )
        assert result.status == 0
        assert 'error' not in result.stdout.lower()

        result = target_sat.execute(f'ls {coll_path}/ansible_collections/theforeman/')
        assert result.status == 0
        assert 'foreman' in result.stdout
        assert 'operations' in result.stdout

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_file_repo(
        self, target_sat, module_capsule_configured, function_org, function_product, function_lce
    ):
        """Sync file-type repository to the capsule.

        :id: 8835c440-016f-408b-8b08-17da8e25a991

        :steps:
            1. Sync file-type repository to Satellite.
            2. Upload one extra file to the repository.
            3. Publish it in a CV, promote to Capsule's LCE.
            4. Check it is synced to Capsule without errors.
            5. Run one more sync, check it succeeds.
            6. Check for content on Satellite and Capsule.

        :expectedresults:
            1. Both capsule syncs succeed.
            2. Content is accessible on both, Satellite and Capsule.

        :BZ: 1985122
        """
        repo = target_sat.api.Repository(
            content_type='file',
            product=function_product,
            url=FAKE_FILE_LARGE_URL,
        ).create()
        repo.sync()

        # Upload one more iso file
        with open(DataFile.FAKE_FILE_NEW_NAME, 'rb') as handle:
            repo.upload_content(files={'content': handle})

        # Associate LCE with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create and publish a content view with all repositories
        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        # Promote the latest CV version into capsule's LCE
        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Run one more sync, check for status (BZ#1985122)
        sync_status = module_capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success'

        # Check for content on SAT and CAPS
        sat_repo_url = target_sat.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        sat_files = get_repo_files_by_url(sat_repo_url, extension='iso')
        caps_files = get_repo_files_by_url(caps_repo_url, extension='iso')
        assert len(sat_files) == len(caps_files) == FAKE_FILE_LARGE_COUNT + 1
        assert FAKE_FILE_NEW_NAME in caps_files
        assert sat_files == caps_files

        for file in sat_files:
            sat_file = target_sat.checksum_by_url(f'{sat_repo_url}{file}')
            caps_file = target_sat.checksum_by_url(f'{caps_repo_url}{file}')
            assert sat_file == caps_file

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_CV_to_multiple_LCEs(
        self, target_sat, module_capsule_configured, module_sca_manifest_org
    ):
        """Synchronize a CV to multiple LCEs at the same time.
        All sync tasks should succeed.

        :id: bd3cbeee-234f-4088-81b3-8f0d6c76e968

        :steps:
            1. Sync a repository to the Satellite.
            2. Create two LCEs, assign them to the Capsule.
            3. Create a Content View, add the repository and publish it.
            4. Promote the CV to both Capsule's LCEs without waiting for
               Capsule sync task completion.
            5. Check all sync tasks finished without errors.

        :expectedresults:
            1. All capsule syncs succeed.

        :customerscenario: true

        :BZ: 1830403
        """
        # Sync a repository to the Satellite.
        repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_sca_manifest_org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhel7_extra']['name'],
            reposet=REPOSET['rhel7_extra'],
            releasever=None,
        )
        repo = target_sat.api.Repository(id=repo_id).read()
        repo.sync()

        # Create two LCEs, assign them to the Capsule.
        lce1 = target_sat.api.LifecycleEnvironment(organization=module_sca_manifest_org).create()
        lce2 = target_sat.api.LifecycleEnvironment(
            organization=module_sca_manifest_org, prior=lce1
        ).create()
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': [lce1.id, lce2.id]}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        # there can and will be LCEs from other tests and orgs, but len() >= 2
        assert len(result['results']) >= 2
        assert {lce1.id, lce2.id}.issubset([capsule_lce['id'] for capsule_lce in result['results']])

        # Create a Content View, add the repository and publish it.
        cv = target_sat.api.ContentView(
            organization=module_sca_manifest_org, repository=[repo]
        ).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        # Promote the CV to both Capsule's LCEs without waiting for Capsule sync task completion.
        cvv = cv.version[-1].read()
        assert len(cvv.environment) == 1
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': lce1.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': lce2.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 3

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_capsule_sync_status_persists(
        self, target_sat, module_capsule_configured, function_org, function_product, function_lce
    ):
        """Synchronize a capsule, delete the task in foreman-rake,
        and then verify that the capsule is still listed as synced

        :id: aa3d7dbb-8cbb-441c-85c2-70e85794c3a9

        :steps:
            1. Create and Sync a Repo
            2. Associate lifecycle env with capsule
            3. Create a CV with the repo
            4. Publish CV
            5. Promote to lifecycle env
            6. Sync Capsule
            7. Delete all sync tasks using foreman-rake console
            8. Verify the status of capsule is still synced

        :bz: 1956985

        :customerscenario: true
        """
        repo_url = settings.repos.yum_1.url
        repo = target_sat.api.Repository(product=function_product, url=repo_url).create()
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        repo.sync()
        cv.publish()
        cv = cv.read()

        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)

        # Delete all capsule sync tasks so that we fall back for audits.
        task_result = target_sat.execute(
            """echo "ForemanTasks::Task.where(action:'Synchronize capsule """
            f"""\\'{module_capsule_configured.hostname}\\'').delete_all" | foreman-rake console"""
        )
        assert task_result.status == 0

        # Ensure task records were deleted.
        task_result = target_sat.execute(
            """echo "ForemanTasks::Task.where(action:'Synchronize capsule """
            f"""\\'{module_capsule_configured.hostname}\\'')" | foreman-rake console"""
        )
        assert task_result.status == 0
        assert '[]' in task_result.stdout

        # Check sync status again, and ensure last_sync_time is still correct
        sync_status = module_capsule_configured.nailgun_capsule.content_get_sync()
        assert (
            datetime.strptime(sync_status['last_sync_time'], '%Y-%m-%d %H:%M:%S UTC').replace(
                tzinfo=UTC
            )
            >= timestamp
        )

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_remove_capsule_orphans(
        self,
        target_sat,
        pytestconfig,
        capsule_configured,
        function_sca_manifest_org,
        function_lce_library,
    ):
        """Synchronize RPM content to the capsule, disassociate the capsule form the content
        source and resync, run orphan cleanup and ensure the RPM artifacts were removed.

        :id: 7089a36e-ea68-47ad-86ac-9945b732b0c4

        :setup:
            1. A blank external capsule that has not been synced yet with immediate download policy.

        :steps:
            1. Enable RHST repo and sync it to the Library LCE.
            2. Set immediate download policy to the capsule, assign it the Library LCE and sync it.
               Ensure the RPM artifacts were created.
            3. Remove the Library LCE from the capsule and resync it.
            4. Run orphan cleanup for the capsule.
            5. Ensure the artifacts were removed.

        :expectedresults:
            1. RPM artifacts are created after capsule sync.
            2. RPM artifacts are removed after orphan cleanup.

        :customerscenario: true

        :BZ: 22043089, 2211962

        """
        if pytestconfig.option.n_minus:
            pytest.skip('Test cannot be run on n-minus setups session-scoped capsule')
        # Enable RHST repo and sync it to the Library LCE.
        repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=function_sca_manifest_org.id,
            product=REPOS['rhst8']['product'],
            repo=REPOS['rhst8']['name'],
            reposet=REPOSET['rhst8'],
        )
        repo = target_sat.api.Repository(id=repo_id).read()
        repo.sync()

        # Set immediate download policy to the capsule, assign it the Library LCE and sync it.
        proxy = capsule_configured.nailgun_smart_proxy.read()
        proxy.download_policy = 'immediate'
        proxy.update(['download_policy'])

        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce_library.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results']) == 1
        assert result['results'][0]['id'] == function_lce_library.id

        sync_status = capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success', 'Capsule sync task failed.'

        # Ensure the RPM artifacts were created.
        result = capsule_configured.execute(f'ls {PULP_ARTIFACT_DIR}*/* | xargs file | grep RPM')
        assert not result.status, 'RPM artifacts are missing after capsule sync.'

        # Remove the Library LCE from the capsule and resync it.
        capsule_configured.nailgun_capsule.content_delete_lifecycle_environment(
            data={'environment_id': function_lce_library.id}
        )
        sync_status = capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success', 'Capsule sync task failed.'

        # datetime string (local time) to search for proper task.
        timestamp = (datetime.now().replace(microsecond=0) - timedelta(seconds=1)).strftime(
            '%B %d, %Y at %I:%M:%S %p'
        )
        # Run orphan cleanup for the capsule.
        target_sat.execute(
            'foreman-rake katello:delete_orphaned_content RAILS_ENV=production '
            f'SMART_PROXY_ID={capsule_configured.nailgun_capsule.id}'
        )
        target_sat.wait_for_tasks(
            search_query=(
                'label = Actions::Katello::OrphanCleanup::RemoveOrphans'
                f' and started_at >= "{timestamp}"'
            ),
            search_rate=5,
            max_tries=10,
        )

        # Ensure the artifacts were removed.
        result = capsule_configured.execute(f'ls {PULP_ARTIFACT_DIR}*/* | xargs file | grep RPM')
        assert result.status, 'RPM artifacts are still present. They should be gone.'

    @pytest.mark.e2e
    @pytest.mark.parametrize(
        'repos_collection',
        [
            {
                'distro': 'rhel10',
                'YumRepository': {'url': settings.repos.yum_0.url},
            }
        ],
        indirect=True,
    )
    @pytest.mark.rhel_ver_match('N-0')
    def test_complete_sync_fixes_metadata(
        self,
        module_target_sat,
        module_capsule_configured,
        rhel_contenthost,
        repos_collection,
        function_org,
        function_lce,
        default_location,
    ):
        """Ensure that Capsule complete sync repairs repository metadata.

        :id: bd84f5d0-5d77-4828-ade5-404e713d465b

        :parametrized: yes

        :Verifies: SAT-28575

        :customerscenario: true

        :setup:
            1. Satellite with registered external Capsule, associated with an LCE.
            2. Sync a yum repo, publish and promote it to a CVE, sync the Capsule and wait for it.

        :steps:
            1. Gather all metadata files and their checksums from repodata.
            2. Locate all metadata artifacts on the Capsule filesystem and destroy them.
            3. Trigger the complete Capsule sync.
            4. Ensure the metadata artifacts were restored.
            5. Register a content host and run dnf actions.

        :expectedresults:
            1. Metadata artifacts are repaired after the complete Capsule sync.
            2. Repository is consumable at the content host via Capsule.

        """
        # Associate LCE with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Sync a yum repo, publish and promote it to a CVE, sync the Capsule and wait for it.
        timestamp = datetime.now(UTC)
        repos_collection.setup_content(function_org.id, function_lce.id, override=True)
        module_capsule_configured.wait_for_sync(start_time=timestamp)

        # Gather all metadata files and their checksums from repodata.
        caps_repo_url = module_capsule_configured.get_published_repo_url(
            org=function_org.label,
            lce=function_lce.label,
            cv=repos_collection.setup_content_data['content_view']['label'],
            prod=repos_collection.setup_content_data['product']['label'],
            repo=repos_collection.setup_content_data['repos'][0]['label'],
        )
        meta_files = get_repo_files_by_url(f'{caps_repo_url}repodata/', extension='gz')
        meta_sums = [file.split('-')[0] for file in meta_files]
        meta_sums.append(
            module_target_sat.checksum_by_url(
                f'{caps_repo_url}repodata/repomd.xml', sum_type='sha256sum'
            )
        )

        # Locate all metadata artifacts on the Capsule filesystem and destroy them.
        for sum in meta_sums:
            ai = module_capsule_configured.get_artifact_info(checksum=sum)
            module_capsule_configured.execute(f'rm -f {ai.path}')
            with pytest.raises(FileNotFoundError):
                module_capsule_configured.get_artifact_info(checksum=sum)

        # Trigger the complete Capsule sync.
        sync_status = module_capsule_configured.nailgun_capsule.content_sync(
            data={'skip_metadata_check': 'true'}
        )
        assert sync_status['result'] == 'success', 'Capsule sync task failed.'

        # Ensure the metadata artifacts were restored.
        assert all(module_capsule_configured.get_artifact_info(checksum=sum) for sum in meta_sums)

        # Register a content host and run dnf actions.
        nc = module_capsule_configured.nailgun_smart_proxy
        module_target_sat.api.SmartProxy(id=nc.id, organization=[function_org]).update(
            ['organization']
        )
        module_target_sat.api.SmartProxy(id=nc.id, location=[default_location]).update(['location'])

        result = rhel_contenthost.api_register(
            module_target_sat,
            smart_proxy=nc,
            organization=function_org,
            location=default_location,
            activation_keys=[repos_collection.setup_content_data['activation_key']['name']],
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        host = module_target_sat.api.Host().search(
            query={'search': f'name="{rhel_contenthost.hostname}"'}
        )[0]
        assert nc.id == host.content_facet_attributes['content_source_id'], (
            'Expected to see the Capsule as the content source'
        )

        result = rhel_contenthost.execute('dnf repolist')
        assert result.status == 0
        assert repos_collection.setup_content_data['repos'][0].content_label in result.stdout

        result = rhel_contenthost.execute('dnf install -y cheetah')  # with dependencies
        assert result.status == 0

        result = rhel_contenthost.execute('dnf -y update')
        assert result.status == 0

    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_capsule_sync_openstack_container_repos(
        self,
        module_target_sat,
        module_capsule_configured,
        function_org,
        function_product,
        function_lce,
    ):
        """Synchronize openstack container repositories to capsule

        :id: 23e64385-7f34-4ab9-bd63-72306e5a4de0

        :setup:
            1. A blank external capsule that has not been synced yet.

        :steps:
            1. Enable and sync openstack container repos.

        :expectedresults:
            1. container repos should sync on capsule.

        :customerscenario: true

        :BZ: 2154734

        """
        upstream_names = [
            'rhosp13/openstack-cinder-api',
            'rhosp13/openstack-neutron-server',
            'rhosp13/openstack-neutron-dhcp-agent',
            'rhosp13/openstack-nova-api',
        ]
        repos = []

        for ups_name in upstream_names:
            repo = module_target_sat.api.Repository(
                content_type='docker',
                docker_upstream_name=ups_name,
                product=function_product,
                url=settings.container.rh.registry_hub,
                upstream_username=settings.subscription.rhn_username,
                upstream_password=settings.subscription.rhn_password,
            ).create()
            repo.sync(timeout=1800)
            repos.append(repo)

        # Associate LCE with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create and publish a content view with all repositories
        cv = module_target_sat.api.ContentView(organization=function_org, repository=repos).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        # Promote the latest CV version into capsule's LCE
        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

    @pytest.mark.parametrize(
        'repos_collection',
        [
            {
                'distro': 'rhel8',
                'YumRepository': {'url': settings.repos.module_stream_1.url},
                'FileRepository': {'url': CUSTOM_FILE_REPO},
                'DockerRepository': {
                    'url': settings.container.registry_hub,
                    'upstream_name': settings.container.upstream_name,
                },
                'AnsibleRepository': {
                    'url': ANSIBLE_GALAXY,
                    'requirements': [
                        {'name': 'theforeman.foreman', 'version': '2.1.0'},
                        {'name': 'theforeman.operations', 'version': '0.1.0'},
                    ],
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize('filtered', [False, True], ids=['unfiltered', 'filtered'])
    def test_positive_content_counts_for_mixed_cv(
        self,
        target_sat,
        module_capsule_configured,
        repos_collection,
        function_org,
        function_lce,
        function_lce_library,
        filtered,
    ):
        """Verify the content counts for a mixed-content CV

        :id: d8a0dea1-d30c-4c30-b3b1-46316de4ff29

        :parametrized: yes

        :setup:
            1. A content view with repos of all content types (currently yum, file, docker, AC)
               published into (unfiltered and filtered) CVV and promoted to an LCE.

        :steps:
            1. Assign the Capsule with Library and the LCE where the setup CVV is promoted to.
            2. Check the capsule doesn't provide any content counts for the setup CVV until synced.
            3. Sync the Capsule and get the content counts again. We should get counts for every
               repo in the CVV multiplied by shared LCEs (LCEs where the CVV is promoted to and
               synced to the Capsule, including Library).
            4. Get the content counts from Satellite side and compare them with Capsule.

        :expectedresults:
            1. Capsule doesn't return any counts for CVV until it is synced.
            2. After sync, content counts from Capsule match those from Satellite.
        """
        expected_keys = {
            'yum': {'rpm', 'package_group', 'module_stream', 'erratum'},
            'file': {'file'},
            'docker': {'docker_tag', 'docker_manifest', 'docker_manifest_list'},
            'ansible_collection': {'ansible_collection'},
        }

        repos_collection.setup_content(function_org.id, function_lce.id)
        cv_id = repos_collection.setup_content_data['content_view']['id']
        cv = target_sat.api.ContentView(id=cv_id).read()

        if filtered:
            for filter_type in ['rpm', 'docker']:
                cvf = target_sat.api.AbstractContentViewFilter(
                    type=filter_type,
                    content_view=cv,
                    inclusion=True,
                ).create()
                target_sat.api.ContentViewFilterRule(
                    content_view_filter=cvf, name='cat' if filter_type == 'rpm' else 'latest'
                ).create()
            cv.publish()
            cv = cv.read()
            cv.version.sort(key=lambda version: version.id)

        cvv = cv.version[-1].read()

        # Assign the Capsule with both content LCEs
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': [function_lce.id, function_lce_library.id]}
        )
        capsule_lces = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()[
            'results'
        ]
        assert len(capsule_lces)
        assert {function_lce.id, function_lce_library.id}.issubset(
            [lce['id'] for lce in capsule_lces]
        )

        # Check the counts for CVV are not present at the Capsule side before sync.
        caps_counts = module_capsule_configured.nailgun_capsule.content_counts()
        assert caps_counts is None or cvv.id not in caps_counts['content_view_versions']

        # Sync, wait for counts to be updated and get them from the Capsule.
        sync_status = module_capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success', 'Capsule sync task failed.'

        target_sat.wait_for_tasks(
            search_query=('label = Actions::Katello::CapsuleContent::UpdateContentCounts'),
            search_rate=5,
            max_tries=10,
        )

        caps_counts = module_capsule_configured.nailgun_capsule.content_counts()[
            'content_view_versions'
        ]
        assert str(cvv.id) in caps_counts, 'CVV is missing in content counts.'
        caps_counts = caps_counts[str(cvv.id)]

        # Every "environment repo" (the one promoted to an LCE and synced to the Capsule)
        # is shown in the content_counts, so we get N-times more for every shared lce.
        shared_lces = {env.id for env in cvv.environment} & {env['id'] for env in capsule_lces}
        assert len(caps_counts['repositories']) == len(cvv.repository) * len(shared_lces), (
            'Repositories count does not match.'
        )

        # Read the environment repos from Satellite side and compare the counts with Capsule.
        sat_repos = [
            target_sat.api.Repository(id=repo).read() for repo in caps_counts['repositories']
        ]
        for repo in sat_repos:
            cnt = caps_counts['repositories'][str(repo.id)]
            assert repo.content_type == cnt['metadata']['content_type']
            common_keys = set(repo.content_counts.keys()) & set(cnt['counts'].keys())
            assert len(common_keys), f'No common keys found for type "{repo.content_type}".'
            assert expected_keys[repo.content_type].issubset(common_keys), (
                'Some fields are missing: expected '
                f'{expected_keys[repo.content_type]} but found {common_keys}'
            )
            assert all(
                [repo.content_counts.get(key) == cnt['counts'].get(key) for key in common_keys]
            )

    @pytest.mark.order(1)
    def test_positive_content_counts_blank_update(
        self,
        target_sat,
        module_capsule_configured,
    ):
        """Verify the content counts and update endpoint for a blank Capsule.

        :id: da9c993e-258e-4215-9d8f-f0feced412d0

        :setup:
            1. A blank unsynced Capsule.

        :steps:
            1. Get content counts from a blank capsule.
            2. Run content counts update via API.
            3. Check no content counts yet.

        :expectedresults:
            1. Capsule returns None for content counts.
            2. Content update task is created and succeeds.
            3. Capsule keeps returning None or empty list for content counts.

        :CaseImportance: Medium
        """
        counts = module_capsule_configured.nailgun_capsule.content_counts()
        assert counts is None

        task = module_capsule_configured.nailgun_capsule.content_update_counts()
        assert task, 'No task was created for content update.'
        assert 'Actions::Katello::CapsuleContent::UpdateContentCounts' in task['label']
        assert 'success' in task['result']

        counts = module_capsule_configured.nailgun_capsule.content_counts()
        assert counts is None or len(counts['content_view_versions']) == 0, (
            f"No content counts expected, but got:\n{counts['content_view_versions']}."
        )

    @pytest.mark.parametrize('module_autosync_setting', [True], indirect=True)
    @pytest.mark.parametrize(
        'setting_update', ['automatic_content_count_updates=False'], indirect=True
    )
    def test_automatic_content_counts_update_toggle(
        self,
        target_sat,
        module_capsule_configured,
        module_autosync_setting,
        setting_update,
        function_org,
        function_product,
        function_lce,
    ):
        """Verify the automatic content counts update can be turned off and on again.

        :id: aa8d50e3-c04c-4e0f-a1c2-544767331973

        :setup:
            1. Satellite with registered external Capsule.
            2. foreman_proxy_content_auto_sync setting is turned on.
            3. automatic_content_count_updates setting is turned off.

        :steps:
            1. Sync some content to the Capsule, capsule is synced automatically.
            2. Verify no content counts update task was spawned after capsule sync completed.
            3. Invoke manual capsule sync and verify no update task was spawned again.
            4. Turn the automatic_content_count_updates on, invoke manual capsule sync again
               and verify the update task was spawned this time.

        :expectedresults:
            1. Capsule content counts update task respects the setting.

        :CaseImportance: Medium

        :BlockedBy: SAT-25503

        :Verifies: SAT-26453

        :customerscenario: true
        """
        # Sync some content to the Capsule, capsule is synced automatically.
        repo = target_sat.api.Repository(
            product=function_product, url=settings.repos.yum_1.url
        ).create()
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        capsule_lces = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(capsule_lces['results'])
        assert function_lce.id in [lce['id'] for lce in capsule_lces['results']]

        cv = target_sat.api.ContentView(organization=function_org, repository=[repo]).create()
        repo.sync()
        cv.publish()
        cv = cv.read()

        cvv = cv.version[-1].read()
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)

        # Verify no content counts update task was spawned after capsule sync completed.
        with pytest.raises(AssertionError) as err:
            target_sat.wait_for_tasks(
                search_query=(
                    'label = Actions::Katello::CapsuleContent::UpdateContentCounts'
                    f' and started_at >= "{timestamp}"'
                ),
                search_rate=5,
                max_tries=12,
            )
        assert 'No task was found' in str(err)

        # Invoke manual capsule sync and verify no update task again.
        sync_status = module_capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success'

        with pytest.raises(AssertionError) as err:
            target_sat.wait_for_tasks(
                search_query=(
                    'label = Actions::Katello::CapsuleContent::UpdateContentCounts'
                    f' and started_at >= "{timestamp}"'
                ),
                search_rate=5,
                max_tries=12,
            )
        assert 'No task was found' in str(err)

        # Turn the automatic_content_count_updates on, invoke manual capsule sync again
        # and verify the update task was spawned this time.
        setting_update.value = True
        setting_update = setting_update.update({'value'})

        sync_status = module_capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success'

        target_sat.wait_for_tasks(
            search_query=(
                'label = Actions::Katello::CapsuleContent::UpdateContentCounts'
                f' and started_at >= "{timestamp}"'
            ),
            search_rate=5,
            max_tries=12,
        )

    def test_positive_read_with_non_admin_user(
        self,
        target_sat,
        module_capsule_configured,
        default_org,
        default_location,
        default_non_admin_user,
    ):
        """Try to list and read Capsules with a non-admin user with and without permissions.

        :id: f3ee19fa-9b91-4b49-b00a-8debee903ce6

        :setup:
            1. Satellite with registered external Capsule.
            2. Non-admin user without any roles/permissions.

        :steps:
            1. Assign the capsule to the default org/loc so it can be searched and found.
            2. Using the non-admin user try to list all or particular Capsule.
            3. Add Viewer role to the user and try again.

        :expectedresults:
            1. Read should fail without Viewer role.
            2. Read should succeed when Viewer role added.

        :BZ: 2096930

        :customerscenario: true
        """
        # Assign the capsule to the default org/loc so it can be searched and found.
        nc = module_capsule_configured.nailgun_smart_proxy
        target_sat.api.SmartProxy(
            id=nc.id, organization=[default_org], location=[default_location]
        ).update(['organization', 'location'])

        # Using the non-admin user try to list all or particular Capsule
        user = default_non_admin_user
        sc = ServerConfig(
            auth=(user.login, user.password),
            url=target_sat.url,
            verify=settings.server.verify_ca,
        )

        with pytest.raises(HTTPError) as error:
            target_sat.api.Capsule(server_config=sc).search()
        assert error.value.response.status_code == 403
        assert 'Access denied' in error.value.response.text

        with pytest.raises(HTTPError) as error:
            target_sat.api.Capsule(
                server_config=sc, id=module_capsule_configured.nailgun_capsule.id
            ).read()
        assert error.value.response.status_code == 403
        assert 'Access denied' in error.value.response.text

        # Add Viewer role to the user and try again.
        v_role = target_sat.api.Role().search(query={'search': 'name="Viewer"'})
        assert len(v_role) == 1, 'Expected just one Viewer to be found.'
        user.role = [v_role[0]]
        user.update(['role'])

        res = target_sat.api.Capsule(server_config=sc).search()
        assert len(res) >= 2, 'Expected at least one internal and one or more external Capsule(s).'
        assert {target_sat.hostname, module_capsule_configured.hostname}.issubset(
            [caps.name for caps in res]
        ), 'Internal and/or external Capsule was not listed.'

        res = target_sat.api.Capsule(
            server_config=sc, id=module_capsule_configured.nailgun_capsule.id
        ).read()
        assert res.name == module_capsule_configured.hostname, 'External Capsule not found.'

    def test_positive_reclaim_space(
        self,
        target_sat,
        module_capsule_configured,
    ):
        """Verify the reclaim_space endpoint spawns the Reclaim space task
        and apidoc references the endpoint correctly.

        :id: eb16ed53-0489-4bb9-a0da-8d857a1c7d06

        :setup:
            1. A registered external Capsule.

        :steps:
            1. Trigger the reclaim space task via API, check it succeeds.
            2. Check the apidoc references the correct endpoint.

        :expectedresults:
            1. Reclaim_space endpoint spawns the Reclaim space task and it succeeds.
            2. Apidoc references the correct endpoint.

        :CaseImportance: Medium

        :BZ: 2218179

        :customerscenario: true
        """
        # Trigger the reclaim space task via API, check it succeeds
        task = module_capsule_configured.nailgun_capsule.content_reclaim_space()
        assert task, 'No task was created for reclaim space.'
        assert 'Actions::Pulp3::CapsuleContent::ReclaimSpace' in task['label'], (
            'Unexpected task triggered'
        )
        assert 'success' in task['result'], 'Reclaim task did not succeed'

        # Check the apidoc references the correct endpoint
        try:
            reclaim_doc = next(
                method
                for method in target_sat.apidoc['docs']['resources']['capsule_content']['methods']
                if '/apidoc/v2/capsule_content/reclaim_space' in method['doc_url']
            )
        except StopIteration:
            raise AssertionError(
                'Could not find the reclaim_space apidoc at the expected path.'
            ) from None
        assert len(reclaim_doc['apis']) == 1
        assert reclaim_doc['apis'][0]['http_method'] == 'POST', 'POST method was expected.'
        assert (
            reclaim_doc['apis'][0]['api_url'] == '/katello/api/capsules/:id/content/reclaim_space'
        ), 'Documented path did not meet the expectation.'

    @pytest.mark.e2e
    @pytest.mark.skip_if_not_set('capsule')
    def test_cleanup_orphaned_content(
        self,
        add_proxy_cli_config,
        module_target_sat,
        module_capsule_configured,
        function_org,
        function_product,
        function_lce,
    ):
        """Verify that when there are orphaned distributions, orphaned content cleanup can still work properly.

        :id: a88ba493-eeae-4b6d-999b-dd697fc073f5

        :steps:
            1. Create and sync a repository.
            2. Associate the LCE with a capsule, and sync.
            3. Add content to the repository, publish and promote to the LCE, and sync.
            4. Add a [cli-proxy] entry to .config/pulp/cli.toml pointing to the capsule
            5. Using pulp CLI and foreman-rake, create a publication and distribution using the first version of the repository.
            6. Trigger orphan cleanup on both capsule and satellite.

        :customerscenario: true

        :Verifies: SAT-31400

        :expectedresults:

            1. Orphaned cleanup runs successfully when there are orphaned distributions and publications present.
        """
        repo_url = settings.repos.yum_1.url
        repo = module_target_sat.api.Repository(product=function_product, url=repo_url).create()
        # Associate the lifecycle environment with the capsule
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': function_lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert function_lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = module_target_sat.api.ContentView(
            organization=function_org, repository=[repo]
        ).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment,
        # invoking capsule sync task(s)
        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()

        # Update a repository with 1 new rpm
        with open(DataFile.RPM_TO_UPLOAD, 'rb') as handle:
            repo.upload_content(files={'content': handle})

        # Publish and promote the repository
        repo = repo.read()
        cv.publish()
        cv = cv.read()
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()

        timestamp = datetime.now(UTC)
        cvv.promote(data={'environment_ids': function_lce.id})

        module_capsule_configured.wait_for_sync(start_time=timestamp)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Assert that packages count in the repository is updated
        assert repo.content_counts['rpm'] == (FAKE_1_YUM_REPOS_COUNT + 1)

        # Create orphaned publication and distribution on Satellite
        version_href = (
            module_target_sat.execute(
                f'echo "::Katello::Repository.find({repo.id}).version_href" | foreman-rake console'
            )
            .stdout.split('"')[1]
            .removesuffix("versions/2/")
        )
        publication_href = module_target_sat.execute(
            f"pulp --force rpm publication create --repository {version_href} --version 1"
        ).stdout.split('"')[3]
        module_target_sat.execute(
            f"pulp --force rpm distribution create --name test2 --base-path test2 --publication {publication_href}"
        )

        # Create orphaned publication and distribution on Capsule
        version_href = (
            module_target_sat.execute(
                "pulp --force --profile proxy repository list --field latest_version_href"
            )
            .stdout.split('"')[3]
            .removesuffix("versions/2/")
        )
        publication_href = module_target_sat.execute(
            f"pulp --force --profile proxy rpm publication create --repository {version_href} --version 1"
        ).stdout.split('"')[3]
        module_target_sat.execute(
            f"pulp --force --profile proxy rpm distribution create --name test2 --base-path test2 --publication {publication_href}"
        )

        # Run orphan cleanup on satellite and capsule
        module_target_sat.run_orphan_cleanup(module_capsule_configured.nailgun_smart_proxy.id)
        module_target_sat.run_orphan_cleanup(module_target_sat.nailgun_smart_proxy.id)


class TestPodman:
    """Tests specific to using podman push/pull on Satellite

    :CaseComponent: Repositories

    :team: Phoenix-content
    """

    @pytest.fixture(scope='class')
    def enable_podman_capsule(module_product, module_capsule_configured):
        """Enable base_os and appstream repos on the sat through cdn registration and install podman."""
        module_capsule_configured.register_to_cdn()
        if module_capsule_configured.os_version.major > 7:
            module_capsule_configured.enable_repo(module_capsule_configured.REPOS['rhel_bos']['id'])
            module_capsule_configured.enable_repo(module_capsule_configured.REPOS['rhel_aps']['id'])
        else:
            module_capsule_configured.enable_repo(module_capsule_configured.REPOS['rhscl']['id'])
            module_capsule_configured.enable_repo(module_capsule_configured.REPOS['rhel']['id'])
        result = module_capsule_configured.execute(
            'dnf install -y --disableplugin=foreman-protector podman'
        )
        assert result.status == 0

    def test_negative_podman_capsule_push(
        self,
        module_target_sat,
        module_product,
        module_org,
        module_lce,
        enable_podman_capsule,
        module_capsule_configured,
    ):
        """Attempt to push a Podman image to a Capsule/Smart Proxy

        :id: 310f629a-837a-4457-980e-d2f4345b495e

        :steps:
            1. Using podman, pull an image from the fedoraproject registry.
            2. Attempt to push this image to a Capsule/Smart Proxy

        :expectedresults: Podman containers cannot be pushed to a Capsule/Smart Proxy and an appropriate
            error is returned when attempting to do so.

        :CaseImportance: High
        """
        IMAGE_NAME_TAG = 'fedora:latest'
        image_pull = module_capsule_configured.execute(
            f'podman pull registry.fedoraproject.org/{IMAGE_NAME_TAG}'
        )
        assert image_pull.status == 0
        large_image_id = image_pull.stdout.strip()
        assert large_image_id
        result = module_capsule_configured.execute(
            f'podman push --creds {settings.server.admin_username}:{settings.server.admin_password} {large_image_id} {module_capsule_configured.hostname}/{IMAGE_NAME_TAG}'
        )
        assert 'Pushing content is unsupported' in result.stderr

    def test_negative_login_without_pass(
        self, request, module_capsule_configured, module_container_contenthost
    ):
        """Ensure the interactive podman login fails with appropriate message
        when password is omitted.

        :id: a2ef15e0-e95e-49ea-8378-b5fbe4e350b3

        :steps:
            1. Try interactive podman login to a Capsule without any password provided.

        :expectedresults: Login fails with appropriate error message.

        :customerscenario: true

        :verifies: SAT-25333

        """
        request.addfinalizer(
            lambda: module_container_contenthost.execute(
                f'podman logout {module_capsule_configured.hostname}'
            )
        )
        cmd = (
            f"""expect -c 'spawn podman login --tls-verify=false {module_capsule_configured.hostname}; """
            """expect "Username:"; send "\n"; expect "Password:"; send "\n"; expect eof'"""
        )
        res = module_container_contenthost.execute(cmd)
        assert res.status == 0  # expect cmd succeeded
        assert 'login succeeded' not in res.stdout.lower()
        assert 'invalid username/password' in res.stdout.lower()
