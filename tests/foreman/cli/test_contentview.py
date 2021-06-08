"""Test class for Content Views

:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
import random

import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_string
from nailgun import entities

from robottelo import ssh
from robottelo.api.utils import create_sync_custom_repo
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.capsule import Capsule
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_content_view_filter
from robottelo.cli.factory import make_content_view_filter_rule
from robottelo.cli.factory import make_fake_host
from robottelo.cli.factory import make_filter
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_role
from robottelo.cli.factory import make_user
from robottelo.cli.filter import Filter
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.location import Location
from robottelo.cli.module_stream import ModuleStream
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.role import Role
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_0_INC_UPD_ERRATA
from robottelo.constants import FAKE_0_INC_UPD_NEW_PACKAGE
from robottelo.constants import FAKE_0_INC_UPD_NEW_UPDATEFILE
from robottelo.constants import FAKE_0_INC_UPD_OLD_PACKAGE
from robottelo.constants import FAKE_0_INC_UPD_OLD_UPDATEFILE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import PERMISSIONS
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants import RPM_TO_UPLOAD
from robottelo.constants.repos import CUSTOM_MODULE_STREAM_REPO_1
from robottelo.constants.repos import CUSTOM_MODULE_STREAM_REPO_2
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.constants.repos import FAKE_0_INC_UPD_URL
from robottelo.constants.repos import FAKE_0_PUPPET_REPO
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.constants.repos import OSTREE_REPO
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_names_list
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import create_repo
from robottelo.helpers import get_data_file
from robottelo.helpers import repo_add_updateinfo
from robottelo.vm_capsule import CapsuleVirtualMachine


@pytest.fixture(scope='module')
def module_rhel_content(module_manifest_org):
    """Returns RH repo after syncing it"""
    product = entities.Product(name=PRDS['rhel'], organization=module_manifest_org).search()[0]
    reposet = entities.RepositorySet(name=REPOSET['rhva6'], product=product).search()[0]
    data = {'basearch': 'x86_64', 'releasever': '6Server', 'product_id': product.id}
    reposet.enable(data=data)

    repo = Repository.info(
        {
            'name': REPOS['rhva6']['name'],
            'organization-id': module_manifest_org.id,
            'product': product.name,
        }
    )
    Repository.synchronize(
        {
            'name': REPOS['rhva6']['name'],
            'organization-id': module_manifest_org.id,
            'product': product.name,
        }
    )
    return repo


@skip_if_os('RHEL6')
@pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
@pytest.fixture(scope='class')
def all_content_type(module_org):
    """Sync all content sync and return their repo info"""
    product = make_product({'organization-id': module_org.id})
    # Create new custom ostree repo
    ostree_repo = make_repository(
        {
            'product-id': product['id'],
            'content-type': 'ostree',
            'publish-via-http': 'false',
            'url': OSTREE_REPO,
        }
    )
    Repository.synchronize({'id': ostree_repo['id']})
    ostree_repo_info = Repository.info(
        {'name': ostree_repo['name'], 'organization-id': module_org.id, 'product': product['name']}
    )
    # Create new yum repo
    yum_repo = make_repository({'url': FAKE_1_YUM_REPO, 'product-id': product['id']})
    Repository.synchronize({'id': yum_repo['id']})
    yum_repo_info = Repository.info(
        {'name': yum_repo['name'], 'organization-id': module_org.id, 'product': product['name']}
    )
    # Create new Puppet repository
    puppet_repo = make_repository(
        {'url': FAKE_0_PUPPET_REPO, 'content-type': 'puppet', 'product-id': product['id']}
    )
    Repository.synchronize({'id': puppet_repo['id']})
    puppet_repo_info = Repository.info(
        {'name': puppet_repo['name'], 'organization-id': module_org.id, 'product': product['name']}
    )
    # Create new docker repository
    docker_repo = make_repository(
        {
            'content-type': 'docker',
            'docker-upstream-name': 'busybox',
            'product-id': product['id'],
            'url': CONTAINER_REGISTRY_HUB,
        }
    )
    Repository.synchronize({'id': docker_repo['id']})
    docker_repo_info = Repository.info(
        {'name': docker_repo['name'], 'organization-id': module_org.id, 'product': product['name']}
    )
    # Get all repo info
    repos = {
        'ostree_repo': ostree_repo_info,
        'yum_repo': yum_repo_info,
        'puppet_repo': puppet_repo_info,
        'docker_repo': docker_repo_info,
    }
    return repos


@pytest.fixture(scope='class')
def atomic_repo(module_manifest_org):
    RepositorySet.enable(
        {
            'basearch': None,
            'name': REPOSET['rhaht'],
            'organization-id': module_manifest_org.id,
            'product': PRDS['rhah'],
            'releasever': None,
        }
    )
    repo_name = REPOS['rhaht']['name']
    repo = Repository.info(
        {
            'name': REPOS['rhaht']['name'],
            'organization-id': module_manifest_org.id,
            'product': PRDS['rhah'],
        }
    )
    Repository.synchronize(
        {'name': repo_name, 'organization-id': module_manifest_org.id, 'product': PRDS['rhah']}
    )
    return repo


def _get_content_view_version_lce_names_set(content_view_id, version_id):
    """returns a set of content view version lifecycle environment names

    :rtype: set that it belongs under
    """
    lifecycle_environments = ContentView.version_info(
        {'content-view-id': content_view_id, 'id': version_id}
    )['lifecycle-environments']
    return {lce['name'] for lce in lifecycle_environments}


class TestContentView:
    """Content View CLI Tests"""

    @pytest.mark.parametrize('name', **parametrized(valid_names_list()))
    @pytest.mark.tier1
    def test_positive_create_with_name(self, module_org, name):
        """create content views with different names

        :id: a154308c-3982-4cf1-a236-3051e740970e

        :expectedresults: content views are created

        :CaseImportance: Critical

        :parametrized: yes
        """
        content_view = make_content_view({'name': name, 'organization-id': module_org.id})
        assert content_view['name'] == name.strip()

    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    @pytest.mark.tier1
    def test_negative_create_with_invalid_name(self, module_org, name):
        """create content views with invalid names

        :id: 83046271-76f9-4cda-b579-a2fe63493295

        :expectedresults: content views are not created; proper error thrown
            and system handles it gracefully

        :CaseImportance: Critical

        :parametrized: yes
        """
        with pytest.raises(CLIFactoryError):
            make_content_view({'name': name, 'organization-id': module_org.id})

    @pytest.mark.tier1
    def test_negative_create_with_org_name(self):
        """Create content view with invalid org name

        :id: f8b76e98-ccc8-41ac-af04-541650e8f5ba

        :expectedresults: content views are not created; proper error thrown
            and system handles it gracefully

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError):
            ContentView.create({'organization-id': gen_string('alpha')})

    @pytest.mark.tier2
    def test_positive_create_with_repo_id(self, module_org, module_product):
        """Create content view providing repository id

        :id: bb91affe-f8d4-4724-8b61-41f3cb898fd3

        :expectedresults: Content view is created and repository is associated
            with CV

        :CaseImportance: High
        :BZ: 1213097
        """
        repo = make_repository({'product-id': module_product.id})
        cv = make_content_view({'organization-id': module_org.id, 'repository-ids': [repo['id']]})
        assert cv['yum-repositories'][0]['id'] == repo['id']

    @pytest.mark.tier1
    def test_positive_create_empty_and_verify_files(self, module_org):
        """Create an empty content view and make sure no files are created at
        /var/lib/pulp/published.

        :id: 0e31573d-bf02-44ae-b3f4-d8aae450ba5e

        :expectedresults: Content view is published and no file is present at
            /var/lib/pulp/published.

        :CaseImportance: Critical
        """
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        # Check content view files presence before deletion
        result = ssh.command(
            'find /var/lib/pulp/published -name "*{}*"'.format(content_view['name'])
        )
        assert result.return_code == 0
        assert len(result.stdout) == 0
        assert len(content_view['versions']) == 1

    @pytest.mark.parametrize('new_name', **parametrized(valid_names_list()))
    @pytest.mark.tier1
    def test_positive_update_name_by_id(self, module_org, new_name):
        """Find content view by its id and update its name afterwards

        :id: 35fccf2c-abc4-4ca8-a565-a7a6adaaf429

        :expectedresults: Content view is updated with new name

        :BZ: 1359665

        :CaseImportance: Critical

        :parametrized: yes
        """
        cv = make_content_view({'name': gen_string('utf8'), 'organization-id': module_org.id})
        ContentView.update({'id': cv['id'], 'new-name': new_name})
        cv = ContentView.info({'id': cv['id']})
        assert cv['name'] == new_name.strip()

    @pytest.mark.parametrize('new_name', **parametrized(valid_names_list()))
    @pytest.mark.tier1
    def test_positive_update_name_by_name(self, module_org, new_name):
        """Find content view by its name and update it

        :id: aa9bced6-ee6c-4a18-90ac-874ab4979711

        :expectedresults: Content view is updated with new name

        :BZ: 1359665, 1416857

        :CaseImportance: Critical

        :parametrized: yes
        """
        cv = make_content_view({'organization-id': module_org.id})
        ContentView.update(
            {'name': cv['name'], 'organization-label': module_org.label, 'new-name': new_name}
        )
        cv = ContentView.info({'id': cv['id']})
        assert cv['name'] == new_name.strip()

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier2
    def test_positive_update_filter(self, repo_setup):
        """Edit content views for a rh content, add a filter and update filter

        :id: 4beab1e4-fc58-460e-af24-cdd2c3d283e6

        :expectedresults: Edited content view save is successful and info is
            updated

        :CaseLevel: Integration

        :CaseImportance: High
        """
        # Create CV
        new_cv = make_content_view({'organization-id': repo_setup['org'].id})
        # Associate repo to CV
        ContentView.add_repository(
            {
                'id': new_cv['id'],
                'organization-id': repo_setup['org'].id,
                'repository-id': repo_setup['repo'].id,
            }
        )
        Repository.synchronize({'id': repo_setup['repo'].id})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['yum-repositories'][0]['name'] == repo_setup['repo'].name
        cvf = make_content_view_filter(
            {'content-view-id': new_cv['id'], 'inclusion': 'true', 'type': 'erratum'}
        )
        cvf_rule = make_content_view_filter_rule(
            {'content-view-filter-id': cvf['filter-id'], 'types': ['bugfix', 'enhancement']}
        )
        cvf = ContentView.filter.info({'id': cvf['filter-id']})
        assert 'security' not in cvf['rules'][0]['types']
        ContentView.filter.rule.update(
            {
                'id': cvf_rule['rule-id'],
                'types': 'security',
                'content-view-filter-id': cvf['filter-id'],
            }
        )
        cvf = ContentView.filter.info({'id': cvf['filter-id']})
        assert 'security' == cvf['rules'][0]['types']

    @pytest.mark.tier1
    def test_positive_delete_by_id(self, module_org):
        """delete content view by its id

        :id: e96d6d47-8be4-4705-979f-e5c320eca293

        :expectedresults: content view can be deleted

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': module_org.id})
        ContentView.delete({'id': cv['id']})
        with pytest.raises(CLIReturnCodeError):
            ContentView.info({'id': cv['id']})

    @pytest.mark.tier1
    def test_positive_delete_by_name(self, module_org):
        """delete content view by its name

        :id: 014b85f3-003b-42d9-bbfe-21620e8eb84b

        :expectedresults: content view can be deleted

        :BZ: 1416857

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': module_org.id})
        ContentView.delete({'name': cv['name'], 'organization': module_org.name})
        with pytest.raises(CLIReturnCodeError):
            ContentView.info({'id': cv['id']})

    @pytest.mark.tier1
    def test_positive_delete_with_custom_repo_by_name_and_verify_files(self, module_org):
        """Delete content view containing custom repo and verify it was
        actually deleted from hard drive.

        :id: 9f381f77-ce43-4b68-8d00-459f40c9efb6

        :expectedresults: Content view was deleted and pulp folder doesn't
            contain content view files anymore

        :BZ: 1317057, 1265703

        :CaseImportance: Critical
        """
        # Create and sync a repository
        new_product = make_product({'organization-id': module_org.id})
        new_repo = make_repository({'product-id': new_product['id']})
        Repository.synchronize({'id': new_repo['id']})
        # Create a content view, add the repo and publish the content view
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': new_repo['id'],
            }
        )
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        # Check content view files presence before deletion
        result = ssh.command('find /var/lib/pulp -name "*{}*"'.format(content_view['name']))
        assert result.return_code == 0
        assert len(result.stdout) != 0
        assert len(content_view['versions']) == 1
        # Completely delete the content view
        ContentView.remove_from_environment(
            {
                'id': content_view['id'],
                'lifecycle-environment-id': content_view['lifecycle-environments'][0]['id'],
            }
        )
        ContentView.version_delete(
            {
                'content-view': content_view['name'],
                'organization': module_org.name,
                'version': content_view['versions'][0]['version'],
            }
        )
        ContentView.delete({'id': content_view['id']})
        # Check content view files presence after deletion
        result = ssh.command('find /var/lib/pulp -name "*{}*"'.format(content_view['name']))
        assert result.return_code == 0
        assert len(result.stdout) == 0

    @pytest.mark.tier2
    def test_positive_delete_version_by_name(self, module_org):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version name as a parameter.

        :id: 6e903131-1aeb-478c-ad92-5dedcc22c3f9

        :expectedresults: Content view version deleted successfully

        :CaseImportance: High

        :CaseLevel: Integration
        """
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1
        cvv = content_view['versions'][0]
        env_id = content_view['lifecycle-environments'][0]['id']
        ContentView.remove_from_environment(
            {'id': content_view['id'], 'lifecycle-environment-id': env_id}
        )
        ContentView.version_delete(
            {
                'content-view': content_view['name'],
                'organization': module_org.name,
                'version': cvv['version'],
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 0

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_delete_version_by_id(self, module_org, module_product):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version id as a parameter. Also,
        add repository to initial content view for better coverage.

        :id: 09457d48-2a92-401d-8dd0-45679a547e70

        :expectedresults: Content view version deleted successfully

        :CaseImportance: High
        """
        # Create new organization, product and repository
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create new content-view and add repository to view
        new_cv = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': new_cv['id'],
                'organization-id': module_org.id,
                'repository-id': new_repo['id'],
            }
        )
        # Publish a version1 of CV
        ContentView.publish({'id': new_cv['id']})
        # Get the CV info
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 1
        # Store the associated environment_id
        env_id = new_cv['lifecycle-environments'][0]['id']
        # Store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Remove the CV from selected environment
        ContentView.remove_from_environment(
            {'id': new_cv['id'], 'lifecycle-environment-id': env_id}
        )
        # Delete the version
        ContentView.version_delete({'id': version1_id})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 0

    @pytest.mark.tier2
    def test_negative_delete_version_by_id(self, module_org):
        """Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        :id: 7334118b-e6c5-4db3-9167-3f006c43f863

        :expectedresults: Content view version is not deleted

        :CaseImportance: Critical

        :CaseLevel: Integration
        """
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1
        cv = content_view['versions'][0]
        # Try to delete content view version while it is in environment Library
        with pytest.raises(CLIReturnCodeError):
            ContentView.version_delete({'id': cv['id']})
        # Check that version was not actually removed from the cv
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

    @pytest.mark.tier1
    def test_positive_remove_lce_by_id(self, module_org):
        """Remove content view from lifecycle environment

        :id: 1bf8a647-d82e-4145-b13b-f92bf6642532

        :expectedresults: Content view removed from environment successfully

        :CaseImportance: Critical
        """
        new_cv = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        ContentView.remove({'id': new_cv['id'], 'environment-ids': env['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['lifecycle-environments']) == 0

    @pytest.mark.tier3
    def test_positive_remove_lce_by_id_and_reassign_ak(self, module_org):
        """Remove content view environment and re-assign activation key to
        another environment and content view

        :id: 3e3ac439-fa85-42ce-8277-2258bc0c7cb4

        :expectedresults: Activation key re-assigned successfully

        :CaseImportance: Medium

        :CaseLevel: Integration
        """
        env = [make_lifecycle_environment({'organization-id': module_org.id}) for _ in range(2)]

        source_cv = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': source_cv['id']})
        source_cv = ContentView.info({'id': source_cv['id']})
        cvv = source_cv['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env[0]['id']})

        destination_cv = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': destination_cv['id']})
        destination_cv = ContentView.info({'id': destination_cv['id']})
        cvv = destination_cv['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env[1]['id']})

        ac_key = make_activation_key(
            {
                'content-view-id': source_cv['id'],
                'lifecycle-environment-id': env[0]['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            }
        )
        source_cv = ContentView.info({'id': source_cv['id']})
        assert source_cv['activation-keys'][0] == ac_key['name']
        destination_cv = ContentView.info({'id': destination_cv['id']})
        assert len(destination_cv['activation-keys']) == 0

        ContentView.remove(
            {
                'id': source_cv['id'],
                'environment-ids': env[0]['id'],
                'key-content-view-id': destination_cv['id'],
                'key-environment-id': env[1]['id'],
            }
        )
        source_cv = ContentView.info({'id': source_cv['id']})
        assert len(source_cv['activation-keys']) == 0
        destination_cv = ContentView.info({'id': destination_cv['id']})
        assert destination_cv['activation-keys'][0] == ac_key['name']

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_remove_lce_by_id_and_reassign_chost(self, module_org):
        """Remove content view environment and re-assign content host to
        another environment and content view

        :id: 40900199-dcfc-4906-bf54-16c13882c05b

        :expectedresults: Content host re-assigned successfully

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        env = [make_lifecycle_environment({'organization-id': module_org.id}) for _ in range(2)]

        source_cv = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': source_cv['id']})
        source_cv = ContentView.info({'id': source_cv['id']})
        cvv = source_cv['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env[0]['id']})

        destination_cv = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': destination_cv['id']})
        destination_cv = ContentView.info({'id': destination_cv['id']})
        cvv = destination_cv['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env[1]['id']})

        source_cv = ContentView.info({'id': source_cv['id']})
        assert source_cv['content-host-count'] == '0'

        make_fake_host(
            {
                'content-view-id': source_cv['id'],
                'lifecycle-environment-id': env[0]['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            }
        )

        source_cv = ContentView.info({'id': source_cv['id']})
        assert source_cv['content-host-count'] == '1'
        destination_cv = ContentView.info({'id': destination_cv['id']})
        assert destination_cv['content-host-count'] == '0'

        ContentView.remove(
            {
                'environment-ids': env[0]['id'],
                'id': source_cv['id'],
                'system-content-view-id': destination_cv['id'],
                'system-environment-id': env[1]['id'],
            }
        )
        source_cv = ContentView.info({'id': source_cv['id']})
        assert source_cv['content-host-count'] == '0'
        destination_cv = ContentView.info({'id': destination_cv['id']})
        assert destination_cv['content-host-count'] == '1'

    @pytest.mark.tier1
    def test_positive_remove_version_by_id(self, module_org):
        """Delete content view version using 'remove' command by id

        :id: e8664353-6601-4566-8478-440be20a089d

        :expectedresults: Content view version deleted successfully

        :CaseImportance: Critical
        """
        new_cv = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 1
        env = new_cv['lifecycle-environments'][0]
        cvv = new_cv['versions'][0]
        ContentView.remove_from_environment(
            {'id': new_cv['id'], 'lifecycle-environment-id': env['id']}
        )

        ContentView.remove({'content-view-version-ids': cvv['id'], 'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 0

    @pytest.mark.tier1
    def test_positive_remove_version_by_name(self, module_org):
        """Delete content view version using 'remove' command by name

        :id: 2c838716-dcd3-4017-bffc-da53727c22a3

        :expectedresults: Content view version deleted successfully

        :BZ: 1416862

        :CaseImportance: Critical
        """
        new_cv = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 1
        env = new_cv['lifecycle-environments'][0]
        cvv = new_cv['versions'][0]
        ContentView.remove_from_environment(
            {'id': new_cv['id'], 'lifecycle-environment-id': env['id']}
        )
        ContentView.remove({'content-view-versions': cvv['version'], 'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 0

    @pytest.mark.tier1
    def test_positive_remove_repository_by_id(self, module_org, module_product):
        """Remove associated repository from content view by id

        :id: 90703181-b3f8-44f6-959a-b65c79b6b6ee

        :customerscenario: true

        :expectedresults: Content view repository removed successfully

        :CaseImportance: Critical
        """
        new_repo = make_repository({'product-id': module_product.id})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['yum-repositories']) == 1
        # Remove repository from CV
        ContentView.remove_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['yum-repositories']) == 0

    @pytest.mark.tier1
    def test_positive_remove_repository_by_name(self, module_org, module_product):
        """Remove associated repository from content view by name

        :id: dc952fe7-eb89-4760-889b-6a3fa17c3e75

        :customerscenario: true

        :expectedresults: Content view repository removed successfully

        :CaseImportance: Critical
        """
        new_repo = make_repository({'product-id': module_product.id})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['yum-repositories']) == 1
        # Remove repository from CV
        ContentView.remove_repository({'id': new_cv['id'], 'repository': new_repo['name']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['yum-repositories']) == 0

    @pytest.mark.tier2
    def test_positive_create_composite(self, module_org):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case
        # (test_negative_add_puppet_repo). Individual modules from a puppet
        # repo, however, are a valid variation.
        """create a composite content view

        :id: bded6acd-8da3-45ea-9e39-19bdc6c06341

        :setup: sync multiple content source/types (RH, custom, etc.)

        :expectedresults: Composite content views are created

        :CaseLevel: Integration

        :CaseImportance: High
        """
        # Create REPO
        new_product = make_product({'organization-id': module_org.id})
        new_repo = make_repository({'product-id': new_product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Create CV
        con_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        # Associate version to composite CV
        ContentView.add_version({'content-view-version-id': version1_id, 'id': con_view['id']})
        # Assert whether version was associated to composite CV
        con_view = ContentView.info({'id': con_view['id']})
        assert con_view['components'][0]['id'] == version1_id

    @pytest.mark.tier2
    def test_positive_create_composite_by_name(self, module_org):
        """Create a composite content view and add non-composite content
        view by its name

        :id: c91271d8-efb8-487e-ab11-2e9e87660d3c

        :expectedresults: Composite content view is created and has another
            view associated to it

        :BZ: 1416857

        :CaseLevel: Integration

        :CaseImportance: High
        """
        new_product = make_product({'organization-id': module_org.id})
        # Create REPO
        new_repo = make_repository({'product-id': new_product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        cvv = new_cv['versions'][0]
        # Create CV
        cv = make_content_view({'composite': True, 'organization-id': module_org.id})
        assert len(cv['components']) == 0
        # Associate version to composite CV
        ContentView.add_version(
            {
                'content-view-version': cvv['version'],
                'content-view': new_cv['name'],
                'name': cv['name'],
                'organization-id': module_org.id,
            }
        )
        # Assert whether version was associated to composite CV
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['components']) == 1
        assert cv['components'][0]['id'] == cvv['id']

    @pytest.mark.tier2
    def test_positive_remove_version_by_id_from_composite(self, module_org, module_product):
        """Create a composite content view and remove its content version by id

        :id: 0ff675d0-45d6-4f15-9e84-3b5ce98ce7de

        :expectedresults: Composite content view info output does not contain
            any values

        :CaseLevel: Integration

        :CaseImportance: High
        """
        # Create new repository
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create new content-view and add repository to view
        new_cv = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': new_cv['id'],
                'organization-id': module_org.id,
                'repository-id': new_repo['id'],
            }
        )
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        # Get the CV info
        new_cv = ContentView.info({'id': new_cv['id']})
        # Create a composite CV
        comp_cv = make_content_view(
            {
                'composite': True,
                'organization-id': module_org.id,
                'component-ids': new_cv['versions'][0]['id'],
            }
        )
        ContentView.publish({'id': comp_cv['id']})
        new_cv = ContentView.info({'id': comp_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        cvv = new_cv['versions'][0]
        ContentView.remove_from_environment(
            {'id': new_cv['id'], 'lifecycle-environment-id': env['id']}
        )
        ContentView.remove({'content-view-version-ids': cvv['id'], 'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 0

    @pytest.mark.tier2
    def test_positive_remove_component_by_name(self, module_org, module_product):
        """Create a composite content view and remove component from it by name

        :id: 908f9cad-b985-4bae-96c0-037ea1d395a6

        :expectedresults: Composite content view info output does not contain
            any values for its components

        :BZ: 1416857

        :CaseLevel: Integration

        :CaseImportance: High
        """
        # Create new repository
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create new content-view and add repository to view
        new_cv = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': new_cv['id'],
                'organization-id': module_org.id,
                'repository-id': new_repo['id'],
            }
        )
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        # Get the CV info
        new_cv = ContentView.info({'id': new_cv['id']})
        # Create a composite CV
        comp_cv = make_content_view(
            {
                'composite': True,
                'organization-id': module_org.id,
                'component-ids': new_cv['versions'][0]['id'],
            }
        )
        assert len(comp_cv['components']) == 1
        ContentView.remove_version(
            {
                'content-view-version': new_cv['versions'][0]['version'],
                'content-view': new_cv['name'],
                'organization-id': module_org.id,
                'name': comp_cv['name'],
            }
        )
        comp_cv = ContentView.info({'id': comp_cv['id']})
        assert len(comp_cv['components']) == 0

    @pytest.mark.tier3
    def test_positive_create_composite_with_component_ids(self, module_org):
        """Create a composite content view with a component_ids option which
        ids are from different content views

        :id: 6d4b94da-258d-4690-a5b6-bacaf6b1671a

        :expectedresults: Composite content view created

        :BZ: 1487265

        :CaseLevel: Integration

        :CaseImportance: High
        """
        # Create first CV
        cv1 = make_content_view({'organization-id': module_org.id})
        # Publish a new version of CV
        ContentView.publish({'id': cv1['id']})
        cv1 = ContentView.info({'id': cv1['id']})
        # Create second CV
        cv2 = make_content_view({'organization-id': module_org.id})
        # Publish a new version of CV
        ContentView.publish({'id': cv2['id']})
        cv2 = ContentView.info({'id': cv2['id']})
        # Let us now store the version ids
        component_ids = [cv1['versions'][0]['id'], cv2['versions'][0]['id']]
        # Create CV
        comp_cv = make_content_view(
            {'composite': True, 'organization-id': module_org.id, 'component-ids': component_ids}
        )
        # Assert whether the composite content view components IDs are equal
        # to the component_ids input values
        comp_cv = ContentView.info({'id': comp_cv['id']})

        assert {comp['id'] for comp in comp_cv['components']} == set(component_ids)

    @pytest.mark.tier3
    def test_negative_create_composite_with_component_ids(self, module_org):
        """Attempt to create a composite content view with a component_ids
        option which ids are from the same content view

        :id: 27ea1f41-44b7-40f0-8990-a4aed09b06b2

        :expectedresults: Composite content view not created

        :BZ: 1487265

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Publish a new version of CV twice
        for _ in range(2):
            ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        # Let us now store the version ids
        component_ids = [version['id'] for version in new_cv['versions']]
        # Try create CV
        with pytest.raises(CLIFactoryError) as context:
            make_content_view(
                {
                    'composite': True,
                    'organization-id': module_org.id,
                    'component-ids': component_ids,
                }
            )
        assert 'Failed to create ContentView with data:' in str(context)

        @pytest.mark.tier3
        def test_positive_update_composite_with_component_ids(module_org):
            """Update a composite content view with a component_ids option

            :id: e6106ff6-c526-40f2-bdc0-ae291f7b267e

            :expectedresults: Composite content view component ids are similar to
                the nested content view versions ids

            :CaseLevel: Integration

            :CaseImportance: Low
            """
            # Create a CV to add to the composite one
            cv = make_content_view({'organization-id': module_org.id})
            # Publish a new version of the CV
            ContentView.publish({'id': cv['id']})
            new_cv = ContentView.info({'id': cv['id']})
            # Let us now store the version ids
            component_ids = new_cv['versions'][0]['id']
            # Create a composite CV
            comp_cv = make_content_view({'composite': True, 'organization-id': module_org.id})
            # Update a composite content view with a component id version
            ContentView.update({'id': comp_cv['id'], 'component-ids': component_ids})
            # Assert whether the composite content view components IDs are equal
            # to the component_ids input values
            comp_cv = ContentView.info({'id': comp_cv['id']})
            assert comp_cv['components'][0]['id'] == component_ids

    @pytest.mark.skip_if_not_set('fake_manifest')
    @pytest.mark.run_in_one_thread
    @pytest.mark.tier1
    def test_positive_add_rh_repo_by_id(self, module_manifest_org, module_rhel_content):
        """Associate Red Hat content to a content view

        :id: b31a85c3-aa56-461b-9e3a-f7754c742573

        :setup: Sync RH content

        :expectedresults: RH Content can be seen in the content view

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Create CV
        new_cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV
        ContentView.add_repository(
            {
                'id': new_cv['id'],
                'organization-id': module_manifest_org.id,
                'repository-id': module_rhel_content['id'],
            }
        )
        new_cv = ContentView.info({'id': new_cv['id']})

        assert new_cv['yum-repositories'][0]['name'] == module_rhel_content['name']

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_add_rh_repo_by_id_and_create_filter(
        self, module_manifest_org, module_rhel_content
    ):
        """Associate Red Hat content to a content view and create filter

        :id: 7723247a-9367-4367-b251-bd079b79b8a2

        :setup: Sync RH content

        :steps: Assure filter(s) applied to associated content

        :expectedresults: Filtered RH content only is available/can be seen in
            a view

        :CaseImportance: Low

        :CaseLevel: Integration

        :BZ: 1359665
        """
        # Create CV
        new_cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV
        ContentView.add_repository(
            {
                'id': new_cv['id'],
                'organization-id': module_manifest_org.id,
                'repository-id': module_rhel_content['id'],
            }
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['yum-repositories'][0]['name'] == module_rhel_content['name']
        name = gen_string('alphanumeric')
        ContentView.filter.create(
            {'content-view-id': new_cv['id'], 'inclusion': 'true', 'name': name, 'type': 'rpm'}
        )
        ContentView.filter.rule.create(
            {'content-view-filter': name, 'content-view-id': new_cv['id'], 'name': 'walgrind'}
        )

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_add_module_stream_filter_rule(self, module_org):
        """Associate module stream content to a content view and create filter rule

        :id: 8186a4b2-1c11-11ea-99cf-d46d6dd3b5b2

        :setup: Sync custom yum repo content

        :steps: Assure filter(s) applied to associated content

        :expectedresults: Filter rule should get applied to Filter

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        create_sync_custom_repo(
            module_org.id, repo_name=repo_name, repo_url=CUSTOM_MODULE_STREAM_REPO_2
        )
        repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[
            0
        ]
        content_view = entities.ContentView(organization=module_org.id, repository=[repo]).create()
        walrus_stream = ModuleStream.list({'search': "name=walrus, stream=5.21"})[0]
        content_view = ContentView.info({'id': content_view.id})
        assert content_view['yum-repositories'][0]['name'] == repo.name
        content_view_filter = ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': filter_name,
                'type': 'modulemd',
            }
        )
        content_view_filter_rule = ContentView.filter.rule.create(
            {
                'content-view-filter': filter_name,
                'content-view-id': content_view['id'],
                'module-stream-ids': walrus_stream['id'],
            }
        )
        filter_info = ContentView.filter.info({'id': content_view_filter['filter-id']})
        assert filter_info['rules'][0]['id'] == content_view_filter_rule['rule-id']

    @pytest.mark.tier2
    def test_positive_add_custom_repo_by_id(self, module_org, module_product):
        """Associate custom content to a Content view

        :id: b813b222-b984-47e0-8d9b-2daa43f9a221

        :setup: Sync custom content

        :expectedresults: Custom content can be seen in a view

        :CaseImportance: High

        :CaseLevel: Integration
        """
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['yum-repositories'][0]['name'] == new_repo['name']

    @pytest.mark.tier1
    def test_positive_add_custom_repo_by_name(self, module_org, module_product):
        """Associate custom content to a content view with name

        :id: 62431e11-bec6-4444-abb0-e3758ba25fd8

        :expectedresults: whether repos are added to cv.

        :CaseImportance: Critical

        :BZ: 1343006
        """
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV with names.
        ContentView.add_repository(
            {
                'name': new_cv['name'],
                'organization': module_org.name,
                'product': module_product.name,
                'repository': new_repo['name'],
            }
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['yum-repositories'][0]['name'] == new_repo['name']

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_add_puppet_module(self, module_org, module_product):
        """Add puppet module to Content View by name

        :id: 81d3305e-c0c2-487b-9fd8-828b3250fe6e

        :expectedresults: Module was added and has latest version.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        module = {'name': 'versioned', 'version': '3.3.3'}
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': module_product.id,
                'url': CUSTOM_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_module = PuppetModule.list(
            {'search': 'name={name} and version={version}'.format(**module)}
        )[0]
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.puppet_module_add(
            {
                'content-view-id': content_view['id'],
                'name': puppet_module['name'],
                'author': puppet_module['author'],
            }
        )
        # Check output of `content-view info` subcommand
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['puppet-modules'])
        assert puppet_module['name'] == content_view['puppet-modules'][0]['name']
        # Check output of `content-view puppet module list` subcommand
        cv_module = ContentView.puppet_module_list({'content-view-id': content_view['id']})
        assert len(cv_module) > 0
        assert puppet_module['version'] in cv_module[0]['version']
        assert 'Latest' in cv_module[0]['version']

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_add_puppet_module_older_version(self, module_org, module_product):
        """Add older version of puppet module to Content View by id/uuid

        :id: 39654b3e-963f-4859-81f2-9992b60433c2

        :Steps:

            1. Upload/sync puppet repo with several versions of the same module
            2. Add older version by id/uuid to CV

        :expectedresults: Exact version (and not latest) was added.

        :CaseLevel: Integration

        :CaseImportance: Low

        :BZ: 1240491
        """
        module = {'name': 'versioned', 'version': '2.2.2'}
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': module_product.id,
                'url': CUSTOM_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_module = PuppetModule.list(
            {'search': 'name={name} and version={version}'.format(**module)}
        )[0]
        for identifier_type in ('uuid', 'id'):
            content_view = make_content_view({'organization-id': module_org.id})
            ContentView.puppet_module_add(
                {
                    'content-view-id': content_view['id'],
                    identifier_type: puppet_module[identifier_type],
                }
            )
            # Check output of `content-view info` subcommand
            content_view = ContentView.info({'id': content_view['id']})
            assert len(content_view['puppet-modules']) > 0
            assert puppet_module['name'] == content_view['puppet-modules'][0]['name']
            # Check output of `content-view puppet module list` subcommand
            cv_module = ContentView.puppet_module_list({'content-view-id': content_view['id']})
            assert len(cv_module) > 0
            assert cv_module[0]['version'] == module['version']

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_puppet_module_by_name(self, module_org, module_product):
        """Remove puppet module from Content View by name

        :id: b9d161de-d2a1-46e1-922d-5e22826a41e4

        :expectedresults: Module successfully removed and no modules are listed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': module_product.id,
                'url': CUSTOM_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({'repository-id': puppet_repository['id']})
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({'organization-id': module_org.id})
        # Add puppet module
        ContentView.puppet_module_add(
            {
                'content-view-id': content_view['id'],
                'name': puppet_module['name'],
                'author': puppet_module['author'],
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['puppet-modules']) > 0
        # Remove puppet module
        ContentView.puppet_module_remove(
            {
                'content-view-id': content_view['id'],
                'name': puppet_module['name'],
                'author': puppet_module['author'],
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['puppet-modules']) == 0

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_puppet_module_by_id(self, module_org, module_product):
        """Remove puppet module from Content View by id

        :id: 972a484c-6f38-4015-b20b-6a83d15b6c97

        :expectedresults: Module successfully removed and no modules are listed

        :CaseLevel: Integration

        :BZ: 1427260

        :CaseImportance: High
        """
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': module_product.id,
                'url': CUSTOM_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({'repository-id': puppet_repository['id']})
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({'organization-id': module_org.id})
        # Add puppet module
        ContentView.puppet_module_add(
            {'content-view-id': content_view['id'], 'id': puppet_module['id']}
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['puppet-modules']) > 0
        # Remove puppet module
        ContentView.puppet_module_remove(
            {'content-view-id': content_view['id'], 'id': content_view['puppet-modules'][0]['id']}
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['puppet-modules']) == 0

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_puppet_module_by_uuid(self, module_org, module_product):
        """Remove puppet module from Content View by uuid

        :id: c63339aa-3d74-4a37-aaef-6777e0f6cb35

        :expectedresults: Module successfully removed and no modules are listed

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': module_product.id,
                'url': CUSTOM_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({'repository-id': puppet_repository['id']})
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({'organization-id': module_org.id})
        # Add puppet module
        ContentView.puppet_module_add(
            {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['puppet-modules']) > 0
        # Remove puppet module
        ContentView.puppet_module_remove(
            {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['puppet-modules']) == 0

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_negative_add_puppet_repo(self, module_org, module_product):
        # Again, individual modules should be ok.
        """attempt to associate puppet repos within a custom content
        view

        :id: 7625c07b-edeb-48ef-85a2-4d1c09874a4b

        :expectedresults: User cannot create a content view that contains
            direct puppet repos.

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        new_repo = make_repository(
            {
                'content-type': 'puppet',
                'product-id': module_product.id,
                'url': FAKE_0_PUPPET_REPO,
            }
        )
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate puppet repo to CV
        with pytest.raises(CLIReturnCodeError):
            ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})

    @pytest.mark.tier2
    def test_negative_add_component_in_non_composite_cv(self, module_org, module_product):
        """attempt to associate components in a non-composite content
        view

        :id: 2a6f150d-e012-47c1-9423-d73f5d620dc9

        :expectedresults: User cannot add components to the view

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create component CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        # Fetch version id
        cv_version = ContentView.version_list({'content-view-id': new_cv['id']})
        # Create non-composite CV
        with pytest.raises(CLIFactoryError):
            make_content_view(
                {'component-ids': cv_version[0]['id'], 'organization-id': module_org.id}
            )

    @pytest.mark.tier2
    def test_negative_add_same_yum_repo_twice(self, module_org, module_product):
        """attempt to associate the same repo multiple times within a
        content view

        :id: 5fb09b30-5f5b-4473-a62b-8f41045ac2b6

        :expectedresults: User cannot add repos multiple times to the view

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['yum-repositories'][0]['name'] == new_repo['name']
        repos_length = len(new_cv['yum-repositories'])
        # Re-associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['yum-repositories']) == repos_length

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_negative_add_same_puppet_repo_twice(self, module_org, module_product):
        """attempt to associate duplicate puppet module(s) within a
        content view

        :id: 674cbae2-8493-466d-a2e4-dc11fb5c6b6f

        :expectedresults: User cannot add puppet modules multiple times to the
            content view

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        # see BZ #1222118
        repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': module_product.id,
                'url': FAKE_0_PUPPET_REPO,
            }
        )
        # Sync REPO
        Repository.synchronize({'id': repository['id']})
        repository = Repository.info({'id': repository['id']})
        puppet_modules = int(repository['content-counts']['puppet-modules'])
        # Create CV
        content_view = make_content_view({'organization-id': module_org.id})
        # Fetch puppet module
        puppet_result = PuppetModule.list({'repository-id': repository['id'], 'per-page': False})
        assert len(puppet_result) == puppet_modules
        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add(
                {
                    'author': puppet_module['author'],
                    'content-view-id': content_view['id'],
                    'name': puppet_module['name'],
                }
            )
            # Re-associate same puppet module to CV
            with pytest.raises(CLIReturnCodeError):
                ContentView.puppet_module_add(
                    {
                        'author': puppet_module['author'],
                        'content-view-id': content_view['id'],
                        'name': puppet_module['name'],
                    }
                )

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier2
    def test_positive_promote_rh_content(self, module_manifest_org, module_rhel_content):
        """attempt to promote a content view containing RH content

        :id: 53b3661b-b40f-466e-a742-bc4b8c1f6cd8

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be promoted

        :CaseImportance: Critical

        :CaseLevel: Integration
        """
        # Create CV
        new_cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': module_rhel_content['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        env1 = make_lifecycle_environment({'organization-id': module_manifest_org.id})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {'id': new_cv['versions'][0]['id'], 'to-lifecycle-environment-id': env1['id']}
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        environment = {'id': env1['id'], 'name': env1['name']}
        assert environment in new_cv['lifecycle-environments']

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    def test_positive_promote_rh_and_custom_content(self, module_manifest_org, module_rhel_content):
        """attempt to promote a content view containing RH content and
        custom content using filters

        :id: f96e97ef-f73c-4506-855c-2392e06f3a6a

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be promoted

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        # Create custom repo
        new_repo = make_repository(
            {'product-id': make_product({'organization-id': module_manifest_org.id})['id']}
        )
        # Sync custom repo
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repos with CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': module_rhel_content['id']})
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        cvf = make_content_view_filter(
            {'content-view-id': new_cv['id'], 'inclusion': 'false', 'type': 'rpm'}
        )
        make_content_view_filter_rule(
            {
                'content-view-filter-id': cvf['filter-id'],
                'min-version': 5,
                'name': FAKE_1_CUSTOM_PACKAGE_NAME,
            }
        )
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        env1 = make_lifecycle_environment({'organization-id': module_manifest_org.id})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {'id': new_cv['versions'][0]['id'], 'to-lifecycle-environment-id': env1['id']}
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        environment = {'id': env1['id'], 'name': env1['name']}
        assert environment in new_cv['lifecycle-environments']

    @pytest.mark.tier2
    def test_positive_promote_custom_content(self, module_org, module_product):
        """attempt to promote a content view containing custom content

        :id: 64c2f1c2-7443-4836-a108-060b913ad2b1

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be promoted

        :CaseImportance: High

        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # create lce
        environment = make_lifecycle_environment({'organization-id': module_org.id})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {
                'id': new_cv['versions'][0]['id'],
                'to-lifecycle-environment-id': environment['id'],
            }
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        assert {'id': environment['id'], 'name': environment['name']} in new_cv[
            'lifecycle-environments'
        ]

    @pytest.mark.tier2
    def test_positive_promote_ccv(self, module_org, module_product):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to promote a content view containing custom content

        :id: 9d31113d-39ec-4524-854c-7f03b0f028fe

        :setup: Multiple environments for an org; custom content synced

        :steps: create a composite view containing multiple content types

        :expectedresults: Content view can be promoted

        :CaseImportance: High

        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create lce
        environment = make_lifecycle_environment({'organization-id': module_org.id})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Create CV
        con_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        # Associate version to composite CV
        ContentView.add_version({'content-view-version-id': version1_id, 'id': con_view['id']})
        # Publish a new version of CV
        ContentView.publish({'id': con_view['id']})
        # As version info is populated after publishing only
        con_view = ContentView.info({'id': con_view['id']})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {
                'id': con_view['versions'][0]['id'],
                'to-lifecycle-environment-id': environment['id'],
            }
        )
        con_view = ContentView.info({'id': con_view['id']})
        assert {'id': environment['id'], 'name': environment['name']} in con_view[
            'lifecycle-environments'
        ]

    @pytest.mark.tier2
    def test_negative_promote_default_cv(self, module_org):
        """attempt to promote a default content view

        :id: ef25a4d9-8852-4d2c-8355-e9b07eb0560b

        :expectedresults: Default content views cannot be promoted

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        environment = make_lifecycle_environment({'organization-id': module_org.id})
        print("Hello, the org ID is currently", module_org.id)
        result = ContentView.list({'organization-id': module_org.id}, per_page=False)
        content_view = random.choice([cv for cv in result if cv['name'] == DEFAULT_CV])
        cvv = ContentView.version_list({'content-view-id': content_view['content-view-id']})[0]
        # Promote the Default CV to the next env
        with pytest.raises(CLIReturnCodeError):
            ContentView.version_promote(
                {'id': cvv['id'], 'to-lifecycle-environment-id': environment['id']}
            )

    @pytest.mark.tier2
    def test_negative_promote_with_invalid_lce(self, module_org, module_product):
        """attempt to promote a content view using an invalid
        environment

        :id: b143552e-610e-4188-b754-e7462ced8cf3

        :expectedresults: Content views cannot be promoted; handled gracefully

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        # Promote the Published version of CV,
        # to the previous env which is Library
        with pytest.raises(CLIReturnCodeError):
            ContentView.version_promote(
                {
                    'id': new_cv['versions'][0]['id'],
                    'to-lifecycle-environment-id': new_cv['lifecycle-environments'][0]['id'],
                }
            )

    # Content Views: publish
    # katello content definition publish --label=MyView

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier2
    def test_positive_publish_rh_content(self, module_manifest_org, module_rhel_content):
        """attempt to publish a content view containing RH content

        :id: d4323759-d869-4d62-ab2e-f1ea3dbb38ba

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be published

        :CaseImportance: Critical

        :CaseLevel: Integration
        """
        # Create CV
        new_cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': module_rhel_content['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['yum-repositories'][0]['name'] == module_rhel_content['name']

        assert new_cv['versions'][0]['version'] == '1.0'

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    def test_positive_publish_rh_and_custom_content(self, module_manifest_org, module_rhel_content):
        """attempt to publish  a content view containing a RH and custom
        repos and has filters

        :id: 0b116172-06a3-4327-81a8-17a098a1a564

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be published

        :CaseImportance: High

        :CaseLevel: Integration
        """
        # Create custom repo
        new_repo = make_repository(
            {'product-id': make_product({'organization-id': module_manifest_org.id})['id']}
        )
        # Sync custom repo
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repos with CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': module_rhel_content['id']})
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        cvf = make_content_view_filter(
            {'content-view-id': new_cv['id'], 'inclusion': 'false', 'type': 'rpm'}
        )
        make_content_view_filter_rule(
            {
                'content-view-filter-id': cvf['filter-id'],
                'min-version': 5,
                'name': FAKE_1_CUSTOM_PACKAGE_NAME,
            }
        )
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert {module_rhel_content['name'], new_repo['name']}.issubset(
            {repo['name'] for repo in new_cv['yum-repositories']}
        )
        assert new_cv['versions'][0]['version'] == '1.0'

    @pytest.mark.tier2
    def test_positive_publish_custom_content(self, module_org, module_product):
        """attempt to publish a content view containing custom content

        :id: 84158023-3980-45c6-87d8-faacea3c942f

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be published

        :CaseImportance: Critical

        :CaseLevel: Integration
        """
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['yum-repositories'][0]['name'] == new_repo['name']
        assert new_cv['versions'][0]['version'] == '1.0'

    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_publish_custom_content_module_stream(self, module_org, module_product):
        """attempt to publish a content view containing custom content
        module streams

        :id: 435e49f0-2891-4b04-98b1-bf303dd3a135

        :setup: Multiple repositories for an org and custom content synced

        :expectedresults: Content view published with module streams
            and count should be correct each time even after republishing CV

        :CaseImportance: Medium

        :CaseLevel: Integration
        """
        software_repo = make_repository(
            {
                'product-id': module_product.id,
                'content-type': 'yum',
                'url': CUSTOM_MODULE_STREAM_REPO_1,
            }
        )

        animal_repo = make_repository(
            {
                'product-id': module_product.id,
                'content-type': 'yum',
                'url': CUSTOM_MODULE_STREAM_REPO_2,
            }
        )

        # Sync REPO's
        Repository.synchronize({'id': animal_repo['id']})
        Repository.synchronize({'id': software_repo['id']})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': animal_repo['id']})
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv_version_1 = ContentView.info({'id': new_cv['id']})['versions'][0]
        module_streams = ModuleStream.list({'content-view-version-id': (new_cv_version_1['id'])})
        assert len(module_streams) > 6
        # Publish another new version of CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': software_repo['id']})
        ContentView.publish({'id': new_cv['id']})
        new_cv_version_2 = ContentView.info({'id': new_cv['id']})['versions'][1]
        module_streams = ModuleStream.list({'content-view-version-id': new_cv_version_2['id']})
        assert len(module_streams) > 13

    @pytest.mark.tier2
    def test_positive_republish_after_content_removed(self, module_org, module_product):
        """Attempt to re-publish content view after all associated content
        were removed from that CV

        :id: 8d67cc35-afd5-49f9-8049-fe1fd2c8cf98

        :setup: Create content of different types and sync it

        :expectedresults: Content view re-published successfully and no error
            is raised

        :BZ: 1323751, 1625783

        :CaseImportance: High

        :CaseLevel: Integration
        """
        # Create new Yum repository
        yum_repo = make_repository({'product-id': module_product.id})
        # Create new Docker repository
        docker_repo = make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': 'quay/busybox',
                'product-id': module_product.id,
                'url': CONTAINER_REGISTRY_HUB,
            }
        )
        # Sync all three repos
        for repo_id in [yum_repo['id'], docker_repo['id']]:
            Repository.synchronize({'id': repo_id})
        # Create CV with different content types
        new_cv = make_content_view(
            {
                'organization-id': module_org.id,
                'repository-ids': [yum_repo['id'], docker_repo['id']],
            }
        )
        # Check that repos were actually assigned to CV
        for repo_type in [
            'yum-repositories',
            'container-image-repositories',
        ]:
            assert len(new_cv[repo_type]) == 1
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 1
        # Remove content from CV
        for repo_id in [yum_repo['id'], docker_repo['id']]:
            ContentView.remove_repository({'id': new_cv['id'], 'repository-id': repo_id})
        new_cv = ContentView.info({'id': new_cv['id']})
        for repo_type in [
            'yum-repositories',
            'container-image-repositories',
        ]:
            assert len(new_cv[repo_type]) == 0
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 2

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier2
    def test_positive_republish_after_rh_content_removed(
        self, module_manifest_org, module_rhel_content
    ):
        """Attempt to re-publish content view after all RH associated content
        was removed from that CV

        :id: 9c6b7678-bb72-4e95-855f-64ad04195661

        :setup: Create RH content

        :expectedresults: Content view re-published successfully and no error
            is raised

        :BZ: 1323751

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        new_cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV
        ContentView.add_repository(
            {
                'id': new_cv['id'],
                'organization-id': module_manifest_org.id,
                'repository-id': module_rhel_content['id'],
            }
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['yum-repositories']) == 1
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 1
        # Remove content from CV
        ContentView.remove_repository(
            {'id': new_cv['id'], 'repository-id': module_rhel_content['id']}
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['yum-repositories']) == 0
        # Publish a new version of CV once more
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert len(new_cv['versions']) == 2

    @pytest.mark.tier2
    def test_positive_publish_ccv(self, module_org, module_product):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to publish a composite content view containing custom
        content

        :id: fde99446-241f-422d-987b-fa1987b654ee

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be published

        :CaseImportance: Critical

        :CaseLevel: Integration
        """
        repository = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': repository['id']})
        # Create CV
        content_view = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repository['id']})
        # Publish a new version of CV
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        # Let us now store the version1 id
        version1_id = content_view['versions'][0]['id']
        # Create composite CV
        composite_cv = make_content_view({'composite': True, 'organization-id': module_org.id})
        # Associate version to composite CV
        ContentView.add_version({'content-view-version-id': version1_id, 'id': composite_cv['id']})
        # Assert whether version was associated to composite CV
        composite_cv = ContentView.info({'id': composite_cv['id']})
        assert composite_cv['components'][0]['id'] == version1_id
        # Publish a new version of CV
        ContentView.publish({'id': composite_cv['id']})
        # Assert whether Version1 was created and exists in Library Env.
        composite_cv = ContentView.info({'id': composite_cv['id']})
        assert composite_cv['lifecycle-environments'][0]['name'] == ENVIRONMENT
        assert composite_cv['versions'][0]['version'] == '1.0'

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_update_version_once(self, module_org, module_product):
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)
        """when publishing new version to environment, version
        gets updated

        :id: cef62d34-c006-4bd0-950e-29e732388c00

        :setup: Multiple environments for an org; multiple versions of a
            content view created/published

        :steps:
            1. publish a view to an environment noting the CV version
            2. edit and republish a new version of a CV

        :expectedresults: Content view version is updated in target
            environment.


        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Create REPO
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create lce
        environment = make_lifecycle_environment({'organization-id': module_org.id})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a version1 of CV
        ContentView.publish({'id': new_cv['id']})
        # Only after we publish version1 the info is populated.
        new_cv = ContentView.info({'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Actual assert for this test happens HERE
        # Test whether the version1 now belongs to Library
        version1 = ContentView.version_info({'id': version1_id})
        assert ENVIRONMENT in [env['label'] for env in version1['lifecycle-environments']]
        # Promotion of version1 to Dev env
        ContentView.version_promote(
            {'id': version1_id, 'to-lifecycle-environment-id': environment['id']}
        )
        # The only way to validate whether env has the version is to
        # validate that version has the env.
        version1 = ContentView.version_info({'id': version1_id})
        assert environment['id'] in [env['id'] for env in version1['lifecycle-environments']]
        # Now Publish version2 of CV
        ContentView.publish({'id': new_cv['id']})
        # Only after we publish version2 the info is populated.
        new_cv = ContentView.info({'id': new_cv['id']})
        new_cv['versions'].sort(key=lambda version: version['id'])
        # Let us now store the version2 id
        version2_id = new_cv['versions'][1]['id']
        # Test whether the version2 now belongs to Library
        version2 = ContentView.version_info({'id': version2_id})
        assert ENVIRONMENT in [env['label'] for env in version2['lifecycle-environments']]
        # Promotion of version2 to Dev env
        ContentView.version_promote(
            {'id': version2_id, 'to-lifecycle-environment-id': environment['id']}
        )
        # Actual assert for this test happens here.
        # Test whether the version2 now belongs to next env
        version2 = ContentView.version_info({'id': version2_id})
        assert environment['id'] in [env['id'] for env in version2['lifecycle-environments']]

    @pytest.mark.tier2
    def test_positive_update_version_multiple(self, module_org, module_product):
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)
        """when publishing new version to environment, version
        gets updated

        :id: e5704b86-9919-471b-8362-1831d1983e70

        :setup: Multiple environments for an org; multiple versions of a
            content view created/published

        :steps:
            1. publish a view to an environment
            2. edit and republish a new version of a CV

        :expectedresults: Content view version is updated in source
            environment.

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({'product-id': module_product.id})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create lce
        environment = make_lifecycle_environment({'organization-id': module_org.id})
        # Create CV
        new_cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV
        ContentView.add_repository({'id': new_cv['id'], 'repository-id': new_repo['id']})
        # Publish a version1 of CV
        ContentView.publish({'id': new_cv['id']})
        # Only after we publish version1 the info is populated.
        new_cv = ContentView.info({'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Test whether the version1 now belongs to Library
        version = ContentView.version_info({'id': version1_id})
        assert ENVIRONMENT in [env['label'] for env in version['lifecycle-environments']]
        # Promotion of version1 to Dev env
        ContentView.version_promote(
            {'id': version1_id, 'to-lifecycle-environment-id': environment['id']}
        )
        # The only way to validate whether env has the version is to
        # validate that version has the env.
        # Test whether the version1 now belongs to next env
        version1 = ContentView.version_info({'id': version1_id})
        assert environment['id'] in [env['id'] for env in version1['lifecycle-environments']]
        # Now Publish version2 of CV
        ContentView.publish({'id': new_cv['id']})
        # As per Dev Notes:
        # Similarly when I publish version y, version x goes away from Library.
        # Actual assert for this test happens here.
        # Test that version1 does not exist in Library after publishing v2
        version1 = ContentView.version_info({'id': version1_id})
        assert len(version1['lifecycle-environments']) == 1
        assert ENVIRONMENT not in [env['label'] for env in version1['lifecycle-environments']]
        # Only after we publish version2 the info is populated.
        new_cv = ContentView.info({'id': new_cv['id']})
        new_cv['versions'].sort(key=lambda version: version['id'])
        # Let us now store the version2 id
        version2_id = new_cv['versions'][1]['id']
        # Promotion of version2 to next env
        ContentView.version_promote(
            {'id': version2_id, 'to-lifecycle-environment-id': environment['id']}
        )
        # Actual assert for this test happens here.
        # Test that version1 does not exist in any/next env after,
        # promoting version2 to next env
        version1 = ContentView.version_info({'id': version1_id})
        assert len(version1['lifecycle-environments']) == 0

    @pytest.mark.tier2
    def test_positive_auto_update_composite_to_latest_cv_version(self, module_org):
        """Ensure that composite content view component is auto updated to the
        latest content view version.

        :id: c0726d16-1802-4b56-a850-d66948ab70e2

        :customerscenario: true

        :steps:
            1. Create a non composite content view and publish it
            2. Create a composite content view
            3. Add the non composite content view to composite one components
                with latest option
            4. Ensure that the published non composite content view version 1
                is in composite content view components
            5. Publish a second time the non composite content view

        :expectedresults: The composite content view component was updated
            to version 2 of the non composite one

        :BZ: 1177766

        :CaseLevel: Integration

        :CaseImportance: High
        """
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1
        version_1_id = content_view['versions'][0]['id']
        composite_cv = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.component_add(
            {
                'composite-content-view-id': composite_cv['id'],
                'component-content-view-id': content_view['id'],
                'latest': True,
            }
        )
        # Ensure that version 1 is in  composite content view components
        components = ContentView.component_list({'composite-content-view-id': composite_cv['id']})
        assert len(components) == 1
        component_id = components[0]['id']
        assert components[0]['version-id'] == f'{version_1_id} (Latest)'
        assert components[0]['current-version'] == '1.0'
        # Publish the content view a second time
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 2
        content_view['versions'].sort(key=lambda version: version['id'])
        # Ensure that composite content view component has been updated to
        # version 2
        version_2_id = content_view['versions'][1]['id']
        assert version_1_id != version_2_id
        components = ContentView.component_list({'composite-content-view-id': composite_cv['id']})
        assert len(components) == 1
        # Ensure that this is the same component that is updated
        assert component_id == components[0]['id']
        assert components[0]['version-id'] == f'{version_2_id} (Latest)'
        assert components[0]['current-version'] == '2.0'

    @pytest.mark.tier3
    def test_positive_subscribe_chost_by_id(self, module_org):
        """Attempt to subscribe content host to content view

        :id: db0bfd9d-3150-427e-9683-a68af33813e7

        :expectedresults: Content host can be subscribed to content view

        :CaseImportance: High

        :CaseLevel: System
        """
        env = make_lifecycle_environment({'organization-id': module_org.id})
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '0'
        make_fake_host(
            {
                'content-view-id': content_view['id'],
                'lifecycle-environment-id': env['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '1'

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    def test_positive_subscribe_chost_by_id_using_rh_content(
        self, module_manifest_org, module_rhel_content
    ):
        """Attempt to subscribe content host to content view that has
        Red Hat repository assigned to it

        :id: aeaaa363-5146-45ee-8c81-e54c7876fb81

        :expectedresults: Content Host can be subscribed to content view with
            Red Hat repository

        :CaseLevel: System

        :CaseImportance: Medium
        """
        env = make_lifecycle_environment({'organization-id': module_manifest_org.id})
        content_view = make_content_view({'organization-id': module_manifest_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_manifest_org.id,
                'repository-id': module_rhel_content['id'],
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['yum-repositories'][0]['name'] == module_rhel_content['name']
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '0'
        make_fake_host(
            {
                'content-view-id': content_view['id'],
                'lifecycle-environment-id': env['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_manifest_org.id,
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '1'

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_subscribe_chost_by_id_using_rh_content_and_filters(
        self, module_manifest_org, module_rhel_content
    ):
        """Attempt to subscribe content host to filtered content view
        that has Red Hat repository assigned to it

        :id: 8d1e0daf-6130-4b50-827d-061e6c32749d

        :expectedresults: Content Host can be subscribed to filtered content
            view with Red Hat repository

        :CaseLevel: System

        :BZ: 1359665

        :CaseImportance: Low
        """
        env = make_lifecycle_environment({'organization-id': module_manifest_org.id})
        content_view = make_content_view({'organization-id': module_manifest_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_manifest_org.id,
                'repository-id': module_rhel_content['id'],
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['yum-repositories'][0]['name'] == module_rhel_content['name']

        name = gen_string('utf8')
        ContentView.filter.create(
            {
                'content-view-id': content_view['id'],
                'inclusion': 'true',
                'name': name,
                'type': 'rpm',
            }
        )

        make_content_view_filter_rule(
            {
                'content-view-filter': name,
                'content-view-id': content_view['id'],
                'name': gen_string('utf8'),
            }
        )

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env['id']})

        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '0'

        make_fake_host(
            {
                'content-view-id': content_view['id'],
                'lifecycle-environment-id': env['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_manifest_org.id,
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '1'

    @pytest.mark.tier3
    def test_positive_subscribe_chost_by_id_using_custom_content(self, module_org):
        """Attempt to subscribe content host to content view that has
        custom repository assigned to it

        :id: 9758756a-2536-4777-a6a9-ed618453ebe7

        :expectedresults: Content Host can be subscribed to content view with
            custom repository

        :CaseLevel: System

        :CaseImportance: High
        """
        new_product = make_product({'organization-id': module_org.id})
        new_repo = make_repository({'product-id': new_product['id']})
        env = make_lifecycle_environment({'organization-id': module_org.id})
        Repository.synchronize({'id': new_repo['id']})
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': new_repo['id'],
            }
        )

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env['id']})

        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '0'

        make_fake_host(
            {
                'content-view-id': content_view['id'],
                'lifecycle-environment-id': env['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '1'

    @pytest.mark.tier3
    def test_positive_subscribe_chost_by_id_using_ccv(self, module_org):
        """Attempt to subscribe content host to composite content view

        :id: 4be340c0-9e58-4b96-ab37-d7e3b12c724f

        :expectedresults: Content host can be subscribed to composite content
            view

        :CaseImportance: High

        :CaseLevel: System
        """
        env = make_lifecycle_environment({'organization-id': module_org.id})
        content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env['id']})

        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '0'

        make_fake_host(
            {
                'content-view-id': content_view['id'],
                'lifecycle-environment-id': env['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '1'

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_subscribe_chost_by_id_using_puppet_content(self, module_org):
        """Attempt to subscribe content host to content view that has
        puppet module assigned to it

        :id: 7f45a162-e944-4e2c-a892-b26d1d21c844

        :expectedresults: Content Host can be subscribed to content view with
            puppet module

        :CaseLevel: System

        :CaseImportance: Low
        """
        # see BZ #1222118
        new_product = make_product({'organization-id': module_org.id})

        repository = make_repository(
            {'content-type': 'puppet', 'product-id': new_product['id'], 'url': FAKE_0_PUPPET_REPO}
        )
        Repository.synchronize({'id': repository['id']})

        content_view = make_content_view({'organization-id': module_org.id})

        puppet_result = PuppetModule.list({'repository-id': repository['id'], 'per-page': False})

        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add(
                {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
            )

        env = make_lifecycle_environment({'organization-id': module_org.id})

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': env['id']})

        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '0'

        make_fake_host(
            {
                'content-view-id': content_view['id'],
                'lifecycle-environment-id': env['id'],
                'name': gen_alphanumeric(),
                'organization-id': module_org.id,
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert content_view['content-host-count'] == '1'

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_sub_host_with_restricted_user_perm_at_custom_loc(
        self, module_org, rhel7_contenthost
    ):
        """Attempt to subscribe a host with restricted user permissions and
        custom location.

        :id: 0184ab20-2ffd-4377-9efa-4f25bb6e5a0c

        :BZ: 1379856, 1470765, 1511481

        :steps:

            1. Create organization, location, content view with yum repository.
            2. Publish the content view
            3. Create a user within the created organization and location with
               the following permissions::

                - (Miscellaneous) [my_organizations]
                - Environment [view_environments]
                - Organization [view_organizations],
                - Katello::Subscription: [
                    view_subscriptions,
                    attach_subscriptions,
                    unattach_subscriptions,
                    import_manifest,
                    delete_manifest]
                - Katello::ContentView [view_content_views]
                - ConfigGroup [view_config_groups]
                - Hostgroup view_hostgroups
                - Host [view_hosts, create_hosts, edit_hosts]
                - Location [view_locations]
                - Katello::KTEnvironment [view_lifecycle_environments]
                - SmartProxy [view_smart_proxies, view_capsule_content]
                - Architecture [view_architectures]

        :expectedresults: host subscribed to content view with user that has
            restricted permissions.

        :CaseLevel: System
        """
        # Note: this test has been stubbed waitin for bug 1511481 resolution
        # prepare the user and the required permissions data
        user_name = gen_alphanumeric()
        user_password = gen_alphanumeric()
        required_rc_permissions = {
            '(Miscellaneous)': ['my_organizations'],
            'Environment': ['view_environments'],
            'Organization': ['view_organizations'],
            'Katello::Subscription': [
                'view_subscriptions',
                'attach_subscriptions',
                'unattach_subscriptions',
                'import_manifest',
                'delete_manifest',
            ],
            'Katello::ContentView': ['view_content_views'],
            'ConfigGroup': ['view_config_groups'],
            'Hostgroup': ['view_hostgroups'],
            'Host': ['view_hosts', 'create_hosts', 'edit_hosts'],
            'Location': ['view_locations'],
            'Katello::KTEnvironment': ['view_lifecycle_environments'],
            'SmartProxy': ['view_smart_proxies', 'view_capsule_content'],
            'Architecture': ['view_architectures'],
        }
        # Create a location and organization
        loc = make_location()
        default_loc = Location.info({'name': DEFAULT_LOC})
        org = make_org()
        Org.add_location({'id': org['id'], 'location-id': loc['id']})
        # Create a non admin user, for the moment without any permissions
        user = make_user(
            {
                'admin': False,
                'default-organization-id': org['id'],
                'organization-ids': [org['id']],
                'default-location-id': loc['id'],
                'location-ids': [loc['id'], default_loc['id']],
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
        for resource_type, permission_names in required_rc_permissions.items():
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
            make_filter({'role-id': role['id'], 'permissions': permission_names})
        # Add the created and initiated role with permissions to user
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # assert that the user is not an admin one and cannot read the current
        # role info (note: view_roles is not in the required permissions)
        with pytest.raises(CLIReturnCodeError) as context:
            Role.with_user(user_name, user_password).info({'id': role['id']})
        assert 'Access denied' in str(context)
        # Create a lifecycle environment
        env = make_lifecycle_environment({'organization-id': org['id']})
        # Create a product
        product = make_product({'organization-id': org['id']})
        # Create a yum repository and synchronize
        repo = make_repository({'product-id': product['id'], 'url': FAKE_1_YUM_REPO})
        Repository.synchronize({'id': repo['id']})
        # Create a content view, add the yum repository and publish
        content_view = make_content_view({'organization-id': org['id']})
        ContentView.add_repository(
            {'id': content_view['id'], 'organization-id': org['id'], 'repository-id': repo['id']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        # assert that the content view has been published and has versions
        assert len(content_view['versions']) > 0
        content_view_version = content_view['versions'][0]
        # Promote the content view version to the created environment
        ContentView.version_promote(
            {'id': content_view_version['id'], 'to-lifecycle-environment-id': env['id']}
        )
        # assert that the user can read the content view info as per required
        # permissions
        user_content_view = ContentView.with_user(user_name, user_password).info(
            {'id': content_view['id']}
        )
        # assert that this is the same content view
        assert content_view['name'] == user_content_view['name']
        # create a client host and register it with the created user
        rhel7_contenthost.install_katello_ca()
        rhel7_contenthost.register_contenthost(
            org['label'],
            lce=f'{env["name"]}/{content_view["name"]}',
            username=user_name,
            password=user_password,
        )
        assert rhel7_contenthost.subscribed
        # check that the client host exist in the system
        org_hosts = Host.list({'organization-id': org['id']})
        assert len(org_hosts) == 1
        assert org_hosts[0]['name'] == rhel7_contenthost.hostname

    @pytest.mark.tier3
    def test_positive_sub_host_with_restricted_user_perm_at_default_loc(
        self, module_org, rhel7_contenthost
    ):
        """Attempt to subscribe a host with restricted user permissions and
        default location.

        :id: 7b5ec90b-3942-48a9-9cc1-a361e698d16d

        :BZ: 1379856, 1470765

        :steps:

            1. Create organization, content view with custom yum repository.
            2. Publish the content view
            3. Create a user within the created organization and default
               location  with the following permissions::

                - (Miscellaneous) [my_organizations]
                - Environment [view_environments]
                - Organization [view_organizations],
                - Katello::Subscription: [
                    view_subscriptions,
                    attach_subscriptions,
                    unattach_subscriptions,
                    import_manifest,
                    delete_manifest]
                - Katello::ContentView [view_content_views]
                - ConfigGroup [view_config_groups]
                - Hostgroup view_hostgroups
                - Host [view_hosts, create_hosts, edit_hosts]
                - Location [view_locations]
                - Katello::KTEnvironment [view_lifecycle_environments]
                - SmartProxy [view_smart_proxies, view_capsule_content]
                - Architecture [view_architectures]

        :expectedresults: host subscribed to content view with user that has
            restricted permissions.

        :CaseLevel: System
        """
        # prepare the user and the required permissions data
        user_name = gen_alphanumeric()
        user_password = gen_alphanumeric()
        required_rc_permissions = {
            '(Miscellaneous)': ['my_organizations'],
            'Environment': ['view_environments'],
            'Organization': ['view_organizations'],
            'Katello::Subscription': [
                'view_subscriptions',
                'attach_subscriptions',
                'unattach_subscriptions',
                'import_manifest',
                'delete_manifest',
            ],
            'Katello::ContentView': ['view_content_views'],
            'ConfigGroup': ['view_config_groups'],
            'Hostgroup': ['view_hostgroups'],
            'Host': ['view_hosts', 'create_hosts', 'edit_hosts'],
            'Location': ['view_locations'],
            'Katello::KTEnvironment': ['view_lifecycle_environments'],
            'SmartProxy': ['view_smart_proxies', 'view_capsule_content'],
            'Architecture': ['view_architectures'],
        }
        # Create organization
        loc = Location.info({'name': DEFAULT_LOC})
        org = make_org()
        Org.add_location({'id': org['id'], 'location-id': loc['id']})
        # Create a non admin user, for the moment without any permissions
        user = make_user(
            {
                'admin': False,
                'default-organization-id': org['id'],
                'organization-ids': [org['id']],
                'default-location-id': loc['id'],
                'location-ids': [loc['id']],
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
        for resource_type, permission_names in required_rc_permissions.items():
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
            make_filter({'role-id': role['id'], 'permissions': permission_names})
        # Add the created and initiated role with permissions to user
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # assert that the user is not an admin one and cannot read the current
        # role info (note: view_roles is not in the required permissions)
        with pytest.raises(CLIReturnCodeError) as context:
            Role.with_user(user_name, user_password).info({'id': role['id']})
            assert '403 Forbidden' in str(context)
        # Create a lifecycle environment
        env = make_lifecycle_environment({'organization-id': org['id']})
        # Create a product
        product = make_product({'organization-id': org['id']})
        # Create a yum repository and synchronize
        repo = make_repository({'product-id': product['id'], 'url': FAKE_1_YUM_REPO})
        Repository.synchronize({'id': repo['id']})
        # Create a content view, add the yum repository and publish
        content_view = make_content_view({'organization-id': org['id']})
        ContentView.add_repository(
            {'id': content_view['id'], 'organization-id': org['id'], 'repository-id': repo['id']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        # assert that the content view has been published and has versions
        assert len(content_view['versions']) > 0
        content_view_version = content_view['versions'][0]
        # Promote the content view version to the created environment
        ContentView.version_promote(
            {'id': content_view_version['id'], 'to-lifecycle-environment-id': env['id']}
        )
        # assert that the user can read the content view info as per required
        # permissions
        user_content_view = ContentView.with_user(user_name, user_password).info(
            {'id': content_view['id']}
        )
        # assert that this is the same content view
        assert content_view['name'] == user_content_view['name']
        # create a client host and register it with the created user
        rhel7_contenthost.install_katello_ca()
        rhel7_contenthost.register_contenthost(
            org['label'],
            lce='/'.join([env['name'], content_view['name']]),
            username=user_name,
            password=user_password,
        )
        assert rhel7_contenthost.subscribed
        # check that the client host exist in the system
        org_hosts = Host.list({'organization-id': org['id']})
        assert len(org_hosts) == 1
        assert org_hosts[0]['name'] == rhel7_contenthost.hostname

    @pytest.mark.tier1
    def test_positive_clone_by_id(self, module_org):
        """Clone existing content view by id

        :id: e3b63e6e-0964-45fb-a765-e1885c0ecbdd

        :expectedresults: Content view is cloned successfully

        :CaseImportance: Critical
        """
        cloned_cv_name = gen_string('alpha')
        content_view = make_content_view({'organization-id': module_org.id})
        new_cv = ContentView.copy({'id': content_view['id'], 'new-name': cloned_cv_name})[0]
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['name'] == cloned_cv_name

    @pytest.mark.tier1
    def test_positive_clone_by_name(self, module_org):
        """Clone existing content view by name

        :id: b4c94286-ebbe-4e4c-a1df-22cb7055984d

        :expectedresults: Content view is cloned successfully

        :BZ: 1416857

        :CaseImportance: Critical
        """
        cloned_cv_name = gen_string('alpha')
        content_view = make_content_view({'organization-id': module_org.id})
        new_cv = ContentView.copy(
            {
                'name': content_view['name'],
                'organization-id': module_org.id,
                'new-name': cloned_cv_name,
            }
        )[0]
        new_cv = ContentView.info({'id': new_cv['id']})
        assert new_cv['name'] == cloned_cv_name

    @pytest.mark.tier2
    def test_positive_clone_within_same_env(self, module_org):
        """Attempt to create, publish and promote new content view based on
        existing view within the same environment as the original content view

        :id: 4d7fa623-3516-4abe-a98c-98acbfb7e9c9

        :expectedresults: Cloned content view can be published and promoted to
            the same environment as the original content view

        :CaseLevel: Integration

        :CaseImportance: High
        """
        cloned_cv_name = gen_string('alpha')
        lc_env = make_lifecycle_environment({'organization-id': module_org.id})
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': lc_env['id']})
        new_cv = ContentView.copy({'id': content_view['id'], 'new-name': cloned_cv_name})[0]
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        cvv = new_cv['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': lc_env['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        assert {'id': lc_env['id'], 'name': lc_env['name']} in new_cv['lifecycle-environments']

    @pytest.mark.tier2
    def test_positive_clone_with_diff_env(self, module_org):
        """Attempt to create, publish and promote new content view based on
        existing view but promoted to a different environment

        :id: 308ffaa3-cd01-4a16-b84d-c60c32959235

        :expectedresults: Cloned content view can be published and promoted to
            a different environment as the original content view

        :CaseImportance: Low

        :CaseLevel: Integration
        """
        cloned_cv_name = gen_string('alpha')
        lc_env = make_lifecycle_environment({'organization-id': module_org.id})
        lc_env_cloned = make_lifecycle_environment({'organization-id': module_org.id})
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': lc_env['id']})
        new_cv = ContentView.copy({'id': content_view['id'], 'new-name': cloned_cv_name})[0]
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        cvv = new_cv['versions'][0]
        ContentView.version_promote(
            {'id': cvv['id'], 'to-lifecycle-environment-id': lc_env_cloned['id']}
        )
        new_cv = ContentView.info({'id': new_cv['id']})
        assert {'id': lc_env_cloned['id'], 'name': lc_env_cloned['name']} in new_cv[
            'lifecycle-environments'
        ]

    @pytest.mark.stubbed
    def test_positive_restart_dynflow_promote(self):
        """attempt to restart a failed content view promotion

        :id: 2be23f85-3f62-4319-87ea-41f28cf401dc

        :steps:
            1. (Somehow) cause a CV promotion to fail.  Not exactly sure how
               yet.
            2. Via Dynflow, restart promotion

        :expectedresults: Promotion is restarted.

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.stubbed
    def test_positive_restart_dynflow_publish(self):
        """attempt to restart a failed content view publish

        :id: 24468014-46b2-403e-8ed6-2daeda5a0163

        :steps:
            1. (Somehow) cause a CV publish  to fail.  Not exactly sure how
               yet.
            2. Via Dynflow, restart publish

        :expectedresults: Publish is restarted.

        :CaseAutomation: NotAutomated
        """

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_renamed_cv_version_from_default_env(self, module_org):
        """Remove version of renamed content view from Library environment

        :id: aa9bbfda-72e8-45ec-b26d-fdf2691980cf

        :Steps:

            1. Create a content view
            2. Add a yum repo to the content view
            3. Publish the content view
            4. Rename the content view
            5. remove the published version from Library environment

        :expectedresults: content view version is removed from Library
            environment

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        new_name = gen_string('alpha')
        custom_yum_product = make_product({'organization-id': module_org.id})
        custom_yum_repo = make_repository(
            {
                'content-type': 'yum',
                'product-id': custom_yum_product['id'],
                'url': FAKE_1_YUM_REPO,
            }
        )
        Repository.synchronize({'id': custom_yum_repo['id']})
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': custom_yum_repo['id'],
            }
        )
        ContentView.publish({'id': content_view['id']})
        # ensure that the published content version is in Library environment
        content_view_versions = ContentView.info({'id': content_view['id']})['versions']
        assert len(content_view_versions) > 0
        content_view_version = content_view_versions[-1]
        assert ENVIRONMENT in _get_content_view_version_lce_names_set(
            content_view['id'], content_view_version['id']
        )
        # rename the content view
        ContentView.update({'id': content_view['id'], 'new-name': new_name})
        content_view = ContentView.info({'id': content_view['id']})
        assert new_name == content_view['name']
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'lifecycle-environment': ENVIRONMENT,
            }
        )
        # ensure that the published content version is not in Library
        # environment
        assert ENVIRONMENT not in _get_content_view_version_lce_names_set(
            content_view['id'], content_view_version['id']
        )

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_promoted_cv_version_from_default_env(self, module_org):
        """Remove promoted content view version from Library environment

        :id: 6643837a-560a-47de-aa4d-90778914dcfa

        :Steps:

            1. Create a content view
            2. Add a puppet module(s) to the content view
            3. Publish the content view
            4. Promote the content view version from Library -> DEV
            5. remove the content view version from Library environment

        :expectedresults:

            1. Content view version exist only in DEV and not in Library
            2. The puppet module(s) exists in content view version

        :CaseLevel: Integration

        :CaseImportance: High
        """
        lce_dev = make_lifecycle_environment({'organization-id': module_org.id})
        puppet_product = make_product({'organization-id': module_org.id})
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': puppet_product['id'],
                'url': FAKE_0_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {'repository-id': puppet_repository['id'], 'per-page': False}
        )
        assert len(puppet_modules) > 0
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.puppet_module_add(
            {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view_versions = ContentView.info({'id': content_view['id']})['versions']
        assert len(content_view_versions) > 0
        content_view_version = content_view_versions[-1]
        ContentView.version_promote(
            {'id': content_view_version['id'], 'to-lifecycle-environment-id': lce_dev['id']}
        )
        # ensure that the published content version is in Library and DEV
        # environments
        content_view_version_info = ContentView.version_info(
            {
                'organization-id': module_org.id,
                'content-view-id': content_view['id'],
                'id': content_view_version['id'],
            }
        )
        content_view_version_lce_names = {
            lce['name'] for lce in content_view_version_info['lifecycle-environments']
        }
        assert {ENVIRONMENT, lce_dev['name']} == content_view_version_lce_names
        initial_puppet_modules_ids = {
            puppet_module['id']
            for puppet_module in content_view_version_info.get('puppet-modules', [])
        }
        assert len(initial_puppet_modules_ids) > 0
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'lifecycle-environment': ENVIRONMENT,
            }
        )
        # ensure content view version not in Library and only in DEV
        # environment and that puppet module still exist
        content_view_version_info = ContentView.version_info(
            {
                'organization-id': module_org.id,
                'content-view-id': content_view['id'],
                'id': content_view_version['id'],
            }
        )
        content_view_version_lce_names = {
            lce['name'] for lce in content_view_version_info['lifecycle-environments']
        }
        assert {lce_dev['name']} == content_view_version_lce_names
        puppet_modules_ids = {
            puppet_module['id']
            for puppet_module in content_view_version_info.get('puppet-modules', [])
        }
        assert initial_puppet_modules_ids == puppet_modules_ids

    @pytest.mark.tier2
    def test_positive_remove_qe_promoted_cv_version_from_default_env(self, module_org):
        """Remove QE promoted content view version from Library environment

        :id: e286697f-4113-40a3-b8e8-9ca50647e6d5

        :Steps:

            1. Create a content view
            2. Add docker repo(s) to it
            3. Publish content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE and not in
            Library

        :CaseLevel: Integration

        :CaseImportance: High
        """
        lce_dev = make_lifecycle_environment({'organization-id': module_org.id})
        lce_qe = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_dev['name']}
        )
        docker_product = make_product({'organization-id': module_org.id})
        docker_repository = make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                'name': gen_string('alpha', 20),
                'product-id': docker_product['id'],
                'url': CONTAINER_REGISTRY_HUB,
            }
        )
        Repository.synchronize({'id': docker_repository['id']})
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': docker_repository['id'],
            }
        )
        ContentView.publish({'id': content_view['id']})
        content_view_versions = ContentView.info({'id': content_view['id']})['versions']
        assert len(content_view_versions) > 0
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe]:
            ContentView.version_promote(
                {'id': content_view_version['id'], 'to-lifecycle-environment-id': lce['id']}
            )
        # ensure that the published content version is in Library, DEV and QE
        # environments
        assert {
            ENVIRONMENT,
            lce_dev['name'],
            lce_qe['name'],
        } == _get_content_view_version_lce_names_set(content_view['id'], content_view_version['id'])
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'lifecycle-environment': ENVIRONMENT,
            }
        )
        # ensure content view version is not in Library and only in DEV and QE
        # environments
        assert {lce_dev['name'], lce_qe['name']} == _get_content_view_version_lce_names_set(
            content_view['id'], content_view_version['id']
        )

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_prod_promoted_cv_version_from_default_env(self, module_org):
        """Remove PROD promoted content view version from Library environment

        :id: ffe3d64e-c3d2-4889-9454-ccc6b10f4db7

        :Steps:

            1. Create a content view
            2. Add yum repositories, puppet modules, docker repositories to CV
            3. Publish content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> PROD
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE, PROD and
            not in Library

        :CaseImportance: High

        :CaseLevel: Integration
        """
        lce_dev = make_lifecycle_environment({'organization-id': module_org.id})
        lce_qe = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_dev['name']}
        )
        lce_prod = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_qe['name']}
        )
        custom_yum_product = make_product({'organization-id': module_org.id})
        custom_yum_repo = make_repository(
            {
                'content-type': 'yum',
                'product-id': custom_yum_product['id'],
                'url': FAKE_1_YUM_REPO,
            }
        )
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({'organization-id': module_org.id})
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': puppet_product['id'],
                'url': FAKE_0_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {'repository-id': puppet_repository['id'], 'per-page': False}
        )
        assert len(puppet_modules) > 0
        puppet_module = random.choice(puppet_modules)
        docker_product = make_product({'organization-id': module_org.id})
        docker_repository = make_repository(
            {
                'content-type': 'docker',
                'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                'name': gen_string('alpha', 20),
                'product-id': docker_product['id'],
                'url': CONTAINER_REGISTRY_HUB,
            }
        )
        Repository.synchronize({'id': docker_repository['id']})
        content_view = make_content_view({'organization-id': module_org.id})
        for repo in [custom_yum_repo, docker_repository]:
            ContentView.add_repository(
                {
                    'id': content_view['id'],
                    'organization-id': module_org.id,
                    'repository-id': repo['id'],
                }
            )
        ContentView.puppet_module_add(
            {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view_versions = ContentView.info({'id': content_view['id']})['versions']
        assert len(content_view_versions) > 0
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_prod]:
            ContentView.version_promote(
                {'id': content_view_version['id'], 'to-lifecycle-environment-id': lce['id']}
            )
        # ensure that the published content version is in Library, DEV, QE and
        # PROD environments
        assert {
            ENVIRONMENT,
            lce_dev['name'],
            lce_qe['name'],
            lce_prod['name'],
        } == _get_content_view_version_lce_names_set(content_view['id'], content_view_version['id'])
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'lifecycle-environment': ENVIRONMENT,
            }
        )
        # ensure content view version is not in Library and only in DEV, QE
        # and PROD environments
        assert {
            lce_dev['name'],
            lce_qe['name'],
            lce_prod['name'],
        } == _get_content_view_version_lce_names_set(content_view['id'], content_view_version['id'])

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_cv_version_from_env(self, module_org):
        """Remove promoted content view version from environment

        :id: 577757ac-b184-4ece-9310-182dd5ceb718

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> STAGE -> PROD
            5. remove the content view version from PROD environment
            6. Assert: content view version exists only in Library, DEV, QE,
               STAGE and not in PROD
            7. Promote again from STAGE -> PROD

        :expectedresults: Content view version exist in Library, DEV, QE,
            STAGE, PROD

        :CaseLevel: Integration

        :CaseImportance: High
        """
        lce_dev = make_lifecycle_environment({'organization-id': module_org.id})
        lce_qe = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_dev['name']}
        )
        lce_stage = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_qe['name']}
        )
        lce_prod = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_stage['name']}
        )
        custom_yum_product = make_product({'organization-id': module_org.id})
        custom_yum_repo = make_repository(
            {
                'content-type': 'yum',
                'product-id': custom_yum_product['id'],
                'url': FAKE_1_YUM_REPO,
            }
        )
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({'organization-id': module_org.id})
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': puppet_product['id'],
                'url': FAKE_0_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {'repository-id': puppet_repository['id'], 'per-page': False}
        )
        assert len(puppet_modules) > 0
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': custom_yum_repo['id'],
            }
        )
        ContentView.puppet_module_add(
            {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view_versions = ContentView.info({'id': content_view['id']})['versions']
        assert len(content_view_versions) > 0
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote(
                {'id': content_view_version['id'], 'to-lifecycle-environment-id': lce['id']}
            )
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        assert {
            ENVIRONMENT,
            lce_dev['name'],
            lce_qe['name'],
            lce_stage['name'],
            lce_prod['name'],
        } == _get_content_view_version_lce_names_set(content_view['id'], content_view_version['id'])
        # remove content view version from PROD lifecycle environment
        ContentView.remove_from_environment(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'lifecycle-environment': lce_prod['name'],
            }
        )
        # ensure content view version is not in PROD and only in Library, DEV,
        # QE and STAGE environments
        assert {
            ENVIRONMENT,
            lce_dev['name'],
            lce_qe['name'],
            lce_stage['name'],
        } == _get_content_view_version_lce_names_set(content_view['id'], content_view_version['id'])
        # promote content view version to PROD environment again
        ContentView.version_promote(
            {'id': content_view_version['id'], 'to-lifecycle-environment-id': lce_prod['id']}
        )
        assert {
            ENVIRONMENT,
            lce_dev['name'],
            lce_qe['name'],
            lce_stage['name'],
            lce_prod['name'],
        } == _get_content_view_version_lce_names_set(content_view['id'], content_view_version['id'])

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_cv_version_from_multi_env(self, module_org):
        """Remove promoted content view version from multiple environment

        :id: 997cfd7d-9029-47e2-a41e-84f4370b5ce5

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> STAGE -> PROD
            5. Remove content view version from QE, STAGE and PROD

        :expectedresults: Content view version exists only in Library, DEV

        :CaseLevel: Integration

        :CaseImportance: High
        """
        lce_dev = make_lifecycle_environment({'organization-id': module_org.id})
        lce_qe = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_dev['name']}
        )
        lce_stage = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_qe['name']}
        )
        lce_prod = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_stage['name']}
        )
        custom_yum_product = make_product({'organization-id': module_org.id})
        custom_yum_repo = make_repository(
            {
                'content-type': 'yum',
                'product-id': custom_yum_product['id'],
                'url': FAKE_1_YUM_REPO,
            }
        )
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({'organization-id': module_org.id})
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': puppet_product['id'],
                'url': FAKE_0_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {'repository-id': puppet_repository['id'], 'per-page': False}
        )
        assert len(puppet_modules) > 0
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': custom_yum_repo['id'],
            }
        )
        ContentView.puppet_module_add(
            {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view_versions = ContentView.info({'id': content_view['id']})['versions']
        assert len(content_view_versions) > 0
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote(
                {'id': content_view_version['id'], 'to-lifecycle-environment-id': lce['id']}
            )
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        assert {
            ENVIRONMENT,
            lce_dev['name'],
            lce_qe['name'],
            lce_stage['name'],
            lce_prod['name'],
        } == _get_content_view_version_lce_names_set(content_view['id'], content_view_version['id'])
        # remove content view version from QE, STAGE, PROD lifecycle
        # environments
        for lce in [lce_qe, lce_stage, lce_prod]:
            ContentView.remove_from_environment(
                {
                    'id': content_view['id'],
                    'organization-id': module_org.id,
                    'lifecycle-environment': lce['name'],
                }
            )
        # ensure content view version is not in PROD and only in Library, DEV,
        # QE and STAGE environments
        assert {ENVIRONMENT, lce_dev['name']} == _get_content_view_version_lce_names_set(
            content_view['id'], content_view_version['id']
        )

    @pytest.mark.tier3
    def test_positive_delete_cv_promoted_to_multi_env(self, module_org):
        """Delete published content view with version promoted to multiple
         environments

        :id: 93dd7518-5901-4a71-a4c3-0f1215238b26

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
               -> QE -> STAGE -> PROD
            5. Delete the content view (may delete the published versions
               environments prior this step)

        :expectedresults: The content view doesn't exists

        :CaseLevel: Integration

        :CaseImportance: High
        """
        lce_dev = make_lifecycle_environment({'organization-id': module_org.id})
        lce_qe = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_dev['name']}
        )
        lce_stage = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_qe['name']}
        )
        lce_prod = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': lce_stage['name']}
        )
        custom_yum_product = make_product({'organization-id': module_org.id})
        custom_yum_repo = make_repository(
            {
                'content-type': 'yum',
                'product-id': custom_yum_product['id'],
                'url': FAKE_1_YUM_REPO,
            }
        )
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({'organization-id': module_org.id})
        puppet_repository = make_repository(
            {
                'content-type': 'puppet',
                'product-id': puppet_product['id'],
                'url': FAKE_0_PUPPET_REPO,
            }
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list(
            {'repository-id': puppet_repository['id'], 'per-page': False}
        )
        assert len(puppet_modules) > 0
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({'organization-id': module_org.id})
        ContentView.add_repository(
            {
                'id': content_view['id'],
                'organization-id': module_org.id,
                'repository-id': custom_yum_repo['id'],
            }
        )
        ContentView.puppet_module_add(
            {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view_versions = ContentView.info({'id': content_view['id']})['versions']
        assert len(content_view_versions) > 0
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote(
                {'id': content_view_version['id'], 'to-lifecycle-environment-id': lce['id']}
            )
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        promoted_lce_names_set = _get_content_view_version_lce_names_set(
            content_view['id'], content_view_version['id']
        )
        assert {
            ENVIRONMENT,
            lce_dev['name'],
            lce_qe['name'],
            lce_stage['name'],
            lce_prod['name'],
        } == promoted_lce_names_set
        # remove from all promoted lifecycle environments
        for lce_name in promoted_lce_names_set:
            ContentView.remove_from_environment(
                {
                    'id': content_view['id'],
                    'organization-id': module_org.id,
                    'lifecycle-environment': lce_name,
                }
            )
        # ensure content view in content views list
        content_views = ContentView.list({'organization-id': module_org.id})
        assert content_view['name'] in [cv['name'] for cv in content_views]
        # delete the content view
        ContentView.delete({'id': content_view['id']})
        # ensure the content view is not in content views list
        content_views = ContentView.list({'organization-id': module_org.id})
        assert content_view['name'] not in [cv['name'] for cv in content_views]

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_remove_cv_version_from_env_with_host_registered(self):
        """Remove promoted content view version from environment that is used
        in association of an Activation key and content-host registration.

        :id: 001a2b76-a87b-4c11-8837-f5fe3c04a075

        :Steps:

            1. Create a content view cv1
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
               -> QE
            5. Create an Activation key with the QE environment
            6. Register a content-host using the Activation key
            7. Remove the content view cv1 version from QE environment.
               Note - prior removing replace the current QE environment of cv1
               by DEV and content view cv1 for Content-host and for Activation
               key.
            8. Refresh content-host subscription

        :expectedresults:

            1. Activation key exists
            2. Content-host exists
            3. QE environment of cv1 was replaced by DEV environment of cv1 in
               activation key
            4. QE environment of cv1 was replaced by DEV environment of cv1 in
               content-host
            5. At content-host some package from cv1 is installable

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_delete_cv_multi_env_promoted_with_host_registered(self):
        """Delete published content view with version promoted to multiple
         environments, with one of the environments used in association of an
         Activation key and content-host registration.

        :id: 82442d23-45b5-4d39-b867-c5d46bbcbbf9

        :Steps:

            1. Create two content view cv1 and cv2
            2. Add a yum repo and a puppet module to both content views
            3. Publish the content views
            4. Promote the content views to multiple environment Library -> DEV
               -> QE
            5. Create an Activation key with the QE environment and cv1
            6. Register a content-host using the Activation key
            7. Delete the content view cv1.
               Note - prior deleting replace the current QE environment of cv1
               by DEV and content view cv2 for Content-host and for Activation
               key.
            8. Refresh content-host subscription

        :expectedresults:

            1. The content view cv1 doesn't exist
            2. Activation key exists
            3. Content-host exists
            4. QE environment of cv1 was replaced by DEV environment of cv2 in
               activation key
            5. QE environment of cv1 was replaced by DEV environment of cv2 in
               content-host
            6. At content-host some package from cv2 is installable

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    @pytest.mark.libvirt_content_host
    @pytest.mark.upgrade
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_cv_version_from_multi_env_capsule_scenario(self, module_org):
        """Remove promoted content view version from multiple environment,
        with satellite setup to use capsule

        :id: 3725fef6-73a4-4dcb-a306-70e6ba826a3d

        :Steps:

            1. Create a content view
            2. Setup satellite to use a capsule and to sync all lifecycle
               environments
            3. Add a yum repo, puppet module and a docker repo to the content
               view
            4. Publish the content view
            5. Promote the content view to multiple environment Library -> DEV
               -> QE -> PROD
            6. Make sure the capsule is updated (content synchronization may be
               applied)
            7. Disconnect the capsule
            8. Remove the content view version from Library and DEV
               environments and assert successful completion
            9. Bring the capsule back online and assert that the task is
               completed in capsule
            10. Make sure the capsule is updated (content synchronization may
                be applied)

        :expectedresults: content view version in capsule is removed from
            Library and DEV and exists only in QE and PROD

        :CaseAutomation: Automated

        :CaseLevel: System

        :CaseImportance: High
        """
        # Note: This test case requires complete external capsule
        #  configuration.
        dev_env = make_lifecycle_environment({'organization-id': module_org.id})
        qe_env = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': dev_env['name']}
        )
        prod_env = make_lifecycle_environment(
            {'organization-id': module_org.id, 'prior': qe_env['name']}
        )
        with CapsuleVirtualMachine(organization_ids=[module_org.id]) as capsule_vm:
            capsule = Capsule().info({'name': capsule_vm.hostname})
            # Add all environments to capsule
            environments = {ENVIRONMENT, dev_env['name'], qe_env['name'], prod_env['name']}
            for env_name in environments:
                Capsule.content_add_lifecycle_environment(
                    {
                        'id': capsule['id'],
                        'organization-id': module_org.id,
                        'environment': env_name,
                    }
                )
            capsule_environments = Capsule.content_lifecycle_environments(
                {'id': capsule['id'], 'organization-id': module_org.id}
            )
            capsule_environments_names = {env['name'] for env in capsule_environments}
            assert environments == capsule_environments_names
            # Setup a yum repo
            custom_yum_product = make_product({'organization-id': module_org.id})
            custom_yum_repo = make_repository(
                {
                    'content-type': 'yum',
                    'product-id': custom_yum_product['id'],
                    'url': FAKE_1_YUM_REPO,
                }
            )
            Repository.synchronize({'id': custom_yum_repo['id']})
            # Setup a puppet repo
            puppet_product = make_product({'organization-id': module_org.id})
            puppet_repository = make_repository(
                {
                    'content-type': 'puppet',
                    'product-id': puppet_product['id'],
                    'url': FAKE_0_PUPPET_REPO,
                }
            )
            Repository.synchronize({'id': puppet_repository['id']})
            puppet_modules = PuppetModule.list(
                {'repository-id': puppet_repository['id'], 'per-page': False}
            )
            assert len(puppet_modules) > 0
            puppet_module = puppet_modules[0]
            # Setup a docker repo
            docker_product = make_product({'organization-id': module_org.id})
            docker_repository = make_repository(
                {
                    'content-type': 'docker',
                    'docker-upstream-name': 'busybox',
                    'name': gen_string('alpha', 20),
                    'product-id': docker_product['id'],
                    'url': CONTAINER_REGISTRY_HUB,
                }
            )
            Repository.synchronize({'id': docker_repository['id']})
            content_view = make_content_view({'organization-id': module_org.id})
            # Associate the yum repository to content view
            ContentView.add_repository(
                {
                    'id': content_view['id'],
                    'organization-id': module_org.id,
                    'repository-id': custom_yum_repo['id'],
                }
            )
            # Associate the puppet module to content view
            ContentView.puppet_module_add(
                {'content-view-id': content_view['id'], 'uuid': puppet_module['uuid']}
            )
            # Associate the docker repository to content view
            ContentView.add_repository(
                {'id': content_view['id'], 'repository-id': docker_repository['id']}
            )
            # Publish the content view
            ContentView.publish({'id': content_view['id']})
            content_view_version = ContentView.info({'id': content_view['id']})['versions'][-1]
            # Promote the content view to DEV, QE, PROD
            for env in [dev_env, qe_env, prod_env]:
                ContentView.version_promote(
                    {
                        'id': content_view_version['id'],
                        'organization-id': module_org.id,
                        'to-lifecycle-environment-id': env['id'],
                    }
                )
            # Synchronize the capsule content
            Capsule.content_synchronize({'id': capsule['id'], 'organization-id': module_org.id})
            capsule_content_info = Capsule.content_info(
                {'id': capsule['id'], 'organization-id': module_org.id}
            )
            # Ensure that all environments exists in capsule content
            capsule_content_info_lces = capsule_content_info['lifecycle-environments']
            capsule_content_lce_names = {lce['name'] for lce in capsule_content_info_lces.values()}
            assert environments == capsule_content_lce_names
            # Ensure first that the content view exit in all capsule
            # environments
            for capsule_content_info_lce in capsule_content_info_lces.values():
                assert 'content-views' in capsule_content_info_lce
                # Retrieve the content views info of this lce
                capsule_content_info_lce_cvs = list(
                    capsule_content_info_lce['content-views'].values()
                )
                # Get the content views names of this lce
                capsule_content_info_lce_cvs_names = [
                    cv['name']['name'] for cv in capsule_content_info_lce_cvs
                ]
                cv_count = 1
                if capsule_content_info_lce['name'] == ENVIRONMENT:
                    # There is a Default Organization View in addition
                    cv_count = 2
                assert len(capsule_content_info_lce_cvs) == cv_count
                assert content_view['name'] in capsule_content_info_lce_cvs_names
            # Suspend the capsule with ensure True to ping the virtual machine
            suspended = capsule_vm.suspend(ensure=True)
            assert suspended
            # Remove the content view version from Library and DEV environments
            for lce_name in [ENVIRONMENT, dev_env['name']]:
                ContentView.remove_from_environment(
                    {
                        'id': content_view['id'],
                        'organization-id': module_org.id,
                        'lifecycle-environment': lce_name,
                    }
                )
            # Assert that the content view version does not exit in Library and
            # DEV and exist only in QE and PROD
            environments_with_cv = {qe_env['name'], prod_env['name']}
            assert environments_with_cv == _get_content_view_version_lce_names_set(
                content_view['id'], content_view_version['id']
            )
            # Resume the capsule with ensure True to ping the virtual machine
            resumed = capsule_vm.resume(ensure=True)
            assert resumed
            # Assert that in capsule content the content view version
            # does not exit in Library and DEV and exist only in QE and PROD
            capsule_content_info = Capsule.content_info(
                {'id': capsule['id'], 'organization-id': module_org.id}
            )
            capsule_content_info_lces = capsule_content_info['lifecycle-environments']
            for capsule_content_info_lce in capsule_content_info_lces.values():
                # retrieve the content views info of this lce
                capsule_content_info_lce_cvs = capsule_content_info_lce.get(
                    'content-views', {}
                ).values()
                # get the content views names of this lce
                capsule_content_info_lce_cvs_names = [
                    cv['name']['name'] for cv in capsule_content_info_lce_cvs
                ]
                if capsule_content_info_lce['name'] in environments_with_cv:
                    assert content_view['name'] in capsule_content_info_lce_cvs_names
                else:
                    assert content_view['name'] not in capsule_content_info_lce_cvs_names

    @pytest.mark.tier2
    def test_negative_user_with_no_create_view_cv_permissions(self, module_org):
        """Unauthorized users are not able to create/view content views

        :id: 17617893-27c2-4cb2-a2ed-47378ef90e7a

        :setup: Create a user without the Content View create/view permissions

        :expectedresults: User with no content view create/view permissions
            cannot create or view the content view

        :CaseImportance: Critical
        """
        password = gen_alphanumeric()
        no_rights_user = make_user({'password': password})
        no_rights_user['password'] = password
        org_id = make_org(cached=True)['id']
        for name in generate_strings_list(exclude_types=['cjk']):
            # test that user can't create
            with pytest.raises(CLIReturnCodeError):
                ContentView.with_user(no_rights_user['login'], no_rights_user['password']).create(
                    {'name': name, 'organization-id': org_id}
                )
            # test that user can't read
            con_view = make_content_view({'name': name, 'organization-id': org_id})
            with pytest.raises(CLIReturnCodeError):
                ContentView.with_user(no_rights_user['login'], no_rights_user['password']).info(
                    {'id': con_view['id']}
                )

    @pytest.mark.tier2
    def test_negative_user_with_read_only_cv_permission(self, module_org):
        """Read-only user is able to view content view

        :id: 588f57b5-9855-4c14-80d0-64b617c6b6dc

        :setup: create a user with the Content View read-only role

        :expectedresults: User with read-only role for content view can view
            the content view but not Create / Modify / Promote / Publish /
            create product / create host collection / create activation key

        :BZ: 1922134

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': module_org.id})
        environment = make_lifecycle_environment({'organization-id': module_org.id})
        password = gen_string('alphanumeric')
        user = make_user({'password': password})
        role = make_role()
        make_filter(
            {
                'organization-ids': module_org.id,
                'permissions': 'view_content_views',
                'role-id': role['id'],
                'override': 1,
            }
        )
        User.add_role({'id': user['id'], 'role-id': role['id']})
        ContentView.with_user(user['login'], password).info({'id': cv['id']})
        # Verify read-only user can't either edit CV
        with pytest.raises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).update(
                {'id': cv['id'], 'new-name': gen_string('alphanumeric')}
            )
        # or create a new one
        with pytest.raises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).create(
                {'name': gen_string('alphanumeric'), 'organization-id': module_org.id}
            )
        # or publish
        with pytest.raises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).publish({'id': cv['id']})
        ContentView.publish({'id': cv['id']})
        cvv = ContentView.info({'id': cv['id']})['versions'][-1]
        # or promote
        with pytest.raises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).version_promote(
                {
                    'id': cvv['id'],
                    'organization-id': module_org.id,
                    'to-lifecycle-environment-id': environment['id'],
                }
            )
        # or create a product
        with pytest.raises(CLIReturnCodeError):
            Product.with_user(user['login'], password).create(
                {'name': gen_string('alpha'), 'organization-id': module_org.id}
            )
        # cannot create activation key
        with pytest.raises(CLIReturnCodeError):
            ActivationKey.with_user(user['login'], password).create(
                {'name': gen_string('alpha'), 'organization-id': module_org.id}
            )
        # cannot create host collection
        with pytest.raises(CLIReturnCodeError):
            HostCollection.with_user(user['login'], password).create(
                {'organization-id': module_org.id}
            )

    @pytest.mark.tier2
    def test_positive_user_with_all_cv_permissions(self, module_org):
        """A user with all content view permissions is able to create,
        read, modify, promote, publish content views

        :id: ac40e9bb-9f1a-48d1-a0fe-9ac2be0f33f4

        :setup: create a user with all content view permissions

        :expectedresults: User is able to perform create, read, modify,
            promote, publish content view

        :BZ: 1464414

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': module_org.id})
        environment = make_lifecycle_environment({'organization-id': module_org.id})
        password = gen_string('alphanumeric')
        user = make_user({'password': password, 'organization-ids': module_org.id})
        role = make_role({'organization-ids': module_org.id})
        # note: the filters inherit role organizations
        make_filter({'permissions': PERMISSIONS['Katello::ContentView'], 'role-id': role['id']})
        make_filter({'permissions': PERMISSIONS['Katello::KTEnvironment'], 'role-id': role['id']})
        User.add_role({'id': user['id'], 'role-id': role['id']})
        # Make sure user is not admin and has only expected roles assigned
        user = User.info({'id': user['id']})
        assert user['admin'] == 'no'
        assert set(user['roles']) == {role['name']}
        # Verify user can either edit CV
        ContentView.with_user(user['login'], password).info({'id': cv['id']})
        new_name = gen_string('alphanumeric')
        ContentView.with_user(user['login'], password).update(
            {'id': cv['id'], 'new-name': new_name}
        )
        cv = ContentView.info({'id': cv['id']})
        assert cv['name'] == new_name
        # or create a new one
        new_cv_name = gen_string('alphanumeric')
        new_cv = ContentView.with_user(user['login'], password).create(
            {'name': new_cv_name, 'organization-id': module_org.id}
        )
        assert new_cv['name'] == new_cv_name
        # or publish
        ContentView.with_user(user['login'], password).publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1
        # or promote
        ContentView.with_user(user['login'], password).version_promote(
            {
                'id': cv['versions'][-1]['id'],
                'organization-id': module_org.id,
                'to-lifecycle-environment-id': environment['id'],
            }
        )
        cv = ContentView.info({'id': cv['id']})
        assert environment['id'] in [env['id'] for env in cv['lifecycle-environments']]

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_inc_update_no_lce(self, module_org, module_product):
        """Publish incremental update without providing lifecycle environment
        for a content view version not promoted to any lifecycle environment

        :BZ: 1322917

        :id: 34bdd55f-f9b5-4d4e-bd35-acd0aae3380d

        :customerscenario: true

        :expectedresults: Incremental update went successfully

        :CaseImportance: Medium

        :CaseLevel: Integration
        """
        repo_name = gen_string('alphanumeric')
        repo_url = create_repo(repo_name, FAKE_0_INC_UPD_URL, [FAKE_0_INC_UPD_OLD_PACKAGE])
        result = repo_add_updateinfo(
            repo_name, f'{FAKE_0_INC_UPD_URL}{FAKE_0_INC_UPD_OLD_UPDATEFILE}'
        )
        assert result.return_code == 0
        repo = make_repository({'product-id': module_product.id, 'url': repo_url})
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view(
            {'organization-id': module_org.id, 'repository-ids': repo['id']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1
        cvv = content_view['versions'][0]
        create_repo(repo_name, FAKE_0_INC_UPD_URL, [FAKE_0_INC_UPD_NEW_PACKAGE], wipe_repodata=True)
        result = repo_add_updateinfo(
            repo_name, f'{FAKE_0_INC_UPD_URL}{FAKE_0_INC_UPD_NEW_UPDATEFILE}'
        )
        assert result.return_code == 0
        Repository.synchronize({'id': repo['id']})
        result = ContentView.version_incremental_update(
            {'content-view-version-id': cvv['id'], 'errata-ids': FAKE_0_INC_UPD_ERRATA}
        )
        # Inc update output format is pretty weird - list of dicts where each
        # key's value is actual line from stdout
        result = [line.strip() for line_dict in result for line in line_dict.values()]
        assert FAKE_0_INC_UPD_ERRATA in [line.strip() for line in result]
        assert FAKE_0_INC_UPD_NEW_PACKAGE.rstrip('.rpm') in [line.strip() for line in result]
        content_view = ContentView.info({'id': content_view['id']})
        assert '1.1' in [cvv_['version'] for cvv_ in content_view['versions']]

    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_incremental_update_propagate_composite(self, module_org, module_product):
        """Incrementally update a CVV in composite CV with
        `propagate_all_composites` flag set

        :BZ: 1288148

        :id: 97f7c34d-0b89-49ca-ae2a-65a4552789b8

        :customerscenario: true

        :Steps:

            1. Create and publish CV with some content
            2. Create composite CV, add previously created CV inside it
            3. Publish composite CV
            4. Create a puppet repository and upload a puppet module into it
            5. Incrementally update the CVV with the puppet module with
               `propagate_all_composites` flag set to `True`

        :expectedresults:

            1. The incremental update succeeds with no errors
            2. New incremental CVV contains new puppet module
            3. New incremental composite CVV contains new puppet module

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        yum_repo = make_repository({'product-id': module_product.id})
        Repository.synchronize({'id': yum_repo['id']})
        content_view = make_content_view(
            {'organization-id': module_org.id, 'repository-ids': yum_repo['id']}
        )
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1
        cvv = ContentView.version_info({'id': content_view['versions'][0]['id']})
        assert len(cvv['puppet-modules']) == 0
        comp_content_view = make_content_view(
            {'component-ids': cvv['id'], 'composite': True, 'organization-id': module_org.id}
        )
        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert len(comp_content_view['versions']) == 1
        comp_cvv = ContentView.version_info({'id': comp_content_view['versions'][0]['id']})
        assert len(comp_cvv['puppet-modules']) == 0
        puppet_repository = make_repository(
            {'content-type': 'puppet', 'product-id': module_product.id, 'url': CUSTOM_PUPPET_REPO}
        )
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_module = PuppetModule.list(
            {
                'organization-id': module_org.id,
                'product-id': module_product.id,
                'repository-id': puppet_repository['id'],
            }
        )[0]
        ContentView.version_incremental_update(
            {
                'content-view-version-id': cvv['id'],
                'propagate-all-composites': 'true',
                'puppet-module-ids': puppet_module['id'],
            }
        )
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 2
        cvvs = [
            ContentView.version_info({'id': version['id']}, output_format='json')
            for version in content_view['versions']
            if version['version'] == '1.1'
        ]
        assert len(cvvs) > 0
        cvv = cvvs[0]
        assert len(cvv['puppet-modules']) == 1
        assert list(cvv['puppet-modules'].values())[0]['id'] == puppet_module['id']
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert len(comp_content_view['versions']) == 2
        comp_cvv = [
            ContentView.version_info({'id': comp_version['id']}, output_format='json')
            for comp_version in comp_content_view['versions']
            if comp_version['version'] == '1.1'
        ]
        assert len(comp_cvv) > 0
        comp_cvvs = comp_cvv[0]
        assert len(comp_cvvs['puppet-modules']) == 1
        assert list(comp_cvvs['puppet-modules'].values())[0]['id'] == puppet_module['id']


@pytest.mark.skip_if_open("BZ:1625783")
class TestOstreeContentView:
    """Tests for custom ostree contents in content views."""

    @pytest.mark.tier3
    def test_positive_add_custom_ostree_content(self, module_org, all_content_type):
        """Associate custom ostree content in a view

        :id: 6e89094d-ffd3-4dc6-b925-f76531c56c20

        :expectedresults: Custom ostree content assigned and present in content
            view

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Create CV
        cv = make_content_view({'organization-id': module_org.id})
        product = all_content_type['ostree_repo']['product']['name']
        ostree_repo = all_content_type['ostree_repo']['name']
        # Associate repo to CV with names.
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_org.name,
                'product': product,
                'repository': ostree_repo,
            }
        )
        cv = ContentView.info({'id': cv['id']})
        assert cv['ostree-repositories'][0]['name'] == ostree_repo

    @pytest.mark.tier3
    def test_positive_publish_custom_ostree(self, module_org, all_content_type):
        """Publish a content view with custom ostree contents

        :id: ec66f1d3-9750-4dfc-a189-f3b0fd6af3e8

        :expectedresults: Content-view with Custom ostree published
            successfully

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV with names.
        product = all_content_type['ostree_repo']['product']['name']
        ostree_repo = all_content_type['ostree_repo']['name']
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_org.name,
                'product': product,
                'repository': ostree_repo,
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1

    @pytest.mark.tier3
    def test_positive_promote_custom_ostree(self, module_org, all_content_type):
        """Promote a content view with custom ostree contents

        :id: 5eb7b9e6-8757-4152-9114-42a5eb021bbc

        :expectedresults: Content-view with custom ostree contents promoted
            successfully

        CaseImportance: Critical

        :CaseLevel: Integration
        """
        cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV with names.
        product = all_content_type['ostree_repo']['product']['name']
        ostree_repo = all_content_type['ostree_repo']['name']
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_org.name,
                'product': product,
                'repository': ostree_repo,
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        lc_env = make_lifecycle_environment({'organization-id': module_org.id})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': lc_env['id']}
        )
        cv = ContentView.info({'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        assert environment in cv['lifecycle-environments']

    @pytest.mark.tier3
    def test_positive_publish_promote_with_custom_ostree_and_other(
        self, module_org, all_content_type
    ):
        """Publish & Promote a content view with custom ostree and other contents

        :id: 35668fa6-0a24-43ae-b562-26c5ac77e94d

        :expectedresults: Content-view with custom ostree and other contents
            promoted successfully

        :CaseLevel: Integration

        :CaseImportance: High
        """
        cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV with names.
        product = all_content_type['ostree_repo']['product']['name']
        ostree_repo = all_content_type['ostree_repo']['name']
        yum_repo = all_content_type['yum_repo']['name']
        puppet_repo = all_content_type['puppet_repo']
        docker_repo = all_content_type['docker_repo']['name']
        repos = [ostree_repo, yum_repo, docker_repo]
        for repo in repos:
            ContentView.add_repository(
                {
                    'name': cv['name'],
                    'organization': module_org.name,
                    'product': product,
                    'repository': repo,
                }
            )
        cv = ContentView.info({'id': cv['id']})
        assert cv['ostree-repositories'][0]['name'] == ostree_repo
        assert cv['yum-repositories'][0]['name'] == yum_repo
        assert cv['container-image-repositories'][0]['name'] == docker_repo
        # Fetch puppet module
        puppet_result = PuppetModule.list({'repository-id': puppet_repo['id'], 'per-page': False})
        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add(
                {'content-view-id': cv['id'], 'uuid': puppet_module['uuid']}
            )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        lc_env = make_lifecycle_environment({'organization-id': module_org.id})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': lc_env['id']}
        )
        cv = ContentView.info({'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        assert environment in cv['lifecycle-environments']


@pytest.mark.skip_if_open("BZ:1625783")
@pytest.mark.run_in_one_thread
class TestContentViewRedHatOstreeContent:
    """Tests for publishing and promoting cv with RH ostree contents."""

    @pytest.mark.tier3
    def test_positive_add_rh_ostree_content(self, module_manifest_org, atomic_repo):
        """Associate RH atomic ostree content in a view

        :id: 5e9dfb32-9cc7-4257-ab6b-f439fb9db2bd

        :expectedresults: RH atomic ostree content assigned and present in
            content view

        :CaseImportance: Medium

        :CaseLevel: Integration
        """
        cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV with names.
        repo = atomic_repo['name']
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_manifest_org.name,
                'product': PRDS['rhah'],
                'repository': repo,
            }
        )
        cv = ContentView.info({'id': cv['id']})
        assert cv['ostree-repositories'][0]['name'] == repo

    @pytest.mark.tier3
    def test_positive_publish_RH_ostree(self, module_manifest_org, atomic_repo):
        """Publish a content view with RH ostree contents

        :id: 4ac5c7d1-9ab2-4a65-b4b8-1582b001125f

        :expectedresults: Content-view with RH ostree contents published
            successfully

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV with names.
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_manifest_org.name,
                'product': PRDS['rhah'],
                'repository': atomic_repo['name'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        assert len(cv['versions']) == 1

    @pytest.mark.tier3
    def test_positive_promote_RH_ostree(self, module_manifest_org, atomic_repo):
        """Promote a content view with RH ostree contents

        :id: 71986705-fe45-4e0f-af0b-288c9c7ce61b

        :expectedresults: Content-view with RH ostree contents promoted
            successfully

        :CaseLevel: Integration

        :CaseImportance: High
        """
        cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV with names.
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_manifest_org.name,
                'product': PRDS['rhah'],
                'repository': atomic_repo['name'],
            }
        )
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        lc_env = make_lifecycle_environment({'organization-id': module_manifest_org.id})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': lc_env['id']}
        )
        cv = ContentView.info({'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        assert environment in cv['lifecycle-environments']

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_publish_promote_with_RH_ostree_and_other(
        self, module_manifest_org, atomic_repo
    ):
        """Publish & Promote a content view with RH ostree and other contents

        :id: 87c8ddb1-da32-4103-810d-8e5e28fa888f

        :expectedresults: Content-view with RH ostree and other contents
            promoted successfully

        :CaseLevel: Integration

        :CaseImportance: High
        """
        RepositorySet.enable(
            {
                'name': REPOSET['rhst7'],
                'organization-id': module_manifest_org.id,
                'product': PRDS['rhel'],
                'releasever': None,
                'basearch': 'x86_64',
            }
        )
        rpm_repo_name = REPOS['rhst7']['name']
        Repository.synchronize(
            {
                'name': rpm_repo_name,
                'organization-id': module_manifest_org.id,
                'product': PRDS['rhel'],
            }
        )
        cv = make_content_view({'organization-id': module_manifest_org.id})
        # Associate repo to CV with names.
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_manifest_org.name,
                'product': PRDS['rhah'],
                'repository': atomic_repo['name'],
            }
        )
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization': module_manifest_org.name,
                'product': PRDS['rhel'],
                'repository': rpm_repo_name,
            }
        )
        cv = ContentView.info({'id': cv['id']})
        assert cv['ostree-repositories'][0]['name'] == atomic_repo['name']
        assert cv['yum-repositories'][0]['name'] == rpm_repo_name
        ContentView.publish({'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        lc_env = make_lifecycle_environment({'organization-id': module_manifest_org.id})
        # Promote the Published version of CV to the next env
        ContentView.version_promote(
            {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': lc_env['id']}
        )
        cv = ContentView.info({'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        assert environment in cv['lifecycle-environments']


class TestContentViewFileRepo:
    """Specific tests for Content Views with File Repositories containing
    arbitrary files
    """

    def make_file_repository_upload_contents(self, module_org, module_product, options=None):
        """Makes a new File repository, Upload File/Multiple Files
        and asserts its success"""

        if options is None:
            options = {'product-id': module_product.id, 'content-type': 'file'}
        if not options.get('content-type'):
            raise CLIFactoryError('Please provide a valid Content Type.')
        new_repo = make_repository(options)
        remote_path = f"/tmp/{RPM_TO_UPLOAD}"
        if 'multi_upload' not in options or not options['multi_upload']:
            ssh.upload_file(local_file=get_data_file(RPM_TO_UPLOAD), remote_file=remote_path)
        else:
            remote_path = "/tmp/{}/".format(gen_string('alpha'))
            ssh.upload_files(local_dir=os.getcwd() + "/../data/", remote_dir=remote_path)

        Repository.upload_content(
            {
                'name': new_repo['name'],
                'organization-id': module_org.id,
                'path': remote_path,
                'product-id': new_repo['product']['id'],
            }
        )
        new_repo = Repository.info({'id': new_repo['id']})
        assert int(new_repo['content-counts']['files']) > 0
        return new_repo

    @pytest.mark.skip_if_open("BZ:1610309")
    @pytest.mark.tier3
    def test_positive_arbitrary_file_repo_addition(self, module_org, module_product):
        """Check a File Repository with Arbitrary File can be added to a
        Content View

        :id: 8c217d44-6f66-4b41-b77d-f5179a9e3b4e

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)

        :Steps:
            1. Add the FR to the CV

        :expectedresults: Check FR is added to CV

        :CaseAutomation: Automated

        :CaseLevel: Integration

        :CaseImportance: High

        :BZ: 1610309, 1908465
        """
        repo = self.make_file_repository_upload_contents(module_org, module_product)
        cv = make_content_view({'organization-id': module_org.id})
        # Associate repo to CV with names.
        ContentView.add_repository(
            {
                'name': cv['name'],
                'organization-id': module_org.id,
                'product-id': module_product.id,
                'repository': repo['name'],
            }
        )
        cv = ContentView.info({'id': cv['id']})
        assert cv['file-repositories'][0]['name'] == repo['name']

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_arbitrary_file_repo_removal(self):
        """Check a File Repository with Arbitrary File can be removed from a
        Content View

        :id: 156e30ab-bfae-4120-9353-d3b567801106

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV

        :Steps:
            1. Remove the FR from the CV

        :expectedresults: Check FR is removed from CV

        :CaseAutomation: NotAutomated

        :CaseLevel: Integration
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_arbitrary_file_sync_over_capsule(self):
        """Check a File Repository with Arbitrary File can be added to a
        Content View is synced throughout capsules

        :id: ffa59550-464c-40dc-9bd2-444331f73708

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV
            5. Create a Capsule
            6. Connect the Capsule with Satellite/Foreman host

        :Steps:
            1. Start synchronization

        :expectedresults: Check CV with FR is synced over Capsule

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.tier3
    def test_positive_arbitrary_file_repo_promotion(self, module_org, module_product):
        """Check arbitrary files availability for Content view version after
        content-view promotion.

        :id: 3c728b9e-27e4-4afc-90b0-8c728e634d6f

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV
            5. Create an Environment

        :Steps:
            1. Promote the CV to the Environment

        :expectedresults: Check arbitrary files from FR is available on
            content view version environment

        :CaseAutomation: Automated

        :CaseLevel: Integration

        :CaseImportance: High
        """

        cv = make_content_view({'organization-id': module_org.id})
        repo = self.make_file_repository_upload_contents(module_product, module_product)
        ContentView.add_repository(
            {'id': cv['id'], 'repository-id': repo['id'], 'organization-id': module_org.id}
        )
        env = make_lifecycle_environment({'organization-id': module_org.id})
        ContentView.publish({'id': cv['id']})
        content_view_info = ContentView.version_info({'content-view-id': cv['id'], 'version': 1})
        ContentView.version_promote(
            {'id': content_view_info['id'], 'to-lifecycle-environment-id': env['id']}
        )
        expected_repo = ContentView.version_info(
            {
                'content-view-id': cv['id'],
                'lifecycle-environment': env['name'],
                'version': 1,
                'organization-id': module_org.id,
            }
        )['repositories'][0]['name']

        assert repo['name'] in expected_repo

    @pytest.mark.tier3
    def test_positive_katello_repo_rpms_max_int(self):
        """Checking that datatype for katello_repository_rpms table is a
        bigint for id for a closed loop bz.

        :id: e83b3a00-c851-4970-a70d-abd26b2d3593

        :expectedresults: id datatype is bigint

        :CaseImportance: Medium

        :BZ: 1793701
        """
        result = ssh.command('sudo -u postgres psql -d foreman -c "\\d katello_repository_rpms"')
        assert "id|bigint" in result.stdout[3].replace(" ", "")
