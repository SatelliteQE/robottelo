# -*- encoding: utf-8 -*-
# pylint: disable=too-many-public-methods, invalid-name
"""Test class for Repository CLI"""

from fauxfactory import gen_string
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    make_gpg_key,
    make_org,
    make_product,
    make_repository,
    CLIFactoryError
)
from robottelo.cli.repository import Repository
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_0_YUM_REPO,
    FAKE_1_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_2_PUPPET_REPO,
    FAKE_2_YUM_REPO,
    FAKE_3_PUPPET_REPO,
    FAKE_3_YUM_REPO,
    FAKE_4_PUPPET_REPO,
    FAKE_4_YUM_REPO,
    FAKE_5_PUPPET_REPO,
    RPM_TO_UPLOAD,
)
from robottelo.decorators import run_only_on, skip_if_bug_open, stubbed
from robottelo.helpers import (
    get_data_file,
    valid_data_list,
    invalid_values_list,
)
from robottelo.test import CLITestCase


class TestRepository(CLITestCase):
    """Repository CLI tests."""

    org = None
    product = None

    # pylint: disable=unexpected-keyword-arg
    def setUp(self):
        """Tests for Repository via Hammer CLI"""

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

    def test_bugzilla_1189289(self):
        """@Test: Check if repository docker-upstream-name is shown
        in repository info

        @Feature: Repository

        @Assert: repository info command returns upstream-repository-name
        value

        """
        repository = self._make_repository({
            u'content-type': u'docker',
            u'name': gen_string('alpha'),
            u'docker-upstream-name': u'fedora/rabbitmq',
        })
        self.assertIn(u'upstream-repository-name', repository)
        self.assertEqual(
            repository['upstream-repository-name'], u'fedora/rabbitmq')

    @run_only_on('sat')
    def test_positive_create_1(self):
        """@Test: Check if repository can be created with random names

        @Feature: Repository

        @Assert: Repository is created and has random name

        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({u'name': name})
                self.assertEqual(new_repo['name'], name)

    def test_positive_create_2(self):
        """@Test: Check if repository can be created with random names and
        labels

        @Feature: Repository

        @Assert: Repository is created and has random name and labels

        """
        for name in valid_data_list():
            with self.subTest(name):
                # Generate a random, 'safe' label
                label = gen_string('alpha', 20)
                new_repo = self._make_repository({
                    u'label': label,
                    u'name': name,
                })
                self.assertEqual(new_repo['name'], name)
                self.assertNotEqual(new_repo['name'], new_repo['label'])

    @run_only_on('sat')
    def test_positive_create_3(self):
        """@Test: Create YUM repository

        @Feature: Repository

        @Assert: YUM repository is created

        """
        for url in (FAKE_0_YUM_REPO, FAKE_1_YUM_REPO, FAKE_2_YUM_REPO,
                    FAKE_3_YUM_REPO, FAKE_4_YUM_REPO):
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url,
                })
                self.assertEqual(new_repo['url'], url)
                self.assertEqual(new_repo['content-type'], u'yum')

    def test_positive_create_4(self):
        """@Test: Create Puppet repository

        @Feature: Repository

        @Assert: Puppet repository is created

        """
        for url in (FAKE_1_PUPPET_REPO, FAKE_2_PUPPET_REPO, FAKE_3_PUPPET_REPO,
                    FAKE_4_PUPPET_REPO, FAKE_5_PUPPET_REPO):
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'puppet',
                    u'url': url,
                })
                self.assertEqual(new_repo['url'], url)
                self.assertEqual(new_repo['content-type'], u'puppet')

    @run_only_on('sat')
    def test_positive_create_5(self):
        """@Test: Check if repository can be created with gpg key ID

        @Feature: Repository

        @Assert: Repository is created and has gpg key

        """
        # Make a new gpg key
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({
                    u'gpg-key-id': gpg_key['id'],
                    u'name': name,
                })
                self.assertEqual(new_repo['gpg-key']['id'], gpg_key['id'])
                self.assertEqual(new_repo['gpg-key']['name'], gpg_key['name'])

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1103944)
    def test_positive_create_6(self):
        """@Test: Check if repository can be created with gpg key name

        @Feature: Repository

        @Assert: Repository is created and has gpg key

        @BZ: 1103944

        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({
                    u'gpg-key': gpg_key['name'],
                    u'name': name,
                })
                self.assertEqual(new_repo['gpg-key']['id'], gpg_key['id'])
                self.assertEqual(new_repo['gpg-key']['name'], gpg_key['name'])

    @run_only_on('sat')
    def test_positive_create_7(self):
        """@Test: Create repository published via http

        @Feature: Repository

        @Assert: Repository is created and is published via http

        """
        for use_http in u'true', u'yes', u'1':
            with self.subTest(use_http):
                repo = self._make_repository({'publish-via-http': use_http})
                self.assertEqual(repo['publish-via-http'], u'yes')

    @run_only_on('sat')
    def test_positive_create_8(self):
        """@Test: Create repository not published via http

        @Feature: Repository

        @Assert: Repository is created and is not published via http

        """
        for use_http in u'false', u'no', u'0':
            with self.subTest(use_http):
                repo = self._make_repository({'publish-via-http': use_http})
                self.assertEqual(repo['publish-via-http'], u'no')

    @run_only_on('sat')
    def test_positive_create_9(self):
        """@Test: Create a YUM repository with a checksum type

        @Feature: Repository

        @Assert: A YUM repository is created and contains the correct checksum
        type


        """
        for checksum_type in u'sha1', u'sha256':
            with self.subTest(checksum_type):
                content_type = u'yum'
                repository = self._make_repository({
                    u'checksum-type': checksum_type,
                    u'content-type': content_type,
                })
                self.assertEqual(repository['content-type'], content_type)
                self.assertEqual(repository['checksum-type'], checksum_type)

    @run_only_on('sat')
    def test_positive_create_docker_repo_1(self):
        """@Test: Create a Docker repository with upstream name.

        @Feature: Repository

        @Assert: Docker repository is created and contains correct values.

        """
        content_type = u'docker'
        new_repo = self._make_repository({
            u'content-type': content_type,
            u'docker-upstream-name': u'busybox',
            u'name': u'busybox',
            u'url': DOCKER_REGISTRY_HUB,
        })
        # Assert that urls and content types matches data passed
        self.assertEqual(new_repo['url'], DOCKER_REGISTRY_HUB)
        self.assertEqual(new_repo['content-type'], content_type)
        self.assertEqual(new_repo['name'], u'busybox')

    @run_only_on('sat')
    def test_positive_create_docker_repo_2(self):
        """@Test: Create a Docker repository with a random name.

        @Feature: Repository

        @Assert: Docker repository is created and contains correct values.

        """
        for name in valid_data_list():
            with self.subTest(name):
                content_type = u'docker'
                new_repo = self._make_repository({
                    u'content-type': content_type,
                    u'docker-upstream-name': u'busybox',
                    u'name': name,
                    u'url': DOCKER_REGISTRY_HUB,
                })
                # Assert that urls, content types and name matches data passed
                self.assertEqual(new_repo['url'], DOCKER_REGISTRY_HUB)
                self.assertEqual(new_repo['content-type'], content_type)
                self.assertEqual(new_repo['name'], name)

    def test_negative_create_1(self):
        """@Test: Repository name cannot be 300-characters long

        @Feature: Repository

        @Assert: Repository cannot be created

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({u'name': name})

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1152237)
    def test_positive_synchronize_1(self):
        """@Test: Check if repository can be created and synced

        @Feature: Repository

        @Assert: Repository is created and synced

        """
        for url in FAKE_1_YUM_REPO, FAKE_3_YUM_REPO, FAKE_4_YUM_REPO:
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url,
                })
                # Assertion that repo is not yet synced
                self.assertEqual(new_repo['sync']['status'], 'Not Synced')
                # Synchronize it
                Repository.synchronize({'id': new_repo['id']})
                # Verify it has finished
                new_repo = Repository.info({'id': new_repo['id']})
                self.assertEqual(new_repo['sync']['status'], 'Finished')

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1152237)
    def test_positive_synchronize_2(self):
        """@Test: Check if Docker repository can be created and synced

        @Feature: Repository

        @Assert: Docker repository is created and synced

        """
        new_repo = self._make_repository({
            u'content-type': u'docker',
            u'docker-upstream-name': u'busybox',
            u'url': DOCKER_REGISTRY_HUB,
        })
        # Assertion that repo is not yet synced
        self.assertEqual(new_repo['sync']['status'], 'Not Synced')
        # Synchronize it
        Repository.synchronize({'id': new_repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(new_repo['sync']['status'], 'Finished')

    @run_only_on('sat')
    def test_positive_update_1(self):
        """@Test: Update the original url for a repository

        @Feature: Repository

        @Assert: Repository url is updated

        """
        new_repo = self._make_repository()
        for url in (FAKE_4_YUM_REPO, FAKE_1_PUPPET_REPO, FAKE_2_PUPPET_REPO,
                    FAKE_3_PUPPET_REPO, FAKE_2_YUM_REPO):
            with self.subTest(url):
                # Update the url
                Repository.update({
                    u'id': new_repo['id'],
                    u'url': url,
                })
                # Fetch it again
                result = Repository.info({'id': new_repo['id']})
                self.assertEqual(result['url'], url)

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_2(self):
        """@Test: Update the original gpg key

        @Feature: Repository

        @Assert: Repository gpg key is updated

        @Status: manual

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_update_3(self):
        """@Test: Update the original publishing method

        @Feature: Repository

        @Assert: Repository publishing method is updated

        @Status: manual

        """

    @skip_if_bug_open('bugzilla', 1208305)
    @run_only_on('sat')
    def test_positive_update_4(self):
        """@Test: Create a YUM repository and update the checksum type

        @Feature: Repository

        @Assert: A YUM repository is updated and contains the correct checksum
        type

        @BZ: 1208305

        """
        content_type = u'yum'
        repository = self._make_repository({
            u'content-type': content_type
        })
        self.assertEqual(repository['content-type'], content_type)
        self.assertEqual(repository['checksum-type'], '')
        for checksum_type in u'sha1', u'sha256':
            with self.subTest(checksum_type):
                # Update the checksum
                Repository.update({
                    u'checksum-type': checksum_type,
                    u'id': repository['id'],
                })
                # Fetch it again
                result = Repository.info({'id': repository['id']})
                self.assertEqual(result['checksum-type'], checksum_type)

    @run_only_on('sat')
    def test_positive_delete_1(self):
        """@Test: Check if repository can be created and deleted

        @Feature: Repository

        @Assert: Repository is created and then deleted

        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({u'name': name})
                Repository.delete({u'id': new_repo['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Repository.info({u'id': new_repo['id']})

    def test_upload_content(self):
        """@Test: Create repository and upload content

        @Feature: Repository

        @Assert: upload content is successful

        """
        new_repo = self._make_repository({'name': gen_string('alpha', 15)})
        ssh.upload_file(local_file=get_data_file(RPM_TO_UPLOAD),
                        remote_file="/tmp/{0}".format(RPM_TO_UPLOAD))
        result = Repository.upload_content({
            'name': new_repo['name'],
            'organization': new_repo['organization'],
            'path': "/tmp/{0}".format(RPM_TO_UPLOAD),
            'product-id': new_repo['product']['id'],
        })
        self.assertIn(
            "Successfully uploaded file '{0}'".format(RPM_TO_UPLOAD),
            result[0]['message'],
        )
