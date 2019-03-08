"""Unit tests for the ``repositories`` paths.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import tempfile

from six.moves.urllib.parse import urljoin
from fauxfactory import gen_string
from nailgun import client, entities
from nailgun.entity_mixins import TaskFailedError
from OpenSSL import SSL
from requests.exceptions import HTTPError
from robottelo import manifests, ssh
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo.constants import (
    CUSTOM_MODULE_STREAM_REPO_1,
    CUSTOM_MODULE_STREAM_REPO_2,
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_7_PUPPET_REPO,
    FAKE_2_YUM_REPO,
    FAKE_5_YUM_REPO,
    FAKE_YUM_DRPM_REPO,
    FAKE_YUM_SRPM_REPO,
    FEDORA26_OSTREE_REPO,
    FEDORA27_OSTREE_REPO,
    PRDS,
    REPOS,
    REPOSET,
    RPM_TO_UPLOAD,
    SRPM_TO_UPLOAD,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
    DOWNLOAD_POLICIES,
    REPO_TYPE,
    FAKE_1_PUPPET_REPO)
from robottelo.datafactory import (
    invalid_http_credentials,
    invalid_names_list,
    invalid_values_list,
    valid_data_list,
    valid_docker_repository_names,
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
    stubbed,
    tier4,
    upgrade
)
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import get_data_file, read_data_file
from robottelo.config import settings
from robottelo.test import APITestCase
from robottelo.api.utils import call_entity_method_with_timeout


class RepositoryTestCase(APITestCase):
    """Tests for ``katello/api/v2/repositories``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(RepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create a repository with valid name.

        :id: 159f7296-55d2-4360-948f-c24e7d75b962

        :expectedresults: A repository is created with the given name.

        :CaseImportance: Critical
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

        :id: 3be1b3fa-0e17-416f-97f0-858709e6b1da

        :expectedresults: A repository is created with expected label.

        :CaseImportance: Critical
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

        :id: 7bac7f45-0fb3-4443-bb3b-cee72248ca5d

        :expectedresults: A repository is created and has yum type.

        :CaseImportance: Critical
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

        :id: daa10ded-6de3-44b3-9707-9f0ac983d2ea

        :expectedresults: A repository is created and has puppet type.

        :CaseImportance: Critical
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

        :id: 1b17fe37-cdbf-4a79-9b0d-6813ea502754

        :expectedresults: yum repository is created

        :CaseImportance: Critical
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
    @upgrade
    def test_positive_create_with_download_policy(self):
        """Create YUM repositories with available download policies

        :id: 5e5479c4-904d-4892-bc43-6f81fa3813f8

        :expectedresults: YUM repository with a download policy is created

        :CaseImportance: Critical
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

        :id: 54108f30-d73e-46d3-ae56-cda28678e7e9

        :expectedresults: YUM repository with a default download policy

        :CaseImportance: Critical
        """

        default_dl_policy = entities.Setting().search(
            query={'search': 'name=default_download_policy'}
        )
        self.assertTrue(default_dl_policy)
        repo = entities.Repository(
            product=self.product,
            content_type='yum'
        ).create()
        self.assertEqual(repo.download_policy, default_dl_policy[0].value)

    @tier1
    def test_positive_create_immediate_update_to_on_demand(self):
        """Update `immediate` download policy to `on_demand`
        for a newly created YUM repository

        :id: 8a70de9b-4663-4251-b91e-d3618ee7ef84

        :expectedresults: immediate download policy is updated to on_demand

        :CaseImportance: Critical
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

        :id: 9aaf53be-1127-4559-9faf-899888a52846

        :expectedresults: immediate download policy is updated to background

        :CaseImportance: Critical
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

        :id: 589ff7bb-4251-4218-bb90-4e63c9baf702

        :expectedresults: on_demand download policy is updated to immediate

        :CaseImportance: Critical
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

        :id: 1d9888a0-c5b5-41a7-815d-47e936022a60

        :expectedresults: on_demand download policy is updated to background

        :CaseImportance: Critical
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

        :id: 169530a7-c5ce-4ca5-8cdd-15398e13e2af

        :expectedresults: background download policy is updated to immediate

        :CaseImportance: Critical
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

        :id: 40a3e963-61ff-41c4-aa6c-d9a4a638af4a

        :expectedresults: background download policy is updated to on_demand

        :CaseImportance: Critical
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

        :id: af9e4f0f-d128-43d2-a680-0a62c7dab266

        :expectedresults: Puppet repository is created

        :CaseImportance: Critical
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

        :id: c3678878-758a-4501-a038-a59503fee453

        :expectedresults: A repository is created and has expected checksum
            type.

        :CaseImportance: Critical
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

        :id: 38f78733-6a72-4bf5-912a-cfc51658f80c

        :expectedresults: A repository is created and has expected unprotected
            flag state.

        :CaseImportance: Critical
        """
        for unprotected in True, False:
            repo = entities.Repository(
                product=self.product, unprotected=unprotected).create()
            self.assertEqual(repo.unprotected, unprotected)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_gpg(self):
        """Create a repository and provide a GPG key ID.

        :id: 023cf84b-74f3-4e63-a9d7-10afee6c1990

        :expectedresults: A repository is created with the given GPG key ID.

        :CaseLevel: Integration
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

        :id: bd1bd7e3-e393-44c8-a6d0-42edade40f60

        :expectedresults: The two repositories are successfully created and
            have given name.

        :CaseLevel: Integration
        """
        repo1 = entities.Repository(product=self.product).create()
        repo2 = entities.Repository(name=repo1.name).create()
        self.assertEqual(repo1.name, repo2.name)

    @tier2
    def test_positive_create_puppet_repo_same_url_different_orgs(self):
        """Create two repos with the same URL in two different organizations.

        :id: 7c74c2b8-732a-4c47-8ad9-697121db05be

        :expectedresults: Repositories are created and puppet modules are
            visible from different organizations.

        :CaseLevel: Integration
        """
        url = 'https://omaciel.fedorapeople.org/7c74c2b8/'
        # Use setup product for the first repo and create new org/product
        # for the second one
        org = entities.Organization().create()
        products = (self.product, entities.Product(organization=org).create())
        # Create repositories within different organizations/products
        for product in products:
            repo = entities.Repository(
                url=url, product=product, content_type='puppet').create()
            repo.sync()
            self.assertGreaterEqual(
                repo.read().content_counts['puppet_module'], 1)

    @tier1
    @run_only_on('sat')
    def test_negative_create_name(self):
        """Attempt to create repository with invalid names only.

        :id: 24947c92-3415-43df-add6-d6eb38afd8a3

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical
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

        :id: 0493dfc4-0043-4682-b339-ce61da7d48ae

        :expectedresults: Second repository is not created

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        entities.Repository(product=self.product, name=name).create()
        with self.assertRaises(HTTPError):
            entities.Repository(product=self.product, name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_label(self):
        """Attempt to create repository with invalid label.

        :id: f646ae84-2660-41bd-9883-331285fa1c9a

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.Repository(label=gen_string('utf8')).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_url(self):
        """Attempt to create repository with invalid url.

        :id: 0bb9fc3f-d442-4437-b5d8-83024bc7ceab

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical
        """
        for url in invalid_names_list():
            with self.subTest(url):
                with self.assertRaises(HTTPError):
                    entities.Repository(url=url).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_auth_url_with_special_characters(self):
        """Verify that repository URL cannot contain unquoted special characters

        :id: 2ffaa412-e5e5-4bec-afaa-9ea54315df49

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical
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

        :id: 5aad4e9f-f7e1-497c-8e1f-55e07e38ee80

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical
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

        :id: c39bf33a-26f6-411b-8658-eab1bb40ef84

        :expectedresults: YUM repository is not created with invalid download
            policy

        :CaseImportance: Critical
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

        :id: 24d36e79-855e-4832-a136-30cbd144de44

        :expectedresults: YUM repository is not updated to invalid download
            policy

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            repo = entities.Repository(
                product=self.product,
                content_type='yum'
            ).create()
            repo.download_policy = gen_string('alpha', 5)
            repo.update(['download_policy'])

    @tier1
    @skip_if_bug_open('bugzilla', 1654944)
    def test_negative_create_non_yum_with_download_policy(self):
        """Verify that non-YUM repositories cannot be created with
        download policy

        :id: 8a59cb31-164d-49df-b3c6-9b90634919ce

        :expectedresults: Non-YUM repository is not created with a download
            policy

        :CaseImportance: Critical
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

        :id: c49a3c49-110d-4b74-ae14-5c9494a4541c

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.Repository(checksum_type=gen_string('alpha')).create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update repository name to another valid name.

        :id: 1b428129-7cf9-449b-9e3b-74360c5f9eca

        :expectedresults: The repository name can be updated.

        :CaseImportance: Critical
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

        :id: 205e6e59-33c6-4a58-9245-1cac3a4f550a

        :expectedresults: The repository checksum type can be updated.

        :CaseImportance: Critical
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

        :id: 8fbc11f0-a5c5-498e-a314-87958dcd7832

        :expectedresults: The repository url can be updated.

        :CaseImportance: Critical
        """
        repo = entities.Repository(product=self.product).create()
        repo.url = FAKE_2_YUM_REPO
        repo = repo.update(['url'])
        self.assertEqual(repo.url, FAKE_2_YUM_REPO)

    @tier1
    @run_only_on('sat')
    def test_positive_update_unprotected(self):
        """Update repository unprotected flag to another valid one.

        :id: c55d169a-8f11-4bf8-9913-b3d39fee75f0

        :expectedresults: The repository unprotected flag can be updated.

        :CaseImportance: Critical
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

        :id: 0e9319dc-c922-4ecf-9f83-d221cfdf54c2

        :expectedresults: The updated repository points to a new GPG key.

        :CaseLevel: Integration
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
        repo = repo.update(['gpg_key'])
        self.assertEqual(repo.gpg_key.id, gpg_key_2.id)

    @run_only_on('sat')
    @tier2
    def test_positive_update_contents(self):
        """Create a repository and upload RPM contents.

        :id: 8faa64f9-b620-4c0a-8c80-801e8e6436f1

        :expectedresults: The repository's contents include one RPM.

        :CaseLevel: Integration
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

        :id: e091a725-048f-44ca-90cc-c016c450ced9

        :expectedresults: The repository's contents include one SRPM.

        :CaseImportance: Critical
        """
        # Create a repository and upload source RPM content.
        repo = entities.Repository(product=self.product).create()
        with open(get_data_file(SRPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})
        # Verify the repository's contents.
        self.assertEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1459845)
    @tier1
    def test_positive_remove_contents(self):
        """Synchronize a repository and remove rpm content.

        :id: f686b74b-7ee9-4806-b999-bc05ffe61a9d

        :expectedresults: The repository's content is removed and content count
            shows zero packages

        :BZ: 1459845

        :CaseImportance: Critical
        """
        # Create repository and synchronize it
        repo = entities.Repository(
            url=FAKE_2_YUM_REPO,
            content_type='yum',
            product=self.product,
        ).create()
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)
        # Find repo packages and remove them
        packages = entities.Package(repository=repo).search(
            query={'per_page': 1000})
        repo.remove_content(data={'ids': [package.id for package in packages]})
        self.assertEqual(repo.read().content_counts['rpm'], 0)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Attempt to update repository name to invalid one

        :id: 6f2f41a4-d871-4b91-87b1-a5a401c4aa69

        :expectedresults: Repository is not updated

        :CaseImportance: Critical
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

        :id: 828d85df-3c25-4a69-b6a2-401c6b82e4f3

        :expectedresults: Repository is not updated and error is raised

        :CaseImportance: Critical
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

        :id: 47530b1c-e964-402a-a633-c81583fb5b98

        :expectedresults: Repository url not updated

        :CaseImportance: Critical
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
                    new_repo.update(['url'])

    @run_only_on('sat')
    @tier1
    def test_negative_update_auth_url_too_long(self):
        """Update the original url for a repository to value which is too long

        :id: cc00fbf4-d284-4404-88d9-ea0c0f03abe1

        :expectedresults: Repository url not updated

        :CaseImportance: Critical
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
                    new_repo.update(['url'])

    @tier2
    def test_positive_synchronize(self):
        """Create a repo and sync it.

        :id: 03beb469-570d-4109-b447-9c4c0b849266

        :expectedresults: The repo has at least one RPM.

        :CaseLevel: Integration
        """
        repo = entities.Repository(product=self.product).create()
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_positive_synchronize_auth_yum_repo(self):
        """Check if secured repository can be created and synced

        :id: bc44881c-e13f-45a9-90c2-5b18c7b25454

        :expectedresults: Repository is created and synced

        :CaseLevel: Integration
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

        :id: 88361168-69b5-4239-819a-889e316e28dc

        :expectedresults: Repository is created but synchronization fails

        :CaseLevel: Integration
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
    @upgrade
    def test_positive_synchronize_auth_puppet_repo(self):
        """Check if secured puppet repository can be created and synced

        :id: a1e25d36-baae-46cb-aa3b-5cb9fca4f059

        :expectedresults: Repository is created and synced

        :CaseLevel: Integration
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

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1459845)
    @tier2
    def test_positive_resynchronize_rpm_repo(self):
        """Check that repository content is resynced after packages were
        removed from repository

        :id: a5c056ab-16c3-4052-b53d-818163b9983e

        :expectedresults: Repository has updated non-zero packages count

        :BZ: 1459845

        :CaseLevel: Integration

        :BZ: 1318004
        """
        # Create repository and synchronize it
        repo = entities.Repository(
            url=FAKE_2_YUM_REPO,
            content_type='yum',
            product=self.product,
        ).create()
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)
        # Find repo packages and remove them
        packages = entities.Package(repository=repo).search(
            query={'per_page': 1000})
        repo.remove_content(data={'ids': [package.id for package in packages]})
        self.assertEqual(repo.read().content_counts['rpm'], 0)
        # Re-synchronize repository
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @tier2
    def test_positive_resynchronize_puppet_repo(self):
        """Check that repository content is resynced after puppet modules
        were removed from repository

        :id: db50beb0-de73-4783-abc8-57e61188b6c7

        :expectedresults: Repository has updated non-zero puppet modules count

        :CaseLevel: Integration

        :BZ: 1318004
        """
        # Create repository and synchronize it
        repo = entities.Repository(
            url=FAKE_1_PUPPET_REPO,
            content_type='puppet',
            product=self.product,
        ).create()
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['puppet_module'], 1)
        # Find repo packages and remove them
        modules = entities.PuppetModule(repository=[repo]).search(
            query={'per_page': 1000})
        repo.remove_content(data={'ids': [module.id for module in modules]})
        self.assertEqual(repo.read().content_counts['puppet_module'], 0)
        # Re-synchronize repository
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['puppet_module'], 1)

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create a repository with different names and then delete it.

        :id: 29c2571a-b7fb-4ec7-b433-a1840758bcb0

        :expectedresults: The repository deleted successfully.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                repo = entities.Repository(
                    product=self.product, name=name).create()
                repo.delete()
                with self.assertRaises(HTTPError):
                    repo.read()

    @tier2
    @run_only_on('sat')
    @upgrade
    def test_positive_delete_rpm(self):
        """Check if rpm repository with packages can be deleted.

        :id: d61c8c8b-2b77-4bff-b215-fa2b7c05aa78

        :expectedresults: The repository deleted successfully.

        :CaseLevel: Integration
        """
        repo = entities.Repository(
            url=FAKE_2_YUM_REPO,
            content_type='yum',
            product=self.product,
        ).create()
        repo.sync()
        # Check that there is at least one package
        self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)
        repo.delete()
        with self.assertRaises(HTTPError):
            repo.read()

    @tier2
    @run_only_on('sat')
    @upgrade
    def test_positive_delete_puppet(self):
        """Check if puppet repository with puppet modules can be deleted.

        :id: 5c60b0ab-ef50-41a3-8578-bfdb5cb228ea

        :expectedresults: The repository deleted successfully.

        :CaseLevel: Integration

        :BZ: 1316681
        """
        repo = entities.Repository(
            url=FAKE_1_PUPPET_REPO,
            content_type='puppet',
            product=self.product,
        ).create()
        repo.sync()
        # Check that there is at least one puppet module
        self.assertGreaterEqual(repo.read().content_counts['puppet_module'], 1)
        repo.delete()
        with self.assertRaises(HTTPError):
            repo.read()

    @tier1
    @run_only_on('sat')
    def test_positive_list_puppet_modules_with_multiple_repos(self):
        """Verify that puppet modules list for specific repo is correct
        and does not affected by other repositories.

        :id: e9e16ac2-a58d-4d49-b378-59e4f5b3a3ec

        :expectedresults: Number of modules has no changed after a second repo
            was synced.

        :CaseImportance: Critical
        """
        # Create and sync first repo
        repo1 = entities.Repository(
            product=self.product,
            content_type='puppet',
            url=FAKE_0_PUPPET_REPO,
        ).create()
        repo1.sync()
        # Verify that number of synced modules is correct
        content_count = repo1.read().content_counts['puppet_module']
        modules_num = len(repo1.puppet_modules()['results'])
        self.assertEqual(content_count, modules_num)
        # Create and sync second repo
        repo2 = entities.Repository(
            product=self.product,
            content_type='puppet',
            url=FAKE_1_PUPPET_REPO,
        ).create()
        repo2.sync()
        # Verify that number of modules from the first repo has not changed
        self.assertEqual(modules_num, len(repo1.puppet_modules()['results']))

    @tier2
    @upgrade
    def test_positive_access_protected_repository(self):
        """Access protected/https repository data file URL using organization
        debug certificate

        :id: 4dba5b31-1818-45dd-a9bd-3ec627c3db57

        :customerscenario: true

        :expectedresults: The repository data file successfully accessed.

        :BZ: 1242310

        :CaseLevel: Integration

        :CaseImportance: High
        """
        # create a new protected repository
        repository = entities.Repository(
            url=FAKE_2_YUM_REPO,
            content_type=REPO_TYPE['yum'],
            product=self.product,
            unprotected=False,
        ).create()
        repository.sync()
        repo_data_file_url = urljoin(
            repository.full_path, 'repodata/repomd.xml')
        # ensure the url is based on the protected base server URL
        self.assertTrue(repo_data_file_url.startswith(
            'https://{0}'.format(settings.server.hostname)))
        # try to access repository data without organization debug certificate
        with self.assertRaises(SSL.Error):
            client.get(repo_data_file_url, verify=False)
        # get the organization debug certificate
        cert_content = self.org.download_debug_certificate()
        # save the organization debug certificate to file
        cert_file_path = '{0}/{1}.pem'.format(
            tempfile.gettempdir(), self.org.label)
        with open(cert_file_path, 'w') as cert_file:
            cert_file.write(cert_content)
        # access repository data with organization debug certificate
        response = client.get(
            repo_data_file_url, cert=cert_file_path, verify=False)
        self.assertEqual(response.status_code, 200)

    @tier2
    @upgrade
    def test_module_stream_repository_crud_operations(self):
        """Verify that module stream api calls works with product having other type
        repositories.

        :id: 61a5d24e-d4da-487d-b6ea-9673c05ceb60

        :expectedresults: module stream repo create, update, delete api calls should work with
         count of module streams

        :CaseImportance: Critical
        """
        repository = entities.Repository(
            url=CUSTOM_MODULE_STREAM_REPO_2,
            content_type=REPO_TYPE['yum'],
            product=self.product,
            unprotected=False,
        ).create()
        repository.sync()
        self.assertEquals(repository.read().content_counts['module_stream'], 7)
        repository.url = CUSTOM_MODULE_STREAM_REPO_1
        repository = repository.update(['url'])
        repository.sync()
        self.assertEquals(repository.read().content_counts['module_stream'], 53)
        repository.delete()
        with self.assertRaises(HTTPError):
            repository.read()


@run_in_one_thread
class RepositorySyncTestCase(APITestCase):
    """Tests for ``/katello/api/repositories/:id/sync``."""

    @tier2
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    def test_positive_sync_rh(self):
        """Sync RedHat Repository.

        :id: d69c44cd-753c-4a75-9fd5-a8ed963b5e04

        :expectedresults: Synced repo should fetch the data successfully.

        :CaseLevel: Integration
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

    @stubbed
    @tier2
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    def test_positive_sync_rh_app_stream(self):
        """Sync RedHat Appstream Repository.

        :id: 44810877-15cd-48c4-aa85-5881b5c4410e

        :expectedresults: Synced repo should fetch the data successfully and
         it should contain the module streams.

        :CaseLevel: Integration
        """


class DockerRepositoryTestCase(APITestCase):
    """Tests specific to using ``Docker`` repositories."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    @run_only_on('sat')
    def test_positive_create(self):
        """Create a Docker-type repository

        :id: 2ce5b52d-8470-4c33-aeeb-9aee1af1cd74

        :expectedresults: A repository is created with a Docker repository.

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.org).create()
        for name in valid_docker_repository_names():
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

        :id: 27653663-e5a7-4700-a3c1-f6eab6468adf

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseLevel: Integration
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

        :id: 6dff0c90-170f-40b9-9347-8ec97d89f2fd

        :expectedresults: The repository's name is updated.

        :CaseImportance: Critical
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

    @tier2
    @run_only_on('sat')
    def test_positive_synchronize_private_registry(self):
        """Create and sync a Docker-type repository from a private registry

        :id: c71fe7c1-1160-4145-ac71-f827c14b1027

        :expectedresults: A repository is created with a private Docker \
            repository and it is synchronized.

        :customerscenario: true

        :BZ: 1475121

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=settings.docker.private_registry_name,
            name=gen_string('alpha'),
            product=product,
            url=settings.docker.private_registry_url,
            upstream_username=settings.docker.private_registry_username,
            upstream_password=settings.docker.private_registry_password,
        ).create()
        repo.sync()
        self.assertGreaterEqual(
            repo.read().content_counts['docker_manifest'], 1)

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1580510)
    def test_negative_synchronize_private_registry_wrong_password(self):
        """Create and try to sync a Docker-type repository from a private
        registry providing wrong credentials the sync must fail with
        reasonable error message.

        :id: 2857fce2-fed7-49fc-be20-bf2e4726c9f5

        :expectedresults: A repository is created with a private Docker \
            repository and sync fails with reasonable error message.

        :customerscenario: true

        :BZ: 1475121, 1580510

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=settings.docker.private_registry_name,
            name=gen_string('alpha'),
            product=product,
            url=settings.docker.private_registry_url,
            upstream_username=settings.docker.private_registry_username,
            upstream_password='ThisIsaWrongPassword',
        ).create()

        with self.assertRaises(TaskFailedError) as excinfo:
            repo.sync()
        # assert error message includes the proper pulp_docker error code
        # DKR1007 = Error("DKR1007", _("Could not fetch repository %(repo)s
        # from registry %(registry)s - ""%(reason)s"),
        # in this case reason = "Unauthorized or Not Found"
        self.assertIn("DKR1007", str(excinfo.exception))
        self.assertIn("Unauthorized or Not Found", str(excinfo.exception))

    @tier2
    @run_only_on('sat')
    def test_negative_synchronize_private_registry_wrong_repo(self):
        """Create and try to sync a Docker-type repository from a private
        registry providing wrong repository the sync must fail with
        reasonable error message.

        :id: 16c21aaf-796e-4e29-b3a1-7d93de0d6257

        :expectedresults: A repository is created with a private Docker \
            repository and sync fails with reasonable error message.

        :customerscenario: true

        :BZ: 1475121, 1580510

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=settings.docker.private_registry_name,
            name=gen_string('alpha'),
            product=product,
            # url=settings.docker.private_registry_url,
            url='https://registry.doesnot.exist.com',
            upstream_username='ThisRegistry/DoesNotExist',
            upstream_password='ThisIsaWrongPassword',
        ).create()

        with self.assertRaises(TaskFailedError) as excinfo:
            repo.sync()
        # assert error message includes the proper pulp_docker error code
        # DKR1008 = Error("DKR1008", _("Could not find registry API at
        # %(registry)s"), ['registry'])
        self.assertIn("DKR1008", str(excinfo.exception))
        self.assertIn("Could not find registry API", str(excinfo.exception))

    @tier2
    @run_only_on('sat')
    def test_negative_synchronize_private_registry_no_passwd(self):
        """Create and try to sync a Docker-type repository from a private
        registry providing empty password and the sync must fail with
        reasonable error message.

        :id: 86bde2f1-4761-4045-aa54-c7be7715cd3a

        :expectedresults: A repository is created with a private Docker \
            repository and sync fails with reasonable error message.

        :customerscenario: true

        :BZ: 1475121, 1580510

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.org).create()
        with self.assertRaises(HTTPError) as excinfo:
            entities.Repository(
                content_type=u'docker',
                docker_upstream_name=settings.docker.private_registry_name,
                name=gen_string('alpha'),
                product=product,
                url=settings.docker.private_registry_url,
                upstream_username=settings.docker.private_registry_username,
            ).create()
        self.assertIn("422", str(excinfo.exception))
        self.assertIn("Unprocessable Entity", str(excinfo.exception))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_synchronize_docker_repo_with_tags_whitelist(self):
        """Check if only whitelisted tags are synchronized

        :id: abd584ef-f616-49d8-ab30-ae32e4e8a685

        :expectedresults: Only whitelisted tag is synchronized
        """
        tags = ['latest']
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
                content_type='docker',
                docker_tags_whitelist=tags,
                docker_upstream_name='alpine',
                name=gen_string('alphanumeric', 10),
                product=product,
                url=DOCKER_REGISTRY_HUB,
        ).create()
        repo.sync()
        repo = repo.read()
        [self.assertIn(tag, repo.docker_tags_whitelist) for tag in tags]
        self.assertEqual(repo.content_counts['docker_tag'], 1)

    @run_only_on('sat')
    @tier2
    def test_positive_synchronize_docker_repo_set_tags_later(self):
        """Verify that adding tags whitelist and re-syncing after
        synchronizing full repository doesn't remove content that was
        already pulled in

        :id: 6838e152-5fd9-4f25-ae04-67760571f6ba

        :expectedresults: Non-whitelisted tags are not removed
        """
        tags = ['latest']
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
                content_type='docker',
                docker_upstream_name='alpine',
                name=gen_string('alphanumeric', 10),
                product=product,
                url=DOCKER_REGISTRY_HUB,
        ).create()
        repo.sync()
        repo = repo.read()
        self.assertEqual(len(repo.docker_tags_whitelist), 0)
        self.assertGreaterEqual(repo.content_counts['docker_tag'], 2)

        repo.docker_tags_whitelist = tags
        repo.update(['docker_tags_whitelist'])
        repo.sync()
        repo = repo.read()
        [self.assertIn(tag, repo.docker_tags_whitelist) for tag in tags]
        self.assertGreaterEqual(repo.content_counts['docker_tag'], 2)

    @run_only_on('sat')
    @tier2
    def test_negative_synchronize_docker_repo_with_mix_valid_invalid_tags(self):
        """Set tags whitelist to contain both valid and invalid (non-existing)
        tags. Check if only whitelisted tags are synchronized

        :id: 7b66171f-5bf1-443b-9ca3-9614d66a0c6b

        :expectedresults: Only whitelisted tag is synchronized
        """
        tags = ['latest', gen_string('alpha')]
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
                content_type='docker',
                docker_tags_whitelist=tags,
                docker_upstream_name='alpine',
                name=gen_string('alphanumeric', 10),
                product=product,
                url=DOCKER_REGISTRY_HUB,
        ).create()
        repo.sync()
        repo = repo.read()
        [self.assertIn(tag, repo.docker_tags_whitelist) for tag in tags]
        self.assertEqual(repo.content_counts['docker_tag'], 1)

    @run_only_on('sat')
    @tier2
    def test_negative_synchronize_docker_repo_with_invalid_tags(self):
        """Set tags whitelist to contain only invalid (non-existing)
        tags. Check that no data is synchronized.

        :id: c419da6a-1530-4f66-8f8e-d4ec69633356

        :expectedresults: Tags are not synchronized
        """
        tags = [gen_string('alpha') for _ in range(3)]
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
                content_type='docker',
                docker_tags_whitelist=tags,
                docker_upstream_name='alpine',
                name=gen_string('alphanumeric', 10),
                product=product,
                url=DOCKER_REGISTRY_HUB,
        ).create()
        repo.sync()
        repo = repo.read()
        [self.assertIn(tag, repo.docker_tags_whitelist) for tag in tags]
        self.assertEqual(repo.content_counts['docker_tag'], 0)


class OstreeRepositoryTestCase(APITestCase):
    """Tests specific to using ``OSTree`` repositories."""

    @classmethod
    @skip_if_os('RHEL6')
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(OstreeRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()

    @tier1
    def test_positive_create_ostree(self):
        """Create ostree repository.

        :id: f3332dd3-1e6d-44e2-8f24-fae6fba2de8d

        :expectedresults: A repository is created and has ostree type.

        :CaseImportance: Critical
        """
        repo = entities.Repository(
            product=self.product,
            content_type='ostree',
            url=FEDORA27_OSTREE_REPO,
            unprotected=False
        ).create()
        self.assertEqual(repo.content_type, 'ostree')

    @tier1
    def test_positive_update_name(self):
        """Update ostree repository name.

        :id: 4d9f1418-cc08-4c3c-a5dd-1d20fb9052a2

        :expectedresults: The repository name is updated.

        :CaseImportance: Critical
        """
        repo = entities.Repository(
            product=self.product,
            content_type='ostree',
            url=FEDORA27_OSTREE_REPO,
            unprotected=False
        ).create()
        new_name = gen_string('alpha')
        repo.name = new_name
        repo = repo.update(['name'])
        self.assertEqual(new_name, repo.name)

    @tier1
    def test_positive_update_url(self):
        """Update ostree repository url.

        :id: 6ba45475-a060-42a7-bc9e-ea2824a5476b

        :expectedresults: The repository url is updated.

        :CaseImportance: Critical
        """
        repo = entities.Repository(
            product=self.product,
            content_type='ostree',
            url=FEDORA27_OSTREE_REPO,
            unprotected=False
        ).create()
        new_url = FEDORA26_OSTREE_REPO
        repo.url = new_url
        repo = repo.update(['url'])
        self.assertEqual(new_url, repo.url)

    @tier1
    @upgrade
    def test_positive_delete_ostree(self):
        """Delete an ostree repository.

        :id: 05db79ed-28c7-47fc-85f5-194a805d71ca

        :expectedresults: The ostree repository deleted successfully.

        :CaseImportance: Critical
        """
        repo = entities.Repository(
            product=self.product,
            content_type='ostree',
            url=FEDORA27_OSTREE_REPO,
            unprotected=False
        ).create()
        repo.delete()
        with self.assertRaises(HTTPError):
            repo.read()

    @tier2
    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @upgrade
    def test_positive_sync_rh_atomic(self):
        """Sync RH Atomic Ostree Repository.

        :id: 38c8aeaa-5ad2-40cb-b1d2-f0ac604f9fdd

        :expectedresults: Synced repo should fetch the data successfully.

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        repo_id = enable_rhrepo_and_fetchid(
            org_id=org.id,
            product=PRDS['rhah'],
            repo=REPOS['rhaht']['name'],
            reposet=REPOSET['rhaht'],
            releasever=None,
            basearch=None,
        )
        call_entity_method_with_timeout(
            entities.Repository(id=repo_id).sync, timeout=1500)


class SRPMRepositoryTestCase(APITestCase):
    """Tests specific to using repositories containing source RPMs."""

    @classmethod
    @skip_if_bug_open('bugzilla', 1378442)
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(SRPMRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()

    @tier2
    def test_positive_sync(self):
        """Synchronize repository with SRPMs

        :id: f87391c6-c18a-4c4f-81db-decbba7f1856

        :expectedresults: srpms can be listed in repository
        """
        repo = entities.Repository(
            product=self.product,
            url=FAKE_YUM_SRPM_REPO,
        ).create()
        repo.sync()
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.org.label,
                self.product.label,
                repo.label,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_sync_publish_cv(self):
        """Synchronize repository with SRPMs, add repository to content view
        and publish content view

        :id: a0868429-584c-4e36-b93f-c85e8e94a60b

        :expectedresults: srpms can be listed in content view
        """
        repo = entities.Repository(
            product=self.product,
            url=FAKE_YUM_SRPM_REPO,
        ).create()
        repo.sync()
        cv = entities.ContentView(organization=self.org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.org.label,
                cv.label,
                self.product.label,
                repo.label,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    @upgrade
    def test_positive_sync_publish_promote_cv(self):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: 811b524f-2b19-4408-ad7f-d7251625e35c

        :expectedresults: srpms can be listed in content view in proper
            lifecycle environment
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        repo = entities.Repository(
            product=self.product,
            url=FAKE_YUM_SRPM_REPO,
        ).create()
        repo.sync()
        cv = entities.ContentView(organization=self.org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        promote(cv.version[0], lce.id)
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            ' | grep .src.rpm'
            .format(
                self.org.label,
                lce.name,
                cv.label,
                self.product.label,
                repo.label,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)


class DRPMRepositoryTestCase(APITestCase):
    """Tests specific to using repositories containing delta RPMs."""

    @classmethod
    @skip_if_bug_open('bugzilla', 1378442)
    def setUpClass(cls):
        """Create a product and an org which can be re-used in tests."""
        super(DRPMRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()

    @tier2
    def test_positive_sync(self):
        """Synchronize repository with DRPMs

        :id: 7816031c-b7df-49e0-bf42-7f6e2d9b0233

        :expectedresults: drpms can be listed in repository
        """
        repo = entities.Repository(
            product=self.product,
            url=FAKE_YUM_DRPM_REPO,
        ).create()
        repo.sync()
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.org.label,
                self.product.label,
                repo.label,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    def test_positive_sync_publish_cv(self):
        """Synchronize repository with DRPMs, add repository to content view
        and publish content view

        :id: dac4bd82-1433-4e5d-b82f-856056ca3924

        :expectedresults: drpms can be listed in content view
        """
        repo = entities.Repository(
            product=self.product,
            url=FAKE_YUM_DRPM_REPO,
        ).create()
        repo.sync()
        cv = entities.ContentView(organization=self.org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.org.label,
                cv.label,
                self.product.label,
                repo.label,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier2
    @upgrade
    def test_positive_sync_publish_promote_cv(self):
        """Synchronize repository with DRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: 44296354-8ca2-4ce0-aa16-398effc80d9c

        :expectedresults: drpms can be listed in content view in proper
            lifecycle environment
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        repo = entities.Repository(
            product=self.product,
            url=FAKE_YUM_DRPM_REPO,
        ).create()
        repo.sync()
        cv = entities.ContentView(organization=self.org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        promote(cv.version[0], lce.id)
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}'
            '/drpms/ | grep .drpm'
            .format(
                self.org.label,
                lce.name,
                cv.label,
                self.product.label,
                repo.label,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)


class FileRepositoryTestCase(APITestCase):
    """Specific tests for File Repositories"""
    @stubbed()
    @tier1
    def test_positive_upload_file_to_file_repo(self):
        """Check arbitrary file can be uploaded to File Repository

        :id: fdb46481-f0f4-45aa-b075-2a8f6725e51b

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

        :id: 03b4b7dd-0505-4302-ae00-5de33ad420b0

        :Setup:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Steps: Retrieve file permissions from File Repository

        :expectedresults: uploaded file permissions are kept after upload

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_remove_file(self):
        """Check arbitrary file can be removed from File Repository

        :id: 65068b4c-9018-4baa-b87b-b6e9d7384a5d

        :Setup:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Steps: Remove a file from File Repository

        :expectedresults: file is not listed under File Repository after
            removal

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier4
    @upgrade
    def test_positive_remote_directory_sync(self):
        """Check an entire remote directory can be synced to File Repository
        through http

        :id: 5c29b758-004a-4c71-a860-7087a0e96747

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
            2. Make the directory available through http

        :Steps:
            1. Create a File Repository with url pointing to http url
                created on setup
            2. Initialize synchronization


        :expectedresults: entire directory is synced over http

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_local_directory_sync(self):
        """Check an entire local directory can be synced to File Repository

        :id: 178145e6-62e1-4cb9-b825-44d3ab41e754

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
                locally (on the Satellite/Foreman host)

        :Steps:
            1. Create a File Repository with url pointing to local url
                created on setup
            2. Initialize synchronization


        :expectedresults: entire directory is synced

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_symlinks_sync(self):
        """Check synlinks can be synced to File Repository

        :id: 438a8e21-3502-4995-86db-c67ba0f3c469

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
                locally (on the Satellite/Foreman host)
            2. Make sure it contains synlinks

        :Steps:
            1. Create a File Repository with url pointing to local url
                created on setup
            2. Initialize synchronization

        :expectedresults: entire directory is synced, including files
            referred by symlinks

        :CaseAutomation: notautomated
        """
