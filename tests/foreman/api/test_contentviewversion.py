"""Unit tests for the ``content_view_versions`` paths."""
from nailgun import client, entities
from robottelo.common.constants import FAKE_1_YUM_REPO, ZOO_CUSTOM_GPG_KEY
from robottelo.common.helpers import get_server_credentials, read_data_file
from requests.exceptions import HTTPError
from robottelo.test import APITestCase


class CVVersionTestCase(APITestCase):
    """Tests for content view versions."""

    def test_negative_promote_1(self):
        """@Test: Promote the default content view version.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        env = entities.Environment().create()
        with self.assertRaises(HTTPError):
            entities.ContentViewVersion(id=1).promote(env.id)

    def test_negative_promote_2(self):
        """@Test: Promote a content view version using an invalid environment.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        with self.assertRaises(HTTPError):
            entities.ContentViewVersion(id=1).promote(-1)

    def test_delete_version(self):
        """@Test: Delete a content-view version associated to 'Library'

        @Assert: Deletion fails

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
        # Get 'Library' life-cycle environment id
        response = client.get(
            entities.LifecycleEnvironment().path(),
            auth=get_server_credentials(),
            data={u'organization_id': org.id},
            verify=False,
        )
        response.raise_for_status()
        lc_env_id = response.json()['results'][0]['id']
        # Delete the content-view version from selected env
        content_view.delete_from_environment(lc_env_id)
        # Delete the version
        content_view.version[0].delete()
