# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Content View CLI
"""

from robottelo.cli.content_view import Content_View
from robottelo.cli.org import Org
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_content_view
from robottelo.common.helpers import generate_string
from tests.foreman.cli.basecli import BaseCLI


class TestContentView(BaseCLI):
    """
    Test class for ContentView CLI.
    """

    def test_positive_create(self):
        """
        @test: Create Content View
        @feature: Content View - Create Content View
        @assert: Content View is created
        """

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        con_name = generate_string("alpha", 10)
        con_view = make_content_view({'name': con_name,
                                      'organization-id': org_obj['label']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "Should not have gotten an error")
        result = Content_View.info({'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(con_view['name'], result.stdout['name'])

    def test_negative_create_1(self):
        """
        @test: Create content-view with blank name
        @feature: Content View
        @assert: content-view is not created
        """
        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        
        result = Content_View.create({'name': '', 'organization-id': org_obj['label']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(
            len(result.stderr), 0, "There should be an exception here.")

    def test_negative_create_2(self):
        """
        @test: Create content-view with bad org
        @feature: Content View
        @assert: content-view is not created
        """
        
        org_name = generate_string("alpha", 10)
        con_name = generate_string("alpha", 10)
        result = Content_View.create({'name': con_name, 'organization-id': org_name})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(
            len(result.stderr), 0, "There should be an exception here.")
