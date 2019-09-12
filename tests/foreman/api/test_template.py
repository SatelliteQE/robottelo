"""Unit tests for the ``config_templates`` paths.

A full API reference is available here:
http://theforeman.org/api/apidoc/v2/config_templates.html

:Requirement: Template

:CaseAutomation: Automated

:CaseComponent: ProvisioningTemplates

:TestType: Functional

:CaseLevel: Integration

:CaseImportance: High

:Upstream: No
"""
import time

from random import choice

from fauxfactory import gen_string
from nailgun import client, entities
from requests import get
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import (
    FOREMAN_TEMPLATE_IMPORT_URL,
    FOREMAN_TEMPLATE_TEST_TEMPLATE
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.helpers import get_nailgun_config
from robottelo import ssh
from robottelo.test import APITestCase


class ConfigTemplateTestCase(APITestCase):
    """Tests for config templates

    :CaseComponent: ProvisioningTemplates

    :CaseLevel: Acceptance
    """

    @tier2
    def test_positive_build_pxe_default(self):
        """Call the "build_pxe_default" path.

        :id: ca19d9da-1049-4b39-823b-933fc1a0cebd

        :expectedresults: The response is a JSON payload.

        :CaseLevel: Integration

        :CaseImportance: Critical

        :BZ: 1202564
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

        :id: b60907c3-47b9-4bc7-99d6-08615ebe9d68

        :expectedresults: Config template is associated with organization

        :CaseImportance: Medium

        :BZ: 1395229
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

        :CaseLevel: Component

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

        :CaseLevel: Component

        :CaseImportance: Medium
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

        :CaseLevel: Component

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

        :CaseLevel: Component

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

        :CaseLevel: Component

        :CaseImportance: Medium
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

        :CaseLevel: Component

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

        :CaseImportance: Medium

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

        :CaseImportance: Medium

        :CaseLevel: Component
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

        :CaseLevel: Component
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

        :CaseLevel: Component

        :CaseImportance: Medium
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
    """Implements TemplateSync tests from API

    :CaseComponent: TemplatesPlugin

    :CaseLevel: Acceptance
    """

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
        if not get(FOREMAN_TEMPLATE_IMPORT_URL).status_code == 200:
            raise HTTPError('The foreman templates git url is not accessible')
        # Downloading Test Template
        if not ssh.command('[ -f example_template.erb ]').return_code == 0:
            ssh.command('wget {0}'.format(FOREMAN_TEMPLATE_TEST_TEMPLATE))

    @classmethod
    def tearDownClass(cls):
        """Deletes /usr/share/foreman_templates directory on satellite"""
        if ssh.command('[ -d /usr/share/foreman_templates ]').return_code == 0:
            ssh.command('rm -rf /usr/share/foreman_templates')

    def create_import_export_local_directory(self, dir_name):
        """Creates a local directory on satellite from where the templates will
            be import or exported to

        :param dir_name str: The directory name which will be created as export
            or import directory under ```/usr/share/foreman_templates```
        """
        dir_path = '/usr/share/foreman_templates/{}'.format(dir_name)
        if ssh.command('[ -d {} ]'.format(dir_path)).return_code == 0:
            if ssh.command('rm -rf {}'.format(dir_path)) == 1:
                raise OSError(
                    'The existing export directory {} still exists! Please '
                    'remove, recreate it and try again'.format(dir_path))
        if not ssh.command(
                'mkdir -p {}'.format(dir_path)).return_code == 0:
            raise OSError('The export directory is not being created!')
        ssh.command('chown foreman {} -R'.format(dir_path))
        ssh.command('chmod 777 {} -R'.format(dir_path))
        ssh.command('chcon -t httpd_sys_rw_content_t {} -R'.format(dir_path))
        return dir_path

    @tier2
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
            3. Assert json output doesnt have
               'Name is not matching filter condition, skipping' info message
               for imported template

        :CaseImportance: High
        """
        org = entities.Organization().create()
        filtered_imported_templates = entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'filter': 'robottelo',
                'organization_id': org.id,
                'prefix': org.name
            })
        imported_count = [
            template['imported'] for template in filtered_imported_templates[
                'message']['templates']].count(True)
        self.assertEqual(imported_count, 7)
        ptemplates = entities.ProvisioningTemplate().search(
            query={
                'per_page': 1000,
                'search': 'name~robottelo',
                'organization_id': org.id})
        self.assertEqual(len(ptemplates), 5)
        ptables = entities.PartitionTable().search(
            query={
                'per_page': 1000,
                'search': 'name~robottelo',
                'organization_id': org.id})
        self.assertEqual(len(ptables), 1)
        jtemplates = entities.JobTemplate().search(
            query={
                'per_page': 1000,
                'search': 'name~robottelo',
                'organization_id': org.id})
        self.assertEqual(len(jtemplates), 1)

    @tier2
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

        :CaseImportance: Medium
        """
        org = entities.Organization().create()
        filtered_imported_templates = entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'filter': 'robottelo',
                'organization_id': org.id,
                'prefix': org.name,
                'negate': True
            })
        not_imported_count = [
            template['imported'] for template in filtered_imported_templates[
                'message']['templates']].count(False)
        self.assertEqual(not_imported_count, 7)
        ptemplates = entities.ProvisioningTemplate().search(
            query={
                'per_page': 1000,
                'search': 'name~jenkins',
                'organization_id': org.id})
        self.assertEqual(len(ptemplates), 6)
        ptables = entities.PartitionTable().search(
            query={
                'per_page': 1000,
                'search': 'name~jenkins',
                'organization_id': org.id})
        self.assertEqual(len(ptables), 1)
        jtemplates = entities.JobTemplate().search(
            query={
                'per_page': 1000,
                'search': 'name~jenkins',
                'organization_id': org.id})
        self.assertEqual(len(jtemplates), 1)

    @stubbed()
    @tier2
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

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
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

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
    def test_negative_import_locked_template(self):
        """Assure locked templates are not pulled from repository.

        :id: 88e21cad-448e-45e0-add2-94493a1319c5

        :Steps:
            1. Using nailgun or direct API call try to import a locked template

        :expectedresults:
            1. Assert locked template is not updated

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
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

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
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

        :CaseImportance: Low

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
    def test_positive_import_all_templates_from_repo(self):
        """Assure all templates are imported if no filter is specified.

        :id: 95ac9543-d989-44f4-b4d9-18f20a0b58b9

        :Steps:
            1. Using nailgun or direct API call
               import all templates from repository (ensure filters are empty)

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert all existing templates are imported.

        :CaseImportance: Low

        :CaseAutomation: NotAutomated
        """

    @tier2
    def test_positive_export_filtered_templates_to_localdir(self):
        """Assure only templates with a given filter regex are pushed to
        local directory (new templates are created, existing updated).

        :id: b7c98b75-4dd1-4b6a-b424-35b0f48c25db

        :Steps:
            1. Using nailgun or direct API call
               export only the templates matching with regex e.g: `robottelo`
               refer to: `/apidoc/v2/template/export.html`

        :expectedresults:
            1. Assert result is {'message': 'success'} and templates exported.
            2. Assert no other template has been exported but only those
               matching specified regex.

        :CaseImportance: Low
        """
        # First import all the templates to be exported in dir later
        org = entities.Organization().create()
        all_imported_templates = entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'organization_id': org.id,
                'prefix': org.name
            })
        imported_count = [
            template['imported'] for template in all_imported_templates[
                'message']['templates']].count(True)
        self.assertEqual(imported_count, 16)  # Total Count
        # Export some filtered templates to local dir
        dir_name = 'test-b7c98b75-4dd1-4b6a-b424-35b0f48c25db'
        dir_path = self.create_import_export_local_directory(dir_name)
        exported_temps = entities.Template().exports(
            data={
                'repo': dir_path,
                'organization_ids': [org.id],
                'filter': 'robottelo'
            })
        self.assertEqual(len(exported_temps['message']['templates']), 7)
        self.assertEqual(
            ssh.command(
                'find {} -type f | wc -l'.format(dir_path)).stdout[0], '7')

    @stubbed()
    @tier2
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

        :CaseAutomation: NotAutomated

        The complete test script is available in
        http://pastebin.test.redhat.com/516304

        :CaseAutomation: NotAutomated

        :CaseImportance: Medium
        """

    # Export tests
    @stubbed()
    @tier2
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

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
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

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
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

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
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

        :CaseImportance: Medium

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
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

        :CaseImportance: Low

        :CaseAutomation: NotAutomated
        """

    @stubbed()
    @tier2
    def test_positive_export_all_templates_to_repo(self):
        """Assure all templates are exported if no filter is specified.

        :id: 0bf6fe77-01a3-4843-86d6-22db5b8adf3b

        :Steps:
            1. Using nailgun or direct API call
               export all templates to repository (ensure filters are empty)

        :expectedresults:
            1. Assert result is {'message': 'success'}
            2. Assert all existing templates were exported to repository

        :CaseImportance: Low

        :CaseAutomation: NotAutomated
        """

    # Take Templates out of Tech Preview Feature Tests
    @tier3
    def test_positive_import_json_output_verbose_true(self):
        """Assert all the required fields displayed in import output when
        verbose is True

        :id: 74b0a701-341f-4062-9769-e5cb1a1c4792

        :Steps:
            1. Using nailgun or direct API call
               Impot a template with verbose `True` option

        :expectedresults:
            1. Assert json output has all the following fields
               'name', 'imported', 'diff', 'additional_errors', 'exception',
               'validation_errors', 'file'

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        templates = entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'filter': 'robottelo',
                'organization_id': org.id,
                'prefix': org.name,
                'verbose': True
            })
        expected_fields = [
            'name', 'imported', 'diff', 'additional_errors', 'exception',
            'validation_errors', 'file', 'type', 'id', 'changed'
        ]
        actual_fields = templates['message']['templates'][0].keys()
        self.assertListEqual(sorted(actual_fields), sorted(expected_fields))

    @tier2
    def test_positive_import_json_output_verbose_false(self):
        """Assert all the required fields displayed in import output when
        verbose is `False`

        :id: 7d7c65f5-1af3-4a9b-ba9e-70130f61d7cb

        :Steps:
            1. Using nailgun or direct API call
               Impot a template with verbose `False` option

        :expectedresults:
            1. Assert json output has all the following fields
               'name', 'imported', 'changed', 'additional_errors', 'exception',
               'validation_errors', 'file'

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        templates = entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'filter': 'robottelo',
                'organization_id': org.id,
                'prefix': org.name,
                'verbose': False
            })
        expected_fields = [
            'name', 'imported', 'changed', 'additional_errors', 'exception',
            'validation_errors', 'file', 'type', 'id'
        ]
        actual_fields = templates['message']['templates'][0].keys()
        self.assertListEqual(sorted(actual_fields), sorted(expected_fields))

    @tier2
    def test_positive_import_json_output_changed_key_true(self):
        """Assert template imports output `changed` key returns `True` when
        template data gets updated

        :id: 4b866144-822c-4786-9188-53bc7e2dd44a

        :Steps:
            1. Using nailgun or direct API call
               Create a template and import it from a source
            2. Update the template data in source location
            3. Using nailgun or direct API call
               Re-import the same template

        :expectedresults:
            1. On reimport, Assert json output returns 'changed' as `true`
            2. Assert json output returns diff key with difference as value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        pre_template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
                'prefix': org.name
            })
        self.assertTrue(
            bool(pre_template['message']['templates'][0]['imported']))
        ssh.command(
            'echo " Updating Template data." >> '
            '{}/example_template.erb'.format(
                dir_path)
        )
        post_template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
                'prefix': org.name
            })
        self.assertTrue(
            bool(post_template['message']['templates'][0]['changed']))

    @tier2
    def test_positive_import_json_output_changed_key_false(self):
        """Assert template imports output `changed` key returns `False` when
        template data gets updated

        :id: 64456c0c-c2c6-4a1c-a16e-54ca4a8b66d3

        :Steps:
            1. Using nailgun or direct API call
               Create a template and import it from a source
            2. Dont update the template data in source location
            3. Using nailgun or direct API call
               Re-import the same template

        :expectedresults:
            1. On reiport, Assert json output returns 'changed' as `false`

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        pre_template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
                'prefix': org.name
            })
        self.assertTrue(
            bool(pre_template['message']['templates'][0]['imported']))
        post_template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
                'prefix': org.name
            })
        self.assertFalse(
            bool(post_template['message']['templates'][0]['changed']))

    @tier2
    def test_positive_import_json_output_name_key(self):
        """Assert template imports output `name` key returns correct name

        :id: a5639368-3d23-4a37-974a-889e2ec0916e

        :Steps:
            1. Using nailgun or direct API call
               Create a template with some name and import it from a source

        :expectedresults:
            1. On Import, Assert json output returns 'name' key with correct
            name as per template metadata

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        template_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        ssh.command(
            'sed -ie "s/name: .*/name: {0}/" {1}/example_template.erb'.format(
                template_name, dir_path)
        )
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
            })
        self.assertIn('name', template['message']['templates'][0].keys())
        self.assertEqual(
            template_name, template['message']['templates'][0]['name'])

    @tier2
    def test_positive_import_json_output_imported_key(self):
        """Assert template imports output `imported` key returns `True` on
        successful import

        :id: 5bc11163-e8f3-4744-8a76-5c16e6e46e86

        :Steps:
            1. Using nailgun or direct API call
               Create a template and import it from a source

        :expectedresults:
            1. On Import, Assert json output returns 'imported' key as `True`

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
                'prefix': org.name
            })
        self.assertTrue(
            bool(template['message']['templates'][0]['imported']))

    @tier2
    def test_positive_import_json_output_file_key(self):
        """Assert template imports output `file` key returns correct file name
        from where the template is imported

        :id: da0b094c-6dc8-4526-b115-8e08bfb05fbb

        :Steps:
            1. Using nailgun or direct API call
               Create a template with some name and import it from a source

        :expectedresults:
            1. Assert json output returns 'file' key with correct
            file name

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
            })
        self.assertEqual(
            'example_template.erb',
            template['message']['templates'][0]['file'])

    @tier2
    def test_positive_import_json_output_corrupted_metadata(self):
        """Assert template imports output returns corrupted metadata error for
        incorrect metadata in template

        :id: 6bd5bc6b-a7a2-4529-9df6-47a670cd86d8

        :Steps:
            1. Create a template with wrong syntax in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has error contains
            'Failed to parse metadata' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Medium
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        ssh.command(
            'sed -ie "s/<%#/$#$#@%^$^@@RT$$/" {0}/example_template.erb'.format(
                dir_path)
        )
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
            })
        self.assertFalse(bool(template['message']['templates'][0]['imported']))
        self.assertEqual(
            'Failed to parse metadata',
            template['message']['templates'][0]['additional_errors'])

    @tier2
    def test_positive_import_json_output_filtered_skip_message(self):
        """Assert template imports output returns template import skipped info
        for templates whose name doesnt match the filter

        :id: db68b5de-7647-4568-b79c-2aec3292328a

        :Steps:
            1. Using nailgun or direct API call
               Create template with name not matching filter

        :expectedresults:
            1. Assert json output has info contains
            'Name is not matching filter condition, skipping' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id,
                'filter': gen_string('alpha')
            })
        self.assertFalse(bool(template['message']['templates'][0]['imported']))
        self.assertEqual(
            "Skipping, 'name' filtered out based on"
            " 'filter' and 'negate' settings",
            template['message']['templates'][0]['additional_errors'])

    @tier2
    def test_positive_import_json_output_no_name_error(self):
        """Assert template imports output returns no name error for template
        without name

        :id: 259a8a3a-8749-442d-a2bc-51e9af89ce8c

        :Steps:
            1. Create a template without name in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has error contains
            'No 'name' found in metadata' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        ssh.command(
            'sed -ie "s/name: .*/name: /" {}/example_template.erb'.format(
                dir_path)
        )
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id
            })
        self.assertFalse(bool(template['message']['templates'][0]['imported']))
        self.assertEqual(
            "No 'name' found in metadata",
            template['message']['templates'][0]['additional_errors'])

    @tier2
    def test_positive_import_json_output_no_model_error(self):
        """Assert template imports output returns no model error for template
        without model

        :id: d3f1ffe4-58d7-45a8-b278-74e081dc5062

        :Steps:
            1. Create a template without model keyword in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has error contains
            'No 'model' found in metadata' text
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        ssh.command(
            'sed -ie "/model: .*/d" {0}/example_template.erb'.format(
                dir_path)
        )
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id
            })
        self.assertFalse(bool(template['message']['templates'][0]['imported']))
        self.assertEqual(
            "No 'model' found in metadata",
            template['message']['templates'][0]['additional_errors'])

    @tier2
    def test_positive_import_json_output_blank_model_error(self):
        """Assert template imports output returns blank model name error for
        template without template name

        :id: 5007b12d-1cf6-49e6-8e54-a189d1a209de

        :Steps:
            1. Create a template with blank model name in metadata
            2. Using nailgun or direct API call
               Import above template

        :expectedresults:
            1. Assert json output has additional_error contains
               'Template type was not found, maybe you are missing a plugin?'
            2. Assert 'imported' key returns 'false' value

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        ssh.command('cp example_template.erb {}'.format(dir_path))
        ssh.command(
            'sed -ie "s/model: .*/model: /" {}/example_template.erb'.format(
                dir_path)
        )
        template = entities.Template().imports(
            data={
                'repo': dir_path,
                'organization_id': org.id
            })
        self.assertFalse(bool(template['message']['templates'][0]['imported']))
        self.assertEqual(
            "Template type  was not found, are you missing a plugin?",
            template['message']['templates'][0]['additional_errors'])

    @tier2
    def test_positive_export_json_output(self):
        """Assert template export output returns template names

        :id: 141b893d-72a3-47c2-bb03-004c757bcfc9

        :Steps:
            1. Using nailgun or direct API call
               Export all the templates

        :expectedresults:
            1. Assert json output has all the exported template names
            and typewise

        :Requirement: Take Templates out of tech preview

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        imported_templates = entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'organization_id': org.id,
                'prefix': org.name
            })
        imported_count = [
            template['imported'] for template in imported_templates[
                'message']['templates']].count(True)
        self.assertEqual(imported_count, 16)  # Total Count
        # Export some filtered templates to local dir
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        exported_temps = entities.Template().exports(
            data={
                'repo': dir_path,
                'organization_ids': [org.id],
                'filter': org.name
            })
        self.assertEqual(len(exported_temps['message']['templates']), 16)
        self.assertIn('name', exported_temps['message']['templates'][0].keys())
        self.assertEqual(
            ssh.command(
                '[ -d {}/job_templates ]'.format(dir_path)
            ).return_code, 0)
        self.assertEqual(
            ssh.command(
                '[ -d {}/partition_tables_templates ]'.format(dir_path)
            ).return_code, 0)
        self.assertEqual(
            ssh.command(
                '[ -d {}/provisioning_templates ]'.format(dir_path)
            ).return_code, 0)

    @tier3
    def test_positive_import_log_to_production(self):
        """Assert template import logs are logged to production logs

        :id: 19ed0e6a-ee77-4e28-86c9-49db1adec479

        :Steps:
            1. Using nailgun or direct API call
               Import template from a source

        :expectedresults:
            1. Assert template import task and status logged to production log

        :Requirement: Take Templates out of tech preview

        :CaseLevel: System

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'organization_id': org.id,
                'filter': 'empty'
            })
        time.sleep(5)
        result = ssh.command(
            'grep -i \'Started POST "/api/v2/templates/import"\' '
            '/var/log/foreman/production.log')
        self.assertEqual(result.return_code, 0)

    @tier3
    def test_positive_export_log_to_production(self):
        """Assert template export logs are logged to production logs

        :id: 8ae370b1-84e8-436e-a7d7-99cd0b8f45b1

        :Steps:
            1. Using nailgun or direct API call
               Export template to destination

        :expectedresults:
            1. Assert template export task and status logged to production log

        :Requirement: Take Templates out of tech preview

        :CaseLevel: System

        :CaseImportance: Low
        """
        org = entities.Organization().create()
        entities.Template().imports(
            data={
                'repo': FOREMAN_TEMPLATE_IMPORT_URL,
                'branch': 'master',
                'organization_id': org.id,
                'filter': 'empty'
            })
        dir_name = gen_string('alpha')
        dir_path = self.create_import_export_local_directory(dir_name)
        entities.Template().exports(
            data={
                'repo': dir_path,
                'organization_ids': [org.id],
                'filter': 'empty'
            })
        time.sleep(5)
        result = ssh.command(
            'grep -i \'Started POST "/api/v2/templates/export"\' '
            '/var/log/foreman/production.log')
        self.assertEqual(result.return_code, 0)
