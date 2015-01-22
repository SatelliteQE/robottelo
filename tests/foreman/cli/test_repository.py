# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Repository CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import (
    make_gpg_key,
    make_org,
    make_product,
    make_repository,
    CLIFactoryError
)
from robottelo.cli.repository import Repository
from robottelo.common.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_0_YUM_REPO,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    FAKE_3_YUM_REPO,
    FAKE_4_YUM_REPO,
    FAKE_1_PUPPET_REPO,
    FAKE_2_PUPPET_REPO,
    FAKE_3_PUPPET_REPO,
    FAKE_4_PUPPET_REPO,
    FAKE_5_PUPPET_REPO,
)
from robottelo.common.decorators import (
    data,
    run_only_on,
    skip_if_bug_open,
    stubbed,
)
from robottelo.test import CLITestCase
from robottelo.common import ssh
from robottelo.common.constants import RPM_TO_UPLOAD
from robottelo.common.helpers import get_data_file


@ddt
class TestRepository(CLITestCase):
    """Repository CLI tests."""

    org = None
    product = None

    def setUp(self):
        """Tests for Repositiry via Hammer CLI"""

        super(TestRepository, self).setUp()

        if TestRepository.org is None:
            TestRepository.org = make_org(cached=True)
        if TestRepository.product is None:
            TestRepository.product = make_product(
                {u'organization-id': TestRepository.org['id']},
                cached=True)

    def _make_repository(self, options=None):
        """Makes a new repository and asserts its success"""
        if options is None:
            options = {}

        if options.get('product-id') is None:
            options[u'product-id'] = self.product['id']

        return make_repository(options)

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_positive_create_1(self, name):
        """@Test: Check if repository can be created with random names

        @Feature: Repository

        @Assert: Repository is created and has random name

        """

        new_repo = self._make_repository({u'name': name})
        # Assert that name matches data passed
        self.assertEqual(new_repo['name'], name, "Names don't match")

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_positive_create_2(self, name):
        """@Test: Check if repository can be created with random names and labels

        @Feature: Repository

        @Assert: Repository is created and has random name and labels

        """

        # Generate a random, 'safe' label
        label = gen_string('alpha', 20)

        new_repo = self._make_repository({
            u'name': name,
            u'label': label,
        })
        # Assert that name matches data passed
        self.assertEqual(new_repo['name'], name, "Names don't match")
        self.assertNotEqual(
            new_repo['name'],
            new_repo['label'],
            "Label should not match the repository name"
        )

    @run_only_on('sat')
    @data(
        {u'url': FAKE_3_YUM_REPO, u'content-type': u'yum'},
        {u'url': FAKE_4_YUM_REPO, u'content-type': u'yum'},
        {u'url': FAKE_0_YUM_REPO, u'content-type': u'yum'},
        {u'url': FAKE_2_YUM_REPO, u'content-type': u'yum'},
        {u'url': FAKE_1_YUM_REPO, u'content-type': u'yum'},
    )
    def test_positive_create_3(self, test_data):
        """@Test: Create YUM repository

        @Feature: Repository

        @Assert: YUM repository is created

        """

        new_repo = self._make_repository({
            u'url': test_data['url'],
            u'content-type': test_data['content-type'],
        })
        # Assert that urls and content types matches data passed
        self.assertEqual(
            new_repo['url'], test_data['url'], "Urls don't match")
        self.assertEqual(
            new_repo['content-type'],
            test_data['content-type'],
            "Content Types don't match"
        )

    @run_only_on('sat')
    @data(
        {u'url': FAKE_1_PUPPET_REPO, u'content-type': u'puppet'},
        {u'url': FAKE_2_PUPPET_REPO, u'content-type': u'puppet'},
        {u'url': FAKE_3_PUPPET_REPO, u'content-type': u'puppet'},
        {u'url': FAKE_4_PUPPET_REPO, u'content-type': u'puppet'},
        {u'url': FAKE_5_PUPPET_REPO, u'content-type': u'puppet'},
    )
    def test_positive_create_4(self, test_data):
        """@Test: Create Puppet repository

        @Feature: Repository

        @Assert: Puppet repository is created

        """

        new_repo = self._make_repository({
            u'url': test_data['url'],
            u'content-type': test_data['content-type'],
        })
        # Assert that urls and content types matches data passed
        self.assertEqual(
            new_repo['url'], test_data['url'], "Urls don't match")
        self.assertEqual(
            new_repo['content-type'],
            test_data['content-type'],
            "Content Types don't match"
        )

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_positive_create_5(self, name):
        """@Test: Check if repository can be created with gpg key ID

        @Feature: Repository

        @Assert: Repository is created and has gpg key

        """
        # Make a new gpg key
        new_gpg_key = make_gpg_key({'organization-id': self.org['id']})

        new_repo = self._make_repository({
            u'name': name,
            u'gpg-key-id': new_gpg_key['id'],
        })

        # Fetch it again
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that data matches data passed
        self.assertEqual(
            result.stdout['gpg-key']['id'],
            new_gpg_key['id'],
            "GPG Keys ID don't match"
        )
        self.assertEqual(
            result.stdout['gpg-key']['name'],
            new_gpg_key['name'],
            "GPG Keys name don't match"
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1103944)
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_positive_create_6(self, name):
        """@Test: Check if repository can be created with gpg key name

        @Feature: Repository

        @Assert: Repository is created and has gpg key

        @BZ: 1103944

        """

        # Make a new gpg key
        new_gpg_key = make_gpg_key({'organization-id': self.org['id']})

        new_repo = self._make_repository({
            u'name': name,
            u'gpg-key': new_gpg_key['name'],
        })

        # Fetch it again
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that data matches data passed
        self.assertEqual(
            result.stdout['gpg-key']['id'],
            new_gpg_key['id'],
            "GPG Keys ID don't match"
        )
        self.assertEqual(
            result.stdout['gpg-key']['name'],
            new_gpg_key['name'],
            "GPG Keys name don't match"
        )

    @run_only_on('sat')
    @data(u'true', u'yes', u'1')
    def test_positive_create_7(self, test_data):
        """@Test: Create repository published via http

        @Feature: Repository

        @Assert: Repository is created and is published via http

        """

        new_repo = self._make_repository({'publish-via-http': test_data})

        # Fetch it again
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        self.assertEqual(
            result.stdout['publish-via-http'],
            u'yes',
            "Publishing methods don't match"
        )

    @run_only_on('sat')
    @data(u'false', u'no', u'0')
    def test_positive_create_8(self, use_http):
        """@Test: Create repository not published via http

        @Feature: Repository

        @Assert: Repository is created and is not published via http

        """

        new_repo = self._make_repository({'publish-via-http': use_http})

        # Fetch it again
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        self.assertEqual(
            result.stdout['publish-via-http'],
            u'no',
            "Publishing methods don't match"
        )

    @run_only_on('sat')
    def test_positive_create_9(self):
        """@Test: Create a Docker repository

        @Feature: Repository

        @Assert: Docker repository is created and contains correct values.

        """
        content_type = u'docker'
        new_repo = self._make_repository({
            u'name': u'busybox',
            u'url': DOCKER_REGISTRY_HUB,
            u'content-type': content_type,
        })
        # Assert that urls and content types matches data passed
        self.assertEqual(
            new_repo['url'],
            DOCKER_REGISTRY_HUB,
            "Expected URL {0} but received {1}".format(
                DOCKER_REGISTRY_HUB, new_repo['url'])
        )
        self.assertEqual(
            new_repo['content-type'],
            content_type,
            "Expected content type {0} but received {1}".format(
                content_type, new_repo['content-type'])
        )

    @skip_if_bug_open('bugzilla', 1155237)
    @run_only_on('sat')
    @data(
        u'sha1',
        u'sha256',
    )
    def test_positive_create_10(self, checksum_type):
        """@Test: Create a YUM repository with a checksum type

        @Feature: Repository

        @Assert: A YUM repository is created and contains the correct checksum
        type

        @BZ: 1155237

        """
        content_type = u'yum'
        repository = self._make_repository({
            u'content-type': content_type,
            u'checksum-type': checksum_type,
        })
        self.assertEqual(repository['content-type'], content_type)
        self.assertEqual(repository['checksum-type'], checksum_type)

    @run_only_on('sat')
    @data(
        gen_string('alpha', 300),
        gen_string('alphanumeric', 300),
        gen_string('numeric', 300),
        gen_string('latin1', 300),
        gen_string('utf8', 300),
        gen_string('html', 300),
    )
    def test_negative_create_1(self, name):
        """@Test: Repository name cannot be 300-characters long

        @Feature: Repository

        @Assert: Repository cannot be created

        """

        with self.assertRaises(Exception):
            self._make_repository({u'name': name})

    @run_only_on('sat')
    @data(
        {u'url': FAKE_3_YUM_REPO, u'content-type': u'yum'},
        {u'url': FAKE_4_YUM_REPO, u'content-type': u'yum'},
        {u'url': FAKE_1_YUM_REPO, u'content-type': u'yum'},
    )
    @skip_if_bug_open('bugzilla', 1152237)
    def test_positive_synchronize_1(self, test_data):
        """@Test: Check if repository can be created and synced

        @Feature: Repository

        @Assert: Repository is created and synced

        """

        new_repo = self._make_repository({
            u'url': test_data['url'],
            u'content-type': test_data['content-type'],
        })
        # Assertion that repo is not yet synced
        self.assertEqual(
            new_repo['sync']['status'],
            'Not Synced',
            "The status of repository should be 'Not Synced'")

        # Synchronize it
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not synchronized")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Verify it has finished
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            result.stdout['sync']['status'],
            'Finished',
            "The new status of repository should be 'Finished'")

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1152237)
    def test_positive_synchronize_2(self):
        """@Test: Check if Docker repository can be created and synced

        @Feature: Repository

        @Assert: Docker repository is created and synced

        """

        new_repo = self._make_repository({
            u'name': u'busybox',
            u'url': DOCKER_REGISTRY_HUB,
            u'content-type': u'docker',
        })
        # Assertion that repo is not yet synced
        self.assertEqual(new_repo['sync']['status'], 'Not Synced')

        # Synchronize it
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Verify it has finished
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result.stdout['sync']['status'], 'Finished')

    @run_only_on('sat')
    @data(
        FAKE_4_YUM_REPO,
        FAKE_1_PUPPET_REPO,
        FAKE_2_PUPPET_REPO,
        FAKE_3_PUPPET_REPO,
        FAKE_2_YUM_REPO,
    )
    def test_positive_update_1(self, url):
        """@Test: Update the original url for a repository

        @Feature: Repository

        @Assert: Repository url is updated

        """

        new_repo = self._make_repository()

        # Update the url
        result = Repository.update({
            u'id': new_repo['id'],
            u'url': url,
        })
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it again
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertNotEqual(
            result.stdout['url'],
            new_repo['url'],
            "Urls should not match"
        )
        self.assertEqual(
            result.stdout['url'],
            url,
            "Urls don't match"
        )

    @run_only_on('sat')
    @stubbed
    def test_positive_update_2(self, test_data):
        """@Test: Update the original gpg key

        @Feature: Repository

        @Assert: Repository gpg key is updated

        @Status: manual

        """

    @run_only_on('sat')
    @stubbed
    def test_positive_update_3(self, test_data):
        """@Test: Update the original publishing method

        @Feature: Repository

        @Assert: Repository publishing method is updated

        @Status: manual

        """

    @skip_if_bug_open('bugzilla', 1155237)
    @run_only_on('sat')
    @data(
        u'sha1',
        u'sha256',
    )
    def test_positive_update_4(self, checksum_type):
        """@Test: Create a YUM repository and update the checksum type

        @Feature: Repository

        @Assert: A YUM repository is updated and contains the correct checksum
        type

        @BZ: 1155237

        """
        content_type = u'yum'
        repository = self._make_repository({
            u'content-type': content_type,
        })

        self.assertEqual(repository['content-type'], content_type)
        self.assertEqual(repository['checksum-type'], '')

        # Update the url
        result = Repository.update({
            u'id': repository['id'],
            u'checksum-type': checksum_type,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it again
        result = Repository.info({'id': repository['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertNotEqual(
            result.stdout['checksum-type'],
            repository['checksum-type'],
        )
        self.assertEqual(
            result.stdout['checksum-type'],
            checksum_type,
        )

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_positive_delete_1(self, name):
        """@Test: Check if repository can be created and deleted

        @Feature: Repository

        @Assert: Repository is created and then deleted

        """

        new_repo = self._make_repository({u'name': name})
        # Assert that name matches data passed
        self.assertEqual(new_repo['name'], name, "Names don't match")

        # Delete it
        result = Repository.delete({u'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = Repository.info({
            u'id': new_repo['id'],
        })
        self.assertNotEqual(
            result.return_code,
            0,
            "Repository should not be found"
        )
        self.assertGreater(
            len(result.stderr),
            0,
            "Expected an error here"
        )

    def test_upload_content(self):
        """@Test: Create repository and upload content

        @Feature: Repository

        @Assert: upload content is successful

        """
        name = gen_string('alpha', 15)
        try:
            new_repo = self._make_repository({'name': name})
        except CLIFactoryError as err:
            self.fail(err)

        ssh.upload_file(local_file=get_data_file(RPM_TO_UPLOAD),
                        remote_file="/tmp/{0}".format(RPM_TO_UPLOAD))
        result = Repository.upload_content({
            'name': new_repo['name'],
            'path': "/tmp/{0}".format(RPM_TO_UPLOAD),
            'product-id': new_repo['product']['id'],
            'organization': new_repo['organization'],
        })
        self.assertEqual(result.return_code, 0,
                         "return code must be 0, instead got {0}"
                         ''.format(result.return_code))
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertIn("Successfully uploaded file '{0}'"
                      ''.format(RPM_TO_UPLOAD),
                      result.stdout[0]['message'])
