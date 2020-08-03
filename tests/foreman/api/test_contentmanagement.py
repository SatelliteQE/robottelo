"""Test class for the content management tests.

:Requirement: Content Management

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
from time import sleep

import pytest
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError

from robottelo import manifests
from robottelo import ssh
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import CUSTOM_KICKSTART_REPO
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_1_YUM_REPO
from robottelo.constants import FAKE_1_YUM_REPO_RPMS
from robottelo.constants import FAKE_1_YUM_REPOS_COUNT
from robottelo.constants import FAKE_3_YUM_REPO
from robottelo.constants import FAKE_3_YUM_REPOS_COUNT
from robottelo.constants import FAKE_7_YUM_REPO
from robottelo.constants import FAKE_8_YUM_REPO
from robottelo.constants import PRDS
from robottelo.constants import PULP_PUBLISHED_ISO_REPOS_PATH
from robottelo.constants import PULP_PUBLISHED_PUPPET_REPOS_PATH
from robottelo.constants import PULP_PUBLISHED_YUM_REPOS_PATH
from robottelo.constants import REPO_TYPE
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants import RPM_TO_UPLOAD
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import stubbed
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import tier4
from robottelo.helpers import create_repo
from robottelo.helpers import form_repo_path
from robottelo.helpers import get_data_file
from robottelo.helpers import is_open
from robottelo.helpers import md5_by_url
from robottelo.host_info import get_repo_files
from robottelo.host_info import get_repomd_revision
from robottelo.test import APITestCase
from robottelo.vm import VirtualMachine
from robottelo.vm_capsule import CapsuleVirtualMachine


class ContentManagementTestCase(APITestCase):
    """Content Management related tests, which exercise katello with pulp
    interactions.
    """

    @tier2
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
            repo = entities.Repository(product=product, url=FAKE_7_YUM_REPO).create()
            with self.assertNotRaises(TaskFailedError):
                repo.sync()

    @tier2
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
        repo = entities.Repository(product=product, url=FAKE_8_YUM_REPO).create()
        with self.assertNotRaises(TaskFailedError):
            repo.sync()

    @tier4
    def test_positive_sync_kickstart_repo(self):
        """No encoding gzip errors on kickstart repositories
        sync.

        :id: dbdabc0e-583c-4186-981a-a02844f90412

        :expectedresults: No encoding gzip errors present in /var/log/messages.

        :CaseLevel: Integration

        :steps:

            1. Sync a kickstart repository.
            2. After the repo is synced, change the download policy to
                immediate.
            3. Sync the repository again.
            4. Assert that no errors related to encoding gzip are present in
                /var/log/messages.
            5. Assert that sync was executed properly.

        :CaseComponent: Pulp

        :BZ: 1687801
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product, url=CUSTOM_KICKSTART_REPO).create()
        repo.sync()
        repo.download_policy = 'immediate'
        repo = repo.update(['download_policy'])
        call_entity_method_with_timeout(repo.sync, timeout=600)
        result = ssh.command(
            'grep pulp /var/log/messages | grep failed | grep encoding | grep gzip'
        )
        self.assertEqual(result.return_code, 1)
        self.assertEqual(len(result.stdout), 0)
        repo = repo.read()
        self.assertGreater(repo.content_counts['package'], 0)
        self.assertGreater(repo.content_counts['package_group'], 0)
        self.assertGreater(repo.content_counts['rpm'], 0)


@run_in_one_thread
class CapsuleContentManagementTestCase(APITestCase):
    """Content Management related tests, which exercise katello with pulp
    interactions and use capsule.
    """

    @classmethod
    @skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def setUpClass(cls):
        """Create a separate capsule for tests"""
        super(CapsuleContentManagementTestCase, cls).setUpClass()
        cls.capsule_vm = CapsuleVirtualMachine()
        cls.capsule_vm.create()
        # for debugging purposes. you may replace these 3 variables with your
        # capsule values and comment lines above to speed up test execution
        cls.capsule_vm._capsule = entities.Capsule().search(
            query={'search': 'name={0}'.format(cls.capsule_vm.hostname)}
        )[0]

        cls.capsule_id = cls.capsule_vm._capsule.id
        cls.capsule_hostname = cls.capsule_vm.hostname
        cls.capsule_ip = cls.capsule_vm.ip_addr

    @classmethod
    def tearDownClass(cls):
        """Destroy the capsule"""
        cls.capsule_vm.destroy()
        super(CapsuleContentManagementTestCase, cls).tearDownClass()

    def update_capsule_download_policy(self, capsule_id, download_policy):
        """Updates capsule's download policy to desired value"""
        proxy = entities.SmartProxy(id=capsule_id).read()
        proxy.download_policy = download_policy
        proxy.update(['download_policy'])

    @tier3
    def test_positive_insights_puppet_package_availability(self):
        """Check `redhat-access-insights-puppet` package availability for
        capsule

        :BZ: 1315844

        :id: a31b0e21-aa5d-44e2-a408-5e01b79db3a1

        :CaseComponent: RHCloud-Insights

        :customerscenario: true

        :expectedresults: `redhat-access-insights-puppet` package is delivered
            in capsule repo and is available for installation on capsule via
            yum

        :CaseLevel: System
        """
        package_name = 'redhat-access-insights-puppet'
        result = ssh.command(
            'yum list {0} | grep @capsule'.format(package_name), hostname=self.capsule_ip
        )
        if result.return_code != 0:
            result = ssh.command(
                'yum list available | grep {0}'.format(package_name), hostname=self.capsule_ip
            )
        self.assertEqual(result.return_code, 0)

    @tier4
    def test_positive_uploaded_content_library_sync(self):
        """Ensure custom repo with no upstream url and manually uploaded
        content after publishing to Library is synchronized to capsule
        automatically

        :id: f5406312-dd31-4551-9f03-84eb9c3415f5

        :customerscenario: true

        :BZ: 1340686

        :expectedresults: custom content is present on external capsule

        :CaseLevel: System
        """
        # Create organization, product, repository with no upstream url
        org = entities.Organization(smart_proxy=[self.capsule_id]).create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product, url=None).create()
        capsule = entities.Capsule(id=self.capsule_id).search(
            query={'search': 'name={0}'.format(self.capsule_hostname)}
        )[0]
        # Find "Library" lifecycle env for specific organization
        lce = entities.LifecycleEnvironment(organization=org).search(
            query={'search': 'name={}'.format(ENVIRONMENT)}
        )[0]
        # Associate the lifecycle environment with the capsule
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(lce.id, [capsule_lce['id'] for capsule_lce in result['results']])

        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()

        # Upload custom content into the repo
        with open(get_data_file(RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})
        self.assertEqual(repo.read().content_counts['package'], 1)
        # Publish new version of the content view

        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 1)

        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        # Verify previously uploaded content is present on capsule
        lce_repo_path = form_repo_path(
            org=org.label,
            lce=lce.label,
            cv=cv.label,
            prod=product.label,
            repo=repo.label,
            capsule=True,
        )
        for i in range(5):
            capsule_rpms = get_repo_files(lce_repo_path, hostname=self.capsule_ip)
            if len(capsule_rpms) != 0:
                break
            else:
                sleep(5)
        self.assertEqual(len(capsule_rpms), 1)
        self.assertEqual(capsule_rpms[0], RPM_TO_UPLOAD)

    @tier4
    def test_positive_checksum_sync(self):
        """Synchronize repository to capsule, update repository's checksum
        type, trigger capsule sync and make sure checksum type was updated on
        capsule

        :id: eb07bdf3-6cd8-4a2f-919b-8dfc84e16115

        :customerscenario: true

        :BZ: 1288656, 1664288, 1732066

        :expectedresults: checksum type is updated in repodata of corresponding
            repository on  capsule

        :CaseLevel: System

        :CaseImportance: Critical
        """
        repomd_path = 'repodata/repomd.xml'
        # Create organization, product, lce and repository with sha256 checksum
        # type
        org = entities.Organization(smart_proxy=[self.capsule_id]).create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(
            product=product, checksum_type='sha256', download_policy='immediate'
        ).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environment with the capsule
        capsule = entities.Capsule(id=self.capsule_id).read()
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(lce.id, [capsule_lce['id'] for capsule_lce in result['results']])
        # Sync, publish and promote a repo
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        repo.sync()
        repo = repo.read()
        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 1)
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Wait till capsule sync finishes
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        sync_status = capsule.content_get_sync()
        last_sync_time = sync_status['last_sync_time']
        # Verify repodata's checksum type is sha256, not sha1 on capsule
        lce_repo_path = form_repo_path(
            org=org.label, lce=lce.label, cv=cv.label, prod=product.label, repo=repo.label
        )
        result = ssh.command(
            'grep -o \'checksum type="sha1"\' {}/{}'.format(lce_repo_path, repomd_path),
            hostname=self.capsule_ip,
        )
        self.assertNotEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout), 0)
        result = ssh.command(
            'grep -o \'checksum type="sha256"\' {}/{}'.format(lce_repo_path, repomd_path),
            hostname=self.capsule_ip,
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreater(len(result.stdout), 0)
        # Update repo's checksum type to sha1
        repo.checksum_type = 'sha1'
        repo = repo.update(['checksum_type'])
        # Sync, publish and promote repo
        repo.sync()
        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 2)
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Wait till capsule sync finishes
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1
            or sync_status['last_sync_time'] != last_sync_time
        )
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        # Verify repodata's checksum type has updated to sha1 on capsule
        result = ssh.command(
            'grep -o \'checksum type="sha256"\' {}/{}'.format(lce_repo_path, repomd_path),
            hostname=self.capsule_ip,
        )
        self.assertNotEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout), 0)
        result = ssh.command(
            'grep -o \'checksum type="sha1"\' {}/{}'.format(lce_repo_path, repomd_path),
            hostname=self.capsule_ip,
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreater(len(result.stdout), 0)

    @tier4
    def test_positive_capsule_sync(self):
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
        repo_name = gen_string('alphanumeric')
        # Create and publish custom repository with 2 packages in it
        repo_url = create_repo(repo_name, FAKE_1_YUM_REPO, FAKE_1_YUM_REPO_RPMS[0:2])
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        org = entities.Organization(smart_proxy=[self.capsule_id]).create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product, url=repo_url).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environment with the capsule
        capsule = entities.Capsule(id=self.capsule_id).read()
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(lce.id, [capsule_lce['id'] for capsule_lce in result['results']])
        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 1)
        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        # Assert that the content of the published content view in
        # lifecycle environment is exactly the same as content of
        # repository
        lce_repo_path = form_repo_path(
            org=org.label, lce=lce.label, cv=cv.label, prod=product.label, repo=repo.label
        )
        cvv_repo_path = form_repo_path(
            org=org.label, cv=cv.label, cvv=cvv.version, prod=product.label, repo=repo.label
        )
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        sync_status = capsule.content_get_sync()
        last_sync_time = sync_status['last_sync_time']

        # If BZ1439691 is open, need to sync repo once more, as repodata
        # will change on second attempt even with no changes in repo
        if is_open('BZ:1439691'):
            repo.sync()
            repo = repo.read()
            cv.publish()
            cv = cv.read()
            self.assertEqual(len(cv.version), 2)
            cv.version.sort(key=lambda version: version.id)
            cvv = cv.version[-1].read()
            promote(cvv, lce.id)
            cvv = cvv.read()
            self.assertEqual(len(cvv.environment), 2)
            sync_status = capsule.content_get_sync()
            self.assertTrue(
                len(sync_status['active_sync_tasks']) >= 1
                or sync_status['last_sync_time'] != last_sync_time
            )
            for task in sync_status['active_sync_tasks']:
                entities.ForemanTask(id=task['id']).poll()
            sync_status = capsule.content_get_sync()
            last_sync_time = sync_status['last_sync_time']

        # Assert that the content published on the capsule is exactly the
        # same as in repository on satellite
        lce_revision_capsule = get_repomd_revision(lce_repo_path, hostname=self.capsule_ip)
        self.assertEqual(
            get_repo_files(lce_repo_path, hostname=self.capsule_ip), get_repo_files(cvv_repo_path)
        )
        # Sync repository for a second time
        result = repo.sync()
        # Assert that the task summary contains a message that says the
        # publish was skipped because content had not changed
        self.assertEqual(result['result'], 'success')
        self.assertTrue(result['output']['post_sync_skipped'])
        self.assertEqual(result['humanized']['output'], 'No new packages.')
        # Publish a new version of content view
        cv.publish()
        cv = cv.read()
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        # Promote new content view version to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Wait till capsule sync finishes
        sync_status = capsule.content_get_sync()
        tasks = []
        if not sync_status['active_sync_tasks']:
            self.assertNotEqual(sync_status['last_sync_time'], last_sync_time)
        else:
            for task in sync_status['active_sync_tasks']:
                tasks.append(entities.ForemanTask(id=task['id']))
                tasks[-1].poll()
        # Assert that the value of repomd revision of repository in
        # lifecycle environment on the capsule has not changed
        new_lce_revision_capsule = get_repomd_revision(lce_repo_path, hostname=self.capsule_ip)
        self.assertEqual(lce_revision_capsule, new_lce_revision_capsule)
        # Update a repository with 1 new rpm
        create_repo(repo_name, FAKE_1_YUM_REPO, FAKE_1_YUM_REPO_RPMS[-1:])
        # Sync, publish and promote the repository
        repo.sync()
        repo = repo.read()
        cv.publish()
        cv = cv.read()
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1
            or sync_status['last_sync_time'] != last_sync_time
        )
        # Assert that packages count in the repository is updated
        self.assertEqual(repo.content_counts['package'], 3)
        # Assert that the content of the published content view in
        # lifecycle environment is exactly the same as content of the
        # repository
        cvv_repo_path = form_repo_path(
            org=org.label, cv=cv.label, cvv=cvv.version, prod=product.label, repo=repo.label
        )
        self.assertEqual(repo.content_counts['package'], cvv.package_count)
        self.assertEqual(get_repo_files(lce_repo_path), get_repo_files(cvv_repo_path))
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        # Assert that the content published on the capsule is exactly the
        # same as in the repository
        self.assertEqual(
            get_repo_files(lce_repo_path, hostname=self.capsule_ip), get_repo_files(cvv_repo_path)
        )

    @stubbed()
    @tier4
    def test_positive_iso_library_sync(self):
        """Ensure RH repo with ISOs after publishing to Library is synchronized
        to capsule automatically

        :id: 221a2d41-0fef-46dd-a804-fdedd7187163

        :customerscenario: true

        :BZ: 1303102, 1480358, 1303103, 1734312

        :expectedresults: ISOs are present on external capsule

        :CaseLevel: System
        """
        # Create organization, product, enable & sync RH repository with ISOs
        org = entities.Organization(smart_proxy=[self.capsule_id]).create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        rh_repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhsc'],
            repo=REPOS['rhsc7_iso']['name'],
            reposet=REPOSET['rhsc7_iso'],
            releasever=None,
        )
        rh_repo = entities.Repository(id=rh_repo_id).read()
        call_entity_method_with_timeout(rh_repo.sync, timeout=2500)
        capsule = entities.Capsule(id=self.capsule_id).read()
        # Find "Library" lifecycle env for specific organization
        lce = entities.LifecycleEnvironment(organization=org).search(
            query={'search': 'name={}'.format(ENVIRONMENT)}
        )[0]
        # Associate the lifecycle environment with the capsule
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(lce.id, [capsule_lce['id'] for capsule_lce in result['results']])
        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[rh_repo]).create()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 1)
        # Verify ISOs are present on satellite
        repo_path = os.path.join(PULP_PUBLISHED_ISO_REPOS_PATH, rh_repo.backend_identifier)
        sat_isos = get_repo_files(repo_path, extension='iso')
        self.assertGreater(len(result), 0)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll(timeout=600)
        # Verify all the ISOs are present on capsule
        capsule_isos = get_repo_files(repo_path, extension='iso', hostname=self.capsule_ip)
        self.assertGreater(len(result), 0)
        self.assertEqual(set(sat_isos), set(capsule_isos))

    @tier4
    def test_positive_on_demand_sync(self):
        """Create a repository with 'on_demand' sync, add it to lifecycle
        environment with a capsule, sync repository, examine existing packages
        on capsule, download any package, examine packages once more

        :id: ba470269-a7ad-4181-bc7c-8e17a177ca20

        :expectedresults:

            1. After initial syncing only symlinks are present on both
               satellite and capsule, no real packages were fetched.
            2. All the symlinks are pointing to non-existent files.
            3. Attempt to download package is successful
            4. Downloaded package checksum matches checksum of the source
               package

        :CaseLevel: System
        """
        repo_url = FAKE_3_YUM_REPO
        packages_count = FAKE_3_YUM_REPOS_COUNT
        package = FAKE_1_YUM_REPO_RPMS[0]
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        repo = entities.Repository(
            download_policy='on_demand', mirror_on_sync=True, product=prod, url=repo_url
        ).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environment with the capsule
        capsule = entities.Capsule(id=self.capsule_id).read()
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(lce.id, [capsule_lce['id'] for capsule_lce in result['results']])
        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 1)
        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        # Check whether the symlinks for all the packages were created on
        # satellite
        cvv_repo_path = form_repo_path(
            org=org.label, cv=cv.label, cvv=cvv.version, prod=prod.label, repo=repo.label
        )
        result = ssh.command('find {}/ -type l'.format(cvv_repo_path))
        self.assertEqual(result.return_code, 0)
        links = set(link for link in result.stdout if link)
        self.assertEqual(len(links), packages_count)
        # Ensure all the symlinks on satellite are broken (pointing to
        # nonexistent files)
        result = ssh.command(
            'find {}/ -type l ! -exec test -e {{}} \\; -print'.format(cvv_repo_path)
        )
        self.assertEqual(result.return_code, 0)
        broken_links = set(link for link in result.stdout if link)
        self.assertEqual(len(broken_links), packages_count)
        self.assertEqual(broken_links, links)
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        lce_repo_path = form_repo_path(
            org=org.label, lce=lce.label, cv=cv.label, prod=prod.label, repo=repo.label
        )
        # Check whether the symlinks for all the packages were created on
        # capsule
        result = ssh.command('find {}/ -type l'.format(lce_repo_path), hostname=self.capsule_ip)
        self.assertEqual(result.return_code, 0)
        links = set(link for link in result.stdout if link)
        self.assertEqual(len(links), packages_count)
        # Ensure all the symlinks on capsule are broken (pointing to
        # nonexistent files)
        result = ssh.command(
            'find {}/ -type l ! -exec test -e {{}} \\; -print'.format(lce_repo_path),
            hostname=self.capsule_ip,
        )
        self.assertEqual(result.return_code, 0)
        broken_links = set(link for link in result.stdout if link)
        self.assertEqual(len(broken_links), packages_count)
        self.assertEqual(broken_links, links)
        # Download package from satellite and get its md5 checksum
        published_repo_url = 'http://{}{}/pulp/{}/'.format(
            settings.server.hostname,
            ':{}'.format(settings.server.port) if settings.server.port else '',
            lce_repo_path.split('http/')[1],
        )
        package_md5 = md5_by_url('{}{}'.format(repo_url, package))
        # Get md5 checksum of source package
        published_package_md5 = md5_by_url('{}{}'.format(published_repo_url, package))
        # Assert checksums are matching
        self.assertEqual(package_md5, published_package_md5)

    @tier4
    def test_positive_mirror_on_sync(self):
        """Create 2 repositories with 'on_demand' download policy and mirror on
        sync option, associate them with capsule, sync first repo, move package
        from first repo to second one, sync it, attempt to install package on
        some host.

        :id: 39149642-1e7e-4ef8-8762-bec295913014

        :BZ: 1426408

        :expectedresults: host, subscribed to second repo only, can
            successfully install package

        :CaseLevel: System
        """
        repo1_name = gen_string('alphanumeric')
        repo2_name = gen_string('alphanumeric')
        # Create and publish first custom repository with 2 packages in it
        repo1_url = create_repo(repo1_name, FAKE_1_YUM_REPO, FAKE_1_YUM_REPO_RPMS[1:3])
        # Create and publish second repo with no packages in it
        repo2_url = create_repo(repo2_name)
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        org = entities.Organization().create()
        prod1 = entities.Product(organization=org).create()
        repo1 = entities.Repository(
            download_policy='on_demand', mirror_on_sync=True, product=prod1, url=repo1_url
        ).create()
        prod2 = entities.Product(organization=org).create()
        repo2 = entities.Repository(
            download_policy='on_demand', mirror_on_sync=True, product=prod2, url=repo2_url
        ).create()
        lce1 = entities.LifecycleEnvironment(organization=org).create()
        lce2 = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environments with the capsule
        capsule = entities.Capsule(id=self.capsule_id).read()
        for lce_id in (lce1.id, lce2.id):
            capsule.content_add_lifecycle_environment(data={'environment_id': lce_id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 2)
        self.assertTrue(
            {lce1.id, lce2.id}.issubset([capsule_lce['id'] for capsule_lce in result['results']])
        )
        # Create content views with the repositories
        cv1 = entities.ContentView(organization=org, repository=[repo1]).create()
        cv2 = entities.ContentView(organization=org, repository=[repo2]).create()
        # Sync first repository
        repo1.sync()
        repo1 = repo1.read()
        # Publish new version of the content view
        cv1.publish()
        cv1 = cv1.read()
        self.assertEqual(len(cv1.version), 1)
        cvv1 = cv1.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv1, lce1.id)
        cvv1 = cvv1.read()
        self.assertEqual(len(cvv1.environment), 2)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        # Move one package from the first repo to second one
        ssh.command(
            'mv {} {}'.format(
                os.path.join(PULP_PUBLISHED_YUM_REPOS_PATH, repo1_name, FAKE_1_YUM_REPO_RPMS[2]),
                os.path.join(PULP_PUBLISHED_YUM_REPOS_PATH, repo2_name, FAKE_1_YUM_REPO_RPMS[2]),
            )
        )
        # Update repositories (re-trigger 'createrepo' command)
        create_repo(repo1_name)
        create_repo(repo2_name)
        # Synchronize first repository
        repo1.sync()
        cv1.publish()
        cv1 = cv1.read()
        self.assertEqual(len(cv1.version), 2)
        cv1.version.sort(key=lambda version: version.id)
        cvv1 = cv1.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv1, lce1.id)
        cvv1 = cvv1.read()
        self.assertEqual(len(cvv1.environment), 2)
        # Synchronize second repository
        repo2.sync()
        repo2 = repo2.read()
        self.assertEqual(repo2.content_counts['package'], 1)
        cv2.publish()
        cv2 = cv2.read()
        self.assertEqual(len(cv2.version), 1)
        cvv2 = cv2.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv2, lce2.id)
        cvv2 = cvv2.read()
        self.assertEqual(len(cvv2.environment), 2)
        # Create activation key, add subscription to second repo only
        activation_key = entities.ActivationKey(
            content_view=cv2, environment=lce2, organization=org
        ).create()
        subscription = entities.Subscription(organization=org).search(
            query={'search': 'name={}'.format(prod2.name)}
        )[0]
        activation_key.add_subscriptions(data={'subscription_id': subscription.id})
        # Subscribe a host with activation key
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(org.label, activation_key.name)
            # Install the package
            package_name = FAKE_1_YUM_REPO_RPMS[2].rstrip('.rpm')
            result = client.run('yum install -y {}'.format(package_name))
            self.assertEqual(result.return_code, 0)
            # Ensure package installed
            result = client.run('rpm -qa | grep {}'.format(package_name))
            self.assertEqual(result.return_code, 0)
            self.assertIn(package_name, result.stdout[0])

    @tier4
    def test_positive_update_with_immediate_sync(self):
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
        repo_url = FAKE_1_YUM_REPO
        packages_count = FAKE_1_YUM_REPOS_COUNT
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        repo = entities.Repository(
            download_policy='on_demand', mirror_on_sync=True, product=prod, url=repo_url
        ).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Update capsule's download policy to on_demand to match repository's
        # policy
        self.update_capsule_download_policy(self.capsule_id, 'on_demand')
        # Associate the lifecycle environment with the capsule
        capsule = entities.Capsule(id=self.capsule_id).read()
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(lce.id, [capsule_lce['id'] for capsule_lce in result['results']])
        # Create a content view with the repository
        cv = entities.ContentView(organization=org, repository=[repo]).create()
        # Sync repository
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 1)
        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        # Update download policy to 'immediate'
        repo.download_policy = 'immediate'
        repo = repo.update(['download_policy'])
        self.assertEqual(repo.download_policy, 'immediate')
        # Update capsule's download policy as well
        self.update_capsule_download_policy(self.capsule_id, 'immediate')
        # Make sure to revert capsule's download policy after the test as the
        # capsule is shared among other tests
        self.addCleanup(self.update_capsule_download_policy, self.capsule_id, 'on_demand')
        # Sync repository once again
        repo.sync()
        repo = repo.read()
        # Publish new version of the content view
        cv.publish()
        cv = cv.read()
        self.assertEqual(len(cv.version), 2)
        cv.version.sort(key=lambda version: version.id)
        cvv = cv.version[-1].read()
        # Promote content view to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        # Check whether the symlinks for all the packages were created on
        # satellite
        cvv_repo_path = form_repo_path(
            org=org.label, cv=cv.label, cvv=cvv.version, prod=prod.label, repo=repo.label
        )
        result = ssh.command('find {}/ -type l'.format(cvv_repo_path))
        self.assertEqual(result.return_code, 0)
        links = set(link for link in result.stdout if link)
        self.assertEqual(len(links), packages_count)
        # Ensure there're no broken symlinks (pointing to nonexistent files) on
        # satellite
        result = ssh.command(
            'find {}/ -type l ! -exec test -e {{}} \\; -print'.format(cvv_repo_path)
        )
        self.assertEqual(result.return_code, 0)
        broken_links = set(link for link in result.stdout if link)
        self.assertEqual(len(broken_links), 0)
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        lce_repo_path = form_repo_path(
            org=org.label, lce=lce.label, cv=cv.label, prod=prod.label, repo=repo.label
        )
        # Check whether the symlinks for all the packages were created on
        # capsule
        result = ssh.command('find {}/ -type l'.format(lce_repo_path), hostname=self.capsule_ip)
        self.assertEqual(result.return_code, 0)
        links = set(link for link in result.stdout if link)
        self.assertEqual(len(links), packages_count)
        # Ensure there're no broken symlinks (pointing to nonexistent files) on
        # capsule
        result = ssh.command(
            'find {}/ -type l ! -exec test -e {{}} \\; -print'.format(lce_repo_path),
            hostname=self.capsule_ip,
        )
        self.assertEqual(result.return_code, 0)
        broken_links = set(link for link in result.stdout if link)
        self.assertEqual(len(broken_links), 0)

    @tier4
    def test_positive_sync_puppet_module_with_versions(self):
        """Ensure it's possible to sync multiple versions of the same puppet
        module to the capsule

        :id: 83a0ddd6-8a6a-43a0-b169-094a2556dd28

        :customerscenario: true

        :BZ: 1365952, 1655243

        :Steps:

            1. Register a capsule
            2. Associate LCE with the capsule
            3. Sync a puppet module with multiple versions
            4. Publish a CV with one version of puppet module and promote it to
               capsule's LCE
            5. Wait for capsule synchronization to finish
            6. Publish another CV with different version of puppet module and
               promote it to capsule's LCE
            7. Wait for capsule synchronization to finish once more

        :expectedresults: Capsule was successfully synchronized, new version of
            puppet module is present on capsule

        :CaseLevel: System

        :CaseImportance: Medium
        """
        module_name = 'versioned'
        module_versions = ['2.2.2', '3.3.3']
        org = entities.Organization().create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        prod = entities.Product(organization=org).create()
        puppet_repository = entities.Repository(
            content_type=REPO_TYPE['puppet'], product=prod, url=CUSTOM_PUPPET_REPO
        ).create()
        capsule = entities.Capsule(id=self.capsule_id).read()
        capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(lce.id, [capsule_lce['id'] for capsule_lce in result['results']])
        puppet_repository.sync()
        puppet_module_old = entities.PuppetModule().search(
            query={'search': 'name={} and version={}'.format(module_name, module_versions[0])}
        )[0]
        # Add puppet module to the CV
        entities.ContentViewPuppetModule(
            content_view=content_view, id=puppet_module_old.id
        ).create()
        content_view = content_view.read()
        self.assertGreater(len(content_view.puppet_module), 0)
        # Publish and promote CVV
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        cvv = content_view.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Wait till capsule sync finishes
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']
        )
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        sync_status = capsule.content_get_sync()
        last_sync_time = sync_status['last_sync_time']
        # Unassign old puppet module version from CV
        entities.ContentViewPuppetModule(
            content_view=content_view, id=content_view.puppet_module[0].id
        ).delete()
        # Assign new puppet module version
        puppet_module_new = entities.PuppetModule().search(
            query={'search': 'name={} and version={}'.format(module_name, module_versions[1])}
        )[0]
        entities.ContentViewPuppetModule(
            content_view=content_view, id=puppet_module_new.id
        ).create()
        self.assertGreater(len(content_view.puppet_module), 0)
        # Publish and promote CVV
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 2)
        cvv = content_view.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Wait till capsule sync finishes
        sync_status = capsule.content_get_sync()
        if sync_status['active_sync_tasks']:
            for task in sync_status['active_sync_tasks']:
                entities.ForemanTask(id=task['id']).poll()
        else:
            self.assertNotEqual(sync_status['last_sync_time'], last_sync_time)
        stored_modules = get_repo_files(PULP_PUBLISHED_PUPPET_REPOS_PATH, 'gz', self.capsule_ip)
        with self.assertNotRaises(StopIteration):
            next(
                filename
                for filename in stored_modules
                if '{}-{}'.format(module_name, module_versions[1]) in filename
            )

    @tier4
    def test_positive_capsule_pub_url_accessible(self):
        """Ensure capsule pub url is accessible

        :id: 311eaa2a-146b-4d18-95db-4fbbe843d5b2

        :customerscenario: true

        :expectedresults: capsule pub url is accessible

        :BZ: 1463810

        :CaseLevel: System
        """
        https_pub_url = 'https://{0}/pub'.format(self.capsule_ip)
        http_pub_url = 'http://{0}/pub'.format(self.capsule_ip)
        for url in [http_pub_url, https_pub_url]:
            response = client.get(url, verify=False)
            self.assertEqual(response.status_code, 200)
            # check that one of the files is in the content
            self.assertIn(b'katello-server-ca.crt', response.content)
