"""Test class for the content management tests.

@Requirement: Content Management

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.api.utils import promote
from robottelo.constants import FAKE_1_YUM_REPO, FAKE_1_YUM_REPO_RPMS
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    skip_if_not_set,
    tier4,
)
from robottelo.helpers import create_repo, form_repo_path
from robottelo.host_info import get_repo_rpms, get_repomd_revision
from robottelo.vm_capsule import CapsuleVirtualMachine
from robottelo.test import APITestCase


@run_in_one_thread
class ContentManagementTestCase(APITestCase):
    """Content Management related tests, which exercise katello with pulp
    interactions.
    """

    @classmethod
    @skip_if_not_set('capsule', 'clients', 'fake_manifest')
    def setUpClass(cls):
        """Create a separate capsule for tests"""
        super(ContentManagementTestCase, cls).setUpClass()
        cls.capsule_vm = CapsuleVirtualMachine()
        cls.capsule_vm.create()
        # for debugging purposes. you may replace these 2 variables with your
        # capsule values and comment lines above to speed up test execution
        cls.capsule_id = cls.capsule_vm.capsule['id']
        cls.capsule_hostname = cls.capsule_vm.hostname

    @classmethod
    def tearDownClass(cls):
        """Destroy the capsule"""
        cls.capsule_vm.destroy()
        super(ContentManagementTestCase, cls).tearDownClass()

    @tier4
    def test_positive_capsule_sync(self):
        """Create repository, add it to lifecycle environment, assign lifecycle
        environment with a capsule, sync repository, sync it once again, update
        repository (add 1 new package), sync repository once again.

        @id: 35513099-c918-4a8e-90d0-fd4c87ad2f82

        @BZ: 1388296

        @expectedresults:

        1. Repository sync triggers capsule sync
        2. After syncing capsule contains same repo content as satellite
        3. Syncing repository which has no changes for a second time does not
           trigger any new publish task
        4. Repository revision on capsule remains exactly the same after second
           repo sync with no changes
        5. Syncing repository which was updated will update the content on
           capsule

        """
        repo_name = gen_string('alphanumeric')
        # Create and publish custom repository with 2 packages in it
        repo_url = create_repo(
            FAKE_1_YUM_REPO,
            FAKE_1_YUM_REPO_RPMS[0:2],
            repo_name
        )
        # Create organization, product, repository in satellite, and lifecycle
        # environment
        org = entities.Organization(smart_proxy=[self.capsule_id]).create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(
            product=product,
            url=repo_url,
        ).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        # Associate the lifecycle environment with the capsule
        capsule = entities.Capsule(id=self.capsule_id).read()
        capsule.content_add_lifecycle_environment(data={
            'environment_id': lce.id,
        })
        result = capsule.content_lifecycle_environments()
        self.assertGreaterEqual(len(result['results']), 1)
        self.assertIn(
            lce.id, [capsule_lce['id'] for capsule_lce in result['results']])
        # Create a content view with the repository
        cv = entities.ContentView(
            organization=org,
            repository=[repo],
        ).create()
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
            len(sync_status['active_sync_tasks']) >= 1 or
            sync_status['last_sync_time']
        )
        # Assert that the content of the published content view in
        # lifecycle environment is exactly the same as content of
        # repository
        lce_repo_path = form_repo_path(
            org=org.label,
            lce=lce.label,
            cv=cv.label,
            prod=product.label,
            repo=repo.label,
        )
        cvv_repo_path = form_repo_path(
            org=org.label,
            cv=cv.label,
            cvv=cvv.version,
            prod=product.label,
            repo=repo.label,
        )
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        sync_status = capsule.content_get_sync()
        last_sync_time = sync_status['last_sync_time']

        # If BZ1439691 is open, need to sync repo once more, as repodata
        # will change on second attempt even with no changes in repo
        if bz_bug_is_open(1439691):
            repo.sync()
            repo = repo.read()
            cv.publish()
            cv = cv.read()
            self.assertEqual(len(cv.version), 2)
            cvv = cv.version[-1].read()
            promote(cvv, lce.id)
            cvv = cvv.read()
            self.assertEqual(len(cvv.environment), 2)
            sync_status = capsule.content_get_sync()
            self.assertTrue(
                len(sync_status['active_sync_tasks']) >= 1 or
                sync_status['last_sync_time'] != last_sync_time
            )
            for task in sync_status['active_sync_tasks']:
                entities.ForemanTask(id=task['id']).poll()
            sync_status = capsule.content_get_sync()
            last_sync_time = sync_status['last_sync_time']

        # Assert that the content published on the capsule is exactly the
        # same as in repository on satellite
        lce_revision_capsule = get_repomd_revision(
            lce_repo_path, hostname=self.capsule_hostname)
        self.assertEqual(
            get_repo_rpms(lce_repo_path, hostname=self.capsule_hostname),
            get_repo_rpms(cvv_repo_path)
        )
        # Sync repository for a second time
        result = repo.sync()
        # Assert that the task summary contains a message that says the
        # publish was skipped because content had not changed
        self.assertEqual(result['result'], 'success')
        self.assertTrue(result['output']['post_sync_skipped'])
        self.assertEqual(
            result['humanized']['output'],
            'No new packages.'
        )
        # Publish a new version of content view
        cv.publish()
        cv = cv.read()
        cvv = cv.version[-1].read()
        # Promote new content view version to lifecycle environment
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Wait till capsule sync finishes
        sync_status = capsule.content_get_sync()
        tasks = []
        if not sync_status['active_sync_tasks']:
            self.assertNotEqual(
                sync_status['last_sync_time'], last_sync_time)
        else:
            for task in sync_status['active_sync_tasks']:
                tasks.append(entities.ForemanTask(id=task['id']))
                tasks[-1].poll()
        # Assert that the value of repomd revision of repository in
        # lifecycle environment on the capsule has not changed
        new_lce_revision_capsule = get_repomd_revision(
            lce_repo_path, hostname=self.capsule_hostname)
        self.assertEqual(lce_revision_capsule, new_lce_revision_capsule)
        # Update a repository with 1 new rpm
        create_repo(
            FAKE_1_YUM_REPO,
            FAKE_1_YUM_REPO_RPMS[-1:],
            repo_name
        )
        # Sync, publish and promote the repository
        repo.sync()
        repo = repo.read()
        cv.publish()
        cv = cv.read()
        cvv = cv.version[-1].read()
        promote(cvv, lce.id)
        cvv = cvv.read()
        self.assertEqual(len(cvv.environment), 2)
        # Assert that a task to sync lifecycle environment to the capsule
        # is started (or finished already)
        sync_status = capsule.content_get_sync()
        self.assertTrue(
            len(sync_status['active_sync_tasks']) >= 1 or
            sync_status['last_sync_time'] != last_sync_time
        )
        # Assert that packages count in the repository is updated
        self.assertEqual(repo.content_counts['package'], 3)
        # Assert that the content of the published content view in
        # lifecycle environment is exactly the same as content of the
        # repository
        cvv_repo_path = form_repo_path(
            org=org.label,
            cv=cv.label,
            cvv=cvv.version,
            prod=product.label,
            repo=repo.label,
        )
        self.assertEqual(
            repo.content_counts['package'],
            cvv.package_count,
        )
        self.assertEqual(
            get_repo_rpms(lce_repo_path),
            get_repo_rpms(cvv_repo_path)
        )
        # Wait till capsule sync finishes
        for task in sync_status['active_sync_tasks']:
            entities.ForemanTask(id=task['id']).poll()
        # Assert that the content published on the capsule is exactly the
        # same as in the repository
        self.assertEqual(
            get_repo_rpms(lce_repo_path, hostname=self.capsule_hostname),
            get_repo_rpms(cvv_repo_path)
        )
