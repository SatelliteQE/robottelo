"""Unit tests for the ``content_view_filters`` paths.

A full API reference for content views can be found here:
http://www.katello.org/docs/api/apidoc/content_view_filters.html


:Requirement: Contentviewfilter

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import http
from random import randint

import pytest
from fauxfactory import gen_integer
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo import ssh
from robottelo.api.utils import promote
from robottelo.config import get_credentials
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CUSTOM_REPODATA_PATH
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list


@pytest.fixture(scope='module')
def sync_repo(module_product):
    repo = entities.Repository(product=module_product).create()
    repo.sync()
    return repo


@pytest.fixture(scope='module')
def sync_repo_module_stream(module_product):
    repo = entities.Repository(
        content_type='yum', product=module_product, url=settings.repos.module_stream_1.url
    ).create()
    repo.sync()
    return repo


@pytest.fixture
def content_view(module_org, sync_repo):
    return entities.ContentView(organization=module_org, repository=[sync_repo]).create()


@pytest.fixture
def content_view_module_stream(module_org, sync_repo_module_stream):
    return entities.ContentView(
        organization=module_org, repository=[sync_repo_module_stream]
    ).create()


class TestContentViewFilter:
    """Tests for content view filters."""

    @pytest.mark.tier2
    def test_negative_get_with_no_args(self):
        """Issue an HTTP GET to the base content view filters path.

        :id: da29fd90-cd96-49f9-b94e-71d4e3a35a57

        :expectedresults: An HTTP 200 response is received if a GET request is
            issued with no arguments specified.

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=get_credentials(),
            verify=False,
        )
        assert response.status_code == http.client.OK

    @pytest.mark.tier2
    def test_negative_get_with_bad_args(self):
        """Issue an HTTP GET to the base content view filters path.

        :id: e6fea726-930b-4b74-b784-41528811994f

        :expectedresults: An HTTP 200 response is received if a GET request is
            issued with bad arguments specified.

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        response = client.get(
            entities.AbstractContentViewFilter().path(),
            auth=get_credentials(),
            verify=False,
            data={'foo': 'bar'},
        )
        assert response.status_code == http.client.OK

    @pytest.mark.tier2
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_erratum_with_name(self, name, content_view):
        """Create new erratum content filter using different inputs as a name

        :id: f78a133f-441f-4fcc-b292-b9eed228d755

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct name and type

        :CaseLevel: Integration
        """
        cvf = entities.ErratumContentViewFilter(content_view=content_view, name=name).create()
        assert cvf.name == name
        assert cvf.type == 'erratum'

    @pytest.mark.tier2
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_pkg_group_with_name(self, name, content_view):
        """Create new package group content filter using different inputs as a name

        :id: f9bfb6bf-a879-4f1a-970d-8f4df533cd59

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct name and type

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        cvf = entities.PackageGroupContentViewFilter(
            content_view=content_view,
            name=name,
        ).create()
        assert cvf.name == name
        assert cvf.type == 'package_group'

    @pytest.mark.tier2
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_rpm_with_name(self, name, content_view):
        """Create new RPM content filter using different inputs as a name

        :id: f1c88e72-7993-47ac-8fbc-c749d32bc768

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct name and type

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view, name=name).create()
        assert cvf.name == name
        assert cvf.type == 'rpm'

    @pytest.mark.tier2
    @pytest.mark.parametrize('inclusion', [True, False])
    def test_positive_create_with_inclusion(self, inclusion, content_view):
        """Create new content view filter with different inclusion values

        :id: 81130dc9-ae33-48bc-96a7-d54d3e99448e

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct inclusion value

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view, inclusion=inclusion).create()
        assert cvf.inclusion == inclusion

    @pytest.mark.tier2
    @pytest.mark.parametrize('description', **parametrized(valid_data_list()))
    def test_positive_create_with_description(self, description, content_view):
        """Create new content filter using different inputs as a description

        :id: e057083f-e69d-46e7-b336-45faaf67fa52

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            correct description

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            description=description,
        ).create()
        assert cvf.description == description

    @pytest.mark.tier2
    def test_positive_create_with_repo(self, content_view, sync_repo):
        """Create new content filter with repository assigned

        :id: 7207d4cf-3ccf-4d63-a50a-1373b16062e2

        :expectedresults: Content view filter created successfully and has
            repository assigned

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo],
        ).create()
        assert cvf.repository[0].id == sync_repo.id

    @pytest.mark.tier2
    @pytest.mark.parametrize('original_packages', [True, False])
    def test_positive_create_with_original_packages(
        self, original_packages, content_view, sync_repo
    ):
        """Create new content view filter with different 'original packages'
        option values

        :id: 789abd8a-9e9f-4c7c-b1ac-6b69f23f77dd

        :parametrized: yes

        :expectedresults: Content view filter created successfully and has
            'original packages' value

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo],
            original_packages=original_packages,
        ).create()
        assert cvf.original_packages == original_packages

    @pytest.mark.tier2
    def test_positive_create_with_docker_repos(self, module_product, sync_repo, content_view):
        """Create new docker repository and add to content view that has yum
        repo already assigned to it. Create new content view filter and assign
        it to the content view.

        :id: 2cd28bf3-cd8a-4943-8e63-806d3676ada1

        :expectedresults: Content view filter created successfully and has both
            repositories assigned (yum and docker)

        :CaseLevel: Integration
        """
        docker_repository = entities.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=module_product.id,
            url=CONTAINER_REGISTRY_HUB,
        ).create()
        content_view.repository = [sync_repo, docker_repository]
        content_view.update(['repository'])

        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo, docker_repository],
        ).create()
        assert len(cvf.repository) == 2
        for repo in cvf.repository:
            assert repo.id in (sync_repo.id, docker_repository.id)

    @pytest.mark.tier2
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_positive_create_with_module_streams(
        self, module_product, sync_repo, sync_repo_module_stream, content_view
    ):
        """Verify Include and Exclude Filters creation for modulemd (module streams)

        :id: 4734dcca-ea5b-47d6-8f5f-239da0dc7629

        :expectedresults: Content view filter created successfully for both
            Include and Exclude Type

        :CaseLevel: Integration
        """
        content_view.repository += [sync_repo_module_stream]
        content_view.update(['repository'])
        for inclusion in (True, False):
            cvf = entities.ModuleStreamContentViewFilter(
                content_view=content_view,
                inclusion=inclusion,
                repository=[sync_repo, sync_repo_module_stream],
            ).create()
            assert cvf.inclusion == inclusion
            assert len(cvf.repository) == 2
        assert content_view.id == cvf.content_view.id
        assert cvf.type == 'modulemd'

    @pytest.mark.tier2
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_positive_publish_with_content_view_filter_and_swid_tags(
        self, module_org, module_product
    ):
        """Verify SWID tags content file should exist in publish content view
        version location even after applying content view filters.

        :id: 00ac640f-1dfc-4083-8405-5164650d71b5

        :steps:
            1. create product and repository with custom contents having swid tags
            2. sync the repository
            3. create the content view
            4. create content view filter
            5. apply content view filter to repository
            6. publish the content-view
            7. ssh into Satellite
            8. verify SWID tags content file exist in publish content view version location

        :expectedresults: SWID tags content file should exist in publish content view
            version location

        :CaseAutomation: Automated

        :CaseImportance: Critical

        :CaseLevel: Integration
        """
        swid_tag_repository = entities.Repository(
            product=module_product, url=settings.repos.swid_tag.url
        ).create()
        swid_tag_repository.sync()
        content_view = entities.ContentView(organization=module_org).create()
        content_view.repository = [swid_tag_repository]
        content_view.update(['repository'])

        cv_filter = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[swid_tag_repository],
        ).create()
        assert len(cv_filter.repository) == 1
        cv_filter_rule = entities.ContentViewFilterRule(
            content_view_filter=cv_filter, name='walrus', version='1.0'
        ).create()
        assert cv_filter.id == cv_filter_rule.content_view_filter.id
        content_view.publish()
        content_view = content_view.read()
        content_view_version_info = content_view.version[0].read()
        assert len(content_view.repository) == 1
        assert len(content_view.version) == 1
        swid_repo_path = "{}/{}/content_views/{}/{}/custom/{}/{}/repodata".format(
            CUSTOM_REPODATA_PATH,
            module_org.name,
            content_view.name,
            content_view_version_info.version,
            module_product.name,
            swid_tag_repository.name,
        )
        result = ssh.command(f'ls {swid_repo_path} | grep swidtags.xml.gz')
        assert result.return_code == 0

    @pytest.mark.tier2
    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    def test_negative_create_with_invalid_name(self, name, content_view):
        """Try to create content view filter using invalid names only

        :id: 8cf4227b-75c4-4d6f-b94f-88e4eb586435

        :parametrized: yes

        :expectedresults: Content view filter was not created

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            entities.RPMContentViewFilter(content_view=content_view, name=name).create()

    @pytest.mark.tier2
    def test_negative_create_with_same_name(self, content_view):
        """Try to create content view filter using same name twice

        :id: 73a64ca7-07a3-49ee-8921-0474a16a23ff

        :expectedresults: Second content view filter was not created

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        kwargs = {'content_view': content_view, 'name': gen_string('alpha')}
        entities.RPMContentViewFilter(**kwargs).create()
        with pytest.raises(HTTPError):
            entities.RPMContentViewFilter(**kwargs).create()

    @pytest.mark.tier2
    def test_negative_create_without_cv(self):
        """Try to create content view filter without providing content
        view

        :id: 3b5af53f-9533-482f-9ec9-b313cbb91dd7

        :expectedresults: Content view filter is not created

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        with pytest.raises(HTTPError):
            entities.RPMContentViewFilter(content_view=None).create()

    @pytest.mark.tier2
    def test_negative_create_with_invalid_repo_id(self, content_view):
        """Try to create content view filter using incorrect repository
        id

        :id: aa427770-c327-4ca1-b67f-a9a94edca784

        :expectedresults: Content view filter is not created

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        with pytest.raises(HTTPError):
            entities.RPMContentViewFilter(
                content_view=content_view,
                repository=[gen_integer(10000, 99999)],
            ).create()

    @pytest.mark.tier2
    def test_positive_delete_by_id(self, content_view):
        """Delete content view filter

        :id: 07caeb9d-419d-43f8-996b-456b0cc0f70d

        :expectedresults: Content view filter was deleted

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view).create()
        cvf.delete()
        with pytest.raises(HTTPError):
            cvf.read()

    @pytest.mark.tier2
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_update_name(self, name, content_view):
        """Update content view filter with new name

        :id: f310c161-00d2-4281-9721-6e45cbc5e4ec

        :parametrized: yes

        :expectedresults: Content view filter updated successfully and name was
            changed

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view).create()
        cvf.name = name
        assert cvf.update(['name']).name == name

    @pytest.mark.tier2
    @pytest.mark.parametrize('description', **parametrized(valid_data_list()))
    def test_positive_update_description(self, description, content_view):
        """Update content view filter with new description

        :id: f2c5db28-0163-4cf3-929a-16ba1cb98c34

        :parametrized: yes

        :expectedresults: Content view filter updated successfully and
            description was changed

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view).create()
        cvf.description = description
        cvf = cvf.update(['description'])
        assert cvf.description == description

    @pytest.mark.tier2
    @pytest.mark.parametrize('inclusion', [True, False])
    def test_positive_update_inclusion(self, inclusion, content_view):
        """Update content view filter with new inclusion value

        :id: 0aedd2d6-d020-4a90-adcd-01694b47c0b0

        :parametrized: yes

        :expectedresults: Content view filter updated successfully and
            inclusion value was changed

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view).create()
        cvf.inclusion = inclusion
        cvf = cvf.update(['inclusion'])
        assert cvf.inclusion == inclusion

    @pytest.mark.tier2
    def test_positive_update_repo(self, module_product, sync_repo, content_view):
        """Update content view filter with new repository

        :id: 329ef155-c2d0-4aa2-bac3-79087ae49bdf

        :expectedresults: Content view filter updated successfully and has new
            repository assigned

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo],
        ).create()
        new_repo = entities.Repository(product=module_product).create()
        new_repo.sync()
        content_view.repository = [new_repo]
        content_view.update(['repository'])
        cvf.repository = [new_repo]
        cvf = cvf.update(['repository'])
        assert len(cvf.repository) == 1
        assert cvf.repository[0].id == new_repo.id

    @pytest.mark.tier2
    def test_positive_update_repos(self, module_product, sync_repo, content_view):
        """Update content view filter with multiple repositories

        :id: 478fbb1c-fa1d-4fcd-93d6-3a7f47092ed3

        :expectedresults: Content view filter updated successfully and has new
            repositories assigned

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo],
        ).create()
        repos = [entities.Repository(product=module_product).create() for _ in range(randint(3, 5))]
        for repo in repos:
            repo.sync()
        content_view.repository = repos
        content_view.update(['repository'])
        cvf.repository = repos
        cvf = cvf.update(['repository'])
        assert {repo.id for repo in cvf.repository} == {repo.id for repo in repos}

    @pytest.mark.tier2
    @pytest.mark.parametrize('original_packages', [True, False])
    def test_positive_update_original_packages(self, original_packages, sync_repo, content_view):
        """Update content view filter with new 'original packages' option value

        :id: 0c41e57a-afa3-479e-83ba-01f09f0fd2b6

        :parametrized: yes

        :expectedresults: Content view filter updated successfully and
            'original packages' value was changed

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo],
        ).create()
        cvf.original_packages = original_packages
        cvf = cvf.update(['original_packages'])
        assert cvf.original_packages == original_packages

    @pytest.mark.tier2
    def test_positive_update_repo_with_docker(self, module_product, sync_repo, content_view):
        """Update existing content view filter which has yum repository
        assigned with new docker repository

        :id: 909db0c9-764a-4ca8-9b56-cd8fedd543eb

        :expectedresults: Content view filter was updated successfully and has
            both repositories assigned (yum and docker)

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo],
        ).create()
        docker_repository = entities.Repository(
            content_type='docker',
            docker_upstream_name='busybox',
            product=module_product.id,
            url=CONTAINER_REGISTRY_HUB,
        ).create()
        content_view.repository = [sync_repo, docker_repository]
        content_view = content_view.update(['repository'])
        cvf.repository = [sync_repo, docker_repository]
        cvf = cvf.update(['repository'])
        assert len(cvf.repository) == 2
        for repo in cvf.repository:
            assert repo.id in (sync_repo.id, docker_repository.id)

    @pytest.mark.tier2
    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    def test_negative_update_name(self, name, content_view):
        """Try to update content view filter using invalid names only

        :id: 9799648a-3900-4186-8271-6b2dedb547ab

        :parametrized: yes

        :expectedresults: Content view filter was not updated

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view).create()
        cvf.name = name
        with pytest.raises(HTTPError):
            cvf.update(['name'])

    @pytest.mark.tier2
    def test_negative_update_same_name(self, content_view):
        """Try to update content view filter's name to already used one

        :id: b68569f1-9f7b-4a95-9e2a-a5da348abff7

        :expectedresults: Content view filter was not updated

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        name = gen_string('alpha', 8)
        entities.RPMContentViewFilter(content_view=content_view, name=name).create()
        cvf = entities.RPMContentViewFilter(content_view=content_view).create()
        cvf.name = name
        with pytest.raises(HTTPError):
            cvf.update(['name'])

    @pytest.mark.tier2
    def test_negative_update_cv_by_id(self, content_view):
        """Try to update content view filter using incorrect content
        view ID

        :id: a6477d5f-e4d2-44ba-84f5-8f9004b52eb2

        :expectedresults: Content view filter was not updated

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(content_view=content_view).create()
        cvf.content_view.id = gen_integer(10000, 99999)
        with pytest.raises(HTTPError):
            cvf.update(['content_view'])

    @pytest.mark.tier2
    def test_negative_update_repo_by_id(self, sync_repo, content_view):
        """Try to update content view filter using incorrect repository
        ID

        :id: 43ded66a-331c-4160-820d-261f973a7be2

        :expectedresults: Content view filter was not updated

        :CaseLevel: Integration
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            repository=[sync_repo],
        ).create()
        cvf.repository[0].id = gen_integer(10000, 99999)
        with pytest.raises(HTTPError):
            cvf.update(['repository'])

    @pytest.mark.tier2
    def test_negative_update_repo(self, module_product, sync_repo, content_view):
        """Try to update content view filter with new repository which doesn't
        belong to filter's content view

        :id: e11ba045-da8a-4f26-a0b9-3b1149358717

        :expectedresults: Content view filter was not updated

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        cvf = entities.RPMContentViewFilter(
            content_view=content_view,
            inclusion=True,
            repository=[sync_repo],
        ).create()
        new_repo = entities.Repository(product=module_product).create()
        new_repo.sync()
        cvf.repository = [new_repo]
        with pytest.raises(HTTPError):
            cvf.update(['repository'])


class TestContentViewFilterSearch:
    """Tests that search through content view filters."""

    @pytest.mark.tier1
    def test_positive_search_erratum(self, content_view):
        """Search for an erratum content view filter's rules.

        :id: 6a86060f-6b4f-4688-8ea9-c198e0aeb3f6

        :expectedresults: The search completes with no errors.

        :CaseImportance: Critical

        :BZ: 1242534
        """
        cv_filter = entities.ErratumContentViewFilter(content_view=content_view).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()

    @pytest.mark.tier1
    def test_positive_search_package_group(self, content_view):
        """Search for an package group content view filter's rules.

        :id: 832c50cc-c2c8-48c9-9a23-80956baf5f3c

        :expectedresults: The search completes with no errors.

        :CaseImportance: Critical
        """
        cv_filter = entities.PackageGroupContentViewFilter(content_view=content_view).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()

    @pytest.mark.tier1
    def test_positive_search_rpm(self, content_view):
        """Search for an rpm content view filter's rules.

        :id: 1c9058f1-35c4-46f2-9b21-155ef988564a

        :expectedresults: The search completes with no errors.

        :CaseImportance: Critical
        """
        cv_filter = entities.RPMContentViewFilter(content_view=content_view).create()
        entities.ContentViewFilterRule(content_view_filter=cv_filter).search()


class TestContentViewFilterRule:
    """Tests for content view filter rules."""

    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    @pytest.mark.tier2
    def test_positive_promote_module_stream_filter(self, module_org, content_view_module_stream):
        """Verify Module Stream, Errata Count after Promote, Publish for Content View
        with Module Stream Exclude Filter

        :id: 2f5d21b1-8cbc-4a77-b8a2-09aa466f56a3

        :expectedresults: Content View should get published and promoted successfully
            with correct Module Stream count.

        :CaseLevel: Integration
        """
        # Exclude module stream filter
        content_view = content_view_module_stream
        cv_filter = entities.ModuleStreamContentViewFilter(
            content_view=content_view,
            inclusion=False,
        ).create()
        module_streams = entities.ModuleStream().search(
            query={'search': 'name="{}"'.format('duck')}
        )
        entities.ContentViewFilterRule(
            content_view_filter=cv_filter, module_stream=module_streams
        ).create()
        content_view.publish()
        content_view = content_view.read()
        content_view_version_info = content_view.version[0].read()
        assert len(content_view.repository) == 1
        assert len(content_view.version) == 1

        # the module stream and errata count based in filter after publish
        assert content_view_version_info.module_stream_count == 4
        assert content_view_version_info.errata_counts['total'] == 3

        # Promote Content View
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        promote(content_view.version[0], lce.id)
        content_view = content_view.read()
        content_view_version_info = content_view.version[0].read()

        # assert the module stream and errata count based in filter after promote
        assert content_view_version_info.module_stream_count == 4
        assert content_view_version_info.errata_counts['total'] == 3

    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    @pytest.mark.tier2
    def test_positive_include_exclude_module_stream_filter(self, content_view_module_stream):
        """Verify Include and Exclude Errata filter(modular errata) automatically force the copy
           of the module streams associated to it.

        :id: 20540722-b163-4ebb-b18d-351444ef0c86

        :steps:
            1. Create Include Errata filter
            2. Publish content view, Verify errata and stream count.
            3. Delete Filter (As we can not update the filter inclusion type)
            4. Create Exclude Errata filter
            5. Publish content view, Verify errata and stream count

        :expectedresults: Module Stream count changes automatically after including or
            excluding modular errata

        :CaseLevel: Integration
        """
        content_view = content_view_module_stream
        cv_filter = entities.ErratumContentViewFilter(
            content_view=content_view,
            inclusion=True,
        ).create()
        errata = entities.Errata().search(
            query={'search': f'errata_id="{settings.repos.module_stream_0.errata[2]}"'}
        )[0]
        entities.ContentViewFilterRule(content_view_filter=cv_filter, errata=errata).create()

        content_view.publish()
        content_view = content_view.read()
        content_view_version_info = content_view.version[0].read()

        # verify the module_stream_count and errata_count for Exclude Filter
        assert content_view_version_info.module_stream_count == 2
        assert content_view_version_info.errata_counts['total'] == 1

        # delete the previous content_view_filter
        cv_filter.delete()
        cv_filter = entities.ErratumContentViewFilter(
            content_view=content_view,
            inclusion=False,
        ).create()
        errata = entities.Errata().search(
            query={'search': f'errata_id="{settings.repos.module_stream_0.errata[2]}"'}
        )[0]
        entities.ContentViewFilterRule(content_view_filter=cv_filter, errata=errata).create()

        content_view.publish()
        content_view_version_info = content_view.read().version[1].read()

        # verify the module_stream_count and errata_count for Include Filter
        assert content_view_version_info.module_stream_count == 5
        assert content_view_version_info.errata_counts['total'] == 5

    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    @pytest.mark.tier2
    def test_positive_multi_level_filters(self, content_view_module_stream):
        """Verify promotion of Content View and Verify count after applying
        multi_filters (errata and module stream)

        :id: aeaf2ac7-eda2-4f07-a1dd-fe6057934697

        :expectedresults: Verify module stream and errata count should correct

        :CaseLevel: Integration
        """
        content_view = content_view_module_stream
        # apply include errata filter
        cv_filter = entities.ErratumContentViewFilter(
            content_view=content_view,
            inclusion=True,
        ).create()
        errata = entities.Errata().search(
            query={'search': f'errata_id="{settings.repos.module_stream_0.errata[2]}"'}
        )[0]
        entities.ContentViewFilterRule(content_view_filter=cv_filter, errata=errata).create()

        # apply exclude module filter
        cv_filter = entities.ModuleStreamContentViewFilter(
            content_view=content_view,
            inclusion=False,
        ).create()
        module_streams = entities.ModuleStream().search(
            query={'search': 'name="{}"'.format('walrus')}
        )
        entities.ContentViewFilterRule(
            content_view_filter=cv_filter, module_stream=module_streams
        ).create()
        content_view.publish()
        content_view = content_view.read()
        content_view_version_info = content_view.read().version[0].read()
        # verify the module_stream_count and errata_count for Include Filter
        assert content_view_version_info.module_stream_count == 2
        assert content_view_version_info.errata_counts['total'] == 1

    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    @pytest.mark.tier2
    def test_positive_dependency_solving_module_stream_filter(self, content_view_module_stream):
        """Verify Module Stream Content View Filter's with Dependency Solve 'Yes'.
        If dependency solving enabled then dependent module streams will be fetched
        over even if the exclude filter has been applied.
        e.g. duck module stream is dependent on kangaroo stream, hence even if add only
        exclude filter on kangaroo it will get ignored as it is fetched because of duck
        module stream. but if both duck and kangaroo module streams are in exclude filter
        both will not get fetched.

        :id: ea8a4d95-dc36-4102-b1a9-d53beaf14352

        :expectedresults: Verify dependant/non dependant module streams are getting fetched.

        :CaseLevel: Integration
        """
        content_view = content_view_module_stream
        content_view.solve_dependencies = True
        content_view = content_view.update(['solve_dependencies'])
        cv_filter = entities.ModuleStreamContentViewFilter(
            content_view=content_view,
            inclusion=False,
        ).create()
        module_streams = entities.ModuleStream().search(
            query={'search': 'name="{}" and version="{}'.format('kangaroo', '20180730223407')}
        )
        entities.ContentViewFilterRule(
            content_view_filter=cv_filter, module_stream=module_streams
        ).create()
        content_view.publish()
        content_view = content_view.read()
        content_view_version_info = content_view.read().version[0].read()

        # Total Module Stream Count = 7, Exclude filter rule get ignored.
        assert content_view_version_info.module_stream_count == 7
