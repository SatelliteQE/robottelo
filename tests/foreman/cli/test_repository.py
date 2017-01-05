# -*- encoding: utf-8 -*-
"""Test class for Repository CLI

@Requirement: Repository

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.task import Task
from robottelo.cli.factory import (
    make_content_view,
    make_gpg_key,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_product_wait,
    make_repository,
    CLIFactoryError,
)
from robottelo.cli.repository import Repository
from robottelo.cli.settings import Settings
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
    FAKE_5_YUM_REPO,
    FAKE_7_PUPPET_REPO,
    FAKE_YUM_DRPM_REPO,
    FAKE_YUM_SRPM_REPO,
    RPM_TO_UPLOAD,
    SRPM_TO_UPLOAD,
    DOWNLOAD_POLICIES,
    REPO_TYPE
)
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    tier1,
    tier2,
)
from robottelo.datafactory import (
    invalid_http_credentials,
    invalid_values_list,
    valid_data_list,
    valid_http_credentials,
)
from robottelo.helpers import get_data_file
from robottelo.test import CLITestCase


class RepositoryTestCase(CLITestCase):
    """Repository CLI tests."""

    org = None
    product = None

    # pylint: disable=unexpected-keyword-arg
    def setUp(self):
        """Tests for Repository via Hammer CLI"""

        super(RepositoryTestCase, self).setUp()

        if RepositoryTestCase.org is None:
            RepositoryTestCase.org = make_org(cached=True)
        if RepositoryTestCase.product is None:
            RepositoryTestCase.product = make_product_wait(
                {u'organization-id': RepositoryTestCase.org['id']},
                )

    def _make_repository(self, options=None):
        """Makes a new repository and asserts its success"""
        if options is None:
            options = {}

        if options.get('product-id') is None:
            options[u'product-id'] = self.product['id']

        return make_repository(options)

    @tier1
    def test_verify_bugzilla_1189289(self):
        """Check if repository docker-upstream-name is shown
        in repository info

        @id: f197a14c-2cf3-4564-9b18-5fd37d469ea4

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
    @tier1
    def test_positive_create_with_name(self):
        """Check if repository can be created with random names

        @id: 604dea2c-d512-4a27-bfc1-24c9655b6ea9

        @Assert: Repository is created and has random name
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({u'name': name})
                self.assertEqual(new_repo['name'], name)

    @tier1
    def test_positive_create_with_name_label(self):
        """Check if repository can be created with random names and
        labels

        @id: 79d2a6d0-5032-46cd-880c-46cf392521fa

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
    @tier1
    def test_positive_create_with_yum_repo(self):
        """Create YUM repository

        @id: 4c08824f-ba95-486c-94c2-9abf0a3441ea

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

    @tier1
    def test_positive_create_with_puppet_repo(self):
        """Create Puppet repository

        @id: 75c309ba-fbc9-419d-8427-7a61b063ec13

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
    @tier1
    def test_positive_create_with_auth_yum_repo(self):
        """Create YUM repository with basic HTTP authentication

        @id: da8309fd-3076-427b-a96f-8d883d6e944f

        @Assert: YUM repository is created
        """
        url = FAKE_5_YUM_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url_encoded
                })
                self.assertEqual(new_repo['url'], url_encoded)
                self.assertEqual(new_repo['content-type'], u'yum')

    @tier1
    def test_positive_create_with_download_policy(self):
        """Create YUM repositories with available download policies

        @id: ffb386e6-c360-4d4b-a324-ccc21768b4f8

        @Assert: YUM repository with a download policy is created
        """
        for policy in DOWNLOAD_POLICIES:
            with self.subTest(policy):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'download-policy': policy
                })
                self.assertEqual(new_repo['download-policy'], policy)

    @tier1
    def test_positive_create_with_default_download_policy(self):
        """Verify if the default download policy is assigned
        when creating a YUM repo without `--download-policy`

        @id: 9a3c4d95-d6ca-4377-9873-2c552b7d6ce7

        @Assert: YUM repository with a default download policy
        """
        default_dl_policy = Settings.list(
            {'search': 'name=default_download_policy'}
        )
        self.assertTrue(default_dl_policy)
        new_repo = self._make_repository({u'content-type': u'yum'})
        self.assertEqual(
            new_repo['download-policy'], default_dl_policy[0]['value']
        )

    @tier1
    def test_positive_create_immediate_update_to_on_demand(self):
        """Update `immediate` download policy to `on_demand`
        for a newly created YUM repository

        @id: 1a80d686-3f7b-475e-9d1a-3e1f51d55101

        @Assert: immediate download policy is updated to on_demand
        """
        new_repo = self._make_repository({
            u'content-type': u'yum',
            u'download-policy': 'immediate'
        })
        Repository.update({
            u'id': new_repo['id'],
            u'download-policy': 'on_demand'
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['download-policy'], 'on_demand')

    @tier1
    def test_positive_create_immediate_update_to_background(self):
        """Update `immediate` download policy to `background`
        for a newly created YUM repository

        @id: 7a9243eb-012c-40ad-9105-b078ed0a9eda

        @Assert: immediate download policy is updated to background
        """
        new_repo = self._make_repository({
            u'content-type': u'yum',
            u'download-policy': 'immediate'
        })
        Repository.update({
            u'id': new_repo['id'],
            u'download-policy': 'background'
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['download-policy'], 'background')

    @tier1
    def test_positive_create_on_demand_update_to_immediate(self):
        """Update `on_demand` download policy to `immediate`
        for a newly created YUM repository

        @id: 1e8338af-32e5-4f92-9215-bfdc1973c8f7

        @Assert: on_demand download policy is updated to immediate
        """
        new_repo = self._make_repository({
            u'content-type': u'yum',
            u'download-policy': 'on_demand'
        })
        Repository.update({
            u'id': new_repo['id'],
            u'download-policy': 'immediate'
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['download-policy'], 'immediate')

    @tier1
    def test_positive_create_on_demand_update_to_background(self):
        """Update `on_demand` download policy to `background`
        for a newly created YUM repository

        @id: da600200-5bd4-4cb8-a891-37cd2233803e

        @Assert: on_demand download policy is updated to background
        """
        new_repo = self._make_repository({
            u'content-type': u'yum',
            u'download-policy': 'on_demand'
        })
        Repository.update({
            u'id': new_repo['id'],
            u'download-policy': 'background'
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['download-policy'], 'background')

    @tier1
    def test_positive_create_background_update_to_immediate(self):
        """Update `background` download policy to `immediate`
        for a newly created YUM repository

        @id: cf4dca0c-36bd-4a3c-aa29-f435ac60b3f8

        @Assert: background download policy is updated to immediate
        """
        new_repo = self._make_repository({
            u'content-type': u'yum',
            u'download-policy': 'background'
        })
        Repository.update({
            u'id': new_repo['id'],
            u'download-policy': 'immediate'
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['download-policy'], 'immediate')

    @tier1
    def test_positive_create_background_update_to_on_demand(self):
        """Update `background` download policy to `on_demand`
        for a newly created YUM repository

        @id: 0f943e3d-44b7-4b6e-9a7d-d33f7f4864d1

        @Assert: background download policy is updated to on_demand
        """
        new_repo = self._make_repository({
            u'content-type': u'yum',
            u'download-policy': 'background'
        })
        Repository.update({
            u'id': new_repo['id'],
            u'download-policy': 'on_demand'
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['download-policy'], 'on_demand')

    @tier1
    def test_positive_create_with_auth_puppet_repo(self):
        """Create Puppet repository with basic HTTP authentication

        @id: b13f8ae2-60ab-47e6-a096-d3f368e5cab3

        @Assert: Puppet repository is created
        """
        url = FAKE_7_PUPPET_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'puppet',
                    u'url': url_encoded
                })
                self.assertEqual(new_repo['url'], url_encoded)
                self.assertEqual(new_repo['content-type'], u'puppet')

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_gpg_key_by_id(self):
        """Check if repository can be created with gpg key ID

        @id: 6d22f0ea-2d27-4827-9b7a-3e1550a47285

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
    @tier1
    def test_positive_create_with_gpg_key_by_name(self):
        """Check if repository can be created with gpg key name

        @id: 95cde404-3449-410d-9a08-d7f8619a2ad5

        @Assert: Repository is created and has gpg key

        @BZ: 1103944
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({
                    u'gpg-key': gpg_key['name'],
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(new_repo['gpg-key']['id'], gpg_key['id'])
                self.assertEqual(new_repo['gpg-key']['name'], gpg_key['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_publish_via_http(self):
        """Create repository published via http

        @id: faf6058c-9dd3-444c-ace2-c41791669e9e

        @Assert: Repository is created and is published via http
        """
        for use_http in u'true', u'yes', u'1':
            with self.subTest(use_http):
                repo = self._make_repository({'publish-via-http': use_http})
                self.assertEqual(repo['publish-via-http'], u'yes')

    @run_only_on('sat')
    @tier1
    def test_positive_create_publish_via_https(self):
        """Create repository not published via http

        @id: 4395a5df-207c-4b34-a42d-7b3273bd68ec

        @Assert: Repository is created and is not published via http
        """
        for use_http in u'false', u'no', u'0':
            with self.subTest(use_http):
                repo = self._make_repository({'publish-via-http': use_http})
                self.assertEqual(repo['publish-via-http'], u'no')

    @run_only_on('sat')
    @tier1
    def test_positive_create_yum_repo_with_checksum_type(self):
        """Create a YUM repository with a checksum type

        @id: 934f4a09-2a64-485d-ae6c-8ef73aa8fb2b

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
    @tier1
    def test_positive_create_docker_repo_with_upstream_name(self):
        """Create a Docker repository with upstream name.

        @id: 776f92eb-8b40-4efd-8315-4fbbabcb2d4e

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
    @tier1
    def test_positive_create_docker_repo_with_name(self):
        """Create a Docker repository with a random name.

        @id: b6a01434-8672-4196-b61a-dcb86c49f43b

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

    @tier1
    def test_negative_create_with_name(self):
        """Repository name cannot be 300-characters long

        @id: af0652d3-012d-4846-82ac-047918f74722

        @Assert: Repository cannot be created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({u'name': name})

    @tier1
    def test_negative_create_with_auth_url_with_special_characters(self):
        """Verify that repository URL cannot contain unquoted special characters

        @id: 2bd5ee17-0fe5-43cb-9cdc-dc2178c5374c

        @Assert: Repository cannot be created
        """
        # get a list of valid credentials without quoting them
        for cred in [creds for creds in valid_http_credentials()
                     if creds['quote'] is True]:
            with self.subTest(cred):
                url = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({u'url': url})

    @tier1
    def test_negative_create_with_auth_url_too_long(self):
        """Verify that repository URL length is limited

        @id: de356c66-4237-4421-89e3-f4f8bbe6f526

        @Assert: Repository cannot be created
        """
        for cred in invalid_http_credentials():
            with self.subTest(cred):
                url = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({u'url': url})

    @tier1
    def test_negative_create_with_invalid_download_policy(self):
        """Verify that YUM repository cannot be created with invalid download policy

        @id: 3b143bf8-7056-4c94-910d-69a451071f26

        @Assert: YUM repository is not created with invalid download policy
        """
        with self.assertRaises(CLIFactoryError):
            self._make_repository({
                u'content-type': u'yum',
                u'download-policy': gen_string('alpha', 5)
            })

    @tier1
    def test_negative_update_to_invalid_download_policy(self):
        """Verify that YUM repository cannot be updated to invalid download policy

        @id: 5bd6a2e4-7ff0-42ac-825a-6b2a2f687c89

        @Assert: YUM repository is not updated to invalid download policy
        """
        with self.assertRaises(CLIReturnCodeError):
            new_repo = self._make_repository({u'content-type': u'yum'})
            Repository.update({
                u'id': new_repo['id'],
                u'download-policy': gen_string('alpha', 5)
            })

    @tier1
    def test_negative_create_non_yum_with_download_policy(self):
        """Verify that non-YUM repositories cannot be created with download policy

        @id: 71388973-50ea-4a20-9406-0aca142014ca

        @Assert: Non-YUM repository is not created with a download policy
        """
        non_yum_repo_types = [
            item for item in REPO_TYPE.keys() if item != 'yum'
        ]
        for content_type in non_yum_repo_types:
            with self.subTest(content_type):
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({
                        u'content-type': content_type,
                        u'download-policy': u'on_demand'
                    })

    @run_only_on('sat')
    @tier2
    def test_positive_synchronize_yum_repo(self):
        """Check if repository can be created and synced

        @id: e3a62529-edbd-4062-9246-bef5f33bdcf0

        @Assert: Repository is created and synced

        @CaseLevel: Integration
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
                self.assertEqual(new_repo['sync']['status'], 'Success')

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_positive_synchronize_auth_yum_repo(self):
        """Check if secured repository can be created and synced

        @id: b0db676b-e0f0-428c-adf3-1d7c0c3599f0

        @Assert: Repository is created and synced

        @CaseLevel: Integration
        """
        url = FAKE_5_YUM_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if cred['http_valid']]:
            url_encoded = url.format(
                creds['login'], creds['pass']
            )
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url_encoded,
                })
                # Assertion that repo is not yet synced
                self.assertEqual(new_repo['sync']['status'], 'Not Synced')
                # Synchronize it
                Repository.synchronize({'id': new_repo['id']})
                # Verify it has finished
                new_repo = Repository.info({'id': new_repo['id']})
                self.assertEqual(new_repo['sync']['status'], 'Success')

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_negative_synchronize_auth_yum_repo(self):
        """Check if secured repo fails to synchronize with invalid credentials

        @id: 809905ae-fb76-465d-9468-1f99c4274aeb

        @Assert: Repository is created but synchronization fails

        @CaseLevel: Integration
        """
        url = FAKE_5_YUM_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if not cred['http_valid']]:
            url_encoded = url.format(
                creds['login'], creds['pass']
            )
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url_encoded,
                })
                # Try to synchronize it
                repo_sync = Repository.synchronize(
                    {'id': new_repo['id'], u'async': True}
                )
                Task.progress({u'id': repo_sync[0]['id']})
                self.assertEqual(
                    Task.progress({u'id': repo_sync[0]['id']})[0],
                    u'Yum Metadata: Unauthorized'
                )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_positive_synchronize_auth_puppet_repo(self):
        """Check if secured puppet repository can be created and synced

        @id: 1d2604fc-8a18-4cbe-bf4c-5c7d9fbdb82c

        @Assert: Repository is created and synced

        @CaseLevel: Integration
        """
        url = FAKE_7_PUPPET_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if cred['http_valid']]:
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url_encoded,
                })
                # Assertion that repo is not yet synced
                self.assertEqual(new_repo['sync']['status'], 'Not Synced')
                # Synchronize it
                Repository.synchronize({'id': new_repo['id']})
                # Verify it has finished
                new_repo = Repository.info({'id': new_repo['id']})
                self.assertEqual(new_repo['sync']['status'], 'Success')

    @run_only_on('sat')
    @tier2
    def test_positive_synchronize_docker_repo(self):
        """Check if Docker repository can be created and synced

        @id: cb9ae788-743c-4785-98b2-6ae0c161bc9a

        @Assert: Docker repository is created and synced

        @CaseLevel: Integration
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
        self.assertEqual(new_repo['sync']['status'], 'Success')

    @run_only_on('sat')
    @tier1
    def test_positive_update_url(self):
        """Update the original url for a repository

        @id: 1a2cf29b-5c30-4d4c-b6d1-2f227b0a0a57

        @Assert: Repository url is updated
        """
        new_repo = self._make_repository()
        # generate repo URLs with all valid credentials
        auth_repos = [
            repo.format(creds['login'], creds['pass'])
            for creds in valid_http_credentials(url_encoded=True)
            for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
        ]

        for url in [FAKE_4_YUM_REPO, FAKE_1_PUPPET_REPO, FAKE_2_PUPPET_REPO,
                    FAKE_3_PUPPET_REPO, FAKE_2_YUM_REPO] + auth_repos:
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
    @tier1
    def test_negative_update_auth_url_with_special_characters(self):
        """Verify that repository URL credentials cannot be updated to contain
        the forbidden characters

        @id: 566553b2-d077-4fd8-8ed5-00ba75355386

        @Assert: Repository url not updated
        """
        new_repo = self._make_repository()
        # get auth repos with credentials containing unquoted special chars
        auth_repos = [
            repo.format(cred['login'], cred['pass'])
            for cred in valid_http_credentials() if cred['quote']
            for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
        ]

        for url in auth_repos:
            with self.subTest(url):
                with self.assertRaises(CLIReturnCodeError):
                    Repository.update({
                        u'id': new_repo['id'],
                        u'url': url,
                    })
                # Fetch it again
                result = Repository.info({'id': new_repo['id']})
                self.assertEqual(result['url'], new_repo['url'])

    @run_only_on('sat')
    @tier1
    def test_negative_update_auth_url_too_long(self):
        """Update the original url for a repository to value which is too long

        @id: a703de60-8631-4e31-a9d9-e51804f27f03

        @Assert: Repository url not updated
        """
        new_repo = self._make_repository()
        # generate repo URLs with all invalid credentials
        auth_repos = [
            repo.format(cred['login'], cred['pass'])
            for cred in invalid_http_credentials()
            for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
        ]

        for url in auth_repos:
            with self.subTest(url):
                with self.assertRaises(CLIReturnCodeError):
                    Repository.update({
                        u'id': new_repo['id'],
                        u'url': url,
                    })
                # Fetch it again
                result = Repository.info({'id': new_repo['id']})
                self.assertEqual(result['url'], new_repo['url'])

    @run_only_on('sat')
    @tier1
    def test_positive_update_gpg_key(self):
        """Update the original gpg key

        @id: 367ff375-4f52-4a8c-b974-8c1c54e3fdd3

        @Assert: Repository gpg key is updated
        """
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        gpg_key_new = make_gpg_key({'organization-id': self.org['id']})
        new_repo = self._make_repository({
            u'gpg-key-id': gpg_key['id'],
        })
        Repository.update({
            u'id': new_repo['id'],
            u'gpg-key-id': gpg_key_new['id'],
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['gpg-key']['id'], gpg_key_new['id'])

    @run_only_on('sat')
    @tier1
    def test_positive_update_publish_method(self):
        """Update the original publishing method

        @id: e7bd2667-4851-4a64-9c70-1b5eafbc3f71

        @Assert: Repository publishing method is updated
        """
        new_repo = self._make_repository({
            u'publish-via-http': 'no',
        })
        Repository.update({
            u'id': new_repo['id'],
            u'publish-via-http': 'yes',
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['publish-via-http'], 'yes')

    @run_only_on('sat')
    @tier1
    def test_positive_update_checksum_type(self):
        """Create a YUM repository and update the checksum type

        @id: 42f14257-d860-443d-b337-36fd355014bc

        @Assert: A YUM repository is updated and contains the correct checksum
        type
        """
        content_type = u'yum'
        repository = self._make_repository({
            u'content-type': content_type
        })
        self.assertEqual(repository['content-type'], content_type)
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
    @tier1
    def test_positive_delete_by_id(self):
        """Check if repository can be created and deleted

        @id: bcf096db-0033-4138-90a3-cb7355d5dfaf

        @Assert: Repository is created and then deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({u'name': name})
                Repository.delete({u'id': new_repo['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Repository.info({u'id': new_repo['id']})

    @skip_if_bug_open('bugzilla', 1343006)
    @tier1
    def test_positive_upload_content(self):
        """Create repository and upload content

        @id: eb0ec599-2bf1-483a-8215-66652f948d67

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


class SRPMRepositoryTestCase(CLITestCase):
    """Tests specific to using repositories containing source RPMs."""

    @classmethod
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(SRPMRepositoryTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({'organization-id': cls.org['id']})

    @skip_if_bug_open('bugzilla', 1378442)
    @tier1
    def test_positive_upload_content_srpm(self):
        """Create repository and upload a SRPM content

        @id: 706dc3e2-dacb-4fdd-8eef-5715ce498888

        @Assert: File successfully uploaded
        """
        new_repo = self._make_repository({'name': gen_string('alpha', 15)})
        ssh.upload_file(local_file=get_data_file(SRPM_TO_UPLOAD),
                        remote_file="/tmp/{0}".format(SRPM_TO_UPLOAD))
        result = Repository.upload_content({
            'name': new_repo['name'],
            'organization': new_repo['organization'],
            'path': "/tmp/{0}".format(SRPM_TO_UPLOAD),
            'product-id': new_repo['product']['id'],
        })
        self.assertIn(
            "Successfully uploaded file '{0}'".format(SRPM_TO_UPLOAD),
            result[0]['message'],
        )

    @tier2
    def test_positive_sync(self):
        """Synchronize repository with SRPMs

        @id: eb69f840-122d-4180-b869-1bd37518480c

        @Assert: srpms can be listed in repository
        """
        repo = make_repository({
            'product-id': self.product['id'],
            'url': FAKE_YUM_SRPM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.org['label'],
                self.product['label'],
                repo['label'],
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_sync_publish_cv(self):
        """Synchronize repository with SRPMs, add repository to content view
        and publish content view

        @id: 78cd6345-9c6c-490a-a44d-2ad64b7e959b

        @Assert: srpms can be listed in content view
        """
        repo = make_repository({
            'product-id': self.product['id'],
            'url': FAKE_YUM_SRPM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': self.org['id']})
        ContentView.add_repository({
            'id': cv['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': cv['id']})
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.org['label'],
                cv['label'],
                self.product['label'],
                repo['label'],
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_sync_publish_promote_cv(self):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        @id: 3d197118-b1fa-456f-980e-ad1a517bc769

        @Assert: srpms can be listed in content view in proper lifecycle
        environment
        """
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        repo = make_repository({
            'product-id': self.product['id'],
            'url': FAKE_YUM_SRPM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': self.org['id']})
        ContentView.add_repository({
            'id': cv['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': cv['id']})
        content_view = ContentView.info({'id': cv['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            'id': cvv['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            ' | grep .src.rpm'
            .format(
                self.org['label'],
                lce['label'],
                cv['label'],
                self.product['label'],
                repo['label'],
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)


class DRPMRepositoryTestCase(CLITestCase):
    """Tests specific to using repositories containing delta RPMs."""

    @classmethod
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(DRPMRepositoryTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({'organization-id': cls.org['id']})

    @tier2
    def test_positive_sync(self):
        """Synchronize repository with DRPMs

        @id: a645966c-750b-40ef-a264-dc3bb632b9fd

        @Assert: drpms can be listed in repository
        """
        repo = make_repository({
            'product-id': self.product['id'],
            'url': FAKE_YUM_DRPM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.org['label'],
                self.product['label'],
                repo['label'],
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_sync_publish_cv(self):
        """Synchronize repository with DRPMs, add repository to content view
        and publish content view

        @id: 014bfc80-4622-422e-a0ec-755b1d9f845e

        @Assert: drpms can be listed in content view
        """
        repo = make_repository({
            'product-id': self.product['id'],
            'url': FAKE_YUM_DRPM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': self.org['id']})
        ContentView.add_repository({
            'id': cv['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': cv['id']})
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.org['label'],
                cv['label'],
                self.product['label'],
                repo['label'],
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_sync_publish_promote_cv(self):
        """Synchronize repository with DRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        @id: a01cb12b-d388-4902-8532-714f4e28ec56

        @Assert: drpms can be listed in content view in proper lifecycle
        environment
        """
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        repo = make_repository({
            'product-id': self.product['id'],
            'url': FAKE_YUM_DRPM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': self.org['id']})
        ContentView.add_repository({
            'id': cv['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': cv['id']})
        content_view = ContentView.info({'id': cv['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            'id': cvv['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}'
            '/drpms/ | grep .drpm'
            .format(
                self.org['label'],
                lce['label'],
                cv['label'],
                self.product['label'],
                repo['label'],
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)


class GitPuppetMirrorTestCase(CLITestCase):
    """Tests for creating the hosts via CLI."""

    # Notes for Puppet GIT puppet mirror content
    #
    # This feature does not allow us to actually sync/update content in a
    # GIT repo.
    # Instead, we're essentially "snapshotting" what contains in a repo at any
    # given time. The ability to update the GIT puppet mirror comes is/should
    # be provided by pulp itself, via script.  However, we should be able to
    # create a sync schedule against the mirror to make sure it is periodically
    # update to contain the latest and greatest.

    @tier2
    def test_positive_git_local_create(self):
        """Create repository with local git puppet mirror.

        @id: 89211cd5-82b8-4391-b729-a7502e57f824

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror via cli

        @Assert: Content source containing local GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_local_update(self):
        """Update repository with local git puppet mirror.

        @id: 341f40f2-3501-4754-9acf-7cda1a61f7db

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Modify details for existing puppet repo (name, etc.) via cli

        @Assert: Content source containing local GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_local_delete(self):
        """Delete repository with local git puppet mirror.

        @id: a243f5bb-5186-41b3-8e8a-07d5cc784ccd

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to local puppet mirror via cli

        @Assert: Content source containing local GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_create(self):
        """Create repository with remote git puppet mirror.

        @id: 8582529f-3112-4b49-8d8f-f2bbf7dceca7

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror via cli

        @Assert: Content source containing remote GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_update(self):
        """Update repository with remote git puppet mirror.

        @id: 582c50b3-3b90-4244-b694-97642b1b13a9

        @CaseLevel: Integration

        @Setup: Assure remote  GIT puppet has been created and found by pulp

        @Steps:

        1.  modify details for existing puppet repo (name, etc.) via cli

        @Assert: Content source containing remote GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_delete(self):
        """Delete repository with remote git puppet mirror.

        @id: 0a23f969-b202-4c6c-b12e-f651a0b7d049

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to remote puppet mirror via cli

        @Assert: Content source containing remote GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_sync(self):
        """Sync repository with git puppet mirror.
        @id: a46c16bd-0986-48db-8e62-aeb3907ba4d2

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to sync content from mirror via cli

        @Assert: Content is pulled down without error

        @Assert: Confirmation that various resources actually exist in
        local content repo

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_sync_with_content_change(self):
        """Sync repository with changes in git puppet mirror.
        If module changes in GIT mirror but the version in manifest
        does not change, content still pulled.

        @id: 7d9519ca-8660-4014-8e0e-836594891c0c

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Sync a git repo and observe the contents/checksum etc. of an
            existing puppet module
        2.  Assure a puppet module in git repo has changed but the manifest
            version for this module does not change.
        3.  Using pulp script, update repo mirror and re-sync within satellite
        4.  View contents/details of same puppet module

        @Assert: Puppet module has been updated in our content, even though
        the module's version number has not changed.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_sync_schedule(self):
        """Scheduled sync of git puppet mirror.

        @id: 0d58d180-9836-4524-b608-66b67f9cab12

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to create a scheduled sync content from mirror, via cli

        @Assert: Content is pulled down without error  on expected schedule

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_view_content(self):
        """View content in synced git puppet mirror

        @id: 02f06092-dd6c-49fa-be9f-831e52476e41

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to list contents of repo via cli

        @Assert: Spot-checked items (filenames, dates, perhaps checksums?)
        are correct.

        @CaseAutomation: notautomated
        """
