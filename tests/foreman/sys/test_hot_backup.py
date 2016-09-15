# -*- encoding: utf-8 -*-
"""Test class for ``katello-backup``

@Requirement: HotBackup

@CaseAutomation: notautomated

@CaseLevel: Acceptance

@CaseComponent: Backup

@TestType: System

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import stubbed
from robottelo.test import TestCase


class HotBackupTestCase(TestCase):
    """Implements ``katello-backup --online`` tests"""

    @classmethod
    def setUpClass(cls):
        super(HotBackupTestCase, cls).setUpClass()

    @stubbed()
    def test_positive_directory(self):
        """katello-backup with existing directory

        @id: 3f8285d5-c68b-4d84-8568-bcd7e4f7f19e

        @Steps:
            1. Populate Satellite system.
            2. Run katello-backup with existing directory
            3. Restore from backup

        @Assert: The backup and restore succeed.
        """
        pass

    @stubbed()
    def test_negative_directory(self):
        """katello-backup with non-existing directory


        @id: 946991ad-125a-4f24-a33e-ea27fce38eda

        @Steps:
            1. Populate Satellite system.
            2. Run katello-backup with non-existing directory

        @Assert: An error message is printed
        """
        pass

    @stubbed()
    def test_positive_incremental(self):
        """Make an incremental backup

        @id: a5b3536f-8365-41c7-9386-cddde588fe8c

        @Steps:
            1. Configure basic satellite system
            2. Back full backup (base)
            3. Make config change c1
            4. Run incremental backup ib1
            5. Restore base backup, verify c1 config doesnt not exist
            6. restore ib1, veirfy c1 config does exist
            7. Make config change c2
            8. run katello-backup <path_to_ib1> --incremental

        @Assert: Backup "ib1" is backed up.
        """
        pass

    @stubbed()
    def test_positive_restore_fresh_install(self):
        """Restore to a clean Satellite with no config

        @id: 2069b860-43d4-4b65-a8cd-89a8b2feafbe

        @Steps:
            1. Restore online backup
            2. Restore offline backup
            3. Restore online incremenetal backup
            4. Restore offline incremenetal backup

        @Assert: Each backup is fully restored.

        """
        pass

    @stubbed()
    def test_positive_restore(self):
        """Restore to a Satellite with config that is been updated since the backup

        @id: 03a47dec-9cd4-4cae-88ec-c19dfaa1d5ad

        @Steps:
            1. Restore online backup
            2. Restore offline backup
            3. Restore online incremenetal backup
            4. Restore offline incremental backu

        @Assert: Each backup is fully restored.

        """
        pass

    @stubbed()
    def test_positive_load_backup(self):
        """Load testing, backup

        @id: b0d7de3a-d1d5-4cb9-8041-47301b658408

        @Steps:
            1. Run a backup while the Satellite is under load

        @Assert: The backup is successful

        """
        pass

    @stubbed()
    def test_positive_load_restore(self):
        """Load testing, restore

        @id: c0347aee-48b4-45da-92ef-1e92397c5543

        @Steps:
            1. Run a restore while the Satellite is under load

        @Assert: The restore is successful.

        """
        pass

    @stubbed()
    def test_positive_pull_content(self):
        """Pull content while a backup is running.

        @id: 1026f5f5-4180-4215-acce-876dd2d09ba9

        @Steps:
            1. Populate a satellite with hosts
            2. Start a backup
            3. While backing up, have a host pull content from the satellite.

        @Assert: The backup succeeds  and the host gets the requested content.

        """
        pass
