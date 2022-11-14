"""Test class for the content management tests.

:Requirement: Content Management

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re
import uuid

import pytest
from nailgun import client
from nailgun import entities

from robottelo import constants
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants.repos import ANSIBLE_GALAXY
from robottelo.content_info import get_repo_files_by_url
from robottelo.content_info import get_repomd
from robottelo.content_info import get_repomd_revision
from robottelo.helpers import form_repo_url
from robottelo.helpers import get_data_file
from robottelo.helpers import md5_by_url


class TestSatelliteContentManagement:
    """Content Management related tests, which exercise katello with pulp
    interactions.
    """

    @pytest.mark.tier2
    @pytest.mark.skip("Uses old large_errata repo from repos.fedorapeople")
    def test_positive_sync_repos_with_large_errata(self):
        """Attempt to synchronize 2 repositories containing large (or lots of)
        errata.

        :id: d6680b9f-4c88-40b4-8b96-3d170664cb28

        :customerscenario: true

        :BZ: 1463811

        :CaseLevel: Integration

        :expectedresults: both repositories were successfully synchronized
        """
        org = entities.Organization().create()
        for _ in range(2):
            product = entities.Product(organization=org).create()
            repo = entities.Repository(product=product, url=settings.repos.yum_7.url).create()
            response = repo.sync()
            assert response, f"Repository {repo} failed to sync."

    @pytest.mark.tier2
    def test_positive_sync_repos_with_lots_files(self):
        """Attempt to synchronize repository containing a lot of files inside
        rpms.

        :id: 2cc09ce3-d5df-4caa-956a-78f83a7735ca

        :customerscenario: true

        :BZ: 1404345

        :CaseLevel: Integration

        :expectedresults: repository was successfully synchronized
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product, url=settings.repos.yum_8.url).create()
        response = repo.sync()
        assert response, f"Repository {repo} failed to sync."

    @pytest.mark.tier4
    def test_positive_sync_kickstart_repo(self, module_manifest_org, target_sat):
        """No encoding gzip errors on kickstart repositories
        sync.

        :id: dbdabc0e-583c-4186-981a-a02844f90412

        :expectedresults: No encoding gzip errors present in /var/log/messages.

        :CaseLevel: Integration

        :customerscenario: true

        :steps:

            1. Sync a kickstart repository.
            2. After the repo is synced, change the download policy to
                immediate.
            3. Sync the repository again.
            4. Assert that no errors related to encoding gzip are present in
                /var/log/messages.
            5. Assert that sync was executed properly.

        :CaseComponent: Pulp

        :Assignee: ltran

        :BZ: 1687801
        """
        rh_repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_manifest_org.id,
            product=constants.PRDS['rhel8'],
            repo=constants.REPOS['rhel8_bos_ks']['name'],
            reposet=constants.REPOSET['rhel8_bos_ks'],
            releasever='8.4',
        )
        rh_repo = entities.Repository(id=rh_repo_id).read()
        rh_repo.sync()
        rh_repo.download_policy = 'immediate'
        rh_repo = rh_repo.update(['download_policy'])
        call_entity_method_with_timeout(rh_repo.sync, timeout=600)
        result = target_sat.execute(
            'grep pulp /var/log/messages | grep failed | grep encoding | grep gzip'
        )
        assert result.status == 1
        assert not result.stdout
        rh_repo = rh_repo.read()
        assert rh_repo.content_counts['package'] > 0
        assert rh_repo.content_counts['package_group'] > 0
        assert rh_repo.content_counts['rpm'] > 0

    @pytest.mark.tier2
    def test_positive_mirroring_policy(self, target_sat):
        """Assert that the content of a repository with 'Mirror Policy' enabled
        is restored properly after resync.

        :id: cbf1c781-cb96-4b4a-bae2-15c9f5be5e50

        :steps:
            1. Create and sync a repo with 'Mirroring Policy - mirror complete enabled.
            2. Remove all packages from the repo and upload another one.
            3. Resync the repo again.
            4. Check the content was restored properly.

        :expectedresults:
            1. The resync restores the original content properly.

        :CaseLevel: System
        """
        repo_url = settings.repos.yum_0.url
        packages_count = constants.FAKE_0_YUM_REPO_PACKAGES_COUNT

        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        repo = entities.Repository(
            download_policy='immediate',
            mirroring_policy='mirror_complete',
            product=prod,
            url=repo_url,
        ).create()
        repo.sync()
        repo = repo.read()
        assert repo.content_counts['package'] == packages_count

        # remove all packages from the repo and upload another one
        packages = entities.Package(repository=repo).search(query={'per_page': '1000'})
        repo.remove_content(data={'ids': [package.id for package in packages]})

        with open(get_data_file(constants.RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})

        repo = repo.read()
        assert repo.content_counts['package'] == 1
        files = get_repo_files_by_url(repo.full_path)
        assert len(files) == 1
        assert constants.RPM_TO_UPLOAD in files

        # resync the repo again and check the content
        repo.sync()

        repo = repo.read()
        assert repo.content_counts['package'] == packages_count
        files = get_repo_files_by_url(repo.full_path)
        assert len(files) == packages_count
        assert constants.RPM_TO_UPLOAD not in files


@pytest.mark.run_in_one_thread
class TestCapsuleContentManagement:
    """Content Management related tests, which exercise katello with pulp
    interactions and use capsule.

    :CaseComponent: Capsule-Content

    :Assignee: vsedmik
    """

    def update_capsule_download_policy(self, capsule_configured, download_policy):
        """Updates capsule's download policy to desired value"""
        proxy = entities.SmartProxy(id=capsule_configured.nailgun_capsule.id).read()
        proxy.download_policy = download_policy
        proxy.update(['download_policy'])

    @pytest.mark.tier3
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_insights_puppet_package_availability(self, capsule_configured):
        """Check `redhat-access-insights-puppet` package availability for
        capsule

        :BZ: 1315844

        :id: a31b0e21-aa5d-44e2-a408-5e01b79db3a1

        :CaseComponent: RHCloud-Insights

        :Assignee: jpathan

        :customerscenario: true

        :expectedresults: `redhat-access-insights-puppet` package is delivered
            in capsule repo and is available for installation on capsule via
            yum

        :CaseLevel: System
        """
        package_name = 'redhat-access-insights-puppet'
        result = capsule_configured.run(f'yum list {package_name} | grep @capsule')
        if result.status != 0:
            result = capsule_configured.run(f'yum list available | grep {package_name}')
        assert result.status == 0

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_uploaded_content_library_sync(self, capsule_configured):
        """Ensure custom repo with no upstream url and manually uploaded
        content after publishing to Library is synchronized to capsule
        automatically

        :id: f5406312-dd31-4551-9f03-84eb9c3415f5

        :customerscenario: true

        :BZ: 1340686

        :expectedresults: custom content is present on external capsule

        :CaseLevel: System
        """
        org = entities.Organization(smart_proxy=[capsule_configured.nailgun_capsule.id]).create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product, url=None).create()
        capsule = entities.Capsule(id=capsule_configured.nailgun_capsule.id).search(
            query={'search': f'name={capsule_configured.hostname}'}
        )[0]
        # Find "Library" lifecycle env for specific organization
        lce = entities.LifecycleEnvironment(organization=org).search(
            query={'search': f'name={constants.ENVIRONMENT}'}
        )[0]
        # Associate the lifecycle environment with the capsule
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()

        assert len(result['results']) >= 1
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()

        # Upload custom content into the repo
        with open(get_data_file(constants.RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})

        assert repo.read().content_counts['package'] == 1

        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        assert len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()

        # Verify that new artifacts were created on Capsule
        result = capsule_configured.run('find /var/lib/pulp/media/artifact -type f | wc -l')
        assert int(result.stdout) > 0

        # Verify the RPM published on Capsule
        caps_repo_url = form_repo_url(
            capsule_configured,
            org=org.label,
            lce=lce.label,
            cv=cv.label,
            prod=product.label,
            repo=repo.label,
        )
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert len(caps_files) == 1
        assert caps_files[0] == constants.RPM_TO_UPLOAD

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_checksum_sync(self, capsule_configured):
        """Synchronize repository to capsule, update repository's checksum
        type, trigger capsule sync and make sure checksum type was updated on
        capsule

        :id: eb07bdf3-6cd8-4a2f-919b-8dfc84e16115

        :customerscenario: true

        :BZ: 1288656, 1664288, 1732066, 2001052

        :expectedresults: checksum type is updated in repodata of corresponding
            repository on capsule

        :CaseLevel: System

        :CaseImportance: Critical
        """
        # Create organization, product, lce and repository with sha256 checksum
        # type
        org = entities.Organization(smart_proxy=[capsule_configured.nailgun_capsule.id]).create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(
            product=product,
            checksum_type='sha256',
            mirroring_policy='additive',
            download_policy='immediate',
        ).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environment with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results']) >= 1
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Sync, publish and promote a repo
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        repo.sync()
        repo = repo.read()
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Wait till capsule sync finishes
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']

        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        last_sync_time = sync_status['last_sync_time']

        # Verify repodata's checksum type is sha256, not sha1 on capsule
        repo_url = form_repo_url(
            capsule_configured,
            org=org.label,
            prod=product.label,
            repo=repo.label,
            lce=lce.label,
            cv=cv.label,
        )
        repomd = get_repomd(repo_url)
        checksum_types = re.findall(r'(?<=checksum type=").*?(?=")', repomd)
        assert "sha1" not in checksum_types
        assert "sha256" in checksum_types

        # Update repo's checksum type to sha1
        repo.checksum_type = 'sha1'
        repo = repo.update(['checksum_type'])

        # Sync, publish, and promote repo
        repo.sync()
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 2

        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Wait till capsule sync finishes
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert (
            len(sync_status['active_sync_tasks']) or sync_status['last_sync_time'] != last_sync_time
        )

        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()

        # Verify repodata's checksum type has updated to sha1 on capsule
        repomd = get_repomd(repo_url)
        checksum_types = re.findall(r'(?<=checksum type=").*?(?=")', repomd)
        assert "sha1" in checksum_types
        assert "sha256" not in checksum_types

    @pytest.mark.skip_if_open("BZ:2025494")
    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_updated_repo(
        self, target_sat, capsule_configured, function_org, function_product
    ):
        """Sync a custom repo with no upstream url but uploaded content to the Capsule via promoted CV,
        update content of the repo, publish and promote the CV again, resync the Capsule.

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

        :CaseLevel: Integration

        :customerscenario: true

        :BZ: 2025494
        """
        repo = entities.Repository(url=None, product=function_product).create()
        lce = entities.LifecycleEnvironment(organization=function_org).create()

        # Associate the lifecycle environment with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Upload custom content into the repo
        with open(get_data_file(constants.RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})

        assert repo.read().content_counts['package'] == 1

        # Create, publish and promote CV with the repository to the Capsule's LCE
        cv = entities.ContentView(organization=function_org, repository=[repo]).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()

        # Upload more content to the repository
        with open(get_data_file(constants.SRPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})

        assert repo.read().content_counts['package'] == 2

        # Publish new version and promote it to the Capsule's LCE.
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 2

        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']
        # Wait till capsule sync finishes and assert the sync task succeeded
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll(timeout=600)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['last_failed_sync_tasks']) == 0

        # Check the content is synced on the Capsule side properly
        sat_repo_url = form_repo_url(
            target_sat,
            org=function_org.label,
            lce=lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        caps_repo_url = form_repo_url(
            capsule_configured,
            org=function_org.label,
            lce=lce.label,
            cv=cv.label,
            prod=function_product.label,
            repo=repo.label,
        )
        sat_files = get_repo_files_by_url(sat_repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert sat_files == caps_files
        assert len(caps_files) == 2

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_capsule_sync(self, capsule_configured, target_sat):
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

        :CaseLevel: System
        """
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        repo_url = settings.repos.yum_1.url
        org = entities.Organization(smart_proxy=[capsule_configured.nailgun_capsule.id]).create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product, url=repo_url).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environment with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']

        # Content of the published content view in
        # lifecycle environment should equal content of the
        # repository
        assert repo.content_counts['package'] == cvv.package_count

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        last_sync_time = sync_status['last_sync_time']

        # Assert that the content published on the capsule is exactly the
        # same as in repository on satellite
        sat_repo_url = form_repo_url(
            target_sat,
            org=org.label,
            lce=lce.label,
            cv=cv.label,
            prod=product.label,
            repo=repo.label,
        )
        caps_repo_url = form_repo_url(
            capsule_configured,
            org=org.label,
            lce=lce.label,
            cv=cv.label,
            prod=product.label,
            repo=repo.label,
        )
        sat_files = get_repo_files_by_url(sat_repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert sat_files == caps_files

        lce_revision_capsule = get_repomd_revision(caps_repo_url)

        # Sync repository for a second time
        result = repo.sync()
        # Assert that the task summary contains a message that says the
        # publish was skipped because content had not changed
        assert result['result'] == 'success'
        assert 'Associating Content: 0/0' in result['humanized']['output']

        # Publish a new version of content view
        cv.publish()
        cv = cv.read()
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        # Promote new content view version to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Wait till capsule sync finishes
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        tasks = []

        if not sync_status['active_sync_tasks']:
            assert sync_status['last_sync_time'] != last_sync_time
        else:
            for task in sync_status['active_sync_tasks']:
                tasks.append(entities.ForemanTask(id=task['id']))
                tasks[-1].poll()

        # Assert that the value of repomd revision of repository in
        # lifecycle environment on the capsule has not changed
        new_lce_revision_capsule = get_repomd_revision(caps_repo_url)
        assert lce_revision_capsule == new_lce_revision_capsule

        # Update a repository with 1 new rpm
        with open(get_data_file(constants.RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})

        # Publish and promote the repository
        repo = repo.read()
        cv.publish()
        cv = cv.read()
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert (
            len(sync_status['active_sync_tasks']) or sync_status['last_sync_time'] != last_sync_time
        )

        # Assert that packages count in the repository is updated
        assert repo.content_counts['package'] == (constants.FAKE_1_YUM_REPOS_COUNT + 1)

        # Assert that the content of the published content view in
        # lifecycle environment is exactly the same as content of the
        # repository
        assert repo.content_counts['package'] == cvv.package_count

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()

        # Assert that the content published on the capsule is exactly the
        # same as in the repository
        sat_files = get_repo_files_by_url(sat_repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert sat_files == caps_files

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_iso_library_sync(self, module_manifest_org, capsule_configured):
        """Ensure RH repo with ISOs after publishing to Library is synchronized
        to capsule automatically

        :id: 221a2d41-0fef-46dd-a804-fdedd7187163

        :customerscenario: true

        :BZ: 1303102, 1480358, 1303103, 1734312

        :expectedresults: ISOs are present on external capsule

        :CaseLevel: System
        """
        # Enable & sync RH repository with ISOs
        rh_repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_manifest_org.id,
            product=constants.PRDS['rhsc'],
            repo=constants.REPOS['rhsc7_iso']['name'],
            reposet=constants.REPOSET['rhsc7_iso'],
            releasever=None,
        )
        rh_repo = entities.Repository(id=rh_repo_id).read()
        call_entity_method_with_timeout(rh_repo.sync, timeout=2500)
        # Find "Library" lifecycle env for specific organization
        lce = entities.LifecycleEnvironment(organization=module_manifest_org).search(
            query={'search': f'name={constants.ENVIRONMENT}'}
        )[0]

        # Associate the lifecycle environment with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results']) >= 1
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = entities.ContentView(organization=module_manifest_org, repository=[rh_repo]).create()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        # Verify ISOs are present on satellite
        sat_isos = get_repo_files_by_url(rh_repo.full_path, extension='iso')
        assert len(sat_isos) == 4

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll(timeout=600)

        # Verify all the ISOs are present on capsule
        caps_path = (
            f'{capsule_configured.url}/pulp/content/{module_manifest_org.label}/{lce.label}'
            f'/{cv.label}/content/dist/rhel/server/7/7Server/x86_64/sat-capsule/6.4/iso/'
        )
        caps_isos = get_repo_files_by_url(caps_path, extension='iso')
        assert len(caps_isos) == 4
        assert set(sat_isos) == set(caps_isos)

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_on_demand_sync(self, capsule_configured, target_sat):
        """Create a repository with 'on_demand' policy, add it to a CV,
        promote to an 'on_demand' Capsule's LCE, check artifacts were created,
        download a published package, assert it matches the source.

        :id: ba470269-a7ad-4181-bc7c-8e17a177ca20

        :expectedresults:

            1. A custom yum repository is successfully synced and ContentView published
            2. The ContentView is successfully promoted to the Capsule's LCE and the content
               is automatically synced to the Capsule
            3. Artifacts are created on the Capsule in /var/lib/pulp/media/artifacts/
            4. Package is successfully downloaded from the Capsule, its checksum matches
               the original package from the upstream repo

        :CaseLevel: System
        """
        repo_url = settings.repos.yum_3.url
        packages_count = constants.FAKE_3_YUM_REPOS_COUNT
        package = constants.FAKE_3_YUM_REPO_RPMS[0]
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        repo = entities.Repository(
            download_policy='on_demand',
            mirroring_policy='mirror_complete',
            product=prod,
            url=repo_url,
        ).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environment with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()

        # Verify that new artifacts were created on Capsule but rpms were not downloaded
        result = capsule_configured.run('find /var/lib/pulp/media/artifact -type f | wc -l')
        assert 0 < int(result.stdout) < packages_count

        # Verify packages on Capsule match the source
        caps_repo_url = form_repo_url(
            capsule_configured,
            org=org.label,
            lce=lce.label,
            cv=cv.label,
            prod=prod.label,
            repo=repo.label,
        )
        source_files = get_repo_files_by_url(repo_url)
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert source_files == caps_files
        assert len(caps_files) == packages_count

        # Download a package from the Capsule and get its md5 checksum
        published_package_md5 = md5_by_url(f'{caps_repo_url}/{package}')
        # Get md5 checksum of source package
        package_md5 = md5_by_url(f'{repo_url}/{package}')
        # Assert checksums are matching
        assert package_md5 == published_package_md5

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_update_with_immediate_sync(self, capsule_configured, target_sat):
        """Create a repository with on_demand download policy, associate it
        with capsule, sync repo, update download policy to immediate, sync once
        more.

        :id: 511b531d-1fbe-4d64-ae31-0f9eb6625e7f

        :customerscenario: true

        :BZ: 1315752

        :expectedresults: content was successfully synchronized - capsule
            filesystem contains valid links to packages

        :CaseLevel: System
        """
        repo_url = settings.repos.yum_1.url
        packages_count = constants.FAKE_1_YUM_REPOS_COUNT
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        repo = entities.Repository(
            download_policy='on_demand',
            mirror_on_sync='mirror_complete',
            product=prod,
            url=repo_url,
        ).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Update capsule's download policy to on_demand to match repository's
        # policy
        self.update_capsule_download_policy(capsule_configured, 'on_demand')
        # Associate the lifecycle environment with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        # Update download policy to 'immediate'
        repo.download_policy = 'immediate'
        repo = repo.update(['download_policy'])

        assert repo.download_policy == 'immediate'

        # Update capsule's download policy as well
        self.update_capsule_download_policy(capsule_configured, 'immediate')

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
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()

        # Verify that new artifacts were created on Capsule
        result = capsule_configured.run('find /var/lib/pulp/media/artifact -type f | wc -l')
        assert int(result.stdout)

        # Verify the count of RPMs published on Capsule
        caps_repo_url = form_repo_url(
            capsule_configured,
            org=org.label,
            lce=lce.label,
            cv=cv.label,
            prod=prod.label,
            repo=repo.label,
        )
        caps_files = get_repo_files_by_url(caps_repo_url)
        assert len(caps_files) == packages_count

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_capsule_pub_url_accessible(self, capsule_configured):
        """Ensure capsule pub url is accessible

        :id: 311eaa2a-146b-4d18-95db-4fbbe843d5b2

        :customerscenario: true

        :expectedresults: capsule pub url is accessible

        :BZ: 1463810

        :CaseLevel: System
        """
        https_pub_url = f'https://{capsule_configured.ip_addr}/pub'
        http_pub_url = f'http://{capsule_configured.ip_addr}/pub'
        for url in [http_pub_url, https_pub_url]:
            response = client.get(url, verify=False)

            assert response.status_code == 200

            # check that one of the files is in the content
            assert b'katello-server-ca.crt' in response.content

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def test_positive_sync_kickstart_repo(
        self, module_manifest_org, target_sat, capsule_configured
    ):
        """Sync kickstart repository to the capsule.

        :id: bc97b53f-f79b-42f7-8014-b0641435bcfc

        :steps:
            1. Sync a kickstart repository to Satellite.
            2. Publish it in a CV, promote to Capsule's LCE.
            3. Check it is synced to Capsule without errors.
            4. Check for kickstart content on Satellite and Capsule.

        :expectedresults:
            1. The kickstart repo is successfully synced to the Capsule.

        :CaseLevel: Integration

        :BZ: 1992329
        """
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_manifest_org.id,
            product=constants.PRDS['rhel8'],
            repo=constants.REPOS['rhel8_bos_ks']['name'],
            reposet=constants.REPOSET['rhel8_bos_ks'],
            releasever='8.4',
        )
        repo = entities.Repository(id=repo_id).read()

        lce = entities.LifecycleEnvironment(organization=module_manifest_org).create()
        # Associate the lifecycle environment with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()

        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create a content view with the repository
        cv = entities.ContentView(organization=module_manifest_org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()

        assert len(cv.version) == 1

        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()

        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()

        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']

        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()

        # Assert the sync task succeeded
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['last_failed_sync_tasks']) == 0

        # Check for kickstart content on SAT and CAPS
        url_base = (
            f'pulp/content/{module_manifest_org.label}/{lce.label}/'
            f'{cv.label}/content/dist/rhel8/8.4/x86_64/baseos/kickstart'
        )

        # Check kickstart specific files
        for file in constants.KICKSTART_CONTENT:
            sat_file = md5_by_url(f'{target_sat.url}/{url_base}/{file}')
            caps_file = md5_by_url(f'{capsule_configured.url}/{url_base}/{file}')
            assert sat_file == caps_file

        # Check packages
        sat_pkg_url = f'{target_sat.url}/{url_base}/Packages/'
        caps_pkg_url = f'{capsule_configured.url}/{url_base}/Packages/'
        sat_pkgs = get_repo_files_by_url(sat_pkg_url)
        caps_pkgs = get_repo_files_by_url(caps_pkg_url)
        assert len(caps_pkgs)
        assert sat_pkgs == caps_pkgs

    @pytest.mark.tier4
    @pytest.mark.e2e
    @pytest.mark.skip_if_not_set('capsule', 'clients')
    def test_positive_sync_container_repo_end_to_end(
        self, target_sat, capsule_configured, container_contenthost, module_org, module_product
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

        :CaseLevel: Integration
        """
        upstream_names = [
            'quay/busybox',  # schema 1
            'foreman/busybox-test',  # schema 2
            'foreman/foreman',  # schema 1+2
        ]
        repos = []

        for ups_name in upstream_names:
            repo = entities.Repository(
                content_type='docker',
                docker_upstream_name=ups_name,
                product=module_product,
                url='https://quay.io',
            ).create()
            repo.sync(timeout='20m')
            repos.append(repo)

        # Create a LCE and associate it with the capsule
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create and publish a content view with all repositories
        cv = entities.ContentView(organization=module_org, repository=repos).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        # Promote the latest CV version into capsule's LCE
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']

        # Wait till capsule sync finishes and assert the sync task succeeded
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll(timeout=600)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['last_failed_sync_tasks']) == 0

        # Pull the images from capsule to the content host
        repo_paths = [
            (
                f'{module_org.label.lower()}-{lce.label.lower()}-{cv.label.lower()}-'
                f'{module_product.label.lower()}-{repo.label.lower()}'
            )
            for repo in repos
        ]

        for con_client in constants.CONTAINER_CLIENTS:
            result = container_contenthost.execute(
                f'{con_client} login -u {settings.server.admin_username}'
                f' -p {settings.server.admin_password} {capsule_configured.hostname}'
            )
            assert result.status == 0

            for path in repo_paths:
                result = container_contenthost.execute(
                    f'{con_client} search {capsule_configured.hostname}/{path}'
                )
                assert result.status == 0

                result = container_contenthost.execute(
                    f'{con_client} pull {capsule_configured.hostname}/{path}'
                )
                assert result.status == 0

                result = container_contenthost.execute(
                    f'{con_client} rmi {capsule_configured.hostname}/{path}'
                )
                assert result.status == 0

            result = container_contenthost.execute(
                f'{con_client} logout {capsule_configured.hostname}'
            )
            assert result.status == 0

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_collection_repo(
        self, target_sat, module_lce_library, module_product, capsule_configured, rhel7_contenthost
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

        :CaseLevel: Integration
        """
        requirements = '''
        ---
        collections:
        - name: theforeman.foreman
          version: "2.1.0"
        - name: theforeman.operations
          version: "0.1.0"
        '''
        repo = entities.Repository(
            content_type='ansible_collection',
            ansible_collection_requirements=requirements,
            product=module_product,
            url=ANSIBLE_GALAXY,
        ).create()

        # Associate the Library LCE with the capsule
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': module_lce_library.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert module_lce_library.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Sync the repo
        repo.sync(timeout=600)
        repo = repo.read()
        assert repo.content_counts['ansible_collection'] == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']

        # Wait till capsule sync finishes and assert the sync task succeeded
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll(timeout=600)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['last_failed_sync_tasks']) == 0

        # Configure the content host to fetch collections from capsule
        rhel7_contenthost.install_katello_ca(capsule_configured)
        rhel7_contenthost.create_custom_repos(
            **{
                'server': settings.repos.rhel7_os,
                'ansible': settings.repos.ansible_repo,
            }
        )
        result = rhel7_contenthost.execute('yum -y install ansible')
        assert result.status == 0

        repo_path = repo.full_path.replace(target_sat.hostname, capsule_configured.hostname)
        coll_path = './collections'
        cfg = (
            '[defaults]\n'
            f'collections_paths = {coll_path}\n\n'
            '[galaxy]\n'
            'server_list = capsule_galaxy\n\n'
            '[galaxy_server.capsule_galaxy]\n'
            f'url={repo_path}\n'
        )
        rhel7_contenthost.execute(f'echo "{cfg}" > ./ansible.cfg')

        # Try to install collections from the Capsule
        result = rhel7_contenthost.execute(
            'ansible-galaxy collection install theforeman.foreman theforeman.operations'
        )
        assert result.status == 0
        assert 'error' not in result.stdout.lower()

        result = rhel7_contenthost.execute(f'ls {coll_path}/ansible_collections/theforeman/')
        assert result.status == 0
        assert 'foreman' in result.stdout
        assert 'operations' in result.stdout

    @pytest.mark.tier4
    @pytest.mark.skip_if_not_set('capsule')
    def test_positive_sync_file_repo(
        self, target_sat, capsule_configured, module_org, module_product
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

        :CaseLevel: Integration

        :BZ: 1985122
        """
        repo = entities.Repository(
            content_type='file',
            product=module_product,
            url=constants.FAKE_FILE_LARGE_URL,
        ).create()
        repo.sync()

        # Upload one more iso file
        with open(get_data_file(constants.FAKE_FILE_NEW_NAME), 'rb') as handle:
            repo.upload_content(files={'content': handle})

        # Create a LCE and associate it with the capsule
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert len(result['results'])
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]

        # Create and publish a content view with all repositories
        cv = entities.ContentView(organization=module_org, repository=[repo]).create()
        cv.publish()
        cv = cv.read()
        assert len(cv.version) == 1

        # Promote the latest CV version into capsule's LCE
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        assert len(cvv.environment) == 2

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['active_sync_tasks']) or sync_status['last_sync_time']

        # Wait till capsule sync finishes and assert the sync task succeeded
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll(timeout=600)
        sync_status = capsule_configured.nailgun_capsule.content_get_sync()
        assert len(sync_status['last_failed_sync_tasks']) == 0

        # Run one more sync, check for status (BZ#1985122)
        sync_status = capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success'

        # Check for content on SAT and CAPS
        sat_repo_url = form_repo_url(
            target_sat,
            org=module_org.label,
            lce=lce.label,
            cv=cv.label,
            prod=module_product.label,
            repo=repo.label,
        )
        caps_repo_url = form_repo_url(
            capsule_configured,
            org=module_org.label,
            lce=lce.label,
            cv=cv.label,
            prod=module_product.label,
            repo=repo.label,
        )
        sat_files = get_repo_files_by_url(sat_repo_url, extension='iso')
        caps_files = get_repo_files_by_url(caps_repo_url, extension='iso')
        assert len(sat_files) == len(caps_files) == constants.FAKE_FILE_LARGE_COUNT + 1
        assert constants.FAKE_FILE_NEW_NAME in caps_files
        assert sat_files == caps_files

        for file in sat_files:
            sat_file = md5_by_url(f'{sat_repo_url}{file}')
            caps_file = md5_by_url(f'{caps_repo_url}{file}')
            assert sat_file == caps_file

    @pytest.mark.tier3
    def test_positive_allow_reregistration_when_dmi_uuid_changed(
        self, module_org, rhel_contenthost, target_sat
    ):
        """Register a content host with a custom DMI UUID, unregistering it, change
        the DMI UUID, and re-registering it again

        :id: 7f431cb2-5a63-41f7-a27f-62b86328b50d

        :expectedresults: The content host registers successfully

        :customerscenario: true

        :BZ: 1747177

        :CaseLevel: Integration
        """
        uuid_1 = str(uuid.uuid1())
        uuid_2 = str(uuid.uuid4())
        rhel_contenthost.install_katello_ca(target_sat)
        target_sat.execute(
            f'echo \'{{"dmi.system.uuid": "{uuid_1}"}}\' > /etc/rhsm/facts/uuid.facts'
        )
        result = rhel_contenthost.register_contenthost(module_org.label, lce=constants.ENVIRONMENT)
        assert result.status == 0
        result = rhel_contenthost.execute('subscription-manager clean')
        assert result.status == 0
        target_sat.execute(
            f'echo \'{{"dmi.system.uuid": "{uuid_2}"}}\' > /etc/rhsm/facts/uuid.facts'
        )
        result = rhel_contenthost.register_contenthost(module_org.label, lce=constants.ENVIRONMENT)
        assert result.status == 0
