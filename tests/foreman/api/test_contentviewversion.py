"""Unit tests for the ``content_view_versions`` paths."""
from nailgun import client, entities
from robottelo.common.constants import FAKE_1_YUM_REPO, ZOO_CUSTOM_GPG_KEY
from robottelo.common.helpers import get_server_credentials, read_data_file
from requests.exceptions import HTTPError
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


class CVVersionTestCase(APITestCase):
    """Tests for content view versions."""

    def test_negative_promote_1(self):
        """@Test: Promote the default content view version.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        env_id = entities.Environment().create_json()['id']
        with self.assertRaises(HTTPError):
            entities.ContentViewVersion(id=1).promote(env_id)

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
        org_id = entities.Organization().create_json()['id']
        gpgkey_id = entities.GPGKey(
            content=key_content,
            organization=org_id
        ).create_json()['id']
        # Creates new product without selecting GPGkey
        product_id = entities.Product(
            organization=org_id
        ).create_json()['id']
        # Creates new repository with GPGKey
        repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=product_id,
            gpg_key=gpgkey_id,
        ).create()
        # sync repository
        repo.sync()
        # Create content view
        content_view = entities.ContentView(
            organization=org_id
        ).create()
        # Associate repository to new content view
        client.put(
            content_view.path(),
            {u'repository_ids': [repo.id]},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        # Publish content view
        content_view.publish()
        # Get published content-view version id
        cv = entities.ContentView(id=content_view.id).read_json()
        self.assertEqual(len(cv['versions']), 1)
        cv_version_id = cv['versions'][0]['id']
        # Get 'Library' life-cycle environment id
        response = client.get(
            entities.LifecycleEnvironment().path(),
            auth=get_server_credentials(),
            data={u'organization_id': org_id},
            verify=False,
        )
        response.raise_for_status()
        lc_env_id = response.json()['results'][0]['id']
        # Delete the content-view version from selected env
        entities.ContentView(
            id=content_view.id
        ).delete_from_environment(lc_env_id)
        # Delete the version
        entities.ContentViewVersion(id=cv_version_id).delete()
