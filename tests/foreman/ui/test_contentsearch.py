# -*- encoding: utf-8 -*-
"""Test class for Content Search UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.common.constants import FAKE_0_YUM_REPO
from robottelo.ui.session import Session
from robottelo.test import UITestCase


class TestContentSearchUI(UITestCase):
    """Implement tests for content search via UI"""

    def test_search_content_view(self):
        """@Test: Create content view with yum repository assigned to it.
        Search for package inside of it

        @Feature: Content Search

        @Assert: Content search functionality works as intended and expected
        package is present inside of content view

        """
        # Prepare data for content search
        org = entities.Organization().create()
        product = entities.Product(
            name=gen_string('alpha'),
            organization=org,
        ).create()
        yum_repo = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            content_type='yum',
            url=FAKE_0_YUM_REPO,
        ).create()
        yum_repo.sync()
        content_view = entities.ContentView(
            name=gen_string('alpha'),
            organization=org,
        ).create()
        content_view.repository = [yum_repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(len(content_view.repository), 1)
        content_view.publish()

        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            session.nav.go_to_content_search()
            self.content_search.add_filter('Content Views', content_view.name)
            # It is necessary to choose 'Packages' from Content dropdown as we
            # are searching for packages in Content View
            self.content_search.add_search_criteria('Packages', '')
            expected_result = [
                ['Content View', content_view.name, True],
                ['Product', product.name, True],
                ['Repository', yum_repo.name, True],
                ['Package', 'bear', False],
                ['Package', 'cat', False],
            ]
            self.content_search.search(expected_result)
