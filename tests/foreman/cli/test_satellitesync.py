# -*- encoding: utf-8 -*-
"""Test class for InterSatellite Sync

:Requirement: Satellitesync

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: InterSatelliteSync

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json

from fauxfactory import gen_integer, gen_string
from nailgun import entities
from random import randint

from robottelo import manifests, ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    make_content_view,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.package import Package
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.settings import Settings
from robottelo.cli.subscription import Subscription
from robottelo.constants import (
    CUSTOM_PUPPET_REPO,
    ENVIRONMENT,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    tier4,
    upgrade
)
from robottelo.test import CLITestCase


class ExportDirectoryNotSet(Exception):
    """Raise when export Directory is not set or found"""


@run_in_one_thread
class RepositoryExportTestCase(CLITestCase):
    """Tests for exporting a repository via CLI"""

    export_dir = None
    is_set_up = False
    org = None

    def setUp(self):
        """Create a directory for export, configure permissions and satellite
        settings
        """
        super(RepositoryExportTestCase, self).setUp()

        if not RepositoryExportTestCase.is_set_up:
            RepositoryExportTestCase.export_dir = gen_string('alphanumeric')

            # Create a new 'export' directory on the Satellite system
            result = ssh.command('mkdir /mnt/{0}'.format(self.export_dir))
            self.assertEqual(result.return_code, 0)

            result = ssh.command(
                'chown foreman.foreman /mnt/{0}'.format(self.export_dir))
            self.assertEqual(result.return_code, 0)

            result = ssh.command(
                'ls -Z /mnt/ | grep {0}'.format(self.export_dir))
            self.assertEqual(result.return_code, 0)
            self.assertGreaterEqual(len(result.stdout), 1)
            self.assertIn('unconfined_u:object_r:mnt_t:s0', result.stdout[0])

            # Fix SELinux policy for new directory
            result = ssh.command(
                'semanage fcontext -a -t foreman_var_run_t "/mnt/{0}(/.*)?"'
                .format(self.export_dir)
            )
            self.assertEqual(result.return_code, 0)

            result = ssh.command(
                'restorecon -Rv /mnt/{0}'.format(self.export_dir))
            self.assertEqual(result.return_code, 0)

            # Assert that we have the correct policy
            result = ssh.command(
                'ls -Z /mnt/ | grep {0}'.format(self.export_dir))
            self.assertEqual(result.return_code, 0)
            self.assertGreaterEqual(len(result.stdout), 1)
            self.assertIn(
                'unconfined_u:object_r:foreman_var_run_t:s0', result.stdout[0])

            # Update the 'pulp_export_destination' settings to new directory
            Settings.set({
                'name': 'pulp_export_destination',
                'value': '/mnt/{0}'.format(self.export_dir),
            })
            # Create an organization to reuse in tests
            RepositoryExportTestCase.org = make_org()

            RepositoryExportTestCase.is_set_up = True

    @classmethod
    def tearDownClass(cls):
        """Remove the export directory with all exported repository archives"""
        ssh.command(
            'rm -rf /mnt/{0}'.format(RepositoryExportTestCase.export_dir))
        super(RepositoryExportTestCase, cls).tearDownClass()

    @tier3
    def test_positive_export_custom_product(self):
        """Export a repository from the custom product

        :id: 9c855866-b9b1-4e32-b3eb-7342fdaa7116

        :expectedresults: Repository was successfully exported, rpm files are
            present on satellite machine

        :CaseLevel: System
        """
        # Create custom product and repository
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({
            'download-policy': 'immediate',
            'organization-id': self.org['id'],
            'product-id': product['id'],
        })
        backend_identifier = entities.Repository(
            id=repo['id']).read().backend_identifier
        repo_export_dir = '/mnt/{0}/{1}/{2}/{3}/custom/{4}/{5}'.format(
            self.export_dir,
            backend_identifier,
            self.org['label'],
            ENVIRONMENT,
            product['label'],
            repo['label'],
        )

        # Export the repository
        Repository.export({'id': repo['id']})

        # Verify export directory is empty
        result = ssh.command("find {} -name '*.rpm'".format(repo_export_dir))
        self.assertEqual(len(result.stdout), 0)

        # Synchronize the repository
        Repository.synchronize({'id': repo['id']})

        # Export the repository once again
        Repository.export({'id': repo['id']})

        # Verify RPMs were successfully exported
        result = ssh.command("find {} -name '*.rpm'".format(repo_export_dir))
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @skip_if_not_set('fake_manifest')
    @tier3
    @upgrade
    def test_positive_export_rh_product(self):
        """Export a repository from the Red Hat product

        :id: e17898db-ca92-4121-a723-0d4b3cf120eb

        :expectedresults: Repository was successfully exported, rpm files are
            present on satellite machine

        :CaseLevel: System
        """
        # Enable RH repository
        with manifests.clone() as manifest:
            ssh.upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': self.org['id'],
        })
        RepositorySet.enable({
            'basearch': 'x86_64',
            'name': REPOSET['rhva6'],
            'organization-id': self.org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
        })
        repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'organization-id': self.org['id'],
            'product': PRDS['rhel'],
        })
        backend_identifier = entities.Repository(
            id=repo['id']).read().backend_identifier
        repo_export_dir = (
            '/mnt/{0}/{1}/{2}/{3}/content/dist/rhel/server/6/6Server/'
            'x86_64/rhev-agent/3/os'
            .format(
                self.export_dir,
                backend_identifier,
                self.org['label'],
                ENVIRONMENT,
            )
        )

        # Update the download policy to 'immediate'
        Repository.update({
            'download-policy': 'immediate',
            'id': repo['id'],
        })

        # Export the repository
        Repository.export({'id': repo['id']})

        # Verify export directory is empty
        result = ssh.command("find {} -name '*.rpm'".format(repo_export_dir))
        self.assertEqual(len(result.stdout), 0)

        # Synchronize the repository
        Repository.synchronize({'id': repo['id']})

        # Export the repository once again
        Repository.export({'id': repo['id']})

        # Verify RPMs were successfully exported
        result = ssh.command("find {} -name '*.rpm'".format(repo_export_dir))
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)


class ContentViewSync(CLITestCase):
    """Implements Content View Export Import tests in CLI

    :CaseComponent: ContentViews
    """

    export_base = '/var/lib/pulp/katello-export'

    @staticmethod
    def _create_cv(cv_name, repo, organization, publish=True):
        """Creates CV and/or publishes in organization with given name and repository

        :param cv_name: The name of CV to create
        :param repo: The repository directory
        :param organization: The organization directory
        :param publish: Publishes the CV if True else doesnt
        :return: The directory of CV and Content View ID
        """
        content_view = make_content_view({
            'name': cv_name,
            'organization-id': organization['id']
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': organization['id'],
            'repository-id': repo['id']
        })
        content_view = ContentView.info({
            'name': cv_name,
            'organization-id': organization['id']
        })
        cvv_id = None
        if publish:
            ContentView.publish({u'id': content_view['id']})
            content_view = ContentView.info({u'id': content_view['id']})
            cvv_id = content_view['versions'][0]['id']
        return content_view, cvv_id

    @staticmethod
    def _enable_rhel_content(organization, repo_name, releasever=None, product=None, sync=True):
        """Enable and/or Synchronize rhel content

        :param organization: The organization directory into which the rhel
            contents will be enabled
        :param bool sync: Syncs contents to repository if true else doesnt
        :return: Repository cli object
        """
        manifests.upload_manifest_locked(
            organization['id'], interface=manifests.INTERFACE_CLI)
        RepositorySet.enable({
            'basearch': 'x86_64',
            'name': REPOSET[repo_name],
            'organization-id': organization['id'],
            'product': PRDS[product],
            'releasever': releasever,
        })
        repo = Repository.info({
            'name': REPOS[repo_name]['name'],
            'organization-id': organization['id'],
            'product': PRDS[product],
        })
        # Update the download policy to 'immediate'
        Repository.update({
            'download-policy': 'immediate',
            'mirror-on-sync': 'no',
            'id': repo['id'],
        })
        if sync:
            # Synchronize the repository
            Repository.synchronize({'id': repo['id']}, timeout=7200)
        repo = Repository.info({
            'name': REPOS[repo_name]['name'],
            'organization-id': organization['id'],
            'product': PRDS[product],
        })
        return repo

    def _update_json(self, json_path):
        """Updates the major and minor version in the exported json file

        :param json_path: json file path on server
        :return: Returns major and minor versions
        """
        new_major = gen_integer(2, 1000)
        new_minor = gen_integer(2, 1000)
        result = ssh.command('[ -f {} ]'.format(json_path))
        if result.return_code == 0:
            ssh.command(
                'sed -i \'s/\"major\": [0-9]\\+/\"major\": {0}/\' {1}'.format(
                    new_major, json_path))
            ssh.command(
                'sed -i \'s/\"minor\": [0-9]\\+/\"minor\": {0}/\' {1}'.format(
                    new_minor, json_path))
            return new_major, new_minor
        raise IOError(
            'Json File {} not found to alternate the major/minor versions'.format(json_path))

    def set_importing_org(self, product, repo, cv, mos='no'):
        """Sets same CV, product and repository in importing organization as
        exporting organization

        :param str product: The product name same as exporting product
        :param str repo: The repo name same as exporting repo
        :param str cv: The cv name same as exporting cv
        :param str mos: Mirror on Sync repo, by default 'no' can override to 'yes'
        """
        self.importing_org = make_org()
        self.importing_prod = make_product({
            'organization-id': self.importing_org['id'],
            'name': product
        })
        self.importing_repo = make_repository({
            'name': repo,
            'mirror-on-sync': mos,
            'download-policy': 'immediate',
            'product-id': self.importing_prod['id']
        })
        self.importing_cv = make_content_view({
            'name': cv,
            'organization-id': self.importing_org['id']
        })
        ContentView.add_repository({
            'id': self.importing_cv['id'],
            'organization-id': self.importing_org['id'],
            'repository-id': self.importing_repo['id']
        })

    @classmethod
    def setUpClass(cls):
        """Create Directory for all CV Sync Tests in export_base directory"""
        super(ContentViewSync, cls).setUpClass()
        if ssh.command('[ -d {} ]'.format(cls.export_base)).return_code == 1:
            raise ExportDirectoryNotSet(
                'Export Directory "{}" is not set/found.'.format(cls.export_base))
        cls.exporting_org = make_org()
        cls.exporting_prod_name = gen_string('alpha')
        product = make_product({
            'organization-id': cls.exporting_org['id'],
            'name': cls.exporting_prod_name
        })
        cls.exporting_repo_name = gen_string('alpha')
        cls.exporting_repo = make_repository({
            'name': cls.exporting_repo_name,
            'mirror-on-sync': 'no',
            'download-policy': 'immediate',
            'product-id': product['id']
        })
        Repository.synchronize({'id': cls.exporting_repo['id']})
        cls.exporting_cv_name = gen_string('alpha')
        cls.exporting_cv, cls.exporting_cvv_id = ContentViewSync._create_cv(
            cls.exporting_cv_name, cls.exporting_repo, cls.exporting_org)

    def tearDown(self):
        """Deletes Directory created for CV export Test during setUp"""
        super(ContentViewSync, self).tearDown()
        ssh.command('rm -rf {}/*'.format(self.export_base))

    @tier3
    def test_positive_export_import_filtered_cvv(self):
        """CV Version with filtered contents only can be exported and imported.

        :id: 2992e0ae-173d-4589-817d-1a11455dfc43

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product.
            4. Create a filter and filter-rule.
            5. Publish the above filtered content-view.
            6. Export Filtered CV version contents to a directory
            7. Import those contents from some other org/satellite.

        :expectedresults:

            1. Filtered CV version custom contents has been exported to directory
            2. Filtered exported custom contents has been imported in org/satellite

        :CaseAutomation: Automated

        :CaseImportance: High

        :CaseLevel: System
        """
        exporting_cv_name = gen_string('alpha')
        exporting_cv, exporting_cvv = ContentViewSync._create_cv(
            exporting_cv_name, self.exporting_repo, self.exporting_org, False)
        filter_name = gen_string('alphanumeric')
        ContentView.filter.create({
            'name': filter_name,
            'content-view-id': exporting_cv['id'],
            'inclusion': 'yes',
            'type': 'rpm'
        })
        ContentView.filter.rule.create({
            'name': 'cat',
            'content-view-filter': filter_name,
            'content-view-id': exporting_cv['id'],
        })
        ContentView.publish({
            'id': exporting_cv['id'],
            'organization-id': self.exporting_org['id'],

        })
        exporting_cv = ContentView.info({u'id': exporting_cv['id']})
        exporting_cvv_id = exporting_cv['versions'][0]['id']
        exporting_cvv_version = exporting_cv['versions'][0]['version']
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': exporting_cvv_id
        })
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, exporting_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        exported_packages = Package.list({'content-view-version-id': exporting_cvv_id})
        self.assertTrue(len(exported_packages) == 1)
        self.set_importing_org(
            self.exporting_prod_name, self.exporting_repo_name, exporting_cv_name)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': self.importing_org['id']
        })
        importing_cvv = ContentView.info({
            u'id': self.importing_cv['id']
        })['versions']
        self.assertTrue(len(importing_cvv) >= 1)
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
        self.assertTrue(len(imported_packages) == 1)

    @tier3
    def test_positive_export_import_cv(self):
        """Export CV version contents in directory and Import them.

        :id: b4fb9386-9b6a-4fc5-a8bf-96d7c80af93e

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite.

        :expectedresults:

            1. CV version custom contents has been exported to directory
            2. All The exported custom contents has been imported in org/satellite

        :CaseAutomation: Automated

        :CaseComponent: ContentViews

        :CaseImportance: High

        :CaseLevel: System
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        exported_packages = Package.list({'content-view-version-id': self.exporting_cvv_id})
        self.assertTrue(len(exported_packages) > 0)
        self.set_importing_org(
            self.exporting_prod_name, self.exporting_repo_name, self.exporting_cv_name)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': self.importing_org['id']
        })
        importing_cvv = ContentView.info({
            u'id': self.importing_cv['id']
        })['versions']
        self.assertTrue(len(importing_cvv) >= 1)
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
        self.assertTrue(len(imported_packages) > 0)
        self.assertEqual(len(exported_packages), len(imported_packages))

    @tier3
    @upgrade
    def test_positive_export_import_redhat_cv(self):
        """Export CV version redhat contents in directory and Import them

        :id: f6bd7fa9-396e-44ac-92a3-ab87ce1a7ef5

        :steps:

            1. Enable product and repository with redhat contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite.

        :expectedresults:

            1. CV version redhat contents has been exported to directory
            2. All The exported redhat contents has been imported in org/satellite

        :bz: 1655239

        :CaseAutomation: Automated

        :CaseComponent: ContentViews

        :CaseImportance: High

        :CaseLevel: System
        """
        rhva_repo_name = 'rhva6'
        releasever = '6Server'
        product = 'rhel'
        rhva_repo = ContentViewSync._enable_rhel_content(
            self.exporting_org, rhva_repo_name, releasever, product)
        rhva_cv_name = gen_string('alpha')
        rhva_cv, exporting_cvv_id = ContentViewSync._create_cv(
            rhva_cv_name, rhva_repo, self.exporting_org)
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': exporting_cvv_id
        })
        exporting_cvv_version = rhva_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, rhva_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        exported_packages = Package.list({'content-view-version-id': exporting_cvv_id})
        self.assertTrue(len(exported_packages) > 0)
        Subscription.delete_manifest({'organization-id': self.exporting_org['id']})
        importing_org = make_org()
        imp_rhva_repo = ContentViewSync._enable_rhel_content(
            importing_org, rhva_repo_name, releasever, product, sync=False)
        importing_cv, _ = ContentViewSync._create_cv(
            rhva_cv_name, imp_rhva_repo, importing_org, publish=False)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': importing_org['id']
        })
        importing_cvv_id = ContentView.info({
            u'id': importing_cv['id']
        })['versions'][0]['id']
        imported_packages = Package.list({'content-view-version-id': importing_cvv_id})
        self.assertTrue(len(imported_packages) > 0)
        self.assertEqual(len(exported_packages), len(imported_packages))

    @tier4
    def test_positive_export_import_redhat_cv_with_huge_contents(self):
        """Export CV version redhat contents in directory and Import them

        :id: 05eb185f-e526-466c-9c14-702dde1d49de

        :steps:

            1. Enable product and repository with redhat repository having huge contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite.

        :expectedresults:

            1. CV version redhat contents has been exported to directory
            2. All The exported redhat contents has been imported in org/satellite

        :bz: 1655239

        :CaseAutomation: Automated

        :CaseComponent: ContentViews

        :CaseImportance: Critical

        :CaseLevel: Acceptance
        """
        rhel_repo_name = 'rhscl7'
        product = 'rhscl'
        releasever = '7Server'
        rhel_repo = ContentViewSync._enable_rhel_content(
            self.exporting_org, rhel_repo_name, releasever, product)
        rhel_cv_name = gen_string('alpha')
        rhel_cv, exporting_cvv_id = ContentViewSync._create_cv(
            rhel_cv_name, rhel_repo, self.exporting_org)
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': exporting_cvv_id}, timeout=7200)
        exporting_cvv_version = rhel_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, rhel_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        exported_packages = Package.list({'content-view-version-id': exporting_cvv_id})
        self.assertTrue(len(exported_packages) > 0)
        Subscription.delete_manifest({'organization-id': self.exporting_org['id']})
        importing_org = make_org()
        imp_rhel_repo = ContentViewSync._enable_rhel_content(
            importing_org, rhel_repo_name, releasever, product, sync=False)
        importing_cv, _ = ContentViewSync._create_cv(
            rhel_cv_name, imp_rhel_repo, importing_org, publish=False)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': importing_org['id']}, timeout=7200)
        importing_cvv_id = ContentView.info({
            u'id': importing_cv['id']
        })['versions'][0]['id']
        imported_packages = Package.list({'content-view-version-id': importing_cvv_id})
        self.assertTrue(len(imported_packages) > 0)
        self.assertEqual(len(exported_packages), len(imported_packages))

    @tier2
    def test_positive_exported_cv_tar_contents(self):
        """Exported CV version contents in export directory are same as CVv contents

        :id: 35cc3b20-0fbc-4177-a89c-b4c8d7389a77

        :steps:

            1. Enable product and repository with contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Validate contents in a directory.

        :expectedresults:

            1. The CVv should be exported to specified location with contents tar and json

        :CaseLevel: Integration
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        result = ssh.command("tar -t -f {}".format(exported_tar))
        contents_tar = 'export-{0}-{1}/export-{0}-{1}-repos.tar'.format(
            self.exporting_cv_name, exporting_cvv_version)
        self.assertIn(contents_tar, result.stdout)
        cvv_packages = Package.list({'content-view-version-id': self.exporting_cvv_id})
        self.assertTrue(len(cvv_packages) > 0)
        ssh.command("tar -xf {0} -C {1}".format(exported_tar, self.export_base))
        exported_packages = ssh.command("tar -tf {0}/{1} | grep .rpm | wc -l".format(
            self.export_base, contents_tar))
        self.assertEqual(len(cvv_packages), int(exported_packages.stdout[0]))

    @tier1
    @upgrade
    def test_positive_export_import_promoted_cv(self):
        """Export promoted CV version contents in directory and Import them.

        :id: 315ef1f0-e2ad-43ec-adff-453fb71654a7

        :steps:

            1. Create product and repository with contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Promote the CV.
            5. Export CV version contents to a directory
            6. Import those contents from some other org/satellite.

        :expectedresults:

            1. Promoted CV version contents has been exported to directory
            2. Promoted CV version contents has been imported successfully
            3. The imported CV should only be published and not promoted

        :CaseLevel: System
        """
        env = make_lifecycle_environment({u'organization-id': self.exporting_org['id']})
        ContentView.version_promote({
            u'id': self.exporting_cvv_id,
            u'to-lifecycle-environment-id': env['id'],
        })
        promoted_cvv_id = ContentView.info({
            u'id': self.exporting_cv['id'],
        })['versions'][-1]['id']
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': promoted_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        exported_packages = Package.list({'content-view-version-id': promoted_cvv_id})
        self.set_importing_org(
            self.exporting_prod_name, self.exporting_repo_name, self.exporting_cv_name)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': self.importing_org['id']
        })
        importing_cvv = ContentView.info({
            u'id': self.importing_cv['id']
        })['versions']
        self.assertEqual(len(importing_cvv), 1)
        imported_packages = Package.list({'content-view-version-id': importing_cvv[0]['id']})
        self.assertEqual(len(exported_packages), len(imported_packages))

    @tier2
    def test_positive_repo_contents_of_imported_cv(self):
        """Repo contents of imported CV are same as repo contents of exported CV

        :id: 76305fb9-2afd-46f8-842a-03bb706fa3fa

        :steps:

            1. Enable product and repository with contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite

        :expectedresults:

            1. The contents in repo of imported CV are same as repo of exported CV

        :CaseLevel: Integration
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        self.set_importing_org(
            self.exporting_prod_name, self.exporting_repo_name, self.exporting_cv_name)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': self.importing_org['id']
        })
        exported_repo = Repository.info({'id': self.exporting_repo['id']})
        imported_repo = Repository.info({'id': self.importing_repo['id']})
        self.assertEqual(
            exported_repo['content-counts']['packages'],
            imported_repo['content-counts']['packages'])
        self.assertEqual(
            exported_repo['content-counts']['errata'],
            imported_repo['content-counts']['errata'])

    @tier2
    def test_negative_reimport_cv_with_same_major_minor(self):
        """Reimport CV version with same major and minor fails

        :id: 15a7ddd3-c1a5-4b22-8460-6cb2b8ea4ef9

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Import those contents from some other org/satellite.
            6. Attempt to reimport the those contents(without changing version in json)

        :expectedresults:

            1. Reimporting the contents with same major and minor fails
            2. Satellite displays an error 'A CV version already exists with the same major and
                minor version'
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        self.set_importing_org(
            self.exporting_prod_name, self.exporting_repo_name, self.exporting_cv_name)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': self.importing_org['id']
        })
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_import({
                'export-tar': exported_tar,
                'organization-id': self.importing_org['id']
            })
        self.assert_error_msg(
            error,
            "the Content View '{0}' is greater or equal to the version you "
            "are trying to import".format(self.exporting_cv_name)
        )

    @tier2
    def test_negative_import_cv_without_replicating_import_part(self):
        """Import CV version without creating same CV and repo at importing side

        :id: 4cc69666-407f-4d66-b3d2-8fe2ed135a5f

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish.
            4. Export CV version contents to a directory
            5. Don't create replica CV and repo at importing org/satellite
            6. Attempt to import the exported contents

        :expectedresults:

            1. Error 'Unable to sync repositories, no library repository found' should be
                displayed
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        importing_org = make_org()
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_import({
                'export-tar': exported_tar,
                'organization-id': importing_org['id']
            })
        self.assert_error_msg(
            error,
            'Error: The Content View {} is not present on this server, '
            'please create the Content View and try the import again'.format(
                self.exporting_cv_name)
        )

    @tier1
    def test_negative_import_without_associating_repo_to_cv(self):
        """Importing CV version without associating repo to CV at importing side throws error

        :id: 3d20612f-b769-462e-9829-f13fd81bd4c7

        :steps:

            1. Create product and repository with custom contents
            2. Sync the repository
            3. Create CV with above product and publish
            4. Export CV version contents to a directory
            5. Create replica CV but don't associate repo to CV at importing org/satellite
            6. Import those contents from some other org/satellite.

        :expectedresults:

            1. Error 'Unable to sync repositories, no library repository found' should be
                displayed
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        importing_org = make_org()
        make_content_view({
            'name': self.exporting_cv_name,
            'organization-id': importing_org['id']
        })
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_import({
                'export-tar': exported_tar,
                'organization-id': importing_org['id']
            })
        self.assert_error_msg(
            error,
            'Unable to sync repositories, no library repository found'
        )

    @tier2
    def test_negative_export_cv_with_on_demand_repo(self):
        """Exporting CV version having on_demand repo throws error

        :id: f8b86d0e-e1a7-4e19-bb82-6de7d16c6676

        :steps:

            1. Create product and on-demand repository with custom contents
            2. Sync the repository
            3. Create CV with above product and publish
            4. Attempt to export CV version contents to a directory

        :expectedresults:

            1. Export fails with error 'All exported repositories must be set to an immediate
                download policy and re-synced' should be displayed.

        """
        exporting_org = make_org()
        exporting_prod = gen_string('alpha')
        product = make_product({
            'organization-id': exporting_org['id'],
            'name': exporting_prod
        })
        exporting_repo = gen_string('alpha')
        repo = make_repository({
            'name': exporting_repo,
            'download-policy': 'on_demand',
            'product-id': product['id']
        })
        Repository.synchronize({'id': repo['id']})
        exporting_cv = gen_string('alpha')
        _, exporting_cvv_id = ContentViewSync._create_cv(
            exporting_cv, repo, exporting_org)
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_export({
                'export-dir': '{}'.format(self.export_base),
                'id': exporting_cvv_id
            })
        self.assert_error_msg(
            error,
            'All exported repositories must be set to an immediate download policy and re-synced'
        )

    @tier2
    def test_negative_export_cv_with_background_policy_repo(self):
        """Exporting CV version having background policy repo throws error

        :id: c0f5a903-e9a8-4ce6-9377-1df1e7ba62c5

        :steps:

            1. Create product and background policy repository with custom contents
            2. Sync the repository
            3. Create CV with above product and publish
            4. Attempt to export CV version contents to a directory

        :expectedresults:

            1. Export fails with error 'All exported repositories must be set to an immediate
                download policy and re-synced' should be displayed.

        """
        exporting_org = make_org()
        exporting_prod = gen_string('alpha')
        product = make_product({
            'organization-id': exporting_org['id'],
            'name': exporting_prod
        })
        repo = make_repository({
            'name': gen_string('alpha'),
            'download-policy': 'background',
            'product-id': product['id']
        })
        Repository.synchronize({'id': repo['id']})
        _, exporting_cvv_id = ContentViewSync._create_cv(
            gen_string('alpha'), repo, exporting_org)
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_export({
                'export-dir': '{}'.format(self.export_base),
                'id': exporting_cvv_id
            })
        self.assert_error_msg(
            error,
            'All exported repositories must be set to an immediate download policy and re-synced'
        )

    @tier2
    def test_negative_import_cv_with_mirroronsync_repo(self):
        """Importing CV version having mirror-on-sync repo throws error

        :id: dfa0cd5f-1596-4097-b505-06bc14de51dd

        :steps:

            1. Create product and mirror-on-sync repository with custom contents
            2. Sync the repository
            3. Create CV with above product and publish
            4. Attempt to export CV version contents to a directory

        :expectedresults:

            1. Export fails with error 'The Repository '<repo_name>' is set with Mirror-on-Sync '
            'to YES. Please change Mirror-on-Sync to NO and try the import again' should be
            displayed.

        """
        exporting_prod_name = gen_string('alpha')
        product = make_product({
            'organization-id': self.exporting_org['id'],
            'name': exporting_prod_name
        })
        exporting_repo_name = gen_string('alpha')
        repo = make_repository({
            'name': exporting_repo_name,
            'download-policy': 'immediate',
            'mirror-on-sync': 'yes',
            'product-id': product['id']
        })
        Repository.synchronize({'id': repo['id']})
        exporting_cv_name = gen_string('alpha')
        exporting_cv, exporting_cvv_id = ContentViewSync._create_cv(
            exporting_cv_name, repo, self.exporting_org)
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': exporting_cvv_id
        })
        exporting_cvv_version = exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, exporting_cv_name, exporting_cvv_version)
        self.set_importing_org(
            exporting_prod_name, exporting_repo_name, exporting_cv_name, mos='yes')
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_import({
                'export-tar': exported_tar,
                'organization-id': self.importing_org['id']
            })
        self.assert_error_msg(
            error,
            "The Repository '{}' is set with Mirror-on-Sync to YES. "
            "Please change Mirror-on-Sync to NO and try the import again".format(
                exporting_repo_name)
        )

    @tier2
    def test_positive_create_custom_major_minor_cv_version(self):
        """CV can published with custom major and minor versions

        :id: 6697cd22-253a-4bdc-a108-7e0af22caaf4

        :steps:

            1. Create product and repository with custom contents
            2. Sync the repository
            3. Create CV with above repository
            4. Publish the CV with custom major and minor versions

        :expectedresults:

            1. CV version with custom major and minor versions is created

        :CaseLevel: System
        """
        org = make_org()
        major = randint(1, 1000)
        minor = randint(1, 1000)
        content_view = make_content_view({
            'name': gen_string('alpha'),
            'organization-id': org['id']
        })
        ContentView.publish({u'id': content_view['id'], 'major': major, 'minor': minor})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]['version']
        self.assertEqual(cvv.split('.')[0], str(major))
        self.assertEqual(cvv.split('.')[1], str(minor))

    @skip_if_bug_open('bugzilla', 1657711)
    @tier3
    def test_negative_export_cv_with_puppet_repo(self):
        """Exporting CV version having non yum(puppet) repo throws error

        :id: 5e27f994-34f2-4595-95a9-346c6b9415f6

        :steps:

            1. Create product and non yum(puppet) repository
            2. Sync the repository
            3. Create CV with above product and publish
            4. Attempt to export CV version contents to a directory

        :expectedresults:

            1. Export fails with error 'The Repository '#name' is a non-yum repository.
            Only Yum is supported at this time. Please remove the repository from the
            Content View, republish and try the export again'.

        """
        module = {'name': 'versioned', 'version': '3.3.3'}
        exporting_org = make_org()
        product = make_product({
            'organization-id': exporting_org['id'],
            'name': gen_string('alpha')
        })
        repo = make_repository({
            'url': CUSTOM_PUPPET_REPO,
            'content-type': 'puppet',
            'product-id': product['id']
        })
        Repository.synchronize({'id': repo['id']})
        puppet_module = PuppetModule.list({
            'search': 'name={name} and version={version}'.format(**module)})[0]
        content_view = make_content_view({u'organization-id': exporting_org['id']})
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'name': puppet_module['name'],
            u'author': puppet_module['author'],
        })
        ContentView.publish({u'id': content_view['id']})
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_export({
                'export-dir': '{}'.format(self.export_base),
                'id': ContentView.info({u'id': content_view['id']})['versions'][0]['id']
            })
        self.assert_error_msg(
            error,
            "Could not export the content view:\n  "
            "Error: The Content View '{}' contains Puppet modules, "
            "this is not supported at this time. Please remove the modules, "
            "publish a new version and try the export again.\n".format(content_view['name'])
        )

    @skip_if_bug_open('bugzilla', 1657711)
    @tier3
    def test_negative_export_cv_with_mixed_content_repos(self):
        """Exporting CV version having yum and non-yum(puppet) repos throws error

        :id: ffcdbbc6-f787-4978-80a7-4b44c389bf49

        :steps:

            1. Create product with yum and non-yum(puppet) repos
            2. Sync the repositories
            3. Create CV with above product and publish
            4. Attempt to export CV version contents to a directory

        :expectedresults:

            1. Export fails with error 'The Repository '#name' is a non-yum repository.
            Only Yum is supported at this time. Please remove the repository from the
            Content View, republish and try the export again'.

        """
        module = {'name': 'versioned', 'version': '3.3.3'}
        product = make_product({
            'organization-id': self.exporting_org['id'],
            'name': gen_string('alpha')
        })
        nonyum_repo = make_repository({
            'url': CUSTOM_PUPPET_REPO,
            'content-type': 'puppet',
            'product-id': product['id']
        })
        Repository.synchronize({'id': nonyum_repo['id']})
        yum_repo = make_repository({
            'name': gen_string('alpha'),
            'download-policy': 'immediate',
            'mirror-on-sync': 'no',
            'product-id': product['id']
        })
        Repository.synchronize({'id': yum_repo['id']})
        puppet_module = PuppetModule.list({
            'search': 'name={name} and version={version}'.format(**module)})[0]
        content_view = make_content_view({u'organization-id': self.exporting_org['id']})
        ContentView.puppet_module_add({
            'content-view-id': content_view['id'],
            'name': puppet_module['name'],
            'author': puppet_module['author'],
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': self.exporting_org['id'],
            'repository-id': yum_repo['id']
        })
        ContentView.publish({u'id': content_view['id']})
        with self.assertRaises(CLIReturnCodeError) as error:
            ContentView.version_export({
                'export-dir': '{}'.format(self.export_base),
                'id': ContentView.info({u'id': content_view['id']})['versions'][0]['id']
            })
        self.assert_error_msg(
            error,
            "Could not export the content view:\n  "
            "Error: The Content View '{}' contains Puppet modules, "
            "this is not supported at this time. Please remove the modules, "
            "publish a new version and try the export again.\n".format(content_view['name'])
        )

    @tier2
    def test_positive_import_cv_with_customized_major_minor(self):
        """Import the CV version with customized major and minor

        :id: 38237795-0275-408c-8a0d-462120dafc59

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish
            4. Export CV version contents to a directory
            5. Untar the exported tar
            6. Customize/Update the major and minor in metadata json
            7. Retar with updated json and contents tar
            8. Import the CV version from the updated json tar from some other org/satellite

        :expectedresults:

            1. The Cv version is imported with updated json
            2. The Imported CV version has major and minor updated in exported tar json
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        self.set_importing_org(
            self.exporting_prod_name, self.exporting_repo_name, self.exporting_cv_name)
        # Updating the json in exported tar
        ssh.command("tar -xf {0} -C {1}".format(exported_tar, self.export_base))
        extracted_directory_name = 'export-{0}-{1}'.format(
            self.exporting_cv_name, exporting_cvv_version)
        json_path = '{0}/{1}/{1}.json'.format(self.export_base, extracted_directory_name)
        new_major, new_minor = self._update_json(json_path)
        custom_cvv_tar = '{0}/{1}.tar'.format(self.export_base, extracted_directory_name)
        ssh.command("tar -cvf {0} {1}/{2}".format(
            custom_cvv_tar, self.export_base, extracted_directory_name))
        # Importing the updated tar
        ContentView.version_import({
            'export-tar': custom_cvv_tar,
            'organization-id': self.importing_org['id']
        })
        imported_cvv = ContentView.info({
            u'id': self.importing_cv['id']
        })['versions']
        self.assertEqual(str(new_major), imported_cvv[0]['version'].split('.')[0])
        self.assertEqual(str(new_minor), imported_cvv[0]['version'].split('.')[1])

    @tier1
    def test_positive_exported_cvv_json_contents(self):
        """Export the CV version and verify export metadata json fields

        :id: 44934116-b051-4bb3-814a-08a80303e4ee

        :steps:

            1. Create product and repository with custom contents.
            2. Sync the repository.
            3. Create CV with above product and publish
            4. Export CV version contents to a directory
            5. Untar the exported tar

        :expectedresults:

            The exported json has following fields and in sequence:
             Name of CV
             Major of CVv
             Minor of CVv
             Metadata of Repositories in CVv, each with the following info:
             The repository ID
             The repository label
             The repository content Type
             Backend Identifier
             Relative Path to Packages in tar file
             On disk path to Packages in /var/lib/pulp
             rpm file names in CVV repo:
             Rpm names
             Errata IDs in CVV Repo:
             Errata IDs

        """
        exporting_repo = Repository.info({
            u'id': self.exporting_repo['id']
        })
        exporting_cv = ContentView.info({
            u'id': self.exporting_cv['id']
        })
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exporting_cvv_version = self.exporting_cv['versions'][0]['version']
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, exporting_cvv_version)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        # Updating the json in exported tar
        ssh.command("tar -xf {0} -C {1}".format(exported_tar, self.export_base))
        extracted_directory_name = 'export-{0}-{1}'.format(
            self.exporting_cv_name, exporting_cvv_version)
        json_path_server = '{0}/{1}/{1}.json'.format(self.export_base, extracted_directory_name)
        json_path_local = '/tmp/{}.json'.format(extracted_directory_name)
        ssh.download_file(json_path_server, json_path_local)
        with open(json_path_local) as metafile:
            metadata = json.load(metafile)
        self.assertEqual(metadata.get('name'), self.exporting_cv_name)
        self.assertEqual(
            str(metadata.get('major')), exporting_cv['versions'][0]['version'].split('.')[0])
        self.assertEqual(
            str(metadata.get('minor')), exporting_cv['versions'][0]['version'].split('.')[1])
        self.assertIsNotNone(metadata.get('repositories'))
        cvv_repository = metadata['repositories'][0]
        self.assertEqual(cvv_repository.get('content_type'), 'yum')
        self.assertEqual(cvv_repository.get('label'), self.exporting_repo_name)
        self.assertIsNotNone(cvv_repository.get('backend_identifier'))
        self.assertIsNotNone(cvv_repository.get('on_disk_path'))
        self.assertIsNotNone(cvv_repository.get('relative_path'))
        self.assertEqual(
            int(exporting_repo['content-counts']['packages']),
            len(cvv_repository.get('rpm_filenames')))
        self.assertEqual(
            int(exporting_repo['content-counts']['errata']),
            len(cvv_repository.get('errata_ids')))


class InterSatelliteSyncTestCase(CLITestCase):
    """Implements InterSatellite Sync tests in CLI"""

    @stubbed()
    @tier3
    def test_negative_import_cv(self):
        """Export whole CV version contents in directory and Import nothing.

        :id: bcb4f64f-a480-4be0-a4ef-3ee1f024d8d7

        :steps:

            1. Export whole CV version contents to a directory specified in
               settings.
            2. Don't copy exported contents to /var/www/html/pub/export
               directory.
            3. Attempt to import these not copied contents from some other
               org/satellite.

        :expectedresults:

            1. Whole CV version contents has been exported to directory
               specified in settings.
            2. The exported contents are not imported due to non availability.
            3. Error is thrown for non availability of CV contents to import.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_cv(self):
        """Export whole CV version contents is aborted due to insufficient
        memory.

        :id: 4fa58c0c-95d2-45f5-a7fc-c5f3312a989c

        :steps: Attempt to Export whole CV version contents to a directory
            which has less memory available than contents size.

        :expectedresults: The export CV version contents has been aborted due
            to insufficient memory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_cv_iso(self):
        """Export CV version contents in directory as iso and Import it.

        :id: 5c39afd4-09d6-43c5-8d50-edc98105b7db

        :steps:

            1. Export whole CV version contents as ISO to a directory specified
               in settings.
            2. Copy exported ISO to /var/www/html/pub/export directory.
            3. Import these copied ISO from some other org/satellite.

        :expectedresults:

            1. CV version has been exported to directory as ISO in specified in
               settings.
            2. The exported ISO has been imported in org/satellite.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_import_cv_iso(self):
        """Export whole CV version as ISO in directory and Import nothing.

        :id: af9b3d6f-25c0-43a5-b8a7-d9a0df1986b4

        :steps:

            1. Export whole CV version as ISO to a directory specified in
               settings.
            2. Don't copy exported ISO to /var/www/html/pub/export directory.
            3. Attempt to import this not copied ISO from some other
               org/satellite.

        :expectedresults:

            1. The exported iso is not imported due to non availability.
            2. Error is thrown for non availability of CV version ISO to
               import.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_cv_iso(self):
        """Export whole CV version to iso is aborted due to insufficient
        memory.

        :id: ef84ffbd-c7cf-4d9a-9944-3c3b06a18872

        :steps: Attempt to Export whole CV version as iso to a directory which
            has less memory available than contents size.

        :expectedresults: The export CV version to iso has been aborted due to
            insufficient memory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_cv_iso_max_size(self):
        """Export whole CV version to iso is aborted due to inadequate maximum
        iso size.

        :id: 93fe1cef-254b-484d-a628-bec56b356234

        :steps: Attempt to Export whole CV version as iso with mb size less
            than required.

        :expectedresults: The export CV version to iso has been aborted due to
            maximum size is not enough to contain the CV version contents.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_export_cv_iso_max_size(self):
        """CV version exported to iso in maximum iso size.

        :id: 7ec91557-bafc-490d-b760-573a07389be5

        :steps: Attempt to Export whole CV version as iso with mb size more
            than required.

        :expectedresults: CV version has been exported to iso successfully.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_cv_incremental(self):
        """Export and Import CV version contents incrementally.

        :id: 3c4dfafb-fabf-406e-bca8-7af1ab551135

        :steps:

            1. In upstream, Export CV version contents to a directory specified
               in settings.
            2. In downstream, Import these copied contents from some other
               org/satellite.
            3. In upstream, Add new packages to the CV.
            4. Export the CV incrementally from the last date time.
            5. In downstream, Import the CV incrementally.

        :expectedresults:

            1. On incremental export, only the new packages are exported.
            2. New directory of incremental export with new packages is
               created.
            3. On incremental import, only the new packages are imported.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_import_cv_incremental(self):
        """No new incremental packages exported or imported.

        :id: 90692d59-788c-4e18-add1-33db04204a4b

        :steps:

            1. In upstream, Export CV version contents to a directory specified
               in settings.
            2. In downstream, Import these copied contents from some other
               org/satellite.
            3. In upstream, Don't add any new packages to the CV.
            4. Export the CV incrementally from the last date time.
            5. In downstream, Import the CV incrementally.

        :expectedresults:

            1. An Empty packages directory created on incremental export.
            2. On incremental import, no new packages are imported.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_exported_cv_iso_dir_structure(self):
        """Exported CV in iso format respects cdn directory structure.

        :id: cb901dde-1839-4e7d-a57b-8e41c212dc77

        :steps:

            1. Export the full CV in iso format.
            2. Mount the iso.
            3. Verify iso directory structure.

        :expectedresults: Exported CV in iso should follow the cdn directory
            structure.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_repo(self):
        """Export repo in directory and Import them.

        :id: 2c5f09ce-225b-4f9d-ad4b-a26fe094b0e7

        :steps:

            1. Export repo to a directory specified in settings.
            2. Copy exported repo contents to /var/www/html/pub/export
               directory.
            3. Import these copied repo contents from some other org/satellite.

        :expectedresults:

            1. The repo has been exported to directory specified in settings.
            2. The exported repo has been imported in org/satellite.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_import_repo(self):
        """Export repo contents in directory and Import nothing.

        :id: 8e0bbed9-bc68-44d3-a79c-2861f323e2ff

        :steps:

            1. Export repo to a directory specified in settings.
            2. Dont copy exported repo to /var/www/html/pub/export directory.
            3. Attempt to import this not copied repo from some other
               org/satellite.

        :expectedresults:

            1. The repo has been exported to directory specified in settings.
            2. The exported repo are not imported due to non availability.
            3. Error is thrown for non availability of repo contents to import.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_repo(self):
        """Export repo is aborted due ti insufficient memory.

        :id: 4bdd1183-a3a5-41a8-8a38-34c1035b64da

        :steps: Attempt to Export repo to a directory which has less memory
            available than contents size.

        :expectedresults: The export repo has been aborted due to insufficient
            memory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_lazy_sync_repo(self):
        """Error is raised for lazy sync repo.

        :id: 296a7bde-d8af-4e4d-b673-a7c393f6f846

        :steps: Attempt to Export repo with 'on_demand' download policy.

        :expectedresults: An Error is raised for updating the repo download
            policy to 'immediate' to be exported.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_reimport_repo(self):
        """Packages missing from upstream are removed from downstream on reimport.

        :id: b3a71405-d8f0-4085-b728-8fc3513611c8

        :steps:

            1. From upstream Export repo fully and import it in downstream.
            2. In upstream delete some packages from repo.
            3. Re-export the full repo.
            4. In downstream, reimport the repo re-exported.

        :expectedresults: Deleted packages from upstream are removed from
            downstream.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_repo_iso(self):
        """Export repo in directory as iso and Import it.

        :id: 95658d9e-9f0b-466f-a412-1bebadc709c9

        :steps:

            1. Export repo as ISO to a directory specified in settings.
            2. Copy exported ISO to /var/www/html/pub/export directory.
            3. Import this copied ISO from some other org/satellite.

        :expectedresults:

            1. repo has been exported to directory as ISO in specified in
               settings.
            2. The exported ISO has been imported in org/satellite.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_import_repo_iso(self):
        """Export repo as ISO in directory and Import nothing.

        :id: dab72a79-e508-4236-ad7e-f92bb9639b5e

        :steps:

            1. Export repo as ISO to a directory specified in settings.
            2. Dont copy exported ISO to /var/www/html/pub/export directory.
            3. Attempt to import this not copied ISO from some other
               org/satellite.

        :expectedresults:

            1. The exported iso is not imported due to non availability.
            2. Error is thrown for non availability of repo ISO to import.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_repo_iso(self):
        """Export repo to iso is aborted due to insufficient memory.

        :id: 028c4972-5746-463d-afd3-a1cea337ee11

        :steps: Attempt to Export repo as iso to a directory which has less
            memory available than contents size.

        :expectedresults: The export repo to iso has been aborted due to
            insufficient memory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_repo_iso_max_size(self):
        """Export repo to iso is aborted due to inadequate maximum iso size.

        :id: ef2ba2ec-0ec6-4c33-9c22-e4102734eecf

        :steps: Attempt to Export repo as iso with mb size less than required.

        :expectedresults: The export repo to iso has been aborted due to
            maximum size is not enough to contain the repo  contents.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_export_repo_iso_max_size(self):
        """Repo exported to iso with maximum iso size.

        :id: 19626697-9c5e-49d1-8429-720881dfe73d

        :steps: Attempt to Export repo as iso with mb size more than required.

        :expectedresults: Repo has been exported to iso successfully.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_repo_from_future_datetime(self):
        """Incremental export fails with future datetime.

        :id: 1e8bc352-198f-4d59-b437-1b184141fab4

        :steps: Export the repo incrementally from the future date time.

        :expectedresults: Error is raised for attempting to export from future
            datetime.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_repo_incremental(self):
        """Export and Import repo incrementally.

        :id: b2537c09-4dd8-440d-be11-0728ee4be804

        :steps:

            1. In upstream, Export repo to a directory specified in settings.
            2. In downstream, Import this repo fully.
            3. In upstream, Add new packages to the repo.
            4. Export the repo incrementally from the last date time.
            5. In downstream, Import the repo incrementally.

        :expectedresults:

            1. On incremental export, only the new packages are exported.
            2. New directory of incremental export with new packages is
               created.
            3. On incremental import, only the new packages are imported.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_import_repo_incremental(self):
        """No new incremental packages exported or imported.

        :id: b51a3718-87d0-4aa1-8bff-fa153bd72df0

        :steps:

            1. In upstream, Export repo to a directory specified in settings.
            2. In downstream, fully Import this repo.
            3. In upstream, Don't add any new packages to the repo.
            4. Export the repo incrementally from the last date time.
            5. In downstream, Import the repo incrementally.

        :expectedresults:

            1. An Empty packages directory created on incremental export.
            2. On incremental import, no new packages are imported.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_exported_repo_iso_dir_structure(self):
        """Exported repo in iso format respects cdn directory structure.

        :id: 6bfc28a8-6615-4927-976a-30e7a9bb6860

        :steps:

            1. Export the full repo in iso format.
            2. Mount the iso.
            3. Verify iso directory structure.

        :expectedresults: Exported repo in iso should follow the cdn directory
            structure.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_kickstart_tree(self):
        """kickstart tree is exported to specified location.

        :id: bb9e77ed-fbbb-4e43-b118-2ddcb7c6341f

        :steps:

            1. Export the full kickstart tree.
            2. Copy exported kickstart tree contents to
               /var/www/html/pub/export.
            3. Import above exported kickstart tree from other org/satellite.

        :expectedresults:

            1. Whole kickstart tree contents has been exported to directory
               specified in settings.
            2. All The exported contents has been imported in org/satellite.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_import_kickstart_tree(self):
        """Export whole kickstart tree in directory and Import nothing.

        :id: 55ddf6a6-b99a-4986-bdd3-7a5384f06915

        :steps:

            1. Export whole kickstart tree contents to a directory specified in
               settings.
            2. Dont copy exported contents to /var/www/html/pub/export
               directory.
            3. Attempt to import these not copied contents from some other
               org/satellite.

        :expectedresults:

            1. Whole kickstart tree has been exported to directory specified in
               settings.
            2. The exported contents are not imported due to non availability.
            3. Error is thrown for non availability of kickstart tree to
               import.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_export_kickstart_tree(self):
        """Export whole kickstart tree contents is aborted due to insufficient
        memory.

        :id: 5f681f43-bac8-4196-9b3c-8b66b9c149f9

        :steps: Attempt to Export whole kickstart tree contents to a directory
            which has less memory available than contents size.

        :expectedresults: The export kickstart tree has been aborted due to
            insufficient memory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

# Red Hat Repositories Export and Import

    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_repo(self):
        """Export Red Hat YUM repo in directory.

        :id: 96bd5c72-6eb0-4b32-b75a-14c6ad556cc0

        :steps: Export whole Red Hat YUM repo to some path.

        :expectedresults: Whole YUM repo contents has been exported to
            directory specified in settings.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_redhat_yum_repo(self):
        """Import the exported YUM repo contents.

        :id: afc447b4-ed74-4ed3-839f-3d0048e4eca3

        :steps:

            1. Export Red Hat YUM repo to path which will be accessible over
               HTTP.
            2. Import the repository by defining the CDN URL the same as the
               exported HTTP URL.

        :expectedresults: All the exported YUM repo contents are imported
            successfully.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_export_redhat_incremental_yum_repo(self):
        """Export Red Hat YUM repo in directory incrementally.

        :id: be054636-629a-40a0-b414-da3964154bd1

        :steps:

            1. Export whole Red Hat YUM repo.
            2. Add some packages to the earlier exported yum repo.
            3. Incrementally export the yum repo from last exported date.

        :expectedresults: Red Hat YUM repo contents have been exported
            incrementally in separate directory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_redhat_incremental_yum_repo(self):
        """Import the exported YUM repo contents incrementally.

        :id: 318560d7-71f5-4646-ab5c-12a2ec22d031

        :steps:

            1. First, Export and Import whole Red Hat YUM repo.
            2. Add some packages to the earlier exported yum repo.
            3. Incrementally export the Red Hat YUM repo from last exported
               date.
            4. Import the exported YUM repo contents incrementally.

        :expectedresults: YUM repo contents have been imported incrementally.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory.

        :id: e96a7a8c-9e71-4379-86e6-78177dfbf555

        :steps: Export whole Red Hat YUM repo as ISO.

        :expectedresults: Whole repo contents has been exported as ISO in
            separate directory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_redhat_yum_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory and Import.

        :id: d1af556e-c622-4ca0-a617-0216d5805d45

        :steps:

            1. Export whole Red Hat YUM repo as ISO.
            2. Mount exported ISO and explore the ISO contents on HTTP.
            3. Import the repository by defining the CDN URL the same as the
               exported HTTP URL.

        :expectedresults: All The exported repo contents in ISO has been
            imported successfully.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_incremental_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory and import incrementally.

        :id: c54e9410-9945-4662-bea0-a4ab35e90606

        :steps:

            1. First, Export and Import whole Red Hat YUM repo.
            2. Add some packages to the earlier exported yum repo.
            3. Incrementally export the yum repo as ISO from last exported
               date.

        :expectedresults: Repo contents have been exported as ISO incrementally
            in separate directory.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_redhat_yum_incremental_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory and import incrementally.

        :id: 5e3f4013-489e-4d4e-abd9-49077f89efcd

        :steps:

            1. First, Export and Import whole Red Hat YUM repo.
            2. Add some packages to the earlier exported yum repo.
            3. Incrementally export the yum repo as ISO from last exported
               date.
            4. Mount incrementally exported contents ISO.
            5. Import the repo contents incrementally.

        :expectedresults: Repo contents have been exported as ISO and imported
            incrementally.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_export_redhat_cv(self):
        """Export CV version having Red Hat contents in directory.

        :id: 3eacbd64-e81b-455e-969d-570582616c4a

        :steps: Export whole CV version having Red Hat contents to a directory
            specified in settings.

        :expectedresults: Whole CV version contents has been exported to
            directory specified in settings.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_redhat_cv(self):
        """Export CV version having Red Hat contents in directory and Import
        them.

        :id: 0c9f1a9b-a166-4b9a-a9c4-099f3a45d552

        :steps:

            1. Export whole CV version having Red Hat contents to a path
               accessible over HTTP.
            2. Import the repository by defining the CDN URL from the exported
               HTTP URL.

        :expectedresults: The repo from an exported CV contents has been
            imported successfully.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_redhat_mix_cv(self):
        """Export CV version having Red Hat and custom repo in directory
        and Import them.

        :id: a38cf67d-563c-46f0-a263-4825b26faf2b

        :steps:

            1. Export whole CV version having mixed repos to a path accessible
               over HTTP.
            2. Import the Red Hat repository by defining the CDN URL from the
               exported HTTP URL.
            3. Import custom repo by creating new repo and setting yum repo url
               to exported HTTP url.

        :expectedresults: Both custom and Red Hat repos are imported
            successfully.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_redhat_cv_iso(self):
        """Export CV version having Red Hat contents as ISO.

        :id: 7a35b76b-046f-402b-ba0d-4336e1757b8b

        :steps: Export whole CV version having Red Hat contents as ISO.

        :expectedresults: Whole CV version contents has been exported as ISO.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_import_redhat_cv_iso(self):
        """Export CV version having Red Hat contents as ISO and Import them.

        :id: 44b3d4b7-2da2-4db0-afd7-6c696a444915

        :steps:

            1. Export whole CV version having Red Hat contents as ISO.
            2. Mount ISO to local filesystem and explore iso contents over
               HTTP.
            3. Import the Red Hat repository by defining the CDN URL from the
               exported HTTP URL.

        :expectedresults: The repo is imported successfully from exported CV
            ISO contents.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_install_package_from_imported_repos(self):
        """Install packages in client from imported repo of Downstream satellite.

        :id: a81ffb55-398d-4ad0-bcae-5ed48f504ded

        :steps:

            1. Export whole Red Hat YUM repo to a path accessible over HTTP.
            2. Import the Red Hat repository by defining the CDN URL from the
               exported HTTP URL.
            3. In downstream satellite create CV, AK with this imported repo.
            4. Register/Subscribe a client with a downstream satellite.
            5. Attempt to install a package on a client from imported repo of
               downstream.

        :expectedresults: The package is installed on client from imported repo
            of downstream satellite.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
