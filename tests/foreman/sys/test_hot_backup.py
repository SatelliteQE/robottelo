# -*- encoding: utf-8 -*-
"""Test class for ``katello-backup``

@Requirement: HotBackup

@CaseAutomation: notautomated

@CaseLevel: System

@CaseComponent: Backup

@TestType: System

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import stubbed, tier3
from robottelo.test import TestCase


class HotBackupTestCase(TestCase):
    """Implements ``katello-backup --online`` tests"""

    @classmethod
    def setUpClass(cls):
        super(HotBackupTestCase, cls).setUpClass()

    @tier3()
    @stubbed()
    def test_positive_directory_exists(self):
        """katello-backup with existing directory

        @id: 3f8285d5-c68b-4d84-8568-bcd7e4f7f19e

        @Setup:

        Populate a Satellite with hosts/repos/contents

        @Steps:

        1. Create a directory (ie /tmp/backup1)
        2. Run ``katello-backup /tmp/backup1``
        3. Restore from backup

        @Assert: The backup and restore succeed.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass

    @tier3()
    @stubbed()
    def test_positive_directory_created(self):
        """katello-backup with non-existing directory


        @id: 946991ad-125a-4f24-a33e-ea27fce38eda

        @Setup:

        Populate a Satellite with hosts/repos/contents

        @Steps:

        1. Ensure the directory /tmp/backup2 does not exist.
        2. Run ``katello /tmp/backup2``

        @Assert: ``/tmp/backup2' is created and the backup is saved to it.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass

    @tier3()
    @stubbed()
    def test_positive_incremental(self):
        """Make an incremental backup

        @id: a5b3536f-8365-41c7-9386-cddde588fe8c

        @Setup:

        Populate a Satellite with hosts/repos/contents

        @Steps:

        1. Run full backup (base)
        2. Make config change c1
        3. Run incremental backup ib1
        4. Restore base backup, verify c1 config doesnt not exist
        5. restore ib1, veirfy c1 config does exist
        6. Make config change c2
        7. run katello-backup <path_to_ib1> --incremental

        @Assert: Backup "ib1" is backed up.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass

    @tier3()
    @stubbed()
    def test_positive_restore_fresh_install(self):
        """Restore to a clean Satellite with no config

        @id: 2069b860-43d4-4b65-a8cd-89a8b2feafbe

        @Setup:

        Populate a Satellite with hosts/repos/contents

        @Steps:

        1. Restore online backup
        2. Restore offline backup
        3. Restore online incremenetal backup
        4. Restore offline incremenetal backup

        @Assert: Each backup is fully restored.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass

    @tier3()
    @stubbed()
    def test_positive_restore(self):
        """Restore to a Satellite with config that has been updated since the backup

        @id: 03a47dec-9cd4-4cae-88ec-c19dfaa1d5ad

        @Steps:

        1. Restore online backup
        2. Restore offline backup
        3. Restore online incremental backup
        4. Restore offline incremental backup

        @Assert: Each backup is fully restored.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass

    @tier3()
    @stubbed()
    def test_positive_load_backup(self):
        """Load testing, backup

        @id: b0d7de3a-d1d5-4cb9-8041-47301b658408

        @Setup:

        Populate a Satellite with a large number of hosts/repos/contents

        @Steps:
        1. Create load on the Satellite by having multiple host pull content.
        2. Run a backup while the Satellite is under load
        3. Restore the backup

        @Assert: The backup is successful and the restored configuration is
        correct.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass

    @tier3()
    @stubbed()
    def test_positive_load_restore(self):
        """Load testing, restore

        @id: c0347aee-48b4-45da-92ef-1e92397c5543

        @Setup:

        Populate a Satellite with a large number of hosts/repos/content.

        @Steps:

        1. Run a backup.
        2. Run a restore.

        @Assert: The restore is successful.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass

    @stubbed()
    @tier3()
    def test_positive_pull_content(self):
        """Pull content while a backup is running.

        @id: 1026f5f5-4180-4215-acce-876dd2d09ba9

        @Setup:

        Populate a Satellite with hosts/repos/contents

        @Steps:

        1. Start a backup
        2. While backing up, have a host pull content from the satellite.

        @Assert: The backup succeeds  and the host gets the requested content.

        @CaseAutomation: notautomated

        @CaseLevel: System
        """
        pass
