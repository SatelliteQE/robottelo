"""Unit tests for the ``config_templates`` paths.

A full API reference is available here:
http://theforeman.org/api/apidoc/v2/config_templates.html

"""
from nailgun import client, entities
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
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

    def test_associate_config_template_with_organization(self):
        """@Test: Associate config template with organization

        @Assert: Config template is associated with organization

        @Feature: ConfigTemplate

        """
        org_1 = entities.Organization().create()
        org_2 = entities.Organization().create()

        # By default, a configuration template should have no organizations.
        conf_templ = entities.ConfigTemplate().create()
        self.assertEqual(0, len(conf_templ.organization))

        # Associate our configuration template with one organization.
        client.put(
            conf_templ.path(),
            {'config_template': {'organization_ids': [org_1.id]}},
            verify=False,
            auth=get_server_credentials(),
        ).raise_for_status()

        # Verify that the association succeeded.
        conf_templ = conf_templ.read()
        self.assertEqual(1, len(conf_templ.organization))
        self.assertEqual(org_1.id, conf_templ.organization[0].id)

        # Associate our configuration template with two organizations.
        client.put(
            conf_templ.path(),
            {'config_template': {'organization_ids': [org_1.id, org_2.id]}},
            verify=False,
            auth=get_server_credentials(),
        ).raise_for_status()

        # Verify that the association succeeded.
        conf_templ = conf_templ.read()
        self.assertEqual(2, len(conf_templ.organization))
        for org in conf_templ.organization:
            self.assertIn(org.id, (org_1.id, org_2.id))

        # Finally, associate our config template with zero organizations.
        client.put(
            conf_templ.path(),
            {'config_template': {'organization_ids': []}},
            verify=False,
            auth=get_server_credentials(),
        ).raise_for_status()

        # Verify that the association succeeded.
        conf_templ = conf_templ.read()
        self.assertEqual(conf_templ.organization, [])
