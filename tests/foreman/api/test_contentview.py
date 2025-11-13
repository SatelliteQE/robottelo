"""Unit tests for the ``content_views`` paths.

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Artemis

:CaseImportance: High

"""

from datetime import UTC, datetime, timedelta
import random

from fauxfactory import gen_integer, gen_string, gen_utf8
import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings, user_nailgun_config
from robottelo.constants import (
    CUSTOM_RPM_SHA_512_FEED_COUNT,
    DEFAULT_ARCHITECTURE,
    PERMISSIONS,
    PRDS,
    REPOS,
    REPOSET,
    DataFile,
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
    return content_view.version[0].read()


class TestContentView:
    @pytest.mark.upgrade
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
        assert host.content_facet_attributes['content_view']['id'] == class_cv.id
        assert host.content_facet_attributes['lifecycle_environment']['id'] == module_lce.id
        assert class_cv.read().content_host_count == 1

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

    @pytest.mark.pit_server
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_positive_add_sha512_rpm(self, content_view, module_org, module_target_sat):
        """Associate sha512 RPM content in a view

        :id: 1f473b02-5e2b-41ff-a706-c0635abc2476

        :expectedresults: Custom sha512 assigned and present in content view

        :CaseComponent: Pulp

        :team: Artemis

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

    def test_ccv_promote_registry_name_change(self, module_target_sat, module_sca_manifest_org):
        """Testing CCV promotion scenarios where the registry_name has been changed to some
        specific value.

        :id: 41641d4a-d144-4833-869a-284624df2410

        :steps:

            1) Sync a RH Repo
            2) Create a CV, add the repo and publish it
            3) Create a CCV and add the CV version to it, then publish it
            4) Create LCEs with the specific value for registry_name
            5) Promote the CCV to both LCEs

        :expectedresults: CCV can be promoted to both LCEs without issue.

        :CaseImportance: High

        :customerscenario: true

        :BZ: 2153523
        """
        rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=module_sca_manifest_org.id,
            product=REPOS['kickstart']['rhel8_aps']['product'],
            repo=REPOS['kickstart']['rhel8_aps']['name'],
            reposet=REPOS['kickstart']['rhel8_aps']['reposet'],
            releasever=REPOS['kickstart']['rhel8_aps']['version'],
        )
        repo = module_target_sat.api.Repository(id=rh_repo_id).read()
        repo.sync(timeout=600)
        cv = module_target_sat.api.ContentView(organization=module_sca_manifest_org).create()
        cv = module_target_sat.api.ContentView(id=cv.id, repository=[repo]).update(["repository"])
        cv.publish()
        cv = cv.read()
        composite_cv = module_target_sat.api.ContentView(
            organization=module_sca_manifest_org, composite=True
        ).create()
        composite_cv.component = [cv.version[0]]
        composite_cv = composite_cv.update(['component'])
        composite_cv.publish()
        composite_cv = composite_cv.read()
        # Create LCEs with the specific registry value
        lce1 = module_target_sat.api.LifecycleEnvironment(
            organization=module_sca_manifest_org,
            registry_name_pattern='<%= repository.name %>',
        ).create()
        lce2 = module_target_sat.api.LifecycleEnvironment(
            organization=module_sca_manifest_org,
            registry_name_pattern='<%= lifecycle_environment.label %>/<%= repository.name %>',
        ).create()
        version = composite_cv.version[0].read()
        assert 'success' in version.promote(data={'environment_ids': lce1.id})['result']
        assert 'success' in version.promote(data={'environment_ids': lce2.id})['result']


class TestContentViewCreate:
    """Create tests for content views."""

    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_with_name(self, name, target_sat):
        """Create empty content-view with random names.

        :id: 80d36498-2e71-4aa9-b696-f0a45e86267f

        :parametrized: yes

        :expectedresults: Content-view is created and had random name.

        :CaseImportance: Critical
        """
        assert target_sat.api.ContentView(name=name).create().name == name

    @pytest.mark.parametrize('desc', **parametrized(valid_data_list()))
    def test_positive_create_with_description(self, desc, target_sat):
        """Create empty content view with random description.

        :id: 068e3e7c-34ac-47cb-a1bb-904d12c74cc7

        :parametrized: yes

        :expectedresults: Content-view is created and has random description.

        :CaseImportance: High
        """
        assert target_sat.api.ContentView(description=desc).create().description == desc

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
        self.add_content_views_to_composite(
            module_target_sat, composite_cv, module_org, random.randint(2, 3)
        )

        for i in range(random.randint(2, 3)):
            composite_cv.publish()
            assert len(composite_cv.read().version) == i + 1

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

    def test_negative_publish_during_repo_sync(self, content_view, module_target_sat):
        """Attempt to publish a new version of the content-view,
        while an associated repository is being synced.

        :id: c272fff7-a679-4844-a261-80830cdd5694

        :BZ: 1957144

        :steps:
            1. Add repository to content-view
            2. Perform asynchronous repository sync
            3. Attempt to publish a version of the content-view, while repo sync ongoing.

        :expectedresults:
            1. User cannot publish during repository sync.
            2. HTTP exception raised, assert publish task failed for expected reason,
                repo sync task_id found in humanized error, content-view versions unchanged.
        """
        org = content_view.organization.read()
        # add repository to content-view
        content_view.repository = [self.yum_repo]
        content_view.update(['repository'])
        content_view = content_view.read()
        existing_versions = content_view.version
        timestamp = (datetime.now(UTC) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M')

        # perform async repository sync, while still in progress-
        # attempt to publish a new version of the content view.
        repo_task_id = self.yum_repo.sync(synchronous=False)['id']
        with pytest.raises(HTTPError) as InternalServerError:
            content_view.publish()
        assert str(content_view.id) in str(InternalServerError)
        # search for failed publish task
        task_action = f"Publish content view '{content_view.name}', organization '{org.name}'"
        task_search = module_target_sat.api.ForemanTask().search(
            query={'search': f'{task_action} and started_at >= "{timestamp}"'}
        )
        assert len(task_search) > 0
        task_id = task_search[0].id
        # publish task failed for expected reason
        task = module_target_sat.api.ForemanTask(id=task_id).poll(must_succeed=False)
        assert task['result'] == 'error'
        assert len(task['humanized']['errors']) == 1
        assert repo_task_id in task['humanized']['errors'][0]
        # no new versions of content view, any existing remained the same
        assert content_view.read().version == existing_versions

    @pytest.mark.upgrade
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
        self.add_content_views_to_composite(
            module_target_sat, composite_cv, module_org, random.randint(2, 3)
        )
        composite_cv.publish()
        composite_cv.read().version[0].promote(data={'environment_ids': module_lce.id})
        composite_cv = composite_cv.read()
        assert len(composite_cv.version) == 1
        assert len(composite_cv.version[0].read().environment) == 2

    @pytest.mark.upgrade
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
        self.add_content_views_to_composite(
            module_target_sat, composite_cv, module_org, random.randint(2, 3)
        )
        composite_cv.publish()
        composite_cv = composite_cv.read()

        envs_amount = random.randint(2, 3)
        for _ in range(envs_amount):
            lce = module_target_sat.api.LifecycleEnvironment(organization=module_org).create()
            composite_cv.version[0].promote(data={'environment_ids': lce.id})
        composite_cv = composite_cv.read()
        assert len(composite_cv.version) == 1
        assert len(composite_cv.version[0].read().environment) == envs_amount + 1

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

    @pytest.mark.pit_server
    def test_positive_publish_multiple_repos(self, content_view, module_org, module_target_sat):
        """Attempt to publish a content view with multiple YUM repos.

        :id: 5557a33b-7a6f-45f5-9fe4-23a704ed9e21

        :expectedresults: Content view publish should not raise an exception.

        :CaseComponent: Pulp

        :team: Artemis

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
            content_view_info = apply_package_filter(
                content_view, repo, package, target_sat, inclusion=False
            )
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

    @pytest.mark.e2e
    def test_ccv_audit_scenarios(self, module_org, target_sat):
        """Check for various scenarios where a composite content view or it's component
        content views needs_publish flags should be set to true and that they properly
        get set and unset

        :id: cdd94ab8-da31-40ac-ab81-02472517e9bf

        :steps:

            1. Create a ccv
            2. Add some content views to the composite view
            3. Remove a content view from the composite view
            4. Add a CV that has `latest` set to true to the composite view
            5. Publish a new version of that CV
            6. Publish a new version of another CV in the CCV, and update it to latest

        :expectedresults: When appropriate, a ccv and it's cvs needs_publish flags get
            set or unset

        :CaseImportance: High
        """
        composite_cv = target_sat.api.ContentView(composite=True).create()
        # Needs_publish is set to True on creation
        assert composite_cv.read().needs_publish
        composite_cv.publish()
        assert not composite_cv.read().needs_publish
        # Add some content_views to the composite view
        self.add_content_views_to_composite(target_sat, composite_cv, module_org, 2)
        # Needs_publish should be set to True when a component CV is added/removed
        assert composite_cv.read().needs_publish
        composite_cv.publish()
        assert not composite_cv.read().needs_publish
        component_cvs = composite_cv.read().component
        # Remove a component cv, should need publish now
        component_cvs.pop(1)
        composite_cv.component = component_cvs
        composite_cv = composite_cv.update(['component'])
        assert composite_cv.read().needs_publish
        composite_cv.publish()
        assert not composite_cv.read().needs_publish
        # add a CV that has `latest` set to true
        new_cv = target_sat.api.ContentView().create()
        new_cv.publish()
        composite_cv.content_view_component[0].add(
            data={"components": [{"content_view_id": new_cv.id, "latest": "true"}]}
        )
        assert composite_cv.read().needs_publish
        composite_cv.publish()
        assert not composite_cv.read().needs_publish
        # a new version of a component cv that has "latest" - needs publish
        new_cv.publish()
        assert composite_cv.read().needs_publish
        composite_cv.publish()
        assert not composite_cv.read().needs_publish
        # a component CV was changed to "always update" when ccv has old version - needs publish
        # update composite_cv after changes
        composite_cv = composite_cv.read()
        # get the first CV that was added, which has 1 version
        old_component = composite_cv.content_view_component[0].read()
        old_component.content_view.publish()
        old_component.latest = True
        old_component = old_component.update(['latest'])
        # set latest to true and see if CV needs publish
        assert composite_cv.read().needs_publish
        composite_cv.publish()
        assert not composite_cv.read().needs_publish

    def test_check_needs_publish_flag(self, target_sat):
        """Check that the publish_only_if_needed option in the API works as intended (defaults to
        false, is able to be overridden to true, and if so gives the appropriate message
        if the cvs needs_publish flag is set to false)

        :id: 6e4aa845-db08-4cc3-a960-ea64fb20f50c

        :expectedresults: The publish_only_if_needed flag is working as intended, and is defaulted
            to false

        :CaseImportance: High
        """
        cv = target_sat.api.ContentView().create()
        assert cv.publish()
        assert not cv.read().needs_publish
        with pytest.raises(HTTPError):
            assert (
                cv.publish(data={'publish_only_if_needed': True})['displayMessage']
                == """
            Content view does not need a publish since there are no audited changes since the
            last publish. Pass check_needs_publish parameter as false if you don't want to check
            if content view needs a publish."""
            )

    def test_inc_update_composite_updated_expected_version(
        self,
        target_sat,
        module_org,
        fake_yum_repos,
    ):
        """Perform an Incremental Update, on a latest CV Version contained in a CompositeCV.
        Incr. Update the CV's Version to add an Erratum to the Composite's latest Version.
        Ensure only the intended Version was updated, and the Composite,
        which contains the expected Versions, and now the added erratum.

        :id: c8ab2dea-f51a-423e-ae1d-027fe6d85674

        :setup:
            1. Create and sync multiple custom yum repositories.
            2. Create 3 content views and add a single custom repo to each, auto_publish False.
            3. Publish v1.0 for a ContentView, with no filters applied (child_cvs[0]).
            4. Publish v1.0 for a ContentView, with an erratum Exclusion Filter applied (child_cvs[1]).
            5. Publish v1.0 of the Control ContentView, which we do not change after (child_cvs[2]).
            6. Create a Composite ContentView, add the 3 prior published Versions as components, use latest True.
            7. Publish v1.0 of the Composite ContentView.
            8. Add a second repo to the Unfiltered ContentView (child_cvs[0]), publish it v2.0.

        :steps:
            1. GET content_view_versions/incremental_update <content_view_version_environments> <add_content> <propagate_all_composites>
                - Invoke the Incremental Update on the child-CV[1] Version in Library, specifying erratum that was previously filtered out.
                - flag --propagate-all-composites set to True (incrementally updates the CompositeCV too)
            2. Successful incremental update, on the Filtered ContentView Version, v1.0->1.1, adding the filtered erratum (type: security).
            3. Composite components updated, expected Versions are present (see ExpectedResults).
            4. Publish the CompositeCV one final time (v2.0).

        Note: child_cvs[0] is Unfiltered, child_cvs[1] is Filtered, child_cvs[2] is a control.

        :expectedresults:
            1. Incrementally Updated Filtered ContentView to v1.1, Composite updated to v1.1. Added the security erratum.
            2. CompositeCV Version contains all the latest CV Versions, except the Unfiltered CVV v2.0 (only expect v1.0).
            3. After publishing again, CompositeCV Version now contains the Unfiltered CVV v2.0 (added other_repo content).
            4. The control CV only has its initial version 1.0.

        :Verifies: SAT-26559

        :customerscenario: true

        """
        ERRATUM_ID = settings.repos.yum_9.errata[0]  # RHSA-2012:0055
        child_cvs = []
        # custom repos created and synced in fixture `fake_yum_repos`
        other_repo = fake_yum_repos[3]
        for i in range(3):
            _cv = target_sat.api.ContentView(
                organization=module_org,
                auto_publish=False,
                repository=[fake_yum_repos[-i]],
            ).create()
            child_cvs.append(_cv)
        child_cvs = [_cv.read() for _cv in child_cvs]
        # Erratum exclusion filter for one of the child-CVs
        cv_filter = target_sat.api.ErratumContentViewFilter(
            content_view=child_cvs[1],
            inclusion=False,
        ).create()
        erratum = target_sat.api.Errata().search(query={'search': f'errata_id="{ERRATUM_ID}"'})[0]
        target_sat.api.ContentViewFilterRule(content_view_filter=cv_filter, errata=erratum).create()
        # publish 1.0 for each child CV
        child_cvs[0].read().publish()  # v1.0 unfiltered
        child_cvs[1].read().publish()  # v1.0 w/ erratum filter
        child_cvs[2].read().publish()  # v1.0 control
        child_cvs = [_cv.read() for _cv in child_cvs]
        child_versions = {_ver.read() for _cv in child_cvs for _ver in _cv.version}
        filtered_security = child_cvs[1].version[0].read().errata_counts['security']
        filtered_total = child_cvs[1].version[0].read().errata_counts['total']
        # create composite CV passing component from the other CV Versions
        composite_cv = target_sat.api.ContentView(
            organization=module_org,
            auto_publish=False,
            composite=True,
            component=child_versions,
        ).create()
        composite_cv = composite_cv.read()
        # make all composite components use latest version
        for _i in range(len(composite_cv.content_view_component)):
            component = composite_cv.content_view_component[_i].read()
            component.latest = True
            component.update(['latest'])
        child_cvs = [_cv.read() for _cv in child_cvs]
        composite_cv = composite_cv.read()
        # Publish v1.0 of Composite, with content and filter from the two prior CVs added
        composite_cv.publish()
        child_cvs = [_cv.read() for _cv in child_cvs]
        # Add new content to Unfiltered CV (other_repo)
        child_cvs[0].repository.append(other_repo.read())
        child_cvs[0].update(['repository'])
        child_cvs[0] = child_cvs[0].read()
        # Publish v2.0 of Unfiltered CV.
        child_cvs[0].publish()  # Unfiltered v2.0
        child_cvs = [_cv.read() for _cv in child_cvs]

        # Invoke the Incremental Update, on the latest Filtered child[1]-Version,
        # Specify the filtered erratum to add back, propagate all composites.
        result = target_sat.api.ContentViewVersion().incremental_update(
            data={
                'content_view_version_environments': [
                    {
                        'content_view_version_id': child_cvs[1].version[0].id,
                        'environment_ids': [module_org.library.id],
                    }
                ],
                'add_content': {'errata_ids': [ERRATUM_ID]},
                'propagate_all_composites': True,
            }
        )
        # Updated expected Version and added the filtered erratum
        assert f'{child_cvs[1].name} version 1.1' in result['humanized']['output']
        assert ERRATUM_ID in result['output']['changed_content'][0]['added_units']['erratum']
        child_cvs = [_cv.read() for _cv in child_cvs]
        child_versions = {_ver.read() for _cv in child_cvs for _ver in _cv.version}
        composite_cv = composite_cv.read()
        composite_v1_1 = composite_cv.version[0].read()
        assert ERRATUM_ID in composite_v1_1.description
        # Expect CompositeCV v1.0 -> v1.1 (option: propagate_all_composites)
        assert composite_cv.version[0].read().version == '1.1'
        # We published v2.0 of Unfiltered prior to Inc Update, unchanged
        assert child_cvs[0].version[0].read().version == '2.0'
        # Expect Incrementally Updated CV (filtered) is v1.1
        inc_ver = child_cvs[1].version[0].read()
        assert inc_ver.version == '1.1'
        assert inc_ver.errata_counts['security'] == 1 + filtered_security
        assert inc_ver.errata_counts['total'] == 1 + filtered_total
        # Control CV no changes (original version)
        assert len(child_cvs[2].version) == 1
        assert child_cvs[2].version[0].read().version == '1.0'

        # 'Update Available' for Composite (Unfiltered v2.0)
        assert composite_cv.read().needs_publish
        composite_cv.publish()  # Composite v2.0
        composite_cv = composite_cv.read()
        assert not composite_cv.needs_publish
        composite_v2_0 = composite_cv.version[0].read()
        assert composite_v2_0.version == '2.0'
        assert composite_v2_0.component_view_count == 3
        # Only difference between Composite v1.1 and v2.0,
        # is we added Unfiltered v2.0, which added the single other_repo:
        assert composite_v2_0.repository != composite_v1_1.repository
        # all Versions of all child CVs
        child_versions = {_ver.read() for _cv in child_cvs for _ver in _cv.version}
        # match Composite components to child CV Versions
        for comp in composite_cv.component:
            comp = comp.read()
            assert comp.id in [version.id for version in child_versions]
            # match CV-id from Component (each CV's latest Version)
            cv_id = comp.content_view.id
            if cv_id == child_cvs[0].id:
                # Unfiltered CV v2.0 is contained
                assert comp.version == '2.0'
            if cv_id == child_cvs[1].id:
                # Filtered CV, incrementally updated prior
                assert comp.version == '1.1'
            if cv_id == child_cvs[2].id:
                # Control CV, no changes
                assert comp.version == '1.0'


class TestContentViewUpdate:
    """Tests for updating content views."""

    @pytest.mark.parametrize(
        ('key', 'value'),
        **(lambda x: {'argvalues': list(x.items()), 'ids': list(x.keys())})(
            {'description': gen_utf8(), 'name': gen_utf8()}
        ),
    )
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


@pytest.mark.run_in_one_thread
class TestContentViewRedHatContent:
    """Tests for publishing and promoting content views."""

    @pytest.fixture(scope='class', autouse=True)
    def initiate_testclass(self, request, module_cv, module_sca_manifest_org, class_target_sat):
        """Set up organization, product and repositories for tests."""

        repo_id = class_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=module_sca_manifest_org.id,
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

    @pytest.mark.e2e
    def test_cv_audit_scenarios(self, module_product, target_sat):
        """Check for various scenarios where a content view's needs_publish flag
        should be set to true and that it properly gets set and unset

        :id: 48b0ce35-f76b-447e-a465-d9ce70cbb20e`

        :steps:

            1. Create a CV
            2. Add a filter to the CV
            3. Add a rule to the filter
            4. Delete that rule
            5. Delete that filter
            6. Add a repo to the CV
            7. Delete content from the repo
            8. Add content to the repo
            9. Sync the repo

        :expectedresults: All of the above steps should results in the CV needing to be
            be published

        :CaseImportance: High
        """
        # needs_publish is set to true when created
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # needs_publish is set to true when a filter is added/updated/deleted
        cv_filter = target_sat.api.RPMContentViewFilter(
            content_view=self.yumcv, inclusion='true', name=gen_string('alphanumeric')
        ).create()
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # Adding a rule should set needs_publish to true
        cvf_rule = target_sat.api.ContentViewFilterRule(
            content_view_filter=cv_filter, name=gen_string('alphanumeric'), version='1.0'
        ).create()
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # Deleting a rule should set needs_publish to true
        cvf_rule.delete()
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # Deleting a filter should set needs_publish to true
        cv_filter.delete()
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # needs_publish is set to true whenever repositories are interacted with on the CV
        # add a repo to the CV, needs_publish should be set to true
        repo_url = settings.repos.yum_0.url
        repo = target_sat.api.Repository(
            download_policy='immediate',
            mirroring_policy='mirror_complete',
            product=module_product,
            url=repo_url,
        ).create()
        repo.sync()
        self.yumcv.repository = [repo]
        self.yumcv = self.yumcv.update(['repository'])
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # needs_publish is set to true when repository content is removed
        packages = target_sat.api.Package(repository=repo).search(query={'per_page': '1000'})
        repo.remove_content(data={'ids': [package.id for package in packages]})
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # needs_publish is set to true whenever repo content is added
        with open(DataFile.RPM_TO_UPLOAD, 'rb') as handle:
            repo.upload_content(files={'content': handle})
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish
        # needs_publish is set to true whenever a repo is synced
        repo.sync()
        assert self.yumcv.read().needs_publish
        self.yumcv.publish()
        assert not self.yumcv.read().needs_publish


def test_repository_rpms_id_type(target_sat):
    """Katello_repository_rpms_id_seq needs to have the type bigint to allow
    repeated publishing of Content Views by customers.

    :id: a506782f-1edd-4568-99bb-d289212156ba

    :steps:
        1. Login to the Satellite cli and access the foreman posgres shell
        2. Search for katello_repository_rpms_id_seq

    :expectedresults: katello_repository_rpms_id_seq should have the type bigint, and not the type integer

    :CaseImportance: Medium
    """
    db_out = target_sat.execute(
        'sudo -u postgres psql -d foreman -c "select * from pg_sequences where sequencename=\'katello_repository_rpms_id_seq\';"'
    )
    assert 'bigint' in db_out.stdout
    assert 'integer' not in db_out.stdout


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


@pytest.mark.stubbed
class TestOstreeContentView:
    """Tests for ostree contents in content views."""

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
            url=settings.container.registry_hub,
        ).create()
        self.docker_repo.sync()

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


@pytest.mark.stubbed
class TestContentViewRedHatOstreeContent:
    """Tests for publishing and promoting cv with RH ostree contents."""

    @pytest.fixture(scope='class', autouse=True)
    def initiate_testclass(self, request, module_sca_manifest_org, class_target_sat):
        """Set up organization, product and repositories for tests."""

        repo_id = class_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=None,
            org_id=module_sca_manifest_org.id,
            product=PRDS['rhah'],
            repo=REPOS['rhaht']['name'],
            reposet=REPOSET['rhaht'],
            releasever=None,
        )
        request.cls.repo = class_target_sat.api.Repository(id=repo_id)
        self.repo.sync()

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
