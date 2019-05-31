"""Test class for ISO downloads UI

:Requirement: Isodownload

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier1, upgrade
from robottelo.test import UITestCase


class ISODownloadTestCase(UITestCase):
    """Test class for iso download feature"""

    @stubbed()
    @tier1
    def test_positive_download(self):
        """Downloading ISO from export

        :id: 47f20df7-f6f3-422b-b57b-3a5ef9cf62ad

        :Steps:

            1. find out the location where all iso's are kept
            2. check whether a valid iso can be downloaded

            :expectedresults: iso file is properly downloaded on your satellite
                6 system

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_upload(self):
        """Uploadng the iso successfully to the sat6 system

        :id: daf87a68-7c61-46f1-b4cc-021476080b6b

        :Steps:

            1. download the iso
            2. upload it to sat6 system

        :expectedresults: uploading iso to satellite6 is successful

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_mount(self):
        """Mounting iso to directory accessible to satellite6 works

        :id: 44d3c8fa-c01f-438c-b83e-8f6894befbbf

        :Steps:

            1. download the iso
            2. upload it to sat6 system
            3. mount it a local sat6 directory

        :expectedresults: iso is mounted to sat6 local directory

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_validate_cdn_url(self):
        """Validate that cdn url to file path works

        :id: 00157f61-1557-48a7-b7c9-6dac726eff94

        :Steps:

            1. after mounting the iso locally try to update the cdn url
            2. the path should be validated

        :expectedresults: cdn url path is validated

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_check_message(self):
        """Check if proper message is displayed after successful upload

        :id: 5ed31a26-b902-4352-900f-bb38eac95511

        :Steps:

            1. mount the iso to sat6
            2. update the cdn url with file path
            3. check if proper message is displayed

        :expectedresults: Asserting the message after successful upload

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_enable_repo(self):
        """Enable the repositories

        :id: e33e2796-0554-419f-b5a1-3e2c8e23e950

        :Steps:

            1. mount iso to directory
            2. update cdn url
            3. upload manifest
            4. try to enable redhat repositories

        :expectedresults: Redhat repositories are enabled

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_validate_checkboxes(self):
        """Check if enabling the checkbox works

        :id: 10b19405-f82e-4f95-869d-28d91cac1e6f

        :Steps:

            1. mount iso to directory
            2. update cdn url
            3. upload manifest
            4. Click the checkbox to enable redhat repositories
            5. redhat repository enabled

        :expectedresults: Checkbox functionality works

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_sync_repos(self):
        """Sync repos to local iso's

        :id: 96266438-4a52-4222-b573-96bd7cde1700

        :Steps:

            1. mount iso to directory
            2. update cdn url
            3. upload manifest
            4. try to enable redhat repositories
            5. sync the repos

        :expectedresults: Repos are synced after upload

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_disable_repo(self):
        """Disabling the repo works

        :id: 075700a7-fda0-41db-b9b7-3d6b29f63784

        :Steps:

            1. mount iso to directory
            2. update cdn url
            3. upload manifest
            4. try to enable redhat repositories
            5. sync the contents
            6. try disabling the repository

        :expectedresults: Assert disabling the repo

        :CaseAutomation: notautomated


        :CaseImportance: Critical
        """
