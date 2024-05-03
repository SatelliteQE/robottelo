"""Test class for Repository CLI

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

from random import choice
from string import punctuation

from fauxfactory import gen_alphanumeric, gen_integer, gen_string, gen_url
from nailgun import entities
import pytest
import requests
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
    CUSTOM_FILE_REPO_FILES_COUNT,
    CUSTOM_LOCAL_FOLDER,
    DOWNLOAD_POLICIES,
    FAKE_3_YUM_REPO_RPMS,
    MIRRORING_POLICIES,
    OS_TEMPLATE_DATA_FILE,
    REPO_TYPE,
    RPM_TO_UPLOAD,
    SRPM_TO_UPLOAD,
    DataFile,
)
from robottelo.constants.repos import (
    ANSIBLE_GALAXY,
    CUSTOM_3RD_PARTY_REPO,
    CUSTOM_FILE_REPO,
    CUSTOM_RPM_SHA,
    FAKE_5_YUM_REPO,
    FAKE_YUM_MD5_REPO,
    FAKE_YUM_SRPM_REPO,
)
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.logging import logger
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
    valid_docker_repository_names,
    valid_http_credentials,
)
from tests.foreman.api.test_contentview import content_view

YUM_REPOS = (
    settings.repos.yum_0.url,
    settings.repos.yum_1.url,
    settings.repos.yum_2.url,
    settings.repos.yum_3.url,
    settings.repos.yum_4.url,
)
PUPPET_REPOS = (
    settings.repos.puppet_1.url,
    settings.repos.puppet_2.url,
    settings.repos.puppet_3.url,
    settings.repos.puppet_4.url,
    settings.repos.puppet_5.url,
)


def _get_image_tags_count(repo, sat):
    return sat.cli.Repository.info({'id': repo['id']})


def _validated_image_tags_count(repo, sat):
    """Wrapper around Repository.info(), that returns once
    container-image-tags in repo is greater than 0.
    Needed due to BZ#1664631 (container-image-tags is not populated
    immediately after synchronization), which was CLOSED WONTFIX
    """
    wait_for(
        lambda: int(
            _get_image_tags_count(repo=repo, sat=sat)['content-counts']['container-image-tags']
        )
        > 0,
        timeout=30,
        delay=2,
        logger=logger,
    )
    return _get_image_tags_count(repo=repo, sat=sat)


@pytest.fixture
def repo_options(request, module_org, module_product):
    """Return the options that were passed as indirect parameters."""
    options = getattr(request, 'param', {}).copy()
    options['organization-id'] = module_org.id
    options['product-id'] = module_product.id
    return options


@pytest.fixture
def repo(repo_options, target_sat):
    """create a new repository."""
    return target_sat.cli_factory.make_repository(repo_options)


@pytest.fixture
def gpg_key(module_org, module_target_sat):
    """Create a new GPG key."""
    return module_target_sat.cli_factory.make_content_credential({'organization-id': module_org.id})


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
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'yum',
                    'url': FAKE_5_YUM_REPO,
                    'upstream-username': cred['login'],
                    'upstream-password': cred['pass'],
                }
                for cred in valid_http_credentials()
                if cred['http_valid']
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
        repo = entities.Repository(id=repo['id']).read()
        assert repo.upstream_username == repo_options['upstream-username']

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
            [{'content-type': 'yum', 'mirroring-policy': policy} for policy in MIRRORING_POLICIES]
        ),
        indirect=True,
    )
    def test_positive_mirroring_policy(self, repo_options, repo):
        """Create YUM repositories with available mirroring policy options

        :id: 37a09a91-42fc-4271-b58b-8e00ef0dc5a7

        :parametrized: yes

        :expectedresults: YUM repository created successfully and its mirroring
            policy value can be read back

        :BZ: 1383258

        :CaseImportance: Critical
        """
        assert repo.get('mirroring-policy') == MIRRORING_POLICIES[repo_options['mirroring-policy']]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'content-type': 'yum'}]), indirect=True
    )
    def test_positive_create_with_default_download_policy(self, repo_options, repo, target_sat):
        """Verify if the default download policy is assigned when creating a
        YUM repo without `--download-policy`

        :id: 9a3c4d95-d6ca-4377-9873-2c552b7d6ce7

        :parametrized: yes

        :expectedresults: YUM repository with a default download policy

        :CaseImportance: Critical
        """
        default_dl_policy = target_sat.cli.Settings.list({'search': 'name=default_download_policy'})
        assert default_dl_policy
        assert repo.get('download-policy') == default_dl_policy[0]['value']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'content-type': 'yum'}]), indirect=True
    )
    def test_positive_create_immediate_update_to_on_demand(self, repo_options, repo, target_sat):
        """Update `immediate` download policy to `on_demand` for a newly
        created YUM repository

        :id: 1a80d686-3f7b-475e-9d1a-3e1f51d55101

        :parametrized: yes

        :expectedresults: immediate download policy is updated to on_demand

        :CaseImportance: Critical

        :BZ: 1732056
        """
        assert repo.get('download-policy') == 'immediate'
        target_sat.cli.Repository.update({'id': repo['id'], 'download-policy': 'on_demand'})
        result = target_sat.cli.Repository.info({'id': repo['id']})
        assert result.get('download-policy') == 'on_demand'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'on_demand'}]),
        indirect=True,
    )
    def test_positive_create_on_demand_update_to_immediate(self, repo_options, repo, target_sat):
        """Update `on_demand` download policy to `immediate` for a newly
        created YUM repository

        :id: 1e8338af-32e5-4f92-9215-bfdc1973c8f7

        :parametrized: yes

        :expectedresults: on_demand download policy is updated to immediate

        :CaseImportance: Critical
        """
        target_sat.cli.Repository.update({'id': repo['id'], 'download-policy': 'immediate'})
        result = target_sat.cli.Repository.info({'id': repo['id']})
        assert result['download-policy'] == 'immediate'

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_create_with_gpg_key_by_id(self, repo_options, gpg_key, target_sat):
        """Check if repository can be created with gpg key ID

        :id: 6d22f0ea-2d27-4827-9b7a-3e1550a47285

        :parametrized: yes

        :expectedresults: Repository is created and has gpg key

        :CaseImportance: Critical
        """
        repo_options['gpg-key-id'] = gpg_key['id']
        repo = target_sat.cli_factory.make_repository(repo_options)
        assert repo['gpg-key']['id'] == gpg_key['id']
        assert repo['gpg-key']['name'] == gpg_key['name']

    # Comment out test until https://bugzilla.redhat.com/show_bug.cgi?id=2008656 is resolved
    # @pytest.mark.tier1
    # def test_positive_create_with_gpg_key_by_name(
    #         self, repo_options, module_org, module_product, gpg_key
    # ):
    #     """Check if repository can be created with gpg key name
    #     :id: 95cde404-3449-410d-9a08-d7f8619a2ad5
    #     :parametrized: yes
    #     :expectedresults: Repository is created and has gpg key
    #     :BZ: 1103944
    #     :CaseImportance: Critical
    #     """
    #     repo_options['gpg-key'] = gpg_key['name']
    #     repo = make_repository(repo_options)
    #     assert repo['gpg-key']['id'] == gpg_key['id']
    #     assert repo['gpg-key']['name'] == gpg_key['name']

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
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'name': valid_docker_repository_names()[0],
                    'url': CONTAINER_REGISTRY_HUB,
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
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'name': name,
                    'url': CONTAINER_REGISTRY_HUB,
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

    @pytest.mark.tier1
    def test_positive_create_repo_with_new_organization_and_location(self, target_sat):
        """Check if error is thrown when creating a Repo with a new Organization and Location.

        :id: 9ea4f2a9-f339-4215-b301-cd39c6b5c474

        :parametrized: no

        :expectedresults: No error is present when Repository is created

        :BZ: 1992967

        :CaseImportance: High
        """
        new_org = target_sat.cli_factory.make_org()
        new_location = target_sat.cli_factory.make_location()
        new_product = target_sat.cli_factory.make_product(
            {'organization-id': new_org['id'], 'description': 'test_product'}
        )
        target_sat.cli.Org.add_location(
            {'location-id': new_location['id'], 'name': new_org['name']}
        )
        assert new_location['name'] in target_sat.cli.Org.info({'id': new_org['id']})['locations']
        target_sat.cli_factory.make_repository(
            {
                'content-type': 'yum',
                'organization-id': new_org['id'],
                'product-id': new_product['id'],
            }
        )

        result = target_sat.execute(
            "cat /var/log/foreman/production.log | "
            "grep \"undefined method `id' for nil:NilClass (NoMethodError)\""
        )
        assert result.status == 1

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': name} for name in invalid_values_list()]),
        indirect=True,
    )
    def test_negative_create_with_name(self, repo_options, target_sat):
        """Repository name cannot be 300-characters long

        :id: af0652d3-012d-4846-82ac-047918f74722

        :parametrized: yes

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            target_sat.cli_factory.make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'url': f'http://{gen_string("alpha")}{punctuation}.com'}]),
        indirect=True,
    )
    def test_negative_create_with_url_with_special_characters(
        self, repo_options, module_target_sat
    ):
        """Verify that repository URL cannot contain unquoted special characters

        :id: 2bd5ee17-0fe5-43cb-9cdc-dc2178c5374c

        :parametrized: yes

        :expectedresults: Repository cannot be created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': gen_string('alpha', 5)}]),
        indirect=True,
    )
    def test_negative_create_with_invalid_download_policy(self, repo_options, module_target_sat):
        """Verify that YUM repository cannot be created with invalid download
        policy

        :id: 3b143bf8-7056-4c94-910d-69a451071f26

        :parametrized: yes

        :expectedresults: YUM repository is not created with invalid download
            policy

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'content-type': 'yum'}]), indirect=True
    )
    def test_negative_update_to_invalid_download_policy(self, repo_options, repo, target_sat):
        """Verify that YUM repository cannot be updated to invalid download
        policy

        :id: 5bd6a2e4-7ff0-42ac-825a-6b2a2f687c89

        :parametrized: yes

        :expectedresults: YUM repository is not updated to invalid download
            policy

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.Repository.update(
                {'id': repo['id'], 'download-policy': gen_string('alpha', 5)}
            )

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {'content-type': content_type, 'download-policy': 'on_demand'}
                for content_type in REPO_TYPE
                if content_type != 'yum'
                if content_type != 'ostree'
            ]
        ),
        indirect=True,
    )
    def test_negative_create_non_yum_with_download_policy(self, repo_options, module_target_sat):
        """Verify that non-YUM repositories cannot be created with download
        policy TODO: Remove ostree from exceptions when ostree is added back in Satellite 7

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
            module_target_sat.cli_factory.make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_synchronize_file_repo(self, repo_options, repo, target_sat):
        """Check if repository can be created and synced

        :id: eafc421d-153e-41e1-afbd-938e556ef827

        :parametrized: yes

        :expectedresults: Repository is created and synced

        :CaseImportance: Critical
        """
        # Assertion that repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert int(repo['content-counts']['files']) == CUSTOM_FILE_REPO_FILES_COUNT

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'yum',
                    'url': FAKE_5_YUM_REPO,
                    'upstream-username': cred['login'],
                    'upstream-password': cred['pass'],
                }
                for cred in valid_http_credentials()
                if cred['http_valid']
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_auth_yum_repo(self, repo, target_sat):
        """Check if secured repository can be created and synced

        :id: b0db676b-e0f0-428c-adf3-1d7c0c3599f0

        :parametrized: yes

        :expectedresults: Repository is created and synced

        :BZ: 1328092

        """
        # Assertion that repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        new_repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert new_repo['sync']['status'] == 'Success'

    @pytest.mark.skip_if_open("BZ:2035025")
    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                (
                    {
                        'content-type': 'yum',
                        'url': FAKE_5_YUM_REPO,
                        'upstream-username': creds['login'],
                        'upstream-password': creds['pass'],
                    }
                    for creds in valid_http_credentials()
                    if not creds['http_valid']
                )
            ]
        ),
        indirect=['repo_options'],
    )
    def test_negative_synchronize_auth_yum_repo(self, repo, target_sat):
        """Check if secured repo fails to synchronize with invalid credentials

        :id: 809905ae-fb76-465d-9468-1f99c4274aeb

        :parametrized: yes

        :expectedresults: Repository is created but synchronization fails

        :BZ: 1405503, 1453118

        """
        # Try to synchronize it
        repo_sync = target_sat.cli.Repository.synchronize({'id': repo['id'], 'async': True})
        response = target_sat.cli.Task.progress(
            {'id': repo_sync[0]['id']}, return_raw_response=True
        )
        assert "Error: 401, message='Unauthorized'" in response.stderr[1].decode('utf-8')

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'name': valid_docker_repository_names()[0],
                    'url': CONTAINER_REGISTRY_HUB,
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_docker_repo(
        self, repo, module_product, module_org, module_target_sat
    ):
        """Check if Docker repository can be created, synced, and deleted

        :id: cb9ae788-743c-4785-98b2-6ae0c161bc9a

        :parametrized: yes

        :customerscenario: true

        :expectedresults: Docker repository is created, synced, and deleted

        :BZ: 1810165
        """
        # Assertion that repo is not yet synced
        assert repo['sync']['status'] == 'Not Synced'
        # Synchronize it
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        new_repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert new_repo['sync']['status'] == 'Success'
        # For BZ#1810165, assert repo can be deleted
        module_target_sat.cli.Repository.delete({'id': repo['id']})
        assert (
            new_repo['name']
            not in module_target_sat.cli.Product.info(
                {'id': module_product.id, 'organization-id': module_org.id}
            )['content']
        )

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'name': valid_docker_repository_names()[0],
                    'url': CONTAINER_REGISTRY_HUB,
                }
            ]
        ),
        indirect=True,
    )
    def test_verify_checksum_container_repo(self, repo, target_sat):
        """Check if Verify Content Checksum can be run on container repos

        :id: c8f0eb45-3cb6-41b2-aad9-52ac847d7bf8

        :parametrized: yes

        :expectedresults: Docker repository is created, and can be synced with
            validate-contents set to True

        :BZ: 2161209

        :customerscenario: true
        """
        assert repo['sync']['status'] == 'Not Synced'
        target_sat.cli.Repository.synchronize({'id': repo['id'], 'validate-contents': 'true'})
        new_repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert new_repo['sync']['status'] == 'Success'

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'url': CONTAINER_REGISTRY_HUB,
                    'mirroring-policy': 'additive',
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_docker_repo_set_tags_later_additive(self, repo, target_sat):
        """Verify that adding tags whitelist and re-syncing after
        synchronizing full repository doesn't remove content that was
        already pulled in when mirroring policy is set to additive

        :id: 97f2087f-6041-4242-8b7c-be53c68f46ff

        :parametrized: yes

        :expectedresults: Non-whitelisted tags are not removed
        """
        tags = 'latest'
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo, sat=target_sat)
        assert not repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) >= 2
        target_sat.cli.Repository.update({'id': repo['id'], 'include-tags': tags})
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo, sat=target_sat)
        assert tags in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) >= 2

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'url': CONTAINER_REGISTRY_HUB,
                    'mirroring-policy': 'mirror_content_only',
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_docker_repo_set_tags_later_content_only(self, repo, target_sat):
        """Verify that adding tags whitelist and re-syncing after
        synchronizing full repository does remove content that was
        already pulled in when mirroring policy is set to content only

        :id: 539dc138-8566-40ad-b0de-1d9ec80aa56f


        :parametrized: yes

        :expectedresults: Non-whitelisted tags are removed
        """
        tags = 'latest'
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo, sat=target_sat)
        assert not repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) >= 2
        target_sat.cli.Repository.update({'id': repo['id'], 'include-tags': tags})
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo, sat=target_sat)
        assert tags in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) <= 2

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'url': CONTAINER_REGISTRY_HUB,
                    'include-tags': f"latest,{gen_string('alpha')}",
                }
            ]
        ),
        indirect=True,
    )
    def test_negative_synchronize_docker_repo_with_mix_valid_invalid_tags(
        self, repo_options, repo, target_sat
    ):
        """Set tags whitelist to contain both valid and invalid (non-existing)
        tags. Check if only whitelisted tags are synchronized

        :id: 75668da8-cc94-4d39-ade1-d3ef91edc812

        :parametrized: yes

        :expectedresults: Only whitelisted tag is synchronized
        """
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = _validated_image_tags_count(repo=repo, sat=target_sat)
        for tag in repo_options['include-tags'].split(','):
            assert tag in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) == 1

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'docker',
                    'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                    'url': CONTAINER_REGISTRY_HUB,
                    'include-tags': ",".join([gen_string('alpha') for _ in range(3)]),
                }
            ]
        ),
        indirect=True,
    )
    def test_negative_synchronize_docker_repo_with_invalid_tags(
        self, repo_options, repo, target_sat
    ):
        """Set tags whitelist to contain only invalid (non-existing)
        tags. Check that no data is synchronized.

        :id: da05cdb1-2aea-48b9-9424-6cc700bc1194

        :parametrized: yes

        :expectedresults: Tags are not synchronized
        """
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        for tag in repo_options['include-tags'].split(','):
            assert tag in repo['container-image-tags-filter']
        assert int(repo['content-counts']['container-image-tags']) == 0

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': settings.repos.yum_1.url}]),
        indirect=True,
    )
    def test_positive_resynchronize_rpm_repo(self, repo, target_sat):
        """Check that repository content is resynced after packages were
        removed from repository

        :id: a21b6710-4f12-4722-803e-3cb29d70eead

        :parametrized: yes

        :expectedresults: Repository has updated non-zero packages count

        :BZ: 1459845, 1459874, 1318004

        """
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'
        # Find repo packages and remove them
        packages = target_sat.cli.Package.list({'repository-id': repo['id']})
        target_sat.cli.Repository.remove_content(
            {'id': repo['id'], 'ids': [package['id'] for package in packages]}
        )
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '0'
        # Re-synchronize repository
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'

    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'yum',
                    'name': gen_string('alpha'),
                    'url': settings.repos.yum_1.url,
                }
            ]
        ),
        indirect=True,
    )
    @pytest.mark.parametrize(
        'repo_options_2',
        **parametrized(
            [
                {
                    'content-type': 'yum',
                    'name': gen_string('alpha'),
                }
            ]
        ),
    )
    @pytest.mark.tier2
    def test_mirror_on_sync_removes_rpm(self, module_org, repo, repo_options_2, module_target_sat):
        """
            Check that a package removed upstream is removed downstream when the repo
            is next synced if mirror-on-sync is enabled (the default setting).

        :id: 637d6479-842d-4570-97eb-3a986eca2142

        :Setup:
            1. Create product with yum type repository (repo 1), URL to upstream, sync it.
            2. Create another product with yum type repository (repo 2), URL to repo 1, sync it.
            3. Delete one package from repo 1.
            4. Sync the second repo (repo 2) from the first repo (repo 1).

        :steps:
            1. Check that the package deleted from repo 1 was removed from repo 2.

        :expectedresults: A package removed from repo 1 is removed from repo 2 when synced.

        :CaseImportance: Medium
        """
        # Add description to repo 1 and its product
        module_target_sat.cli.Product.update(
            {
                'id': repo.get('product')['id'],
                'organization': module_org.label,
                'description': 'Fake Upstream',
            }
        )
        module_target_sat.cli.Repository.update(
            {'id': repo['id'], 'description': ['Fake Upstream']}
        )
        # Sync repo 1 from the real upstream
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'
        # Make 2nd repo
        prod_2 = module_target_sat.cli_factory.make_product(
            {'organization-id': module_org.id, 'description': 'Downstream'}
        )
        repo_options_2['organization-id'] = module_org.id
        repo_options_2['product-id'] = prod_2['id']
        repo_options_2['url'] = repo.get('published-at')
        repo_2 = module_target_sat.cli_factory.make_repository(repo_options_2)
        module_target_sat.cli.Repository.update({'id': repo_2['id'], 'description': ['Downstream']})
        repo_2 = module_target_sat.cli.Repository.info({'id': repo_2['id']})
        module_target_sat.cli.Repository.synchronize({'id': repo_2['id']})
        # Get list of repo 1's packages and remove one
        package = choice(module_target_sat.cli.Package.list({'repository-id': repo['id']}))
        module_target_sat.cli.Repository.remove_content({'id': repo['id'], 'ids': [package['id']]})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '31'
        # Re-synchronize repo_2, the downstream repository
        module_target_sat.cli.Repository.synchronize({'id': repo_2['id']})
        repo_2 = module_target_sat.cli.Repository.info({'id': repo_2['id']})
        assert repo_2['sync']['status'] == 'Success'
        assert repo_2['content-counts']['packages'] == '31'

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'yum',
                    'url': settings.repos.yum_mixed.url,
                    'ignorable-content': ['srpm'],
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_synchronize_rpm_repo_ignore_SRPM(
        self, module_org, module_product, repo, target_sat
    ):
        """Synchronize yum repository with ignore SRPM

        :id: fa32ff10-e2e2-4ee0-b444-82f66f4a0e96

        :parametrized: yes

        :expectedresults: No SRPM Content is Synced

        :BZ: 1591358

        """
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['srpms'] == '0', 'content not ignored correctly'

    @pytest.mark.tier1
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_positive_update_url(self, repo, module_target_sat):
        """Update the original url for a repository

        :id: 1a2cf29b-5c30-4d4c-b6d1-2f227b0a0a57

        :parametrized: yes

        :expectedresults: Repository url is updated

        :CaseImportance: Critical
        """
        # Update the url
        module_target_sat.cli.Repository.update({'id': repo['id'], 'url': settings.repos.yum_2.url})
        # Fetch it again
        result = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert result['url'] == settings.repos.yum_2.url

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'new_repo_options',
        **parametrized([{'url': f'http://{gen_string("alpha")}{punctuation}'}]),
    )
    def test_negative_update_url_with_special_characters(
        self, new_repo_options, repo, module_target_sat
    ):
        """Verify that repository URL cannot be updated to contain
        the forbidden characters

        :id: 566553b2-d077-4fd8-8ed5-00ba75355386

        :parametrized: yes

        :expectedresults: Repository url not updated

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Repository.update(
                {'id': repo['id'], 'url': new_repo_options['url']}
            )
        # Fetch it again, ensure url hasn't changed.
        result = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert result['url'] == repo['url']

    @pytest.mark.tier1
    def test_positive_update_gpg_key(self, repo_options, module_org, repo, gpg_key, target_sat):
        """Update the original gpg key

        :id: 367ff375-4f52-4a8c-b974-8c1c54e3fdd3

        :parametrized: yes

        :expectedresults: Repository gpg key is updated

        :CaseImportance: Critical
        """
        target_sat.cli.Repository.update({'id': repo['id'], 'gpg-key-id': gpg_key['id']})

        gpg_key_new = target_sat.cli_factory.make_content_credential(
            {'organization-id': module_org.id}
        )
        target_sat.cli.Repository.update({'id': repo['id'], 'gpg-key-id': gpg_key_new['id']})
        result = target_sat.cli.Repository.info({'id': repo['id']})
        assert result['gpg-key']['id'] == gpg_key_new['id']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'mirroring-policy': policy} for policy in MIRRORING_POLICIES]),
        indirect=True,
    )
    def test_positive_update_mirroring_policy(self, repo, repo_options, module_target_sat):
        """Update the mirroring policy rule for repository

        :id: 9bab2537-3223-40d7-bc4c-a51b09d2e812

        :parametrized: yes

        :expectedresults: Repository is updated

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.update(
            {'id': repo['id'], 'mirroring-policy': repo_options['mirroring-policy']}
        )
        result = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert result['mirroring-policy'] == MIRRORING_POLICIES[repo_options['mirroring-policy']]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'publish-via-http': 'no'}]), indirect=True
    )
    def test_positive_update_publish_method(self, repo, module_target_sat):
        """Update the original publishing method

        :id: e7bd2667-4851-4a64-9c70-1b5eafbc3f71

        :parametrized: yes

        :expectedresults: Repository publishing method is updated

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.update({'id': repo['id'], 'publish-via-http': 'yes'})
        result = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert result['publish-via-http'] == 'yes'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'download-policy': 'immediate'}]),
        indirect=True,
    )
    @pytest.mark.parametrize('checksum_type', ['sha1', 'sha256'])
    def test_positive_update_checksum_type(
        self, repo_options, repo, checksum_type, module_target_sat
    ):
        """Create a YUM repository and update the checksum type

        :id: 42f14257-d860-443d-b337-36fd355014bc

        :parametrized: yes

        :expectedresults: A YUM repository is updated and contains the correct
            checksum type

        :CaseImportance: Critical
        """
        assert repo['content-type'] == repo_options['content-type']
        module_target_sat.cli.Repository.update({'checksum-type': checksum_type, 'id': repo['id']})
        result = module_target_sat.cli.Repository.info({'id': repo['id']})
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
    def test_negative_create_checksum_with_on_demand_policy(self, repo_options, module_target_sat):
        """Attempt to create repository with checksum and on_demand policy.

        :id: 33d712e6-e91f-42bb-8c5d-35bdc427182c

        :parametrized: yes

        :expectedresults: A repository is not created and error is raised.

        :CaseImportance: Critical

        :BZ: 1732056
        """
        with pytest.raises(CLIFactoryError):
            module_target_sat.cli_factory.make_repository(repo_options)

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'name': name} for name in valid_data_list().values()]),
        indirect=True,
    )
    def test_positive_delete_by_name(self, repo_options, repo, module_target_sat):
        """Check if repository can be created and deleted

        :id: 463980a4-dbcf-4178-83a6-1863cf59909a

        :parametrized: yes

        :expectedresults: Repository is created and then deleted

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.delete(
            {'name': repo['name'], 'product-id': repo_options['product-id']}
        )
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': settings.repos.yum_1.url}]),
        indirect=True,
    )
    def test_positive_delete_rpm(self, repo, module_target_sat):
        """Check if rpm repository with packages can be deleted.

        :id: 1172492f-d595-4c8e-89c1-fabb21eb04ac

        :parametrized: yes

        :expectedresults: Repository is deleted.

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        # Check that there is at least one package
        assert int(repo['content-counts']['packages']) > 0
        module_target_sat.cli.Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': settings.repos.yum_1.url}]),
        indirect=True,
    )
    def test_positive_remove_content_by_repo_name(
        self, module_org, module_product, repo, module_target_sat
    ):
        """Synchronize and remove rpm content using repo name

        :id: a8b6f17d-3b13-4185-920a-2558ace59458

        :parametrized: yes

        :expectedresults: Content Counts shows zero packages

        :BZ: 1349646, 1413145, 1459845, 1459874

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.synchronize(
            {
                'name': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
            }
        )
        repo = module_target_sat.cli.Repository.info(
            {
                'name': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
            }
        )
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'
        # Find repo packages and remove them
        packages = module_target_sat.cli.Package.list(
            {
                'repository': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
            }
        )
        module_target_sat.cli.Repository.remove_content(
            {
                'name': repo['name'],
                'product': module_product.name,
                'organization': module_org.name,
                'ids': [package['id'] for package in packages],
            }
        )
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '0'

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': settings.repos.yum_1.url}]),
        indirect=True,
    )
    def test_positive_remove_content_rpm(self, repo, module_target_sat):
        """Synchronize repository and remove rpm content from it

        :id: c4bcda0e-c0d6-424c-840d-26684ca7c9f1

        :parametrized: yes

        :expectedresults: Content Counts shows zero packages

        :BZ: 1459845, 1459874

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['packages'] == '32'
        # Find repo packages and remove them
        packages = module_target_sat.cli.Package.list({'repository-id': repo['id']})
        module_target_sat.cli.Repository.remove_content(
            {'id': repo['id'], 'ids': [package['id'] for package in packages]}
        )
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['content-counts']['packages'] == '0'

    @pytest.mark.tier1
    def test_positive_upload_content(self, repo, target_sat):
        """Create repository and upload content

        :id: eb0ec599-2bf1-483a-8215-66652f948d67

        :parametrized: yes

        :customerscenario: true

        :expectedresults: upload content is successful

        :BZ: 1343006, 1421298

        :CaseImportance: Critical
        """
        target_sat.put(
            local_path=DataFile.RPM_TO_UPLOAD,
            remote_path=f"/tmp/{RPM_TO_UPLOAD}",
        )
        result = target_sat.cli.Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{RPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file {RPM_TO_UPLOAD}" == result[0]['message']
        assert (
            int(target_sat.cli.Repository.info({'id': repo['id']})['content-counts']['packages'])
            == 1
        )

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_upload_content_to_file_repo(self, repo, target_sat):
        """Create file repository and upload content to it

        :id: 5e24b416-2928-4533-96cf-6bffbea97a95

        :parametrized: yes

        :customerscenario: true

        :expectedresults: upload content operation is successful

        :BZ: 1446975, 1421298

        :CaseImportance: Critical
        """
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        # Verify it has finished
        new_repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert int(new_repo['content-counts']['files']) == CUSTOM_FILE_REPO_FILES_COUNT
        target_sat.put(
            local_path=DataFile.OS_TEMPLATE_DATA_FILE,
            remote_path=f"/tmp/{OS_TEMPLATE_DATA_FILE}",
        )
        result = target_sat.cli.Repository.upload_content(
            {
                'name': new_repo['name'],
                'organization': new_repo['organization'],
                'path': f"/tmp/{OS_TEMPLATE_DATA_FILE}",
                'product-id': new_repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file {OS_TEMPLATE_DATA_FILE}" == result[0]['message']
        new_repo = target_sat.cli.Repository.info({'id': new_repo['id']})
        assert int(new_repo['content-counts']['files']) == CUSTOM_FILE_REPO_FILES_COUNT + 1

    @pytest.mark.skip_if_open("BZ:1410916")
    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': settings.repos.yum_1.url}]),
        indirect=True,
    )
    def test_negative_restricted_user_cv_add_repository(self, module_org, repo, module_target_sat):
        """Attempt to add a product repository to content view with a
        restricted user, using product name not visible to restricted user.

        :id: 65792ae0-c5be-4a6c-9062-27dc03b83e10

        :parametrized: yes

        :customerscenario: true

        :BZ: 1436209,1410916

        :steps:
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

        """
        required_permissions = {
            'Katello::Product': (
                [
                    'view_products',
                    'create_products',
                    'edit_products',
                    'destroy_products',
                    'sync_products',
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
        user = module_target_sat.cli_factory.user(
            {
                'admin': False,
                'default-organization-id': module_org.id,
                'organization-ids': [module_org.id],
                'login': user_name,
                'password': user_password,
            }
        )
        # Create a new role
        role = module_target_sat.cli_factory.make_role()
        # Get the available permissions
        available_permissions = module_target_sat.cli.Filter.available_permissions()
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
            module_target_sat.cli_factory.make_filter(
                {'role-id': role['id'], 'permissions': permission_names, 'search': search}
            )
        # Add the created and initiated role with permissions to user
        module_target_sat.cli.User.add_role({'id': user['id'], 'role-id': role['id']})
        # assert that the user is not an admin one and cannot read the current
        # role info (note: view_roles is not in the required permissions)
        with pytest.raises(
            CLIReturnCodeError,
            match=r'Access denied\\nMissing one of the required permissions: view_roles',
        ):
            module_target_sat.cli.Role.with_user(user_name, user_password).info({'id': role['id']})

        module_target_sat.cli.Repository.synchronize({'id': repo['id']})

        # Create a content view
        content_view = module_target_sat.cli_factory.make_content_view(
            {'organization-id': module_org.id, 'name': content_view_name}
        )
        # assert that the user can read the content view info as per required
        # permissions
        user_content_view = module_target_sat.cli.ContentView.with_user(
            user_name, user_password
        ).info({'id': content_view['id']})
        # assert that this is the same content view
        assert content_view['name'] == user_content_view['name']
        # assert admin user is able to view the product
        repos = module_target_sat.cli.Repository.list({'organization-id': module_org.id})
        assert len(repos) == 1
        # assert that this is the same repo
        assert repos[0]['id'] == repo['id']
        # assert that restricted user is not able to view the product
        repos = module_target_sat.cli.Repository.with_user(user_name, user_password).list(
            {'organization-id': module_org.id}
        )
        assert len(repos) == 0
        # assert that the user cannot add the product repo to content view
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.with_user(user_name, user_password).add_repository(
                {
                    'id': content_view['id'],
                    'organization-id': module_org.id,
                    'repository-id': repo['id'],
                }
            )
        # assert that restricted user still not able to view the product
        repos = module_target_sat.cli.Repository.with_user(user_name, user_password).list(
            {'organization-id': module_org.id}
        )
        assert len(repos) == 0

    @pytest.mark.tier2
    def test_positive_upload_remove_srpm_content(self, repo, target_sat):
        """Create repository, upload and remove an SRPM content

        :id: 706dc3e2-dacb-4fdd-8eef-5715ce498888

        :parametrized: yes

        :customerscenario: true

        :expectedresults: SRPM successfully uploaded and removed

        :CaseImportance: Critical

        :BZ: 1378442
        """
        target_sat.put(
            local_path=DataFile.SRPM_TO_UPLOAD,
            remote_path=f"/tmp/{SRPM_TO_UPLOAD}",
        )
        # Upload SRPM
        result = target_sat.cli.Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{SRPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
                'content-type': 'srpm',
            }
        )
        assert f"Successfully uploaded file '{SRPM_TO_UPLOAD}'" in result[0]['message']
        assert (
            int(target_sat.cli.Repository.info({'id': repo['id']})['content-counts']['srpms']) == 1
        )

        # Remove uploaded SRPM
        target_sat.cli.Repository.remove_content(
            {
                'id': repo['id'],
                'ids': [target_sat.cli.Srpm.list({'repository-id': repo['id']})[0]['id']],
                'content-type': 'srpm',
            }
        )
        assert (
            int(target_sat.cli.Repository.info({'id': repo['id']})['content-counts']['srpms']) == 0
        )

    @pytest.mark.upgrade
    @pytest.mark.tier2
    @pytest.mark.e2e
    def test_positive_srpm_list_end_to_end(self, repo, target_sat):
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
        target_sat.put(
            local_path=DataFile.SRPM_TO_UPLOAD,
            remote_path=f"/tmp/{SRPM_TO_UPLOAD}",
        )
        # Upload SRPM
        target_sat.cli.Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f'/tmp/{SRPM_TO_UPLOAD}',
                'product-id': repo['product']['id'],
                'content-type': 'srpm',
            }
        )
        assert len(target_sat.cli.Srpm.list()) > 0
        srpm_list = target_sat.cli.Srpm.list({'repository-id': repo['id']})
        assert srpm_list[0]['filename'] == SRPM_TO_UPLOAD
        assert len(srpm_list) == 1
        assert target_sat.cli.Srpm.info({'id': srpm_list[0]['id']})[0]['filename'] == SRPM_TO_UPLOAD
        assert (
            int(target_sat.cli.Repository.info({'id': repo['id']})['content-counts']['srpms']) == 1
        )
        assert (
            len(
                target_sat.cli.Srpm.list(
                    {
                        'organization': repo['organization'],
                        'product-id': repo['product']['id'],
                        'repository-id': repo['id'],
                    }
                )
            )
            > 0
        )
        assert len(target_sat.cli.Srpm.list({'organization': repo['organization']})) > 0
        assert (
            len(
                target_sat.cli.Srpm.list(
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
                target_sat.cli.Srpm.list(
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
        target_sat.cli.Repository.remove_content(
            {
                'id': repo['id'],
                'ids': [target_sat.cli.Srpm.list({'repository-id': repo['id']})[0]['id']],
                'content-type': 'srpm',
            }
        )
        assert int(
            target_sat.cli.Repository.info({'id': repo['id']})['content-counts']['srpms']
        ) == len(target_sat.cli.Srpm.list({'repository-id': repo['id']}))

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': settings.repos.module_stream_1.url}]),
        indirect=True,
    )
    def test_positive_create_get_update_delete_module_streams(
        self, repo_options, module_org, module_product, repo, module_target_sat
    ):
        """Check module-stream get for each create, get, update, delete.

        :id: e9001f76-9bc7-42a7-b8c9-2dccd5bf0b1f2f2e70b8-e446-4a28-9bae-fc870c80e83e

        :parametrized: yes

        :Setup:
            1. valid yum repo with Module Streams.

        :steps:
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
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert (
            repo['content-counts']['module-streams'] == '7'
        ), 'Module Streams not synced correctly'

        # adding repo with same yum url should not change count.
        duplicate_repo = module_target_sat.cli_factory.make_repository(repo_options)
        module_target_sat.cli.Repository.synchronize({'id': duplicate_repo['id']})

        module_streams = module_target_sat.cli.ModuleStream.list({'organization-id': module_org.id})
        assert len(module_streams) == 7, 'Module Streams get worked correctly'
        module_target_sat.cli.Repository.update(
            {
                'product-id': module_product.id,
                'id': repo['id'],
                'url': settings.repos.module_stream_1.url,
            }
        )
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert (
            repo['content-counts']['module-streams'] == '7'
        ), 'Module Streams not synced correctly'

        module_target_sat.cli.Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Repository.info({'id': repo['id']})

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': settings.repos.module_stream_1.url}]),
        indirect=True,
    )
    def test_module_stream_info_validation(self, repo, module_target_sat):
        """Check module-stream get with info on hammer.

        :id: ddbeb49e-d292-4dc4-8fb9-e9b768acc441a2c2e797-02b7-4b12-9f95-cffc93254198

        :parametrized: yes

        :Setup:
            1. valid yum repo with Module Streams.

        :steps:
            1. Create Yum Repositories with url contain module-streams
            2. Initialize synchronization
            3. Verify the module-stream info with various inputs options

        :expectedresults: Verify the module-stream info response.

        :CaseAutomation: Automated
        """
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        module_streams = module_target_sat.cli.ModuleStream.list(
            {'repository-id': repo['id'], 'search': 'name="walrus" and stream="5.21"'}
        )
        actual_result = module_target_sat.cli.ModuleStream.info({'id': module_streams[0]['id']})
        expected_result = {
            'module-stream-name': 'walrus',
            'stream': '5.21',
            'architecture': 'x86_64',
        }
        assert expected_result == {
            key: value for key, value in actual_result.items() if key in expected_result
        }

    @pytest.mark.tier1
    @pytest.mark.skip_if_open('BZ:2002653')
    def test_negative_update_red_hat_repo(self, module_manifest_org, module_target_sat):
        """Updates to Red Hat products fail.

        :id: d3ac0ea2-faab-4df4-be66-733e1b7ae6b4

        :customerscenario: true

        :BZ: 1756951, 2002653

        :steps:
            1. Import manifest and enable a Red Hat repository.
            2. Attempt to update the Red Hat repository:
               # hammer repository update --id <id> --url http://example.com/repo

        :expectedresults: hammer returns error code. The repository is not updated.
        """

        rh_repo_set_id = module_target_sat.cli.RepositorySet.list(
            {'organization-id': module_manifest_org.id}
        )[0]['id']

        module_target_sat.cli.RepositorySet.enable(
            {
                'organization-id': module_manifest_org.id,
                'basearch': "x86_64",
                'id': rh_repo_set_id,
            }
        )
        repo_list = module_target_sat.cli.Repository.list(
            {'organization-id': module_manifest_org.id}
        )

        rh_repo_id = module_target_sat.cli.Repository.list(
            {'organization-id': module_manifest_org.id}
        )[0]['id']

        module_target_sat.cli.Repository.update(
            {
                'id': rh_repo_id,
                'url': f'{gen_url(scheme="https")}:{gen_integer(min_value=10, max_value=9999)}',
            }
        )
        repo_info = module_target_sat.cli.Repository.info(
            {'organization-id': module_manifest_org.id, 'id': rh_repo_id}
        )
        assert repo_info['url'] in [repo.get('url') for repo in repo_list]

    @pytest.mark.tier1
    def test_positive_accessible_content_status(
        self, module_org, module_ak_with_synced_repo, rhel7_contenthost, target_sat
    ):
        """Verify that the Candlepin response accesible_content returns a 304 when no
            certificate has been updated

        :id: 9f8f443d-63fc-41ba-8962-b0ceb6763da1

        :expectedresults: accessible_content should return 304 not Modified status when
            yum repolist is run

        :customerscenario: true

        :BZ: 2010138

        :CaseImportance: Critical
        """
        rhel7_contenthost.register(module_org, None, module_ak_with_synced_repo['name'], target_sat)
        assert rhel7_contenthost.subscribed
        rhel7_contenthost.run('yum repolist')
        access_log = target_sat.execute(
            'tail -n 10 /var/log/httpd/foreman-ssl_access_ssl.log | grep "/rhsm"'
        )
        assert 'accessible_content HTTP/1.1" 304' in access_log.stdout

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': CUSTOM_RPM_SHA}]),
        indirect=True,
    )
    def test_positive_sync_sha_repo(self, repo_options, module_target_sat):
        """Sync repository with 'sha' checksum, which uses 'sha1' in particular actually

        :id: 20579f52-a67b-4d3f-be07-41eec059a891

        :parametrized: yes

        :customerscenario: true

        :BZ: 2024889

        :SubComponent: Pulp
        """
        sha_repo = module_target_sat.cli_factory.make_repository(repo_options)
        sha_repo = module_target_sat.cli.Repository.info({'id': sha_repo['id']})
        module_target_sat.cli.Repository.synchronize({'id': sha_repo['id']})
        sha_repo = module_target_sat.cli.Repository.info({'id': sha_repo['id']})
        assert sha_repo['sync']['status'] == 'Success'

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'yum', 'url': CUSTOM_3RD_PARTY_REPO}]),
        indirect=True,
    )
    def test_positive_sync_third_party_repo(self, repo_options, module_target_sat):
        """Sync third party repo successfully

        :id: 45936ab8-46b7-4f07-8b71-d7c8a4a2d984

        :parametrized: yes

        :customerscenario: true

        :BZ: 1920511

        :SubComponent: Pulp
        """
        repo = module_target_sat.cli_factory.make_repository(repo_options)
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'


# TODO: un-comment when OSTREE functionality is restored in Satellite 6.11
# class TestOstreeRepository:
#     """Ostree Repository CLI tests."""
#
#     @pytest.mark.tier1
#     @pytest.mark.parametrize(
#         'repo_options',
#         **parametrized(
#             [
#                 {
#                     'name': name,
#                     'content-type': 'ostree',
#                     'publish-via-http': 'false',
#                     'url': FEDORA_OSTREE_REPO,
#                 }
#                 for name in valid_data_list().values()
#             ]
#         ),
#         indirect=True,
#     )
#     def test_positive_create_ostree_repo(self, repo_options, repo):
#         """Create an ostree repository
#
#         :id: a93c52e1-b32e-4590-981b-636ae8b8314d
#
#         :parametrized: yes
#
#         :customerscenario: true
#
#         :expectedresults: ostree repository is created
#
#         :CaseImportance: Critical
#         """
#         assert repo['name'] == repo_options['name']
#         assert repo['content-type'] == 'ostree'
#
#     @pytest.mark.skip_if_open("BZ:1716429")
#     @pytest.mark.tier1
#     @pytest.mark.parametrize(
#         'repo_options',
#         **parametrized(
#             [
#                 {
#                     'content-type': 'ostree',
#                     'checksum-type': checksum_type,
#                     'publish-via-http': 'false',
#                     'url': FEDORA_OSTREE_REPO,
#                 }
#                 for checksum_type in ('sha1', 'sha256')
#             ]
#         ),
#         indirect=True,
#     )
#     def test_negative_create_ostree_repo_with_checksum(self, repo_options):
#         """Create a ostree repository with checksum type
#
#         :id: a334e0f7-e1be-4add-bbf2-2fd9f0b982c4
#
#         :parametrized: yes
#
#         :expectedresults: Validation error is raised
#
#         :CaseImportance: Critical
#
#         :BZ: 1716429
#         """
#         with pytest.raises(
#             CLIFactoryError,
#             match='Validation failed: Checksum type cannot be set for non-yum repositories',
#         ):
#             make_repository(repo_options)
#
#     @pytest.mark.tier1
#     @pytest.mark.parametrize(
#         'repo_options',
#         **parametrized(
#             [
#                 {
#                     'content-type': 'ostree',
#                     'publish-via-http': use_http,
#                     'url': FEDORA_OSTREE_REPO,
#                 }
#                 for use_http in ('true', 'yes', '1')
#             ]
#         ),
#         indirect=True,
#     )
#     def test_negative_create_unprotected_ostree_repo(self, repo_options):
#         """Create a ostree repository and published via http
#
#         :id: 2b139560-65bb-4a40-9724-5cca57bd8d30
#
#         :parametrized: yes
#
#         :expectedresults: ostree repository is not created
#
#         :CaseImportance: Critical
#         """
#         with pytest.raises(
#             CLIFactoryError,
#             match='Validation failed: OSTree Repositories cannot be unprotected',
#         ):
#             make_repository(repo_options)
#
#     @pytest.mark.tier2
#     @pytest.mark.upgrade
#     @pytest.mark.skip_if_open("BZ:1625783")
#     @pytest.mark.parametrize(
#         'repo_options',
#         **parametrized(
#             [{'content-type': 'ostree', 'publish-via-http': 'false', 'url': FEDORA_OSTREE_REPO}]
#         ),
#         indirect=True,
#     )
#     def test_positive_synchronize_ostree_repo(self, repo):
#         """Synchronize ostree repo
#
#         :id: 64fcae0a-44ae-46ae-9938-032bba1331e9
#
#         :parametrized: yes
#
#         :expectedresults: Ostree repository is created and synced


#         :BZ: 1625783
#         """
#         # Synchronize it
#         Repository.synchronize({'id': repo['id']})
#         # Verify it has finished
#         repo = Repository.info({'id': repo['id']})
#         assert repo['sync']['status'] == 'Success'
#
#     @pytest.mark.tier1
#     @pytest.mark.parametrize(
#         'repo_options',
#         **parametrized(
#             [{'content-type': 'ostree', 'publish-via-http': 'false', 'url': FEDORA_OSTREE_REPO}]
#         ),
#         indirect=True,
#     )
#     def test_positive_delete_ostree_by_name(self, repo):
#         """Delete Ostree repository by name
#
#         :id: 0b545c22-acff-47b6-92ff-669b348f9fa6
#
#         :parametrized: yes
#
#         :expectedresults: Repository is deleted by name
#
#         :CaseImportance: Critical
#         """
#         Repository.delete(
#             {
#                 'name': repo['name'],
#                 'product': repo['product']['name'],
#                 'organization': repo['organization'],
#             }
#         )
#         with pytest.raises(CLIReturnCodeError):
#             Repository.info({'name': repo['name']})
#
#     @pytest.mark.tier1
#     @pytest.mark.upgrade
#     @pytest.mark.parametrize(
#         'repo_options',
#         **parametrized(
#             [{'content-type': 'ostree', 'publish-via-http': 'false', 'url': FEDORA_OSTREE_REPO}]
#         ),
#         indirect=True,
#     )
#     def test_positive_delete_ostree_by_id(self, repo):
#         """Delete Ostree repository by id
#
#         :id: 171917f5-1a1b-440f-90c7-b8418f1da132
#
#         :parametrized: yes
#
#         :expectedresults: Repository is deleted by id
#
#         :CaseImportance: Critical
#         """
#         Repository.delete({'id': repo['id']})
#         with pytest.raises(CLIReturnCodeError):
#             Repository.info({'id': repo['id']})


class TestSRPMRepository:
    """Tests specific to using repositories containing source RPMs."""

    @pytest.mark.tier2
    @pytest.mark.skip("Uses deprecated SRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_SRPM_REPO}]), indirect=True
    )
    def test_positive_sync(self, repo, module_org, module_product, target_sat):
        """Synchronize repository with SRPMs

        :id: eb69f840-122d-4180-b869-1bd37518480c

        :parametrized: yes

        :expectedresults: srpms can be listed in repository
        """
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        result = target_sat.execute(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/Library"
            f"/custom/{module_product.label}/{repo['label']}/Packages/t/ | grep .src.rpm"
        )
        assert result.status == 0
        assert result.stdout

    @pytest.mark.tier2
    @pytest.mark.skip("Uses deprecated SRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_SRPM_REPO}]), indirect=True
    )
    def test_positive_sync_publish_cv(self, module_org, module_product, repo, target_sat):
        """Synchronize repository with SRPMs, add repository to content view
        and publish content view

        :id: 78cd6345-9c6c-490a-a44d-2ad64b7e959b

        :parametrized: yes

        :expectedresults: srpms can be listed in content view
        """
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        cv = target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
        target_sat.cli.ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})
        target_sat.cli.ContentView.publish({'id': cv['id']})
        result = target_sat.execute(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/content_views/"
            f"{cv['label']}/1.0/custom/{module_product.label}/{repo['label']}/Packages/t/"
            " | grep .src.rpm"
        )
        assert result.status == 0
        assert result.stdout

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.skip("Uses deprecated SRPM repository")
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_SRPM_REPO}]), indirect=True
    )
    def test_positive_sync_publish_promote_cv(self, repo, module_org, module_product, target_sat):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: 3d197118-b1fa-456f-980e-ad1a517bc769

        :parametrized: yes

        :expectedresults: srpms can be listed in content view in proper
            lifecycle environment
        """
        lce = target_sat.cli_factory.make_lifecycle_environment({'organization-id': module_org.id})
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        cv = target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
        target_sat.cli.ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})
        target_sat.cli.ContentView.publish({'id': cv['id']})
        target_sat.cli.content_view = target_sat.cli.ContentView.info({'id': cv['id']})
        cvv = content_view['versions'][0]
        target_sat.cli.ContentView.version_promote(
            {'id': cvv['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        result = target_sat.execute(
            f"ls /var/lib/pulp/published/yum/https/repos/{module_org.label}/{lce['label']}/"
            f"{cv['label']}/custom/{module_product.label}/{repo['label']}/Packages/t"
            " | grep .src.rpm"
        )
        assert result.status == 0
        assert result.stdout


class TestAnsibleCollectionRepository:
    """Ansible Collections repository tests"""

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        [
            {
                'content-type': 'ansible_collection',
                'url': ANSIBLE_GALAXY,
                'ansible-collection-requirements': '{collections: [ \
                            { name: theforeman.foreman, version: "2.1.0" }, \
                            { name: theforeman.operations, version: "0.1.0"} ]}',
            },
            {
                'content-type': 'ansible_collection',
                'url': settings.ansible_hub.url,
                'ansible-collection-auth-token': settings.ansible_hub.token,
                'ansible-collection-auth-url': settings.ansible_hub.sso_url,
                'ansible-collection-requirements': '{collections: \
                                                         [redhat.satellite_operations ]}',
            },
        ],
        ids=['ansible_galaxy', 'ansible_hub'],
        indirect=True,
    )
    def test_positive_sync_ansible_collection(self, repo, module_target_sat):
        """Sync ansible collection repository from Ansible Galaxy and Hub

        :id: 4b6a819b-8c3d-4a74-bd97-ee3f34cf5d92

        :expectedresults: All content synced successfully

        :CaseImportance: High

        :parametrized: yes

        """
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        [
            {
                'content-type': 'ansible_collection',
                'url': ANSIBLE_GALAXY,
                'ansible-collection-requirements': '{collections: [ \
                            { name: theforeman.foreman, version: "2.1.0" }, \
                            { name: theforeman.operations, version: "0.1.0"} ]}',
            }
        ],
        ids=['ansible_galaxy'],
        indirect=True,
    )
    def test_positive_export_ansible_collection(self, repo, module_org, target_sat):
        """Export ansible collection between organizations

        :id: 4858227e-1669-476d-8da3-4e6bfb6b7e2a

        :expectedresults: All content exported and imported successfully

        :CaseImportance: High

        """
        import_org = target_sat.cli_factory.make_org()
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        # export
        result = target_sat.cli.ContentExport.completeLibrary({'organization-id': module_org.id})
        target_sat.execute(f'cp -r /var/lib/pulp/exports/{module_org.name} /var/lib/pulp/imports/.')
        target_sat.execute('chown -R pulp:pulp /var/lib/pulp/imports')
        export_metadata = result['message'].split()[1]
        # import
        import_path = export_metadata.replace('/metadata.json', '').replace('exports', 'imports')
        target_sat.cli.ContentImport.library(
            {'organization-id': import_org['id'], 'path': import_path}
        )
        cv = target_sat.cli.ContentView.info(
            {'name': 'Import-Library', 'organization-label': import_org['label']}
        )
        assert cv['description'] == 'Content View used for importing into library'
        prods = target_sat.cli.Product.list({'organization-id': import_org['id']})
        prod = target_sat.cli.Product.info(
            {'id': prods[0]['id'], 'organization-id': import_org['id']}
        )
        ac_content = [
            cont for cont in prod['content'] if cont['content-type'] == 'ansible_collection'
        ]
        assert len(ac_content) > 0
        repo = target_sat.cli.Repository.info(
            {'name': ac_content[0]['repo-name'], 'product-id': prod['id']}
        )
        result = target_sat.execute(f'curl {repo["published-at"]}')
        assert "available_versions" in result.stdout

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        [
            {
                'content-type': 'ansible_collection',
                'url': ANSIBLE_GALAXY,
                'ansible-collection-requirements': '{collections: [ \
                            { name: theforeman.foreman, version: "2.1.0" }, \
                            { name: theforeman.operations, version: "0.1.0"} ]}',
            }
        ],
        ids=['ansible_galaxy'],
        indirect=True,
    )
    def test_positive_sync_ansible_collection_from_satellite(self, repo, target_sat):
        """Sync ansible collection from another organization

        :id: f7897a56-d014-4189-b4c7-df8f15aaf30a

        :expectedresults: All content synced successfully

        :CaseImportance: High

        """
        import_org = target_sat.cli_factory.make_org()
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        published_url = repo['published-at']
        # sync from different org
        prod_2 = target_sat.cli_factory.make_product(
            {'organization-id': import_org['id'], 'description': 'Sync from Satellite'}
        )
        repo_2 = target_sat.cli_factory.make_repository(
            {
                'organization-id': import_org['id'],
                'product-id': prod_2['id'],
                'url': published_url,
                'content-type': 'ansible_collection',
                'ansible-collection-requirements': '{collections: \
                    [{ name: theforeman.operations, version: "0.1.0"}]}',
            }
        )
        target_sat.cli.Repository.synchronize({'id': repo_2['id']})
        repo_2_status = target_sat.cli.Repository.info({'id': repo_2['id']})
        assert repo_2_status['sync']['status'] == 'Success'


class TestMD5Repository:
    """Tests specific to using MD5 signed repositories containing RPMs."""

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options', **parametrized([{'url': FAKE_YUM_MD5_REPO}]), indirect=True
    )
    def test_positive_sync_publish_promote_cv(self, repo, module_org, target_sat):
        """Synchronize MD5 signed repository with add repository to content view,
        publish and promote content view to lifecycle environment

        :id: 81cf2606-739f-44ed-8954-41b9d824a69f

        :parametrized: yes

        :expectedresults: rpms can be listed in content view in proper
            lifecycle environment
        """
        lce = target_sat.cli_factory.make_lifecycle_environment({'organization-id': module_org.id})
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        synced_repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert synced_repo['sync']['status'].lower() == 'success'
        assert synced_repo['content-counts']['packages'] == '35'
        cv = target_sat.cli_factory.make_content_view({'organization-id': module_org.id})
        target_sat.cli.ContentView.add_repository({'id': cv['id'], 'repository-id': repo['id']})
        target_sat.cli.ContentView.publish({'id': cv['id']})
        content_view = target_sat.cli.ContentView.info({'id': cv['id']})
        cvv = content_view['versions'][0]
        target_sat.cli.ContentView.version_promote(
            {'id': cvv['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        cv = target_sat.cli.ContentView.info({'id': cv['id']})
        assert synced_repo['id'] in [repo['id'] for repo in cv['yum-repositories']]
        assert lce['id'] in [lc['id'] for lc in cv['lifecycle-environments']]


class TestFileRepository:
    """Specific tests for File Repositories"""

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_upload_file_to_file_repo(self, repo_options, repo, target_sat):
        """Check arbitrary file can be uploaded to File Repository

        :id: 134d668d-bd63-4475-bf7b-b899bb9fb7bb

        :parametrized: yes

        :steps:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :Expectedresults: uploaded file is available under File Repository

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        target_sat.put(
            local_path=DataFile.RPM_TO_UPLOAD,
            remote_path=f"/tmp/{RPM_TO_UPLOAD}",
        )
        result = target_sat.cli.Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{RPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{RPM_TO_UPLOAD}'" in result[0]['message']
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['content-counts']['files'] == '1'
        filesearch = entities.File().search(
            query={"search": f"name={RPM_TO_UPLOAD} and repository={repo['name']}"}
        )
        assert filesearch[0].name == RPM_TO_UPLOAD

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_positive_remove_file(self, repo, target_sat):
        """Check arbitrary file can be removed from File Repository

        :id: 07ca9c8d-e764-404e-866d-30d8cd2ca2b6

        :parametrized: yes

        :Setup:
            1. Create a File Repository
            2. Upload an arbitrary file to it

        :steps: Remove a file from File Repository

        :expectedresults: file is not listed under File Repository after
            removal

        :CaseImportance: Critical
        """
        target_sat.put(
            local_path=DataFile.RPM_TO_UPLOAD,
            remote_path=f"/tmp/{RPM_TO_UPLOAD}",
        )
        result = target_sat.cli.Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{RPM_TO_UPLOAD}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{RPM_TO_UPLOAD}'" in result[0]['message']
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['files']) > 0
        files = target_sat.cli.File.list({'repository-id': repo['id']})
        target_sat.cli.Repository.remove_content(
            {'id': repo['id'], 'ids': [file_['id'] for file_ in files]}
        )
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['content-counts']['files'] == '0'

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized(
            [
                {
                    'content-type': 'file',
                    'url': settings.repos.file_type_repo.url,
                    'name': gen_string('alpha'),
                }
            ]
        ),
        indirect=True,
    )
    def test_positive_remote_directory_sync(self, repo, module_target_sat):
        """Check an entire remote directory can be synced to File Repository
        through http

        :id: 5c246307-8597-4f68-a6aa-4f1a6bbf0939

        :parametrized: yes

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
            2. Make the directory available through http

        :steps:
            1. Create a File Repository with url pointing to http url
                created on setup
            2. Initialize synchronization

        :expectedresults: entire directory is synced over http

        """
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['sync']['status'] == 'Success'
        assert repo['content-counts']['files'] == '2'

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': f'file://{CUSTOM_LOCAL_FOLDER}'}]),
        indirect=True,
    )
    def test_positive_file_repo_local_directory_sync(self, repo, target_sat):
        """Check an entire local directory can be synced to File Repository

        :id: ee91ecd2-2f07-4678-b782-95a7e7e57159

        :parametrized: yes

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
                locally (on the Satellite/Foreman host)

        :steps:
            1. Create a File Repository with url pointing to local url
                created on setup
            2. Initialize synchronization


        :expectedresults: entire directory is synced

        :CaseImportance: Critical
        """
        # Making Setup For Creating Local Directory using Pulp Manifest
        target_sat.execute(f'mkdir -p {CUSTOM_LOCAL_FOLDER}')
        target_sat.execute(
            f'wget -P {CUSTOM_LOCAL_FOLDER} -r -np -nH --cut-dirs=5 -R "index.html*" '
            f'{CUSTOM_FILE_REPO}'
        )
        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['files']) > 1

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': f'file://{CUSTOM_LOCAL_FOLDER}'}]),
        indirect=True,
    )
    def test_positive_symlinks_sync(self, repo, target_sat):
        """Check symlinks can be synced to File Repository

        :id: b0b0a725-b754-450b-bc0d-572d0294307a

        :parametrized: yes

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
                locally (on the Satellite/Foreman host)
            2. Make sure it contains symlinks

        :steps:
            1. Create a File Repository with url pointing to local url
                created on setup
            2. Initialize synchronization

        :expectedresults: entire directory is synced, including files
            referred by symlinks

        :CaseAutomation: Automated
        """
        # Downloading the pulp repository into Satellite Host
        target_sat.execute(f'mkdir -p {CUSTOM_LOCAL_FOLDER}')
        target_sat.execute(
            f'wget -P {CUSTOM_LOCAL_FOLDER} -r -np -nH --cut-dirs=5 -R "index.html*" '
            f'{CUSTOM_FILE_REPO}'
        )
        target_sat.execute(f'ln -s {CUSTOM_LOCAL_FOLDER} /{gen_string("alpha")}')

        target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['files']) > 1

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'repo_options',
        **parametrized([{'content-type': 'file', 'url': CUSTOM_FILE_REPO}]),
        indirect=True,
    )
    def test_file_repo_contains_only_newer_file(self, repo_options, repo, target_sat):
        """
            Check that a file-type repo contains only the newer of
            two versions of a file with the same name.

        :id: d2530bc4-647c-41cd-a062-5dcf8f9086c6

        :Setup:
            1. Create a product with a file type repository.
            2. Create a text file locally.
            3. Upload the file and check it is in the published repo.
            4. Add some text keyword to the file locally.
            5. Upload new version of file.

        :steps:
            1. Check that the repo contains only the new version of the file

        :expectedresults: The file is not duplicated and only the latest version of the file
            is present in the repo.

        :parametrized: yes
        """
        text_file_name = f'test-{gen_string("alpha", 5)}.txt'.lower()
        target_sat.execute(f'echo "First File" > /tmp/{text_file_name}')
        result = target_sat.cli.Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{text_file_name}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{text_file_name}'" in result[0]['message']
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        # Assert there is only one file
        assert repo['content-counts']['files'] == '1'
        filesearch = entities.File().search(
            query={"search": f"name={text_file_name} and repository={repo['name']}"}
        )
        assert text_file_name == filesearch[0].name
        # Create new version of the file by changing the text
        target_sat.execute(f'echo "Second File" > /tmp/{text_file_name}')
        result = target_sat.cli.Repository.upload_content(
            {
                'name': repo['name'],
                'organization': repo['organization'],
                'path': f"/tmp/{text_file_name}",
                'product-id': repo['product']['id'],
            }
        )
        assert f"Successfully uploaded file '{text_file_name}'" in result[0]['message']
        repo = target_sat.cli.Repository.info({'id': repo['id']})
        # Assert there is still only one file
        assert repo['content-counts']['files'] == '1'
        filesearch = entities.File().search(
            query={"search": f"name={text_file_name} and repository={repo['name']}"}
        )
        # Assert file name has not changed
        assert text_file_name == filesearch[0].name
        # Get the file and assert it has the updated contents
        textfile = requests.get(f"{repo['published-at']}{text_file_name}", verify=False)
        assert 'Second File' in textfile.text


@pytest.mark.tier2
def test_positive_syncable_yum_format_repo_import(target_sat, module_org):
    """Verify that you can import syncable yum format repositories

    :id: dc6422c3-1ea1-4856-ab64-7c66e6043300

    :steps:
        1. Execute hammer command
            hammer content-import repository --organization='' --path=''
        2. Assert job is successful
        3. Verify repository is synced and contains rpms

    :expectedresults: The syncable repository sync correctly and all content is imported

    :customerscenario: true

    :BZ: 2128894
    """
    target_sat.execute('mkdir /var/lib/pulp/imports/syncable-repo')
    target_sat.execute(
        'wget -m -np -nH -e robots=off -P /var/lib/pulp/imports/syncable-repo'
        f' {settings.robottelo.REPOS_HOSTING_URL}/exported_repo/'
    )
    target_sat.cli.ContentImport.repository(
        {
            'organization': module_org.name,
            'path': '/var/lib/pulp/imports/syncable-repo/exported_repo',
        }
    )
    repodata = target_sat.cli.Repository.info(
        {'name': 'testrepo', 'organization-id': module_org.id, 'product': 'testproduct'}
    )
    assert repodata['content-counts']['packages'] != 0
    assert repodata['sync']['status'] == 'Success'


@pytest.mark.rhel_ver_list([9])
def test_positive_install_uploaded_rpm_on_host(
    target_sat, rhel_contenthost, function_org, function_lce
):
    """Verify that uploaded rpm successfully install on content host

    :id: 8701782e-2d1e-41b7-a9dc-07325bfeaf1c

    :steps:
        1. Create product, custom repo and upload rpm into repo
        2. Create CV, add repo into it & publish CV
        3. Upload package on to the satellite, rename it then upload it into repo
        4. Register host with satellite and install rpm on it

    :expectedresults: rpm should install successfully

    :customerscenario: true

    :BZ: 2161993
    """
    product = target_sat.cli_factory.make_product({'organization-id': function_org.id})
    repo = target_sat.cli_factory.make_repository(
        {
            'content-type': 'yum',
            'name': gen_string('alpha', 5),
            'product-id': product['id'],
        }
    )
    target_sat.cli.Repository.synchronize({'id': repo['id']})
    sync_status = target_sat.cli.Repository.info({'id': repo['id']})['sync']['status']
    assert sync_status == 'Success', f'Failed to sync {repo["name"]} repo'

    # Upload package
    target_sat.put(
        local_path=DataFile.FAKE_3_YUM_REPO_RPMS_ANT,
        remote_path=f"/tmp/{FAKE_3_YUM_REPO_RPMS[0]}",
    )
    # Rename uploaded package name
    rpm_new_name = f'{gen_string(str_type="alpha", length=5)}.rpm'
    target_sat.execute(f"mv /tmp/{FAKE_3_YUM_REPO_RPMS[0]} /tmp/{rpm_new_name}")

    result = target_sat.cli.Repository.upload_content(
        {
            'name': repo['name'],
            'organization': repo['organization'],
            'path': f"/tmp/{rpm_new_name}",
            'product-id': repo['product']['id'],
        }
    )
    assert f"Successfully uploaded file {rpm_new_name}" == result[0]['message']
    queryinfo = target_sat.execute(f"rpm -q /tmp/{rpm_new_name}")

    content_view = target_sat.cli_factory.make_content_view(
        {'organization-id': function_org.id, 'name': gen_string('alpha', 5)}
    )
    target_sat.cli.ContentView.add_repository(
        {'id': content_view['id'], 'repository-id': repo['id']}
    )
    target_sat.cli.ContentView.publish({'id': content_view['id']})
    content_view = target_sat.cli.ContentView.info({'id': content_view['id']})
    target_sat.cli.ContentView.version_promote(
        {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': function_lce.id}
    )
    activation_key = target_sat.cli_factory.make_activation_key(
        {
            'organization-id': function_org.id,
            'lifecycle-environment-id': function_lce.id,
            'content-view-id': content_view['id'],
        }
    )
    target_sat.cli.ActivationKey.content_override(
        {'id': activation_key.id, 'content-label': repo.content_label, 'value': 'true'}
    )
    assert (
        rhel_contenthost.register(function_org, None, activation_key.name, target_sat).status == 0
    )
    assert (
        rhel_contenthost.execute(f'yum install -y {FAKE_3_YUM_REPO_RPMS[0].split("-")[0]}').status
        == 0
    )
    installed_package_name = rhel_contenthost.execute(
        f'rpm -q {FAKE_3_YUM_REPO_RPMS[0].split("-")[0]}'
    )
    assert installed_package_name.stdout == queryinfo.stdout
