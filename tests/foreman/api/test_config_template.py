"""Unit tests for the ``config_templates`` paths.

A full API reference is available here:
http://theforeman.org/api/apidoc/v2/config_templates.html

"""
from nailgun import client, entities
from robottelo.decorators import skip_if_bug_open
from robottelo.helpers import get_server_credentials
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

    def test_config_template_orgs(self):
        """@Test: Associate a config template with organizations.

        @Assert: Config template is associated with organization

        @Feature: ConfigTemplate

        """
        orgs = [entities.Organization().create() for _ in range(2)]

        # By default, a configuration template should have no organizations.
        conf_templ = entities.ConfigTemplate().create()
        self.assertEqual(0, len(conf_templ.organization))

        # Associate our configuration template with one organization.
        conf_templ.organization = orgs[:1]
        conf_templ = conf_templ.update(['organization'])
        self.assertEqual(len(conf_templ.organization), 1)
        self.assertEqual(conf_templ.organization[0].id, orgs[0].id)

        # Associate our configuration template with two organizations.
        conf_templ.organization = orgs
        conf_templ = conf_templ.update(['organization'])
        self.assertEqual(len(conf_templ.organization), 2)
        self.assertEqual(
            set((org.id for org in conf_templ.organization)),
            set((org.id for org in orgs)),
        )

        # Finally, associate our config template with zero organizations.
        conf_templ.organization = []
        conf_templ = conf_templ.update(['organization'])
        self.assertEqual(len(conf_templ.organization), 0)
