"""Unit tests for the ``content_view_versions`` paths.

@Requirement: Contentviewversion

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.api.utils import promote
from robottelo.constants import (
    DEFAULT_CV,
    FAKE_1_YUM_REPO,
    PUPPET_MODULE_NTP_PUPPETLABS,
    ZOO_CUSTOM_GPG_KEY,
)
from robottelo.decorators import tier2
from robottelo.helpers import get_data_file, read_data_file
from robottelo.test import APITestCase


class ContentViewVersionCreateTestCase(APITestCase):
    """Tests for content view version creation."""

    @classmethod
    def setUpClass(cls):
        """Single organization for all tests"""
        super(ContentViewVersionCreateTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    def setUp(self):
        """Init content view with repo per each test"""
        super(ContentViewVersionCreateTestCase, self).setUp()
        self.content_view = entities.ContentView(
            organization=self.org,
        ).create()

    @tier2
    def test_positive_create(self):
        """Create a content view version.

        @id: 627c84b3-e3f1-416c-a09b-5d2200d6429f

        @Assert: Content View Version is created.

        @CaseLevel: Integration
        """
        # Fetch content view for latest information
        cv = self.content_view.read()
        # No versions should be available yet
        self.assertEqual(len(cv.version), 0)

        # Publish existing content view
        cv.publish()
        # Fetch it again
        cv = cv.read()
        self.assertGreater(len(cv.version), 0)

    @tier2
    def test_negative_create(self):
        """Create content view version using the 'Default Content View'.

        @id: 0afd49c6-f3a4-403e-9929-849f51ffa922

        @Assert: Content View Version is not created

        @CaseLevel: Integration
        """
        # The default content view cannot be published
        cv = entities.ContentView(
            organization=self.org,
            name=DEFAULT_CV
        ).search()
        # There should be only 1 record returned
        self.assertEqual(len(cv), 1)
        with self.assertRaises(HTTPError):
            cv[0].publish()


class ContentViewVersionPromoteTestCase(APITestCase):
    """Tests for content view version promotion."""

    @classmethod
    def setUpClass(cls):
        """Create some entities for all tests."""
        super(ContentViewVersionPromoteTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.lce1 = entities.LifecycleEnvironment(organization=cls.org).create()
        cls.lce2 = entities.LifecycleEnvironment(
            organization=cls.org,
            prior=cls.lce1
        ).create()
        default_cv = entities.ContentView(
            organization=cls.org,
            name=DEFAULT_CV
        ).search()
        # There should be only 1 record returned
        assert len(default_cv) == 1
        # There should be only 1 version
        assert len(default_cv[0].version) == 1
        cls.default_cv = default_cv[0].version[0].read()

    @tier2
    def test_positive_promote_valid_environment(self):
        """Promote a content view version to 'next in sequence'
        lifecycle environment.

        @id: f205ca06-8ab5-4546-83bd-deac4363d487

        @Assert: Promotion succeeds.

        @CaseLevel: Integration
        """
        # Create a new content view...
        cv = entities.ContentView(organization=self.org).create()
        # ... and promote it.
        cv.publish()
        # Refresh the entity
        cv = cv.read()
        # Check that we have a new version
        self.assertEqual(len(cv.version), 1)
        version = cv.version[0].read()
        # Assert that content view version is found in 1 lifecycle
        # environments (i.e. 'Library')
        self.assertEqual(len(version.environment), 1)
        # Promote it to the next 'in sequence' lifecycle environment
        promote(version, self.lce1.id)
        # Assert that content view version is found in 2 lifecycle
        # environments.
        version = version.read()
        self.assertEqual(len(version.environment), 2)

    @tier2
    def test_positive_promote_out_of_sequence_environment(self):
        """Promote a content view version to a lifecycle environment
        that is 'out of sequence'.

        @id: e88405de-843d-4279-9d81-cedaab7c23cf

        @Assert: The promotion succeeds.

        @CaseLevel: Integration
        """
        # Create a new content view...
        cv = entities.ContentView(organization=self.org).create()
        # ... and publish it.
        cv.publish()
        # Refresh the entity
        cv = cv.read()
        # Check that we have a new version
        self.assertEqual(len(cv.version), 1)
        version = cv.version[0].read()
        # The immediate lifecycle is lce1, not lce2
        promote(version, self.lce2.id, force=True)
        # Assert that content view version is found in 2 lifecycle
        # environments.
        version = version.read()
        self.assertEqual(len(version.environment), 2)

    @tier2
    def test_negative_promote_valid_environment(self):
        """Promote the default content view version.

        @id: cd4f3c3d-93c5-425f-bc3b-d1ac17696a4a

        @Assert: The promotion fails.

        @CaseLevel: Integration
        """
        with self.assertRaises(HTTPError):
            promote(self.default_cv, self.lce1.id)

    @tier2
    def test_negative_promote_out_of_sequence_environment(self):
        """Promote a content view version to a lifecycle environment
        that is 'out of sequence'.

        @id: 621d1bb6-92c6-4209-8369-6ea14a4c8a01

        @Assert: The promotion fails.

        @CaseLevel: Integration
        """
        # Create a new content view...
        cv = entities.ContentView(organization=self.org).create()
        # ... and publish it.
        cv.publish()
        # Refresh the entity
        cv = cv.read()
        # Check that we have a new version
        self.assertEqual(len(cv.version), 1)
        version = cv.version[0].read()
        # The immediate lifecycle is lce1, not lce2
        with self.assertRaises(HTTPError):
            promote(version, self.lce2.id)


class ContentViewVersionDeleteTestCase(APITestCase):
    """Tests for content view version promotion."""

    @tier2
    def test_positive_delete(self):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'delete_from_environment' command and delete content view version from
        that content view. Add repository and gpg key to initial content view
        for better coverage

        @id: 066dec47-c942-4c01-8956-359c8b23a6d4

        @Assert: Content version deleted successfully

        @CaseLevel: Integration
        """
        key_content = read_data_file(ZOO_CUSTOM_GPG_KEY)
        org = entities.Organization().create()
        gpgkey = entities.GPGKey(
            content=key_content,
            organization=org,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(organization=org).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            gpg_key=gpgkey,
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # sync repository
        repo.sync()
        # Create content view
        content_view = entities.ContentView(organization=org).create()
        # Associate repository to new content view
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        # Get published content-view version id
        self.assertEqual(len(content_view.version), 1)
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 1)
        # Delete the content-view version from selected env
        content_view.delete_from_environment(cvv.environment[0].id)
        # Delete the version
        content_view.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(content_view.read().version), 0)

    @tier2
    def test_positive_delete_non_default(self):
        """Create content view and publish and promote it to new
        environment. After that try to disassociate content view from 'Library'
        and one more non-default environments through 'delete_from_environment'
        command and delete content view version from that content view.

        @id: 95bb973c-ebec-4a72-a1b6-ad28b66bd11b

        @Assert: Content view version deleted successfully

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.version[0].read().environment), 1)
        lce = entities.LifecycleEnvironment(organization=org).create()
        promote(content_view.version[0], lce.id)
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 2)
        # Delete the content-view version from selected environments
        for env in reversed(cvv.environment):
            content_view.delete_from_environment(env.id)
        content_view.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(content_view.read().version), 0)

    @tier2
    def test_negative_delete(self):
        """Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        @id: 21c35aae-2f9c-4679-b3ba-7cd9182bd880

        @Assert: Content view version is not deleted

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        with self.assertRaises(HTTPError):
            content_view.version[0].delete()
        # Make sure that content view version is still present
        self.assertEqual(len(content_view.read().version), 1)


class ContentViewVersionIncrementalTestCase(APITestCase):
    """Tests for content view version promotion."""

    @tier2
    def test_positive_incremental_update_puppet(self):
        """Incrementally update a CVV with a puppet module.

        @id: 19b2fe3b-6c91-4713-9910-17517fba661f

        @Assert: The incremental update succeeds with no errors, and the
        content view is given an additional version.

        @CaseLevel: Integration
        """
        # Create a content view and add a yum repository to it. Publish the CV.
        product = entities.Product().create()
        yum_repo = entities.Repository(
            content_type='yum',
            product=product,
        ).create()
        content_view = entities.ContentView(
            organization=product.organization,
            repository=[yum_repo],
        ).create()
        content_view.publish()
        content_view = content_view.read()

        # Create a puppet repository and upload a puppet module into it.
        puppet_repo = entities.Repository(
            content_type='puppet',
            product=product,
        ).create()
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            puppet_repo.upload_content(files={'content': handle})
        # Extract all the available puppet modules.
        puppet_modules = content_view.available_puppet_modules()['results']
        # Make sure that we have results. Uploading content does not
        # seem to create a task so we cannot pool it for status. We
        # should then check that we have some results back before
        # proceeding.
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = entities.PuppetModule(
            id=puppet_modules[0]['id']
        )

        # Incrementally update the CVV with the puppet module.
        payload = {
            'content_view_version_environments': [{
                'content_view_version_id': content_view.version[0].id,
                'environment_ids': [
                    environment.id
                    for environment
                    in content_view.version[0].read().environment
                ],
            }],
            'add_content': {'puppet_module_ids': [puppet_module.id]},
        }
        content_view.version[0].incremental_update(data=payload)
        content_view = content_view.read()

        # The CV now has two versions. The first version has no puppet modules,
        # and the second version has one puppet module. Let's verify this.
        # NOTE: The `read_json` lines should be refactored after the 'minor'
        # attribute is added to the ContentViewVersion entity class.
        self.assertEqual(len(content_view.version), 2)
        for i in range(len(content_view.version)):
            content_view.version[i] = content_view.version[i].read()
        content_view.version.sort(key=lambda cvv: cvv.read_json()['minor'])
        self.assertEqual(len(content_view.version[0].puppet_module), 0)
        self.assertEqual(len(content_view.version[1].puppet_module), 1)
        self.assertEqual(
            content_view.version[1].puppet_module[0].id,
            puppet_module.id,
        )
