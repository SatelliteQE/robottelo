"""Unit tests for the ``config_templates`` paths.

A full API reference is available here:
http://theforeman.org/api/apidoc/v2/config_templates.html


@Requirement: Template

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase


class ConfigTemplateTestCase(APITestCase):
    """Tests for config templates."""

    @tier2
    @skip_if_bug_open('bugzilla', 1202564)
    def test_positive_build_pxe_default(self):
        """Call the "build_pxe_default" path.

        @id: ca19d9da-1049-4b39-823b-933fc1a0cebd

        @Assert: The response is a JSON payload.

        @CaseLevel: Integration
        """
        response = client.get(
            entities.ConfigTemplate().path('build_pxe_default'),
            auth=settings.server.get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        self.assertIsInstance(response.json(), dict)

    @tier2
    def test_positive_add_orgs(self):
        """Associate a config template with organizations.

        @id: b60907c3-47b9-4bc7-99d6-08615ebe9d68

        @Assert: Config template is associated with organization

        @CaseLevel: Integration
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

    @tier1
    def test_positive_create_with_name(self):
        """Create a configuration template providing the initial name.

        @id: 20ccd5c8-98c3-4f22-af50-9760940e5d39

        @Assert: Configuration Template is created and contains provided name.
        """
        for name in valid_data_list():
            with self.subTest(name):
                c_temp = entities.ConfigTemplate(name=name).create()
                self.assertEqual(name, c_temp.name)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create configuration template providing an invalid name.

        @id: 2ec7023f-db4d-49ed-b783-6a4fce79064a

        @Assert: Configuration Template is not created
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.ConfigTemplate(name=name).create()

    @tier1
    def test_positive_update_name(self):
        """Create configuration template providing the initial name,
        then update its name to another valid name.

        @id: 58ccc4ee-5faa-4fb2-bfd0-e19412e230dd

        @Assert: Configuration Template is created, and its name can be
        updated.
        """
        c_temp = entities.ConfigTemplate().create()

        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated = entities.ConfigTemplate(
                    id=c_temp.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated.name)

    @tier1
    def test_negative_update_name(self):
        """Create configuration template then update its name to an
        invalid name.

        @id: f6167dc5-26ba-46d7-b61f-14c290d6a8fa

        @Assert: Configuration Template is created, and its name is not
        updated.
        """
        c_temp = entities.ConfigTemplate().create()
        for new_name in invalid_names_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.ConfigTemplate(
                        id=c_temp.id, name=new_name).update(['name'])
                c_temp = entities.ConfigTemplate(id=c_temp.id).read()
                self.assertNotEqual(c_temp.name, new_name)

    @tier1
    def test_positive_delete(self):
        """Create configuration template and then delete it.

        @id: 1471f17c-4412-4717-a6c4-b57a8d2f8cfd

        @Assert: Configuration Template is successfully deleted.
        """
        for name in valid_data_list():
            with self.subTest(name):
                c_temp = entities.ConfigTemplate().create()
                c_temp.delete()
                with self.assertRaises(HTTPError):
                    entities.ConfigTemplate(id=c_temp.id).read()

    @tier2
    def test_positive_clone(self):
        """Assure ability to clone a provisioning template

        @id: 8dfbb234-7a52-4873-be72-4de086472669

        @Assert: The template is cloned successfully with all values

        @CaseLevel: Integration
        """
        template = entities.ConfigTemplate().create()
        template_origin = template.read_json()

        # remove unique keys
        uniqe_keys = (u'updated_at', u'created_at', u'id', u'name')
        for key in uniqe_keys:
            del template_origin[key]

        for name in valid_data_list():
            with self.subTest(name):
                new_template = entities.ConfigTemplate(
                    id=template.clone(data={u'name': name})['id']).read_json()
                for key in uniqe_keys:
                    del new_template[key]
                self.assertEqual(template_origin, new_template)
