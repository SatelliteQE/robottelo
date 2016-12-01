# -*- encoding: utf-8 -*-
"""CLI tests for ``pulp-puppet-module-builder`` and Repository UI.

@Requirement: Repository

@CaseAutomation: notautomated

@CaseLevel: Integration

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from robottelo.decorators import tier2
from robottelo.test import UITestCase

# Notes for Puppet GIT puppet mirror content
#
# This feature does not allow us to actually sync/update content in a GIT repo.
# Instead, we're essentially "snapshotting" what contains in a repo at any
# given time. The ability to update the GIT puppet mirror comes is/should be
# provided by pulp itself, via script.  However, we should be able to create
# a sync schedule against the mirror to make sure it is periodically update to
# contain the latest and greatest.


class GitPuppetMirrorTestCase(UITestCase):
    """Tests for creating the hosts via CLI."""

    @tier2
    def test_positive_git_local_create(self):
        """Create repository with local git puppet mirror.

        @id: b1d3ef84-cf59-4d08-8123-abda3b2086ca

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror

        @Assert: Content source containing local GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_local_update(self):
        """Update repository with local git puppet mirror.

        @id: d8b32e52-ee3e-4c99-b47f-8726ece6ab94

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Modify details for existing puppet repo (name, etc.)

        @Assert: Content source containing local GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_local_delete(self):
        """Delete repository with local git puppet mirror.

        @id: 45b02a5d-0536-4a89-8222-3584a69363ea

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to local puppet mirror

        @Assert: Content source containing local GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_create(self):
        """Create repository with remote git puppet mirror.

        @id: 50d90ae5-9c3d-4ec7-bdd8-9c418d56e167

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror

        @Assert: Content source containing remote GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_update(self):
        """Update repository with remote git puppet mirror.

        @id: df53b612-eadb-411a-abf0-07eae3ae1059

        @CaseLevel: Integration

        @Setup: Assure remote  GIT puppet has been created and found by pulp

        @Steps:

        1.  modify details for existing puppet repo (name, etc.)

        @Assert: Content source containing remote GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_delete(self):
        """Delete repository with remote git puppet mirror.

        @id: 3971f330-2b91-44cb-89e4-350002ef0ee8

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to remote puppet mirror

        @Assert: Content source containing remote GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_sync(self):
        """Sync repository with git puppet mirror.
        @id: f46fa078-81d3-492b-86e9-c11fa97fae0b

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to sync content from mirror

        @Assert: Content is pulled down without error

        @Assert: Confirmation that various resources actually exist in
        local content repo

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_sync_with_content_change(self):
        """Sync repository with changes in git puppet mirror.
        If module changes in GIT mirror but the version in manifest
        does not change, content still pulled.

        @id: 7b0484c2-df0a-46e8-95a7-1535435e6079

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Sync a git repo and observe the contents/checksum etc. of an
            existing puppet module
        2.  Assure a puppet module in git repo has changed but the manifest
            version for this module does not change.
        3.  Using pulp script, update repo mirror and re-sync within satellite
        4.  View contents/details of same puppet module

        @Assert: Puppet module has been updated in our content, even though
        the module's version number has not changed.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_sync_schedule(self):
        """Scheduled sync of git puppet mirror.

        @id: 1e15e4ad-35e8-493f-84f5-47ad180d2a7a

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to create a scheduled sync content from mirror

        @Assert: Content is pulled down without error  on expected schedule

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_view_content(self):
        """View content in synced git puppet mirror

        @id: bb536b1b-13f6-448d-b1b2-44e2fdf93b5f

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to list contents of repo

        @Assert: Spot-checked items (filenames, dates, perhaps checksums?)
        are correct.

        @CaseAutomation: notautomated
        """
