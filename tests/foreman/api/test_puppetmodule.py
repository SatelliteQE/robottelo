"""Unit tests for the ``katello/api/v2/puppet_modules`` paths.

@Requirement: Puppetmodule

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from nailgun import entities
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.decorators import tier1, upgrade
from robottelo.helpers import get_data_file
from robottelo.test import APITestCase


class RepositorySearchTestCase(APITestCase):
    """Tests that search for puppet modules and filter by repository."""

    @classmethod
    def setUpClass(cls):
        """Create a product. Make it available as ``cls.product``."""
        super(RepositorySearchTestCase, cls).setUpClass()
        cls.product = entities.Product().create()

    def setUp(self):
        """Create a puppet repository as ``self.repository``.

        The repository belongs to ``cls.product``.
        """
        super(RepositorySearchTestCase, self).setUp()
        self.repository = entities.Repository(
            content_type='puppet',
            product=self.product,
        ).create()

    @tier1
    def test_positive_search_no_results(self):
        """Search for puppet modules in an empty repository.

        @id: eafc7a71-d550-4983-9941-b87aa57b83e9

        @expectedresults: No puppet modules are returned.
        """
        query = {'repository_id': self.repository.id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 0)

    @tier1
    def test_positive_search_single_result(self):
        """Search for puppet modules in a non-empty repository.

        @id: 5337b2be-e207-4580-8407-19b88cb40403

        @expectedresults: Only the modules in that repository are returned.
        """
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            self.repository.upload_content(files={'content': handle})
        query = {'repository_id': self.repository.id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 1)


class ContentViewVersionSearchTestCase(APITestCase):
    """Tests that search for puppet modules and filter by content view ver."""

    @classmethod
    def setUpClass(cls):
        """Create a product. Make it available as ``cls.product``."""
        super(ContentViewVersionSearchTestCase, cls).setUpClass()
        cls.product = entities.Product().create()
        repository = entities.Repository(
            content_type='puppet',
            product=cls.product,
        ).create()
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            repository.upload_content(files={'content': handle})

    def setUp(self):
        """Create a content view. Make it available as ``cls.content_view``.

        The content view belongs to organization ``cls.product.organization``.
        """
        super(ContentViewVersionSearchTestCase, self).setUp()
        self.content_view = entities.ContentView(
            organization=self.product.organization,
        ).create()

    @tier1
    def test_positive_search_no_results(self):
        """Search for puppet modules in an emtpy content view version.

        @id: 3a59e2fc-5c95-405e-bf4a-f1fe78e73300

        @expectedresults: No puppet modules are found.
        """
        self.content_view.publish()
        self.content_view = self.content_view.read()
        query = {'content_view_version_id': self.content_view.version[0].id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 0)

    @tier1
    @upgrade
    def test_positive_search_single_result(self):
        """Search for puppet modules in a CVV with one puppet module.

        @id: cc358a91-8640-48e3-851d-383e55ba42c3

        @expectedresults: One puppet module is found.
        """
        # Find the puppet module in `self.repository` and assign it to
        # `self.content_view`. Publish the content view.
        puppet_module = entities.PuppetModule(
            id=self.content_view.available_puppet_modules()['results'][0]['id']
        )
        entities.ContentViewPuppetModule(
            content_view=self.content_view,
            id=puppet_module.id,
        ).create()
        self.content_view.publish()

        # Search for all puppet modules in the new content view version.
        self.content_view = self.content_view.read()
        query = {'content_view_version_id': self.content_view.version[0].id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 1)
