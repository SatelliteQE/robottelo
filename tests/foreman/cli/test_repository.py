"""Test class for Repository CLI

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:Assignee: tpapaioa

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import logging

import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string
from nailgun import entities
from wait_for import wait_for

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_filter
from robottelo.cli.factory import make_gpg_key
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.file import File
from robottelo.cli.filter import Filter
from robottelo.cli.module_stream import ModuleStream
from robottelo.cli.package import Package
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.cli.role import Role
from robottelo.cli.settings import Settings
from robottelo.cli.srpm import Srpm
from robottelo.cli.task import Task
from robottelo.cli.user import User
from robottelo.constants import CUSTOM_FILE_REPO_FILES_COUNT
from robottelo.constants import CUSTOM_LOCAL_FOLDER
from robottelo.constants import DOCKER_REGISTRY_HUB
from robottelo.constants import DOCKER_UPSTREAM_NAME
from robottelo.constants import DOWNLOAD_POLICIES
from robottelo.constants import OS_TEMPLATE_DATA_FILE
from robottelo.constants import REPO_TYPE
from robottelo.constants import RPM_TO_UPLOAD
from robottelo.constants import SRPM_TO_UPLOAD
from robottelo.constants.repos import CUSTOM_FILE_REPO
from robottelo.constants.repos import CUSTOM_MODULE_STREAM_REPO_1
from robottelo.constants.repos import CUSTOM_MODULE_STREAM_REPO_2
from robottelo.constants.repos import FAKE_0_YUM_REPO
from robottelo.constants.repos import FAKE_1_PUPPET_REPO
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.constants.repos import FAKE_2_PUPPET_REPO
from robottelo.constants.repos import FAKE_2_YUM_REPO
from robottelo.constants.repos import FAKE_3_PUPPET_REPO
from robottelo.constants.repos import FAKE_3_YUM_REPO
from robottelo.constants.repos import FAKE_4_PUPPET_REPO
from robottelo.constants.repos import FAKE_4_YUM_REPO
from robottelo.constants.repos import FAKE_5_PUPPET_REPO
from robottelo.constants.repos import FAKE_5_YUM_REPO
from robottelo.constants.repos import FAKE_7_PUPPET_REPO
from robottelo.constants.repos import FAKE_PULP_REMOTE_FILEREPO
from robottelo.constants.repos import FAKE_YUM_DRPM_REPO
from robottelo.constants.repos import FAKE_YUM_MIXED_REPO
from robottelo.constants.repos import FAKE_YUM_SRPM_REPO
from robottelo.constants.repos import FEDORA27_OSTREE_REPO
from robottelo.datafactory import invalid_http_credentials
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_docker_repository_names
from robottelo.datafactory import valid_http_credentials
from robottelo.helpers import get_data_file
from robottelo.utils.issue_handlers import is_open


YUM_REPOS = (FAKE_0_YUM_REPO, FAKE_1_YUM_REPO, FAKE_2_YUM_REPO, FAKE_3_YUM_REPO, FAKE_4_YUM_REPO)
PUPPET_REPOS = (
    FAKE_1_PUPPET_REPO,
    FAKE_2_PUPPET_REPO,
    FAKE_3_PUPPET_REPO,
    FAKE_4_PUPPET_REPO,
    FAKE_5_PUPPET_REPO,
)


def _get_image_tags_count(repo):
    return Repository.info({'id': repo['id']})


def _validated_image_tags_count(repo):
    """Wrapper around Repository.info(), that returns once
    container-image-tags in repo is greater than 0.
    Needed due to BZ#1664631 (container-image-tags is not populated
    immediately after synchronization), which was CLOSED WONTFIX
    """
    wait_for(
        lambda: int(_get_image_tags_count(repo=repo)['content-counts']['container-image-tags'])
        > 0,
        timeout=30,
        delay=2,
        logger=logging.getLogger('robottelo'),
    )
    return _get_image_tags_count(repo=repo)


@pytest.fixture
def repo_options(request, module_org, module_product):
    """Return the options that were passed as indirect parameters."""
    options = getattr(request, 'param', {}).copy()
    options['organization-id'] = module_org.id
    options['product-id'] = module_product.id
    return options


@pytest.fixture
def repo(repo_options):
    """create a new repository."""
    return make_repository(repo_options)


@pytest.fixture
def gpg_key(module_org):
    """Create a new GPG key."""
    return make_gpg_key({'organization-id': module_org.id})


class TestRepository:
    """Repository CLI tests."""

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        [
            {
                'content-type': 'docker',
                'name': gen_string('alpha'),
                'docker-upstream-name': 'fedora/rabbitmq',
            }
        ],
        indirect=True,
    )
    def test_positive_info_docker_upstream_name(self, repo_options, repo):
        """Check if repository docker-upstream-name is shown
        in repository info

        :id: f197a14c-2cf3-4564-9b18-5fd37d469ea4

        :parametrized: yes

        :expectedresults: repository info command returns upstream-repository-
            name value

        :BZ: 1189289

        :CaseImportance: Critical
        """
        assert repo.get('upstream-repository-name') == repo_options['docker-upstream-name']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': name} for name in valid_data_list().values()]),
        indirect=True,
    )
    def test_positive_create_with_name(self, repo_options, repo):
        """Check if repository can be created with random names

        :id: 604dea2c-d512-4a27-bfc1-24c9655b6ea9

        :parametrized: yes

        :expectedresults: Repository is created and has random name

        :CaseImportance: Critical
        """
        assert repo.get('name') == repo_options['name']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'name': name, 'label': gen_string('alpha', 20)}
                for name in valid_data_list().values()
            ]
        ),
        indirect=True,
    )
    def test_positive_create_with_name_label(self, repo_options, repo):
        """Check if repository can be created with random names and
        labels

        :id: 79d2a6d0-5032-46cd-880c-46cf392521fa

        :parametrized: yes

        :expectedresults: Repository is created and has random name and labels

        :CaseImportance: Critical
        """
        for key in 'name', 'label':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': url} for url in YUM_REPOS]),
        indirect=True,
    )
    def test_positive_create_with_yum_repo(self, repo_options, repo):
        """Create YUM repository

        :id: 4c08824f-ba95-486c-94c2-9abf0a3441ea

        :parametrized: yes

        :expectedresults: YUM repository is created

        :CaseImportance: Critical
        """
        for key in 'url', 'content-type':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'puppet', 'url': url} for url in PUPPET_REPOS]),
        indirect=True,
    )
    def test_positive_create_with_puppet_repo(self, repo_options, repo):
        """Create Puppet repository

        :id: 75c309ba-fbc9-419d-8427-7a61b063ec13

        :parametrized: yes

        :expectedresults: Puppet repository is created

        :CaseImportance: Critical
        """
        for key in 'url', 'content-type':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_create_with_file_repo(self, repo_options, repo):
        """Create file repository

        :id: 46f63419-1acc-4ae2-be8c-d97816ba342f

        :parametrized: yes

        :expectedresults: file repository is created

        :CaseImportance: Critical
        """
        for key in 'url', 'content-type':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'content-type': 'yum', 'url': FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])}
                for cred in valid_http_credentials(url_encoded=True)
            ]
        ),
        indirect=True,
    )
    def test_positive_create_with_auth_yum_repo(self, repo_options, repo):
        """Create YUM repository with basic HTTP authentication

        :id: da8309fd-3076-427b-a96f-8d883d6e944f

        :parametrized: yes

        :expectedresults: YUM repository is created

        :CaseImportance: Critical
        """
        for key in 'url', 'content-type':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [{'content-type': 'yum', 'download-policy': policy} for policy in DOWNLOAD_POLICIES]
        ),
        indirect=True,
    )
    def test_positive_create_with_download_policy(self, repo_options, repo):
        """Create YUM repositories with available download policies

        :id: ffb386e6-c360-4d4b-a324-ccc21768b4f8

        :parametrized: yes

        :expectedresults: YUM repository with a download policy is created

        :CaseImportance: Critical
        """
        assert repo.get('download-policy') == repo_options['download-policy']

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [{'content-type': 'yum', 'mirror-on-sync': value} for value in ('yes', 'no')]
        ),
        indirect=True,
    )
    def test_positive_create_with_mirror_on_sync(self, repo_options, repo):
        """Create YUM repositories with available mirror on sync rule

        :id: 37a09a91-42fc-4271-b58b-8e00ef0dc5a7

        :parametrized: yes

        :expectedresults: YUM repository created successfully and its mirror on
            sync rule value can be read back

        :BZ: 1383258

        :CaseImportance: Critical
        """
        assert repo.get('mirror-on-sync') == repo_options['mirror-on-sync']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'content-type': 'yum'}]), indirect=True
    )
    def test_positive_create_with_default_download_policy(self, repo_options, repo):
        """Verify if the default download policy is assigned when creating a
        YUM repo without `--download-policy`

        :id: 9a3c4d95-d6ca-4377-9873-2c552b7d6ce7

        :parametrized: yes

        :expectedresults: YUM repository with a default download policy

        :CaseImportance: Critical
        """
        default_dl_policy = Settings.list({'search': 'name=default_download_policy'})
        assert default_dl_policy
        assert repo.get('download-policy') == default_dl_policy[0]['value']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'content-type': 'yum'}]), indirect=True
    )
    def test_positive_create_immediate_update_to_on_demand(self, repo_options, repo):
        """Update `immediate` download policy to `on_demand` for a newly
        created YUM repository

        :id: 1a80d686-3f7b-475e-9d1a-3e1f51d55101

        :parametrized: yes

        :expectedresults: immediate download policy is updated to on_demand

        :CaseImportance: Critical

        :BZ: 1732056
        """
        assert repo.get('download-policy') == 'immediate'
        Repository.update({'id': repo['id'], 'download-policy': 'on_demand'})
        result = Repository.info({'id': repo['id']})
        assert result.get('download-policy') == 'on_demand'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'immediate'}]),
        indirect=True,
    )
    def test_positive_create_immediate_update_to_background(self, repo_options, repo):
        """Update `immediate` download policy to `background` for a newly
        created YUM repository

        :id: 7a9243eb-012c-40ad-9105-b078ed0a9eda

        :parametrized: yes

        :expectedresults: immediate download policy is updated to background

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'download-policy': 'background'})
        result = Repository.info({'id': repo['id']})
        assert result['download-policy'] == 'background'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'on_demand'}]),
        indirect=True,
    )
    def test_positive_create_on_demand_update_to_immediate(self, repo_options, repo):
        """Update `on_demand` download policy to `immediate` for a newly
        created YUM repository

        :id: 1e8338af-32e5-4f92-9215-bfdc1973c8f7

        :parametrized: yes

        :expectedresults: on_demand download policy is updated to immediate

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'download-policy': 'immediate'})
        result = Repository.info({'id': repo['id']})
        assert result['download-policy'] == 'immediate'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'on_demand'}]),
        indirect=True,
    )
    def test_positive_create_on_demand_update_to_background(self, repo_options, repo):
        """Update `on_demand` download policy to `background` for a newly
        created YUM repository

        :id: da600200-5bd4-4cb8-a891-37cd2233803e

        :parametrized: yes

        :expectedresults: on_demand download policy is updated to background

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'download-policy': 'background'})
        result = Repository.info({'id': repo['id']})
        assert result['download-policy'] == 'background'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'background'}]),
        indirect=True,
    )
    def test_positive_create_background_update_to_immediate(self, repo_options, repo):
        """Update `background` download policy to `immediate` for a newly
        created YUM repository

        :id: cf4dca0c-36bd-4a3c-aa29-f435ac60b3f8

        :parametrized: yes

        :expectedresults: background download policy is updated to immediate

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'download-policy': 'immediate'})
        result = Repository.info({'id': repo['id']})
        assert result['download-policy'] == 'immediate'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'background'}]),
        indirect=True,
    )
    def test_positive_create_background_update_to_on_demand(self, repo_options, repo):
        """Update `background` download policy to `on_demand` for a newly
        created YUM repository

        :id: 0f943e3d-44b7-4b6e-9a7d-d33f7f4864d1

        :parametrized: yes

        :expectedresults: background download policy is updated to on_demand

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'download-policy': 'on_demand'})
        result = Repository.info({'id': repo['id']})
        assert result['download-policy'] == 'on_demand'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'puppet',
                    'url': FAKE_7_PUPPET_REPO.format(cred['login'], cred['pass']),
                }
                for cred in valid_http_credentials(url_encoded=True)
            ]
        ),
        indirect=True,
    )
    def test_positive_create_with_auth_puppet_repo(self, repo_options, repo):
        """Create Puppet repository with basic HTTP authentication

        :id: b13f8ae2-60ab-47e6-a096-d3f368e5cab3

        :parametrized: yes

        :expectedresults: Puppet repository is created

        :CaseImportance: Critical
        """
        for key in 'url', 'content-type':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    def test_positive_create_with_gpg_key_by_id(self, repo_options, gpg_key):
        """Check if repository can be created with gpg key ID

        :id: 6d22f0ea-2d27-4827-9b7a-3e1550a47285

        :parametrized: yes

        :expectedresults: Repository is created and has gpg key

        :CaseImportance: Critical
        """
        repo_options['gpg-key-id'] = gpg_key['id']
        repo = make_repository(repo_options)
        assert repo['gpg-key']['id'] == gpg_key['id']
        assert repo['gpg-key']['name'] == gpg_key['name']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    def test_positive_create_with_gpg_key_by_name(
        self, repo_options, module_org, module_product, gpg_key
    ):
        """Check if repository can be created with gpg key name

        :id: 95cde404-3449-410d-9a08-d7f8619a2ad5

        :parametrized: yes

        :expectedresults: Repository is created and has gpg key

        :BZ: 1103944

        :CaseImportance: Critical
        """
        repo_options['gpg-key'] = gpg_key['name']
        repo = make_repository(repo_options)
        assert repo['gpg-key']['id'] == gpg_key['id']
        assert repo['gpg-key']['name'] == gpg_key['name']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'publish-via-http': use_http} for use_http in ('true', 'yes', '1')]),
        indirect=True,
    )
    def test_positive_create_publish_via_http(self, repo_options, repo):
        """Create repository published via http

        :id: faf6058c-9dd3-444c-ace2-c41791669e9e

        :parametrized: yes

        :expectedresults: Repository is created and is published via http

        :CaseImportance: Critical
        """
        assert repo.get('publish-via-http') == 'yes'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'publish-via-http': use_http} for use_http in ('false', 'no', '0')]),
        indirect=True,
    )
    def test_positive_create_publish_via_https(self, repo_options, repo):
        """Create repository not published via http

        :id: 4395a5df-207c-4b34-a42d-7b3273bd68ec

        :parametrized: yes

        :expectedresults: Repository is created and is not published via http

        :CaseImportance: Critical
        """
        assert repo.get('publish-via-http') == 'no'

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'checksum-type': checksum_type,
                    'content-type': 'yum',
                    'download-policy': 'immediate',
                }
                for checksum_type in ('sha1', 'sha256')
            ]
        ),
        indirect=True,
    )
    def test_positive_create_yum_repo_with_checksum_type(self, repo_options, repo):
        """Create a YUM repository with a checksum type

        :id: 934f4a09-2a64-485d-ae6c-8ef73aa8fb2b

        :parametrized: yes

        :expectedresults: A YUM repository is created and contains the correct
            checksum type

        :CaseImportance: Critical
        """
        for key in 'content-type', 'checksum-type':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': DOCKER_UPSTREAM_NAME,
                    'name': valid_docker_repository_names()[0],
                    'url': DOCKER_REGISTRY_HUB,
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_create_docker_repo_with_upstream_name(self, repo_options, repo):
        """Create a Docker repository with upstream name.

        :id: 776f92eb-8b40-4efd-8315-4fbbabcb2d4e

        :parametrized: yes

        :expectedresults: Docker repository is created and contains correct
            values.

        :CaseImportance: Critical
        """
        for key in 'url', 'content-type', 'name':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': DOCKER_UPSTREAM_NAME,
                    'name': name,
                    'url': DOCKER_REGISTRY_HUB,
                }
                for name in valid_docker_repository_names()
            ]
        ),
        indirect=True,
    )
    def test_positive_create_docker_repo_with_name(self, repo_options, repo):
        """Create a Docker repository with a random name.

        :id: b6a01434-8672-4196-b61a-dcb86c49f43b

        :parametrized: yes

        :expectedresults: Docker repository is created and contains correct
            values.

        :CaseImportance: Critical
        """
        for key in 'url', 'content-type', 'name':
            assert repo.get(key) == repo_options[key]

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [{'content-type': 'puppet', 'url': 'https://omaciel.fedorapeople.org/b3502064/'}]
        ),
        indirect=True,
    )
    def test_positive_create_puppet_repo_same_url_different_orgs(self, repo_options, repo):
        """Create two repos with the same URL in two different organizations.

        :id: b3502064-f400-4e60-a11f-b3772bd23a98

        :parametrized: yes

        :expectedresults: Repositories are created and puppet modules are
            visible from different organizations.

        :CaseLevel: Integration
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['puppet-modules'] == '1'

        # Create the repo in another org.
        org_2 = make_org()
        product_2 = make_product({'organization-id': org_2['id']})
        repo_options_2 = repo_options.copy()
        repo_options_2['organization-id'] = org_2['id']
        repo_options_2['product-id'] = product_2['id']
        repo_2 = make_repository(repo_options_2)

        Repository.synchronize({'id': repo_2['id']})
        repo_2 = Repository.info({'id': repo_2['id']})
        assert repo_2['content-counts']['puppet-modules'] == '1'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': name} for name in invalid_values_list()]),
        indirect=True,
    )
    def test_negative_create_with_name(self, repo_options):
        """Repository name cannot be 300-characters long

        :id: af0652d3-012d-4846-82ac-047918f74722

        :parametrized: yes

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'url': repo.format(cred['login'], cred['pass'])}
                for cred in valid_http_credentials()
                if cred['quote']
                for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
            ]
        ),
        indirect=True,
    )
    def test_negative_create_with_auth_url_with_special_characters(self, repo_options):
        """Verify that repository URL cannot contain unquoted special characters

        :id: 2bd5ee17-0fe5-43cb-9cdc-dc2178c5374c

        :parametrized: yes

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'url': repo.format(cred['login'], cred['pass'])}
                for cred in invalid_http_credentials()
                for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
            ]
        ),
        indirect=True,
    )
    def test_negative_create_with_auth_url_too_long(self, repo_options):
        """Verify that repository URL length is limited

        :id: de356c66-4237-4421-89e3-f4f8bbe6f526

        :parametrized: yes

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': gen_string('alpha', 5)}]),
        indirect=True,
    )
    def test_negative_create_with_invalid_download_policy(self, repo_options):
        """Verify that YUM repository cannot be created with invalid download
        policy

        :id: 3b143bf8-7056-4c94-910d-69a451071f26

        :parametrized: yes

        :expectedresults: YUM repository is not created with invalid download
            policy

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'content-type': 'yum'}]), indirect=True
    )
    def test_negative_update_to_invalid_download_policy(self, repo_options, repo):
        """Verify that YUM repository cannot be updated to invalid download
        policy

        :id: 5bd6a2e4-7ff0-42ac-825a-6b2a2f687c89

        :parametrized: yes

        :expectedresults: YUM repository is not updated to invalid download
            policy

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            Repository.update({'id': repo['id'], 'download-policy': gen_string('alpha', 5)})

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'content-type': content_type, 'download-policy': 'on_demand'}
                for content_type in REPO_TYPE.keys()
                if content_type != 'yum'
            ]
        ),
        indirect=True,
    )
    def test_negative_create_non_yum_with_download_policy(self, repo_options):
        """Verify that non-YUM repositories cannot be created with download
        policy

        :id: 71388973-50ea-4a20-9406-0aca142014ca

        :parametrized: yes

        :expectedresults: Non-YUM repository is not created with a download
            policy

        :BZ: 1439835

        :CaseImportance: Critical
        """
        with pytest.raises(
            CLIFactoryError,
            match='Download policy Cannot set attribute download_policy for content type',
        ):
            make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'content-type': 'yum', 'url': url}
                for url in (FAKE_1_YUM_REPO, FAKE_3_YUM_REPO, FAKE_4_YUM_REPO)
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_yum_repo(self, repo_options, repo):
        """Check if repository can be created and synced

        :id: e3a62529-edbd-4062-9246-bef5f33bdcf0

        :parametrized: yes

        :expectedresults: Repository is created and synced

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_synchronize_file_repo(self, repo_options, repo):
        """Check if repository can be created and synced

        :id: eafc421d-153e-41e1-afbd-938e556ef827

        :parametrized: yes

        :expectedresults: Repository is created and synced

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Assertion that repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert int(repo['content-counts']['files']) == CUSTOM_FILE_REPO_FILES_COUNT

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'content-type': 'yum', 'url': FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])}
                for cred in valid_http_credentials(url_encoded=True)
                if cred['http_valid']
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_auth_yum_repo(self, repo):
        """Check if secured repository can be created and synced

        :id: b0db676b-e0f0-428c-adf3-1d7c0c3599f0

        :parametrized: yes

        :expectedresults: Repository is created and synced

        :BZ: 1328092

        :CaseLevel: Integration
        """
        # Assertion that repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': repo['id']})
        assert new_repo['sync']['status'] == 'Success'

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options, creds',
        **parametrized(
            [
                (
                    {
                        'content-type': 'yum',
                        'url': FAKE_5_YUM_REPO.format(cred['login'], cred['pass']),
                    },
                    cred,
                )
                for cred in valid_http_credentials(url_encoded=True)
                if not cred['http_valid']
            ]
        ),
        indirect=['repo_options'],
    )
    def test_negative_synchronize_auth_yum_repo(self, creds, repo):
        """Check if secured repo fails to synchronize with invalid credentials

        :id: 809905ae-fb76-465d-9468-1f99c4274aeb

        :parametrized: yes

        :expectedresults: Repository is created but synchronization fails

        :BZ: 1405503, 1453118

        :CaseLevel: Integration
        """
        # Try to synchronize it
        repo_sync = Repository.synchronize({'id': repo['id'], 'async': True})
        response = Task.progress({'id': repo_sync[0]['id']}, return_raw_response=True)
        if creds['original_encoding'] == 'utf8':
            assert "Error retrieving metadata: 'latin-1' codec can't encode characters" in ''.join(
                response.stderr
            )
        else:
            assert 'Error retrieving metadata: Unauthorized' in ''.join(response.stderr)

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'puppet',
                    'url': FAKE_7_PUPPET_REPO.format(cred['login'], cred['pass']),
                }
                for cred in valid_http_credentials(url_encoded=True)
                if cred['http_valid']
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_auth_puppet_repo(self, repo):
        """Check if secured puppet repository can be created and synced

        :id: 1d2604fc-8a18-4cbe-bf4c-5c7d9fbdb82c

        :parametrized: yes

        :expectedresults: Repository is created and synced

        :BZ: 1405503

        :CaseLevel: Integration
        """
        # Assertion that repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': repo['id']})
        assert new_repo['sync']['status'] == 'Success'

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': DOCKER_UPSTREAM_NAME,
                    'name': valid_docker_repository_names()[0],
                    'url': DOCKER_REGISTRY_HUB,
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_docker_repo(self, repo):
        """Check if Docker repository can be created and synced

        :id: cb9ae788-743c-4785-98b2-6ae0c161bc9a

        :parametrized: yes

        :expectedresults: Docker repository is created and synced
        """
        # Assertion that repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': repo['id']})
        assert new_repo['sync']['status'] == 'Success'

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': DOCKER_UPSTREAM_NAME,
                    'url': DOCKER_REGISTRY_HUB,
                    'docker-tags-whitelist': 'latest',
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_docker_repo_with_tags_whitelist(self, repo_options, repo):
        """Check if only whitelisted tags are synchronized

        :id: aa820c65-2de1-4b32-8890-98bd8b4320dc

        :parametrized: yes

        :expectedresults: Only whitelisted tag is synchronized
        """
        Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo)
        assert repo_options['docker-tags-whitelist'] in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) == 1

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': DOCKER_UPSTREAM_NAME,
                    'url': DOCKER_REGISTRY_HUB,
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_docker_repo_set_tags_later(self, repo):
        """Verify that adding tags whitelist and re-syncing after
        synchronizing full repository doesn't remove content that was
        already pulled in

        :id: 97f2087f-6041-4242-8b7c-be53c68f46ff

        :parametrized: yes

        :expectedresults: Non-whitelisted tags are not removed
        """
        tags = 'latest'
        Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo)
        assert not repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) >= 2
        Repository.update({'id': repo['id'], 'docker-tags-whitelist': tags})
        Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo)
        assert tags in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) >= 2

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': DOCKER_UPSTREAM_NAME,
                    'url': DOCKER_REGISTRY_HUB,
                    'docker-tags-whitelist': f"latest,{gen_string('alpha')}",
                }
            ]
        ),
        indirect=True,
    )
    def test_negative_synchronize_docker_repo_with_mix_valid_invalid_tags(
        self, repo_options, repo
    ):
        """Set tags whitelist to contain both valid and invalid (non-existing)
        tags. Check if only whitelisted tags are synchronized

        :id: 75668da8-cc94-4d39-ade1-d3ef91edc812

        :parametrized: yes

        :expectedresults: Only whitelisted tag is synchronized
        """
        Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo)
        for tag in repo_options['docker-tags-whitelist'].split(','):
            assert tag in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) == 1

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': DOCKER_UPSTREAM_NAME,
                    'url': DOCKER_REGISTRY_HUB,
                    'docker-tags-whitelist': ",".join([gen_string('alpha') for _ in range(3)]),
                }
            ]
        ),
        indirect=True,
    )
    def test_negative_synchronize_docker_repo_with_invalid_tags(self, repo_options, repo):
        """Set tags whitelist to contain only invalid (non-existing)
        tags. Check that no data is synchronized.

        :id: da05cdb1-2aea-48b9-9424-6cc700bc1194

        :parametrized: yes

        :expectedresults: Tags are not synchronized
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        for tag in repo_options['docker-tags-whitelist'].split(','):
            assert tag in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) == 0

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': FAKE_1_YUM_REPO}]),
        indirect=True,
    )
    def test_positive_resynchronize_rpm_repo(self, repo):
        """Check that repository content is resynced after packages were
        removed from repository

        :id: a21b6710-4f12-4722-803e-3cb29d70eead

        :parametrized: yes

        :expectedresults: Repository has updated non-zero packages count

        :BZ: 1459845, 1459874, 1318004

        :CaseLevel: Integration
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'
        # Find repo packages and remove them
        packages = Package.list({'repository-id': repo['id']})
        Repository.remove_content(
            {'id': repo['id'], 'ids': [package['id'] for package in packages]}
        )
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '0'
        # Re-synchronize repository
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'puppet', 'url': FAKE_1_PUPPET_REPO}]),
        indirect=True,
    )
    def test_positive_resynchronize_puppet_repo(self, repo):
        """Check that repository content is resynced after puppet modules
        were removed from repository

        :id: 9e28f0ae-3875-4c1e-ad8b-d068f4409fe3

        :parametrized: yes

        :expectedresults: Repository has updated non-zero puppet modules count

        :BZ: 1459845, 1318004

        :CaseLevel: Integration
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['puppet-modules'] == '2'
        # Find repo packages and remove them
        modules = PuppetModule.list({'repository-id': repo['id']})
        Repository.remove_content({'id': repo['id'], 'ids': [module['id'] for module in modules]})
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['puppet-modules'] == '0'
        # Re-synchronize repository
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['puppet-modules'] == '2'

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'yum',
                    'url': FAKE_YUM_MIXED_REPO,
                    'ignorable-content': ['erratum', 'srpm', 'drpm'],
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_rpm_repo_ignore_content(self, module_org, module_product, repo):
        """Synchronize yum repository with ignore content setting

        :id: fa32ff10-e2e2-4ee0-b444-82f66f4a0e96

        :parametrized: yes

        :expectedresults: Selected content types are ignored during
            synchronization

        :BZ: 1591358

        :CaseLevel: Integration

        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        # Check synced content types
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '5', 'content not synced correctly'
        assert repo['content-counts']['errata'] == '0', 'content not ignored correctly'
        assert repo['content-counts']['source-rpms'] == '0', 'content not ignored correctly'
        # drpm check requires a different method
        result = ssh.command(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/Library"
            f"/custom/{module_product.label}/{repo['label']}/drpms/ | grep .drpm"
        )
        # expecting No such file or directory for drpms
        assert result.return_code == 1
        assert 'No such file or directory' in result.stderr

        # Find repo packages and remove them
        packages = Package.list({'repository-id': repo['id']})
        Repository.remove_content(
            {'id': repo['id'], 'ids': [package['id'] for package in packages]}
        )
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '0'

        # Update the ignorable-content setting
        Repository.update({'id': repo['id'], 'ignorable-content': ['rpm']})

        # Re-synchronize repository
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        # Re-check synced content types
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '0', 'content not ignored correctly'
        assert repo['content-counts']['errata'] == '2', 'content not synced correctly'
        if not is_open('BZ:1664549'):
            assert repo['content-counts']['source-rpms'] == '3', 'content not synced correctly'

        if not is_open('BZ:1682951'):
            result = ssh.command(
                f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/Library"
                f"/custom/{module_product.label}/{repo['label']}/drpms/ | grep .drpm"
            )
            assert result.return_code == 0
            assert len(result.stdout) >= 4, 'content not synced correctly'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'new_repo_options',
        **parametrized(
            [
                {'url': url}
                for url in [
                    repo.format(creds['login'], creds['pass'])
                    for creds in valid_http_credentials(url_encoded=True)
                    for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
                ]
                + [
                    FAKE_4_YUM_REPO,
                    FAKE_1_PUPPET_REPO,
                    FAKE_2_PUPPET_REPO,
                    FAKE_3_PUPPET_REPO,
                    FAKE_2_YUM_REPO,
                ]
            ]
        ),
    )
    def test_positive_update_url(self, new_repo_options, repo):
        """Update the original url for a repository

        :id: 1a2cf29b-5c30-4d4c-b6d1-2f227b0a0a57

        :parametrized: yes

        :expectedresults: Repository url is updated

        :CaseImportance: Critical
        """
        # Update the url
        Repository.update({'id': repo['id'], 'url': new_repo_options['url']})
        # Fetch it again
        result = Repository.info({'id': repo['id']})
        assert result['url'] == new_repo_options['url']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    @pytest.mark.parametrize(
        'new_repo_options',
        **parametrized(
            [
                {'url': repo.format(cred['login'], cred['pass'])}
                for cred in valid_http_credentials()
                if cred['quote']
                for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
            ]
        ),
    )
    def test_negative_update_auth_url_with_special_characters(self, new_repo_options, repo):
        """Verify that repository URL credentials cannot be updated to contain
        the forbidden characters

        :id: 566553b2-d077-4fd8-8ed5-00ba75355386

        :parametrized: yes

        :expectedresults: Repository url not updated

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            Repository.update({'id': repo['id'], 'url': new_repo_options['url']})
        # Fetch it again, ensure url hasn't changed.
        result = Repository.info({'id': repo['id']})
        assert result['url'] == repo['url']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    @pytest.mark.parametrize(
        'new_repo_options',
        **parametrized(
            [
                {'url': repo.format(cred['login'], cred['pass'])}
                for cred in invalid_http_credentials()
                for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
            ]
        ),
    )
    def test_negative_update_auth_url_too_long(self, new_repo_options, repo):
        """Update the original url for a repository to value which is too long

        :id: a703de60-8631-4e31-a9d9-e51804f27f03

        :parametrized: yes

        :expectedresults: Repository url not updated

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            Repository.update({'id': repo['id'], 'url': new_repo_options['url']})
        # Fetch it again, ensure url is unchanged.
        result = Repository.info({'id': repo['id']})
        assert result['url'] == repo['url']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    def test_positive_update_gpg_key(self, repo_options, module_org, repo, gpg_key):
        """Update the original gpg key

        :id: 367ff375-4f52-4a8c-b974-8c1c54e3fdd3

        :parametrized: yes

        :expectedresults: Repository gpg key is updated

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'gpg-key-id': gpg_key['id']})

        gpg_key_new = make_gpg_key({'organization-id': module_org.id})
        Repository.update({'id': repo['id'], 'gpg-key-id': gpg_key_new['id']})
        result = Repository.info({'id': repo['id']})
        assert result['gpg-key']['id'] == gpg_key_new['id']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'mirror-on-sync': 'no'}]), indirect=True
    )
    def test_positive_update_mirror_on_sync(self, repo):
        """Update the mirror on sync rule for repository

        :id: 9bab2537-3223-40d7-bc4c-a51b09d2e812

        :parametrized: yes

        :expectedresults: Repository is updated

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'mirror-on-sync': 'yes'})
        result = Repository.info({'id': repo['id']})
        assert result['mirror-on-sync'] == 'yes'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'publish-via-http': 'no'}]), indirect=True
    )
    def test_positive_update_publish_method(self, repo):
        """Update the original publishing method

        :id: e7bd2667-4851-4a64-9c70-1b5eafbc3f71

        :parametrized: yes

        :expectedresults: Repository publishing method is updated

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'publish-via-http': 'yes'})
        result = Repository.info({'id': repo['id']})
        assert result['publish-via-http'] == 'yes'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'immediate'}]),
        indirect=True,
    )
    @pytest.mark.parametrize('checksum_type', ['sha1', 'sha256'])
    def test_positive_update_checksum_type(self, repo_options, repo, checksum_type):
        """Create a YUM repository and update the checksum type

        :id: 42f14257-d860-443d-b337-36fd355014bc

        :parametrized: yes

        :expectedresults: A YUM repository is updated and contains the correct
            checksum type

        :CaseImportance: Critical
        """
        assert repo['content-type'] == repo_options['content-type']
        Repository.update({'checksum-type': checksum_type, 'id': repo['id']})
        result = Repository.info({'id': repo['id']})
        assert result['checksum-type'] == checksum_type

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'yum',
                    'checksum-type': checksum_type,
                    'download-policy': 'on_demand',
                }
                for checksum_type in ('sha1', 'sha256')
            ]
        ),
        indirect=True,
    )
    def test_negative_create_checksum_with_on_demand_policy(self, repo_options):
        """Attempt to create repository with checksum and on_demand policy.

        :id: 33d712e6-e91f-42bb-8c5d-35bdc427182c

        :parametrized: yes

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical

        :BZ: 1732056
        """
        with pytest.raises(CLIFactoryError):
            make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': name} for name in valid_data_list().values()]),
        indirect=True,
    )
    def test_positive_delete_by_id(self, repo):
        """Check if repository can be created and deleted

        :id: bcf096db-0033-4138-90a3-cb7355d5dfaf

        :parametrized: yes

        :expectedresults: Repository is created and then deleted

        :CaseImportance: Critical
        """
        Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': name} for name in valid_data_list().values()]),
        indirect=True,
    )
    def test_positive_delete_by_name(self, repo_options, repo):
        """Check if repository can be created and deleted

        :id: 463980a4-dbcf-4178-83a6-1863cf59909a

        :parametrized: yes

        :expectedresults: Repository is created and then deleted

        :CaseImportance: Critical
        """
        Repository.delete({'name': repo['name'], 'product-id': repo_options['product-id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': FAKE_1_YUM_REPO}]),
        indirect=True,
    )
    def test_positive_delete_rpm(self, repo):
        """Check if rpm repository with packages can be deleted.

        :id: 1172492f-d595-4c8e-89c1-fabb21eb04ac

        :parametrized: yes

        :expectedresults: Repository is deleted.

        :CaseImportance: Critical
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        # Check that there is at least one package
        assert int(repo['content-counts']['packages']) > 0
        Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'puppet', 'url': FAKE_1_PUPPET_REPO}]),
        indirect=True,
    )
    def test_positive_delete_puppet(self, repo):
        """Check if puppet repository with puppet modules can be deleted.

        :id: 83d92454-11b7-4f9a-952d-650ffe5135e4

        :parametrized: yes

        :expectedresults: Repository is deleted.

        :BZ: 1316681

        :CaseImportance: Critical
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        # Check that there is at least one puppet module
        assert int(repo['content-counts']['puppet-modules']) > 0
        Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': FAKE_1_YUM_REPO}]),
        indirect=True,
    )
    def test_positive_remove_content_by_repo_name(self, module_org, module_product, repo):
        """Synchronize and remove rpm content using repo name

        :id: a8b6f17d-3b13-4185-920a-2558ace59458

        :parametrized: yes

        :expectedresults: Content Counts shows zero packages

        :BZ: 1349646, 1413145, 1459845, 1459874

        :CaseImportance: Critical
        """
        Repository.synchronize(
            {
                'name': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
            }
        )
        repo = Repository.info(
            {
                'name': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
            }
        )
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'
        # Find repo packages and remove them
        packages = Package.list(
            {
                'repository': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
            }
        )
        Repository.remove_content(
            {
                'name': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
                'ids': [package['id'] for package in packages],
            }
        )
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '0'

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': FAKE_1_YUM_REPO}]),
        indirect=True,
    )
    def test_positive_remove_content_rpm(self, repo):
        """Synchronize repository and remove rpm content from it

        :id: c4bcda0e-c0d6-424c-840d-26684ca7c9f1

        :parametrized: yes

        :expectedresults: Content Counts shows zero packages

        :BZ: 1459845, 1459874

        :CaseImportance: Critical
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'
        # Find repo packages and remove them
        packages = Package.list({'repository-id': repo['id']})
        Repository.remove_content(
            {'id': repo['id'], 'ids': [package['id'] for package in packages]}
        )
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '0'

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'puppet', 'url': FAKE_1_PUPPET_REPO}]),
        indirect=True,
    )
    def test_positive_remove_content_puppet(self, repo):
        """Synchronize repository and remove puppet content from it

        :id: b025ccd0-9beb-4ac0-9fbf-21340c90650e

        :parametrized: yes

        :expectedresults: Content Counts shows zero puppet modules

        :BZ: 1459845

        :CaseImportance: Critical
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['puppet-modules'] == '2'
        # Find puppet modules and remove them from repository
        modules = PuppetModule.list({'repository-id': repo['id']})
        Repository.remove_content({'id': repo['id'], 'ids': [module['id'] for module in modules]})
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['puppet-modules'] == '0'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    def test_positive_upload_content(self, repo):
        """Create repository and upload content

        :id: eb0ec599-2bf1-483a-8215-66652f948d67

        :parametrized: yes

        :expectedresults: upload content is successful

        :BZ: 1343006, 1421298

        :CaseImportance: Critical
        """
        ssh.upload_file(
            local_file=get_data_file(RPM_TO_UPLOAD), remote_file=f"/tmp/{RPM_TO_UPLOAD}"
        )
        result = Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{RPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{RPM_TO_UPLOAD}'" in result[0]['message']
        assert int(Repository.info({'id': repo['id']})['content-counts']['packages']) == 1

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_upload_content_to_file_repo(self, repo):
        """Create file repository and upload content to it

        :id: 5e24b416-2928-4533-96cf-6bffbea97a95

        :parametrized: yes

        :customerscenario: true

        :expectedresults: upload content operation is successful

        :BZ: 1446975, 1421298

        :CaseImportance: Critical
        """
        Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        new_repo = Repository.info({'id': repo['id']})
        assert int(new_repo['content-counts']['files']) == CUSTOM_FILE_REPO_FILES_COUNT
        ssh.upload_file(
            local_file=get_data_file(OS_TEMPLATE_DATA_FILE),
            remote_file=f"/tmp/{OS_TEMPLATE_DATA_FILE}",
        )
        result = Repository.upload_content(
            {
                'name': new_repo['name'],
                'organization': new_repo['organization'],
                'path': f"/tmp/{OS_TEMPLATE_DATA_FILE}",
                'product-id': new_repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{OS_TEMPLATE_DATA_FILE}'" in result[0]['message']
        new_repo = Repository.info({'id': new_repo['id']})
        assert int(new_repo['content-counts']['files']) == CUSTOM_FILE_REPO_FILES_COUNT + 1

    @pytest.mark.skip_if_open("BZ:1410916")
    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': FAKE_1_YUM_REPO}]),
        indirect=True,
    )
    def test_negative_restricted_user_cv_add_repository(self, module_org, repo):
        """Attempt to add a product repository to content view with a
        restricted user, using product name not visible to restricted user.

        :id: 65792ae0-c5be-4a6c-9062-27dc03b83e10

        :parametrized: yes

        :BZ: 1436209,1410916

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
                    'export_products',
                ],
                'name ~ "Test_*" || name ~ "rhel7*"',
            ),
            'Katello::ContentView': (
                [
                    'view_content_views',
                    'create_content_views',
                    'edit_content_views',
                    'destroy_content_views',
                    'publish_content_views',
                    'promote_or_remove_content_views',
                    'export_content_views',
                ],
                'name ~ "Test_*" || name ~ "rhel7*"',
            ),
            'Organization': (
                [
                    'view_organizations',
                    'create_organizations',
                    'edit_organizations',
                    'destroy_organizations',
                    'assign_organizations',
                ],
                None,
            ),
        }
        user_name = gen_alphanumeric()
        user_password = gen_alphanumeric()
        # Generate a content view name like Test_*
        content_view_name = f"Test_{gen_string('alpha', 20)}"

        # Create a non admin user, for the moment without any permissions
        user = make_user(
            {
                'admin': False,
                'default-organization-id': module_org.id,
                'organization-ids': [module_org.id],
                'login': user_name,
                'password': user_password,
            }
        )
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
            assert resource_type in available_rc_permissions
            available_permission_names = [
                permission['name']
                for permission in available_rc_permissions[resource_type]
                if permission['name'] in permission_names
            ]
            # assert that all the required permissions are available
            assert set(permission_names) == set(available_permission_names)
            # Create the current resource type role permissions
            make_filter({'role-id': role['id'], 'permissions': permission_names, 'search': search})
        # Add the created and initiated role with permissions to user
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # assert that the user is not an admin one and cannot read the current
        # role info (note: view_roles is not in the required permissions)
        with pytest.raises(
            CLIReturnCodeError,
            match=r'Access denied\\nMissing one of the required permissions: view_roles',
        ):
            Role.with_user(user_name, user_password).info({'id': role['id']})

        Repository.synchronize({'id': repo['id']})

        # Create a content view
        content_view = make_content_view(
            {'organization-id': module_org.id, 'name': content_view_name}
        )
        # assert that the user can read the content view info as per required
        # permissions
        user_content_view = ContentView.with_user(user_name, user_password).info(
            {'id': content_view['id']}
        )
        # assert that this is the same content view
        assert content_view['name'] == user_content_view['name']
        # assert admin user is able to view the product
        repos = Repository.list({'organization-id': module_org.id})
        assert len(repos) == 1
        # assert that this is the same repo
        assert repos[0]['id'] == repo['id']
        # assert that restricted user is not able to view the product
        repos = Repository.with_user(user_name, user_password).list(
            {'organization-id': module_org.id}
        )
        assert len(repos) == 0
        # assert that the user cannot add the product repo to content view
        with pytest.raises(CLIReturnCodeError):
            ContentView.with_user(user_name, user_password).add_repository(
                {
                    'id': content_view['id'],
                    'organization-id': module_org.id,
                    'repository-id': repo['id'],
                }
            )
        # assert that restricted user still not able to view the product
        repos = Repository.with_user(user_name, user_password).list(
            {'organization-id': module_org.id}
        )
        assert len(repos) == 0

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    def test_positive_upload_remove_srpm_content(self, repo):
        """Create repository, upload and remove an SRPM content

        :id: 706dc3e2-dacb-4fdd-8eef-5715ce498888

        :parametrized: yes

        :expectedresults: SRPM successfully uploaded and removed

        :CaseImportance: Critical

        :BZ: 1378442
        """
        ssh.upload_file(
            local_file=get_data_file(SRPM_TO_UPLOAD), remote_file=f"/tmp/{SRPM_TO_UPLOAD}"
        )
        # Upload SRPM
        result = Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{SRPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
                'content-type': 'srpm',
            }
        )
        assert f"Successfully uploaded file '{SRPM_TO_UPLOAD}'" in result[0]['message']
        assert int(Repository.info({'id': repo['id']})['content-counts']['source-rpms']) == 1

        # Remove uploaded SRPM
        Repository.remove_content(
            {
                'id': repo['id'],
                'ids': [Srpm.list({'repository-id': repo['id']})[0]['id']],
                'content-type': 'srpm',
            }
        )
        assert int(Repository.info({'id': repo['id']})['content-counts']['source-rpms']) == 0

    @pytest.mark.upgrade
    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': list(valid_data_list().values())[0]}]),
        indirect=True,
    )
    def test_positive_srpm_list_end_to_end(self, repo):
        """Create repository,  upload, list and remove an SRPM content

        :id: 98ad4228-f2e5-438a-9210-5ce6561769f2

        :parametrized: yes

        :expectedresults:
            1. SRPM should be listed repository wise.
            2. SRPM should be listed product wise.
            3. SRPM should be listed for specific and all Organizations.
            4. SRPM should be listed LCE wise.
            5. Able to see info of uploaded SRPM.

        :CaseImportance: High
        """
        ssh.upload_file(
            local_file=get_data_file(SRPM_TO_UPLOAD), remote_file=f"/tmp/{SRPM_TO_UPLOAD}"
        )
        # Upload SRPM
        Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f'/tmp/{SRPM_TO_UPLOAD}',
                'product-id': repo['product']['id'],
                'content-type': 'srpm',
            }
        )
        assert len(Srpm.list()) > 0
        srpm_list = Srpm.list({'repository-id': repo['id']})
        assert srpm_list[0]['filename'] == SRPM_TO_UPLOAD
        assert len(srpm_list) == 1
        assert Srpm.info({'id': srpm_list[0]['id']})[0]['filename'] == SRPM_TO_UPLOAD
        assert int(Repository.info({'id': repo['id']})['content-counts']['source-rpms']) == 1
        assert (
            len(
                Srpm.list(
                    {
                        'organization': repo['organization'],
                        'product-id': repo['product']['id'],
                        'repository-id': repo['id'],
                    }
                )
            )
            > 0
        )
        assert len(Srpm.list({'organization': repo['organization']})) > 0
        assert (
            len(
                Srpm.list(
                    {
                        'organization': repo['organization'],
                        'lifecycle-environment': 'Library',
                    }
                )
            )
            > 0
        )
        assert (
            len(
                Srpm.list(
                    {
                        'content-view': 'Default Organization View',
                        'lifecycle-environment': 'Library',
                        'organization': repo['organization'],
                    }
                )
            )
            > 0
        )

        # Remove uploaded SRPM
        Repository.remove_content(
            {
                'id': repo['id'],
                'ids': [Srpm.list({'repository-id': repo['id']})[0]['id']],
                'content-type': 'srpm',
            }
        )
        assert int(Repository.info({'id': repo['id']})['content-counts']['source-rpms']) == len(
            Srpm.list({'repository-id': repo['id']})
        )

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': CUSTOM_MODULE_STREAM_REPO_2}]),
        indirect=True,
    )
    def test_positive_create_get_update_delete_module_streams(
        self, repo_options, module_org, module_product, repo
    ):
        """Check module-stream get for each create, get, update, delete.

        :id: e9001f76-9bc7-42a7-b8c9-2dccd5bf0b1f2f2e70b8-e446-4a28-9bae-fc870c80e83e

        :parametrized: yes

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

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert (
            repo['content-counts']['module-streams'] == '7'
        ), 'Module Streams not synced correctly'

        # adding repo with same yum url should not change count.
        duplicate_repo = make_repository(repo_options)
        Repository.synchronize({'id': duplicate_repo['id']})

        module_streams = ModuleStream.list({'organization-id': module_org.id})
        assert len(module_streams) == 7, 'Module Streams get worked correctly'
        Repository.update(
            {
                'product-id': module_product.id,
                'id': repo['id'],
                'url': CUSTOM_MODULE_STREAM_REPO_2,
            }
        )
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert (
            repo['content-counts']['module-streams'] == '7'
        ), 'Module Streams not synced correctly'

        Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': CUSTOM_MODULE_STREAM_REPO_1}]),
        indirect=True,
    )
    @pytest.mark.parametrize(
        'repo_options_2',
        **parametrized([{'content-type': 'yum', 'url': CUSTOM_MODULE_STREAM_REPO_2}]),
    )
    def test_module_stream_list_validation(self, module_org, repo, repo_options_2):
        """Check module-stream get with list on hammer.

        :id: 9842a0c3-8532-4b16-a00a-534fc3b0a776ff89f23e-cd00-4d20-84d3-add0ea24abf8

        :parametrized: yes

        :Setup:
            1. valid yum repo with Module Streams.

        :Steps:
            1. Create Yum Repositories with url contain module-streams and Products
            2. Initialize synchronization
            3. Verify the module-stream list with various inputs options

        :expectedresults: Verify the module-stream list response.

        :CaseAutomation: Automated
        """
        Repository.synchronize({'id': repo['id']})

        prod_2 = make_product({'organization-id': module_org.id})
        repo_options_2['organization-id'] = module_org.id
        repo_options_2['product-id'] = prod_2['id']
        repo_2 = make_repository(repo_options_2)

        Repository.synchronize({'id': repo_2['id']})
        module_streams = ModuleStream.list()
        assert len(module_streams) > 13, 'Module Streams list failed'
        module_streams = ModuleStream.list({'product-id': prod_2['id']})
        assert len(module_streams) == 7, 'Module Streams list by product failed'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': CUSTOM_MODULE_STREAM_REPO_2}]),
        indirect=True,
    )
    def test_module_stream_info_validation(self, repo):
        """Check module-stream get with info on hammer.

        :id: ddbeb49e-d292-4dc4-8fb9-e9b768acc441a2c2e797-02b7-4b12-9f95-cffc93254198

        :parametrized: yes

        :Setup:
            1. valid yum repo with Module Streams.

        :Steps:
            1. Create Yum Repositories with url contain module-streams
            2. Initialize synchronization
            3. Verify the module-stream info with various inputs options

        :expectedresults: Verify the module-stream info response.

        :CaseAutomation: Automated
        """
        Repository.synchronize({'id': repo['id']})
        module_streams = ModuleStream.list(
            {'repository-id': repo['id'], 'search': 'name="walrus" and stream="5.21"'}
        )
        actual_result = ModuleStream.info({'id': module_streams[0]['id']})
        expected_result = {
            'module-stream-name': 'walrus',
            'stream': '5.21',
            'architecture': 'x86_64',
        }
        assert expected_result == {
            key: value for key, value in actual_result.items() if key in expected_result
        }


class TestOstreeRepository:
    """Ostree Repository CLI tests."""

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'name': name,
                    'content-type': 'ostree',
                    'publish-via-http': 'false',
                    'url': FEDORA27_OSTREE_REPO,
                }
                for name in valid_data_list().values()
            ]
        ),
        indirect=True,
    )
    def test_positive_create_ostree_repo(self, repo_options, repo):
        """Create an ostree repository

        :id: a93c52e1-b32e-4590-981b-636ae8b8314d

        :parametrized: yes

        :expectedresults: ostree repository is created

        :CaseImportance: Critical
        """
        assert repo['name'] == repo_options['name']
        assert repo['content-type'] == 'ostree'

    @pytest.mark.skip_if_open("BZ:1716429")
    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'ostree',
                    'checksum-type': checksum_type,
                    'publish-via-http': 'false',
                    'url': FEDORA27_OSTREE_REPO,
                }
                for checksum_type in ('sha1', 'sha256')
            ]
        ),
        indirect=True,
    )
    def test_negative_create_ostree_repo_with_checksum(self, repo_options):
        """Create a ostree repository with checksum type

        :id: a334e0f7-e1be-4add-bbf2-2fd9f0b982c4

        :parametrized: yes

        :expectedresults: Validation error is raised

        :CaseImportance: Critical

        :BZ: 1716429
        """
        with pytest.raises(
            CLIFactoryError,
            match='Validation failed: Checksum type cannot be set for non-yum repositories',
        ):
            make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'ostree',
                    'publish-via-http': use_http,
                    'url': FEDORA27_OSTREE_REPO,
                }
                for use_http in ('true', 'yes', '1')
            ]
        ),
        indirect=True,
    )
    def test_negative_create_unprotected_ostree_repo(self, repo_options):
        """Create a ostree repository and published via http

        :id: 2b139560-65bb-4a40-9724-5cca57bd8d30

        :parametrized: yes

        :expectedresults: ostree repository is not created

        :CaseImportance: Critical
        """
        with pytest.raises(
            CLIFactoryError,
            match='Validation failed: OSTree Repositories cannot be unprotected',
        ):
            make_repository(repo_options)

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.skip_if_open("BZ:1625783")
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [{'content-type': 'ostree', 'publish-via-http': 'false', 'url': FEDORA27_OSTREE_REPO}]
        ),
        indirect=True,
    )
    def test_positive_synchronize_ostree_repo(self, repo):
        """Synchronize ostree repo

        :id: 64fcae0a-44ae-46ae-9938-032bba1331e9

        :parametrized: yes

        :expectedresults: Ostree repository is created and synced

        :CaseLevel: Integration

        :BZ: 1625783
        """
        # Synchronize it
        Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [{'content-type': 'ostree', 'publish-via-http': 'false', 'url': FEDORA27_OSTREE_REPO}]
        ),
        indirect=True,
    )
    def test_positive_delete_ostree_by_name(self, repo):
        """Delete Ostree repository by name

        :id: 0b545c22-acff-47b6-92ff-669b348f9fa6

        :parametrized: yes

        :expectedresults: Repository is deleted by name

        :CaseImportance: Critical
        """
        Repository.delete(
            {
                'name': repo['name'],
                'product': repo['product']['name'],
                'organization': repo['organization'],
            }
        )
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'name': repo['name']})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [{'content-type': 'ostree', 'publish-via-http': 'false', 'url': FEDORA27_OSTREE_REPO}]
        ),
        indirect=True,
    )
    def test_positive_delete_ostree_by_id(self, repo):
        """Delete Ostree repository by id

        :id: 171917f5-1a1b-440f-90c7-b8418f1da132

        :parametrized: yes

        :expectedresults: Repository is deleted by id

        :CaseImportance: Critical
        """
        Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})


class TestSRPMRepository:
    """Tests specific to using repositories containing source RPMs."""

    @pytest.mark.tier2
    @pytest.mark.skip("Uses deprecated SRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_SRPM_REPO}]), indirect=True
    )
    def test_positive_sync(self, repo, module_org, module_product):
        """Synchronize repository with SRPMs

        :id: eb69f840-122d-4180-b869-1bd37518480c

        :parametrized: yes

        :expectedresults: srpms can be listed in repository
        """
        Repository.synchronize({'id': repo['id']})
        result = ssh.command(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/Library"
            f"/custom/{module_product.label}/{repo['label']}/Packages/t/ | grep .src.rpm"
        )
        assert result.return_code == 0
        assert len(result.stdout) >= 1

    @pytest.mark.tier2
    @pytest.mark.skip("Uses deprecated SRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_SRPM_REPO}]), indirect=True
    )
    def test_positive_sync_publish_cv(self, module_org, module_product, repo):
        """Synchronize repository with SRPMs, add repository to content view
        and publish content view

        :id: 78cd6345-9c6c-490a-a44d-2ad64b7e959b

        :parametrized: yes

        :expectedresults: srpms can be listed in content view
        """
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': cv['id']})
        result = ssh.command(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/content_views/"
            f"{cv['label']}/1.0/custom/{module_product.label}/{repo['label']}/Packages/t/"
            " | grep .src.rpm"
        )
        assert result.return_code == 0
        assert len(result.stdout) >= 1

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.skip("Uses deprecated SRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_SRPM_REPO}]), indirect=True
    )
    def test_positive_sync_publish_promote_cv(self, repo, module_org, module_product):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: 3d197118-b1fa-456f-980e-ad1a517bc769

        :parametrized: yes

        :expectedresults: srpms can be listed in content view in proper
            lifecycle environment
        """
        lce = make_lifecycle_environment({'organization-id': module_org.id})
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': cv['id']})
        content_view = ContentView.info({'id': cv['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': lce['id']})
        result = ssh.command(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/{lce['label']}/"
            f"{cv['label']}/custom/{module_product.label}/{repo['label']}/Packages/t"
            " | grep .src.rpm"
        )
        assert result.return_code == 0
        assert len(result.stdout) >= 1


@pytest.mark.skip_if_open("BZ:1682951")
class TestDRPMRepository:
    """Tests specific to using repositories containing delta RPMs."""

    @pytest.mark.tier2
    @pytest.mark.skip("Uses deprecated DRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_DRPM_REPO}]), indirect=True
    )
    def test_positive_sync(self, repo, module_org, module_product):
        """Synchronize repository with DRPMs

        :id: a645966c-750b-40ef-a264-dc3bb632b9fd

        :parametrized: yes

        :expectedresults: drpms can be listed in repository
        """
        Repository.synchronize({'id': repo['id']})
        result = ssh.command(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/Library"
            f"/custom/{module_product.label}/{repo['label']}/drpms/ | grep .drpm"
        )
        assert result.return_code == 0
        assert len(result.stdout) >= 1

    @pytest.mark.tier2
    @pytest.mark.skip("Uses deprecated DRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_DRPM_REPO}]), indirect=True
    )
    def test_positive_sync_publish_cv(self, repo, module_org, module_product):
        """Synchronize repository with DRPMs, add repository to content view
        and publish content view

        :id: 014bfc80-4622-422e-a0ec-755b1d9f845e

        :parametrized: yes

        :expectedresults: drpms can be listed in content view
        """
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': cv['id']})
        result = ssh.command(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/content_views/"
            f"{cv['label']}/1.0/custom/{module_product.label}/{repo['label']}/drpms/ | grep .drpm"
        )
        assert result.return_code == 0
        assert len(result.stdout) >= 1

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.skip("Uses deprecated DRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_DRPM_REPO}]), indirect=True
    )
    def test_positive_sync_publish_promote_cv(self, repo, module_org, module_product):
        """Synchronize repository with DRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: a01cb12b-d388-4902-8532-714f4e28ec56

        :parametrized: yes

        :expectedresults: drpms can be listed in content view in proper
            lifecycle environment
        """
        lce = make_lifecycle_environment({'organization-id': module_org.id})
        Repository.synchronize({'id': repo['id']})
        cv = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': cv['id']})
        content_view = ContentView.info({'id': cv['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': lce['id']})
        result = ssh.command(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/{lce['label']}"
            f"/{cv['label']}/custom/{module_product.label}/{repo['label']}/drpms/ | grep .drpm"
        )
        assert result.return_code == 0
        assert len(result.stdout) >= 1


class TestGitPuppetMirror:
    """Tests for creating the hosts via CLI.

    Notes for GIT puppet mirror content

    This feature does not allow us to actually sync / update the content in a
    GIT repo. Instead, we essentially "snapshot" a repo's contents at any
    given time. The ability to update the GIT puppet mirror is / should
    be provided by Pulp itself, via a script.  However, we should be able to
    # create a sync schedule against the mirror to make sure it is periodically
    updated to contain the latest and greatest.
    """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_git_local_create(self):
        """Create repository with local git puppet mirror.

        :id: 89211cd5-82b8-4391-b729-a7502e57f824

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Create link to local puppet mirror via cli

        :expectedresults: Content source containing local GIT puppet mirror
            content is created

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_git_local_update(self):
        """Update repository with local git puppet mirror.

        :id: 341f40f2-3501-4754-9acf-7cda1a61f7db

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Modify details for existing puppet repo (name, etc.) via cli

        :expectedresults: Content source containing local GIT puppet mirror
            content is modified

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_git_local_delete(self):
        """Delete repository with local git puppet mirror.

        :id: a243f5bb-5186-41b3-8e8a-07d5cc784ccd

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Delete link to local puppet mirror via cli

        :expectedresults: Content source containing local GIT puppet mirror
            content no longer exists/is available.

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_git_remote_create(self):
        """Create repository with remote git puppet mirror.

        :id: 8582529f-3112-4b49-8d8f-f2bbf7dceca7

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps: Create link to local puppet mirror via cli

        :expectedresults: Content source containing remote GIT puppet mirror
            content is created

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_git_remote_update(self):
        """Update repository with remote git puppet mirror.

        :id: 582c50b3-3b90-4244-b694-97642b1b13a9

        :CaseLevel: Integration

        :Setup: Assure remote  GIT puppet has been created and found by pulp

        :Steps: modify details for existing puppet repo (name, etc.) via cli

        :expectedresults: Content source containing remote GIT puppet mirror
            content is modified

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_git_remote_delete(self):
        """Delete repository with remote git puppet mirror.

        :id: 0a23f969-b202-4c6c-b12e-f651a0b7d049

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps: Delete link to remote puppet mirror via cli

        :expectedresults: Content source containing remote GIT puppet mirror
            content no longer exists/is available.

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_git_sync(self):
        """Sync repository with git puppet mirror.

        :id: a46c16bd-0986-48db-8e62-aeb3907ba4d2

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to sync content from mirror via cli

        :expectedresults: Content is pulled down without error

        :expectedresults: Confirmation that various resources actually exist in
            local content repo

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    @pytest.mark.upgrade
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

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_git_sync_schedule(self):
        """Scheduled sync of git puppet mirror.

        :id: 0d58d180-9836-4524-b608-66b67f9cab12

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to create a scheduled sync content from mirror, via cli

        :expectedresults: Content is pulled down without error  on expected
            schedule

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_positive_git_view_content(self):
        """View content in synced git puppet mirror

        :id: 02f06092-dd6c-49fa-be9f-831e52476e41

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to list contents of repo via cli

        :expectedresults: Spot-checked items (filenames, dates, perhaps
            checksums?) are correct.

        :CaseAutomation: NotAutomated
        """


class TestFileRepository:
    """Specific tests for File Repositories"""

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_upload_file_to_file_repo(self, repo_options, repo):
        """Check arbitrary file can be uploaded to File Repository

        :id: 134d668d-bd63-4475-bf7b-b899bb9fb7bb

        :parametrized: yes

        :Steps:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Expectedresults: uploaded file is available under File Repository

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        ssh.upload_file(
            local_file=get_data_file(RPM_TO_UPLOAD), remote_file=f"/tmp/{RPM_TO_UPLOAD}"
        )
        result = Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{RPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{RPM_TO_UPLOAD}'" in result[0]['message']
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['files'] == '1'
        filesearch = entities.File().search(
            query={"search": f"name={RPM_TO_UPLOAD} and repository={repo['name']}"}
        )
        assert RPM_TO_UPLOAD == filesearch[0].name

    @pytest.mark.stubbed
    @pytest.mark.tier1
    def test_positive_file_permissions(self):
        """Check file permissions after file upload to File Repository

        :id: 03da888a-69ba-492f-b204-c62d85948d8a

        :Setup:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Steps: Retrieve file permissions from File Repository

        :expectedresults: uploaded file permissions are kept after upload

        :CaseAutomation: NotAutomated

        :CaseImportance: Critical
        """

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_remove_file(self, repo):
        """Check arbitrary file can be removed from File Repository

        :id: 07ca9c8d-e764-404e-866d-30d8cd2ca2b6

        :parametrized: yes

        :Setup:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Steps: Remove a file from File Repository

        :expectedresults: file is not listed under File Repository after
            removal

        :CaseImportance: Critical
        """
        ssh.upload_file(
            local_file=get_data_file(RPM_TO_UPLOAD), remote_file=f"/tmp/{RPM_TO_UPLOAD}"
        )
        result = Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{RPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{RPM_TO_UPLOAD}'" in result[0]['message']
        repo = Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['files']) > 0
        files = File.list({'repository-id': repo['id']})
        Repository.remove_content({'id': repo['id'], 'ids': [file_['id'] for file_ in files]})
        repo = Repository.info({'id': repo['id']})
        assert repo['content-counts']['files'] == '0'

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'file',
                    'url': FAKE_PULP_REMOTE_FILEREPO,
                    'name': gen_string('alpha'),
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_remote_directory_sync(self, repo):
        """Check an entire remote directory can be synced to File Repository
        through http

        :id: 5c246307-8597-4f68-a6aa-4f1a6bbf0939

        :parametrized: yes

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
            2. Make the directory available through http

        :Steps:
            1. Create a File Repository with url pointing to http url
                created on setup
            2. Initialize synchronization

        :expectedresults: entire directory is synced over http

        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['files'] == '2'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': f'file://{CUSTOM_LOCAL_FOLDER}'}]),
        indirect=True,
    )
    def test_positive_file_repo_local_directory_sync(self, repo):
        """Check an entire local directory can be synced to File Repository

        :id: ee91ecd2-2f07-4678-b782-95a7e7e57159

        :parametrized: yes

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
                locally (on the Satellite/Foreman host)

        :Steps:
            1. Create a File Repository with url pointing to local url
                created on setup
            2. Initialize synchronization


        :expectedresults: entire directory is synced

        :CaseImportance: Critical
        """
        # Making Setup For Creating Local Directory using Pulp Manifest
        ssh.command(f"mkdir -p {CUSTOM_LOCAL_FOLDER}")
        ssh.command(
            f'wget -P {CUSTOM_LOCAL_FOLDER} -r -np -nH --cut-dirs=5 -R "index.html*" '
            f'{CUSTOM_FILE_REPO}'
        )
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['files']) > 1

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': f'file://{CUSTOM_LOCAL_FOLDER}'}]),
        indirect=True,
    )
    def test_positive_symlinks_sync(self, repo):
        """Check symlinks can be synced to File Repository

        :id: b0b0a725-b754-450b-bc0d-572d0294307a

        :parametrized: yes

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

        :CaseAutomation: Automated
        """
        # Downloading the pulp repository into Satellite Host
        ssh.command(f"mkdir -p {CUSTOM_LOCAL_FOLDER}")
        ssh.command(
            f'wget -P {CUSTOM_LOCAL_FOLDER} -r -np -nH --cut-dirs=5 -R "index.html*" '
            f'{CUSTOM_FILE_REPO}'
        )
        ssh.command(f"ln -s {CUSTOM_LOCAL_FOLDER} /{gen_string('alpha')}")

        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['files']) > 1
