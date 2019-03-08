# -*- encoding: utf-8 -*-
"""Test class for Repository CLI

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from wait_for import wait_for

from fauxfactory import gen_alphanumeric, gen_string
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.package import Package
from robottelo.cli.module_stream import ModuleStream
from robottelo.cli.file import File
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.task import Task
from robottelo.cli.factory import (
    CLIFactoryError,
    make_content_view,
    make_filter,
    make_gpg_key,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_product_wait,
    make_repository,
    make_role,
    make_user,
)
from robottelo.cli.filter import Filter
from robottelo.cli.repository import Repository
from robottelo.cli.role import Role
from robottelo.cli.settings import Settings
from robottelo.cli.user import User
from robottelo.constants import (
    FEDORA27_OSTREE_REPO,
    CUSTOM_FILE_REPO,
    CUSTOM_LOCAL_FOLDER,
    CUSTOM_FILE_REPO_FILES_COUNT,
    CUSTOM_MODULE_STREAM_REPO_1,
    CUSTOM_MODULE_STREAM_REPO_2,
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
    FAKE_YUM_MIXED_REPO,
    FAKE_YUM_SRPM_REPO,
    FAKE_PULP_REMOTE_FILEREPO,
    OS_TEMPLATE_DATA_FILE,
    RPM_TO_UPLOAD,
    SRPM_TO_UPLOAD,
    DOWNLOAD_POLICIES,
    REPO_TYPE
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.datafactory import (
    invalid_http_credentials,
    invalid_values_list,
    valid_data_list,
    valid_docker_repository_names,
    valid_http_credentials,
)
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import get_data_file
from robottelo.host_info import get_host_os_version
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

    def _get_image_tags_count(self, repo=None):
        repo_detail = Repository.info({'id': repo['id']})
        return repo_detail

    def _validated_image_tags_count(self, repo=None):
        if bz_bug_is_open(1664631):
            wait_for(
                lambda: int(self._get_image_tags_count(repo=repo)
                            ['content-counts']['container-image-tags']) > 0,
                timeout=30,
                delay=2,
                logger=self.logger
            )
        return self._get_image_tags_count(repo=repo)

    @tier1
    @upgrade
    def test_positive_info_docker_upstream_name(self):
        """Check if repository docker-upstream-name is shown
        in repository info

        :id: f197a14c-2cf3-4564-9b18-5fd37d469ea4

        :expectedresults: repository info command returns upstream-repository-
            name value

        :BZ: 1189289

        :CaseImportance: Critical
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

        :id: 604dea2c-d512-4a27-bfc1-24c9655b6ea9

        :expectedresults: Repository is created and has random name

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({u'name': name})
                self.assertEqual(new_repo['name'], name)

    @tier1
    def test_positive_create_with_name_label(self):
        """Check if repository can be created with random names and
        labels

        :id: 79d2a6d0-5032-46cd-880c-46cf392521fa

        :expectedresults: Repository is created and has random name and labels

        :CaseImportance: Critical
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
                self.assertEqual(new_repo['label'], label)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_yum_repo(self):
        """Create YUM repository

        :id: 4c08824f-ba95-486c-94c2-9abf0a3441ea

        :expectedresults: YUM repository is created

        :CaseImportance: Critical
        """
        for url in (
                FAKE_0_YUM_REPO,
                FAKE_1_YUM_REPO,
                FAKE_2_YUM_REPO,
                FAKE_3_YUM_REPO,
                FAKE_4_YUM_REPO
        ):
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url,
                })
                self.assertEqual(new_repo['url'], url)
                self.assertEqual(new_repo['content-type'], u'yum')

    @tier1
    @upgrade
    def test_positive_create_with_puppet_repo(self):
        """Create Puppet repository

        :id: 75c309ba-fbc9-419d-8427-7a61b063ec13

        :expectedresults: Puppet repository is created

        :CaseImportance: Critical
        """
        for url in (
                FAKE_1_PUPPET_REPO,
                FAKE_2_PUPPET_REPO,
                FAKE_3_PUPPET_REPO,
                FAKE_4_PUPPET_REPO,
                FAKE_5_PUPPET_REPO
        ):
            with self.subTest(url):
                new_repo = self._make_repository({
                    u'content-type': u'puppet',
                    u'url': url,
                })
                self.assertEqual(new_repo['url'], url)
                self.assertEqual(new_repo['content-type'], u'puppet')

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_with_file_repo(self):
        """Create file repository

        :id: 46f63419-1acc-4ae2-be8c-d97816ba342f

        :expectedresults: file repository is created

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({
            u'content-type': u'file',
            u'url': CUSTOM_FILE_REPO,
        })
        self.assertEqual(new_repo['url'], CUSTOM_FILE_REPO)
        self.assertEqual(new_repo['content-type'], u'file')

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_auth_yum_repo(self):
        """Create YUM repository with basic HTTP authentication

        :id: da8309fd-3076-427b-a96f-8d883d6e944f

        :expectedresults: YUM repository is created

        :CaseImportance: Critical
        """
        url = FAKE_5_YUM_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url_encoded):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url_encoded
                })
                self.assertEqual(new_repo['url'], url_encoded)
                self.assertEqual(new_repo['content-type'], u'yum')

    @tier1
    @upgrade
    def test_positive_create_with_download_policy(self):
        """Create YUM repositories with available download policies

        :id: ffb386e6-c360-4d4b-a324-ccc21768b4f8

        :expectedresults: YUM repository with a download policy is created

        :CaseImportance: Critical
        """
        for policy in DOWNLOAD_POLICIES:
            with self.subTest(policy):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'download-policy': policy
                })
                self.assertEqual(new_repo['download-policy'], policy)

    @tier1
    @upgrade
    def test_positive_create_with_mirror_on_sync(self):
        """Create YUM repositories with available mirror on sync rule

        :id: 37a09a91-42fc-4271-b58b-8e00ef0dc5a7

        :expectedresults: YUM repository created successfully and its mirror on
            sync rule value can be read back

        :BZ: 1383258

        :CaseImportance: Critical
        """
        for value in ['yes', 'no']:
            with self.subTest(value):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'mirror-on-sync': value,
                })
                self.assertEqual(new_repo['mirror-on-sync'], value)

    @tier1
    def test_positive_create_with_default_download_policy(self):
        """Verify if the default download policy is assigned when creating a
        YUM repo without `--download-policy`

        :id: 9a3c4d95-d6ca-4377-9873-2c552b7d6ce7

        :expectedresults: YUM repository with a default download policy

        :CaseImportance: Critical
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
        """Update `immediate` download policy to `on_demand` for a newly
        created YUM repository

        :id: 1a80d686-3f7b-475e-9d1a-3e1f51d55101

        :expectedresults: immediate download policy is updated to on_demand

        :CaseImportance: Critical
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
        """Update `immediate` download policy to `background` for a newly
        created YUM repository

        :id: 7a9243eb-012c-40ad-9105-b078ed0a9eda

        :expectedresults: immediate download policy is updated to background

        :CaseImportance: Critical
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
        """Update `on_demand` download policy to `immediate` for a newly
        created YUM repository

        :id: 1e8338af-32e5-4f92-9215-bfdc1973c8f7

        :expectedresults: on_demand download policy is updated to immediate

        :CaseImportance: Critical
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
        """Update `on_demand` download policy to `background` for a newly
        created YUM repository

        :id: da600200-5bd4-4cb8-a891-37cd2233803e

        :expectedresults: on_demand download policy is updated to background

        :CaseImportance: Critical
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
        """Update `background` download policy to `immediate` for a newly
        created YUM repository

        :id: cf4dca0c-36bd-4a3c-aa29-f435ac60b3f8

        :expectedresults: background download policy is updated to immediate

        :CaseImportance: Critical
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
        """Update `background` download policy to `on_demand` for a newly
        created YUM repository

        :id: 0f943e3d-44b7-4b6e-9a7d-d33f7f4864d1

        :expectedresults: background download policy is updated to on_demand

        :CaseImportance: Critical
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

        :id: b13f8ae2-60ab-47e6-a096-d3f368e5cab3

        :expectedresults: Puppet repository is created

        :CaseImportance: Critical
        """
        url = FAKE_7_PUPPET_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url_encoded):
                new_repo = self._make_repository({
                    u'content-type': u'puppet',
                    u'url': url_encoded
                })
                self.assertEqual(new_repo['url'], url_encoded)
                self.assertEqual(new_repo['content-type'], u'puppet')

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_with_gpg_key_by_id(self):
        """Check if repository can be created with gpg key ID

        :id: 6d22f0ea-2d27-4827-9b7a-3e1550a47285

        :expectedresults: Repository is created and has gpg key

        :CaseImportance: Critical
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
    @tier1
    def test_positive_create_with_gpg_key_by_name(self):
        """Check if repository can be created with gpg key name

        :id: 95cde404-3449-410d-9a08-d7f8619a2ad5

        :expectedresults: Repository is created and has gpg key

        :BZ: 1103944

        :CaseImportance: Critical
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

        :id: faf6058c-9dd3-444c-ace2-c41791669e9e

        :expectedresults: Repository is created and is published via http

        :CaseImportance: Critical
        """
        for use_http in u'true', u'yes', u'1':
            with self.subTest(use_http):
                repo = self._make_repository({'publish-via-http': use_http})
                self.assertEqual(repo['publish-via-http'], u'yes')

    @run_only_on('sat')
    @tier1
    def test_positive_create_publish_via_https(self):
        """Create repository not published via http

        :id: 4395a5df-207c-4b34-a42d-7b3273bd68ec

        :expectedresults: Repository is created and is not published via http

        :CaseImportance: Critical
        """
        for use_http in u'false', u'no', u'0':
            with self.subTest(use_http):
                repo = self._make_repository({'publish-via-http': use_http})
                self.assertEqual(repo['publish-via-http'], u'no')

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_yum_repo_with_checksum_type(self):
        """Create a YUM repository with a checksum type

        :id: 934f4a09-2a64-485d-ae6c-8ef73aa8fb2b

        :expectedresults: A YUM repository is created and contains the correct
            checksum type

        :CaseImportance: Critical
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

        :id: 776f92eb-8b40-4efd-8315-4fbbabcb2d4e

        :expectedresults: Docker repository is created and contains correct
            values.

        :CaseImportance: Critical
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

        :id: b6a01434-8672-4196-b61a-dcb86c49f43b

        :expectedresults: Docker repository is created and contains correct
            values.

        :CaseImportance: Critical
        """
        for name in valid_docker_repository_names():
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

    @tier2
    def test_positive_create_puppet_repo_same_url_different_orgs(self):
        """Create two repos with the same URL in two different organizations.

        :id: b3502064-f400-4e60-a11f-b3772bd23a98

        :expectedresults: Repositories are created and puppet modules are
            visible from different organizations.

        :CaseLevel: Integration
        """
        url = 'https://omaciel.fedorapeople.org/b3502064/'
        # Create first repo
        repo = self._make_repository({
            u'content-type': u'puppet',
            u'url': url,
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['puppet-modules'], '1')
        # Create another org and repo
        org = make_org()
        product = make_product({'organization-id': org['id']})
        new_repo = self._make_repository({
            u'url': url,
            u'product': product,
            u'content-type': u'puppet',
        })
        Repository.synchronize({'id': new_repo['id']})
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(new_repo['content-counts']['puppet-modules'], '1')

    @tier1
    def test_negative_create_with_name(self):
        """Repository name cannot be 300-characters long

        :id: af0652d3-012d-4846-82ac-047918f74722

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({u'name': name})

    @tier1
    def test_negative_create_with_auth_url_with_special_characters(self):
        """Verify that repository URL cannot contain unquoted special characters

        :id: 2bd5ee17-0fe5-43cb-9cdc-dc2178c5374c

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        # get a list of valid credentials without quoting them
        for cred in [
            creds for creds in valid_http_credentials()
            if creds['quote'] is True
        ]:
            url_encoded = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
            with self.subTest(url_encoded):
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({u'url': url_encoded})

    @tier1
    def test_negative_create_with_auth_url_too_long(self):
        """Verify that repository URL length is limited

        :id: de356c66-4237-4421-89e3-f4f8bbe6f526

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        for cred in invalid_http_credentials():
            url_encoded = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
            with self.subTest(url_encoded):
                with self.assertRaises(CLIFactoryError):
                    self._make_repository({u'url': url_encoded})

    @tier1
    def test_negative_create_with_invalid_download_policy(self):
        """Verify that YUM repository cannot be created with invalid download
        policy

        :id: 3b143bf8-7056-4c94-910d-69a451071f26

        :expectedresults: YUM repository is not created with invalid download
            policy

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIFactoryError):
            self._make_repository({
                u'content-type': u'yum',
                u'download-policy': gen_string('alpha', 5)
            })

    @tier1
    def test_negative_update_to_invalid_download_policy(self):
        """Verify that YUM repository cannot be updated to invalid download
        policy

        :id: 5bd6a2e4-7ff0-42ac-825a-6b2a2f687c89

        :expectedresults: YUM repository is not updated to invalid download
            policy

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            new_repo = self._make_repository({u'content-type': u'yum'})
            Repository.update({
                u'id': new_repo['id'],
                u'download-policy': gen_string('alpha', 5)
            })

    @tier1
    @skip_if_bug_open('bugzilla', 1654944)
    def test_negative_create_non_yum_with_download_policy(self):
        """Verify that non-YUM repositories cannot be created with download
        policy

        :id: 71388973-50ea-4a20-9406-0aca142014ca

        :expectedresults: Non-YUM repository is not created with a download
            policy

        :BZ: 1439835

        :CaseImportance: Critical
        """
        os_version = get_host_os_version()
        # ostree is not supported for rhel6 so the following check
        if os_version.startswith('RHEL6'):
            non_yum_repo_types = [
                item for item in REPO_TYPE.keys()
                if item != 'yum' and item != 'ostree'
            ]
        else:
            non_yum_repo_types = [
                item for item in REPO_TYPE.keys() if item != 'yum'
            ]
        for content_type in non_yum_repo_types:
            with self.subTest(content_type):
                with self.assertRaisesRegex(
                    CLIFactoryError,
                    u'Download policy Cannot set attribute '
                    'download_policy for content type'
                ):
                    self._make_repository({
                        u'content-type': content_type,
                        u'download-policy': u'on_demand'
                    })

    @run_only_on('sat')
    @tier1
    def test_positive_synchronize_yum_repo(self):
        """Check if repository can be created and synced

        :id: e3a62529-edbd-4062-9246-bef5f33bdcf0

        :expectedresults: Repository is created and synced

        :CaseLevel: Integration
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
    @tier1
    def test_positive_synchronize_file_repo(self):
        """Check if repository can be created and synced

        :id: eafc421d-153e-41e1-afbd-938e556ef827

        :expectedresults: Repository is created and synced

        :CaseLevel: Integration
        """
        new_repo = self._make_repository({
            u'content-type': u'file',
            u'url': CUSTOM_FILE_REPO,
        })
        # Assertion that repo is not yet synced
        self.assertEqual(new_repo['sync']['status'], 'Not Synced')
        # Synchronize it
        Repository.synchronize({'id': new_repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(new_repo['sync']['status'], 'Success')
        self.assertEqual(
            int(new_repo['content-counts']['files']),
            CUSTOM_FILE_REPO_FILES_COUNT
        )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_synchronize_auth_yum_repo(self):
        """Check if secured repository can be created and synced

        :id: b0db676b-e0f0-428c-adf3-1d7c0c3599f0

        :expectedresults: Repository is created and synced

        :BZ: 1328092

        :CaseLevel: Integration
        """
        url = FAKE_5_YUM_REPO
        for creds in [
            cred for cred in valid_http_credentials(url_encoded=True)
            if cred['http_valid']
        ]:
            url_encoded = url.format(
                creds['login'], creds['pass']
            )
            with self.subTest(url_encoded):
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
    def test_negative_synchronize_auth_yum_repo(self):
        """Check if secured repo fails to synchronize with invalid credentials

        :id: 809905ae-fb76-465d-9468-1f99c4274aeb

        :expectedresults: Repository is created but synchronization fails

        :BZ: 1405503, 1453118

        :CaseLevel: Integration
        """
        url = FAKE_5_YUM_REPO
        for creds in [
            cred for cred in valid_http_credentials(url_encoded=True)
            if not cred['http_valid']
        ]:
            url_encoded = url.format(
                creds['login'], creds['pass']
            )
            with self.subTest(url_encoded):
                new_repo = self._make_repository({
                    u'content-type': u'yum',
                    u'url': url_encoded,
                })
                # Try to synchronize it
                repo_sync = Repository.synchronize(
                    {'id': new_repo['id'], u'async': True}
                )
                response = Task.progress(
                    {u'id': repo_sync[0]['id']}, return_raw_response=True)
                if creds['original_encoding'] == 'utf8':
                    self.assertIn(
                        (u"Error retrieving metadata: 'latin-1' codec can't"
                         u" encode characters"),
                        ''.join(response.stderr)
                    )
                else:
                    self.assertIn(
                        u'Error retrieving metadata: Unauthorized',
                        ''.join(response.stderr)
                    )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_synchronize_auth_puppet_repo(self):
        """Check if secured puppet repository can be created and synced

        :id: 1d2604fc-8a18-4cbe-bf4c-5c7d9fbdb82c

        :expectedresults: Repository is created and synced

        :BZ: 1405503

        :CaseLevel: Integration
        """
        url = FAKE_7_PUPPET_REPO
        for creds in [
            cred for cred in valid_http_credentials(url_encoded=True)
            if cred['http_valid']
        ]:
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url_encoded):
                new_repo = self._make_repository({
                    u'content-type': u'puppet',
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
    @upgrade
    def test_positive_synchronize_docker_repo(self):
        """Check if Docker repository can be created and synced

        :id: cb9ae788-743c-4785-98b2-6ae0c161bc9a

        :expectedresults: Docker repository is created and synced

        :CaseLevel: Integration
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
    @tier2
    @upgrade
    def test_positive_synchronize_docker_repo_with_tags_whitelist(self):
        """Check if only whitelisted tags are synchronized

        :id: aa820c65-2de1-4b32-8890-98bd8b4320dc

        :expectedresults: Only whitelisted tag is synchronized
        """
        tags = 'latest'
        repo = self._make_repository({
            'content-type': 'docker',
            'docker-upstream-name': 'alpine',
            'url': DOCKER_REGISTRY_HUB,
            'docker-tags-whitelist': tags,
        })
        Repository.synchronize({'id': repo['id']})
        repo = self._validated_image_tags_count(repo=repo)
        self.assertIn(tags, repo['container-image-tags-filter'])
        self.assertEqual(int(repo['content-counts']['container-image-tags']), 1)

    @run_only_on('sat')
    @tier2
    def test_positive_synchronize_docker_repo_set_tags_later(self):
        """Verify that adding tags whitelist and re-syncing after
        synchronizing full repository doesn't remove content that was
        already pulled in

        :id: 97f2087f-6041-4242-8b7c-be53c68f46ff

        :expectedresults: Non-whitelisted tags are not removed
        """
        tags = 'latest'
        repo = self._make_repository({
            'content-type': 'docker',
            'docker-upstream-name': 'hello-world',
            'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': repo['id']})
        repo = self._validated_image_tags_count(repo=repo)
        self.assertFalse(repo['container-image-tags-filter'])
        self.assertGreaterEqual(int(repo['content-counts']
                                    ['container-image-tags']), 2)
        Repository.update({
            'id': repo['id'],
            'docker-tags-whitelist': tags,
        })
        Repository.synchronize({'id': repo['id']})
        repo = self._validated_image_tags_count(repo=repo)
        self.assertIn(tags, repo['container-image-tags-filter'])
        self.assertGreaterEqual(int(repo['content-counts']
                                    ['container-image-tags']), 2)

    @run_only_on('sat')
    @tier2
    def test_negative_synchronize_docker_repo_with_mix_valid_invalid_tags(self):
        """Set tags whitelist to contain both valid and invalid (non-existing)
        tags. Check if only whitelisted tags are synchronized

        :id: 75668da8-cc94-4d39-ade1-d3ef91edc812

        :expectedresults: Only whitelisted tag is synchronized
        """
        tags = ['latest', gen_string('alpha')]
        repo = self._make_repository({
            'content-type': 'docker',
            'docker-upstream-name': 'alpine',
            'url': DOCKER_REGISTRY_HUB,
            'docker-tags-whitelist': ",".join(tags),
        })
        Repository.synchronize({'id': repo['id']})
        repo = self._validated_image_tags_count(repo=repo)
        [self.assertIn(tag, repo['container-image-tags-filter']) for tag in tags]
        self.assertEqual(int(repo['content-counts']['container-image-tags']), 1)

    @run_only_on('sat')
    @tier2
    def test_negative_synchronize_docker_repo_with_invalid_tags(self):
        """Set tags whitelist to contain only invalid (non-existing)
        tags. Check that no data is synchronized.

        :id: da05cdb1-2aea-48b9-9424-6cc700bc1194

        :expectedresults: Tags are not synchronized
        """
        tags = [gen_string('alpha') for _ in range(3)]
        repo = self._make_repository({
            'content-type': 'docker',
            'docker-upstream-name': 'alpine',
            'url': DOCKER_REGISTRY_HUB,
            'docker-tags-whitelist': ",".join(tags),
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        [self.assertIn(tag, repo['container-image-tags-filter']) for tag in tags]
        self.assertEqual(int(repo['content-counts']['container-image-tags']), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_resynchronize_rpm_repo(self):
        """Check that repository content is resynced after packages were
        removed from repository

        :id: a21b6710-4f12-4722-803e-3cb29d70eead

        :expectedresults: Repository has updated non-zero packages count

        :BZ: 1459845, 1459874

        :CaseLevel: Integration

        :BZ: 1318004
        """
        # Create repository and synchronize it
        repo = self._make_repository({
            u'content-type': u'yum',
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['packages'], '32')
        # Find repo packages and remove them
        packages = Package.list({'repository-id': repo['id']})
        Repository.remove_content({
            'id': repo['id'],
            'ids': [package['id'] for package in packages],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['packages'], '0')
        # Re-synchronize repository
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['packages'], '32')

    @run_only_on('sat')
    @tier2
    def test_positive_resynchronize_puppet_repo(self):
        """Check that repository content is resynced after puppet modules
        were removed from repository

        :id: 9e28f0ae-3875-4c1e-ad8b-d068f4409fe3

        :expectedresults: Repository has updated non-zero puppet modules count

        :BZ: 1459845

        :CaseLevel: Integration

        :BZ: 1318004
        """
        # Create repository and synchronize it
        repo = self._make_repository({
            u'content-type': u'puppet',
            u'url': FAKE_1_PUPPET_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['puppet-modules'], '2')
        # Find repo packages and remove them
        modules = PuppetModule.list({'repository-id': repo['id']})
        Repository.remove_content({
            'id': repo['id'],
            'ids': [module['id'] for module in modules],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['puppet-modules'], '0')
        # Re-synchronize repository
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['puppet-modules'], '2')

    @run_only_on('sat')
    @tier2
    def test_positive_synchronize_rpm_repo_ignore_content(self):
        """Synchronize yum repository with ignore content setting

        :id: fa32ff10-e2e2-4ee0-b444-82f66f4a0e96

        :expectedresults: Selected content types are ignored during
            synchronization

        :BZ: 1591358

        :CaseLevel: Integration

        """
        # Create repository and synchronize it
        repo = self._make_repository({
            'content-type': 'yum',
            'url': FAKE_YUM_MIXED_REPO,
            'ignorable-content': ['erratum', 'srpm', 'drpm'],
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        # Check synced content types
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['packages'], '5',
                         'content not synced correctly')
        self.assertEqual(repo['content-counts']['errata'], '0',
                         'content not ignored correctly')
        if not bz_bug_is_open(1335621):
            self.assertEqual(repo['content-counts']['source-rpms'], '0',
                             'content not ignored correctly')
        # drpm check requires a different method
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.org['label'],
                self.product['label'],
                repo['label'],
            )
        )
        # expecting No such file or directory for drpms
        self.assertEqual(result.return_code, 1)
        self.assertIn('No such file or directory', result.stderr)

        # Find repo packages and remove them
        packages = Package.list({'repository-id': repo['id']})
        Repository.remove_content({
            'id': repo['id'],
            'ids': [package['id'] for package in packages],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['packages'], '0')

        # Update the ignorable-content setting
        Repository.update({
            'id': repo['id'],
            'ignorable-content': ['rpm'],
        })

        # Re-synchronize repository
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        # Re-check synced content types
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['packages'], '0',
                         'content not ignored correctly')
        self.assertEqual(repo['content-counts']['errata'], '2',
                         'content not synced correctly')
        if not bz_bug_is_open(1664549):
            self.assertEqual(repo['content-counts']['source-rpms'], '3',
                             'content not synced correctly')
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
        self.assertGreaterEqual(len(result.stdout), 4,
                                'content not synced correctly')

    @run_only_on('sat')
    @tier1
    def test_positive_update_url(self):
        """Update the original url for a repository

        :id: 1a2cf29b-5c30-4d4c-b6d1-2f227b0a0a57

        :expectedresults: Repository url is updated

        :CaseImportance: Critical
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

        :id: 566553b2-d077-4fd8-8ed5-00ba75355386

        :expectedresults: Repository url not updated

        :CaseImportance: Critical
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

        :id: a703de60-8631-4e31-a9d9-e51804f27f03

        :expectedresults: Repository url not updated

        :CaseImportance: Critical
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

        :id: 367ff375-4f52-4a8c-b974-8c1c54e3fdd3

        :expectedresults: Repository gpg key is updated

        :CaseImportance: Critical
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

    @tier1
    def test_positive_update_mirror_on_sync(self):
        """Update the mirror on sync rule for repository

        :id: 9bab2537-3223-40d7-bc4c-a51b09d2e812

        :expectedresults: Repository is updated

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({u'mirror-on-sync': 'no'})
        Repository.update({
            u'id': new_repo['id'],
            u'mirror-on-sync': 'yes',
        })
        result = Repository.info({'id': new_repo['id']})
        self.assertEqual(result['mirror-on-sync'], 'yes')

    @run_only_on('sat')
    @tier1
    def test_positive_update_publish_method(self):
        """Update the original publishing method

        :id: e7bd2667-4851-4a64-9c70-1b5eafbc3f71

        :expectedresults: Repository publishing method is updated

        :CaseImportance: Critical
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

        :id: 42f14257-d860-443d-b337-36fd355014bc

        :expectedresults: A YUM repository is updated and contains the correct
            checksum type

        :CaseImportance: Critical
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

        :id: bcf096db-0033-4138-90a3-cb7355d5dfaf

        :expectedresults: Repository is created and then deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({u'name': name})
                Repository.delete({u'id': new_repo['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Repository.info({u'id': new_repo['id']})

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete_by_name(self):
        """Check if repository can be created and deleted

        :id: 463980a4-dbcf-4178-83a6-1863cf59909a

        :expectedresults: Repository is created and then deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({u'name': name})
                Repository.delete({
                    'name': new_repo['name'],
                    'product-id': self.product['id']
                })
                with self.assertRaises(CLIReturnCodeError):
                    Repository.info({u'id': new_repo['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_delete_rpm(self):
        """Check if rpm repository with packages can be deleted.

        :id: 1172492f-d595-4c8e-89c1-fabb21eb04ac

        :expectedresults: Repository is deleted.

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({
            u'content-type': u'yum', u'url': FAKE_1_YUM_REPO})
        Repository.synchronize({'id': new_repo['id']})
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(new_repo['sync']['status'], 'Success')
        # Check that there is at least one package
        self.assertGreater(int(new_repo['content-counts']['packages']), 0)
        Repository.delete({u'id': new_repo['id']})
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({u'id': new_repo['id']})

    @run_only_on('sat')
    @tier1
    def test_positive_delete_puppet(self):
        """Check if puppet repository with puppet modules can be deleted.

        :id: 83d92454-11b7-4f9a-952d-650ffe5135e4

        :expectedresults: Repository is deleted.

        :BZ: 1316681

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({
            u'content-type': u'puppet', u'url': FAKE_1_PUPPET_REPO})
        Repository.synchronize({'id': new_repo['id']})
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(new_repo['sync']['status'], 'Success')
        # Check that there is at least one puppet module
        self.assertGreater(
            int(new_repo['content-counts']['puppet-modules']), 0)
        Repository.delete({u'id': new_repo['id']})
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({u'id': new_repo['id']})

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_remove_content_by_repo_name(self):
        """Synchronize repository and remove rpm content from using repo name

        :id: a8b6f17d-3b13-4185-920a-2558ace59458

        :expectedresults: Content Counts shows zero packages

        :BZ: 1349646, 1413145, 1459845, 1459874

        :CaseImportance: Critical
        """
        # Create repository and synchronize it
        repo = self._make_repository({
            'content-type': u'yum',
            'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({
            'name': repo['name'],
            'product': self.product['name'],
            'organization': self.org['name']
        })
        repo = Repository.info({
            'name': repo['name'],
            'product': self.product['name'],
            'organization': self.org['name']
        })
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['packages'], '32')
        # Find repo packages and remove them
        packages = Package.list({
            'repository': repo['name'],
            'product': self.product['name'],
            'organization': self.org['name'],
        })
        Repository.remove_content({
            'name': repo['name'],
            'product': self.product['name'],
            'organization': self.org['name'],
            'ids': [package['id'] for package in packages],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['packages'], '0')

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_remove_content_rpm(self):
        """Synchronize repository and remove rpm content from it

        :id: c4bcda0e-c0d6-424c-840d-26684ca7c9f1

        :expectedresults: Content Counts shows zero packages

        :BZ: 1459845, 1459874

        :CaseImportance: Critical
        """
        # Create repository and synchronize it
        repo = self._make_repository({
            u'content-type': u'yum',
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['packages'], '32')
        # Find repo packages and remove them
        packages = Package.list({'repository-id': repo['id']})
        Repository.remove_content({
            'id': repo['id'],
            'ids': [package['id'] for package in packages],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['packages'], '0')

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_remove_content_puppet(self):
        """Synchronize repository and remove puppet content from it

        :id: b025ccd0-9beb-4ac0-9fbf-21340c90650e

        :expectedresults: Content Counts shows zero puppet modules

        :BZ: 1459845

        :CaseImportance: Critical
        """
        # Create repository and synchronize it
        repo = self._make_repository({
            u'content-type': u'puppet',
            u'url': FAKE_1_PUPPET_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['puppet-modules'], '2')
        # Find puppet modules and remove them from repository
        modules = PuppetModule.list({'repository-id': repo['id']})
        Repository.remove_content({
            'id': repo['id'],
            'ids': [module['id'] for module in modules],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['puppet-modules'], '0')

    @tier1
    def test_positive_upload_content(self):
        """Create repository and upload content

        :id: eb0ec599-2bf1-483a-8215-66652f948d67

        :expectedresults: upload content is successful

        :BZ: 1343006

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({'name': gen_string('alpha')})
        ssh.upload_file(
            local_file=get_data_file(RPM_TO_UPLOAD),
            remote_file="/tmp/{0}".format(RPM_TO_UPLOAD)
        )
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

    @tier1
    def test_positive_upload_content_to_file_repo(self):
        """Create file repository and upload content to it

        :id: 5e24b416-2928-4533-96cf-6bffbea97a95

        :customerscenario: true

        :expectedresults: upload content operation is successful

        :BZ: 1446975

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({
            u'content-type': u'file',
            u'url': CUSTOM_FILE_REPO,
        })
        Repository.synchronize({'id': new_repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            int(new_repo['content-counts']['files']),
            CUSTOM_FILE_REPO_FILES_COUNT
        )
        ssh.upload_file(
            local_file=get_data_file(OS_TEMPLATE_DATA_FILE),
            remote_file="/tmp/{0}".format(OS_TEMPLATE_DATA_FILE)
        )
        result = Repository.upload_content({
            'name': new_repo['name'],
            'organization': new_repo['organization'],
            'path': "/tmp/{0}".format(OS_TEMPLATE_DATA_FILE),
            'product-id': new_repo['product']['id'],
        })
        self.assertIn(
            "Successfully uploaded file '{0}'".format(OS_TEMPLATE_DATA_FILE),
            result[0]['message'],
        )
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(
            int(new_repo['content-counts']['files']),
            CUSTOM_FILE_REPO_FILES_COUNT + 1
        )

    @skip_if_bug_open('bugzilla', 1436209)
    @run_only_on('sat')
    @tier2
    def test_negative_restricted_user_cv_add_repository(self):
        """Attempt to add a product repository to content view with a
        restricted user, using product name not visible to restricted user.

        :id: 65792ae0-c5be-4a6c-9062-27dc03b83e10

        :BZ: 1436209

        :Steps:
            1. Setup a restricted user with permissions that filter the
               products with names like Test_* or "rhel7*"
            2. Create a content view
            3. Create a product with name that should not be visible to the
               user and add a repository to it

        :expectedresults:
            1. The admin user can view the product repository
            2. The restricted user cannot view the product repository
            3. The restricted user cannot add the product repository to a
               content view
            4. After the attempt of adding the product repository to content
               view, assert that the restricted user still cannot view the
               product repository.

        :CaseLevel: Integration
        """
        required_permissions = {
            'Katello::Product': (
                [
                    'view_products',
                    'create_products',
                    'edit_products',
                    'destroy_products',
                    'sync_products',
                    'export_products'
                ],
                'name ~ "Test_*" || name ~ "rhel7*"'
            ),
            'Katello::ContentView': (
                [
                    'view_content_views',
                    'create_content_views',
                    'edit_content_views',
                    'destroy_content_views',
                    'publish_content_views',
                    'promote_or_remove_content_views',
                    'export_content_views'
                ],
                'name ~ "Test_*" || name ~ "rhel7*"'
            ),
            'Organization': (
                [
                    'view_organizations',
                    'create_organizations',
                    'edit_organizations',
                    'destroy_organizations',
                    'assign_organizations'
                ], None
            )
        }
        user_name = gen_alphanumeric()
        user_password = gen_alphanumeric()
        # Generate a product name that is not like Test_* or rhel7*
        product_name = 'zoo_{0}'.format(gen_string('alpha', 20))
        # Generate a content view name like Test_*
        content_view_name = 'Test_{0}'.format(gen_string('alpha', 20))
        # Create an organization
        org = make_org()
        # Create a non admin user, for the moment without any permissions
        user = make_user({
            'admin': False,
            'default-organization-id': org['id'],
            'organization-ids': [org['id']],
            'login': user_name,
            'password': user_password,
        })
        # Create a new role
        role = make_role()
        # Get the available permissions
        available_permissions = Filter.available_permissions()
        # group the available permissions by resource type
        available_rc_permissions = {}
        for permission in available_permissions:
            permission_resource = permission['resource']
            if permission_resource not in available_rc_permissions:
                available_rc_permissions[permission_resource] = []
            available_rc_permissions[permission_resource].append(permission)
        # create only the required role permissions per resource type
        for resource_type, permission_data in required_permissions.items():
            permission_names, search = permission_data
            # assert that the required resource type is available
            self.assertIn(resource_type, available_rc_permissions)
            available_permission_names = [
                permission['name']
                for permission in available_rc_permissions[resource_type]
                if permission['name'] in permission_names
                ]
            # assert that all the required permissions are available
            self.assertEqual(set(permission_names),
                             set(available_permission_names))
            # Create the current resource type role permissions
            make_filter({
                'role-id': role['id'],
                'permissions': permission_names,
                'search': search,
            })
        # Add the created and initiated role with permissions to user
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # assert that the user is not an admin one and cannot read the current
        # role info (note: view_roles is not in the required permissions)
        with self.assertRaises(CLIReturnCodeError) as context:
            Role.with_user(user_name, user_password).info(
                {'id': role['id']})
        self.assertIn(
            'Forbidden - server refused to process the request',
            context.exception.stderr
        )
        # Create a product
        product = make_product(
            {'organization-id': org['id'], 'name': product_name})
        # Create a yum repository and synchronize
        repo = make_repository({
            'product-id': product['id'],
            'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': repo['id']})
        # Create a content view
        content_view = make_content_view(
            {'organization-id': org['id'], 'name': content_view_name})
        # assert that the user can read the content view info as per required
        # permissions
        user_content_view = ContentView.with_user(
            user_name, user_password).info({'id': content_view['id']})
        # assert that this is the same content view
        self.assertEqual(content_view['name'], user_content_view['name'])
        # assert admin user is able to view the product
        repos = Repository.list({'organization-id': org['id']})
        self.assertEqual(len(repos), 1)
        # assert that this is the same repo
        self.assertEqual(repos[0]['id'], repo['id'])
        # assert that restricted user is not able to view the product
        repos = Repository.with_user(user_name, user_password).list(
            {'organization-id': org['id']})
        self.assertEqual(len(repos), 0)
        # assert that the user cannot add the product repo to content view
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user_name, user_password).add_repository({
                'id': content_view['id'],
                'organization-id': org['id'],
                'repository-id': repo['id'],
            })
        # assert that restricted user still not able to view the product
        repos = Repository.with_user(user_name, user_password).list(
            {'organization-id': org['id']})
        self.assertEqual(len(repos), 0)

    @skip_if_bug_open('bugzilla', 1378442)
    @tier1
    def test_positive_upload_content_srpm(self):
        """Create repository and upload a SRPM content

        :id: 706dc3e2-dacb-4fdd-8eef-5715ce498888

        :expectedresults: File successfully uploaded

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({'name': gen_string('alpha', 15)})
        ssh.upload_file(
            local_file=get_data_file(SRPM_TO_UPLOAD),
            remote_file="/tmp/{0}".format(SRPM_TO_UPLOAD)
        )
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

    @tier1
    def test_positive_create_get_update_delete_module_streams(self):
        """Check module-stream get for each create, get, update, delete.

        :id: e9001f76-9bc7-42a7-b8c9-2dccd5bf0b1f2f2e70b8-e446-4a28-9bae-fc870c80e83e

        :Setup:
            1. valid yum repo with Module Streams.
        :Steps:
            1. Create Yum Repository with url contain module-streams
            2. Initialize synchronization
            3. Another Repository with same Url
            4. Module-Stream Get
            5. Update the Module-Stream
            6. Module-Stream Get
            7. Delete Module-Stream
            8. Module-Stream Get

        :expectedresults: yum repository with modules is synced,
         shows correct count and details with create, update, delete and
         even duplicate repositories.

        :CaseAutomation: automated
        """
        org = make_org()
        # Create a product
        product = make_product(
            {'organization-id': org['id']})
        repo = make_repository({
            'product-id': product['id'],
            u'content-type': u'yum',
            u'url': CUSTOM_MODULE_STREAM_REPO_2,
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['module-streams'], '7',
                         'Module Streams not synced correctly')

        # adding repo with same yum url should not change count.
        duplicate_repo = make_repository({
            'product-id': product['id'],
            u'content-type': u'yum',
            u'url': CUSTOM_MODULE_STREAM_REPO_2,
        })
        Repository.synchronize({'id': duplicate_repo['id']})

        module_streams = ModuleStream.list({'organization-id': org['id']})
        self.assertEqual(len(module_streams), 7,
                         'Module Streams get worked correctly')
        Repository.update({
            'product-id': product['id'],
            u'id': repo['id'],
            u'url': CUSTOM_MODULE_STREAM_REPO_2,
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['module-streams'], '7',
                         'Module Streams not synced correctly')

        Repository.delete({'id': repo['id']})
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({u'id': repo['id']})

    @tier1
    def test_module_stream_list_validation(self):
        """Check module-stream get with list on hammer.

         :id: 9842a0c3-8532-4b16-a00a-534fc3b0a776ff89f23e-cd00-4d20-84d3-add0ea24abf8

         :Setup:
             1. valid yum repo with Module Streams.
         :Steps:
             1. Create Yum Repositories with url contain module-streams and Products
             2. Initialize synchronization
             3. Verify the module-stream list with various inputs options

         :expectedresults: Verify the module-stream list response.

         :CaseAutomation: automated
         """
        repo1 = self._make_repository({
            u'content-type': u'yum',
            u'url': CUSTOM_MODULE_STREAM_REPO_1,
        })
        Repository.synchronize({'id': repo1['id']})
        product2 = make_product_wait(
            {u'organization-id': self.org['id']},
        )
        repo2 = self._make_repository({
            u'content-type': u'yum',
            u'url': CUSTOM_MODULE_STREAM_REPO_2,
            u'product-id': product2['id']
        })
        Repository.synchronize({'id': repo2['id']})
        module_streams = ModuleStream.list()
        self.assertGreater(len(module_streams), 11,
                           'Module Streams get worked correctly')
        module_streams = ModuleStream.list({'product-id': product2['id']})
        self.assertEqual(len(module_streams), 7,
                         'Module Streams get worked correctly')

    @tier1
    def test_module_stream_info_validation(self):
        """Check module-stream get with info on hammer.

         :id: ddbeb49e-d292-4dc4-8fb9-e9b768acc441a2c2e797-02b7-4b12-9f95-cffc93254198

         :Setup:
             1. valid yum repo with Module Streams.
         :Steps:
             1. Create Yum Repositories with url contain module-streams
             2. Initialize synchronization
             3. Verify the module-stream info with various inputs options

         :expectedresults: Verify the module-stream info response.

         :CaseAutomation: automated
         """
        product2 = make_product_wait(
            {u'organization-id': self.org['id']},
        )
        repo2 = self._make_repository({
            u'content-type': u'yum',
            u'url': CUSTOM_MODULE_STREAM_REPO_2,
            u'product-id': product2['id']
        })
        Repository.synchronize({'id': repo2['id']})
        module_streams = ModuleStream.list({
            'repository-id': repo2['id'],
            'search': 'name="walrus" and stream="5.21"'
        })
        actual_result = ModuleStream.info({u'id': module_streams[0]['id']})
        expected_result = {
            'module-stream-name': 'walrus',
            'stream': '5.21',
            'architecture': 'x86_64',
         }
        self.assertEqual(
            expected_result,
            {key: value for key, value in actual_result.items() if key in expected_result}
        )


class OstreeRepositoryTestCase(CLITestCase):
    """Ostree Repository CLI tests."""

    @classmethod
    @skip_if_bug_open('bugzilla', 1439835)
    @skip_if_os('RHEL6')
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(OstreeRepositoryTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({u'organization-id': cls.org['id']})

    def _make_repository(self, options=None):
        """Makes a new repository and asserts its success"""
        if options is None:
            options = {}

        if options.get('product-id') is None:
            options[u'product-id'] = self.product['id']

        return make_repository(options)

    @tier1
    def test_positive_create_ostree_repo(self):
        """Create a ostree repository

        :id: a93c52e1-b32e-4590-981b-636ae8b8314d

        :expectedresults: ostree repository is created

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_repo = self._make_repository({
                    u'name': name,
                    u'content-type': u'ostree',
                    u'publish-via-http': u'false',
                    u'url': FEDORA27_OSTREE_REPO,
                })
                self.assertEqual(new_repo['name'], name)
                self.assertEqual(new_repo['content-type'], u'ostree')

    @tier1
    @skip_if_bug_open('bugzilla', 1370108)
    def test_negative_create_ostree_repo_with_checksum(self):
        """Create a ostree repository with checksum type

        :id: a334e0f7-e1be-4add-bbf2-2fd9f0b982c4

        :expectedresults: Validation error is raised

        :CaseImportance: Critical
        """
        for checksum_type in u'sha1', u'sha256':
            with self.subTest(checksum_type):
                with self.assertRaisesRegex(
                    CLIFactoryError,
                    u'Validation failed: Checksum type cannot be set for '
                    'non-yum repositories'
                ):
                    self._make_repository({
                        u'content-type': u'ostree',
                        u'checksum-type': checksum_type,
                        u'publish-via-http': u'false',
                        u'url': FEDORA27_OSTREE_REPO,
                    })

    @tier1
    def test_negative_create_unprotected_ostree_repo(self):
        """Create a ostree repository and published via http

        :id: 2b139560-65bb-4a40-9724-5cca57bd8d30

        :expectedresults: ostree repository is not created

        :CaseImportance: Critical
        """
        for use_http in u'true', u'yes', u'1':
            with self.subTest(use_http):
                with self.assertRaisesRegex(
                    CLIFactoryError,
                    u'Validation failed: OSTree Repositories cannot be '
                    'unprotected'
                ):
                    self._make_repository({
                        u'content-type': u'ostree',
                        u'publish-via-http': u'true',
                        u'url': FEDORA27_OSTREE_REPO,
                    })

    @tier2
    @upgrade
    def test_positive_synchronize_ostree_repo(self):
        """Synchronize ostree repo

        :id: 64fcae0a-44ae-46ae-9938-032bba1331e9

        :expectedresults: Ostree repository is created and synced

        :CaseLevel: Integration
        """
        new_repo = self._make_repository({
            u'content-type': u'ostree',
            u'publish-via-http': u'false',
            u'url': FEDORA27_OSTREE_REPO,
        })
        # Synchronize it
        Repository.synchronize({'id': new_repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': new_repo['id']})
        self.assertEqual(new_repo['sync']['status'], 'Success')

    @tier1
    def test_positive_delete_ostree_by_name(self):
        """Delete Ostree repository by name

        :id: 0b545c22-acff-47b6-92ff-669b348f9fa6

        :expectedresults: Repository is deleted by name

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({
            u'content-type': u'ostree',
            u'publish-via-http': u'false',
            u'url': FEDORA27_OSTREE_REPO,
        })
        Repository.delete({
            u'name': new_repo['name'],
            u'product': new_repo['product']['name'],
            u'organization': new_repo['organization']
        })
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({u'name': new_repo['name']})

    @tier1
    @upgrade
    def test_positive_delete_ostree_by_id(self):
        """Delete Ostree repository by id

        :id: 171917f5-1a1b-440f-90c7-b8418f1da132

        :expectedresults: Repository is deleted by id

        :CaseImportance: Critical
        """
        new_repo = self._make_repository({
            u'content-type': u'ostree',
            u'publish-via-http': u'false',
            u'url': FEDORA27_OSTREE_REPO,
        })
        Repository.delete({u'id': new_repo['id']})
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({u'id': new_repo['id']})


class SRPMRepositoryTestCase(CLITestCase):
    """Tests specific to using repositories containing source RPMs."""

    @classmethod
    @skip_if_bug_open('bugzilla', 1378442)
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(SRPMRepositoryTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({'organization-id': cls.org['id']})

    @tier2
    def test_positive_sync(self):
        """Synchronize repository with SRPMs

        :id: eb69f840-122d-4180-b869-1bd37518480c

        :expectedresults: srpms can be listed in repository
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

        :id: 78cd6345-9c6c-490a-a44d-2ad64b7e959b

        :expectedresults: srpms can be listed in content view
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
    @upgrade
    def test_positive_sync_publish_promote_cv(self):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: 3d197118-b1fa-456f-980e-ad1a517bc769

        :expectedresults: srpms can be listed in content view in proper
            lifecycle environment
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
    @skip_if_bug_open('bugzilla', 1378442)
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(DRPMRepositoryTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({'organization-id': cls.org['id']})

    @tier2
    def test_positive_sync(self):
        """Synchronize repository with DRPMs

        :id: a645966c-750b-40ef-a264-dc3bb632b9fd

        :expectedresults: drpms can be listed in repository
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

        :id: 014bfc80-4622-422e-a0ec-755b1d9f845e

        :expectedresults: drpms can be listed in content view
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
    @upgrade
    def test_positive_sync_publish_promote_cv(self):
        """Synchronize repository with DRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: a01cb12b-d388-4902-8532-714f4e28ec56

        :expectedresults: drpms can be listed in content view in proper
            lifecycle environment
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

    @stubbed()
    @tier2
    def test_positive_git_local_create(self):
        """Create repository with local git puppet mirror.

        :id: 89211cd5-82b8-4391-b729-a7502e57f824

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Create link to local puppet mirror via cli

        :expectedresults: Content source containing local GIT puppet mirror
            content is created

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_local_update(self):
        """Update repository with local git puppet mirror.

        :id: 341f40f2-3501-4754-9acf-7cda1a61f7db

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Modify details for existing puppet repo (name, etc.) via cli

        :expectedresults: Content source containing local GIT puppet mirror
            content is modified

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_git_local_delete(self):
        """Delete repository with local git puppet mirror.

        :id: a243f5bb-5186-41b3-8e8a-07d5cc784ccd

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Delete link to local puppet mirror via cli

        :expectedresults: Content source containing local GIT puppet mirror
            content no longer exists/is available.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_remote_create(self):
        """Create repository with remote git puppet mirror.

        :id: 8582529f-3112-4b49-8d8f-f2bbf7dceca7

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps: Create link to local puppet mirror via cli

        :expectedresults: Content source containing remote GIT puppet mirror
            content is created

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_remote_update(self):
        """Update repository with remote git puppet mirror.

        :id: 582c50b3-3b90-4244-b694-97642b1b13a9

        :CaseLevel: Integration

        :Setup: Assure remote  GIT puppet has been created and found by pulp

        :Steps: modify details for existing puppet repo (name, etc.) via cli

        :expectedresults: Content source containing remote GIT puppet mirror
            content is modified

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_git_remote_delete(self):
        """Delete repository with remote git puppet mirror.

        :id: 0a23f969-b202-4c6c-b12e-f651a0b7d049

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps: Delete link to remote puppet mirror via cli

        :expectedresults: Content source containing remote GIT puppet mirror
            content no longer exists/is available.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_sync(self):
        """Sync repository with git puppet mirror.

        :id: a46c16bd-0986-48db-8e62-aeb3907ba4d2

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to sync content from mirror via cli

        :expectedresults: Content is pulled down without error

        :expectedresults: Confirmation that various resources actually exist in
            local content repo

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_git_sync_with_content_change(self):
        """Sync repository with changes in git puppet mirror.
        If module changes in GIT mirror but the version in manifest
        does not change, content still pulled.

        :id: 7d9519ca-8660-4014-8e0e-836594891c0c

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps:
            1.  Sync a git repo and observe the contents/checksum etc. of an
                existing puppet module
            2.  Assure a puppet module in git repo has changed but the manifest
                version for this module does not change.
            3.  Using pulp script, update repo mirror and re-sync within
                satellite
            4.  View contents/details of same puppet module

        :expectedresults: Puppet module has been updated in our content, even
            though the module's version number has not changed.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_sync_schedule(self):
        """Scheduled sync of git puppet mirror.

        :id: 0d58d180-9836-4524-b608-66b67f9cab12

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to create a scheduled sync content from mirror, via cli

        :expectedresults: Content is pulled down without error  on expected
            schedule

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_view_content(self):
        """View content in synced git puppet mirror

        :id: 02f06092-dd6c-49fa-be9f-831e52476e41

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to list contents of repo via cli

        :expectedresults: Spot-checked items (filenames, dates, perhaps
            checksums?) are correct.

        :CaseAutomation: notautomated
        """


class FileRepositoryTestCase(CLITestCase):
    """Specific tests for File Repositories"""

    @classmethod
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(FileRepositoryTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({'organization-id': cls.org['id']})

    @stubbed()
    @tier1
    def test_positive_upload_file_to_file_repo(self):
        """Check arbitrary file can be uploaded to File Repository

        :id: 134d668d-bd63-4475-bf7b-b899bb9fb7bb

        :Steps:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :expectedresults: uploaded file is available under File Repository

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_file_permissions(self):
        """Check file permissions after file upload to File Repository

        :id: 03da888a-69ba-492f-b204-c62d85948d8a

        :Setup:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Steps: Retrieve file permissions from File Repository

        :expectedresults: uploaded file permissions are kept after upload

        :CaseAutomation: notautomated
        """

    @tier1
    @upgrade
    def test_positive_remove_file(self):
        """Check arbitrary file can be removed from File Repository

        :id: 07ca9c8d-e764-404e-866d-30d8cd2ca2b6

        :Setup:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Steps: Remove a file from File Repository

        :expectedresults: file is not listed under File Repository after
            removal

        """
        new_repo = make_repository({
            'content-type': 'file',
            'product-id': self.product['id'],
            'url': CUSTOM_FILE_REPO,
        })
        ssh.upload_file(
            local_file=get_data_file(RPM_TO_UPLOAD),
            remote_file="/tmp/{0}".format(RPM_TO_UPLOAD)
        )
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
        repo = Repository.info({'id': new_repo['id']})
        self.assertGreater(int(repo['content-counts']['files']), 0)
        files = File.list({'repository-id': repo['id']})
        Repository.remove_content({
            'id': repo['id'],
            'ids': [file['id'] for file in files],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['content-counts']['files'], '0')

    @tier2
    @upgrade
    def test_positive_remote_directory_sync(self):
        """Check an entire remote directory can be synced to File Repository
        through http

        :id: 5c246307-8597-4f68-a6aa-4f1a6bbf0939

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
            2. Make the directory available through http

        :Steps:
            1. Create a File Repository with url pointing to http url
                created on setup
            2. Initialize synchronization

        :expectedresults: entire directory is synced over http

        """
        repo = make_repository({
            'product-id': self.product['id'],
            'content-type': 'file',
            'url': FAKE_PULP_REMOTE_FILEREPO,
            'name': gen_string('alpha'),
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['sync']['status'], 'Success')
        self.assertEqual(repo['content-counts']['files'], '2')

    @tier1
    def test_positive_file_repo_local_directory_sync(self):
        """Check an entire local directory can be synced to File Repository

        :id: ee91ecd2-2f07-4678-b782-95a7e7e57159

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
                locally (on the Satellite/Foreman host)

        :Steps:
            1. Create a File Repository with url pointing to local url
                created on setup
            2. Initialize synchronization


        :expectedresults: entire directory is synced

        """
        # Making Setup For Creating Local Directory using Pulp Manifest
        ssh.command("mkdir -p {}".format(CUSTOM_LOCAL_FOLDER))
        ssh.command('wget -P {0} -r -np -nH --cut-dirs=5 -R "index.html*" '
                    '{1}'.format(CUSTOM_LOCAL_FOLDER, CUSTOM_FILE_REPO))
        repo = make_repository({
            'content-type': 'file',
            'product-id': self.product['id'],
            'url': 'file://{0}'.format(CUSTOM_LOCAL_FOLDER),
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertGreater(repo['content-counts']['files'], '1')

    @tier2
    def test_positive_symlinks_sync(self):
        """Check symlinks can be synced to File Repository

        :id: b0b0a725-b754-450b-bc0d-572d0294307a

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
                locally (on the Satellite/Foreman host)
            2. Make sure it contains symlinks

        :Steps:
            1. Create a File Repository with url pointing to local url
                created on setup
            2. Initialize synchronization

        :expectedresults: entire directory is synced, including files
            referred by symlinks

        :CaseAutomation: automated
        """
        # Downloading the pulp repository into Satellite Host
        ssh.command("mkdir -p {}".format(CUSTOM_LOCAL_FOLDER))
        ssh.command('wget -P {0} -r -np -nH --cut-dirs=5 -R "index.html*" '
                    '{1}'.format(CUSTOM_LOCAL_FOLDER, CUSTOM_FILE_REPO))
        ssh.command("ln -s {0} /{1}"
                    .format(CUSTOM_LOCAL_FOLDER, gen_string('alpha')))

        repo = make_repository({
            'content-type': 'file',
            'product-id': self.product['id'],
            'url': 'file://{0}'.format(CUSTOM_LOCAL_FOLDER),
        })
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertGreater(repo['content-counts']['files'], '1')
