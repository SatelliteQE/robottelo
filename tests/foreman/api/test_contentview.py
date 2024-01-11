"""Unit tests for the ``content_views`` paths.

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""
import random

from fauxfactory import gen_integer, gen_string, gen_utf8
import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings, user_nailgun_config
from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CUSTOM_RPM_SHA_512_FEED_COUNT,
    FILTER_ERRATA_TYPE,
    PERMISSIONS,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.constants.repos import CUSTOM_RPM_SHA_512, FEDORA_OSTREE_REPO
from robottelo.utils.datafactory import (
    invalid_names_list,
    parametrized,
    valid_data_list,
)

# Some tests repeatedly publish content views or promote content view versions.
# How many times should that be done? A higher number means a more interesting
# but longer test.
REPEAT = 3


@pytest.fixture(scope='class')
def class_cv(module_org, class_target_sat):
    return class_target_sat.api.ContentView(organization=module_org).create()


@pytest.fixture(scope='class')
def class_published_cv(class_cv):
    class_cv.publish()
    return class_cv.read()


@pytest.fixture(scope='class')
def class_promoted_cv(class_published_cv, module_lce):
    class_published_cv.version[0].promote(data={'environment_ids': module_lce.id})
    return class_published_cv.read()


@pytest.fixture(scope='class')
def class_cloned_cv(class_cv, class_target_sat):
    copied_cv_id = class_target_sat.api.ContentView(id=class_cv.id).copy(
        data={'name': gen_string('alpha', gen_integer(3, 30))}
    )['id']
    return class_target_sat.api.ContentView(id=copied_cv_id).read()


@pytest.fixture(scope='class')
def class_published_cloned_cv(class_cloned_cv, class_target_sat):
    class_cloned_cv.publish()
    return class_target_sat.api.ContentView(id=class_cloned_cv.id).read()


@pytest.fixture
def content_view(module_org, module_target_sat):
    return module_target_sat.api.ContentView(organization=module_org).create()


def apply_package_filter(content_view, repo, package, target_sat, inclusion=True):
    """Apply package filter on content view

    :param content_view: entity content view
    :param repo: entity repository
    :param str package: package name to filter
    :param bool inclusion: True/False based on include or exclude filter

    :return list : list of content view versions
    """
    cv_filter = target_sat.api.RPMContentViewFilter(
        content_view=content_view, inclusion=inclusion, repository=[repo]
    ).create()
    cv_filter_rule = target_sat.api.ContentViewFilterRule(
        content_view_filter=cv_filter, name=package
    ).create()
    assert cv_filter.id == cv_filter_rule.content_view_filter.id
    content_view.publish()
    content_view = content_view.read()
    content_view_version_info = content_view.version[0].read()
    return content_view_version_info


class TestContentView:
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_subscribe_host(
        self, class_cv, class_promoted_cv, module_lce, module_org, module_target_sat
    ):
        """Subscribe a host to a content view

        :id: b5a08369-bf92-48ab-b9aa-10f5b9774b79

        :expectedresults: It is possible to create a host and set its
            'content_view_id' facet attribute

        :CaseAutomation: Automated

        :CaseImportance: High
        """
        # organization
        # ├── lifecycle environment
        # └── content view

        # Check that no host associated to just created content view
        assert class_cv.content_host_count == 0
        assert len(class_promoted_cv.version) == 1
        host = module_target_sat.api.Host(
            content_facet_attributes={
                'content_view_id': class_cv.id,
                'lifecycle_environment_id': module_lce.id,
            },
            organization=module_org.id,
        ).create()
        assert host.content_facet_attributes['content_view_id'] == class_cv.id
        assert host.content_facet_attributes['lifecycle_environment_id'] == module_lce.id
        assert class_cv.read().content_host_count == 1

    @pytest.mark.tier2
    def test_positive_clone_within_same_env(self, class_published_cloned_cv, module_lce):
        """attempt to create, publish and promote new content view
        based on existing view within the same environment as the
        original content view

        :id: a7be5dc1-26c1-4354-99a1-1cbc90c89c64

        :expectedresults: Cloned content view can be published and promoted to
            the same environment as the original content view

        :CaseImportance: High
        """
        class_published_cloned_cv.read().version[0].promote(data={'environment_ids': module_lce.id})

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_clone_with_diff_env(
        self, module_org, class_published_cloned_cv, module_target_sat
    ):
        """attempt to create, publish and promote new content
        view based on existing view but promoted to a
        different environment

        :id: a4d21c85-a77c-4664-95ba-3d32c3ad1663

        :expectedresults: Cloned content view can be published and promoted to
            a different environment as the original content view

        :CaseImportance: Medium
        """
        le_clone = module_target_sat.api.LifecycleEnvironment(organization=module_org).create()
        class_published_cloned_cv.read().version[0].promote(data={'environment_ids': le_clone.id})

    @pytest.mark.tier2
    def test_positive_add_custom_content(self, module_product, module_org, module_target_sat):
        """Associate custom content in a view

        :id: db452e0c-0c17-40f2-bab4-8467e7a875f1

        :expectedresults: Custom content assigned and present in content view

        :CaseImportance: Critical
        """
        yum_repo = module_target_sat.api.Repository(product=module_product).create()
        yum_repo.sync()
        content_view = module_target_sat.api.ContentView(organization=module_org.id).create()
        assert len(content_view.repository) == 0
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        assert len(content_view.repository) == 1
        assert content_view.repository[0].read().name == yum_repo.name

    @pytest.mark.tier2
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_positive_add_custom_module_streams(
        self, content_view, module_product, module_org, module_target_sat
    ):
        """Associate custom content (module streams) in a view

        :id: 9e4821cb-293a-4d84-bd1f-bb9fff36b143

        :expectedresults: Custom content (module streams) assigned and present in content view

        :CaseImportance: High
        """
        yum_repo = module_target_sat.api.Repository(
            product=module_product, url=settings.repos.module_stream_1.url
        ).create()
        yum_repo.sync()
        assert len(content_view.repository) == 0
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        assert len(content_view.repository) == 1
        repo = content_view.repository[0].read()
        assert repo.name == yum_repo.name
        assert repo.content_counts['module_stream'] == 7

    @pytest.mark.tier2
    def test_negative_add_dupe_repos(
        self, content_view, module_product, module_org, module_target_sat
    ):
        """Attempt to associate the same repo multiple times within a
        content view

        :id: 9e3dff38-fdcc-4483-9844-0619797cf1d5

        :expectedresults: User cannot add repos multiple times to the view

        :CaseImportance: Low
        """
        yum_repo = module_target_sat.api.Repository(product=module_product).create()
        yum_repo.sync()
        assert len(content_view.repository) == 0
        content_view.repository = [yum_repo, yum_repo]
        with pytest.raises(HTTPError):
            content_view.update(['repository'])
        assert len(content_view.read().repository) == 0

    @pytest.mark.tier2
    @pytest.mark.pit_server
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_positive_add_sha512_rpm(self, content_view, module_org, module_target_sat):
        """Associate sha512 RPM content in a view

        :id: 1f473b02-5e2b-41ff-a706-c0635abc2476

        :expectedresults: Custom sha512 assigned and present in content view

        :CaseComponent: Pulp

        :team: Rocket

        :CaseImportance: Medium

        :customerscenario: true

        :BZ: 1639406
        """
        product = module_target_sat.api.Product(organization=module_org).create()
        yum_sha512_repo = module_target_sat.api.Repository(
            product=product, url=CUSTOM_RPM_SHA_512
        ).create()
        yum_sha512_repo.sync()
        repo_content = yum_sha512_repo.read()
        # Assert that the repository content was properly synced
        assert repo_content.content_counts['rpm'] == CUSTOM_RPM_SHA_512_FEED_COUNT['rpm']
        assert repo_content.content_counts['erratum'] == CUSTOM_RPM_SHA_512_FEED_COUNT['errata']
        content_view.repository = [yum_sha512_repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        assert len(content_view.repository) == 1
        assert len(content_view.version) == 1
        content_view_version = content_view.version[0].read()
        assert content_view_version.package_count == CUSTOM_RPM_SHA_512_FEED_COUNT['rpm']
        assert (
            content_view_version.errata_counts['total'] == CUSTOM_RPM_SHA_512_FEED_COUNT['errata']
        )


class TestContentViewCreate:
    """Create tests for content views."""

    @pytest.mark.parametrize('composite', [True, False])
    @pytest.mark.tier1
    def test_positive_create_composite(self, composite, target_sat):
        """Create composite and non-composite content views.

        :id: 4a3b616d-53ab-4396-9a50-916d6c42a401

        :parametrized: yes

        :expectedresults: Creation succeeds and content-view is composite or
            non-composite, respectively.

        :CaseImportance: Critical
        """
        assert target_sat.api.ContentView(composite=composite).create().composite == composite

    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_positive_create_with_name(self, name, target_sat):
        """Create empty content-view with random names.

        :id: 80d36498-2e71-4aa9-b696-f0a45e86267f

        :parametrized: yes

        :expectedresults: Content-view is created and had random name.

        :CaseImportance: Critical
        """
        assert target_sat.api.ContentView(name=name).create().name == name

    @pytest.mark.parametrize('desc', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_positive_create_with_description(self, desc, target_sat):
        """Create empty content view with random description.

        :id: 068e3e7c-34ac-47cb-a1bb-904d12c74cc7

        :parametrized: yes

        :expectedresults: Content-view is created and has random description.

        :CaseImportance: High
        """
        assert target_sat.api.ContentView(description=desc).create().description == desc

    @pytest.mark.tier1
    def test_positive_clone(self, content_view, module_org, module_target_sat):
        """Create a content view by copying an existing one

        :id: ee03dc63-e2b0-4a89-a828-2910405279ff

        :expectedresults: A content view is cloned with relevant parameters

        :CaseImportance: Critical
        """
        cloned_cv = module_target_sat.api.ContentView(
            id=content_view.copy(data={'name': gen_string('alpha', gen_integer(3, 30))})['id']
        ).read_json()
        cv_origin = content_view.read_json()
        uniqe_keys = ('label', 'id', 'name', 'updated_at', 'created_at')
        for key in uniqe_keys:
            del cv_origin[key]
            del cloned_cv[key]
        assert cv_origin == cloned_cv

    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    @pytest.mark.tier1
    def test_negative_create_with_invalid_name(self, name, target_sat):
        """Create content view providing an invalid name.

        :id: 261376ca-7d12-41b6-9c36-5f284865243e

        :parametrized: yes

        :expectedresults: Content View is not created

        :CaseImportance: High
        """
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(name=name).create()


class TestContentViewPublishPromote:
    """Tests for publishing and promoting content views."""

    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, module_product, class_target_sat):
        """Set up organization, product and repositories for tests."""
        request.cls.yum_repo = class_target_sat.api.Repository(product=module_product).create()
        self.yum_repo.sync()
        request.cls.swid_repo = class_target_sat.api.Repository(
            product=module_product, url=settings.repos.swid_tag.url
        ).create()
        self.swid_repo.sync()

    def add_content_views_to_composite(
        self, module_target_sat, composite_cv, module_org, cv_amount=1
    ):
        """Add necessary number of content views to the composite one

        :param composite_cv: Composite content view object
        :param cv_amount: Amount of content views to be added
        """
        cv_versions = []
        for _ in range(cv_amount):
            content_view = module_target_sat.api.ContentView(organization=module_org).create()
            content_view.publish()
            cv_versions.append(content_view.read().version[0])
        composite_cv.component = cv_versions
        composite_cv = composite_cv.update(['component'])
        assert len(composite_cv.component) == cv_amount

    @pytest.mark.tier2
    def test_positive_publish_with_content_multiple(self, content_view, module_org):
        """Give a content view yum packages and publish it repeatedly.

        :id: 7db81c1f-c69e-453f-bea4-ecad47f27c69

        :expectedresults: The yum repo is referenced from the content view, the
            content view can be published several times, and each content view
            version has at least one package.

        :CaseImportance: High
        """
        content_view.repository = [self.yum_repo]
        content_view = content_view.update(['repository'])

        # Check that the yum repo is referenced.
        assert len(content_view.repository) == 1

        # Publish the content view several times and check that each version
        # has some software packages.
        for _ in range(REPEAT):
            content_view.publish()
        for cvv in content_view.read().version:
            assert cvv.read_json()['package_count'] > 0

    @pytest.mark.tier2
    def test_positive_publish_composite_multiple_content_once(self, module_org, module_target_sat):
        """Create empty composite view and assign random number of
        normal content views to it. After that publish that composite content
        view once.

        :id: 0d56d318-46a4-4da5-871b-72a3926055dd

        :expectedresults: Composite content view is published and corresponding
            version is assigned to it.

        :CaseImportance: Critical
        """
        composite_cv = module_target_sat.api.ContentView(
            composite=True,
            organization=module_org,
        ).create()
        self.add_content_views_to_composite(
            module_target_sat, composite_cv, module_org, random.randint(2, 3)
        )
        composite_cv.publish()
        assert len(composite_cv.read().version) == 1

    @pytest.mark.tier2
    def test_positive_publish_composite_multiple_content_multiple(
        self, module_org, module_target_sat
    ):
        """Create empty composite view and assign random number of
        normal content views to it. After that publish that composite content
        view several times.

        :id: da8ad491-02f2-4b84-b850-0dea7259739c

        :expectedresults: Composite content view is published several times and
            corresponding versions are assigned to it.

        :CaseImportance: High
        """
        composite_cv = module_target_sat.api.ContentView(
            composite=True,
            organization=module_org,
        ).create()
        self.add_content_views_to_composite(composite_cv, module_org, random.randint(2, 3))

        for i in range(random.randint(2, 3)):
            composite_cv.publish()
            assert len(composite_cv.read().version) == i + 1

    @pytest.mark.tier2
    def test_positive_promote_with_yum_multiple(self, content_view, module_org, module_target_sat):
        """Give a content view a yum repo, publish it once and promote
        the content view version ``REPEAT + 1`` times.

        :id: 58783790-2839-4e91-94d3-008dc3fe3219

        :expectedresults: The content view has one repository, the content view
            version is in ``REPEAT + 1`` lifecycle environments and it has at
            least one package.

        :CaseImportance: High
        """
        content_view.repository = [self.yum_repo]
        content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()

        # Promote the content view version.
        for _ in range(REPEAT):
            lce = module_target_sat.api.LifecycleEnvironment(organization=module_org).create()
            content_view.version[0].promote(data={'environment_ids': lce.id})

        # Everything's done - check some content view attributes...
        content_view = content_view.read()
        assert len(content_view.repository) == 1
        assert len(content_view.version) == 1

        # ...and some content view version attributes.
        cvv_attrs = content_view.version[0].read_json()
        assert len(cvv_attrs['environments']) == REPEAT + 1
        assert cvv_attrs['package_count'] > 0

    @pytest.mark.tier2
    def test_positive_add_to_composite(self, content_view, module_org, module_target_sat):
        """Create normal content view, publish and add it to a new
        composite content view

        :id: 36894150-5321-4ffd-ab5a-a7ad01401cf4

        :expectedresults: Content view can be created and assigned to composite
            one through content view versions mechanism

        :CaseImportance: Critical
        """
        content_view.repository = [self.yum_repo]
        content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()

        composite_cv = module_target_sat.api.ContentView(
            composite=True,
            organization=module_org,
        ).create()
        composite_cv.component = content_view.version  # list of one CV version
        composite_cv = composite_cv.update(['component'])

        # composite CV → CV version == CV → CV version
        assert composite_cv.component[0].id == content_view.version[0].id
        # composite CV → CV version → CV == CV
        assert composite_cv.component[0].read().content_view.id == content_view.id

    @pytest.mark.tier2
    def test_negative_add_components_to_composite(
        self, content_view, module_org, module_target_sat
    ):
        """Attempt to associate components in a non-composite content
        view

        :id: 60aa7a4e-df6e-407e-86c7-a4c540bda8b5

        :expectedresults: User cannot add components to the view

        :CaseImportance: Low
        """
        content_view.repository = [self.yum_repo]
        content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        non_composite_cv = module_target_sat.api.ContentView(
            composite=False,
            organization=module_org,
        ).create()
        non_composite_cv.component = content_view.version  # list of one cvv
        with pytest.raises(HTTPError):
            non_composite_cv.update(['component'])
        assert len(non_composite_cv.read().component) == 0

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_promote_composite_multiple_content_once(
        self, module_lce, module_org, module_target_sat
    ):
        """Create empty composite view and assign random number of
        normal content views to it. After that promote that composite
        content view once.

        :id: 20389383-7510-421c-803a-e73de9db941a

        :expectedresults: Composite content view version points to ``Library +
            1`` lifecycle environments after the promotions.

        :CaseImportance: High
        """
        composite_cv = module_target_sat.api.ContentView(
            composite=True,
            organization=module_org,
        ).create()
        self.add_content_views_to_composite(composite_cv, module_org, random.randint(2, 3))
        composite_cv.publish()
        composite_cv.read().version[0].promote(data={'environment_ids': module_lce.id})
        composite_cv = composite_cv.read()
        assert len(composite_cv.version) == 1
        assert len(composite_cv.version[0].read().environment) == 2

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_promote_composite_multiple_content_multiple(
        self, module_org, module_target_sat
    ):
        """Create empty composite view and assign random number of
        normal content views to it. After that promote that composite content
        view ``Library + random`` times.

        :id: 368811fe-f24a-48a5-b883-9c1d08a03d6b

        :expectedresults: Composite content view version points to ``Library +
            random`` lifecycle environments after the promotions.

        :CaseImportance: High
        """
        composite_cv = module_target_sat.api.ContentView(
            composite=True,
            organization=module_org,
        ).create()
        self.add_content_views_to_composite(composite_cv, module_org, random.randint(2, 3))
        composite_cv.publish()
        composite_cv = composite_cv.read()

        envs_amount = random.randint(2, 3)
        for _ in range(envs_amount):
            lce = module_target_sat.api.LifecycleEnvironment(organization=module_org).create()
            composite_cv.version[0].promote(data={'environment_ids': lce.id})
        composite_cv = composite_cv.read()
        assert len(composite_cv.version) == 1
        assert len(composite_cv.version[0].read().environment) == envs_amount + 1

    @pytest.mark.tier2
    def test_positive_promote_out_of_sequence(self, content_view, module_org):
        """Try to publish content view few times in a row and then re-promote
        first version to default environment

        :id: 40d20aba-726f-48e3-93b7-fb1ab1851ac7

        :expectedresults: Content view promoted out of sequence properly

        :CaseImportance: Medium
        """
        for _ in range(REPEAT):
            content_view.publish()
        content_view = content_view.read()
        # Check that CV is published and has proper number of CV versions.
        assert len(content_view.version) == REPEAT
        content_view.version.sort(key=lambda version: version.id)
        # After each publish operation application re-assign environment to
        # latest CV version. Correspondingly, at that moment, first cv version
        # should have 0 environments and latest should have one ('Library')
        # assigned to it.
        assert len(content_view.version[0].read().environment) == 0
        lce_list = content_view.version[-1].read().environment
        assert len(lce_list) == 1
        # Trying to re-promote 'Library' environment from latest version to
        # first one
        content_view.version[0].promote(data={'environment_ids': lce_list[0].id, 'force': True})
        content_view = content_view.read()
        content_view.version.sort(key=lambda version: version.id)
        # Verify that, according to our plan, first version contains one
        # environment and latest - 0
        assert len(content_view.version[0].read().environment) == 1
        assert len(content_view.version[-1].read().environment) == 0

    @pytest.mark.tier3
    @pytest.mark.pit_server
    def test_positive_publish_multiple_repos(self, content_view, module_org, module_target_sat):
        """Attempt to publish a content view with multiple YUM repos.

        :id: 5557a33b-7a6f-45f5-9fe4-23a704ed9e21

        :expectedresults: Content view publish should not raise an exception.

        :CaseComponent: Pulp

        :team: Rocket

        :CaseImportance: Medium

        :customerscenario: true

        :BZ: 1651930
        """
        product = module_target_sat.api.Product(organization=module_org).create()
        for _ in range(10):
            repo = module_target_sat.api.Repository(product=product).create()
            repo.sync()
            content_view.repository.append(repo)
            content_view = content_view.update(['repository'])
        content_view = content_view.read()
        assert len(content_view.repository) == 10
        content_view.publish()
        assert len(content_view.read().version) == 1

    @pytest.mark.tier2
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_composite_content_view_with_same_repos(self, module_org, target_sat):
        """Create a Composite Content View with content views having same yum repo.
        Add filter on the content views and check the package count for composite content view
        should not be changed.

        :id: 957f3758-ca1e-4a1f-8e7d-171750e0eb87

        :expectedresults: package count for composite content view should not be changed in
            case of mismatch.

        :bz: 1639390

        :customerscenario: true

        :CaseImportance: Medium
        """
        product = target_sat.api.Product(organization=module_org).create()
        repo = target_sat.api.Repository(
            content_type='yum', product=product, url=settings.repos.module_stream_1.url
        ).create()
        repo.sync()
        content_view_1 = target_sat.api.ContentView(organization=module_org).create()
        content_view_2 = target_sat.api.ContentView(organization=module_org).create()

        # create content views with same repo and different filter
        for content_view, package in [(content_view_1, 'camel'), (content_view_2, 'cow')]:
            content_view.repository = [repo]
            content_view.update(['repository'])
            content_view_info = apply_package_filter(content_view, repo, package, inclusion=False)
            assert content_view_info.package_count == 35

        # create composite content view with these two published content views
        comp_content_view = target_sat.api.ContentView(
            composite=True,
            organization=module_org,
        ).create()
        content_view_1 = content_view_1.read()
        content_view_2 = content_view_2.read()
        for content_view_version in [content_view_1.version[-1], content_view_2.version[-1]]:
            comp_content_view.component.append(content_view_version)
            comp_content_view = comp_content_view.update(['component'])
        comp_content_view.publish()
        comp_content_view = comp_content_view.read()
        comp_content_view_info = comp_content_view.version[0].read()
        assert comp_content_view_info.package_count == 36


class TestContentViewUpdate:
    """Tests for updating content views."""

    @pytest.mark.parametrize(
        ('key', 'value'),
        **(lambda x: {'argvalues': list(x.items()), 'ids': list(x.keys())})(
            {'description': gen_utf8(), 'name': gen_utf8()}
        ),
    )
    @pytest.mark.tier1
    def test_positive_update_attributes(self, module_cv, key, value):
        """Update a content view and provide valid attributes.

        :id: 3f1457f2-586b-472c-8053-99017c4a4909

        :parametrized: yes

        :expectedresults: The update succeeds.

        :CaseImportance: Critical
        """
        setattr(module_cv, key, value)
        content_view = module_cv.update({key})
        assert getattr(content_view, key) == value

    @pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_positive_update_name(self, module_cv, new_name, module_target_sat):
        """Create content view providing the initial name, then update
        its name to another valid name.

        :id: 15e6fa3a-1a65-4e7d-8d32-3a81227ac1c8

        :parametrized: yes

        :expectedresults: Content View is created, and its name can be updated.

        :CaseImportance: Critical
        """
        module_cv.name = new_name
        module_cv.update(['name'])
        updated = module_target_sat.api.ContentView(id=module_cv.id).read()
        assert new_name == updated.name

    @pytest.mark.parametrize('new_name', **parametrized(invalid_names_list()))
    @pytest.mark.tier1
    def test_negative_update_name(self, module_cv, new_name, module_target_sat):
        """Create content view then update its name to an
        invalid name.

        :id: 69a2ce8d-19b2-49a3-97db-a1fdebbb16be

        :parametrized: yes

        :expectedresults: Content View is created, and its name is not updated.

        :CaseImportance: Critical
        """
        module_cv.name = new_name
        with pytest.raises(HTTPError):
            module_cv.update(['name'])
        cv = module_cv.read()
        assert cv.name != new_name


class TestContentViewDelete:
    """Tests for deleting content views."""

    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    @pytest.mark.tier1
    def test_positive_delete(self, content_view, name, target_sat):
        """Create content view and then delete it.

        :id: d582f1b3-8118-4e78-a639-237c6f9d27c6

        :parametrized: yes

        :expectedresults: Content View is successfully deleted.

        :CaseImportance: Critical
        """
        content_view.delete()
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(id=content_view.id).read()


@pytest.mark.run_in_one_thread
class TestContentViewRedHatContent:
    """Tests for publishing and promoting content views."""

    @pytest.fixture(scope='class', autouse=True)
    def initiate_testclass(
        self, request, module_cv, module_entitlement_manifest_org, class_target_sat
    ):
        """Set up organization, product and repositories for tests."""

        repo_id = class_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_entitlement_manifest_org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        request.cls.repo = class_target_sat.api.Repository(id=repo_id)
        self.repo.sync()
        module_cv.repository = [self.repo]
        module_cv.update(['repository'])
        request.cls.yumcv = module_cv.read()

    @pytest.mark.tier2
    def test_positive_add_rh(self):
        """associate Red Hat content in a view

        :id: f011a269-813d-4e82-afe8-f106b23cb03e

        :expectedresults: RH Content assigned and present in a view

        :CaseImportance: High
        """
        assert len(self.yumcv.repository) == 1
        assert self.yumcv.repository[0].read().name == REPOS['rhst7']['name']

    @pytest.mark.tier2
    def test_positive_add_rh_custom_spin(self, target_sat):
        """Associate Red Hat content in a view and filter it using rule

        :id: 30c3103d-9503-4501-8117-1f2d25353215

        :expectedresults: Filtered RH content is available and can be seen in a
            view

        :CaseImportance: High
        """
        # content_view ← cv_filter
        cv_filter = target_sat.api.RPMContentViewFilter(
            content_view=self.yumcv,
            inclusion='true',
            name=gen_string('alphanumeric'),
        ).create()
        assert self.yumcv.id == cv_filter.content_view.id

        # content_view ← cv_filter ← cv_filter_rule
        cv_filter_rule = target_sat.api.ContentViewFilterRule(
            content_view_filter=cv_filter, name=gen_string('alphanumeric'), version='1.0'
        ).create()
        assert cv_filter.id == cv_filter_rule.content_view_filter.id

    @pytest.mark.tier2
    def test_positive_update_rh_custom_spin(self, target_sat):
        """Edit content views for a custom rh spin.  For example,
        modify a filter

        :id: 81d77ecd-8bac-44c6-8bc2-b6e38ad77a0b

        :expectedresults: edited content view save is successful and info is
            updated

        :CaseImportance: High
        """
        cvf = target_sat.api.ErratumContentViewFilter(
            content_view=self.yumcv,
        ).create()
        assert self.yumcv.id == cvf.content_view.id

        cv_filter_rule = target_sat.api.ContentViewFilterRule(
            content_view_filter=cvf, types=[FILTER_ERRATA_TYPE['enhancement']]
        ).create()
        assert cv_filter_rule.types == [FILTER_ERRATA_TYPE['enhancement']]

        cv_filter_rule.types = [FILTER_ERRATA_TYPE['bugfix']]
        cv_filter_rule = cv_filter_rule.update(['types'])
        assert cv_filter_rule.types == [FILTER_ERRATA_TYPE['bugfix']]

    @pytest.mark.tier2
    def test_positive_publish_rh(self, module_org, content_view):
        """Attempt to publish a content view containing Red Hat content

        :id: 4f1698ef-a23b-48d6-be25-dbbf2d76c95c

        :expectedresults: Content view can be published

        :CaseImportance: Critical
        """
        content_view.repository = [self.repo]
        content_view.update(['repository'])
        content_view.publish()
        assert len(content_view.read().version) == 1

    @pytest.mark.tier2
    def test_positive_publish_rh_custom_spin(self, module_org, content_view, module_target_sat):
        """Attempt to publish a content view containing Red Hat spin - i.e.,
        contains filters.

        :id: 094a8c46-935b-4dbc-830e-19bec935276c

        :expectedresults: Content view can be published

        :CaseImportance: High
        """
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        module_target_sat.api.RPMContentViewFilter(
            content_view=content_view, inclusion='true', name=gen_string('alphanumeric')
        ).create()
        content_view.publish()
        assert len(content_view.read().version) == 1

    @pytest.mark.tier2
    def test_positive_promote_rh(self, module_org, content_view, module_lce):
        """Attempt to promote a content view containing Red Hat content

        :id: 991dd9cc-5818-42dc-9098-66b312adfd97

        :expectedresults: Content view can be promoted

        :CaseImportance: Critical
        """
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view.read().version[0].promote(
            data={
                'environment_ids': module_lce.id,
                'force': False,
            }
        )
        assert len(content_view.read().version[0].read().environment) == 2

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_promote_rh_custom_spin(self, content_view, module_lce, module_target_sat):
        """Attempt to promote a content view containing Red Hat spin - i.e.,
        contains filters.

        :id: 8331ba11-1742-425f-83b1-6b06c5785572

        :expectedresults: Content view can be promoted

        :CaseImportance: High
        """
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        module_target_sat.api.RPMContentViewFilter(
            content_view=content_view, inclusion='true', name=gen_string('alphanumeric')
        ).create()
        content_view.publish()
        content_view.read().version[0].promote(data={'environment_ids': module_lce.id})
        assert len(content_view.read().version[0].read().environment) == 2


@pytest.mark.tier2
def test_positive_admin_user_actions(
    target_sat, content_view, function_role, module_org, module_lce
):
    """Attempt to manage content views

    :id: 75b638af-d132-4b5e-b034-a373565c72b4

    :steps: with global admin account:

        1. create a user with all content views permissions
        2. create lifecycle environment
        3. create 2 content views (one to delete, the other to manage)

    :setup: create a user with all content views permissions

    :expectedresults: The user can Read, Modify, Delete, Publish, Promote
        the content views

    :CaseImportance: Critical
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    # create a role with all content views permissions
    for res_type in ['Katello::ContentView', 'Katello::KTEnvironment']:
        permission = target_sat.api.Permission().search(
            query={'search': f'resource_type="{res_type}"'}
        )
        target_sat.api.Filter(
            organization=[module_org], permission=permission, role=function_role
        ).create()
    # create a user and assign the above created role
    target_sat.api.User(
        organization=[module_org],
        role=[function_role],
        login=user_login,
        password=user_password,
    ).create()
    cfg = user_nailgun_config(user_login, user_password)
    # Check that we cannot create random entity due permission restriction
    with pytest.raises(HTTPError):
        target_sat.api.Domain(server_config=cfg).create()
    # Check Read functionality
    content_view = target_sat.api.ContentView(server_config=cfg, id=content_view.id).read()
    # Check Modify functionality
    target_sat.api.ContentView(
        server_config=cfg, id=content_view.id, name=gen_string('alpha')
    ).update(['name'])
    # Publish the content view.
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    # Promote the content view version.
    content_view.version[0].promote(data={'environment_ids': module_lce.id})
    # Check Delete functionality
    content_view = target_sat.api.ContentView(organization=module_org).create()
    content_view = target_sat.api.ContentView(server_config=cfg, id=content_view.id).read()
    content_view.delete()
    with pytest.raises(HTTPError):
        content_view.read()


@pytest.mark.tier2
def test_positive_readonly_user_actions(target_sat, function_role, content_view, module_org):
    """Attempt to view content views

    :id: cdfd6e51-cd46-4afa-807c-98b2195fcf0e

    :setup:

        1. create a user with the Content View read-only role
        2. create content view
        3. add a custom repository to content view

    :expectedresults: User with read-only role for content view can view
        the repository in the content view

    :CaseImportance: Critical
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    # create a role with content views read only permissions
    target_sat.api.Filter(
        organization=[module_org],
        permission=target_sat.api.Permission().search(
            filters={'name': 'view_content_views'},
            query={'search': 'resource_type="Katello::ContentView"'},
        ),
        role=function_role,
    ).create()
    # create read only products permissions and assign it to our role
    target_sat.api.Filter(
        organization=[module_org],
        permission=target_sat.api.Permission().search(
            filters={'name': 'view_products'},
            query={'search': 'resource_type="Katello::Product"'},
        ),
        role=function_role,
    ).create()
    # create a user and assign the above created role
    target_sat.api.User(
        organization=[module_org],
        role=[function_role],
        login=user_login,
        password=user_password,
    ).create()
    # add repository to the created content view
    product = target_sat.api.Product(organization=module_org).create()
    yum_repo = target_sat.api.Repository(product=product).create()
    yum_repo.sync()
    content_view.repository = [yum_repo]
    content_view = content_view.update(['repository'])
    assert len(content_view.repository) == 1
    cfg = user_nailgun_config(user_login, user_password)
    # Check that we can read content view repository information using user
    # with read only permissions
    content_view = target_sat.api.ContentView(server_config=cfg, id=content_view.id).read()
    assert len(content_view.repository) == 1
    assert content_view.repository[0].read().name == yum_repo.name


@pytest.mark.tier2
def test_negative_readonly_user_actions(
    target_sat, function_role, content_view, module_org, module_lce
):
    """Attempt to manage content views

    :id: 8c8cc3a2-a356-4645-9517-ca5bce836969

    :setup:

        1. create a user with the Content View read-only role
        2. create content view
        3. add a custom repository to content view

    :expectedresults: User with read only role for content view cannot
        Modify, Delete, Publish, Promote the content views.  Same user cannot
        create Product, Host Collection, or Activation key

    :BZ: 1922134

    :CaseImportance: Critical
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    # create a role with content views read only permissions
    target_sat.api.Filter(
        organization=[module_org],
        permission=target_sat.api.Permission().search(
            filters={'name': 'view_content_views'},
            query={'search': 'resource_type="Katello::ContentView"'},
        ),
        role=function_role,
    ).create()
    # create environment permissions and assign it to our role
    target_sat.api.Filter(
        organization=[module_org],
        permission=target_sat.api.Permission().search(
            query={'search': 'resource_type="Katello::KTEnvironment"'}
        ),
        role=function_role,
    ).create()
    # create a user and assign the above created role
    target_sat.api.User(
        organization=[module_org],
        role=[function_role],
        login=user_login,
        password=user_password,
    ).create()
    cfg = user_nailgun_config(user_login, user_password)
    # Check that we cannot create content view due read-only permission
    with pytest.raises(HTTPError):
        target_sat.api.ContentView(server_config=cfg, organization=module_org).create()
    # Check that we can read our content view with custom user
    content_view = target_sat.api.ContentView(server_config=cfg, id=content_view.id).read()
    # Check that we cannot modify content view with custom user
    with pytest.raises(HTTPError):
        target_sat.api.ContentView(
            server_config=cfg, id=content_view.id, name=gen_string('alpha')
        ).update(['name'])
    # Check that we cannot delete content view due read-only permission
    with pytest.raises(HTTPError):
        content_view.delete()
    # Check that we cannot publish content view
    with pytest.raises(HTTPError):
        content_view.publish()
    # Check that we cannot promote content view
    content_view = target_sat.api.ContentView(id=content_view.id).read()
    content_view.publish()
    content_view = target_sat.api.ContentView(server_config=cfg, id=content_view.id).read()
    assert len(content_view.version), 1
    with pytest.raises(HTTPError):
        content_view.read().version[0].promote(data={'environment_ids': module_lce.id})
    # Check that we cannot create a Product
    with pytest.raises(HTTPError):
        target_sat.api.Product(server_config=cfg).create()
    # Check that we cannot create an activation key
    with pytest.raises(HTTPError):
        target_sat.api.ActivationKey(server_config=cfg).create()
    # Check that we cannot create a host collection
    with pytest.raises(HTTPError):
        target_sat.api.HostCollection(server_config=cfg).create()


@pytest.mark.tier2
def test_negative_non_readonly_user_actions(target_sat, content_view, function_role, module_org):
    """Attempt to view content views

    :id: b0a53c38-72f1-4731-881e-192134df6ef3

    :setup: create a user with all Content View permissions except 'view'
        role

    :expectedresults: the user can perform different operations against
        content view, but not read it

    :CaseImportance: Critical
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    # create a role with all content views permissions except
    # view_content_views
    cv_permissions_entities = target_sat.api.Permission().search(
        query={'search': 'resource_type="Katello::ContentView"'}
    )
    user_cv_permissions = list(PERMISSIONS['Katello::ContentView'])
    user_cv_permissions.remove('view_content_views')
    user_cv_permissions_entities = [
        entity for entity in cv_permissions_entities if entity.name in user_cv_permissions
    ]
    target_sat.api.Filter(
        organization=[module_org],
        permission=user_cv_permissions_entities,
        role=function_role,
    ).create()
    # create a user and assign the above created role
    target_sat.api.User(
        organization=[module_org],
        role=[function_role],
        login=user_login,
        password=user_password,
    ).create()
    # Check that we cannot read our content view with custom user
    user_cfg = user_nailgun_config(user_login, user_password)
    with pytest.raises(HTTPError):
        target_sat.api.ContentView(server_config=user_cfg, id=content_view.id).read()
    # Check that we have permission to remove the entity
    target_sat.api.ContentView(server_config=user_cfg, id=content_view.id).delete()
    with pytest.raises(HTTPError):
        target_sat.api.ContentView(id=content_view.id).read()


@pytest.mark.skip_if_open("BZ:1625783")
class TestOstreeContentView:
    """Tests for ostree contents in content views."""

    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    @pytest.fixture(scope='class', autouse=True)
    def initiate_testclass(self, request, module_product, class_target_sat):
        """Set up organization, product and repositories for tests."""
        request.cls.ostree_repo = class_target_sat.api.Repository(
            product=module_product,
            content_type='ostree',
            url=FEDORA_OSTREE_REPO,
            unprotected=False,
        ).create()
        self.ostree_repo.sync()
        # Create new yum repository
        request.cls.yum_repo = class_target_sat.api.Repository(
            url=settings.repos.yum_1.url,
            product=module_product,
        ).create()
        self.yum_repo.sync()
        # Create new docker repository
        request.cls.docker_repo = class_target_sat.api.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=module_product,
            url=CONTAINER_REGISTRY_HUB,
        ).create()
        self.docker_repo.sync()

    @pytest.mark.tier2
    def test_positive_add_custom_ostree_content(self, content_view):
        """Associate custom ostree content in a view

        :id: 209e59b0-c73d-4a5f-a1dc-0d74dff9a084

        :expectedresults: Custom ostree content assigned and present in content
            view

        :CaseImportance: High
        """
        assert len(content_view.repository) == 0
        content_view.repository = [self.ostree_repo]
        content_view = content_view.update(['repository'])
        assert len(content_view.repository) == 1
        assert content_view.repository[0].read().name == self.ostree_repo.name

    @pytest.mark.tier2
    def test_positive_publish_custom_ostree(self, content_view):
        """Publish a content view with custom ostree contents

        :id: e5f5c940-20e5-406f-9d27-a703195a3b88

        :expectedresults: Content-view with Custom ostree published
            successfully

        :CaseImportance: High
        """
        content_view.repository = [self.ostree_repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        assert len(content_view.read().version) == 1

    @pytest.mark.tier2
    def test_positive_promote_custom_ostree(self, content_view, module_lce):
        """Promote a content view with custom ostree contents

        :id: 3d9f3641-0776-45f7-bf1e-7d5779346b93

        :expectedresults: Content-view with custom ostree contents promoted
            successfully

        :CaseImportance: High
        """
        content_view.repository = [self.ostree_repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view.read().version[0].promote(
            data={'environment_ids': module_lce.id, 'force': False}
        )
        assert len(content_view.read().version[0].read().environment) == 2

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_publish_promote_with_custom_ostree_and_other(self, content_view, module_lce):
        """Publish & Promote a content view with custom ostree and other contents

        :id: 690ec30a-56ac-4478-afb2-be34a85a614a

        :expectedresults: Content-view with custom ostree and other contents
            promoted successfully

        :CaseImportance: High
        """
        content_view.repository = [self.ostree_repo, self.yum_repo, self.docker_repo]
        content_view = content_view.update(['repository'])
        assert len(content_view.repository) == 3
        content_view.publish()
        assert len(content_view.read().version) == 1
        content_view.read().version[0].promote(
            data={'environment_ids': module_lce.id, 'force': False}
        )
        assert len(content_view.read().version[0].read().environment) == 2


@pytest.mark.skip_if_open("BZ:1625783")
class TestContentViewRedHatOstreeContent:
    """Tests for publishing and promoting cv with RH ostree contents."""

    @pytest.mark.run_in_one_thread
    @pytest.fixture(scope='class', autouse=True)
    def initiate_testclass(self, request, module_entitlement_manifest_org, class_target_sat):
        """Set up organization, product and repositories for tests."""

        repo_id = class_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=None,
            org_id=module_entitlement_manifest_org.id,
            product=PRDS['rhah'],
            repo=REPOS['rhaht']['name'],
            reposet=REPOSET['rhaht'],
            releasever=None,
        )
        request.cls.repo = class_target_sat.api.Repository(id=repo_id)
        self.repo.sync()

    @pytest.mark.tier2
    def test_positive_add_rh_ostree_content(self, content_view):
        """Associate RH atomic ostree content in a view

        :id: 81883f05-e47f-45fa-bea4-c733da9cf30c

        :expectedresults: RH atomic ostree content assigned and present in
            content view

        :CaseImportance: High
        """
        assert len(content_view.repository) == 0
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        assert len(content_view.repository) == 1
        assert content_view.repository[0].read().name == REPOS['rhaht']['name']

    @pytest.mark.tier2
    def test_positive_publish_RH_ostree(self, content_view):
        """Publish a content view with RH ostree contents

        :id: 067ebb6e-2dad-4932-ae84-64c4373c9cb8

        :expectedresults: Content-view with RH ostree contents published
            successfully

        :CaseImportance: High
        """
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        assert len(content_view.read().version) == 1

    @pytest.mark.tier2
    def test_positive_promote_RH_ostree(self, content_view, module_lce):
        """Promote a content view with RH ostree contents

        :id: 447a96e0-331b-447c-9a8d-423d1b22ef6a

        :expectedresults: Content-view with RH ostree contents promoted
            successfully

        :CaseImportance: High
        """
        content_view.repository = [self.repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view.read().version[0].promote(
            data={'environment_ids': module_lce.id, 'force': False}
        )
        assert len(content_view.read().version[0].read().environment) == 2

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_publish_promote_with_RH_ostree_and_other(
        self, content_view, module_org, module_lce, module_target_sat
    ):
        """Publish & Promote a content view with RH ostree and other contents

        :id: def6caa3-ac31-42fa-9579-39a18b8244bd

        :expectedresults: Content-view with RH ostree and other contents
            promoted successfully

        :CaseImportance: High
        """
        repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        # Sync repository
        rpm_repo = module_target_sat.api.Repository(id=repo_id)
        rpm_repo.sync()
        content_view.repository = [self.repo, rpm_repo]
        content_view = content_view.update(['repository'])
        assert len(content_view.repository) == 2
        content_view.publish()
        content_view.read().version[0].promote(
            data={'environment_ids': module_lce.id, 'force': False}
        )
        assert len(content_view.read().version[0].read().environment) == 2
