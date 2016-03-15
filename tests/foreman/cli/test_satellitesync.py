# -*- encoding: utf-8 -*-
"""Test class for InterSatellite Sync"""

from robottelo.decorators import run_only_on, stubbed, tier3
from robottelo.test import CLITestCase


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
