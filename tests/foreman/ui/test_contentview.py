# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification

Feature details: https://fedorahosted.org/katello/wiki/ContentViews


:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import date, timedelta
from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import (
    call_entity_method_with_timeout,
    enable_rhrepo_and_fetchid,
    upload_manifest,
)
from robottelo.constants import (
    FAKE_1_YUM_REPO,
    FILTER_ERRATA_TYPE,
    FILTER_ERRATA_DATE,
    REPO_TYPE,
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_contentview,
)
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.locators.tab import tab_locators
from robottelo.ui.session import Session


class ContentViewTestCase(UITestCase):
    """Implement tests for content view via UI"""

    @classmethod
    def setUpClass(cls):
        super(ContentViewTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    # pylint: disable=too-many-arguments
    def setup_to_create_cv(self, repo_name=None, repo_url=None, repo_type=None,
                           repo_unprotected=True, rh_repo=None, org_id=None,
                           docker_upstream_name=None):
        """Create product/repo and sync it"""

        if not rh_repo:
            repo_name = repo_name or gen_string('alpha')

            # Creates new custom product via API's
            product = entities.Product(
                organization=org_id or self.organization
            ).create()
            # Creates new custom repository via API's
            repo_id = entities.Repository(
                name=repo_name,
                url=(repo_url or FAKE_1_YUM_REPO),
                content_type=(repo_type or REPO_TYPE['yum']),
                product=product,
                unprotected=repo_unprotected,
                docker_upstream_name=docker_upstream_name,
            ).create().id
        elif rh_repo:
            # Uploads the manifest and returns the result.
            with manifests.clone() as manifest:
                upload_manifest(org_id, manifest.content)
            # Enables the RedHat repo and fetches it's Id.
            repo_id = enable_rhrepo_and_fetchid(
                basearch=rh_repo['basearch'],
                # OrgId is passed as data in API hence str
                org_id=str(org_id),
                product=rh_repo['product'],
                repo=rh_repo['name'],
                reposet=rh_repo['reposet'],
                releasever=rh_repo['releasever'],
            )

        # Sync repository with custom timeout
        call_entity_method_with_timeout(
            entities.Repository(id=repo_id).sync, timeout=1500)
        return repo_id

    def _get_cv_version_environments(self, cv_version):
        """Return the list of environments promoted to the version of content
        view. The content view web page must be already opened.

        :param cv_version: The version of the current opened content view
        :type cv_version: str
        :rtype: list[str]
        """
        environment_elements = self.content_views.find_elements(
            locators.contentviews.version_environments % cv_version)
        return [env_element.text for env_element in environment_elements]

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create content views using different names

        :id: 804e51d7-f025-4ec2-a247-834afd351e89

        :expectedresults: Content views are created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_contentview(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(
                        self.content_views.search(name),
                        'Failed to find content view %s from %s org' % (
                            name, self.organization.name)
                    )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """try to create content views using invalid names

        :id: 974f2adc-b7da-4a8c-a8b5-d231b6bda1ce

        :expectedresults: content views are not created; proper error thrown
            and system handles it gracefully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            # invalid_names_list is used instead of invalid_values_list
            # because save button will not be enabled if name is blank
            for name in invalid_names_list():
                with self.subTest(name):
                    make_contentview(
                        session, org=self.organization.name, name=name)
                    self.assertTrue(
                        self.content_views.wait_until_element(
                            locators['contentviews.has_error']),
                        'No validation error found for "%s" from %s org' % (
                            name, self.organization.name))
                    self.assertIsNone(self.content_views.search(name))

    @skip_if_bug_open('bugzilla', 1478132)
    @tier1
    def test_positive_create_date_filter_rule_without_type(self):
        """Create content view erratum filter rule with start/end date and
        without type specified via API and make sure it's accessible via UI

        :id: 5a5cd6e7-8711-47c2-878d-4c0a18bf3b0e

        :BZ: 1386688

        :CaseImportance: Critical

        :expectedresults: filter rule is accessible via UI, type is set to all
            possible errata types and all the rest fields are correctly
            populated
        """
        start_date = date.today().strftime('%Y-%m-%d')
        end_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        # default date type on UI is 'updated', so we'll use different one
        date_type = FILTER_ERRATA_DATE['issued']
        content_view = entities.ContentView(
            organization=self.organization).create()
        cvf = entities.ErratumContentViewFilter(
            content_view=content_view).create()
        cvfr = entities.ContentViewFilterRule(
            end_date=end_date,
            content_view_filter=cvf,
            date_type=date_type,
            start_date=start_date,
        ).create()
        self.assertEqual(set(cvfr.types), set(FILTER_ERRATA_TYPE.values()))
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            result = self.content_views.fetch_erratum_date_range_filter_values(
                content_view.name, cvf.name)
            self.assertEqual(
                set(result['types']), set(FILTER_ERRATA_TYPE.values()))
            self.assertEqual(result['date_type'], date_type)
            self.assertEqual(result['start_date'], start_date)
            self.assertEqual(result['end_date'], end_date)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update content views name to valid one.

        :id: 7d8eb36a-536e-49dc-9eb4-a5885ec77819

        :expectedresults: Content view is updated successfully and has proper
            name

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_contentview(
                session,
                org=self.organization.name,
                name=name,
                description=gen_string('alpha', 15),
            )
            self.assertIsNotNone(self.content_views.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.content_views.update(name, new_name)
                    self.assertIsNotNone(self.content_views.search(new_name))
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Try to update content views name to invalid one.

        :id: 211c319f-802a-4407-9c16-205a82d4afca

        :expectedresults: Content View is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_contentview(
                session, org=self.organization.name, name=name)
            self.assertIsNotNone(self.content_views.search(name))
            # invalid_names_list is used instead of invalid_values_list
            # because save button will not be enabled if name is blank
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.content_views.update(name, new_name)
                    self.assertIsNotNone(self.content_views.wait_until_element(
                        common_locators['alert.error_sub_form']))
                    self.assertIsNone(self.content_views.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Update content views description to valid one.

        :id: f5e46a3b-c317-4575-9c66-ef1da1926f66

        :expectedresults: Content view is updated successfully and has proper
            description

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 8)
        desc = gen_string('alpha', 15)
        with Session(self) as session:
            make_contentview(
                session,
                org=self.organization.name,
                name=name,
                description=desc,
            )
            self.assertIsNotNone(self.content_views.search(name))
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    self.content_views.update(name, new_description=new_desc)
                    self.content_views.search_and_click(name)
                    self.content_views.click(
                        tab_locators['contentviews.tab_details'])
                    self.assertEqual(
                        self.content_views.wait_until_element(
                            locators['contentviews.fetch_description']).text,
                        new_desc
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete content views

        :id: bcea6ef0-bc25-4cc7-9c0c-3591bb8810e5

        :expectedresults: Content view can be deleted and no longer appears in
            UI

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_contentview(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(
                        self.content_views.search(name),
                        'Failed to find content view %s from %s org' % (
                            name, self.organization.name)
                    )
                    self.content_views.delete(name)

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_promote_via_dynflow(self):
        """attempt to restart a promotion

        :id: c7f4e673-5164-417f-a072-1cc51d176780

        :steps:
            1. (Somehow) cause a CV promotion to fail.  Not exactly sure how
                yet.
            2. Via Dynflow, restart promotion

        :expectedresults: Promotion is restarted.

        :caseautomation: notautomated


        :CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_publish_via_dynflow(self):
        """attempt to restart a publish

        :id: d7a1204f-5d7c-4978-bb78-f366786d006a

        :steps:
            1. (Somehow) cause a CV publish  to fail.  Not exactly sure how
                yet.
            2. Via Dynflow, restart publish

        :expectedresults: Publish is restarted.

        :caseautomation: notautomated


        :CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_env_with_host_registered(self):
        """Remove promoted content view version from environment that is used
        in association of an Activation key and content-host registration.

        :id: a8ca3de1-3f79-4029-8033-00315b6b854f

        :Steps:

            1. Create a content view cv1
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
                -> QE
            5. Create an Activation key with the QE environment
            6. Register a content-host using the Activation key
            7. Remove the content view cv1 version from QE environment.  The
                remove environment wizard should propose to replace the current
                QE environment of cv1 by an other (as QE environment of cv1 is
                attached to a content-host), choose DEV and content view cv1 as
                a replacement for Content-host and for Activation key.
            8. Refresh content-host subscription

        :expectedresults:

            1. Activation key exists
            2. Content-host exists
            3. QE environment of cv1 was replaced by DEV environment of cv1 in
                activation key
            4. QE environment of cv1 was replaced by DEV environment of cv1 in
                content-host
            5. At content-host some package from cv1 is installable

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_delete_cv_multi_env_promoted_with_host_registered(self):
        """Delete published content view with version promoted to multiple
         environments, with one of the environments used in association of an
         Activation key and content-host registration.

        :id: 73453c99-8f34-413d-8f95-e4a2f4c58a00

        :Steps:

            1. Create two content view cv1 and cv2
            2. Add a yum repo and a puppet module to both content views
            3. Publish the content views
            4. Promote the content views to multiple environment Library -> DEV
                -> QE
            5. Create an Activation key with the QE environment and cv1
            6. Register a content-host using the Activation key
            7. Delete the content view cv1.  The delete content view wizard
                should propose to replace the current QE environment of cv1 by
                an other (as QE environment of cv1 is attached to a
                content-host), choose DEV and content view cv2 as a replacement
                for Content-host and for Activation key.
            8. Refresh content-host subscription

        :expectedresults:

            1. The content view cv1 doesn't exist
            2. Activation key exists
            3. Content-host exists
            4. QE environment of cv1 was replaced by DEV environment of cv2 in
                activation key
            5. QE environment of cv1 was replaced by DEV environment of cv2 in
                content-host
            6. At content-host some package from cv2 is installable

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_multi_env_capsule_scenario(self):
        """Remove promoted content view version from multiple environment,
        with satellite setup to use capsule

        :id: ba731272-66e6-461e-8e9d-564b4092a92d

        :Steps:

            1. Create a content view
            2. Setup satellite to use a capsule and to sync all lifecycle
                environments
            3. Add a yum repo, puppet module and a docker repo to the content
                view
            4. Publish the content view
            5. Promote the content view to multiple environment Library -> DEV
                -> QE -> PROD
            6. Make sure the capsule is updated (content synchronization may be
                applied)
            7. Disconnect the capsule
            8. Remove the content view version from Library and DEV
                environments and assert successful completion
            9. Bring the capsule back online and assert that the task is
                completed in capsule
            10. Make sure the capsule is updated (content synchronization may
                be applied)

        :expectedresults: content view version in capsule is removed from
            Library and DEV and exists only in QE and PROD

        :caseautomation: notautomated

        :CaseLevel: System
        """
        # Note: This test case requires complete external capsule
        #  configuration.

    @stubbed()
    @tier2
    def test_positive_arbitrary_file_repo_addition(self):
        """Check a File Repository with Arbitrary File can be added to a
        Content View

        :id: 3837799a-1041-44b1-88b5-6f34c118e3a9

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)

        :Steps:
            1. Add the FR to the CV

        :expectedresults: Check FR is added to CV

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_arbitrary_file_repo_removal(self):
        """Check a File Repository with Arbitrary File can be removed from a
        Content View

        :id: f37f7013-569d-4318-95ec-b9fd1111e62d

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV

        :Steps:
            1. Remove the FR from the CV

        :expectedresults: Check FR is removed from CV

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    def test_positive_arbitrary_file_sync_over_capsule(self):
        """Check a File Repository with Arbitrary File can be added to a
        Content View is synced throughout capsules

        :id: ec56b501-daad-4757-a01a-2aec20ed1e2c

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV
            5. Create a Capsule
            6. Connect the Capsule with Satellite/Foreman host

        :Steps:
            1. Start synchronization

        :expectedresults: Check CV with FR is synced over Capsule

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_positive_arbitrary_file_repo_promotion(self):
        """Check arbitrary files availability on Environment after Content
        View promotion

        :id: 1ea04f8d-3341-4d6c-b863-1a96dcebd830

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV
            5. Create an Environment

        :Steps:
            1. Promote the CV to the Environment

        :expectedresults: Check arbitrary files from FR is available on
            environment

        :caseautomation: notautomated

        :CaseLevel: Integration
        """
