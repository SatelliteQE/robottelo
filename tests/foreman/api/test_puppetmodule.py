"""Unit tests for the ``katello/api/v2/puppet_modules`` paths."""
from nailgun import entities
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.decorators import bz_bug_is_open, skip_if_bug_open, tier1
from robottelo.helpers import get_data_file
from robottelo.test import APITestCase
from unittest import skipIf


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
        self.repository = entities.Repository(
            content_type='puppet',
            product=self.product,
        ).create()

    @tier1
    @skip_if_bug_open('bugzilla', 1260206)
    def test_positive_search_no_results(self):
        """Search for puppet modules in an empty repository.

        @Assert: No puppet modules are returned.

        @Feature: PuppetModule
        """
        query = {'repository_id': self.repository.id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 0)

    @skip_if_bug_open('bugzilla', 1260206)
    @skip_if_bug_open('bugzilla', 1329292)
    @tier1
    def test_positive_search_single_result(self):
        """Search for puppet modules in a non-empty repository.

        @Assert: Only the modules in that repository are returned.

        @Feature: PuppetModule
        """
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            self.repository.upload_content(files={'content': handle})
        query = {'repository_id': self.repository.id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 1)


@skipIf(bz_bug_is_open(1329292), 'Skipping due to open Bugzilla bug #1329292')
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
        self.content_view = entities.ContentView(
            organization=self.product.organization,
        ).create()

    @tier1
    def test_positive_search_no_results(self):
        """Search for puppet modules in an emtpy content view version.

        @Assert: No puppet modules are found.

        @Feature: PuppetModule
        """
        self.content_view.publish()
        self.content_view = self.content_view.read()
        query = {'content_view_version_id': self.content_view.version[0].id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 0)

    @tier1
    def test_positive_search_single_result(self):
        """Search for puppet modules in a CVV with one puppet module.

        @Assert: One puppet module is found.

        @Feature: PuppetModule
        """
        # Find the puppet module in `self.repository` and assign it to
        # `self.content_view`. Publish the content view.
        puppet_module = entities.PuppetModule(
            id=self.content_view.available_puppet_modules()['results'][0]['id']
        )
        entities.ContentViewPuppetModule(
            content_view=self.content_view,
            puppet_module=puppet_module,
        ).create()
        self.content_view.publish()

        # Search for all puppet modules in the new content view version.
        self.content_view = self.content_view.read()
        query = {'content_view_version_id': self.content_view.version[0].id}
        self.assertEqual(len(entities.PuppetModule().search(query=query)), 1)
