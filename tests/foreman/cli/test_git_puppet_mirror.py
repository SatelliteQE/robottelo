# -*- encoding: utf-8 -*-
"""CLI tests for ``pulp-puppet-module-builder`` and ``hammer repository``.

@Requirement: Repository

@CaseAutomation: notautomated

@CaseLevel: Integration

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from robottelo.decorators import tier2
from robottelo.test import CLITestCase

# Notes for Puppet GIT puppet mirror content
#
# This feature does not allow us to actually sync/update content in a GIT repo.
# Instead, we're essentially "snapshotting" what contains in a repo at any
# given time. The ability to update the GIT puppet mirror comes is/should be
# provided by pulp itself, via script.  However, we should be able to create
# a sync schedule against the mirror to make sure it is periodically update to
# contain the latest and greatest.


class GitPuppetMirrorTestCase(CLITestCase):
    """Tests for creating the hosts via CLI."""

    @tier2
    def test_positive_git_local_create(self):
        """Create repository with local git puppet mirror.

        @id: 89211cd5-82b8-4391-b729-a7502e57f824

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror via cli

        @Assert: Content source containing local GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_local_update(self):
        """Update repository with local git puppet mirror.

        @id: 341f40f2-3501-4754-9acf-7cda1a61f7db

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Modify details for existing puppet repo (name, etc.) via cli

        @Assert: Content source containing local GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_local_delete(self):
        """Delete repository with local git puppet mirror.

        @id: a243f5bb-5186-41b3-8e8a-07d5cc784ccd

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to local puppet mirror via cli

        @Assert: Content source containing local GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_create(self):
        """Create repository with remote git puppet mirror.

        @id: 8582529f-3112-4b49-8d8f-f2bbf7dceca7

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror via cli

        @Assert: Content source containing remote GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_update(self):
        """Update repository with remote git puppet mirror.

        @id: 582c50b3-3b90-4244-b694-97642b1b13a9

        @CaseLevel: Integration

        @Setup: Assure remote  GIT puppet has been created and found by pulp

        @Steps:

        1.  modify details for existing puppet repo (name, etc.) via cli

        @Assert: Content source containing remote GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_remote_delete(self):
        """Delete repository with remote git puppet mirror.

        @id: 0a23f969-b202-4c6c-b12e-f651a0b7d049

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to remote puppet mirror via cli

        @Assert: Content source containing remote GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_sync(self):
        """Sync repository with git puppet mirror.
        @id: a46c16bd-0986-48db-8e62-aeb3907ba4d2

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to sync content from mirror via cli

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

        @id: 7d9519ca-8660-4014-8e0e-836594891c0c

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

        @id: 0d58d180-9836-4524-b608-66b67f9cab12

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to create a scheduled sync content from mirror, via cli

        @Assert: Content is pulled down without error  on expected schedule

        @CaseAutomation: notautomated
        """

    @tier2
    def test_positive_git_view_content(self):
        """View content in synced git puppet mirror

        @id: 02f06092-dd6c-49fa-be9f-831e52476e41

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to list contents of repo via cli

        @Assert: Spot-checked items (filenames, dates, perhaps checksums?)
        are correct.

        @CaseAutomation: notautomated
        """
