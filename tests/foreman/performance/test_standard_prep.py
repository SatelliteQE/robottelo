"""Test class for Environment Preparation after a fresh installation"""
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.org import Org
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.performance.constants import MANIFEST_FILE_NAME
from robottelo.test import TestCase


class StandardPrepTestCase(TestCase):
    """Standard process of preparation after fresh install Satellite 6.

    Standard Preparation Process:

    1. upload manifest,
    2. change CDN address,
    3. enable repositories,
    4. make savepoint

    """

    @classmethod
    def setUpClass(cls):
        super(StandardPrepTestCase, cls).setUpClass()

        # parameters for standard process test
        # note: may need to change savepoint name
        cls.savepoint = settings.performance.fresh_install_savepoint,

        # parameters for uploading manifests
        cls.manifest_file = settings.fake_manifest.url
        cls.org_id = ''

        # parameters for changing cdn address
        cls.target_url = settings.performance.cdn_address

        # parameters for enabling repositories
        cls.sub_id = ''
        cls.sub_name = ''
        cls.pid = ''

        # [repo-id,$basearch,$releasever]
        cls.repository_list = [
            [168, 'x86_64', '6Server'],
            [2456, 'x86_64', '7Server'],
            [1952, 'x86_64', '6.6'],
            [2455, 'x86_64', '7.1'],
            [166, 'x86_64', '6Server'],
            [2463, 'x86_64', '7Server'],
            [167, 'x86_64', '6Server'],
            [2464, 'x86_64', '7Server'],
            [165, 'x86_64', '6Server'],
            [2462, 'x86_64', '7Server']
        ]

    def setUp(self):
        self.logger.debug('Running test %s/%s',
                          type(self).__name__, self._testMethodName)

        # Restore database to clean state
        self._restore_from_savepoint(self.savepoint)
        # Get organization-id
        self.org_id = self._get_organization_id()

    def _restore_from_savepoint(self, savepoint):
        """Restore from a given savepoint"""
        if savepoint == '':
            self.logger.warning('No savepoint while continuing test!')
            return
        self.logger.info('Reset db from /home/backup/{0}'.format(savepoint))
        ssh.command('./reset-db.sh /home/backup/{0}'.format(savepoint))

    def _download_manifest(self):
        """Utility function to download manifest from given URL"""
        self.logger.info(
            'Start downloading manifest: {0}'.format(MANIFEST_FILE_NAME))

        result = ssh.command(
            'rm -f {0}; curl {1} -o /root/{0}'
            .format(MANIFEST_FILE_NAME, self.manifest_file))

        if result.return_code != 0:
            self.logger.error('Fail to download manifest!')
            raise RuntimeError('Unable to download manifest. Stop!')
        self.logger.info('Downloading manifest complete.')

    def _upload_manifest(self):
        """Utility function to upload manifest"""
        self.logger.debug('org-id is {0}'.format(self.org_id))

        try:
            Subscription.upload({
                'file': '/root/{0}'.format(MANIFEST_FILE_NAME),
                'organization-id': self.org_id,
            })
        except CLIReturnCodeError:
            self.logger.error('Fail to upload manifest!')
            raise RuntimeError('Invalid manifest. Stop!')
        self.logger.info('Upload successful!')

        # after uploading manifest, get all default parameters
        self.pid = self._get_production_id()
        (self.sub_id, self.sub_name) = self._get_subscription_id()
        self.logger.debug('product id is {0}'.format(self.pid))

    def _get_organization_id(self):
        """Get organization id"""
        try:
            result = Org.list(per_page=False)
        except CLIReturnCodeError:
            self.logger.error('Fail to list default organization.')
            raise RuntimeError('Invalid organization id. Stop!')
        return result[0]['id']

    def _get_production_id(self):
        """Get available product id after uploading manifest"""
        try:
            result = Product.list(
                {'organization-id': self.org_id},
                per_page=False
            )
        except CLIReturnCodeError:
            self.logger.error('Fail to list default products.')
            raise RuntimeError('Invalid product id. Stop!')
        for item in result:
            if item['name'] == u'Red Hat Enterprise Linux Server':
                return item['id']

    def _get_subscription_id(self):
        """Utility function to get subscription id after uploading manifest"""
        try:
            result = Subscription.list(
                {'organization-id': self.org_id},
                per_page=False
            )
        except CLIReturnCodeError:
            self.logger.error('Fail to list subscriptions!')
            raise RuntimeError('Invalid subscription id. Stop!')
        if not result:
            self.logger.error('Fail to get subscription id!')
            raise RuntimeError('Manifest has no subscription!')
        subscription_id = result[0]['id']
        subscription_name = result[0]['name']
        self.logger.info(
            'Subscribe to {0} with subscription id: {1}'
            .format(subscription_name, subscription_id)
        )
        return (subscription_id, subscription_name)

    def _update_cdn_address(self):
        """Utility function to update CDN address from given URL"""
        if self.target_url == '':
            raise RuntimeError('Invalid CDN address. Stop!')

        Org.update({
            'id': self.org_id,
            'redhat-repository-url': self.target_url,
        })
        try:
            result = Org.info({'id': self.org_id})
        except CLIReturnCodeError:
            self.logger.error('Fail to update CDN address!')
            return
        self.logger.info(
            'RH CDN URL: {0}'
            .format(result['red-hat-repository-url']))

    def _enable_repositories(self):
        """Utility function to retrieve enabled repositories"""
        for i, repo in enumerate(self.repository_list):
            repo_id = repo[0]
            basearch = repo[1]
            releasever = repo[2]
            self.logger.info(
                'Enabling product {0}: repository id {1} '
                'with baserach {2} and release {3}'
                .format(i, repo_id, basearch, releasever))

            # Enable repos from Repository Set
            RepositorySet.enable({
                'basearch': basearch,
                'id': repo_id,
                'product-id': self.pid,
                'releasever': releasever,
            })

        # verify enabled repository list
        result = Repository.list(
            {'organization-id': self.org_id},
            per_page=False
        )

        # repo_list_ids would contain all repositories in the hammer repo list
        repo_list_ids = [repo['id'] for repo in result]
        self.logger.debug(repo_list_ids)

    def test_standard_prep(self):
        """add Manifest to Satellite Server

        @Steps:

        1. download manifest
        2. upload to subscription
        3. update Red Hat CDN URL
        4. enable repositories
        5. take db snapshot backup

        @Assert: Restoring from database where its status is clean

        """
        self._download_manifest()
        self._upload_manifest()
        self._update_cdn_address()
        self._enable_repositories()
