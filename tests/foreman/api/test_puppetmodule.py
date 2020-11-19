"""Unit tests for the ``katello/api/v2/puppet_modules`` paths.

:Requirement: Puppetmodule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.helpers import get_data_file


@pytest.fixture(scope='class')
def class_product():
    product = entities.Product().create()
    yield product
    product.delete()


@pytest.fixture(scope='function')
def blank_repo(class_product):
    return entities.Repository(content_type='puppet', product=class_product).create()


@pytest.fixture(scope='class')
def class_repo_with_content(class_product):
    repo = entities.Repository(content_type='puppet', product=class_product).create()
    with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
        repo.upload_content(files={'content': handle})
    return repo


@pytest.fixture(scope='function')
def make_cv(class_product, class_repo_with_content):
    return entities.ContentView(organization=class_product.organization).create()


class TestRepositorySearch:
    """Tests that search for puppet modules and filter by repository."""

    @pytest.mark.tier1
    def test_positive_search_no_results(self, blank_repo):
        """Search for puppet modules in an empty repository.

        :id: eafc7a71-d550-4983-9941-b87aa57b83e9

        :expectedresults: No puppet modules are returned.

        :CaseImportance: Critical
        """
        query = {'repository_id': blank_repo.id}
        assert len(entities.PuppetModule().search(query=query)) == 0

    @pytest.mark.tier1
    def test_positive_search_single_result(self, blank_repo):
        """Search for puppet modules in a non-empty repository.

        :id: 5337b2be-e207-4580-8407-19b88cb40403

        :expectedresults: Only the modules in that repository are returned.

        :BZ: 1711929

        :CaseImportance: Critical
        """
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            blank_repo.upload_content(files={'content': handle})
        query = {'repository_id': blank_repo.id}
        assert len(entities.PuppetModule().search(query=query)) == 1


class TestContentViewVersionSearch:
    """Tests that search for puppet modules and filter by content view ver."""

    @pytest.mark.tier1
    def test_positive_search_no_results(self, make_cv):
        """Search for puppet modules in an emtpy content view version.

        :id: 3a59e2fc-5c95-405e-bf4a-f1fe78e73300

        :expectedresults: No puppet modules are found.

        :CaseImportance: Critical
        """
        make_cv.publish()
        make_cv = make_cv.read()
        query = {'content_view_version_id': make_cv.version[0].id}
        assert len(entities.PuppetModule().search(query=query)) == 0

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_search_single_result(self, make_cv):
        """Search for puppet modules in a CVV with one puppet module.

        :id: cc358a91-8640-48e3-851d-383e55ba42c3

        :expectedresults: One puppet module is found.

        :CaseImportance: Critical
        """
        # Find the puppet module created in fixture and assign it
        # to `make_cv`. Publish the content view.
        puppet_module = entities.PuppetModule(
            id=make_cv.available_puppet_modules()['results'][0]['id']
        )
        entities.ContentViewPuppetModule(content_view=make_cv, id=puppet_module.id).create()
        make_cv.publish()

        # Search for all puppet modules in the new content view version.
        make_cv = make_cv.read()
        query = {'content_view_version_id': make_cv.version[0].id}
        assert len(entities.PuppetModule().search(query=query)) == 1
