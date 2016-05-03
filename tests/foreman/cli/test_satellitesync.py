# -*- encoding: utf-8 -*-
"""Test class for InterSatellite Sync"""

from fauxfactory import gen_string
from robottelo import manifests, ssh
from robottelo.constants import (
    ENVIRONMENT,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.cli.factory import (
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.settings import Settings
from robottelo.cli.subscription import Subscription
from robottelo.decorators import run_only_on, skip_if_not_set, stubbed, tier3
from robottelo.test import CLITestCase


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

        @Feature: Repository - Export

        @Assert: Repository was successfully exported, rpm files are present on
        satellite machine
        """
        # Create custom product and repository
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({
            'download-policy': 'immediate',
            'organization-id': self.org['id'],
            'product-id': product['id'],
        })
        repo_export_dir = '/mnt/{0}/{1}-{2}-{3}/{1}/{4}/custom/{2}/{3}'.format(
            self.export_dir,
            self.org['label'],
            product['label'],
            repo['label'],
            ENVIRONMENT,
        )

        # Export the repository
        Repository.export({'id': repo['id']})

        # Verify export directory is empty
        result = ssh.command('ls -l {0} | grep .rpm'.format(repo_export_dir))
        self.assertEqual(len(result.stdout), 0)

        # Synchronize the repository
        Repository.synchronize({'id': repo['id']})

        # Export the repository once again
        Repository.export({'id': repo['id']})

        # Verify RPMs were successfully exported
        result = ssh.command('ls -l {0} | grep .rpm'.format(repo_export_dir))
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_export_rh_product(self):
        """Export a repository from the Red Hat product

        @Feature: Repository - Export

        @Assert: Repository was successfully exported, rpm files are present on
        satellite machine
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
        repo_export_dir = (
            '/mnt/{0}/{1}-{2}-{3}/{1}/{4}/content/dist/rhel/server/6/6Server/'
            'x86_64/rhev-agent/3/os'
            .format(
                self.export_dir,
                self.org['label'],
                PRDS['rhel'].replace(' ', '_'),
                repo['label'],
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
        result = ssh.command('ls -l {0} | grep .rpm'.format(repo_export_dir))
        self.assertEqual(len(result.stdout), 0)

        # Synchronize the repository
        Repository.synchronize({'id': repo['id']})

        # Export the repository once again
        Repository.export({'id': repo['id']})

        # Verify RPMs were successfully exported
        result = ssh.command('ls -l {0} | grep .rpm'.format(repo_export_dir))
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)


class InterSatelliteSyncTestCase(CLITestCase):
    """Implements InterSatellite Sync tests in CLI"""

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_cv(self):
        """Export CV version contents in directory and Import them.

        @feature: ISS - Export Import

        @steps:

        1. Export whole CV version contents to a directory specified in
        settings.
        2. Copy exported contents to /var/www/html/pub/export directory.
        3. Import these copied contents from some other org/satellite.

        @assert:

        1. Whole CV version contents has been exported to directory
        specified in settings.
        2. All The exported contents has been imported in org/satellite.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_import_cv(self):
        """Export whole CV version contents in directory and Import nothing.

        @feature: ISS - Import

        @steps:

        1. Export whole CV version contents to a directory specified in
        settings.
        2. Don't copy exported contents to /var/www/html/pub/export directory.
        3. Attempt to import these not copied contents from some other
        org/satellite.

        @assert:

        1. Whole CV version contents has been exported to directory specified
        in settings.
        2. The exported contents are not imported due to non availability.
        3. Error is thrown for non availability of CV contents to import.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_cv(self):
        """Export whole CV version contents is aborted due to insufficient
        memory.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export whole CV version contents to a directory which
        has less memory available than contents size.

        @assert:

        1. The export CV version contents has been aborted due to insufficient
        memory.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_cv_iso(self):
        """Export CV version contents in directory as iso and Import it.

        @feature: ISS - Export Import

        @steps:

        1. Export whole CV version contents as ISO to a directory specified in
        settings.
        2. Copy exported ISO to /var/www/html/pub/export directory.
        3. Import these copied ISO from some other org/satellite.

        @assert:

        1. CV version has been exported to directory as ISO in specified in
        settings.
        2. The exported ISO has been imported in org/satellite.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_import_cv_iso(self):
        """Export whole CV version as ISO in directory and Import nothing.

        @feature: ISS - Import

        @steps:

        1. Export whole CV version as ISO to a directory specified in
        settings.
        2. Don't copy exported ISO to /var/www/html/pub/export directory.
        3. Attempt to import this not copied ISO from some other
        org/satellite.

        @assert:

        2. The exported iso is not imported due to non availability.
        3. Error is thrown for non availability of CV version ISO to import.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_cv_iso(self):
        """Export whole CV version to iso is aborted due to insufficient
        memory.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export whole CV version as iso to a directory which has
        less memory available than contents size.

        @assert:

        1. The export CV version to iso has been aborted due to insufficient
        memory.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_cv_iso_max_size(self):
        """Export whole CV version to iso is aborted due to inadequate maximum
        iso size.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export whole CV version as iso with mb size less than
        required.

        @assert:

        1. The export CV version to iso has been aborted due to maximum size is
        not enough to contain the CV version contents.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_cv_iso_max_size(self):
        """CV version exported to iso in maximum iso size.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export whole CV version as iso with mb size more than
        required.

        @assert:

        1. CV version has been exported to iso successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_cv_incremental(self):
        """Export and Import CV version contents incrementally.

        @feature: ISS - Export Import

        @steps:

        1. In upstream, Export CV version contents to a directory specified in
        settings.
        2. In downstream, Import these copied contents from some other
        org/satellite.
        3. In upstream, Add new packages to the CV.
        4. Export the CV incrementally from the last date time.
        5. In downstream, Import the CV incrementally.

        @assert:

        1. On incremental export, only the new packages are exported.
        2. New directory of incremental export with new packages is created.
        3. On incremental import, only the new packages are imported.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_import_cv_incremental(self):
        """No new incremental packages exported or imported.

        @feature: ISS - Export Import

        @steps:

        1. In upstream, Export CV version contents to a directory specified in
        settings.
        2. In downstream, Import these copied contents from some other
        org/satellite.
        3. In upstream, Don't add any new packages to the CV.
        4. Export the CV incrementally from the last date time.
        5. In downstream, Import the CV incrementally.

        @assert:

        1. An Empty packages directory created on incremental export.
        2. On incremental import, no new packages are imported.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_exported_cv_iso_dir_structure(self):
        """Exported CV in iso format respects cdn directory structure.

        @feature: ISS - Export

        @steps:

        1. Export the full CV in iso format.
        2. Mount the iso.
        3. Verify iso directory structure.

        @assert:

        1. Exported CV in iso should follow the cdn directory structure.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_repo(self):
        """Export repo in directory and Import them.

        @feature: ISS - Export Import

        @steps:

        1. Export repo to a directory specified in settings.
        2. Copy exported repo contents to /var/www/html/pub/export directory.
        3. Import these copied repo contents from some other org/satellite.

        @assert:

        1. The repo has been exported to directory specified in settings.
        2. The exported repo has been imported in org/satellite.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_import_repo(self):
        """Export repo contents in directory and Import nothing.

        @feature: ISS - Import

        @steps:

        1. Export repo to a directory specified in settings.
        2. Dont copy exported repo to /var/www/html/pub/export directory.
        3. Attempt to import this not copied repo from some other
        org/satellite.

        @assert:

        1. The repo has been exported to directory specified in settings.
        2. The exported repo are not imported due to non availability.
        3. Error is thrown for non availability of repo contents to import.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo(self):
        """Export repo is aborted due ti insufficient memory.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export repo to a directory which has less memory
        available than contents size.

        @assert:

        1. The export repo has been aborted due to insufficient memory.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_lazy_sync_repo(self):
        """Error is raised for lazy sync repo.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export repo with 'on_demand' download policy.

        @assert:

        1. An Error is raised for updating the repo download policy to
        'immediate' to be exported.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reimport_repo(self):
        """Packages missing from upstream are removed from downstream on reimport.

        @feature: ISS - Export

        @steps:

        1. From upstream Export repo fully and import it in downstream.
        2. In upstream delete some packages from repo.
        3. Re-export the full repo.
        4. In downstream, reimport the repo re-exported.

        @assert:

        1. Deleted packages from upstream are removed from downstream.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_repo_iso(self):
        """Export repo in directory as iso and Import it.

        @feature: ISS - Export Import

        @steps:

        1. Export repo as ISO to a directory specified in settings.
        2. Copy exported ISO to /var/www/html/pub/export directory.
        3. Import this copied ISO from some other org/satellite.

        @assert:

        1. repo has been exported to directory as ISO in specified in settings.
        2. The exported ISO has been imported in org/satellite.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_import_repo_iso(self):
        """Export repo as ISO in directory and Import nothing.

        @feature: ISS - Import

        @steps:

        1. Export repo as ISO to a directory specified in settings.
        2. Dont copy exported ISO to /var/www/html/pub/export directory.
        3. Attempt to import this not copied ISO from some other
        org/satellite.

        @assert:

        2. The exported iso is not imported due to non availability.
        3. Error is thrown for non availability of repo ISO to import.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo_iso(self):
        """Export repo to iso is aborted due to insufficient memory.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export repo as iso to a directory which has less memory
        available than contents size.

        @assert:

        1. The export repo to iso has been aborted due to insufficient memory.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo_iso_max_size(self):
        """Export repo to iso is aborted due to inadequate maximum iso size.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export repo as iso with mb size less than required.

        @assert:

        1. The export repo to iso has been aborted due to maximum size is not
        enough to contain the repo  contents.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_repo_iso_max_size(self):
        """Repo exported to iso with maximum iso size.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export repo as iso with mb size more than
        required.

        @assert:

        1. Repo has been exported to iso successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_repo_from_future_datetime(self):
        """Incremental export fails with future datetime.

        @feature: ISS - Export

        @steps:

        1. Export the repo incrementally from the future date time.

        @assert:

        1. Error is raised for attempting to export from future datetime.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_repo_incremental(self):
        """Export and Import repo incrementally.

        @feature: ISS - Export Import

        @steps:

        1. In upstream, Export repo to a directory specified in
        settings.
        2. In downstream, Import this repo fully.
        3. In upstream, Add new packages to the repo.
        4. Export the repo incrementally from the last date time.
        5. In downstream, Import the repo incrementally.

        @assert:

        1. On incremental export, only the new packages are exported.
        2. New directory of incremental export with new packages is created.
        3. On incremental import, only the new packages are imported.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_import_repo_incremental(self):
        """No new incremental packages exported or imported.

        @feature: ISS - Export Import

        @steps:

        1. In upstream, Export repo to a directory specified in settings.
        2. In downstream, fully Import this repo.
        3. In upstream, Don't add any new packages to the repo.
        4. Export the repo incrementally from the last date time.
        5. In downstream, Import the repo incrementally.

        @assert:

        1. An Empty packages directory created on incremental export.
        2. On incremental import, no new packages are imported.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_exported_repo_iso_dir_structure(self):
        """Exported repo in iso format respects cdn directory structure.

        @feature: ISS - Export

        @steps:

        1. Export the full repo in iso format.
        2. Mount the iso.
        3. Verify iso directory structure.

        @assert:

        1. Exported repo in iso should follow the cdn directory structure.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_kickstart_tree(self):
        """kickstart tree is exported to specified location.

        @feature: ISS - Export

        @steps:

        1. Export the full kickstart tree.
        2. Copy exported kickstart tree contents to /var/www/html/pub/export.
        3. Import above exported kickstart tree from other org/satellite.

        @assert:

        1. Whole kickstart tree contents has been exported to directory
        specified in settings.
        2. All The exported contents has been imported in org/satellite.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_import_kickstart_tree(self):
        """Export whole kickstart tree in directory and Import nothing.

        @feature: ISS - Import

        @steps:

        1. Export whole kickstart tree contents to a directory specified in
        settings.
        2. Dont copy exported contents to /var/www/html/pub/export directory.
        3. Attempt to import these not copied contents from some other
        org/satellite.

        @assert:

        1. Whole kickstart tree has been exported to directory specified
        in settings.
        2. The exported contents are not imported due to non availability.
        3. Error is thrown for non availability of kickstart tree to import.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_export_kickstart_tree(self):
        """Export whole kickstart tree contents is aborted due to insufficient
        memory.

        @feature: ISS - Export

        @steps:

        1. Attempt to Export whole kickstart tree contents to a directory which
        has less memory available than contents size.

        @assert:

        1. The export kickstart tree has been aborted due to insufficient
        memory.

        @status: Manual
        """

# Red Hat Repositories Export and Import

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_repo(self):
        """Export Red Hat YUM repo in directory.

        @feature: ISS - Export

        @steps:

        1. Export whole Red Hat YUM repo to some path.

        @assert: Whole YUM repo contents has been exported to directory
        specified in settings.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_redhat_yum_repo(self):
        """Import the exported YUM repo contents.

        @feature: ISS - Import

        @steps:

        1. Export Red Hat YUM repo to path which will be accessible over HTTP.
        2. Import the repository by defining the CDN URL the same as the
        exported HTTP URL.

        @assert: All the exported YUM repo contents are imported successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_incremental_yum_repo(self):
        """Export Red Hat YUM repo in directory incrementally.

        @feature: ISS - Export

        @steps:

        1. Export whole Red Hat YUM repo.
        2. Add some packages to the earlier exported yum repo.
        3. Incrementally export the yum repo from last exported date.

        @assert: Red Hat YUM repo contents have been exported incrementally in
        separate directory.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_redhat_incremental_yum_repo(self):
        """Import the exported YUM repo contents incrementally.

        @feature: ISS - Import

        @steps:

        1. First, Export and Import whole Red Hat YUM repo.
        2. Add some packages to the earlier exported yum repo.
        3. Incrementally export the Red Hat YUM repo from last exported date.
        4. Import the exported YUM repo contents incrementally.

        @assert: YUM repo contents have been imported incrementally.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory.

        @feature: ISS - Export

        @steps:

        1. Export whole Red Hat YUM repo as ISO.

        @assert: Whole repo contents has been exported as ISO in separate
        directory.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_redhat_yum_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory and Import.

        @feature: ISS - Import

        @steps:

        1. Export whole Red Hat YUM repo as ISO.
        2. Mount exported ISO and explore the ISO contents on HTTP.
        3. Import the repository by defining the CDN URL the same as the
        exported HTTP URL.

        @assert: All The exported repo contents in ISO has been imported
        successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_yum_incremental_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory and import incrementally.

        @feature: ISS - Export

        @steps:

        1. First, Export and Import whole Red Hat YUM repo.
        2. Add some packages to the earlier exported yum repo.
        3. Incrementally export the yum repo as ISO from last exported date.

        @assert: Repo contents have been exported as ISO incrementally in
        separate directory.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_redhat_yum_incremental_repo_iso(self):
        """Export Red Hat YUM repo as ISO in directory and import incrementally.

        @feature: ISS - Import

        @steps:

        1. First, Export and Import whole Red Hat YUM repo.
        2. Add some packages to the earlier exported yum repo.
        3. Incrementally export the yum repo as ISO from last exported date.
        4. Mount incrementally exported contents ISO.
        5. Import the repo contents incrementally.

        @assert: Repo contents have been exported as ISO and imported
        incrementally.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_cv(self):
        """Export CV version having Red Hat contents in directory.

        @feature: ISS - Export

        @steps:

        1. Export whole CV version having Red Hat contents to a directory
        specified in settings.

        @assert: Whole CV version contents has been exported to directory
        specified in settings.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_redhat_cv(self):
        """Export CV version having Red Hat contents in directory and Import
        them.

        @feature: ISS - Import

        @steps:

        1. Export whole CV version having Red Hat contents to a path accessible
        over HTTP.
        2. Import the repository by defining the CDN URL from the exported HTTP
        URL.

        @assert: The repo from an exported CV contents has been imported
        successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_redhat_mix_cv(self):
        """Export CV version having Red Hat and custom repo in directory
        and Import them.

        @feature: ISS - Import

        @steps:

        1. Export whole CV version having mixed repos to a path accessible over
        HTTP.
        2. Import the Red Hat repository by defining the CDN URL from the
        exported HTTP URL.
        3. Import custom repo by creating new repo and setting yum repo url to
        exported HTTP url.

        @assert: Both custom and Red Hat repos are imported successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_redhat_cv_iso(self):
        """Export CV version having Red Hat contents as ISO.

        @feature: ISS - Export

        @steps:

        1. Export whole CV version having Red Hat contents as ISO.

        @assert: Whole CV version contents has been exported as ISO.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_export_import_redhat_cv_iso(self):
        """Export CV version having Red Hat contents as ISO and Import them.

        @feature: ISS - Import

        @steps:

        1. Export whole CV version having Red Hat contents as ISO.
        2. Mount ISO to local filesystem and explore iso contents over HTTP.
        3. Import the Red Hat repository by defining the CDN URL from the
        exported HTTP URL.

        @assert: The repo is imported successfully from exported CV ISO
        contents.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_install_package_from_imported_repos(self):
        """Install packages in client from imported repo of Downstream satellite.

        @feature: ISS - Export Import

        @steps:

        1. Export whole Red Hat YUM repo to a path accessible over HTTP.
        3. Import the Red Hat repository by defining the CDN URL from the
        exported HTTP URL.
        4. In downstream satellite create CV, AK with this imported repo.
        5. Register/Subscribe a client with a downstream satellite.
        6. Attempt to install a package on a client from imported repo of
        downstream.

        @assert: The package is installed on client from imported repo of
        downstream satellite.

        @status: Manual
        """
