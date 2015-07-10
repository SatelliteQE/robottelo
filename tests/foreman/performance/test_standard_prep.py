"""Test class for Environment Preparation after a fresh installation"""
from robottelo.common import conf, ssh
from robottelo.cli.org import Org
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription

from robottelo.test import TestCase


class StandardPrepTestCase(TestCase):
    """Standard process of preparation after fresh install Sattellite 6.

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
        cls.savepoint = conf.properties[
            'performance.test.savepoint1_fresh_install']
        cls.manifest_location = conf.properties[
            'performance.test.manifest.location']

        # parameters for uploading manifests
        cls.manifest_file = conf.properties['performance.test.manifest.file']
        cls.org_id = conf.properties['performance.test.organization.id']

        # parameters for changing cdn address
        cls.target_url = conf.properties['performance.test.cdn.address']

        # parameters for enabling repositories
        cls.pid = conf.properties['performance.test.pid']

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

    def _restore_from_savepoint(self, savepoint):
        """Restore from a given savepoint"""
        self.logger.info('Reset db from /home/backup/{}'.format(savepoint))
        ssh.command('./reset-db.sh /home/backup/{}'.format(savepoint))

    def _download_manifest(self):
        self.logger.info(
            'Start downloading required manifest: {}'
            .format(self.manifest_location + self.manifest_file))

        result = ssh.command(
            'rm -f {0}; curl {1} -o /root/{0}'
            .format(self.manifest_file,
                    self.manifest_location + self.manifest_file))

        if result.return_code != 0:
            self.logger.error('Fail to download manifest!')
            return
        self.logger.info('Downloading manifest complete.')

    def _upload_manifest(self):
        result = Subscription.upload({
            'file': '/root/{}'.format(self.manifest_file),
            'organization-id': self.org_id
        })

        if result.return_code != 0:
            self.logger.error('Fail to upload manifest!')
            return
        (self.sub_id, self.sub_name) = self._get_subscription_id()
        self.logger.info('Upload successful!')

    def _get_subscription_id(self):
        result = Subscription.list(
            {'organization-id': self.org_id},
            per_page=False
        )

        if result.return_code != 0:
            self.logger.error('Fail to list subscriptions!')
            return
        subscription_id = result.stdout[0]['id']
        subscription_name = result.stdout[0]['name']
        self.logger.info('Subscribe to {0} with subscription id: {1}'
                         .format(subscription_name, subscription_id))
        return (subscription_id, subscription_name)

    def _update_cdn_address(self):
        Org.update({
            'id': self.org_id,
            'redhat-repository-url': self.target_url
        })
        result = Org.info({'id': self.org_id})

        if result.return_code != 0:
            self.logger.error('Fail to update CDN address!')
            return
        self.logger.info(
            'RH CDN URL: {}'
            .format(result.stdout['red-hat-repository-url']))

    def _enable_repositories(self):
        for i, repo in enumerate(self.repository_list):
            repo_id = repo[0]
            basearch = repo[1]
            releasever = repo[2]
            self.logger.info(
                'Enabling product {0}: repository id {1} '
                'with baserach {2} and release {3}'
                .format(i, repo_id, basearch, releasever))

            # Enable repos from Repository Set
            result = RepositorySet.enable({
                'product-id': self.pid,
                'basearch': basearch,
                'releasever': releasever,
                'id': repo_id
            })

        # verify enabled repository list
        result = Repository.list(
            {'organization-id': self.org_id},
            per_page=False
        )

        # repo_list_ids would contain all repositories in the hammer repo list
        repo_list_ids = [repo['id'] for repo in result.stdout]
        self.logger.debug(repo_list_ids)

    def test_standard_prep(self):
        """@Test: add Manifest to Satellite Server

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
