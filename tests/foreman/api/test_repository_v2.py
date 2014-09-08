"""Unit tests for the ``repositories`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/repositories.html

"""
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.constants import (VALID_GPG_KEY_FILE,
                                        VALID_GPG_KEY_BETA_FILE,
                                        FAKE_PUPPET_REPO, FAKE_1_YUM_REPO,
                                        FAKE_2_YUM_REPO, RPM_TO_UPLOAD)
from robottelo.common.helpers import (get_server_credentials, read_data_file,
                                      get_data_file)
from robottelo import entities, orm
from unittest import TestCase
import copy
import ddt
import httplib
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class RepositoriesTestCase(TestCase):
    """Tests for ``katello/api/v2/repositories``."""

    @ddt.data(
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_create_1(self, name):
        """@Test: Create a repository

        @Feature: Repositories

        @Assert: 'Yum' Repository is created with specified name

        """

        # Creates new repository
        repository_attrs = entities.Repository(
            name=name,
            url=FAKE_1_YUM_REPO,
        ).create()

        response = entities.Repository(id=repository_attrs['id']).read_json()

        self.assertEqual(response['name'], name)
        self.assertEqual(response['content_type'], "yum")

    @ddt.data(
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_create_2(self, name):
        """@Test: Create a repository with gpg_key

        @Feature: Repositories

        @Assert: Repository is created with gpg-key

        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)

        # Create an organization, gpg_key, product and repository
        org_attrs = entities.Organization().create()

        gpgkey_attrs = entities.GPGKey(
            content=key_content,
            organization=org_attrs['id']
        ).create()

        product_attrs = entities.Product(
            organization=org_attrs['id']
        ).create()
        # Creates new repository with GPGKey
        repository_attrs = entities.Repository(
            name=name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create()
        # Get the repository and verify it's name.
        response = entities.Repository(id=repository_attrs['id']).read_json()
        self.assertEqual(response['name'], name)
        self.assertEqual(response['gpg_key_id'], gpgkey_attrs['id'])

    def test_positive_create_3(self):
        """@Test: Create a repository with same name
        in two different organizations

        @Feature: Repositories

        @Assert: Repository is created

        """
        repository_name = orm.StringField(str_type=('alpha',)).get_value()

        # Creates new repository
        repository_attrs = entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
        ).create()

        # Get the repository and verify it's name.
        response = entities.Repository(id=repository_attrs['id']).read_json()
        self.assertEqual(response['name'], repository_name)

        # Create repository with same name in another organization
        repository_2_attrs = entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
        ).create()

        # Get the repository and verify it's name.
        response = entities.Repository(id=repository_2_attrs['id']).read_json()
        self.assertEqual(response['name'], repository_name)

    def test_positive_create_4(self):
        """@Test: Create a repository of content-type: 'Puppet'

        @Feature: Repositories

        @Assert: 'Puppet' repository is created with specified name

        """

        repository_name = orm.StringField(str_type=('alpha',)).get_value()

        repository_attrs = entities.Repository(
            name=repository_name,
            url=FAKE_PUPPET_REPO,
            content_type="puppet",
        ).create()
        # Get the repository attributes and verify it's name.
        response = entities.Repository(id=repository_attrs['id']).read_json()
        self.assertEqual(response['name'], repository_name)
        self.assertEqual(response['content_type'], "puppet")

    @ddt.data(
        {u'name': orm.StringField(str_type=('alphanumeric',)).get_value(),
         u'new_name': orm.StringField(str_type=('alphanumeric',)).get_value()},
        {u'name': orm.StringField(str_type=('numeric',)).get_value(),
         u'new_name': orm.StringField(str_type=('numeric',)).get_value()},
        {u'name': orm.StringField(str_type=('alpha',)).get_value(),
         u'new_name': orm.StringField(str_type=('alpha',)).get_value()}
    )
    def test_positive_update_1(self, test_data):
        """@Test: Create a repository and update its name

        @Feature: Repositories

        @Assert: Repository name is updated

        """

        # Creates new repository
        repository_attrs = entities.Repository(
            name=test_data['name'],
            url=FAKE_1_YUM_REPO,
        ).create()

        path = entities.Repository(id=repository_attrs['id']).path()

        repository_copy = copy.deepcopy(repository_attrs)
        repository_copy['name'] = test_data['new_name']

        response = client.put(
            path,
            repository_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )
        # Fetch the updated repository
        updated_attrs = entities.Repository(
            id=repository_attrs['id']
        ).read_json()
        # Assert that name is updated
        self.assertNotEqual(
            updated_attrs['name'],
            repository_attrs['name'],
        )

    def test_positive_update_2(self):
        """@Test: Create a repository and update its URL

        @Feature: Repositories

        @Assert: Repository URL is updated

        """

        # Creates new repository
        repository_attrs = entities.Repository(
            url=FAKE_1_YUM_REPO,
        ).create()

        path = entities.Repository(id=repository_attrs['id']).path()

        repository_copy = copy.deepcopy(repository_attrs)
        repository_copy['url'] = FAKE_2_YUM_REPO

        response = client.put(
            path,
            repository_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )
        # Fetch the updated repository
        updated_attrs = entities.Repository(
            id=repository_attrs['id']
        ).read_json()
        # Assert that URL is updated
        self.assertNotEqual(
            updated_attrs['url'],
            repository_attrs['url'],
        )
        self.assertEqual(
            updated_attrs['url'],
            FAKE_2_YUM_REPO,
        )

    def test_positive_update_3(self):
        """@Test: Create a repository and update its GPGKey

        @Feature: Repositories

        @Assert: Repository is updated with new GPGkey

        """
        key_1_content = read_data_file(VALID_GPG_KEY_FILE)
        key_2_content = read_data_file(VALID_GPG_KEY_BETA_FILE)

        # Create an organization and product
        org_attrs = entities.Organization().create()
        product_attrs = entities.Product(
            organization=org_attrs['id']
        ).create()

        gpgkey_1_attrs = entities.GPGKey(
            content=key_1_content,
            organization=org_attrs['id']
        ).create()

        gpgkey_2_attrs = entities.GPGKey(
            content=key_2_content,
            organization=org_attrs['id']
        ).create()

        # Creates new repository
        repository_attrs = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_1_attrs['id'],
        ).create()

        path = entities.Repository(id=repository_attrs['id']).path()

        repository_copy = copy.deepcopy(repository_attrs)
        repository_copy['gpg_key_id'] = gpgkey_2_attrs['id']

        response = client.put(
            path,
            repository_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )
        # Fetch the updated repository
        updated_attrs = entities.Repository(
            id=repository_attrs['id']
        ).read_json()
        # Assert that key is updated
        self.assertEqual(
            updated_attrs['gpg_key_id'],
            gpgkey_2_attrs['id'],
        )

    def test_positive_update_4(self):
        """@Test: Create a repository and update to publish it via HTTP

        @Feature: Repositories

        @Assert: Repository is updated with unprotected flag 'True'

        """

        repository_attrs = entities.Repository(
            url=FAKE_1_YUM_REPO,
        ).create()

        path = entities.Repository(id=repository_attrs['id']).path()

        repository_copy = copy.deepcopy(repository_attrs)
        repository_copy['unprotected'] = True

        response = client.put(
            path,
            repository_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )
        # Fetch the updated repository
        updated_attrs = entities.Repository(
            id=repository_attrs['id']
        ).read_json()

        # Assert that unprotected flag is updated
        self.assertEqual(
            updated_attrs['unprotected'],
            True,
        )

    def test_positive_update_5(self):
        """@Test: Create a repository and upload rpm contents

        @Feature: Repositories

        @Assert: Repository is updated with contents

        """
        # Create a repository and upload an RPM file.
        attrs = entities.Repository(url=FAKE_1_YUM_REPO).create()
        response = client._call_requests_post(  # FIXME: use `client.post`
            entities.Repository(id=attrs['id']).path(which='upload_content'),
            {},
            auth=get_server_credentials(),
            files={u'content': open(get_data_file(RPM_TO_UPLOAD), 'rb')},
            verify=False,
        )
        response.raise_for_status()

        # Fetch info about the updated repo and verify the file was uploaded.
        attrs = entities.Repository(id=attrs['id']).read_json()
        self.assertEqual(attrs[u'content_counts'][u'rpm'], 1)
