# -*- encoding: utf-8 -*-
"""Unit tests for the ``content_views`` paths.

@Requirement: Contentview

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
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
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.helpers import get_data_file
from robottelo.test import APITestCase


# Some tests repeatedly publish content views or promote content view versions.
# How many times should that be done? A higher number means a more interesting
# but longer test.
REPEAT = 3


class ContentViewTestCase(APITestCase):
    """Tests for content views."""

    @upgrade
    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_host(self):
        """Subscribe a host to a content view

        @id: b5a08369-bf92-48ab-b9aa-10f5b9774b79

        @expectedresults: It is possible to create a host and set its
        'content_view_id' facet attribute

        @CaseLevel: System
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

        # Create a host that is subscribed to the published and promoted
        # content view
        host = entities.Host(
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lc_env.id,
            },
            organization=org,
        ).create()
        # See BZ #1151240
        self.assertEqual(
            host.content_facet_attributes['content_view_id'], content_view.id)
        self.assertEqual(
            host.content_facet_attributes['lifecycle_environment_id'],
            lc_env.id
        )
        if not bz_bug_is_open(1223494):
            self.assertEqual(host.organization.id, org.id)

    @tier2
    @run_only_on('sat')
    def test_positive_clone_within_same_env(self):
        """attempt to create, publish and promote new content view
        based on existing view within the same environment as the
        original content view

        @id: a7be5dc1-26c1-4354-99a1-1cbc90c89c64

        @expectedresults: Cloned content view can be published and promoted to
        the same environment as the original content view

        @CaseLevel: Integration
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

    @upgrade
    @tier2
    @run_only_on('sat')
    def test_positive_clone_with_diff_env(self):
        """attempt to create, publish and promote new content
        view based on existing view but promoted to a
        different environment

        @id: a4d21c85-a77c-4664-95ba-3d32c3ad1663

        @expectedresults: Cloned content view can be published and promoted to
        a different environment as the original content view

        @CaseLevel: Integration
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
        """Associate custom content in a view

        @id: db452e0c-0c17-40f2-bab4-8467e7a875f1

        @expectedresults: Custom content assigned and present in content view

        @CaseLevel: Integration
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
        """Attempt to associate puppet repos within a custom content
        view directly

        @id: 659e0b7a-9886-43aa-a489-dbd509c29ef8

        @expectedresults: User cannot create a non-composite content view that
        contains direct puppet repos reference.

        @CaseLevel: Integration
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
        """Attempt to associate the same repo multiple times within a
        content view

        @id: 9e3dff38-fdcc-4483-9844-0619797cf1d5

        @expectedresults: User cannot add repos multiple times to the view

        @CaseLevel: Integration
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
        """Attempt to associate duplicate puppet modules within a
        content view

        @id: 79036b3b-18dd-489e-9725-15f052371512

        @expectedresults: User cannot add same modules multiple times to the
        view

        @CaseLevel: Integration
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
        """Create composite and non-composite content views.

        @id: 4a3b616d-53ab-4396-9a50-916d6c42a401

        @expectedresults: Creation succeeds and content-view is composite or
        non-composite, respectively.
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
        """Create empty content-view with random names.

        @id: 80d36498-2e71-4aa9-b696-f0a45e86267f

        @expectedresults: Content-view is created and had random name.
        """
        for name in valid_data_list():
            with self.subTest(name):
                self.assertEqual(
                    entities.ContentView(name=name).create().name,
                    name
                )

    @tier1
    def test_positive_create_with_description(self):
        """Create empty content view with random description.

        @id: 068e3e7c-34ac-47cb-a1bb-904d12c74cc7

        @expectedresults: Content-view is created and has random description.
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
    def test_positive_clone(self):
        """Create a content view by copying an existing one

        @id: ee03dc63-e2b0-4a89-a828-2910405279ff

        @expectedresults: A content view is cloned with relevant parameters
        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()

        cloned_cv = entities.ContentView(id=content_view.copy(
            data={u'name': gen_string('alpha', gen_integer(3, 30))}
        )['id']).read_json()

        # remove unique values before comparison
        cv_origin = content_view.read_json()
        uniqe_keys = (u'label', u'id', u'name', u'updated_at', u'created_at')
        for key in uniqe_keys:
            del cv_origin[key]
            del cloned_cv[key]

        self.assertEqual(cv_origin, cloned_cv)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create content view providing an invalid name.

        @id: 261376ca-7d12-41b6-9c36-5f284865243e

        @expectedresults: Content View is not created
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
        """Publish a content view several times.

        @id: 54072676-cb59-43d4-82d6-432d8aa103e7

        @expectedresults: Content view has the correct number of versions after
        each publishing operation.

        @CaseLevel: Integration
        """
        content_view = entities.ContentView().create()
        for _ in range(REPEAT):
            content_view.publish()
        self.assertEqual(len(content_view.read().version), REPEAT)

    @tier1
    def test_positive_publish_with_long_name(self):
        """Publish a content view that has at least 255 characters in its name

        @id: 1c786756-266d-49b2-912f-7808096f5cc0

        @expectedresults: Content view has been published and has one version
            populated

        @BZ: 1365312
        """
        name = gen_string('alpha', 255)
        content_view = entities.ContentView(name=name).create()
        content_view.publish()
        self.assertEqual(len(content_view.read().version), 1)

    @tier2
    def test_positive_publish_with_content_multiple(self):
        """Give a content view yum packages and publish it repeatedly.

        @id: 7db81c1f-c69e-453f-bea4-ecad47f27c69

        @expectedresults: The yum repo is referenced from the content view, the
        content view can be published several times, and each content view
        version has at least one package.

        @CaseLevel: Integration
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
        """Create empty composite view and assign one normal content
        view to it. After that publish that composite content view once.

        @id: da7cff4a-fa89-4ca5-8289-18794eb66b92

        @expectedresults: Composite content view is published and corresponding
        version is assigned to it.

        @CaseLevel: Integration
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
        """Create empty composite view and assign random number of
        normal content views to it. After that publish that composite content
        view once.

        @id: 0d56d318-46a4-4da5-871b-72a3926055dd

        @expectedresults: Composite content view is published and corresponding
        version is assigned to it.

        @CaseLevel: Integration
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
        """Create empty composite view and assign one normal content
        view to it. After that publish that composite content view several
        times.

        @id: c0163c56-97c3-4296-aeff-c35a894572d7

        @expectedresults: Composite content view is published several times and
        corresponding versions are assigned to it.

        @CaseLevel: Integration
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
        """Create empty composite view and assign random number of
        normal content views to it. After that publish that composite content
        view several times.

        @id: da8ad491-02f2-4b84-b850-0dea7259739c

        @expectedresults: Composite content view is published several times and
        corresponding versions are assigned to it.

        @CaseLevel: Integration
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
        """Publish a content view that has puppet module once.

        @id: 42083b8e-1cf0-4ee6-9dd5-7de8f06ae028

        @expectedresults: The puppet module is referenced from the content
        view, the content view can be published once and corresponding version
        refer to puppet module

        @CaseLevel: Integration
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
        """Publish a content view that has puppet module
        several times.

        @id: 7096abc9-e761-40cc-8e5b-acc16c7e9c27

        @expectedresults: The puppet module is referenced from the content
        view, the content view can be published several times, and each version
        references the puppet module.

        @CaseLevel: Integration
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
        """Promote a content view version ``REPEAT`` times.

        @id: 06453880-49fd-4ed1-8ee2-cdc530eaa31a

        @expectedresults: The content view version points to ``REPEAT + 1``
        lifecycle environments after the promotions.

        @CaseLevel: Integration
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
    @upgrade
    def test_positive_promote_with_yum_multiple(self):
        """Give a content view a yum repo, publish it once and promote
        the content view version ``REPEAT + 1`` times.

        @id: 58783790-2839-4e91-94d3-008dc3fe3219

        @expectedresults: The content view has one repository, the content view
        version is in ``REPEAT + 1`` lifecycle environments and it has at least
        one package.

        @CaseLevel: Integration
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
        """Give content view a puppet module. Publish
        and promote it once

        @id: 1d56d5c7-aeb7-4d50-a1fd-43f462cae19c

        @expectedresults: The content view has one puppet module, the content
        view version is in ``Library + 1`` lifecycle environments and it has
        one puppet module assigned too.

        @CaseLevel: Integration
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
    @upgrade
    def test_positive_promote_with_puppet_multiple(self):
        """Give a content view a puppet module, publish it once and
        promote the content view version ``Library + random`` times.

        @id: a01465b6-00e9-4a96-9ab5-269a270313cc

        @expectedresults: The content view has one puppet module, the content
        view version is in ``Library + random`` lifecycle environments and it
        has one puppet module.

        @CaseLevel: Integration
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
        """Create normal content view, publish and add it to a new
        composite content view

        @id: 36894150-5321-4ffd-ab5a-a7ad01401cf4

        @expectedresults: Content view can be created and assigned to composite
        one through content view versions mechanism

        @CaseLevel: Integration
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
        """Attempt to associate components in a non-composite content
        view

        @id: 60aa7a4e-df6e-407e-86c7-a4c540bda8b5

        @expectedresults: User cannot add components to the view

        @CaseLevel: Integration
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
        """Create empty composite view and assign one normal content
        view to it. After that promote that composite content view once.

        @id: f25d2f64-8b42-42d2-b713-8827fa3a6a1b

        @expectedresults: Composite content view version points to ``Library +
        1`` lifecycle environments after the promotions.

        @CaseLevel: Integration
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

    @upgrade
    @tier2
    def test_positive_promote_composite_multiple_content_once(self):
        """Create empty composite view and assign random number of
        normal content views to it. After that promote that composite
        content view once.

        @id: 20389383-7510-421c-803a-e73de9db941a

        @expectedresults: Composite content view version points to ``Library +
        1`` lifecycle environments after the promotions.

        @CaseLevel: Integration
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
        """Create empty composite view and assign one normal content
        view to it. After that promote that composite content view
        ``Library + random`` times.

        @id: ba3b737c-365a-4a7b-9109-e6d52fd1c31f

        @expectedresults: Composite content view version points to ``Library +
        random`` lifecycle environments after the promotions.

        @CaseLevel: Integration
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

    @upgrade
    @tier2
    def test_positive_promote_composite_multiple_content_multiple(self):
        """Create empty composite view and assign random number of
        normal content views to it. After that promote that composite content
        view ``Library + random`` times.

        @id: 368811fe-f24a-48a5-b883-9c1d08a03d6b

        @expectedresults: Composite content view version points to ``Library +
        random`` lifecycle environments after the promotions.

        @CaseLevel: Integration
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

        @id: 40d20aba-726f-48e3-93b7-fb1ab1851ac7

        @expectedresults: Content view promoted out of sequence properly

        @CaseLevel: Integration
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
        """Update a content view and provide valid attributes.

        @id: 3f1457f2-586b-472c-8053-99017c4a4909

        @expectedresults: The update succeeds.
        """
        attrs = {'description': gen_utf8(), 'name': gen_utf8()}
        for key, value in attrs.items():
            with self.subTest((key, value)):
                setattr(self.content_view, key, value)
                self.content_view = self.content_view.update({key})
                self.assertEqual(getattr(self.content_view, key), value)

    @tier1
    def test_positive_update_name(self):
        """Create content view providing the initial name, then update
        its name to another valid name.

        @id: 15e6fa3a-1a65-4e7d-8d32-3a81227ac1c8

        @expectedresults: Content View is created, and its name can be updated.
        """
        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated = entities.ContentView(
                    id=self.content_view.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated.name)

    @tier1
    def test_negative_update_name(self):
        """Create content view then update its name to an
        invalid name.

        @id: 69a2ce8d-19b2-49a3-97db-a1fdebbb16be

        @expectedresults: Content View is created, and its name is not updated.
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

        @id: 77883887-800f-412f-91a3-b2f7ed999c70

        @expectedresults: The content view label is immutable and cannot be
        modified
        """
        with self.assertRaises(HTTPError):
            entities.ContentView(
                id=self.content_view.id,
                label=gen_utf8(30)).update(['label'])


class ContentViewDeleteTestCase(APITestCase):
    """Tests for deleting content views."""

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create content view and then delete it.

        @id: d582f1b3-8118-4e78-a639-237c6f9d27c6

        @expectedresults: Content View is successfully deleted.
        """
        for name in valid_data_list():
            with self.subTest(name):
                cv = entities.ContentView().create()
                cv.delete()
                with self.assertRaises(HTTPError):
                    entities.ContentView(id=cv.id).read()


@run_in_one_thread
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
        """associate Red Hat content in a view

        @id: f011a269-813d-4e82-afe8-f106b23cb03e

        @expectedresults: RH Content assigned and present in a view

        @CaseLevel: Integration
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
        """Associate Red Hat content in a view and filter it using rule

        @id: 30c3103d-9503-4501-8117-1f2d25353215

        @expectedresults: Filtered RH content is available and can be seen in a
        view

        @CaseLevel: Integration
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

        @id: 4f1698ef-a23b-48d6-be25-dbbf2d76c95c

        @expectedresults: Content view can be published

        @CaseLevel: Integration
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

        @id: 094a8c46-935b-4dbc-830e-19bec935276c

        @expectedresults: Content view can be published

        @CaseLevel: Integration
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

        @id: 991dd9cc-5818-42dc-9098-66b312adfd97

        @expectedresults: Content view can be promoted

        @CaseLevel: Integration
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        content_view.publish()

        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(content_view.read().version[0], lce.id)
        self.assertEqual(
            len(content_view.read().version[0].read().environment), 2)

    @upgrade
    @tier2
    def test_positive_promote_rh_custom_spin(self):
        """Attempt to promote a content view containing Red Hat spin - i.e.,
        contains filters.

        @id: 8331ba11-1742-425f-83b1-6b06c5785572

        @expectedresults: Content view can be promoted

        @CaseLevel: Integration
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
        """Edit content views for a custom rh spin.  For example,
        modify a filter

        @id: 81d77ecd-8bac-44c6-8bc2-b6e38ad77a0b

        @expectedresults: edited content view save is successful and info is
        updated

        @caseautomation: notautomated

        @CaseLevel: Integration
        """
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.

    @tier2
    @stubbed()
    def test_positive_refresh_errata_new_view_same_env(self):
        """Attempt to refresh errata in a new view, based on an existing view,
        from within the same  environment

        @id: a34bc7b3-ad56-4708-8520-5111db92a55f

        @expectedresults: Content view can be published

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @tier3
    @stubbed()
    def test_positive_subscribe_host(self):
        """Attempt to  subscribe hosts to content view(s)

        @id: 56b58c3a-b3de-4de4-add9-fb313ff87a86

        @expectedresults: Hosts can be subscribed to content view(s)

        @caseautomation: notautomated

        @CaseLevel: System
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
    @upgrade
    def test_positive_subscribe_host_custom_cv(self):
        """Attempt to subscribe hosts to content view(s)

        @id: beffb785-986f-4510-87e6-3645d981afde

        @expectedresults: Hosts can be subscribed to content view(s)

        @CaseLevel: System
        """
        # This test is implemented in tests/foreman/smoke/test_api_smoke.py.
        # See the end of method TestSmoke.test_smoke.

    @tier2
    @stubbed()
    def test_positive_restart_promote_via_dynflow(self):
        """Attempt to restart a promotion

        @id: 99fc4562-0230-40a5-aef1-f65f02feae65

        @steps:

        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion

        @expectedresults: Promotion is restarted.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @upgrade
    @tier2
    @stubbed()
    def test_positive_restart_publish_via_dynflow(self):
        """Attempt to restart a publish

        @id: 8612959e-cd52-404e-88ec-7351c2d282d0

        @steps:

        1. (Somehow) cause a CV publish  to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart publish

        @expectedresults: Publish is restarted.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    # ROLES TESTING
    # All this stuff is speculative at best.

    @tier2
    @stubbed()
    def test_positive_admin_user_actions(self):
        """Attempt to view content views

        @id: 75b638af-d132-4b5e-b034-a373565c72b4

        @setup: create a user with the Content View admin role

        @expectedresults: User with admin role for content view can perform all
        Variations above

        @caseautomation: notautomated

        @CaseLevel: Integration
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
        """Attempt to view content views

        @id: cdfd6e51-cd46-4afa-807c-98b2195fcf0e

        @setup: create a user with the Content View read-only role

        @expectedresults: User with read-only role for content view can perform
        all Variations above

        @caseautomation: notautomated

        @CaseLevel: Integration
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
        """Attempt to view content views

        @id: fbfe2215-67fe-4147-89ec-5fa84eb299c1

        @setup: create a user with the Content View admin role

        @expectedresults: User withOUT admin role for content view canNOT
        perform any Variations above

        @caseautomation: notautomated

        @CaseLevel: Integration
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
        """Attempt to view content views

        @id: 85d3f02e-3bd5-4c31-9c64-76a45a3c30a6

        @setup: create a user withOUT the Content View read-only role
        @expectedresults: User withOUT read-only role for content view can
        perform all Variations above

        @caseautomation: notautomated

        @CaseLevel: Integration
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
