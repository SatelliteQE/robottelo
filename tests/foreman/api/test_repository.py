"""Unit tests for the ``repositories`` paths.

@Requirement: Repository

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from requests.exceptions import HTTPError
from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid, upload_manifest
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_7_PUPPET_REPO,
    FAKE_2_YUM_REPO,
    FAKE_5_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
    RPM_TO_UPLOAD,
    SRPM_TO_UPLOAD,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
    DOWNLOAD_POLICIES,
    REPO_TYPE
)
from robottelo.datafactory import (
    invalid_http_credentials,
    invalid_names_list,
    invalid_values_list,
    valid_data_list,
    valid_http_credentials,
    valid_labels_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier2,
)
from robottelo.helpers import get_data_file, read_data_file
from robottelo.test import APITestCase


class RepositoryTestCase(APITestCase):
    """Tests for ``katello/api/v2/repositories``."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization and product which can be re-used in tests."""
        super(RepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create a repository with valid name.

        @id: 159f7296-55d2-4360-948f-c24e7d75b962

        @Assert: A repository is created with the given name.
        """
        for name in valid_data_list():
            with self.subTest(name):
                repo = entities.Repository(
                    product=self.product, name=name).create()
                self.assertEqual(name, repo.name)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_label(self):
        """Create a repository providing label which is different from its name

        @id: 3be1b3fa-0e17-416f-97f0-858709e6b1da

        @Assert: A repository is created with expected label.
        """
        for label in valid_labels_list():
            with self.subTest(label):
                repo = entities.Repository(
                    product=self.product, label=label).create()
                self.assertEqual(repo.label, label)
                self.assertNotEqual(repo.name, label)

    @tier1
    @run_only_on('sat')
    def test_positive_create_yum(self):
        """Create yum repository.

        @id: 7bac7f45-0fb3-4443-bb3b-cee72248ca5d

        @Assert: A repository is created and has yum type.
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            url=FAKE_2_YUM_REPO,
        ).create()
        self.assertEqual(repo.content_type, 'yum')
        self.assertEqual(repo.url, FAKE_2_YUM_REPO)

    @tier1
    @run_only_on('sat')
    def test_positive_create_puppet(self):
        """Create puppet repository.

        @id: daa10ded-6de3-44b3-9707-9f0ac983d2ea

        @Assert: A repository is created and has puppet type.
        """
        repo = entities.Repository(
            product=self.product,
            content_type='puppet',
            url=FAKE_0_PUPPET_REPO,
        ).create()
        self.assertEqual(repo.content_type, 'puppet')

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_auth_yum_repo(self):
        """Create yum repository with basic HTTP authentication

        @id: 1b17fe37-cdbf-4a79-9b0d-6813ea502754

        @Assert: yum repository is created
        """
        url = FAKE_5_YUM_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='yum',
                    url=url_encoded,
                ).create()
                self.assertEqual(repo.content_type, 'yum')
                self.assertEqual(repo.url, url_encoded)

    @tier1
    def test_positive_create_with_download_policy(self):
        """Create YUM repositories with available download policies

        @id: 5e5479c4-904d-4892-bc43-6f81fa3813f8

        @Assert: YUM repository with a download policy is created
        """
        for policy in DOWNLOAD_POLICIES:
            with self.subTest(policy):
                repo = entities.Repository(
                    product=self.product,
                    content_type='yum',
                    download_policy=policy
                ).create()
                self.assertEqual(repo.download_policy, policy)

    @tier1
    def test_positive_create_with_default_download_policy(self):
        """Verify if the default download policy is assigned
        when creating a YUM repo without `download_policy` field

        @id: 54108f30-d73e-46d3-ae56-cda28678e7e9

        @Assert: YUM repository with a default download policy
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum'
        ).create()
        # this default value can change to 'on_demand' in future
        self.assertEqual(repo.download_policy, 'immediate')

    @tier1
    def test_positive_create_immediate_update_to_on_demand(self):
        """Update `immediate` download policy to `on_demand`
        for a newly created YUM repository

        @id: 8a70de9b-4663-4251-b91e-d3618ee7ef84

        @Assert: immediate download policy is updated to on_demand
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            download_policy='immediate'
        ).create()
        repo.download_policy = 'on_demand'
        repo = repo.update(['download_policy'])
        self.assertEqual(repo.download_policy, 'on_demand')

    @tier1
    def test_positive_create_immediate_update_to_background(self):
        """Update `immediate` download policy to `background`
        for a newly created YUM repository

        @id: 9aaf53be-1127-4559-9faf-899888a52846

        @Assert: immediate download policy is updated to background
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            download_policy='immediate'
        ).create()
        repo.download_policy = 'background'
        repo = repo.update(['download_policy'])
        self.assertEqual(repo.download_policy, 'background')

    @tier1
    def test_positive_create_on_demand_update_to_immediate(self):
        """Update `on_demand` download policy to `immediate`
        for a newly created YUM repository

        @id: 589ff7bb-4251-4218-bb90-4e63c9baf702

        @Assert: on_demand download policy is updated to immediate
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            download_policy='on_demand'
        ).create()
        repo.download_policy = 'immediate'
        repo = repo.update(['download_policy'])
        self.assertEqual(repo.download_policy, 'immediate')

    @tier1
    def test_positive_create_on_demand_update_to_background(self):
        """Update `on_demand` download policy to `background`
        for a newly created YUM repository

        @id: 1d9888a0-c5b5-41a7-815d-47e936022a60

        @Assert: on_demand download policy is updated to background
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            download_policy='on_demand'
        ).create()
        repo.download_policy = 'background'
        repo = repo.update(['download_policy'])
        self.assertEqual(repo.download_policy, 'background')

    @tier1
    def test_positive_create_background_update_to_immediate(self):
        """Update `background` download policy to `immediate`
        for a newly created YUM repository

        @id: 169530a7-c5ce-4ca5-8cdd-15398e13e2af

        @Assert: background download policy is updated to immediate
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            download_policy='background'
        ).create()
        repo.download_policy = 'immediate'
        repo = repo.update(['download_policy'])
        self.assertEqual(repo.download_policy, 'immediate')

    @tier1
    def test_positive_create_background_update_to_on_demand(self):
        """Update `background` download policy to `on_demand`
        for a newly created YUM repository

        @id: 40a3e963-61ff-41c4-aa6c-d9a4a638af4a

        @Assert: background download policy is updated to on_demand
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            download_policy='background'
        ).create()
        repo.download_policy = 'on_demand'
        repo = repo.update(['download_policy'])
        self.assertEqual(repo.download_policy, 'on_demand')

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_auth_puppet_repo(self):
        """Create Puppet repository with basic HTTP authentication

        @id: af9e4f0f-d128-43d2-a680-0a62c7dab266

        @Assert: Puppet repository is created
        """
        url = FAKE_7_PUPPET_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='puppet',
                    url=url_encoded,
                ).create()
                self.assertEqual(repo.content_type, 'puppet')
                self.assertEqual(repo.url, url_encoded)

    @tier1
    @run_only_on('sat')
    def test_positive_create_checksum(self):
        """Create a repository with valid checksum type.

        @id: c3678878-758a-4501-a038-a59503fee453

        @Assert: A repository is created and has expected checksum type.
        """
        for checksum_type in 'sha1', 'sha256':
            with self.subTest(checksum_type):
                repo = entities.Repository(
                    product=self.product, checksum_type=checksum_type).create()
                self.assertEqual(checksum_type, repo.checksum_type)

    @tier1
    @run_only_on('sat')
    def test_positive_create_unprotected(self):
        """Create a repository with valid unprotected flag values.

        @id: 38f78733-6a72-4bf5-912a-cfc51658f80c

        @Assert: A repository is created and has expected unprotected flag
        state.
        """
        for unprotected in True, False:
            repo = entities.Repository(
                product=self.product, unprotected=unprotected).create()
            self.assertEqual(repo.unprotected, unprotected)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_gpg(self):
        """Create a repository and provide a GPG key ID.

        @id: 023cf84b-74f3-4e63-a9d7-10afee6c1990

        @Assert: A repository is created with the given GPG key ID.

        @CaseLevel: Integration
        """
        gpg_key = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org,
        ).create()
        repo = entities.Repository(
            gpg_key=gpg_key,
            product=self.product,
        ).create()
        # Verify that the given GPG key ID is used.
        self.assertEqual(gpg_key.id, repo.gpg_key.id)

    @tier2
    @run_only_on('sat')
    def test_positive_create_same_name_different_orgs(self):
        """Create two repos with the same name in two different organizations.

        @id: bd1bd7e3-e393-44c8-a6d0-42edade40f60

        @Assert: The two repositories are successfully created and have given
        name.

        @CaseLevel: Integration
        """
        repo1 = entities.Repository(product=self.product).create()
        repo2 = entities.Repository(name=repo1.name).create()
        self.assertEqual(repo1.name, repo2.name)

    @tier1
    @run_only_on('sat')
    def test_negative_create_name(self):
        """Attempt to create repository with invalid names only.

        @id: 24947c92-3415-43df-add6-d6eb38afd8a3

        @Assert: A repository is not created and error is raised.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Repository(name=name).create()

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Attempt to create a repository providing a name of already existent
        entity

        @id: 0493dfc4-0043-4682-b339-ce61da7d48ae

        @Assert: Second repository is not created
        """
        name = gen_string('alphanumeric')
        entities.Repository(product=self.product, name=name).create()
        with self.assertRaises(HTTPError):
            entities.Repository(product=self.product, name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_label(self):
        """Attempt to create repository with invalid label.

        @id: f646ae84-2660-41bd-9883-331285fa1c9a

        @Assert: A repository is not created and error is raised.
        """
        with self.assertRaises(HTTPError):
            entities.Repository(label=gen_string('utf8')).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_url(self):
        """Attempt to create repository with invalid url.

        @id: 0bb9fc3f-d442-4437-b5d8-83024bc7ceab

        @Assert: A repository is not created and error is raised.
        """
        for url in invalid_names_list():
            with self.subTest(url):
                with self.assertRaises(HTTPError):
                    entities.Repository(url=url).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_auth_url_with_special_characters(self):
        """Verify that repository URL cannot contain unquoted special characters

        @id: 2ffaa412-e5e5-4bec-afaa-9ea54315df49

        @Assert: A repository is not created and error is raised.
        """
        # get a list of valid credentials without quoting them
        for cred in [creds for creds in valid_http_credentials()
                     if creds['quote'] is True]:
            with self.subTest(cred):
                url = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
                with self.assertRaises(HTTPError):
                    entities.Repository(url=url).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_auth_url_too_long(self):
        """Verify that repository URL length is limited

        @id: 5aad4e9f-f7e1-497c-8e1f-55e07e38ee80

        @Assert: A repository is not created and error is raised.
        """
        for cred in invalid_http_credentials():
            with self.subTest(cred):
                url = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
                with self.assertRaises(HTTPError):
                    entities.Repository(url=url).create()

    @tier1
    def test_negative_create_with_invalid_download_policy(self):
        """Verify that YUM repository cannot be created with invalid
        download policy

        @id: 3b143bf8-7056-4c94-910d-69a451071f26

        @Assert: YUM repository is not created with invalid download policy
        """
        with self.assertRaises(HTTPError):
            entities.Repository(
                product=self.product,
                content_type='yum',
                download_policy=gen_string('alpha', 5)
            ).create()

    @tier1
    def test_negative_update_to_invalid_download_policy(self):
        """Verify that YUM repository cannot be updated to invalid
        download policy

        @id: 5bd6a2e4-7ff0-42ac-825a-6b2a2f687c89

        @Assert: YUM repository is not updated to invalid download policy
        """
        with self.assertRaises(HTTPError):
            repo = entities.Repository(
                product=self.product,
                content_type='yum'
            ).create()
            repo.download_policy = gen_string('alpha', 5)
            repo.update(['download_policy'])

    @tier1
    def test_negative_create_non_yum_with_download_policy(self):
        """Verify that non-YUM repositories cannot be created with
        download policy

        @id: 71388973-50ea-4a20-9406-0aca142014ca

        @Assert: Non-YUM repository is not created with a
        download policy
        """
        non_yum_repo_types = [
            repo_type for repo_type in REPO_TYPE.keys()
            if repo_type != 'yum'
        ]
        for content_type in non_yum_repo_types:
            with self.subTest(content_type):
                with self.assertRaises(HTTPError):
                    entities.Repository(
                        product=self.product,
                        content_type=content_type,
                        download_policy='on_demand'
                    ).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_checksum(self):
        """Attempt to create repository with invalid checksum type.

        @id: c49a3c49-110d-4b74-ae14-5c9494a4541c

        @Assert: A repository is not created and error is raised.
        """
        with self.assertRaises(HTTPError):
            entities.Repository(checksum_type=gen_string('alpha')).create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update repository name to another valid name.

        @id: 1b428129-7cf9-449b-9e3b-74360c5f9eca

        @Assert: The repository name can be updated.
        """
        repo = entities.Repository(product=self.product).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                repo.name = new_name
                repo = repo.update(['name'])
                self.assertEqual(new_name, repo.name)

    @tier1
    @run_only_on('sat')
    def test_positive_update_checksum(self):
        """Update repository checksum type to another valid one.

        @id: 205e6e59-33c6-4a58-9245-1cac3a4f550a

        @Assert: The repository checksum type can be updated.
        """
        repo = entities.Repository(
            product=self.product, checksum_type='sha1').create()
        repo.checksum_type = 'sha256'
        repo = repo.update(['checksum_type'])
        self.assertEqual(repo.checksum_type, 'sha256')

    @tier1
    @run_only_on('sat')
    def test_positive_update_url(self):
        """Update repository url to another valid one.

        @id: 8fbc11f0-a5c5-498e-a314-87958dcd7832

        @Assert: The repository url can be updated.
        """
        repo = entities.Repository(product=self.product).create()
        repo.url = FAKE_2_YUM_REPO
        repo = repo.update(['url'])
        self.assertEqual(repo.url, FAKE_2_YUM_REPO)

    @tier1
    @run_only_on('sat')
    def test_positive_update_unprotected(self):
        """Update repository unprotected flag to another valid one.

        @id: c55d169a-8f11-4bf8-9913-b3d39fee75f0

        @Assert: The repository unprotected flag can be updated.
        """
        repo = entities.Repository(
            product=self.product, unprotected=False).create()
        repo.unprotected = True
        repo = repo.update(['unprotected'])
        self.assertEqual(repo.unprotected, True)

    @tier2
    @run_only_on('sat')
    def test_positive_update_gpg(self):
        """Create a repository and update its GPGKey

        @id: 0e9319dc-c922-4ecf-9f83-d221cfdf54c2

        @Assert: The updated repository points to a new GPG key.

        @CaseLevel: Integration
        """
        # Create a repo and make it point to a GPG key.
        gpg_key_1 = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org,
        ).create()
        repo = entities.Repository(
            gpg_key=gpg_key_1,
            product=self.product,
        ).create()

        # Update the repo and make it point to a new GPG key.
        gpg_key_2 = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_BETA_FILE),
            organization=self.org,
        ).create()
        repo.gpg_key = gpg_key_2
        repo = repo.update()
        self.assertEqual(repo.gpg_key.id, gpg_key_2.id)

    @run_only_on('sat')
    @tier2
    def test_positive_update_contents(self):
        """Create a repository and upload RPM contents.

        @id: 8faa64f9-b620-4c0a-8c80-801e8e6436f1

        @Assert: The repository's contents include one RPM.

        @CaseLevel: Integration
        """
        # Create a repository and upload RPM content.
        repo = entities.Repository(product=self.product).create()
        with open(get_data_file(RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})
        # Verify the repository's contents.
        self.assertEqual(repo.read().content_counts['rpm'], 1)

    @skip_if_bug_open('bugzilla', 1378442)
    @run_only_on('sat')
    @tier1
    def test_positive_upload_contents_srpm(self):
        """Create a repository and upload SRPM contents.

        @id: e091a725-048f-44ca-90cc-c016c450ced9

        @Assert: The repository's contents include one SRPM.
        """
        # Create a repository and upload source RPM content.
        repo = entities.Repository(product=self.product).create()
        with open(get_data_file(SRPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})
        # Verify the repository's contents.
        self.assertEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Attempt to update repository name to invalid one

        @id: 6f2f41a4-d871-4b91-87b1-a5a401c4aa69

        @Assert: Repository is not updated
        """
        repo = entities.Repository(product=self.product).create()
        for new_name in invalid_values_list():
            repo.name = new_name
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    repo.update(['name'])

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1311113)
    @tier1
    def test_negative_update_label(self):
        """Attempt to update repository label to another one.

        @id: 828d85df-3c25-4a69-b6a2-401c6b82e4f3

        @Assert: Repository is not updated and error is raised
        """
        repo = entities.Repository(product=self.product).create()
        repo.label = gen_string('alpha')
        with self.assertRaises(HTTPError):
            repo.update(['label'])

    @run_only_on('sat')
    @tier1
    def test_negative_update_auth_url_with_special_characters(self):
        """Verify that repository URL credentials cannot be updated to contain
        the forbidden characters

        @id: 47530b1c-e964-402a-a633-c81583fb5b98

        @Assert: Repository url not updated
        """
        new_repo = entities.Repository(product=self.product).create()
        # get auth repos with credentials containing unquoted special chars
        auth_repos = [
            repo.format(cred['login'], cred['pass'])
            for cred in valid_http_credentials() if cred['quote']
            for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
        ]

        for url in auth_repos:
            with self.subTest(url):
                new_repo.url = url
                with self.assertRaises(HTTPError):
                    new_repo = new_repo.update()

    @run_only_on('sat')
    @tier1
    def test_negative_update_auth_url_too_long(self):
        """Update the original url for a repository to value which is too long

        @id: cc00fbf4-d284-4404-88d9-ea0c0f03abe1

        @Assert: Repository url not updated
        """
        new_repo = entities.Repository(product=self.product).create()
        # get auth repos with credentials containing unquoted special chars
        auth_repos = [
            repo.format(cred['login'], cred['pass'])
            for cred in invalid_http_credentials()
            for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
        ]

        for url in auth_repos:
            with self.subTest(url):
                new_repo.url = url
                with self.assertRaises(HTTPError):
                    new_repo = new_repo.update()

    @tier2
    def test_positive_synchronize(self):
        """Create a repo and sync it.

        @id: 03beb469-570d-4109-b447-9c4c0b849266

        @Assert: The repo has at least one RPM.

        @CaseLevel: Integration
        """
        repo = entities.Repository(product=self.product).create()
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_positive_synchronize_auth_yum_repo(self):
        """Check if secured repository can be created and synced

        @id: bc44881c-e13f-45a9-90c2-5b18c7b25454

        @Assert: Repository is created and synced

        @CaseLevel: Integration
        """
        url = FAKE_5_YUM_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if cred['http_valid']]:
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='yum',
                    url=url_encoded,
                ).create()
                # Assertion that repo is not yet synced
                self.assertEqual(repo.content_counts['rpm'], 0)
                # Synchronize it
                repo.sync()
                # Verify it has finished
                self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_negative_synchronize_auth_yum_repo(self):
        """Check if secured repo fails to synchronize with invalid credentials

        @id: 88361168-69b5-4239-819a-889e316e28dc

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
                repo = entities.Repository(
                    product=self.product,
                    content_type='yum',
                    url=url_encoded,
                ).create()
                # Try to synchronize it
                with self.assertRaises(TaskFailedError):
                    repo.sync()

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_positive_synchronize_auth_puppet_repo(self):
        """Check if secured puppet repository can be created and synced

        @id: a1e25d36-baae-46cb-aa3b-5cb9fca4f059

        @Assert: Repository is created and synced

        @CaseLevel: Integration
        """
        url = FAKE_7_PUPPET_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if cred['http_valid']]:
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='puppet',
                    url=url_encoded,
                ).create()
                # Assertion that repo is not yet synced
                self.assertEqual(repo.content_counts['puppet_module'], 0)
                # Synchronize it
                repo.sync()
                # Verify it has finished
                self.assertEqual(
                    repo.read().content_counts['puppet_module'], 1)

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create a repository with different names and then delete it.

        @id: 29c2571a-b7fb-4ec7-b433-a1840758bcb0

        @Assert: The repository deleted successfully.
        """
        for name in valid_data_list():
            with self.subTest(name):
                repo = entities.Repository(
                    product=self.product, name=name).create()
                repo.delete()
                with self.assertRaises(HTTPError):
                    repo.read()


@run_in_one_thread
class RepositorySyncTestCase(APITestCase):
    """Tests for ``/katello/api/repositories/:id/sync``."""

    @tier2
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    def test_positive_sync_rh(self):
        """Sync RedHat Repository.

        @id: d69c44cd-753c-4a75-9fd5-a8ed963b5e04

        @Assert: Synced repo should fetch the data successfully.

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        entities.Repository(id=repo_id).sync()


class DockerRepositoryTestCase(APITestCase):
    """Tests specific to using ``Docker`` repositories."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    @run_only_on('sat')
    def test_positive_create(self):
        """Create a Docker-type repository

        @id: 2ce5b52d-8470-4c33-aeeb-9aee1af1cd74

        @Assert: A repository is created with a Docker repository.
        """
        product = entities.Product(organization=self.org).create()
        for name in valid_data_list():
            with self.subTest(name):
                repo = entities.Repository(
                    content_type=u'docker',
                    docker_upstream_name=u'busybox',
                    name=name,
                    product=product,
                    url=DOCKER_REGISTRY_HUB,
                ).create()
                self.assertEqual(repo.name, name)
                self.assertEqual(
                    repo.docker_upstream_name, u'busybox')
                self.assertEqual(repo.content_type, u'docker')

    @tier2
    @run_only_on('sat')
    def test_positive_synchronize(self):
        """Create and sync a Docker-type repository

        @id: 27653663-e5a7-4700-a3c1-f6eab6468adf

        @Assert: A repository is created with a Docker repository and it is
        synchronized.

        @CaseLevel: Integration
        """
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=u'busybox',
            name=u'busybox',
            product=product,
            url=DOCKER_REGISTRY_HUB,
        ).create()
        repo.sync()
        self.assertGreaterEqual(
            repo.read().content_counts['docker_manifest'], 1)

    @tier1
    @skip_if_bug_open('bugzilla', 1194476)
    def test_positive_update_name(self):
        """Update a repository's name.

        @id: 6dff0c90-170f-40b9-9347-8ec97d89f2fd

        @Assert: The repository's name is updated.
        """
        repository = entities.Repository(
            content_type='docker'
        ).create()
        # The only data provided with the PUT request is a name. No other
        # information about the repository (such as its URL) is provided.
        new_name = gen_string('alpha')
        repository.name = new_name
        repository = repository.update(['name'])
        self.assertEqual(new_name, repository.name)
