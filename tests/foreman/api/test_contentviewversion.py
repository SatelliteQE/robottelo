"""Unit tests for the ``content_view_versions`` paths.

:Requirement: Contentviewversion

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import DEFAULT_CV
from robottelo.constants import ENVIRONMENT
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.constants import REPO_TYPE
from robottelo.constants import ZOO_CUSTOM_GPG_KEY
from robottelo.constants.repos import FAKE_0_PUPPET_REPO
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.helpers import get_data_file
from robottelo.helpers import read_data_file
from robottelo.test import APITestCase


class ContentViewVersionCreateTestCase(APITestCase):
    """Tests for content view version creation."""

    @classmethod
    def setUpClass(cls):
        """Single organization for all tests"""
        super().setUpClass()
        cls.org = entities.Organization().create()

    def setUp(self):
        """Init content view with repo per each test"""
        super().setUp()
        self.content_view = entities.ContentView(organization=self.org).create()

    @pytest.mark.tier2
    def test_positive_create(self):
        """Create a content view version.

        :id: 627c84b3-e3f1-416c-a09b-5d2200d6429f

        :expectedresults: Content View Version is created.

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Fetch content view for latest information
        cv = self.content_view.read()
        # No versions should be available yet
        self.assertEqual(len(cv.version), 0)

        # Publish existing content view
        cv.publish()
        # Fetch it again
        cv = cv.read()
        self.assertGreater(len(cv.version), 0)

    @pytest.mark.tier2
    def test_negative_create(self):
        """Create content view version using the 'Default Content View'.

        :id: 0afd49c6-f3a4-403e-9929-849f51ffa922

        :expectedresults: Content View Version is not created

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # The default content view cannot be published
        cv = entities.ContentView(organization=self.org, name=DEFAULT_CV).search()
        # There should be only 1 record returned
        self.assertEqual(len(cv), 1)
        with self.assertRaises(HTTPError):
            cv[0].publish()


class ContentViewVersionPromoteTestCase(APITestCase):
    """Tests for content view version promotion."""

    @classmethod
    def setUpClass(cls):
        """Create some entities for all tests."""
        super().setUpClass()
        cls.org = entities.Organization().create()
        cls.lce1 = entities.LifecycleEnvironment(organization=cls.org).create()
        cls.lce2 = entities.LifecycleEnvironment(organization=cls.org, prior=cls.lce1).create()
        default_cv = entities.ContentView(organization=cls.org, name=DEFAULT_CV).search()
        # There should be only 1 record returned
        assert len(default_cv) == 1
        # There should be only 1 version
        assert len(default_cv[0].version) == 1
        cls.default_cv = default_cv[0].version[0].read()

    @pytest.mark.tier2
    def test_positive_promote_valid_environment(self):
        """Promote a content view version to 'next in sequence'
        lifecycle environment.

        :id: f205ca06-8ab5-4546-83bd-deac4363d487

        :expectedresults: Promotion succeeds.

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        # Create a new content view...
        cv = entities.ContentView(organization=self.org).create()
        # ... and promote it.
        cv.publish()
        # Refresh the entity
        cv = cv.read()
        # Check that we have a new version
        self.assertEqual(len(cv.version), 1)
        version = cv.version[0].read()
        # Assert that content view version is found in 1 lifecycle
        # environments (i.e. 'Library')
        self.assertEqual(len(version.environment), 1)
        # Promote it to the next 'in sequence' lifecycle environment
        promote(version, self.lce1.id)
        # Assert that content view version is found in 2 lifecycle
        # environments.
        version = version.read()
        self.assertEqual(len(version.environment), 2)

    @pytest.mark.tier2
    def test_positive_promote_out_of_sequence_environment(self):
        """Promote a content view version to a lifecycle environment
        that is 'out of sequence'.

        :id: e88405de-843d-4279-9d81-cedaab7c23cf

        :expectedresults: The promotion succeeds.

        :CaseLevel: Integration
        """
        # Create a new content view...
        cv = entities.ContentView(organization=self.org).create()
        # ... and publish it.
        cv.publish()
        # Refresh the entity
        cv = cv.read()
        # Check that we have a new version
        self.assertEqual(len(cv.version), 1)
        version = cv.version[0].read()
        # The immediate lifecycle is lce1, not lce2
        promote(version, self.lce2.id, force=True)
        # Assert that content view version is found in 2 lifecycle
        # environments.
        version = version.read()
        self.assertEqual(len(version.environment), 2)

    @pytest.mark.tier2
    def test_negative_promote_valid_environment(self):
        """Promote the default content view version.

        :id: cd4f3c3d-93c5-425f-bc3b-d1ac17696a4a

        :expectedresults: The promotion fails.

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        with self.assertRaises(HTTPError):
            promote(self.default_cv, self.lce1.id)

    @pytest.mark.tier2
    def test_negative_promote_out_of_sequence_environment(self):
        """Promote a content view version to a lifecycle environment
        that is 'out of sequence'.

        :id: 621d1bb6-92c6-4209-8369-6ea14a4c8a01

        :expectedresults: The promotion fails.

        :CaseLevel: Integration
        """
        # Create a new content view...
        cv = entities.ContentView(organization=self.org).create()
        # ... and publish it.
        cv.publish()
        # Refresh the entity
        cv = cv.read()
        # Check that we have a new version
        self.assertEqual(len(cv.version), 1)
        version = cv.version[0].read()
        # The immediate lifecycle is lce1, not lce2
        with self.assertRaises(HTTPError):
            promote(version, self.lce2.id)


class ContentViewVersionDeleteTestCase(APITestCase):
    """Tests for content view version promotion."""

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_delete(self):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'delete_from_environment' command and delete content view version from
        that content view. Add repository and gpg key to initial content view
        for better coverage

        :id: 066dec47-c942-4c01-8956-359c8b23a6d4

        :expectedresults: Content version deleted successfully

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        key_content = read_data_file(ZOO_CUSTOM_GPG_KEY)
        org = entities.Organization().create()
        gpgkey = entities.GPGKey(content=key_content, organization=org).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(organization=org).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(gpg_key=gpgkey, product=product, url=FAKE_1_YUM_REPO).create()
        # sync repository
        repo.sync()
        # Create content view
        content_view = entities.ContentView(organization=org).create()
        # Associate repository to new content view
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        # Get published content-view version id
        self.assertEqual(len(content_view.version), 1)
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 1)
        # Delete the content-view version from selected env
        content_view.delete_from_environment(cvv.environment[0].id)
        # Delete the version
        content_view.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(content_view.read().version), 0)

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_delete_non_default(self):
        """Create content view and publish and promote it to new
        environment. After that try to disassociate content view from 'Library'
        and one more non-default environments through 'delete_from_environment'
        command and delete content view version from that content view.

        :id: 95bb973c-ebec-4a72-a1b6-ad28b66bd11b

        :expectedresults: Content view version deleted successfully

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.version[0].read().environment), 1)
        lce = entities.LifecycleEnvironment(organization=org).create()
        promote(content_view.version[0], lce.id)
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 2)
        # Delete the content-view version from selected environments
        for env in reversed(cvv.environment):
            content_view.delete_from_environment(env.id)
        content_view.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(content_view.read().version), 0)

    @pytest.mark.upgrade
    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_delete_composite_version(self):
        """Create composite content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'delete_from_environment' command and delete content view version from
        that content view. Add repository to initial content view
        for better coverage.

        :id: b5bb547e-0174-464c-b974-0254d372cdd6

        :expectedresults: Content version deleted successfully

        :CaseLevel: Integration

        :BZ: 1276479
        """
        org = entities.Organization().create()
        # Create and publish product/repository
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product, url=FAKE_1_YUM_REPO).create()
        repo.sync()
        # Create and publish content views
        content_view = entities.ContentView(organization=org, repository=[repo]).create()
        content_view.publish()
        # Create and publish composite content view
        composite_cv = entities.ContentView(
            organization=org, composite=True, component=[content_view.read().version[0]]
        ).create()
        composite_cv.publish()
        composite_cv = composite_cv.read()
        # Get published content-view version id
        self.assertEqual(len(composite_cv.version), 1)
        cvv = composite_cv.version[0].read()
        self.assertEqual(len(cvv.environment), 1)
        # Delete the content-view version from selected env
        composite_cv.delete_from_environment(cvv.environment[0].id)
        # Delete the version
        composite_cv.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(composite_cv.read().version), 0)

    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_delete_with_puppet_content(self):
        """Delete content view version with puppet module content

        :id: cae1164c-6608-4e19-923c-936e75ed807b

        :steps:
            1. Create a lifecycle environment
            2. Create a content view
            3. Add a puppet module to content view
            4. Publish the content view
            5. Promote the content view to lifecycle environment
            6. Remove the content view versions from all lifecycle environments
            7. Delete the content view version

        :expectedresults: Content view version deleted successfully

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lce_library = (
            entities.LifecycleEnvironment(organization=org, name=ENVIRONMENT).search()[0].read()
        )
        lce = entities.LifecycleEnvironment(organization=org, prior=lce_library).create()
        product = entities.Product(organization=org).create()
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO, content_type=REPO_TYPE['puppet'], product=product
        ).create()
        puppet_repo.sync()
        # create a content view and add the yum repo to it
        content_view = entities.ContentView(organization=org).create()
        # get a random puppet module
        puppet_module = random.choice(content_view.available_puppet_modules()['results'])
        # add the puppet module to content view
        entities.ContentViewPuppetModule(
            author=puppet_module['author'], name=puppet_module['name'], content_view=content_view
        ).create()
        # publish the content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view_version = content_view.version[0].read()
        self.assertEqual(len(content_view_version.environment), 1)
        lce_library = entities.LifecycleEnvironment(
            id=content_view_version.environment[0].id
        ).read()
        self.assertEqual(lce_library.name, ENVIRONMENT)
        # promote content view version to the created lifecycle environment
        promote(content_view_version, lce.id)
        content_view_version = content_view_version.read()
        self.assertEqual(
            {lce_library.id, lce.id}, {lce.id for lce in content_view_version.environment}
        )
        # remove the content view versions from all lifecycle environments
        for env in (lce_library, lce):
            content_view.delete_from_environment(env.id)
        content_view_version = content_view_version.read()
        self.assertEqual(len(content_view_version.environment), 0)
        # delete the content view version
        content_view_version.delete()
        self.assertEqual(len(content_view.read().version), 0)

    @pytest.mark.tier2
    def test_negative_delete(self):
        """Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        :id: 21c35aae-2f9c-4679-b3ba-7cd9182bd880

        :expectedresults: Content view version is not deleted

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        with self.assertRaises(HTTPError):
            content_view.version[0].delete()
        # Make sure that content view version is still present
        self.assertEqual(len(content_view.read().version), 1)

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_renamed_cv_version_from_default_env(self):
        """Remove version of renamed content view from Library environment

        :id: 7d5961d0-6a9a-4610-979e-cbc4ddbc50ca

        :Steps:

            1. Create a content view
            2. Add a yum repo to the content view
            3. Publish the content view
            4. Rename the content view
            5. remove the published version from Library environment

        :expectedresults: content view version is removed from Library
            environment

        :CaseLevel: Integration
        """
        new_name = gen_string('alpha')
        org = entities.Organization().create()
        # create yum product and repo
        product = entities.Product(organization=org).create()
        yum_repo = entities.Repository(url=FAKE_1_YUM_REPO, product=product).create()
        yum_repo.sync()
        # create a content view and add to it the yum repo
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        # publish the content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view_version = content_view.version[0].read()
        self.assertEqual(len(content_view_version.environment), 1)
        lce_library = entities.LifecycleEnvironment(
            id=content_view_version.environment[0].id
        ).read()
        # ensure that the content view version is promoted to the Library
        # lifecycle environment
        self.assertEqual(lce_library.name, ENVIRONMENT)
        # rename the content view
        content_view.name = new_name
        content_view.update(['name'])
        self.assertEqual(content_view.name, new_name)
        # delete the content view version from Library environment
        content_view.delete_from_environment(lce_library.id)
        # assert that the content view version does not exist in Library
        # environment
        self.assertEqual(len(content_view_version.read().environment), 0)

    @pytest.mark.tier2
    def test_positive_remove_qe_promoted_cv_version_from_default_env(self):
        """Remove QE promoted content view version from Library environment

        :id: c7795762-93bd-419c-ac49-d10dc26b842b

        :Steps:

            1. Create a content view
            2. Add docker repo(s) to it
            3. Publish content view
            4. Promote the content view version to multiple environments
                Library -> DEV -> QE
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE and not in
            Library

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lce_dev = entities.LifecycleEnvironment(organization=org).create()
        lce_qe = entities.LifecycleEnvironment(organization=org, prior=lce_dev).create()
        product = entities.Product(organization=org).create()
        docker_repo = entities.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=product,
            url=CONTAINER_REGISTRY_HUB,
        ).create()
        docker_repo.sync()
        # create a content view and add to it the docker repo
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [docker_repo]
        content_view = content_view.update(['repository'])
        # publish the content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view_version = content_view.version[0].read()
        self.assertEqual(len(content_view_version.environment), 1)
        lce_library = entities.LifecycleEnvironment(
            id=content_view_version.environment[0].id
        ).read()
        self.assertEqual(lce_library.name, ENVIRONMENT)
        # promote content view version to DEV QE lifecycle environments
        for lce in [lce_dev, lce_qe]:
            promote(content_view_version, lce.id)
        self.assertEqual(
            {lce_library.id, lce_dev.id, lce_qe.id},
            {lce.id for lce in content_view_version.read().environment},
        )
        # remove the content view version from Library environment
        content_view.delete_from_environment(lce_library.id)
        # assert that the content view version does not exist in Library
        # environment
        self.assertEqual(
            {lce_dev.id, lce_qe.id}, {lce.id for lce in content_view_version.read().environment}
        )

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_prod_promoted_cv_version_from_default_env(self):
        """Remove PROD promoted content view version from Library environment

        :id: 24911876-7c2a-4a12-a3aa-98051dfda29d

        :Steps:

            1. Create a content view
            2. Add yum repositories, puppet modules, docker repositories to CV
            3. Publish content view
            4. Promote the content view version to multiple environments
                Library -> DEV -> QE -> PROD
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE, PROD and
            not in Library

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lce_dev = entities.LifecycleEnvironment(organization=org).create()
        lce_qe = entities.LifecycleEnvironment(organization=org, prior=lce_dev).create()
        lce_prod = entities.LifecycleEnvironment(organization=org, prior=lce_qe).create()
        product = entities.Product(organization=org).create()
        yum_repo = entities.Repository(url=FAKE_1_YUM_REPO, product=product).create()
        yum_repo.sync()
        docker_repo = entities.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=product,
            url=CONTAINER_REGISTRY_HUB,
        ).create()
        docker_repo.sync()
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO, content_type='puppet', product=product
        ).create()
        puppet_repo.sync()
        # create a content view and add to it the yum and docker repos
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [yum_repo, docker_repo]
        content_view = content_view.update(['repository'])
        # get a random puppet module and add it to content view
        puppet_module = random.choice(content_view.available_puppet_modules()['results'])
        entities.ContentViewPuppetModule(
            author=puppet_module['author'], name=puppet_module['name'], content_view=content_view
        ).create()
        # publish the content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view_version = content_view.version[0].read()
        self.assertEqual(len(content_view_version.environment), 1)
        lce_library = entities.LifecycleEnvironment(
            id=content_view_version.environment[0].id
        ).read()
        self.assertEqual(lce_library.name, ENVIRONMENT)
        # promote content view version to DEV QE PROD lifecycle environments
        for lce in [lce_dev, lce_qe, lce_prod]:
            promote(content_view_version, lce.id)
        self.assertEqual(
            {lce_library.id, lce_dev.id, lce_qe.id, lce_prod.id},
            {lce.id for lce in content_view_version.read().environment},
        )
        # remove the content view version from Library environment
        content_view.delete_from_environment(lce_library.id)
        # assert that the content view version exists only in DEV QE PROD and
        # not in Library environment
        self.assertEqual(
            {lce_dev.id, lce_qe.id, lce_prod.id},
            {lce.id for lce in content_view_version.read().environment},
        )

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_cv_version_from_env(self):
        """Remove promoted content view version from environment

        :id: 17cf18bf-09d5-4641-b0e0-c50e628fa6c8

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> STAGE -> PROD
            5. remove the content view version from PROD environment
            6. Assert: content view version exists only in Library, DEV, QE,
               STAGE and not in PROD
            7. Promote again from STAGE -> PROD

        :expectedresults: Content view version exist in Library, DEV, QE,
            STAGE, PROD

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lce_dev = entities.LifecycleEnvironment(organization=org).create()
        lce_qe = entities.LifecycleEnvironment(organization=org, prior=lce_dev).create()
        lce_stage = entities.LifecycleEnvironment(organization=org, prior=lce_qe).create()
        lce_prod = entities.LifecycleEnvironment(organization=org, prior=lce_stage).create()
        product = entities.Product(organization=org).create()
        yum_repo = entities.Repository(url=FAKE_1_YUM_REPO, product=product).create()
        yum_repo.sync()
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO, content_type='puppet', product=product
        ).create()
        puppet_repo.sync()
        # create a content view and add to it the yum repo
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        # get a random puppet module and add it to content view
        puppet_module = random.choice(content_view.available_puppet_modules()['results'])
        entities.ContentViewPuppetModule(
            author=puppet_module['author'], name=puppet_module['name'], content_view=content_view
        ).create()
        # publish the content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view_version = content_view.version[0].read()
        self.assertEqual(len(content_view_version.environment), 1)
        lce_library = entities.LifecycleEnvironment(
            id=content_view_version.environment[0].id
        ).read()
        self.assertEqual(lce_library.name, ENVIRONMENT)
        # promote content view version to DEV QE STAGE PROD lifecycle
        # environments
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            promote(content_view_version, lce.id)
        self.assertEqual(
            {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id},
            {lce.id for lce in content_view_version.read().environment},
        )
        # remove the content view version from Library environment
        content_view.delete_from_environment(lce_prod.id)
        # assert that the content view version exists only in Library DEV QE
        # STAGE and not in PROD environment
        self.assertEqual(
            {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id},
            {lce.id for lce in content_view_version.read().environment},
        )
        # promote content view version to PROD environment again
        promote(content_view_version, lce_prod.id)
        self.assertEqual(
            {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id},
            {lce.id for lce in content_view_version.read().environment},
        )

    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_remove_cv_version_from_multi_env(self):
        """Remove promoted content view version from multiple environment

        :id: 18b86a68-8e6a-43ea-b95e-188fba125a26

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
               Library -> DEV -> QE -> STAGE -> PROD
            5. Remove content view version from QE, STAGE and PROD

        :expectedresults: Content view version exists only in Library, DEV

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        lce_dev = entities.LifecycleEnvironment(organization=org).create()
        lce_qe = entities.LifecycleEnvironment(organization=org, prior=lce_dev).create()
        lce_stage = entities.LifecycleEnvironment(organization=org, prior=lce_qe).create()
        lce_prod = entities.LifecycleEnvironment(organization=org, prior=lce_stage).create()
        product = entities.Product(organization=org).create()
        yum_repo = entities.Repository(url=FAKE_1_YUM_REPO, product=product).create()
        yum_repo.sync()
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO, content_type='puppet', product=product
        ).create()
        puppet_repo.sync()
        # create a content view and add to it the yum repo
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        # get a random puppet module and add it to content view
        puppet_module = random.choice(content_view.available_puppet_modules()['results'])
        entities.ContentViewPuppetModule(
            author=puppet_module['author'], name=puppet_module['name'], content_view=content_view
        ).create()
        # publish the content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view_version = content_view.version[0].read()
        self.assertEqual(len(content_view_version.environment), 1)
        lce_library = entities.LifecycleEnvironment(
            id=content_view_version.environment[0].id
        ).read()
        self.assertEqual(lce_library.name, ENVIRONMENT)
        # promote content view version to DEV QE STAGE PROD lifecycle
        # environments
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            promote(content_view_version, lce.id)
        self.assertEqual(
            {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id},
            {lce.id for lce in content_view_version.read().environment},
        )
        # remove the content view version from QE STAGE and PROD environments
        for lce in [lce_qe, lce_stage, lce_prod]:
            content_view.delete_from_environment(lce.id)
        # assert that the content view version exists only in Library and DEV
        # environments
        self.assertEqual(
            {lce_library.id, lce_dev.id},
            {lce.id for lce in content_view_version.read().environment},
        )

    @pytest.mark.upgrade
    @pytest.mark.tier2
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_delete_cv_promoted_to_multi_env(self):
        """Delete published content view with version promoted to multiple
         environments

        :id: c164bd97-e710-4a5a-9c9f-657e6bed804b

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment
               Library -> DEV -> QE -> STAGE -> PROD
            5. Delete the content view, this should delete the content with all
               it's published/promoted versions from all environments

        :expectedresults: The content view doesn't exists

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        lce_dev = entities.LifecycleEnvironment(organization=org).create()
        lce_qe = entities.LifecycleEnvironment(organization=org, prior=lce_dev).create()
        lce_stage = entities.LifecycleEnvironment(organization=org, prior=lce_qe).create()
        lce_prod = entities.LifecycleEnvironment(organization=org, prior=lce_stage).create()
        product = entities.Product(organization=org).create()
        yum_repo = entities.Repository(url=FAKE_1_YUM_REPO, product=product).create()
        yum_repo.sync()
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO, content_type='puppet', product=product
        ).create()
        puppet_repo.sync()
        # create a content view and add to it the yum repo
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        # get a random puppet module and add it to content view
        puppet_module = random.choice(content_view.available_puppet_modules()['results'])
        entities.ContentViewPuppetModule(
            author=puppet_module['author'], name=puppet_module['name'], content_view=content_view
        ).create()
        # publish the content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        content_view_version = content_view.version[0].read()
        self.assertEqual(len(content_view_version.environment), 1)
        lce_library = entities.LifecycleEnvironment(
            id=content_view_version.environment[0].id
        ).read()
        self.assertEqual(lce_library.name, ENVIRONMENT)
        # promote content view version to DEV QE STAGE PROD lifecycle
        # environments
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            promote(content_view_version, lce.id)
        content_view_version = content_view_version.read()
        self.assertEqual(
            {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id},
            {lce.id for lce in content_view_version.environment},
        )
        # remove content view version from all lifecycle environments
        for lce in content_view_version.environment:
            content_view.delete_from_environment(lce.id)
        # delete the content view
        content_view.delete()
        with self.assertRaises(HTTPError):
            content_view.read()

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_remove_cv_version_from_env_with_host_registered(self):
        """Remove promoted content view version from environment that is used
        in association of an Activation key and content-host registration.

        :id: a5b9ba8b-80e6-4435-bc0a-041b3fda227c

        :Steps:

            1. Create a content view cv1
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
               -> QE
            5. Create an Activation key with the QE environment
            6. Register a content-host using the Activation key
            7. Remove the content view cv1 version from QE environment.  Note -
               prior removing replace the current QE environment of cv1 by DEV
               and content view cv1 for Content-host and for Activation key.
            8. Refresh content-host subscription

        :expectedresults:

            1. Activation key exists
            2. Content-host exists
            3. QE environment of cv1 was replaced by DEV environment of cv1 in
               activation key
            4. QE environment of cv1 was replaced by DEV environment of cv1 in
               content-host
            5. At content-host some package from cv1 is installable

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.upgrade
    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_delete_cv_multi_env_promoted_with_host_registered(self):
        """Delete published content view with version promoted to multiple
         environments, with one of the environments used in association of an
         Activation key and content-host registration.

        :id: 10699af9-617e-4930-9c80-2827a0ba52eb

        :Steps:

            1. Create two content view cv1 and cv2
            2. Add a yum repo and a puppet module to both content views
            3. Publish the content views
            4. Promote the content views to multiple environment Library -> DEV
               -> QE
            5. Create an Activation key with the QE environment and cv1
            6. Register a content-host using the Activation key
            7. Delete the content view cv1.
               Note - prior deleting replace the current QE environment of cv1
               by DEV and content view cv2 for Content-host and for Activation
               key.
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

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_remove_cv_version_from_multi_env_capsule_scenario(self):
        """Remove promoted content view version from multiple environment,
        with satellite setup to use capsule

        :id: 1e8a8e64-eec8-49e0-b121-919c53f416d2

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

        :CaseAutomation: NotAutomated

        :CaseLevel: System
        """
        # Note: This test case requires complete external capsule
        #  configuration.


class ContentViewVersionIncrementalTestCase(APITestCase):
    """Tests for content view version promotion."""

    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_incremental_update_puppet(self):
        """Incrementally update a CVV with a puppet module.

        :id: 19b2fe3b-6c91-4713-9910-17517fba661f

        :expectedresults: The incremental update succeeds with no errors, and
            the content view is given an additional version.

        :CaseLevel: Integration
        """
        # Create a content view and add a yum repository to it. Publish the CV.
        product = entities.Product().create()
        yum_repo = entities.Repository(content_type='yum', product=product).create()
        content_view = entities.ContentView(
            organization=product.organization, repository=[yum_repo]
        ).create()
        content_view.publish()
        content_view = content_view.read()

        # Create a puppet repository and upload a puppet module into it.
        puppet_repo = entities.Repository(content_type='puppet', product=product).create()
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            puppet_repo.upload_content(files={'content': handle})
        # Extract all the available puppet modules.
        puppet_modules = content_view.available_puppet_modules()['results']
        # Make sure that we have results. Uploading content does not
        # seem to create a task so we cannot pool it for status. We
        # should then check that we have some results back before
        # proceeding.
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = entities.PuppetModule(id=puppet_modules[0]['id'])

        # Incrementally update the CVV with the puppet module.
        payload = {
            'content_view_version_environments': [
                {
                    'content_view_version_id': content_view.version[0].id,
                    'environment_ids': [
                        environment.id
                        for environment in content_view.version[0].read().environment
                    ],
                }
            ],
            'add_content': {'puppet_module_ids': [puppet_module.id]},
        }
        content_view.version[0].incremental_update(data=payload)
        content_view = content_view.read()

        # The CV now has two versions. The first version has no puppet modules,
        # and the second version has one puppet module. Let's verify this.
        # NOTE: The `read_json` lines should be refactored after the 'minor'
        # attribute is added to the ContentViewVersion entity class.
        self.assertEqual(len(content_view.version), 2)
        for i in range(len(content_view.version)):
            content_view.version[i] = content_view.version[i].read()
        content_view.version.sort(key=lambda cvv: cvv.read_json()['minor'])
        self.assertEqual(len(content_view.version[0].puppet_module), 0)
        self.assertEqual(len(content_view.version[1].puppet_module), 1)
        self.assertEqual(content_view.version[1].puppet_module[0].id, puppet_module.id)

    @pytest.mark.tier3
    def test_positive_incremental_update_propagate_composite(self):
        """Incrementally update a CVV in composite CV with
        `propagate_all_composites` flag set

        :BZ: 1288148

        :id: 1ddcb2ef-3819-442e-b070-cf44aba58dcd

        :customerscenario: true

        :Steps:

            1. Create and publish CV with some content
            2. Create composite CV, add previously created CV inside it
            3. Publish composite CV
            4. Create a puppet repository and upload a puppet module into it
            5. Incrementally update the CVV with the puppet module with
               `propagate_all_composites` flag set to `True`

        :expectedresults:

            1. The incremental update succeeds with no errors
            2. New incremental CVV contains new puppet module
            3. New incremental composite CVV contains new puppet module

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        product = entities.Product().create()
        yum_repo = entities.Repository(content_type='yum', product=product).create()
        yum_repo.sync()
        content_view = entities.ContentView(
            organization=product.organization, repository=[yum_repo]
        ).create()
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.version[0].read().puppet_module), 0)
        comp_content_view = entities.ContentView(
            component=[content_view.version[0].id],
            composite=True,
            organization=product.organization,
        ).create()
        comp_content_view.publish()
        comp_content_view = comp_content_view.read()
        self.assertEqual(len(comp_content_view.version), 1)
        self.assertEqual(len(comp_content_view.version[0].read().puppet_module), 0)
        puppet_repo = entities.Repository(content_type='puppet', product=product).create()
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            puppet_repo.upload_content(files={'content': handle})
        puppet_modules = content_view.available_puppet_modules()['results']
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = entities.PuppetModule(id=puppet_modules[0]['id'])
        content_view.version[0].incremental_update(
            data={
                'content_view_version_environments': [
                    {
                        'content_view_version_id': content_view.version[0].id,
                        'environment_ids': [
                            environment.id
                            for environment in content_view.version[0].read().environment
                        ],
                    }
                ],
                'add_content': {'puppet_module_ids': [puppet_module.id]},
                'propagate_all_composites': True,
            }
        )
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 2)
        cvv = content_view.version[-1].read()
        self.assertEqual(len(cvv.puppet_module), 1)
        self.assertEqual(cvv.puppet_module[0].id, puppet_module.id)
        comp_content_view = comp_content_view.read()
        self.assertEqual(len(comp_content_view.version), 2)
        comp_cvv = comp_content_view.version[-1].read()
        self.assertEqual(len(comp_cvv.puppet_module), 1)
        self.assertEqual(comp_cvv.puppet_module[0].id, puppet_module.id)
