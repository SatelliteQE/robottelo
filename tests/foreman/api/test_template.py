"""Unit tests for the ``config_templates`` paths.

A full API reference is available here:
http://theforeman.org/api/apidoc/v2/config_templates.html


:Requirement: Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

from fauxfactory import gen_string
from nailgun import client, entities
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.helpers import get_nailgun_config
from robottelo.test import APITestCase


class ConfigTemplateTestCase(APITestCase):
    """Tests for config templates."""

    @tier2
    @skip_if_bug_open('bugzilla', 1202564)
    def test_positive_build_pxe_default(self):
        """Call the "build_pxe_default" path.

        :id: ca19d9da-1049-4b39-823b-933fc1a0cebd

        :expectedresults: The response is a JSON payload.

        :CaseLevel: Integration
        """
        response = client.get(
            entities.ConfigTemplate().path('build_pxe_default'),
            auth=settings.server.get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        self.assertIsInstance(response.json(), dict)

    @skip_if_bug_open('bugzilla', 1395229)
    @tier2
    def test_positive_add_orgs(self):
        """Associate a config template with organizations.

        :id: b60907c3-47b9-4bc7-99d6-08615ebe9d68

        :expectedresults: Config template is associated with organization

        :CaseLevel: Integration
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

        :id: 20ccd5c8-98c3-4f22-af50-9760940e5d39

        :expectedresults: Configuration Template is created and contains
            provided name.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                c_temp = entities.ConfigTemplate(name=name).create()
                self.assertEqual(name, c_temp.name)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create configuration template providing an invalid name.

        :id: 2ec7023f-db4d-49ed-b783-6a4fce79064a

        :expectedresults: Configuration Template is not created

        :CaseImportance: Critical
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.ConfigTemplate(name=name).create()

    @tier1
    def test_positive_create_with_template_kind(self):
        """Create a provisioning template providing the template_kind.

        :id: d7309be8-b5c9-4f77-8c4e-e9f2b8982076

        :expectedresults: Provisioning Template is created and contains
            provided template kind.

        :CaseImportance: Critical
        """
        template_kind = choice(entities.TemplateKind().search())
        template = entities.ProvisioningTemplate(
            snippet=False, template_kind=template_kind,
        ).create()
        self.assertEqual(template.template_kind.id, template_kind.id)

    @tier1
    def test_positive_create_with_template_kind_name(self):
        """Create a provisioning template providing existing
        template_kind name.

        :id: 4a1410e4-aa3c-4d27-b062-089e34722bd9

        :expectedresults: Provisioning Template is created

        :BZ: 1379006

        :CaseImportance: Critical
        """
        template_kind = choice(entities.TemplateKind().search())
        template = entities.ProvisioningTemplate(snippet=False)
        template.create_missing()
        template.template_kind = None
        template.template_kind_name = template_kind.name
        template = template.create(create_missing=False)
        self.assertEqual(template.template_kind.id, template_kind.id)

    @tier1
    def test_negative_create_with_template_kind_name(self):
        """Create a provisioning template providing non-existing
        template_kind name.

        :id: e6de9ceb-fe4b-43ce-b7e3-5453ca4bd164

        :expectedresults: 404 error and expected message is returned

        :BZ: 1379006

        :CaseImportance: Critical
        """
        template = entities.ProvisioningTemplate(snippet=False)
        template.create_missing()
        template.template_kind = None
        template.template_kind_name = gen_string('alpha')
        with self.assertRaises(HTTPError) as context:
            template.create(create_missing=False)
        self.assertEqual(context.exception.response.status_code, 404)
        self.assertRegex(
            context.exception.response.text,
            "Could not find template_kind with name"
        )

    @tier1
    def test_positive_update_name(self):
        """Create configuration template providing the initial name,
        then update its name to another valid name.

        :id: 58ccc4ee-5faa-4fb2-bfd0-e19412e230dd

        :expectedresults: Configuration Template is created, and its name can
            be updated.

        :CaseImportance: Critical
        """
        c_temp = entities.ConfigTemplate().create()

        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated = entities.ConfigTemplate(
                    id=c_temp.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated.name)

    @tier1
    def test_positive_update_with_manager_role(self):
        """Create template providing the initial name, then update its name
        with manager user role.

        :id: 0aed79f0-7c9a-4789-99ba-56f2db82f097

        :expectedresults: Provisioning Template is created, and its name can
            be updated.

        :CaseImportance: Critical

        :BZ: 1277308
        """
        user_login = gen_string('alpha')
        user_password = gen_string('alpha')
        new_name = gen_string('alpha')
        org = entities.Organization().create()
        loc = entities.Location().create()
        template = entities.ProvisioningTemplate(
            organization=[org], location=[loc]).create()
        # Create user with Manager role
        role = entities.Role().search(query={'search': 'name="Manager"'})[0]
        entities.User(
            role=[role],
            admin=False,
            login=user_login,
            password=user_password,
            organization=[org],
            location=[loc],
        ).create()
        # Update template name with that user
        cfg = get_nailgun_config()
        cfg.auth = (user_login, user_password)
        updated = entities.ProvisioningTemplate(
            cfg, id=template.id, name=new_name).update(['name'])
        self.assertEqual(updated.name, new_name)

    @tier1
    def test_negative_update_name(self):
        """Create configuration template then update its name to an
        invalid name.

        :id: f6167dc5-26ba-46d7-b61f-14c290d6a8fa

        :expectedresults: Configuration Template is created, and its name is
            not updated.

        :CaseImportance: Critical
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
    @upgrade
    def test_positive_delete(self):
        """Create configuration template and then delete it.

        :id: 1471f17c-4412-4717-a6c4-b57a8d2f8cfd

        :expectedresults: Configuration Template is successfully deleted.

        :CaseImportance: Critical
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

        :id: 8dfbb234-7a52-4873-be72-4de086472669

        :expectedresults: The template is cloned successfully with all values

        :CaseLevel: Integration
        """
        template = entities.ConfigTemplate().create()
        template_origin = template.read_json()

        # remove unique keys
        unique_keys = (u'updated_at', u'created_at', u'id', u'name')
        for key in unique_keys:
            del template_origin[key]

        for name in valid_data_list():
            with self.subTest(name):
                new_template = entities.ConfigTemplate(
                    id=template.clone(data={u'name': name})['id']).read_json()
                for key in unique_keys:
                    del new_template[key]
                self.assertEqual(template_origin, new_template)


class TemplateSyncTestCase(APITestCase):
    """Implements TemplateSync tests from API"""

    @classmethod
    def setUpClass(cls):
        """Setup for TemplateSync functionality

        :setup:

            1. Git repository must exist (in gitlab or github) and its url
               set in ssh:// form in robottelo.constants.
               (note: git@git... form does not work, should start with ssh://)

            2. SSH key must be set to `foreman` user to access that git host
               via ssh://.

            3. Local directory /usr/share/foreman_templates must be created
               with permissions set to `foreman` user:
               mkdir -p \
                 /usr/share/foreman_templates/provisioning_templates/script/
               chown foreman /usr/share/foreman_templates/ -R
               chmod u+rwx /usr/share/foreman_templates/ -R
               chcon -t \
                 httpd_sys_rw_content_t /usr/share/foreman_templates/ -R

            4. Organization and Location must be created to isolate the
               templates ownership.

            5. Administer -> Settings -> TemplateSync settings must be set
               for default options:
               branch -> develop
               repo -> e.g: ssh://git@github.com/username/community-templates
               prefix - > Community (or something else easy to test)

            6. The git repository must be populated with some dummy templates
               for testing and that repo must have content in different
               branches and diverse directory roots. Based on
               foreman/community templates create some templates with
               diverse set of names and prefixes to use for testing the
               regex filtering and also some templates must have Org/Loc
               metadata matching the previously created Org/Loc. the process of
               population this templates repository can be part of this setUp.

               e.g: https://github.com/theforeman/community-templates/tree/
                    develop/provisioning_templates/provision
                    in the above directory there are templates prefixed with
                    `alterator` `atomic` `coreos` `freebsd` etc..

        Information:
            - https://theforeman.org/plugins/foreman_templates/5.0/index.html
            - /apidoc/v2/template/import.html
            - /apidoc/v2/template/export.html
            - http://pastebin.test.redhat.com/516304

        """

    # Import tests

    @stubbed()
    @tier1
    def test_positive_import_filtered_templates_from_git(self):
        """Assure only templates with a given filter regex are pulled from
        git repo.

        :id: 628a95d6-7a4e-4e56-ad7b-d9fecd34f765

        :Steps:
            1. Using nailgun or direct API call
               import only the templates matching with regex e.g: `^atomic.*`
               refer to: `/apidoc/v2/template/import.html`

        :expectedresults:
            1. Assert result is {'message': 'success'} and template imported
            2. Assert no other template has been imported but only those
               matching specified regex.
               NOTE: Templates are always imported with a prefix defaults to
               `community` unless it is specified as empty string

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_import_filtered_templates_from_git(self):
        """Assure templates with a given filter regex are NOT pulled from
        git repo.

        :id: a6857454-249b-4a2e-9b53-b5d7b4eb34e3

        :Steps:
            1. Using nailgun or direct API call
               import the templates NOT matching with regex e.g: `^freebsd.*`
               refer to: `/apidoc/v2/template/import.html` using the
               {'negate': true} in POST body to negate the filter regex.

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert templates mathing the regex were not pulled.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_import_from_branch(self):
        """Assure only templates from a given branch are imported

        :id: 8ccb2c13-808d-41b7-afd7-22431311d74a

        :Steps:
            1. Using nailgun or direct API call
               import templates specifying a git branch e.g:
               `-d {'branch': 'testing'}` in POST body.

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates imported
            2. Assert only templates from that branch were imported

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_import_from_subdirectory(self):
        """Assure only templates from a given subdirectory are imported

        :id: 9d368931-045b-4bfd-94ea-ef67006191a1

        :Steps:
            1. Using nailgun or direct API call
               import templates specifying a git subdirectory e.g:
               `-d {'dirname': 'test_sub_dir'}` in POST body.

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates imported
            2. Assert only templates from that subdirectory were imported

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_import_locked_template(self):
        """Assure locked templates are not pulled from repository.

        :id: 88e21cad-448e-45e0-add2-94493a1319c5

        :Steps:
            1. Using nailgun or direct API call try to import a locked template

        :expectedresults:
            1. Assert locked template is not updated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_import_force_locked_template(self):
        """Assure locked templates are updated from repository when `force` is
        specified.

        :id: b80fbfc4-bcab-4a5d-b6c1-0e22906cd8ab

        :Steps:
            1. Using nailgun or direct API call
               import some of the locked template specifying the `force`
               parameter e.g: `-d {'force': true}` in POST body.

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert locked template is forced to update

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_import_associated_with_taxonomies(self):
        """Assure imported template is automatically associated with
        Organization and Location.

        :id: 04a14a56-bd71-412b-b2da-4b8c3991c401

        :Steps:
            1. Using nailgun or direct API call
               import some template containing metadata with Org/Loc specs
               and specify the `associate` parameter
               e.g: `-d {'associate': 'always'}` in POST body.

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert template is imported and org/loc are associated based on
               template metadata.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_import_all_templates_from_repo(self):
        """Assure all templates are imported if no filter is specified.

        :id: 95ac9543-d989-44f4-b4d9-18f20a0b58b9

        :Steps:
            1. Using nailgun or direct API call
               import all templates from repository (ensure filters are empty)

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert all existing templates are imported.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_file_based_sync(self):
        """Assure template sync work from a local directory

        :id: cb39b80f-9114-4da0-bf7d-f7ec2b71edc3

        :steps:
            1. Create a new template in local filesystem using $FOLDER=
               '/usr/share/foreman_templates/provisioning_templates/script/'::

                sudo -H -u foreman cat <<EOF > $FOLDER/community_test.erb
                This is a test template
                <%#
                name: Community Test
                snippet: false
                model: ProvisioningTemplate
                kind: script
                %>
                EOF

            2. Call import API endpoint to import that specific template::

                POST to /api/v2/templates/import passing data
                {verbose: false, repo: /usr/share/foreman_templates/,
                    filter: 'Community Test'}
                Call the above using requests.post or nailgun

            3. After asserting the template is imported, change its contents
               using nailgun API::

                obj = entities.ProvisioningTemplate().search(
                    query={'search': 'name="Community Test"'}
                )[0].read()
                assert 'This is a test template' in obj.template
                obj.template += 'imported template has been updated'
                obj.update(['template'])

            4. Export the template back to the $FOLDER::

                POST to /api/v2/templates/export passing same data as in step 2

            5. After asserting the template was exported, change its contents
               directly in filesystem::

                sudo -u foreman echo 'Hello World' >> $FOL../community_test.erb

            6. Import the template again repeating step 2

        :expectedresults:
            1. After step 2, assert template was imported (use nailgun as in
               step 3)
            2. After step 4, assert template was exported and updated
               `cat $FOLDER/community_test.erb | grep 'has been updated`
            3. After step 6, assert template was imported again and the new
               content is updated (use nailgun as in step 3)


        The complete test script is available in
        http://pastebin.test.redhat.com/516304

        """

    # Export tests

    @stubbed()
    @tier1
    def test_positive_export_filtered_templates_to_git(self):
        """Assure only templates with a given filter regex are pushed to
        git template (new templates are created, existing updated).

        :id: fd583f85-f170-4b93-b9b1-36d72f31c31f

        :Steps:
            1. Using nailgun or direct API call
               export only the templates matching with regex e.g: `^atomic.*`
               refer to: `/apidoc/v2/template/export.html`

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates exported.
            2. Assert no other template has been exported but only those
               matching specified regex.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_export_filtered_templates_to_git(self):
        """Assure templates with a given filter regex are NOT pushed to
        git repo.

        :id: ca1186f7-a0d5-4e5e-b7dd-de293308bc90

        :Steps:
            1. Using nailgun or direct API call
               export the templates NOT matching with regex e.g: `^freebsd.*`
               refer to: `/apidoc/v2/template/export.html` using the
               {'negate': true, 'filter': '^freebsd.*'} in POST body to
               negate the filter regex.

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert templates mathing the regex are not pushed

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_export_to_branch(self):
        """Assure templates are exported to specified existing branch

        :id: 2bef9597-1b5a-4010-b6e9-a3540e045a7b

        :Steps:
            1. Using nailgun or direct API call
               export templates specifying a git branch e.g:
               `-d {'branch': 'testing'}` in POST body.

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates exported
            2. Assert templates were exported to specified branch on repo

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_export_to_subdirectory(self):
        """Assure templates are exported to repository existing subdirectory

        :id: 8ea11a1a-165e-4834-9387-7accb4c94e77

        :Steps:
            1. Using nailgun or direct API call
               export templates specifying a git subdirectory e.g:
               `-d {'dirname': 'test_sub_dir'}` in POST body

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates exported
            2. Assert templates are exported to the given subdirectory on repo

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_export_and_import_with_metadata(self):
        """Assure exported template contains metadata.

        :id: ba8a34ce-c2c6-4889-8729-59714c0a4b19

        :Steps:
            1. Create a template using nailgun entity and specify Org/Loc.
            2. Using nailgun or direct API call
               export the template containing metadata with Org/Loc specs
               and specify the `metadata_export_mode` parameter
               e.g: `-d {'metadata_export_mode': 'refresh'}` in POST body
            3. Use import to pull this specific template (using filter) and
               specifying `associate` and a different `prefix`

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert template is exported and org/loc are present on
               template metadata
            3. Assert template can be imported with associated Org/Loc
               as specified in metadata

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_export_all_templates_to_repo(self):
        """Assure all templates are exported if no filter is specified.

        :id: 0bf6fe77-01a3-4843-86d6-22db5b8adf3b

        :Steps:
            1. Using nailgun or direct API call
               export all templates to repository (ensure filters are empty)

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert all existing templates were exported to repository

        :CaseImportance: Critical
        """
