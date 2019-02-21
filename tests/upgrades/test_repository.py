"""Test for Repository related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fabric.api import run
from nailgun import entities
from robottelo.test import APITestCase
from robottelo.api.utils import create_sync_custom_repo
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict, get_entity_data


class Scenario_repository_upstream_authorization_check(APITestCase):
    """ This test scenario is to verify the upstream username in post-upgrade for a custom
    repository which does have a upstream username but not password set on it in pre-upgrade.

    Test Steps:

        1. Before Satellite upgrade, Create a custom repository and sync it.
        2. Set the upstream username on same repository using foreman-rake.
        3. Upgrade Satellite.
        4. Check if the upstream username value is removed for same repository.
    """

    @classmethod
    def setUpClass(cls):
        cls.upstream_username = 'rTtest123'

    @pre_upgrade
    def test_pre_repository_scenario_upstream_authorization(self):
        """ Create a custom repository and set the upstream username on it.

        :id: preupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Create a custom repository and sync it.
            2. Set the upstream username on same repository using foreman-rake.

        :expectedresults:
            1. Upstream username should be set on repository.

        :BZ: 1641785
        """

        org = entities.Organization().create()
        custom_repo = create_sync_custom_repo(org_id=org.id)
        rake_repo = 'repo = Katello::Repository.find_by_id({0})'.format(custom_repo)
        rake_username = '; repo.upstream_username = "{0}"'.format(self.upstream_username)
        rake_repo_save = '; repo.save!(validate: false)'
        result = run("echo '{0}{1}{2}'|foreman-rake console".format(rake_repo, rake_username,
                                                                    rake_repo_save))
        self.assertIn('true', result)

        global_dict = {
            self.__class__.__name__: {'repo_id': custom_repo}
        }
        create_dict(global_dict)

    @post_upgrade
    def test_post_repository_scenario_upstream_authorization(self):
        """ Verify upstream username for pre-upgrade created repository.

        :id: postupgrade-11c5ceee-bfe0-4ce9-8f7b-67a835baf522

        :steps:
            1. Verify upstream username for pre-upgrade created repository using
            foreman-rake.

        :expectedresults:
            1. upstream username should not exists on same repository.

        :BZ: 1641785
        """

        repo_id = get_entity_data(self.__class__.__name__)['repo_id']
        rake_repo = 'repo = Katello::RootRepository.find_by_id({0})'.format(repo_id)
        rake_username = '; repo.upstream_username'
        result = run("echo '{0}{1}'|foreman-rake console".format(rake_repo, rake_username))
        self.assertNotIn(self.upstream_username, result)
