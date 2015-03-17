"""Unit tests for the ``config_templates`` paths.

A full API reference is available here:
http://theforeman.org/api/apidoc/v2/config_templates.html

"""
from nailgun import client
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from robottelo.test import APITestCase


class ConfigTemplateTestCase(APITestCase):
    """Tests for config templates."""

    @skip_if_bug_open('bugzilla', 1202564)
    def test_build_pxe_default(self):
        """@Test: Call the "build_pxe_default" path.

        @Assert: The response is a JSON payload.

        @Feature: ConfigTemplate

        """
        response = client.get(
            entities.ConfigTemplate().path('build_pxe_default'),
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        self.assertIsInstance(response.json(), dict)
