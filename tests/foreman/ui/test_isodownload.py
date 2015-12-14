"""Test class for ISO downloads UI"""
from robottelo.decorators import run_only_on, stubbed, tier1
from robottelo.test import UITestCase


class ISODownloadTestCase(UITestCase):
    """Test class for iso download feature"""

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_download(self):
        """@test: Downloading ISO from export

        @Feature: ISO Downloads

        @Steps:

        1. find out the location where all iso's are kept
        2. check whether a valid iso can be downloaded

        @Assert: iso file is properly downloaded on your satellite 6
        system

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_upload(self):
        """@test: Uploadng the iso successfully to the sat6 system

        @Feature: ISO Downloads

        @Steps:

        1. download the iso
        2. upload it to sat6 system

        @Assert: uploading iso to satellite6 is successful

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_mount(self):
        """@test: Mounting iso to directory accessible to satellite6 works

        @Feature: ISO Downloads

        @Steps:

        1. download the iso
        2. upload it to sat6 system
        3. mount it a local sat6 directory

        @Assert: iso is mounted to sat6 local directory

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_validate_cdn_url(self):
        """@test: Validate that cdn url to file:///path/to/mount works

        @Feature: ISO Downloads

        @Steps:

        1. after mounting the iso locally try to update the cdn url
        2. the path should be validated

        @Assert: cdn url path is validated

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_check_message(self):
        """@test: Check if proper message is displayed after successful upload

        @Feature: ISO Downloads

        @Steps:

        1. mount the iso to sat6
        2. update the cdn url with file path
        3. check if proper message is displayed

        @Assert: Asserting the message after successful upload

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_enable_repo(self):
        """@test: Enable the repositories

        @Feature: ISO Downloads

        @Steps:

        1. mount iso to directory
        2. update cdn url
        3. upload manifest
        4. try to enable redhat repositories


        @Assert: Redhat repositories are enabled

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_validate_checkboxes(self):
        """@test: Check if enabling the checkbox works

        @Feature: ISO Downloads

        @Steps:

        1. mount iso to directory
        2. update cdn url
        3. upload manifest
        4. Click the checkbox to enable redhat repositories
        5. redhat repository enabled


        @Assert: Checkbox functionality works

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_sync_repos(self):
        """@test: Sync repos to local iso's

        @Feature: ISO Downloads

        @Steps:

         1. mount iso to directory
         2. update cdn url
         3. upload manifest
         4. try to enable redhat repositories
         5. sync the repos

        @Assert: Repos are synced after upload

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_disable_repo(self):
        """@test: Disabling the repo works

        @Feature: ISO Downloads

        @Steps:

        1. mount iso to directory
        2. update cdn url
        3. upload manifest
        4. try to enable redhat repositories
        5. sync the contents
        6. try disabling the repository

        @Assert: Assert disabling the repo

        @Status: Manual

        """
