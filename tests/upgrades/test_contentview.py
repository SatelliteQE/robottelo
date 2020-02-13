"""Test for Content View related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os

from fauxfactory import gen_string
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade

from robottelo import ssh
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.constants import FAKE_1_YUM_REPO
from robottelo.constants import FAKE_2_YUM_REPO
from robottelo.constants import RPM_TO_UPLOAD
from robottelo.helpers import get_data_file
from robottelo.test import CLITestCase


class Scenario_contentview_upgrade(CLITestCase):
    """Test Content-view created before migration gets updated successfully
    post migration.

        Test Steps:

        1. Before Satellite upgrade:
        2. Create a product.
        3. Create custom yum, puppet and file repositories in that product.
        4. Create content-view.
        5. Add puppet module, repositories to content view
        6. Publish content-view
        7. Upgrade satellite.
        8. Remove yum repository which was added to content-view before upgrade.
        9. Create new yum repository and add it to content-view.
        10. Remove puppet module which was added to content-view before upgrade.
        11. Add another puppet module to content-view
        12. Publish content-view
     """

    @classmethod
    def setUpClass(cls):
        cls.cls_name = 'Scenario_contentview_upgrade'
        cls.org_name = 'org_' + cls.cls_name
        cls.product_name = 'product_' + cls.cls_name
        cls.yum_repo1_name = 'yum_repo1_' + cls.cls_name
        cls.yum_repo2_name = 'yum_repo2_' + cls.cls_name
        cls.cv_name = 'cv_' + cls.cls_name
        cls.file_repo_name = 'file_repo_' + cls.cls_name
        cls.puppet_module_name = 'versioned'
        cls.puppet_module_author = 'robottelo'
        cls.puppet_repo_name = 'puppet_repo_' + cls.cls_name

    def setupScenario(self):
        """ Create yum, puppet repositories and synchronize them.
        """
        self.org = make_org({'name': self.org_name})
        self.product = make_product({
            'name': self.product_name, 'organization-id': self.org['id']})
        self.yum_repo1 = make_repository({
            'name': self.yum_repo1_name,
            'product-id': self.product['id'],
            'content-type': 'yum',
            'url': FAKE_1_YUM_REPO})
        Repository.synchronize({'id': self.yum_repo1['id']})
        self.module = {'name': self.puppet_module_name, 'version': '3.3.3'}
        self.puppet_repo = make_repository({
            'name': self.puppet_repo_name,
            'content-type': 'puppet',
            'product-id': self.product['id'],
            'url': CUSTOM_PUPPET_REPO,
        })
        Repository.synchronize({'id': self.puppet_repo['id']})
        self.puppet_module = PuppetModule.list({
            'search': 'name={name} and version={version}'.format(**self.module)})[0]

    def make_file_repository_upload_contents(self, options=None):
        """Makes a new File repository, Upload File/Multiple Files
        and asserts its success.
        """
        if options is None:
            options = {
                'name': self.file_repo_name,
                'product-id': self.product['id'],
                'content-type': 'file'
            }
        if not options.get('content-type'):
            raise CLIFactoryError('Please provide a valid Content Type.')
        file_repo = make_repository(options)
        remote_path = "/tmp/{0}".format(RPM_TO_UPLOAD)
        if 'multi_upload' not in options or not options['multi_upload']:
            ssh.upload_file(
                local_file=get_data_file(RPM_TO_UPLOAD),
                remote_file=remote_path
            )
        else:
            remote_path = "/tmp/{}/".format(gen_string('alpha'))
            ssh.upload_files(local_dir=os.getcwd() + "/../data/",
                             remote_dir=remote_path)

        result = Repository.upload_content({
            'name': file_repo['name'],
            'organization': file_repo['organization'],
            'path': remote_path,
            'product-id': file_repo['product']['id'],
        })
        self.assertIn(
            "Successfully uploaded file '{0}'".format(RPM_TO_UPLOAD),
            result[0]['message'],
        )
        file_repo = Repository.info({'id': file_repo['id']})
        self.assertGreater(int(file_repo['content-counts']['files']), 0)
        return file_repo

    @pre_upgrade
    def test_cv_preupgrade_scenario(self):
        """This is pre-upgrade scenario test to verify if we can create a
         content-view with various repositories.

         :id: a4ebbfa1-106a-4962-9c7c-082833879ae8

         :steps:
           1. Create custom yum, puppet and file repositories.
           2. Create content-view.
           3. Add yum, file repositories and puppet module to content view.
           4. Publish content-view.

         :expectedresults: content-view created with various repositories.
         """
        self.setupScenario()
        file_repo = self.make_file_repository_upload_contents()
        content_view = make_content_view({
            'name': self.cv_name,
            'organization-id': self.org['id'],
            'repository-ids': [
                self.yum_repo1['id'], file_repo['id']]
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(
            content_view['yum-repositories'][0]['name'],
            self.yum_repo1['name'],
            'Repo was not associated to CV',
        )
        ContentView.puppet_module_add({
            'content-view-id': content_view['id'],
            'name': self.puppet_module['name'],
            'author': self.puppet_module['author'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertGreater(len(content_view['puppet-modules']), 0)
        ContentView.publish({'id': content_view['id']})
        cv = ContentView.info({'id': content_view['id']})
        self.assertEqual(len(cv['versions']), 1)

    @post_upgrade(depend_on=test_cv_preupgrade_scenario)
    def test_cv_postupgrade_scenario(self):
        """This is post-upgrade scenario test to verify if we can update
         content-view created in pre-upgrade scenario with various repositories.

         :id: a4ebbfa1-106a-4962-9c7c-082833879ae8

         :steps:
           1. Remove yum repository which was added to content-view before upgrade.
           2. Create new yum repository and add it to content-view.
           3. Remove puppet module which was added to content-view before upgrade.
           4. Add another puppet module to content-view
           5. Publish content-view

         :expectedresults: content-view updated with various repositories.
        """
        product_id = Repository.info({
            'name': self.yum_repo1_name,
            'organization': self.org_name,
            'product': self.product_name
        })['product']['id']
        ContentView.remove_repository({
            'organization': self.org_name,
            'name': self.cv_name,
            'repository': self.yum_repo1_name
        })
        content_view = ContentView.info({'name': self.cv_name,
                                         'organization': self.org_name})
        self.assertNotIn(self.yum_repo1_name,
                         content_view['yum-repositories'])
        yum_repo2 = make_repository({
            'name': self.yum_repo2_name,
            'organization': self.org_name,
            'content-type': 'yum',
            'product-id': product_id,
            'url': FAKE_2_YUM_REPO})
        Repository.synchronize({'id': yum_repo2['id'],
                                'organization': self.org_name})
        ContentView.add_repository({
            'name': self.cv_name,
            'organization': self.org_name,
            'product': self.product_name,
            'repository-id': yum_repo2['id']})
        content_view = ContentView.info({'name': self.cv_name,
                                         'organization': self.org_name})
        self.assertEqual(
            content_view['yum-repositories'][0]['name'],
            self.yum_repo2_name,
            'Repo was not associated to CV',
        )
        ContentView.puppet_module_remove({
            'organization': self.org_name,
            'content-view': self.cv_name,
            'name': self.puppet_module_name,
            'author': self.puppet_module_author,
        })
        content_view = ContentView.info({'name': self.cv_name,
                                         'organization': self.org_name})
        self.assertEqual(len(content_view['puppet-modules']), 0)
        module = {'name': 'versioned', 'version': '2.2.2'}
        puppet_module = PuppetModule.list({
            'search': 'name={name} and version={version}'.format(**module)})[0]
        ContentView.puppet_module_add({
            'organization': self.org_name,
            'content-view': self.cv_name,
            'name': puppet_module['name'],
            'author': puppet_module['author'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertGreater(len(content_view['puppet-modules']), 0)
        ContentView.publish({'name': self.cv_name,
                             'organization': self.org_name})
        content_view = ContentView.info({'name': self.cv_name,
                                         'organization': self.org_name})
        self.assertEqual(len(content_view['versions']), 2)
