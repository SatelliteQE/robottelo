"""
Test class for Custom Sync UI
"""

from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.common.helpers import generate_name, valid_names_list
from robottelo.common.constants import DEFAULT_ORG
from tests.ui.commonui import CommonUI


#@ddt
class Sync(CommonUI):
    """
    Implements Custom Sync tests in UI
    """

    #@attr('ui', 'sync', 'implemented')
    #@data(*valid_names_list())
    def test_sync_repos(self):
        """
        @Feature: Content Custom Sync - Positive Create
        @Test: Create Content Custom Sync with minimal input parameters
        @Assert: Whether Sync is successful
        """
        prd_name = generate_name(8, 8)
        repo_name = generate_name(8, 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        provider = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_product(prd_name, description,
                            provider, create_provider=True)
        self.create_repo(repo_name, prd_name, repo_url)
        self.sync_repos(prd_name, [repo_name])
