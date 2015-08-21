# -*- encoding: utf-8 -*-
"""Unit tests for the ``content_views`` paths."""
import random

from ddt import ddt
from fauxfactory import gen_integer, gen_string, gen_utf8
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.api.utils import enable_rhrepo_and_fetchid, promote
from robottelo.common import manifests
from robottelo.common.constants import (
    FAKE_0_PUPPET_REPO,
    PRDS,
    PUPPET_MODULE_NTP_PUPPETLABS,
    REPOS,
    REPOSET,
)
from robottelo.common.decorators import (
    bz_bug_is_open,
    data,
    run_only_on,
    stubbed,
)
from robottelo.common.helpers import get_data_file
from robottelo.test import APITestCase


# Some tests repeatedly publish content views or promote content view versions.
# How many times should that be done? A higher number means a more interesting
# but longer test.
REPEAT = 3


@run_only_on('sat')
class ContentViewTestCase(APITestCase):
    """Tests for content views."""

    def test_subscribe_system_to_cv(self):
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

    def test_cv_clone_within_same_env(self):
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

    def test_cv_clone_within_diff_env(self):
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

    def test_cv_associate_custom_content(self):
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

    def test_cv_associate_puppet_repo_negative(self):
        """@Test: Attempt to associate puppet repos within a custom
        content view directly

        @Assert: User cannot create a non-composite content view
        that contains direct puppet repos reference.

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

    def test_cv_associate_composite_dupe_repos_negative(self):
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

    def test_cv_associate_composite_dupe_modules_negative(self):
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


@ddt
class ContentViewCreateTestCase(APITestCase):
    """Tests for creating content views."""

    def test_positive_create_1(self):
        """@Test: Create an empty non-composite content view.

        @Assert: Creation succeeds and content-view is non-composite.

        @Feature: ContentView

        """
        self.assertFalse(
            entities.ContentView(composite=False).create().composite
        )

    def test_positive_create_2(self):
        """@Test: Create an empty composite content view.

        @Assert: Creation succeeds and content-view is composite.

        @Feature: ContentView

        """
        self.assertTrue(
            entities.ContentView(composite=True).create().composite
        )

    @data(
        gen_string('alpha', gen_integer(3, 30)),
        gen_string('alphanumeric', gen_integer(3, 30)),
        gen_string('cjk', gen_integer(3, 30)),
        gen_string('html', gen_integer(3, 30)),
        gen_string('latin1', gen_integer(3, 30)),
        gen_string('numeric', gen_integer(3, 30)),
        gen_string('utf8', gen_integer(3, 30)),
    )
    def test_positive_create_3(self, name):
        """@Test: Create empty content-view with random names.

        @Assert: Content-view is created and had random name.

        @Feature: ContentView

        """
        self.assertEqual(entities.ContentView(name=name).create().name, name)

    @data(
        gen_string('alpha', gen_integer(3, 30)),
        gen_string('alphanumeric', gen_integer(3, 30)),
        gen_string('cjk', gen_integer(3, 30)),
        gen_string('html', gen_integer(3, 30)),
        gen_string('latin1', gen_integer(3, 30)),
        gen_string('numeric', gen_integer(3, 30)),
        gen_string('utf8', gen_integer(3, 30)),
    )
    def test_positive_create_4(self, description):
        """@Test: Create empty content view with random description.

        @Assert: Content-view is created and has random description.

        @Feature: ContentView

        """
        self.assertEqual(
            description,
            entities.ContentView(description=description).create().description,
        )


class CVPublishPromoteTestCase(APITestCase):
    """Tests for publishing and promoting content views."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Set up organization, product and repositories for tests."""
        super(CVPublishPromoteTestCase, cls).setUpClass()
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

    def add_content_views_to_composite(self, composite_cv, cv_amount=1):
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

    def test_positive_publish_1(self):
        """@Test: Publish a content view several times.

        @Assert: Content view has the correct number of versions after each
        promotion.

        @Feature: ContentView

        """
        content_view = entities.ContentView().create()
        for _ in range(REPEAT):
            content_view.publish()
        self.assertEqual(len(content_view.read().version), REPEAT)

    def test_positive_publish_2(self):
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

    def test_publish_composite_cv_once_1(self):
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

    def test_publish_composite_cv_once_2(self):
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

    def test_publish_composite_cv_multiple_1(self):
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

    def test_publish_composite_cv_multiple_2(self):
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

    def test_publish_cv_with_puppet_once(self):
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

    def test_publish_cv_with_puppet_multiple(self):
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

    def test_positive_promote_1(self):
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

    def test_positive_promote_2(self):
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

    def test_promote_cv_with_puppet_once(self):
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

    def test_promote_cv_with_puppet_multiple(self):
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

    def test_add_normal_cv_to_composite(self):
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

    def test_cv_associate_components_composite_negative(self):
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

    def test_promote_composite_cv_once_1(self):
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

    def test_promote_composite_cv_once_2(self):
        """@Test: Create empty composite view and assign random number of
        normal content views to it. After that promote that composite
        content view once.

        @Assert: Composite content view version points to
        ``Library + 1`` lifecycle environments after the promotions.

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

    def test_promote_composite_cv_multiple_1(self):
        """@Test: Create empty composite view and assign one normal content
        view to it. After that promote that composite content view
        ``Library + random`` times.

        @Assert: Composite content view version points to
        ``Library + random`` lifecycle environments after the promotions.

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

    def test_promote_composite_cv_multiple_2(self):
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


@ddt
class ContentViewUpdateTestCase(APITestCase):
    """Tests for updating content views."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create a content view."""
        cls.content_view = entities.ContentView().create()

    @data(
        {u'name': entities.ContentView().get_fields()['name'].gen_value()},
        {
            u'description':
            entities.ContentView().get_fields()['description'].gen_value()
        },
    )
    def test_positive_update(self, attrs):
        """@Test: Update a content view and provide valid attributes.

        @Assert: The update succeeds.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            id=self.content_view.id,
            **attrs
        ).update()
        for field_name, field_value in attrs.items():
            self.assertEqual(getattr(content_view, field_name), field_value)

    @data(
        {u'label': gen_utf8(30), u'bz-bug': 1147100},  # Immutable.
        {u'name': gen_utf8(256)},
    )
    def test_negative_update_1(self, attrs):
        """@Test: Update a content view and provide an invalid attribute.

        @Assert: The content view's attributes are not updated.

        @Feature: ContentView

        """
        bug_id = attrs.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))
        with self.assertRaises(HTTPError):
            entities.ContentView(id=self.content_view.id, **attrs).update()


class CVRedHatContent(APITestCase):
    """Tests for publishing and promoting content views."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Set up organization, product and repositories for tests."""
        super(CVRedHatContent, cls).setUpClass()

        cls.org = entities.Organization().create()
        with open(manifests.clone(), 'rb') as manifest:
            entities.Subscription().upload(
                data={'organization_id': cls.org.id},
                files={'content': manifest},
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

    def test_cv_associate_rh(self):
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

    def test_cv_associate_rh_custom_spin(self):
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


@run_only_on('sat')
class ContentViewTestCaseStub(APITestCase):
    """Incomplete tests for content views."""
    # Each of these tests should be given a better name when they're
    # implemented. In the meantime, let's not worry about bad names.
    # pylint:disable=invalid-name

    @stubbed()
    def test_cv_edit_rh_custom_spin(self):
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

    # Content View: promotions
    # katello content view promote --label=MyView --env=Dev --org=ACME
    # katello content view promote --view=MyView --env=Staging --org=ACME

    @stubbed()
    def test_cv_promote_rh(self):
        """
        @test: attempt to promote a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @stubbed()
    def test_cv_promote_rh_custom_spin(self):
        """
        @test: attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @stubbed()
    def test_cv_promote_custom_content(self):
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be promoted
        """

    @stubbed()
    def test_cv_promote_composite(self):
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @steps: create a composite view containing multiple content types
        @assert: Content view can be promoted
        @status: Manual
        """
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.

    @stubbed()
    def test_cv_promote_badid_negative(self):
        """
        @test: attempt to promote a content view using an invalid id
        @feature: Content Views
        @assert: Content views cannot be promoted; handled gracefully
        """
        # env = EnvironmentKatello()
        # created_env = ApiCrud.record_create_recursive(env)
        # task = ContentViewDefinition._meta.api_class.promote(
        #     1,
        #     created_env.id
        #     )
        # self.assertIn(
        #     'errors', task.json,
        #     "Invalid id shouldn't be promoted")

    # Content Views: publish
    # katello content definition publish --label=MyView

    @stubbed()
    def test_cv_publish_rh(self):
        """
        @test: attempt to publish a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        """
        # See method test_subscribe_system_to_cv in module test_contentview_v2

    @stubbed()
    def test_cv_publish_rh_custom_spin(self):
        """
        @test: attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed()
    def test_cv_publish_custom_content(self):
        """
        @test: attempt to publish a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed()
    def test_cv_publish_composite(self):
        """
        @test: attempt to publish  a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        @status: Manual
        """
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.

    @stubbed()
    def test_cv_publish_badlabel_negative(self):
        """
        @test: attempt to publish a content view containing invalid strings
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view is not published; condition is handled
        gracefully;
        no tracebacks
        @status: Manual
        """
        # Variations might be:
        # zero length, too long, symbols, etc.

    @stubbed()
    def test_cv_publish_version_changes_in_target_env(self):
        """
        @test: when publishing new version to environment, version
        gets updated
        @feature: Content Views
        @setup: Multiple environments for an org; multiple versions
        of a content view created/published
        @steps:
        1. publish a view to an environment noting the CV version
        2. edit and republish a new version of a CV
        @assert: Content view version is updated intarget environment.
        @status: Manual
        """
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)

    @stubbed()
    def test_cv_publish_version_changes_in_source_env(self):
        """
        @test: when publishing new version to environment, version
        gets updated
        @feature: Content Views
        @setup: Multiple environments for an org; multiple versions
        of a content view created/published
        @steps:
        1. publish a view to an environment
        2. edit and republish a new version of a CV
        @assert: Content view version is updated in source environment.
        @status: Manual
        """
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)

    @stubbed()
    def test_cv_refresh_errata_to_new_view_in_same_env(self):
        """
        @test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed()
    def test_cv_subscribe_system(self):
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

    @stubbed()
    def test_custom_cv_subscribe_system(self):
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        """
        # This test is implemented in tests/foreman/smoke/test_api_smoke.py.
        # See the end of method TestSmoke.test_smoke.

    @stubbed()
    def test_cv_dynflow_restart_promote(self):
        """
        @test: attempt to restart a promotion
        @feature: Content Views
        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion
        @assert: Promotion is restarted.
        @status: Manual
        """

    @stubbed()
    def test_cv_dynflow_restart_publish(self):
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

    @stubbed()
    def test_cv_roles_admin_user(self):
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

    @stubbed()
    def test_cv_roles_readonly_user(self):
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

    @stubbed()
    def test_cv_roles_admin_user_negative(self):
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

    @stubbed()
    def test_cv_roles_readonly_user_negative(self):
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
