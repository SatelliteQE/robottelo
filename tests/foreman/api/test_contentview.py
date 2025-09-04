"""Unit tests for the ``content_views`` paths.

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Artemis

:CaseImportance: High

"""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import random
import time

from fauxfactory import gen_integer, gen_string, gen_utf8
import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings, user_nailgun_config
from robottelo.constants import (
    CUSTOM_RPM_SHA_512_FEED_COUNT,
    DEFAULT_ARCHITECTURE,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_1_ERRATA_ID,
    FAKE_2_CUSTOM_PACKAGE,
    PERMISSIONS,
    PRDS,
    REPOS,
    REPOSET,
    TIMESTAMP_FMT_ZONE,
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


class TestRollingContentView:
    """Testing for rolling content views."""

    def test_negative_create_update_with_invalid_params(self, target_sat):
        """Cannot create or update rolling content view providing an invalid configuration.

        :id: b38b866e-786c-4be0-b4cb-64432dcbad45

        :steps:
            1) try to create a Composite rolling content view
            2) try to create a dependancy-solving rolling content view
            3) try to create an auto-publish (and Composite) rolling content view
            4) create a valid rolling content view
            5) try to update the valid rolling cv with the invalid params

        :expectedresults:
            1) Invalid Rolling Content View is not created
            2) Invalid Update for Rolling Content View is not executed

        :CaseImportance: High

        """
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(rolling=True, composite=True).create()
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(rolling=True, solve_dependencies=True).create()
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(rolling=True, composite=True, auto_publish=True).create()

        rolling_cv = target_sat.api.ContentView(rolling=True).create()
        rolling_cv.composite = True
        rolling_cv.update(['composite'])
        assert not rolling_cv.read().composite
        rolling_cv.auto_publish = True
        with pytest.raises(HTTPError):
            rolling_cv.update(['auto_publish'])
        rolling_cv.solve_dependencies = True
        with pytest.raises(HTTPError):
            rolling_cv.update(['solve_dependencies'])

    def test_negative_publish_rolling(self, target_sat):
        """Cannot publish the rolling content view.

        :id: a838316d-265d-4152-a472-8371b4480379

        :expectedresults: Rolling Content View is not published

        :CaseImportance: Critical

        """
        rolling_cv = target_sat.api.ContentView(rolling=True).create()
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(id=rolling_cv.id).publish()
        assert rolling_cv.version == target_sat.api.ContentView(id=rolling_cv.id).read().version

    def test_negative_convert_to_rolling(self, target_sat):
        """Cannot convert a normal content view into a rolling content view.

        :id: 78dba0fe-617d-4f52-96c9-dea66b1bfdf3

        :expectedresults: Original Content View is not converted to Rolling

        :CaseImportance: Critical

        """
        normal_cv = target_sat.api.ContentView().create()
        normal_cv = normal_cv.read()
        assert not normal_cv.rolling
        normal_cv.rolling = True
        normal_cv.update(['rolling'])
        assert not normal_cv.read().rolling

    def test_negative_promote_rolling_version(
        self, target_sat, default_org, module_org, module_lce
    ):
        """Cannot promote the version of the rolling content view to any environment.

        :id: b4987bb2-560a-4ead-9c98-48336504a7ba

        :expectedresults:
            1) Rolling Content View Version is not promoted.
            2) Rolling Content View is only in Library for its organization.

        :CaseImportance: Critical

        """
        # try in Default Org with its Library environment
        def_rolling_cv = target_sat.api.ContentView(rolling=True, organization=default_org).create()
        with pytest.raises(HTTPError):
            target_sat.api.ContentViewVersion(id=def_rolling_cv.version[0].id).promote(
                data={'environment_ids': def_rolling_cv.environment[0].id}
            )
        # try in non-default org with non-Library environment
        rolling_cv = target_sat.api.ContentView(rolling=True, organization=module_org).create()
        with pytest.raises(HTTPError):
            target_sat.api.ContentViewVersion(id=rolling_cv.version[0].id).promote(
                data={'environment_ids': module_lce.id}
            )
        # try by updating CV's environment
        def_rolling_cv.environment = [default_org.read().library.read()]
        with pytest.raises(HTTPError):
            def_rolling_cv.update(['environment'])
        rolling_cv.environment = [module_lce]
        with pytest.raises(HTTPError):
            rolling_cv.update(['environment'])
        # try by updating CV Version's env and CV's env
        rolling_version = rolling_cv.version[0].read()
        rolling_version.environment = [module_lce]
        rolling_cv.version = [rolling_version]
        rolling_cv.environment = [module_lce]
        with pytest.raises(HTTPError):
            rolling_cv.update(['environment', 'version'])
        # both rolling CVs only in their Library
        assert def_rolling_cv.read().environment == [def_rolling_cv.organization.read().library]
        assert rolling_cv.read().environment == [rolling_cv.organization.read().library]

    def test_negative_change_rolling_version(self, target_sat):
        """Cannot update the rolling content view with another version.

        :id: f16dbe19-29ea-41f1-89e2-fd99aa07857f

        :expectedresults: Rolling Content View is not updated

        :CaseImportance: Critical

        """
        rolling_cv = target_sat.api.ContentView(rolling=True).create()
        normal_cv = target_sat.api.ContentView().create()
        normal_cv.publish()
        normal_cv = normal_cv.read()
        rolling_version = rolling_cv.version[0].read()
        normal_version = normal_cv.version[0].read()
        # try with a single different version
        rolling_cv.version = [normal_version]
        with pytest.raises(HTTPError):
            rolling_cv.update(['version'])
        # try in addition to the rolling version
        rolling_cv.version = [rolling_version, normal_version]
        with pytest.raises(HTTPError):
            rolling_cv.update(['version'])
        # try with just the initial rolling version
        rolling_cv.version = [rolling_version]
        with pytest.raises(HTTPError):
            rolling_cv.update(['version'])
        # version remains unchanged
        assert rolling_cv.read().version[0].read() == rolling_version

    def test_negative_delete_rolling_version(self, target_sat):
        """Cannot delete the version of the rolling content view.

        :id: 6b1f3f0e-3f4e-4d1c-8f7a-2e5a5f3c8e2b

        :expectedresults: Rolling Content View Version is not deleted.

        :CaseImportance: Critical

        """
        rolling_cv = target_sat.api.ContentView(rolling=True).create()
        initial_version = rolling_cv.version[0].read()
        with pytest.raises(HTTPError):
            target_sat.api.ContentViewVersion(id=rolling_cv.version[0].id).delete()
        # try by updating rolling cv's version list
        rolling_cv.version = []
        with pytest.raises(HTTPError):
            rolling_cv.update(['version'])
        assert len(rolling_cv.read().version) == 1
        assert rolling_cv.read().version[0].read() == initial_version

    def test_negative_clone_rolling(self, target_sat):
        """Cannot create a copy of the rolling content view.

        :id: ef64fa8b-2cc9-4d14-b6a2-735996c659f0

        :expectedresults: Rolling Content View is not cloned

        :CaseImportance: High

        """
        rolling_cv = target_sat.api.ContentView(rolling=True).create()
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(
                id=rolling_cv.copy(data={'name': gen_string('alpha', gen_integer(3, 30))})['id']
            ).read_json()

    def test_negative_filter_rolling(self, target_sat, module_org, module_product):
        """Cannot add a content filter to the rolling content view.

        :id: 83f37cd8-e2ef-47e4-bad1-1c230aa7bc70

        :setup: Sync and add a custom repository containing 'walrus' package version(s).

        :expectedresults: Rolling Content View is not filtered.

        :CaseImportance: Critical

        """
        # Create and sync single custom repo containing 'walrus' versions
        repo = target_sat.api.Repository(
            content_type='yum', product=module_product, url=settings.repos.yum_9.url
        ).create()
        repo.sync()
        # Rolling CV created with the repo
        rolling_cv = target_sat.api.ContentView(
            repository=[repo.read()], organization=module_org, rolling=True
        ).create()
        # Try to filter the 'walrus' packages
        with pytest.raises(HTTPError):
            apply_package_filter(rolling_cv, repo, 'walrus', target_sat, inclusion=False)
        # no filter present, version unchanged
        assert not rolling_cv.read().version[0].read().filters_applied
        assert rolling_cv.read().version == rolling_cv.version

    def test_negative_duplicate_repos(self, target_sat, module_org, module_product):
        """Cannot add multiple copies of the exact same repository to rolling content view.

        :id: b3d70168-6b0d-4a8f-81f3-57ca991a8ab7

        :expectedresults: Cannot create or update rolling content view with duplicate repositories.

        :CaseImportance: Critical

        """
        repo = target_sat.api.Repository(
            content_type='yum', product=module_product, url=settings.repos.yum_9.url
        ).create()
        repo.sync()
        # cannot create CV with multiple copies of same repo
        with pytest.raises(HTTPError):
            target_sat.api.ContentView(
                repository=[repo.read(), repo.read()], organization=module_org, rolling=True
            ).create()
        # cannot update CV with a repo already contained
        rolling_cv = target_sat.api.ContentView(
            repository=[repo.read()], organization=module_org, rolling=True
        ).create()
        rolling_cv.repository.append(repo.read())
        with pytest.raises(HTTPError):
            rolling_cv.update(['repository'])

    @pytest.mark.upgrade
    def test_positive_CRUD_rolling(self, target_sat):
        """Create, read, update, and delete the rolling content view.
        It has the expected attributes for a rolling content view.

        :id: e0b296c6-5fb2-48dd-b324-709fb515dd88

        :steps:
            1) Create new empty rolling CV
            2) Check CVs attributes
            3) Update CVs description
            4) Try to delete the CV while it is still in Library
            5) Remove Rolling CV from Library, then Delete it

        :expectedresults:
            1) We can create, read, and update the rolling CV.
            2) We cannot Delete the rolling CV, until it's removed/deleted from environment(s).

        :CaseImportance: Critical

        """
        # created with expected attributes
        rolling_cv = target_sat.api.ContentView(rolling=True).create()
        assert all([rolling_cv.rolling, rolling_cv.read().rolling])
        read_cv = target_sat.api.ContentView(id=rolling_cv.id).read()
        update_cv = target_sat.api.ContentView(id=rolling_cv.id).update()
        assert not rolling_cv.needs_publish
        assert not rolling_cv.auto_publish
        assert len(rolling_cv.environment) == 1
        assert rolling_cv.environment[0].id == rolling_cv.organization.read().library.id
        assert read_cv == rolling_cv == update_cv
        # mutate and update
        rolling_cv.description = valid_data_list()['utf8']
        update_cv = rolling_cv.update(['description'])
        assert update_cv == (rolling_cv := rolling_cv.read())
        cv_desc = target_sat.api.ContentView(id=rolling_cv.id).read().description
        assert rolling_cv.description == cv_desc
        # remove from environment prior to deleting
        with pytest.raises(HTTPError):
            rolling_cv.delete()
        rolling_cv.delete_from_environment(rolling_cv.environment[0].id)
        rolling_cv.delete()
        with pytest.raises(HTTPError):
            rolling_cv.read()

    @pytest.mark.upgrade
    def test_positive_content_types_in_rolling(self, target_sat, module_org, module_product):
        """Can upload and use the different content types with the rolling content view.
        Packages, Package Groups, Module Streams, Errata.

        :id: c9fb36e2-5241-44c2-8f7b-1069ccec5617

        :CaseImportance: Critical

        """
        rolling_cv = target_sat.api.ContentView(organization=module_org, rolling=True).create()
        initial_version = rolling_cv.version[0].read()
        custom_repos = [
            settings.repos.yum_0.url,
            settings.repos.yum_3.url,
            settings.repos.yum_6.url,
            settings.repos.yum_9.url,
        ]
        for _url in custom_repos:
            (repo := target_sat.api.Repository(product=module_product, url=_url).create()).sync()
            rolling_cv.repository.append(repo.read())
        # update rolling cv with the custom repos
        rolling_cv.update(['repository'])
        rolling_cv = rolling_cv.read()
        assert len(rolling_cv.repository) == len(custom_repos)
        assert initial_version != (rolling_version := rolling_cv.version[0].read())
        assert rolling_version.yum_repository_count == len(custom_repos)
        # errata now present from added repos
        assert rolling_version.errata_counts['total'] == 37
        assert rolling_version.errata_counts['bugfix'] == 8
        assert rolling_version.errata_counts['security'] == 16
        assert rolling_version.errata_counts['enhancement'] == 13
        # packages, module streams, and package groups present
        # TODO: fails: expect the version shows updated counts
        """assert rolling_version.package_count > 0
        assert rolling_version.package_group_count > 0
        assert rolling_version.module_stream_count > 0"""

    @pytest.mark.upgrade
    def test_positive_rolling_with_activation_keys(self, module_org, module_ak, target_sat):
        """We can use the rolling content view with one or more associated activation keys.

        :id: b0510759-cee9-4f2e-a34c-dd495a34778c

        :expectedresults:
            1) We can use and delete activation keys associated to a rolling content view.
            2) We cannot delete the rolling content view, until it is unassociated from activation key(s),
               and removed from environment(s).

        :CaseImportance: Critical

        """
        rolling_cv = target_sat.api.ContentView(organization=module_org, rolling=True).create()
        library = rolling_cv.environment[0].read()
        # Create new activation key providing rolling CV
        ak = target_sat.api.ActivationKey(
            organization=module_org,
            content_view=rolling_cv,
            environment=library,
        ).create()
        assert ak.content_view.read() == rolling_cv
        assert ak.environment.read() == library
        # Update an existing activation key with CVE
        module_ak.content_view = rolling_cv
        module_ak.environment = library
        module_ak.update(['content_view', 'environment'])
        module_ak = module_ak.read()
        assert module_ak.content_view.read() == rolling_cv
        assert module_ak.environment.read() == library
        # Can't delete until unassociated from AK's, removed from Library
        with pytest.raises(HTTPError):
            rolling_cv.delete_from_environment(library.id)
        with pytest.raises(HTTPError):
            rolling_cv.delete()
        ak.delete()
        module_ak.content_view = module_ak.environment = None
        module_ak.update(['content_view', 'environment'])
        rolling_cv.delete_from_environment(library.id)
        rolling_cv.delete()
        with pytest.raises(HTTPError):
            rolling_cv.read()

    @pytest.mark.upgrade
    def test_positive_rolling_version(self, target_sat, module_org, module_product):
        """The rolling content view always has a single version, which is updated automatically.

        :id: 3f0b3645-2eca-4cdc-89bc-0b5222bc1350

        :steps:
            1) Create new empty rolling CV
            2) Inspect its first empty version
            3) Add a repository with small amount of content to rolling CV
            4) Update the CV, inspect the latest version again

        :expectedresults:
            1) After creating and updating the rolling CV, only a single version is present.
            2) The single rolling version is always up to date, always published, and in Library.
            3) When new repository content is added to rolling CV, the rolling version is updated with the content.

        :CaseImportance: Critical

        """
        rolling_cv = target_sat.api.ContentView(
            organization=module_org,
            rolling=True,
        ).create()
        assert rolling_cv.read().rolling
        assert len(rolling_cv.version) == 1
        rolling_version = deepcopy(
            target_sat.api.ContentViewVersion(id=rolling_cv.version[0].id).read()
        )
        initial_version_publish = deepcopy(rolling_cv.last_published)
        assert rolling_version.content_view.read() == rolling_cv
        assert rolling_cv.version[0].read() == rolling_version
        assert rolling_cv.environment == rolling_version.environment
        assert rolling_version.version == '1.0'
        assert rolling_version.major == 1
        assert rolling_version.minor == 0
        # check for empty content in version's attributes
        version_content_empty = [
            'docker_repository_count',
            'file_count',
            'file_repository_count',
            'module_stream_count',
            'package_count',
            'package_group_count',
            'yum_repository_count',
        ]
        for key in version_content_empty:
            assert getattr(rolling_version, key) == 0
        for key in rolling_version.errata_counts:
            assert rolling_version.errata_counts[f'{key}'] == 0
        # create, sync, and add a custom repo with some fake content
        repo = target_sat.api.Repository(
            product=module_product, url=settings.repos.yum_0.url
        ).create()
        repo.sync()
        rolling_cv.repository = [repo.read()]
        rolling_cv.update(['repository'])
        rolling_cv = rolling_cv.read()
        # last_published times do not change after rolling cv updates
        assert datetime.strptime(
            rolling_cv.last_published, TIMESTAMP_FMT_ZONE
        ) == datetime.strptime(initial_version_publish, TIMESTAMP_FMT_ZONE)
        # check newly updated version
        new_rolling_version = target_sat.api.ContentViewVersion(id=rolling_cv.version[0].id).read()
        assert new_rolling_version != rolling_version
        assert new_rolling_version.content_view.read() == rolling_cv
        assert rolling_cv.version[0].read() == new_rolling_version
        assert rolling_cv.environment == new_rolling_version.environment
        assert new_rolling_version.version == '1.0'
        assert new_rolling_version.major == 1
        assert new_rolling_version.minor == 0
        # check the new content (errata) is now present in version
        assert new_rolling_version.yum_repository_count == 1
        # TODO: fails, package counts not updated in rolling CVV
        """assert new_rolling_version.package_count > 0
        assert new_rolling_version.package_group_count > 0"""
        assert all(
            [
                new_rolling_version.errata_counts['security'],
                new_rolling_version.errata_counts['total'],
            ]
        )
        # version's :id and some other attrs remain the same
        assert new_rolling_version.id == rolling_version.id
        assert new_rolling_version.name == rolling_version.name
        assert new_rolling_version.version == rolling_version.version
        assert new_rolling_version.description == rolling_version.description
        assert new_rolling_version.environment == rolling_version.environment
        assert new_rolling_version.content_view == rolling_version.content_view

    @pytest.mark.upgrade
    def test_positive_sync_repo_updates_rolling_content(
        self, target_sat, module_org, module_product
    ):
        """When a repository associated to the rolling content view is synced with updated content,
        the content contained within the rolling cv and version is updated as expected.

        :id: 1a5f3b1c-2dcb-4e7b-8f3a-5c3e4f6d7e8f

        :steps:
            1) create a rolling cv with one un-synced custom repository
            2) check the initial empty version for rolling cv
            3) sync the repository, new content is present
            4) check the updated version and content for rolling cv

        :expectedresults:
            1) The initial version of the rolling cv is empty.
            2) After syncing the repository, the version of the rolling cv is updated with the new content.

        :CaseImportance: Critical

        """
        # create one repo, but do not sync it
        repo = target_sat.api.Repository(
            product=module_product, url=settings.repos.yum_6.url
        ).create()
        # create rolling cv with the empty repo
        rolling_cv = target_sat.api.ContentView(
            organization=module_org, repository=[repo.read()], rolling=True
        ).create()
        rolling_cv = rolling_cv.read()
        # initial version is empty
        rolling_version = rolling_cv.version[0].read()
        assert rolling_version.content_view.read() == rolling_cv
        assert rolling_version.yum_repository_count == 1
        assert rolling_version.version == '1.0'
        assert rolling_version.package_count == 0
        assert all(count == 0 for count in rolling_version.errata_counts.values())
        # sync the repo
        repo.sync()
        repo = repo.read()
        # list of single version remains unchanged
        assert rolling_cv.read().version == rolling_cv.version
        rolling_cv = rolling_cv.read()
        new_rolling_version = rolling_cv.version[0].read()
        # version updated is different but id and number is the same
        assert new_rolling_version != rolling_version
        assert new_rolling_version.id == rolling_version.id
        assert new_rolling_version.name == rolling_version.name
        assert new_rolling_version.content_view.read() == rolling_cv
        assert new_rolling_version.yum_repository_count == 1
        assert new_rolling_version.version == '1.0'
        # packages and errata now present, match repo's content
        # TODO: fails, expect matching counts
        """assert (
            new_rolling_version.package_count == repo.content_counts['rpm']
        )
        assert new_rolling_version.package_group_count == repo.content_counts['package_group']
        assert (
            new_rolling_version.module_stream_count == repo.content_counts['module_stream']
        )"""
        assert new_rolling_version.errata_counts['total'] == repo.content_counts['erratum']

    @pytest.mark.e2e
    @pytest.mark.upgrade
    def test_positive_add_remove_repos_from_rolling(
        self, module_target_sat, module_sca_manifest_org, module_product
    ):
        """Can add and remove one or multiple repositories from the rolling content view.
        We can remove the rolling cv from Library and delete it, with repos still added.
        For RedHat and Custom repositories added.

        :id: 623798f0-0974-4119-986e-a6b756e9d9d0

        :setup:
            1) Create one custom repository, create a rolling cv with it
            2) add the other custom repos to rolling cv, update

        :steps:
            1) add multiple Red Hat repositories to the rolling cv
            2) remove a single custom repository from the rolling cv
            3) remove a single RedHat repository from the rolling cv
            4) delete the rolling CV with custom and RH repos still added

        :expectedresults:
            1) We can create a rolling cv providing a repository.
            2) We can add and remove Custom and RedHat repositories.
            3) Version of the rolling CV is updated when a synced repository is added or removed.
            4) (SAT-37282) We can delete the rolling cv with some repos still added to it.

        :CaseImportance: High

        :Verifies: SAT-37282

        """
        custom_repo_urls = [
            settings.repos.yum_3.url,
            settings.repos.yum_6.url,
            settings.repos.yum_9.url,
        ]
        rolling_cv = None
        initial_version = None
        org = module_sca_manifest_org
        # Create rolling cv and add the Custom Repos
        for _url in custom_repo_urls:
            repo = module_target_sat.api.Repository(product=module_product, url=_url).create()
            repo.sync()
            if not rolling_cv:
                # Create rolling_cv if not yet, with first repo initially
                rolling_cv = module_target_sat.api.ContentView(
                    organization=org, repository=[repo.read()], rolling=True
                ).create()
                initial_version = rolling_cv.read().version[0].read()
            else:
                # rolling cv already created, append custom repo and update
                rolling_cv.repository.append(repo.read())
                rolling_cv.update(['repository'])
                rolling_cv = rolling_cv.read()

        rhel_major = settings.content_host.default_rhel_version
        # add RedHat Repositories - RHEL BaseOS, AppStream
        for repo_tail in ['bos', 'aps']:
            _repo = f'rhel{rhel_major}_{repo_tail}'  # 'rhel9_bos', 'rhel9_aps', etc
            # sync and add to rolling cv
            rh_repo_id = module_target_sat.api_factory.enable_sync_redhat_repo(
                rh_repo=REPOS[f'{_repo}'],
                org_id=org.id,
                timeout=2400,
            )
            rh_repo = module_target_sat.api.Repository(id=rh_repo_id, organization=org).read()
            rolling_cv.repository.append(rh_repo.read())
            rolling_cv.update(['repository'])
            rolling_cv = rolling_cv.read()

        num_repos = len(rolling_cv.repository)
        rolling_repos = deepcopy(rolling_cv.repository)
        current_version = rolling_cv.version[0].read()
        assert initial_version != current_version
        # remove a RedHat repository (tail)
        _remove_this = rolling_cv.repository[-1]
        rolling_cv.repository.remove(_remove_this)
        rolling_cv.update(['repository'])
        rolling_cv = rolling_cv.read()
        assert _remove_this not in rolling_cv.repository
        newest_version = rolling_cv.version[0].read()
        assert current_version != newest_version
        current_version = newest_version
        # remove a custom repo (head)
        _remove_this = rolling_cv.repository[0]
        rolling_cv.repository.remove(_remove_this)
        rolling_cv.update(['repository'])
        rolling_cv = rolling_cv.read()
        assert _remove_this not in rolling_cv.repository
        newest_version = rolling_cv.version[0].read()
        assert current_version != newest_version
        assert len(rolling_cv.repository) == num_repos - 2
        # remove from Library, delete cv with some repos left
        with pytest.raises(HTTPError):
            rolling_cv.delete()
        rolling_cv.delete_from_environment(rolling_cv.environment[0].id)
        rolling_cv.delete()
        # can't read the deleted cv
        with pytest.raises(HTTPError):
            rolling_cv.read()
        # can still access repos
        for repo in rolling_repos:
            repo = repo.read()
            repo.sync(timeout=2400)

    @pytest.mark.stubbed
    def test_positive_add_remove_repo_collection_from_rolling(self):
        """Can add and remove a repository collection from the rolling content view.
        The content contained within the rolling cv is updated as expected.

        :id: 768b8b8a-f75b-405c-b11a-cead9a021079

        :CaseImportance: High

        """
        # TODO

    def test_positive_multi_contentview(self, target_sat, module_org, module_product):
        """Can use the rolling content view with multiple published content views present.

        :id: 5af10680-1c0c-47b7-98d3-dd9064be930f

        :steps:
            1) Create several Normal, Published content views with custom repositories.
            2) Create several Rolling content views with different custom repositories.
            3) Add a Rolling content view's repository to each Normal content view, publish them.
            4) Add a Normal content view's repository to each Rolling content view.

        :expectedresults:
            1) Adding a Rolling CV's repository to a Normal CV did not change the Rolling CV or its Version.
            2) Publishing the Normal CVs did not change the Rolling CV or its Version.
            3) Adding a Normal CV's repository to a Rolling CV did not modify the Normal CVs,
                but it updated the Rolling CV and its Version.

        :caseimportance: High

        """
        # TODO add assertions for content counts in-between key steps
        normal_cv_urls = [
            settings.repos.yum_0.url,
            settings.repos.yum_1.url,
            settings.repos.yum_2.url,
        ]
        rolling_cv_urls = [
            settings.repos.yum_3.url,
            settings.repos.yum_6.url,
            settings.repos.yum_9.url,
        ]
        normal_repos = []
        rolling_repos = []
        normal_versions = []
        rolling_versions = []
        for _url in normal_cv_urls:
            # create one repo, sync, create a normal cv with it, publish cv
            repo = target_sat.api.Repository(product=module_product, url=_url).create()
            repo.sync(timeout=360)
            normal_cv = target_sat.api.ContentView(
                organization=module_org, repository=[repo.read()]
            ).create()
            normal_cv.publish()
            normal_repos.append(repo.read())
            normal_versions.append(normal_cv.read().version[0].read())
        for _url in rolling_cv_urls:
            # create one repo, sync, create a rolling cv with it
            repo = target_sat.api.Repository(product=module_product, url=_url).create()
            repo.sync(timeout=360)
            rolling_cv = target_sat.api.ContentView(
                organization=module_org, repository=[repo.read()], rolling=True
            ).create()
            rolling_repos.append(repo.read())
            rolling_versions.append(rolling_cv.read().version[0].read())

        normal_cvs = [ver.content_view.read() for ver in normal_versions]
        rolling_cvs = [ver.content_view.read() for ver in rolling_versions]
        assert all(not cv.read().needs_publish for cv in normal_cvs + rolling_cvs)
        # TODO after first publish, check normal cvs pkgs, ms, errata counts etc.
        # and adding repos, check rolling cvs pkgs, ms, errata counts etc.
        # add a rolling repo to normal cvs and update
        for cv in normal_cvs:
            cv.repository.append(rolling_repos[0])
            cv.update(['repository'])
        # TODO normal cvs content same, until publish
        # rolling cvs content no change
        # normal cvs need publish, rolling cvs do not
        assert all(cv.read().needs_publish for cv in normal_cvs)
        assert all(not cv.read().needs_publish for cv in rolling_cvs)
        # Publish normal cvs, check rolling was unchanged
        [cv.read().publish() for cv in normal_cvs]
        # no cvs need publish
        # TODO normal cvs content new after version published
        # rolling cvs content no change
        assert all(not cv.read().needs_publish for cv in normal_cvs + rolling_cvs)
        # rolling cvs and their version unchanged
        assert all(
            len(cv.read().version) == 1  # single version present
            and cv.read() == cv in rolling_cvs  # same rolling cv
            and cv.read().version[0].read() == ver  # same rolling version
            for cv, ver in zip(rolling_cvs, rolling_versions, strict=False)
        )
        normal_cvs = [ver.content_view.read() for ver in normal_versions]
        rolling_cvs = [ver.content_view.read() for ver in rolling_versions]
        # add a normal cv repo to rolling cvs and update
        for cv in rolling_cvs:
            cv.repository.append(normal_repos[0])
            cv.update(['repository'])
        # TODO rolling cvs content counts changed
        # normal cvs content unchanged
        # no cvs need publish
        assert all(not cv.read().needs_publish for cv in normal_cvs + rolling_cvs)
        # rolling cv and version changed
        assert all(
            len(cv.read().version) == 1  # still only a single version
            and cv.read() != cv in rolling_cvs  # updated rolling cv
            and cv.read().version[0].read() != ver  # updated rolling version
            for cv, ver in zip(rolling_cvs, rolling_versions, strict=False)
        )

    def test_negative_rolling_in_a_composite(self, target_sat):
        """Cannot add the rolling content view to a composite content view.

        :id: cb49166f-7ecc-4c0d-b532-b98fb91c2853

        :expectedresults: The rolling content view is not added
            as a component of the composite content view.

        :CaseImportance: High

        """
        rolling_cv = target_sat.api.ContentView(rolling=True).create()
        # raises TypeError, not HTTP 400?
        with pytest.raises(TypeError):
            # try creating composite cv with rolling cv added at creation
            composite_cv = target_sat.api.ContentView(
                component=[rolling_cv.read()], composite=True
            ).create()
        with pytest.raises(HTTPError):
            # try creating composite cv with rolling cv's Version added at creation
            composite_cv = target_sat.api.ContentView(
                component=[rolling_cv.version[0].read()], composite=True
            ).create()
        # try updating new empty composite components with the rolling cv
        composite_cv = target_sat.api.ContentView(composite=True).create()
        composite_cv.component = [rolling_cv.read()]
        with pytest.raises(HTTPError):
            composite_cv.update(['component'])
        assert not composite_cv.read().component
        # try updating empty composite components with the rolling cv's Version.
        composite_cv = composite_cv.read()
        composite_cv.component = [rolling_cv.version[0].read()]
        with pytest.raises(HTTPError):
            composite_cv.update(['component'])
        assert not composite_cv.read().component

    @pytest.mark.e2e
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('N-2')
    def test_positive_host_with_rolling_content_source(
        self,
        target_sat,
        module_rhel_contenthost,
        function_sca_manifest_org,
        function_product,
        request,
    ):
        """Can use the rolling content view as a content source for a registered host.
        We can use the custom and RedHat repositories available to the content host.
        We can install some outdated package, apply an erratum, and find the updated package on host.

        :id: 6926cd41-92ba-455d-8eba-fc0c08f940c9

        :setup:
            1) Several custom and RedHat repositories added to new rolling cv.
            2) Assign the rolling cv to an activation key.
            3) Override the repos to Enabled for activation key (Hammer).
            4) Add finalizer, cleanup: unregister the host.
            5) Register a RHEL host to the activation key.
            6) SCA enabled, host auto-enabled repos that were overridden for AK.

        :steps:
            1) Remove a repository from the rolling cv. (expectedresults: 3)
            2) Add a new repository to the rolling cv. (expectedresults: 3)
            3) Install some outdated packages to the host, apply the package's erratum. (expectedresults: 4)
            4) Try to delete the rolling cv. (expectedresults: 5)
            5) Unregister the host, delete the activation key, remove CV from Library env.
            6) Try to delete the rolling cv once more. (expectedresults: 6)

        :expectedresults:
            1) The rolling content view is set as the content source for the host.
            2) Repositories and content from rolling CV are available to host.
            3) Changing the rolling CV's content will update the host's content accordingly.
            4) We can install the rolling CV's packages and errata to host.
            5) We cannot delete the rolling cv without deleting the activation key.

        :CaseImportance: High

        :customerscenario: true

        """
        org = function_sca_manifest_org
        client = module_rhel_contenthost
        custom_repo = target_sat.api.Repository(
            product=function_product, url=settings.repos.yum_9.url
        ).create()
        custom_repo.sync()
        # RH BaseOS repo for client's RHEL major version
        rhel_major = client.os_version.major  # int 8, 9, etc
        rh_repo_id = target_sat.api_factory.enable_sync_redhat_repo(
            rh_repo=REPOS[f'rhel{rhel_major}_bos'],
            org_id=org.id,
            timeout=2400,
        )
        rh_repo = target_sat.api.Repository(id=rh_repo_id, organization=org).read()
        # Create empty rolling cv, add both repos, update it
        rolling_cv = target_sat.api.ContentView(organization=org, rolling=True).create()
        rolling_cv.repository = [custom_repo.read(), rh_repo.read()]
        rolling_cv.update(['repository'])
        rolling_cv = rolling_cv.read()
        # create the AK with the rolling cv
        ak = target_sat.api.ActivationKey(
            organization=org,
            content_view=rolling_cv,
            environment=rolling_cv.environment[0].read(),  # Library
        ).create()
        # Hammer CLI: override the repos to enabled for AK
        override = target_sat.cli_factory.override_repos_for_activation_key(
            repos=rolling_cv.repository,  # rolling cv repo list, with both added
            ak_id=ak.id,
            value=True,
        )
        assert override['result'] == 'success'

        # Cleanup for in-between parametrized sessions,
        # unregister the host if it still exists
        @request.addfinalizer
        def cleanup():
            nonlocal client
            if client:
                client.unregister()

        result = client.register(
            target=target_sat,
            activation_keys=ak.name,
            loc=None,
            org=org,
        )
        assert result.status == 0, f'Failed to register host: {result.stdout}'
        assert custom_repo.name in result.stdout
        prior_errata = client.applicable_errata_count
        prior_pkgs = client.applicable_package_count
        time.sleep(120)  # rh repo not reported immediately

        # client reports custom repo
        sub_man_repos = client.subscription_manager_list_repos().stdout
        assert custom_repo.name in sub_man_repos
        custom_repo_content_label = target_sat.cli.Repository.info({'id': custom_repo.id})[
            'content-label'
        ]
        assert custom_repo_content_label in sub_man_repos
        # client reports RedHat repo
        _rh_repo_tail = f' - BaseOS RPMs {rhel_major}'
        assert rh_repo.name.replace(_rh_repo_tail, "") in sub_man_repos
        rh_repo_content_label = target_sat.cli.Repository.info({'id': rh_repo.id})['content-label']
        assert rh_repo_content_label in sub_man_repos
        time.sleep(30)
        # rh repo's package (python) is installed and up to date
        assert 'x86_64' in client.execute('rpm -q python3').stdout
        result = client.execute('yum install -y python3')
        assert 'is already installed' in result.stdout
        # custom repo's outdated package can be installed
        assert client.execute(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}').status == 0
        # outdated package makes errata installable, count increased
        assert client.applicable_errata_count > prior_errata
        assert client.applicable_package_count > prior_pkgs
        # install just one of the erratum
        task_id = target_sat.api.JobInvocation().run(
            data={
                'feature': 'katello_errata_install',
                'inputs': {'errata': str(FAKE_1_ERRATA_ID)},
                'search_query': f'name = {client.hostname}',
                'targeting_type': 'static_query',
                'organization_id': org.id,
            },
        )['id']
        target_sat.wait_for_tasks(
            search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
            search_rate=20,
            max_tries=15,
        )
        time.sleep(60)  # errata applicability update not immediate
        client.execute('subscription-manager repos')
        # applying erratum made applicability same as prior, count decreased
        assert client.applicable_errata_count == prior_errata
        assert client.applicable_package_count == prior_pkgs
        # client's package updated by erratum install
        assert (
            FAKE_2_CUSTOM_PACKAGE in client.execute(f'rpm -q {FAKE_1_CUSTOM_PACKAGE_NAME}').stdout
        )
        rolling_cv = rolling_cv.read()
        # try to delete rolling cv, delete ak and remove cv from Library first
        with pytest.raises(HTTPError):
            rolling_cv.delete()
        ak.delete()
        rolling_cv.delete_from_environment(rolling_cv.environment[0].id)
        rolling_cv.delete()
        with pytest.raises(HTTPError):
            rolling_cv.read()

    @pytest.mark.stubbed
    @pytest.mark.e2e
    def test_positive_host_collection_with_rolling_content_source(self, target_sat):
        """We can use the rolling content view as a content source for a host collection.

        :id: 2394dcad-578a-4565-9aaa-344ba62807c9

        :CaseImportance: High

        :customerscenario: true

        """
        # TODO

    @pytest.mark.stubbed
    @pytest.mark.e2e
    def test_positive_capsule_with_rolling_content_source(self, module_capsule_configured):
        """We can use the rolling content view as a content source for a capsule.

        :id: b3d3d90a-cfb0-45a3-9e4a-d928190180be

        :CaseImportance: High

        :customerscenario: true

        """
        # TODO


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
