"""Unit tests for the ``content_view_versions`` paths."""
from nailgun import entities
from robottelo.common.constants import FAKE_1_YUM_REPO, ZOO_CUSTOM_GPG_KEY
from robottelo.common.helpers import read_data_file
from requests.exceptions import HTTPError
from robottelo.test import APITestCase


class CVVersionTestCase(APITestCase):
    """Tests for content view versions."""

    def test_negative_promote_1(self):
        """@Test: Promote the default content view version.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        env = entities.Environment().create().id
        with self.assertRaises(HTTPError):
            entities.ContentViewVersion(id=1).promote(data={
                u'environment_id': env
            })

    def test_negative_promote_2(self):
        """@Test: Promote a content view version using an invalid environment.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        with self.assertRaises(HTTPError):
            entities.ContentViewVersion(id=1).promote(data={
                u'environment_id': -1
            })

    def test_delete_version(self):
        """@Test: Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'delete_from_environment' command and delete content view version from
        that content view. Add repository and gpg key to initial content view
        for better coverage

        @Assert: Content version deleted successfully

        @Feature: ContentViewVersion

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

    def test_delete_version_non_default(self):
        """@Test: Create content view and publish and promote it to new
        environment. After that try to disassociate content view from 'Library'
        and one more non-default environments through 'delete_from_environment'
        command and delete content view version from that content view.

        @Assert: Content view version deleted successfully

        @Feature: ContentViewVersion

        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.version[0].read().environment), 1)
        lce = entities.LifecycleEnvironment(organization=org).create()
        content_view.version[0].promote(data={u'environment_id': lce.id})
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 2)
        # Delete the content-view version from selected environments
        for env in reversed(cvv.environment):
            content_view.delete_from_environment(env.id)
        content_view.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(content_view.read().version), 0)

    def test_delete_version_negative(self):
        """@Test: Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        @Assert: Content view version is not deleted

        @Feature: ContentViewVersion

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
