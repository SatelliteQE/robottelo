# -*- encoding: utf-8 -*-
"""Unit tests for the ``content_views`` paths."""
import random

from fauxfactory import gen_integer, gen_string, gen_utf8
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.api.utils import enable_rhrepo_and_fetchid, promote
from robottelo import manifests
from robottelo.constants import (
    FAKE_0_PUPPET_REPO,
    PRDS,
    PUPPET_MODULE_NTP_PUPPETLABS,
    REPOS,
    REPOSET,
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    bz_bug_is_open,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.helpers import get_data_file
from robottelo.test import APITestCase


# Some tests repeatedly publish content views or promote content view versions.
# How many times should that be done? A higher number means a more interesting
# but longer test.
REPEAT = 3


class ContentViewTestCase(APITestCase):
    """Tests for content views."""

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_system(self):
        """@Test: Subscribe a system to a content view.

        @Feature: ContentView

        @Assert: It is possible to create a system and set its
        'content_view_id' attribute.
        """
        # organization
        # ├── lifecycle environment
        # └── content view
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()

        # Publish the content view.
        content_view.publish()
        content_view = content_view.read()

        # Promote the content view version.
        self.assertEqual(len(content_view.version), 1)
        promote(content_view.version[0], lc_env.id)

        # Create a system that is subscribed to the published and promoted
        # content view. Associating this system with the organization and
        # environment created above is not particularly important, but doing so
        # means a shorter test where fewer entities are created, as
        # System.organization and System.environment are required attributes.
        system = entities.System(
            content_view=content_view,
            environment=lc_env,
            organization=org,
        ).create()

        # See BZ #1151240
        self.assertEqual(system.content_view.id, content_view.id)
        self.assertEqual(system.environment.id, lc_env.id)
        if not bz_bug_is_open(1223494):
            self.assertEqual(system.organization.id, org.id)

    @tier2
    @run_only_on('sat')
    def test_positive_clone_within_same_env(self):
        """@Test: attempt to create, publish and promote new content view
        based on existing view within the same environment as the
        original content view

        @Feature: Content Views

        @Assert: Cloned content view can be published and promoted
        to the same environment as the original content view
        """
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        content_view.publish()
        promote(content_view.read().version[0], lc_env.id)

        cloned_cv = entities.ContentView(id=content_view.copy(
            data={u'name': gen_string('alpha', gen_integer(3, 30))}
        )['id'])
        cloned_cv.publish()
        promote(cloned_cv.read().version[0], lc_env.id)

    @tier2
    @run_only_on('sat')
    def test_positive_clone_with_diff_env(self):
        """@Test: attempt to create, publish and promote new content
        view based on existing view but promoted to a
        different environment

        @Feature: Content Views

        @Assert: Cloned content view can be published and promoted
        to a different environment as the original content view
        """
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        le_clone = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        content_view.publish()
        promote(content_view.read().version[0], lc_env.id)
        cloned_cv = entities.ContentView(id=content_view.copy(
            data={u'name': gen_string('alpha', gen_integer(3, 30))}
        )['id'])
        cloned_cv.publish()
        promote(cloned_cv.read().version[0], le_clone.id)

    @tier2
    @run_only_on('sat')
    def test_positive_add_custom_content(self):
        """@Test: Associate custom content in a view

        @Assert: Custom content assigned and present in content view

        @Feature: Content Views
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        yum_repo = entities.Repository(product=product).create()
        yum_repo.sync()
        content_view = entities.ContentView(organization=org).create()
        self.assertEqual(len(content_view.repository), 0)
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(len(content_view.repository), 1)
        self.assertEqual(content_view.repository[0].read().name, yum_repo.name)

    @skip_if_bug_open('bugzilla', 1297308)
    @tier2
    @run_only_on('sat')
    def test_negative_add_puppet_content(self):
        """@Test: Attempt to associate puppet repos within a custom content
        view directly

        @Assert: User cannot create a non-composite content view that contains
        direct puppet repos reference.

        @Feature: Content Views
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        puppet_repo = entities.Repository(
            content_type='puppet',
            product=product,
            url=FAKE_0_PUPPET_REPO,
        ).create()
        puppet_repo.sync()
        with self.assertRaises(HTTPError):
            entities.ContentView(
                organization=org,
                repository=[puppet_repo.id],
            ).create()

    @tier2
    @run_only_on('sat')
    def test_negative_add_dupe_repos(self):
        """@Test: Attempt to associate the same repo multiple times within a
        content view

        @Assert: User cannot add repos multiple times to the view

        @Feature: Content Views
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        yum_repo = entities.Repository(product=product).create()
        yum_repo.sync()

        content_view = entities.ContentView(organization=org).create()
        self.assertEqual(len(content_view.repository), 0)
        with self.assertRaises(HTTPError):
            content_view.repository = [yum_repo, yum_repo]
            content_view.update(['repository'])
        self.assertEqual(len(content_view.read().repository), 0)

    @tier2
    @run_only_on('sat')
    def test_negative_add_dupe_modules(self):
        """@Test: Attempt to associate duplicate puppet modules within a
        content view

        @Assert: User cannot add same modules multiple times to the view

        @Feature: Content Views
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        puppet_repo = entities.Repository(
            content_type='puppet',
            product=product,
            url=FAKE_0_PUPPET_REPO,
        ).create()
        puppet_repo.sync()

        content_view = entities.ContentView(organization=org).create()
        puppet_module = random.choice(
            content_view.available_puppet_modules()['results']
        )

        self.assertEqual(len(content_view.read().puppet_module), 0)
        entities.ContentViewPuppetModule(
            author=puppet_module['author'],
            name=puppet_module['name'],
            content_view=content_view,
        ).create()
        self.assertEqual(len(content_view.read().puppet_module), 1)

        with self.assertRaises(HTTPError):
            entities.ContentViewPuppetModule(
                author=puppet_module['author'],
                name=puppet_module['name'],
                content_view=content_view,
            ).create()
        self.assertEqual(len(content_view.read().puppet_module), 1)


class ContentViewCreateTestCase(APITestCase):
    """Create tests for content views."""

    @tier1
    def test_positive_create_composite(self):
        """@Test: Create composite and non-composite content views.

        @Assert: Creation succeeds and content-view is composite or
        non-composite, respectively.

        @Feature: ContentView
        """
        for composite in (True, False):
            with self.subTest(composite):
                self.assertEqual(
                    composite,
                    entities.ContentView(
                        composite=composite
                    ).create().composite,
                )

    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create empty content-view with random names.

        @Assert: Content-view is created and had random name.

        @Feature: ContentView
        """
        for name in valid_data_list():
            with self.subTest(name):
                self.assertEqual(
                    entities.ContentView(name=name).create().name,
                    name
                )

    @tier1
    def test_positive_create_with_description(self):
        """@Test: Create empty content view with random description.

        @Assert: Content-view is created and has random description.

        @Feature: ContentView
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                self.assertEqual(
                    desc,
                    entities.ContentView(
                        description=desc
                    ).create().description,
                )

    @tier1
    def test_negative_create_with_invalid_name(self):
        """@Test: Create content view providing an invalid name.

        @Assert: Content View is not created

        @Feature: Content View
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.ContentView(name=name).create()


class ContentViewPublishPromoteTestCase(APITestCase):
    """Tests for publishing and promoting content views."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Set up organization, product and repositories for tests."""
        super(ContentViewPublishPromoteTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()
        cls.yum_repo = entities.Repository(product=cls.product).create()
        cls.yum_repo.sync()
        cls.puppet_repo = entities.Repository(
            content_type='puppet',
            product=cls.product.id,
            url=FAKE_0_PUPPET_REPO,
        ).create()
        cls.puppet_repo.sync()
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            cls.puppet_repo.upload_content(files={'content': handle})

    def add_content_views_to_composite(
            self, composite_cv, cv_amount=1):
        """Add necessary number of content views to the composite one

        :param composite_cv: Composite content view object
        :param cv_amount: Amount of content views to be added
        """
        cv_versions = []
        for _ in range(cv_amount):
            content_view = entities.ContentView(organization=self.org).create()
            content_view.publish()
            cv_versions.append(content_view.read().version[0])
        composite_cv.component = cv_versions
        composite_cv = composite_cv.update(['component'])
        self.assertEqual(len(composite_cv.component), cv_amount)

    @tier2
    def test_positive_publish_multiple(self):
        """@Test: Publish a content view several times.

        @Assert: Content view has the correct number of versions after each
        publishing operation.

        @Feature: ContentView
        """
        content_view = entities.ContentView().create()
        for _ in range(REPEAT):
            content_view.publish()
        self.assertEqual(len(content_view.read().version), REPEAT)

    @tier2
    def test_positive_publish_with_content_multiple(self):
        """@Test: Give a content view yum packages and publish it repeatedly.

        @Assert: The yum repo is referenced from the content view, the content
        view can be published several times, and each content view version has
        at least one package.

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.yum_repo]
        content_view = content_view.update(['repository'])

        # Check that the yum repo is referenced.
        self.assertEqual(len(content_view.repository), 1)

        # Publish the content view several times and check that each version
        # has some software packages.
        for _ in range(REPEAT):
            content_view.publish()
        for cvv in content_view.read().version:
            self.assertGreater(cvv.read_json()['package_count'], 0)

    @tier2
    def test_positive_publish_composite_single_content_once(self):
        """@Test: Create empty composite view and assign one normal content
        view to it. After that publish that composite content view once.

        @Assert: Composite content view is published and corresponding
        version is assigned to it.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv)
        composite_cv.publish()
        self.assertEqual(len(composite_cv.read().version), 1)

    @tier2
    def test_positive_publish_composite_multiple_content_once(self):
        """@Test: Create empty composite view and assign random number of
        normal content views to it. After that publish that composite content
        view once.

        @Assert: Composite content view is published and corresponding
        version is assigned to it.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv, random.randint(3, 5))
        composite_cv.publish()
        self.assertEqual(len(composite_cv.read().version), 1)

    @tier2
    def test_positive_publish_composite_single_content_multiple(self):
        """@Test: Create empty composite view and assign one normal content
        view to it. After that publish that composite content view several
        times.

        @Assert: Composite content view is published several times
        and corresponding versions are assigned to it.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv)

        for i in range(random.randint(3, 5)):
            composite_cv.publish()
            self.assertEqual(len(composite_cv.read().version), i + 1)

    @tier2
    def test_positive_publish_composite_multiple_content_multiple(self):
        """@Test: Create empty composite view and assign random number of
        normal content views to it. After that publish that composite content
        view several times.

        @Assert: Composite content view is published several times
        and corresponding versions are assigned to it.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv, random.randint(3, 5))

        for i in range(random.randint(3, 5)):
            composite_cv.publish()
            self.assertEqual(len(composite_cv.read().version), i + 1)

    @tier2
    def test_positive_publish_with_puppet_once(self):
        """@Test: Publish a content view that has puppet module once.

        @Assert: The puppet module is referenced from the content view, the
        content view can be published once and corresponding version refer to
        puppet module

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        puppet_module = random.choice(
            content_view.available_puppet_modules()['results']
        )
        entities.ContentViewPuppetModule(
            author=puppet_module['author'],
            name=puppet_module['name'],
            content_view=content_view,
        ).create()
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.puppet_module), 1)

    @tier2
    def test_positive_publish_with_puppet_multiple(self):
        """@Test: Publish a content view that has puppet module
        several times.

        @Assert: The puppet module is referenced from the content view, the
        content view can be published several times, and each version
        references the puppet module.

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        puppet_module = random.choice(
            content_view.available_puppet_modules()['results']
        )

        # Assign a puppet module and check that it is referenced.
        entities.ContentViewPuppetModule(
            author=puppet_module['author'],
            name=puppet_module['name'],
            content_view=content_view,
        ).create()
        self.assertEqual(len(content_view.read().puppet_module), 1)

        # Publish the content view several times and check that each version
        # has the puppet module added above.
        for i in range(random.randint(3, 5)):
            content_view.publish()
            self.assertEqual(len(content_view.read().version), i + 1)
        for cvv in content_view.read().version:
            self.assertEqual(len(cvv.read().puppet_module), 1)

    @tier2
    def test_positive_promote_empty_multiple(self):
        """@Test: Promote a content view version ``REPEAT`` times.

        @Assert: The content view version points to ``REPEAT + 1`` lifecycle
        environments after the promotions.

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.publish()
        content_view = content_view.read()

        # Promote the content view version several times.
        for _ in range(REPEAT):
            lce = entities.LifecycleEnvironment(organization=self.org).create()
            promote(content_view.version[0], lce.id)

        # Does it show up in the correct number of lifecycle environments?
        self.assertEqual(
            len(content_view.read().version[0].read().environment),
            REPEAT + 1,
        )

    @tier2
    def test_positive_promote_with_yum_multiple(self):
        """@Test: Give a content view a yum repo, publish it once and promote
        the content view version ``REPEAT + 1`` times.

        @Assert: The content view has one repository, the content view version
        is in ``REPEAT + 1`` lifecycle environments and it has at least one
        package.

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.yum_repo]
        content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()

        # Promote the content view version.
        for _ in range(REPEAT):
            lce = entities.LifecycleEnvironment(organization=self.org).create()
            promote(content_view.version[0], lce.id)

        # Everything's done - check some content view attributes...
        content_view = content_view.read()
        self.assertEqual(len(content_view.repository), 1)
        self.assertEqual(len(content_view.version), 1)

        # ...and some content view version attributes.
        cvv_attrs = content_view.version[0].read_json()
        self.assertEqual(len(cvv_attrs['environments']), REPEAT + 1)
        self.assertGreater(cvv_attrs['package_count'], 0)

    @tier2
    def test_positive_promote_with_puppet_once(self):
        """@Test: Give content view a puppet module. Publish
        and promote it once

        @Assert: The content view has one puppet module, the content view
        version is in ``Library + 1`` lifecycle environments and it has one
        puppet module assigned too.

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        puppet_module = random.choice(
            content_view.available_puppet_modules()['results']
        )
        entities.ContentViewPuppetModule(
            author=puppet_module['author'],
            name=puppet_module['name'],
            content_view=content_view,
        ).create()
        content_view.publish()
        content_view = content_view.read()
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(content_view.version[0], lce.id)

        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.puppet_module), 1)

        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 2)
        self.assertEqual(len(cvv.puppet_module), 1)

    @tier2
    def test_positive_promote_with_puppet_multiple(self):
        """@Test: Give a content view a puppet module, publish it once and
        promote the content view version ``Library + random`` times.

        @Assert: The content view has one puppet module, the content view
        version is in ``Library + random`` lifecycle environments and it has
        one puppet module.

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        puppet_module = random.choice(
            content_view.available_puppet_modules()['results']
        )
        entities.ContentViewPuppetModule(
            author=puppet_module['author'],
            name=puppet_module['name'],
            content_view=content_view,
        ).create()
        content_view.publish()
        content_view = content_view.read()

        # Promote the content view version.
        envs_amount = random.randint(3, 5)
        for _ in range(envs_amount):
            lce = entities.LifecycleEnvironment(organization=self.org).create()
            promote(content_view.version[0], lce.id)

        # Everything's done. Check some content view attributes...
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.puppet_module), 1)

        # ...and some content view version attributes.
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), envs_amount + 1)
        self.assertEqual(len(cvv.puppet_module), 1)

    @tier2
    def test_positive_add_to_composite(self):
        """@Test: Create normal content view, publish and add it to a new
        composite content view

        @Assert: Content view can be created and assigned to composite one
        through content view versions mechanism

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.yum_repo]
        content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()

        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        composite_cv.component = content_view.version  # list of one CV version
        composite_cv = composite_cv.update(['component'])

        # composite CV → CV version == CV → CV version
        self.assertEqual(
            composite_cv.component[0].id,
            content_view.version[0].id,
        )
        # composite CV → CV version → CV == CV
        self.assertEqual(
            composite_cv.component[0].read().content_view.id,
            content_view.id,
        )

    @tier2
    def test_negative_add_components_to_composite(self):
        """@Test: Attempt to associate components in a non-composite content
        view

        @Assert: User cannot add components to the view

        @Feature: Content Views
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.yum_repo]
        content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()

        non_composite_cv = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        non_composite_cv.component = content_view.version  # list of one cvv
        with self.assertRaises(HTTPError):
            non_composite_cv.update(['component'])
        self.assertEqual(len(non_composite_cv.read().component), 0)

    @tier2
    def test_positive_promote_composite_single_content_once(self):
        """@Test: Create empty composite view and assign one normal content
        view to it. After that promote that composite content view once.

        @Assert: Composite content view version points to
        ``Library + 1`` lifecycle environments after the promotions.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv)
        composite_cv.publish()
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(composite_cv.read().version[0], lce.id)
        composite_cv = composite_cv.read()
        self.assertEqual(len(composite_cv.version), 1)
        self.assertEqual(len(composite_cv.version[0].read().environment), 2)

    @tier2
    def test_positive_promote_composite_multiple_content_once(self):
        """@Test: Create empty composite view and assign random number of
        normal content views to it. After that promote that composite
        content view once.

        @Assert: Composite content view version points to ``Library + 1``
        lifecycle environments after the promotions.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv, random.randint(3, 5))
        composite_cv.publish()
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(composite_cv.read().version[0], lce.id)
        composite_cv = composite_cv.read()
        self.assertEqual(len(composite_cv.version), 1)
        self.assertEqual(len(composite_cv.version[0].read().environment), 2)

    @tier2
    def test_positive_promote_composite_single_content_multiple(self):
        """@Test: Create empty composite view and assign one normal content
        view to it. After that promote that composite content view
        ``Library + random`` times.

        @Assert: Composite content view version points to ``Library + random``
        lifecycle environments after the promotions.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv)
        composite_cv.publish()
        composite_cv = composite_cv.read()

        envs_amount = random.randint(3, 5)
        for _ in range(envs_amount):
            lce = entities.LifecycleEnvironment(organization=self.org).create()
            promote(composite_cv.version[0], lce.id)
        composite_cv = composite_cv.read()
        self.assertEqual(len(composite_cv.version), 1)
        self.assertEqual(
            envs_amount + 1,
            len(composite_cv.version[0].read().environment),
        )

    @tier2
    def test_positive_promote_composite_multiple_content_multiple(self):
        """@Test: Create empty composite view and assign random number of
        normal content views to it. After that promote that composite content
        view ``Library + random`` times.

        @Assert: Composite content view version points to
        ``Library + random`` lifecycle environments after the promotions.

        @Feature: ContentView
        """
        composite_cv = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        self.add_content_views_to_composite(composite_cv, random.randint(3, 5))
        composite_cv.publish()
        composite_cv = composite_cv.read()

        envs_amount = random.randint(3, 5)
        for _ in range(envs_amount):
            lce = entities.LifecycleEnvironment(organization=self.org).create()
            promote(composite_cv.version[0], lce.id)
        composite_cv = composite_cv.read()
        self.assertEqual(len(composite_cv.version), 1)
        self.assertEqual(
            envs_amount + 1,
            len(composite_cv.version[0].read().environment),
        )

    @tier2
    def test_positive_promote_out_of_sequence(self):
        """Try to publish content view few times in a row and then re-promote
        first version to default environment

        @Assert: Content view promoted out of sequence properly

        @Feature: ContentView
        """
        content_view = entities.ContentView(organization=self.org).create()
        for _ in range(REPEAT):
            content_view.publish()
        content_view = content_view.read()
        # Check that CV is published and has proper number of CV versions.
        self.assertEqual(len(content_view.version), REPEAT)
        # After each publish operation application re-assign environment to
        # latest CV version. Correspondingly, at that moment, first cv version
        # should have 0 environments and latest should have one ('Library')
        # assigned to it.
        self.assertEqual(len(content_view.version[0].read().environment), 0)
        lce_list = content_view.version[-1].read().environment
        self.assertEqual(len(lce_list), 1)
        # Trying to re-promote 'Library' environment from latest version to
        # first one
        promote(content_view.version[0], lce_list[0].id, force=True)
        content_view = content_view.read()
        # Verify that, according to our plan, first version contains one
        # environment and latest - 0
        self.assertEqual(len(content_view.version[0].read().environment), 1)
        self.assertEqual(len(content_view.version[-1].read().environment), 0)


class ContentViewUpdateTestCase(APITestCase):
    """Tests for updating content views."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create a content view."""
        super(ContentViewUpdateTestCase, cls).setUpClass()
        cls.content_view = entities.ContentView().create()

    @tier1
    def test_positive_update_attributes(self):
        """@Test: Update a content view and provide valid attributes.

        @Assert: The update succeeds.

        @Feature: ContentView
        """
        attrs = {'description': gen_utf8(), 'name': gen_utf8()}
        for key, value in attrs.items():
            with self.subTest((key, value)):
                setattr(self.content_view, key, value)
                self.content_view = self.content_view.update({key})
                self.assertEqual(getattr(self.content_view, key), value)

    @tier1
    def test_positive_update_name(self):
        """@Test: Create content view providing the initial name, then update
        its name to another valid name.

        @Assert: Content View is created, and its name can be
        updated.

        @Feature: Content View
        """
        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated = entities.ContentView(
                    id=self.content_view.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated.name)

    @tier1
    def test_negative_update_name(self):
        """@Test: Create content view then update its name to an
        invalid name.

        @Assert: Content View is created, and its name is not
        updated.

        @Feature: Content View
        """
        for new_name in invalid_names_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.ContentView(
                        id=self.content_view.id,
                        name=new_name).update(['name'])
                cv = entities.ContentView(id=self.content_view.id).read()
                self.assertNotEqual(cv.name, new_name)

    @skip_if_bug_open('bugzilla', 1147100)
    @tier1
    def test_negative_update_label(self):
        """Try to update a content view label with any value

        @Assert: The content view label is immutable and cannot be modified

        @Feature: ContentView
        """
        with self.assertRaises(HTTPError):
            entities.ContentView(
                id=self.content_view.id,
                label=gen_utf8(30)).update(['label'])


class ContentViewDeleteTestCase(APITestCase):
    """Tests for deleting content views."""

    @tier1
    def test_positive_delete(self):
        """@Test: Create content view and then delete it.

        @Assert: Content View is successfully deleted.

        @Feature: Content View
        """
        for name in valid_data_list():
            with self.subTest(name):
                cv = entities.ContentView().create()
                cv.delete()
                with self.assertRaises(HTTPError):
                    entities.ContentView(id=cv.id).read()


class ContentViewRedHatContent(APITestCase):
    """Tests for publishing and promoting content views."""

    @classmethod
    @skip_if_not_set('fake_manifest')
    def setUpClass(cls):  # noqa
        """Set up organization, product and repositories for tests."""
        super(ContentViewRedHatContent, cls).setUpClass()

        cls.org = entities.Organization().create()
        with manifests.clone() as manifest:
            entities.Subscription().upload(
                data={'organization_id': cls.org.id},
                files={'content': manifest.content},
            )
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=cls.org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        cls.repo = entities.Repository(id=repo_id)
        cls.repo.sync()

    @tier2
    def test_positive_add_rh(self):
        """@Test: associate Red Hat content in a view

        @Assert: RH Content assigned and present in a view

        @Feature: Content Views
        """
        content_view = entities.ContentView(organization=self.org).create()
        self.assertEqual(len(content_view.repository), 0)
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(len(content_view.repository), 1)
        self.assertEqual(
            content_view.repository[0].read().name,
            REPOS['rhst7']['name'],
        )

    @tier2
    def test_positive_add_rh_custom_spin(self):
        """@Test: Associate Red Hat content in a view and filter it using rule

        @Feature: Content Views

        @Assert: Filtered RH content is available and can be seen in a
        view
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(len(content_view.repository), 1)

        # content_view ← cv_filter
        cv_filter = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion='true',
            name=gen_string('alphanumeric'),
        ).create()
        self.assertEqual(content_view.id, cv_filter.content_view.id)

        # content_view ← cv_filter ← cv_filter_rule
        cv_filter_rule = entities.ContentViewFilterRule(
            content_view_filter=cv_filter,
            name=gen_string('alphanumeric'),
            version='1.0',
        ).create()
        self.assertEqual(cv_filter.id, cv_filter_rule.content_view_filter.id)

    @tier2
    def test_positive_publish_rh(self):
        """Attempt to publish a content view containing Red Hat content

        @Assert: Content view can be published

        @Feature: Content View
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        self.assertEqual(len(content_view.read().version), 1)

    @tier2
    def test_positive_publish_rh_custom_spin(self):
        """Attempt to publish a content view containing Red Hat spin - i.e.,
        contains filters.

        @Feature: Content Views

        @Assert: Content view can be published
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion='true',
            name=gen_string('alphanumeric'),
        ).create()
        content_view.publish()
        self.assertEqual(len(content_view.read().version), 1)

    @tier2
    def test_positive_promote_rh(self):
        """Attempt to promote a content view containing Red Hat content

        @Assert: Content view can be promoted

        @Feature: Content View
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        content_view.publish()

        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(content_view.read().version[0], lce.id)
        self.assertEqual(
            len(content_view.read().version[0].read().environment), 2)

    @tier2
    def test_positive_promote_rh_custom_spin(self):
        """Attempt to promote a content view containing Red Hat spin - i.e.,
        contains filters.

        @Feature: Content Views

        @Assert: Content view can be promoted
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion='true',
            name=gen_string('alphanumeric'),
        ).create()
        content_view.publish()

        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(content_view.read().version[0], lce.id)
        self.assertEqual(
            len(content_view.read().version[0].read().environment), 2)


class ContentViewTestCaseStub(APITestCase):
    """Incomplete tests for content views."""
    # Each of these tests should be given a better name when they're
    # implemented. In the meantime, let's not worry about bad names.

    @tier2
    @stubbed()
    def test_positive_update_rh_custom_spin(self):
        """
        @test: edit content views for a custom rh spin.  For example,
        @feature: Content Views
        modify a filter
        @assert: edited content view save is successful and info is
        updated
        @status: Manual
        """
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.

    @tier2
    @stubbed()
    def test_positive_refresh_errata_new_view_same_env(self):
        """
        @test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @tier3
    @stubbed()
    def test_positive_subscribe_system(self):
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        @status: Manual
        """
        # Notes:
        # this should be limited to only those content views
        # to which you have permission, but there are/will be
        # other tests for that.
        # Variations:
        # * rh content
        # * rh custom spins
        # * custom content
        # * composite
        # * CVs with puppet modules

    @tier3
    @stubbed()
    def test_positive_subscribe_system_custom_cv(self):
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        """
        # This test is implemented in tests/foreman/smoke/test_api_smoke.py.
        # See the end of method TestSmoke.test_smoke.

    @tier2
    @stubbed()
    def test_positive_restart_promote_via_dynflow(self):
        """
        @test: attempt to restart a promotion
        @feature: Content Views
        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion
        @assert: Promotion is restarted.
        @status: Manual
        """

    @tier2
    @stubbed()
    def test_positive_restart_publish_via_dynflow(self):
        """
        @test: attempt to restart a publish
        @feature: Content Views
        @steps:
        1. (Somehow) cause a CV publish  to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart publish
        @assert: Publish is restarted.
        @status: Manual
        """

    # ROLES TESTING
    # All this stuff is speculative at best.

    @tier2
    @stubbed()
    def test_positive_admin_user_actions(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View admin role
        @assert: User with admin role for content view can perform all
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe

    @tier2
    @stubbed()
    def test_positive_readonly_user_actions(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View read-only role
        @assert: User with read-only role for content view can perform all
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??

    @tier2
    @stubbed()
    def test_negative_non_admin_user_actions(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View admin role
        @assert: User withOUT admin role for content view canNOT perform any
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe

    @tier2
    @stubbed()
    def test_negative_non_readonly_user_actions(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user withOUT the Content View read-only role
        @assert: User withOUT read-only role for content view can perform all
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??
