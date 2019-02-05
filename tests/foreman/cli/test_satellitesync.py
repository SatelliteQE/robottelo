# -*- encoding: utf-8 -*-
"""Test class for InterSatellite Sync

:Requirement: Satellitesync

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities

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
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.settings import Settings
from robottelo.cli.subscription import Subscription
from robottelo.constants import (
    ENVIRONMENT,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
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
    """Implements Content View Export Import tests in CLI"""

    export_base = '/var/lib/pulp/katello-export'

    @staticmethod
    def _create_cv(cv_name, repo, organization, publish=True):
        """Creates CV in organization with given name and repository"""
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
    def _enable_rhel_content(organization, sync=True):
        """Enable/Synchronize rhel content"""
        manifests.upload_manifest_locked(
            organization['id'], interface=manifests.INTERFACE_CLI)
        RepositorySet.enable({
            'basearch': 'x86_64',
            'name': REPOSET['rhva6'],
            'organization-id': organization['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
        })
        repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'organization-id': organization['id'],
            'product': PRDS['rhel'],
        })
        # Update the download policy to 'immediate'
        Repository.update({
            'download-policy': 'immediate',
            'id': repo['id'],
        })
        if sync:
            # Synchronize the repository
            Repository.synchronize({'id': repo['id']})
        repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'organization-id': organization['id'],
            'product': PRDS['rhel'],
        })
        return repo

    def set_importing_org(self, product, repo, cv):
        """Sets same CV, product and repository in importing organization as
        exporting organization

        :param str product: The product name same as exporting product
        :param str repo: The repo name same as exporting repo
        :param str cv: The cv name same as exporting cv
        """
        self.importing_org = make_org()
        self.importing_prod = make_product({
            'organization-id': self.importing_org['id'],
            'name': product
        })
        self.importing_repo = make_repository({
            'name': repo,
            'mirror-on-sync': 'no',
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

    @run_only_on('sat')
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

        :CaseLevel: System
        """
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': self.exporting_cvv_id
        })
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
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

        :CaseLevel: System
        """
        rhel_repo = ContentViewSync._enable_rhel_content(self.exporting_org)
        rhel_cv_name = gen_string('alpha')
        _, exporting_cvv_id = ContentViewSync._create_cv(
            rhel_cv_name, rhel_repo, self.exporting_org)
        ContentView.version_export({
            'export-dir': '{}'.format(self.export_base),
            'id': exporting_cvv_id
        })
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        exported_packages = Package.list({'content-view-version-id': exporting_cvv_id})
        self.assertTrue(len(exported_packages) > 0)
        imp_rhel_repo = ContentViewSync._enable_rhel_content(self.importing_org, sync=False)
        importing_cv, _ = ContentViewSync._create_cv(
            rhel_cv_name, imp_rhel_repo, self.importing_org, publish=False)
        ContentView.version_import({
            'export-tar': exported_tar,
            'organization-id': self.importing_org['id']
        })
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
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
        result = ssh.command("[ -f {0} ]".format(exported_tar))
        self.assertEqual(result.return_code, 0)
        result = ssh.command("tar -t -f {}".format(exported_tar))
        contents_tar = 'export-{cv_name}-{cvv_id}/export-{cv_name}-{cvv_id}-repos.tar'.format(
            cv_name=self.exporting_cv_name, cvv_id=self.exporting_cvv_id)
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
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
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
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
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

    @tier1
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
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
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

    @tier1
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
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
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
        exported_tar = '{0}/export-{1}-{2}.tar'.format(
            self.export_base, self.exporting_cv_name, self.exporting_cvv_id)
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

    @tier1
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


class InterSatelliteSyncTestCase(CLITestCase):
    """Implements InterSatellite Sync tests in CLI"""

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_cv_iso_max_size(self):
        """CV version exported to iso in maximum iso size.

        :id: 7ec91557-bafc-490d-b760-573a07389be5

        :steps: Attempt to Export whole CV version as iso with mb size more
            than required.

        :expectedresults: CV version has been exported to iso successfully.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo(self):
        """Export repo is aborted due ti insufficient memory.

        :id: 4bdd1183-a3a5-41a8-8a38-34c1035b64da

        :steps: Attempt to Export repo to a directory which has less memory
            available than contents size.

        :expectedresults: The export repo has been aborted due to insufficient
            memory.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_lazy_sync_repo(self):
        """Error is raised for lazy sync repo.

        :id: 296a7bde-d8af-4e4d-b673-a7c393f6f846

        :steps: Attempt to Export repo with 'on_demand' download policy.

        :expectedresults: An Error is raised for updating the repo download
            policy to 'immediate' to be exported.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo_iso(self):
        """Export repo to iso is aborted due to insufficient memory.

        :id: 028c4972-5746-463d-afd3-a1cea337ee11

        :steps: Attempt to Export repo as iso to a directory which has less
            memory available than contents size.

        :expectedresults: The export repo to iso has been aborted due to
            insufficient memory.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo_iso_max_size(self):
        """Export repo to iso is aborted due to inadequate maximum iso size.

        :id: ef2ba2ec-0ec6-4c33-9c22-e4102734eecf

        :steps: Attempt to Export repo as iso with mb size less than required.

        :expectedresults: The export repo to iso has been aborted due to
            maximum size is not enough to contain the repo  contents.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_repo_iso_max_size(self):
        """Repo exported to iso with maximum iso size.

        :id: 19626697-9c5e-49d1-8429-720881dfe73d

        :steps: Attempt to Export repo as iso with mb size more than required.

        :expectedresults: Repo has been exported to iso successfully.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo_from_future_datetime(self):
        """Incremental export fails with future datetime.

        :id: 1e8bc352-198f-4d59-b437-1b184141fab4

        :steps: Export the repo incrementally from the future date time.

        :expectedresults: Error is raised for attempting to export from future
            datetime.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

# Red Hat Repositories Export and Import

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_repo(self):
        """Export Red Hat YUM repo in directory.

        :id: 96bd5c72-6eb0-4b32-b75a-14c6ad556cc0

        :steps: Export whole Red Hat YUM repo to some path.

        :expectedresults: Whole YUM repo contents has been exported to
            directory specified in settings.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory.

        :id: e96a7a8c-9e71-4379-86e6-78177dfbf555

        :steps: Export whole Red Hat YUM repo as ISO.

        :expectedresults: Whole repo contents has been exported as ISO in
            separate directory.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_cv(self):
        """Export CV version having Red Hat contents in directory.

        :id: 3eacbd64-e81b-455e-969d-570582616c4a

        :steps: Export whole CV version having Red Hat contents to a directory
            specified in settings.

        :expectedresults: Whole CV version contents has been exported to
            directory specified in settings.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    @upgrade
    def test_positive_export_redhat_cv_iso(self):
        """Export CV version having Red Hat contents as ISO.

        :id: 7a35b76b-046f-402b-ba0d-4336e1757b8b

        :steps: Export whole CV version having Red Hat contents as ISO.

        :expectedresults: Whole CV version contents has been exported as ISO.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
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

        :caseautomation: notautomated

        :CaseLevel: System
        """
