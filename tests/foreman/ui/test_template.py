# -*- encoding: utf-8 -*-
"""Test class for Template UI

:Requirement: Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import OS_TEMPLATE_DATA_FILE, SNIPPET_DATA_FILE
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import stubbed, tier1, upgrade
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_templates, set_context
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session

OS_TEMPLATE_DATA_FILE = get_data_file(OS_TEMPLATE_DATA_FILE)
SNIPPET_DATA_FILE = get_data_file(SNIPPET_DATA_FILE)


class TemplateTestCase(UITestCase):
    """Implements Provisioning Template tests from UI"""

    @classmethod
    def setUpClass(cls):
        super(TemplateTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.loc = entities.Location().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create new template using different valid names

        :id: 12767d13-2531-4a3c-9527-3191bc9a1149

        :expectedresults: New template of type 'Provisioning template' should
            be created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_templates(
                        session,
                        name=name,
                        template_path=OS_TEMPLATE_DATA_FILE,
                        custom_really=True,
                        template_type='Provisioning template',
                    )
                    self.assertIsNotNone(self.template.search(name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create a new template with invalid names

        :id: cfbc8e10-96b3-425c-ac21-f995a8b038e8

        :expectedresults: Template is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_templates(
                        session,
                        name=name,
                        template_path=OS_TEMPLATE_DATA_FILE,
                        custom_really=True,
                        template_type='Provisioning template',
                    )
                    self.assertIsNotNone(self.template.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    def test_negative_create_with_same_name(self):
        """Template - Create a new template with same name

        :id: 52382553-2708-47d0-97b2-fce6ddb366ad

        :expectedresults: Template is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_templates(
                session,
                name=name,
                template_path=OS_TEMPLATE_DATA_FILE,
                custom_really=True,
                template_type='Provisioning template',
            )
            self.assertIsNotNone(self.template.search(name))
            make_templates(
                session,
                name=name,
                template_path=OS_TEMPLATE_DATA_FILE,
                custom_really=True,
                template_type='Provisioning template',
            )
            self.assertIsNotNone(self.template.wait_until_element(
                common_locators['name_haserror']))

    @tier1
    def test_negative_create_without_type(self):
        """Template - Create a new template without selecting its type

        :id: 370af6a5-0814-4474-b758-46ec25ccbc4a

        :expectedresults: Template is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            with self.assertRaises(UIError) as context:
                make_templates(
                    session,
                    name=name,
                    template_path=OS_TEMPLATE_DATA_FILE,
                    custom_really=True,
                    template_type='',
                )
            self.assertEqual(
                str(context.exception),
                'Could not create template "{0}" without type'.format(name)
            )

    @tier1
    def test_negative_create_without_upload(self):
        """Template - Create a new template without uploading a template

        :id: dd4bb3cb-a7a0-46fa-bc16-e2d117ce79d8

        :expectedresults: Template is not created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            with self.assertRaises(UIError) as context:
                make_templates(
                    session,
                    name=name,
                    template_path='',
                    custom_really=True,
                    template_type='PXELinux template',
                )
            self.assertEqual(
                str(context.exception),
                'Could not create blank template "{0}"'.format(name)
            )

    @tier1
    def test_negative_create_with_too_long_audit(self):
        """Create a new template with 256 characters in audit comments

        :id: 62b06765-f9d5-4e69-967f-76f2649f83ff

        :expectedresults: Template is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_templates(
                session,
                name=gen_string('alpha', 16),
                template_path=OS_TEMPLATE_DATA_FILE,
                custom_really=True,
                audit_comment=gen_string('alpha', 256),
                template_type='PXELinux template',
            )
            self.assertIsNotNone(self.template.wait_until_element(
                common_locators['haserror']))

    @tier1
    def test_positive_create_with_snippet_type(self):
        """Create new template of type snippet

        :id: 56f62153-6dd2-4120-9f23-386442f643c4

        :expectedresults: New provisioning template of type 'snippet' should be
            created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_templates(
                        session,
                        name=name,
                        template_path=SNIPPET_DATA_FILE,
                        custom_really=True,
                        snippet=True,
                    )
                    self.assertIsNotNone(self.template.search(name))

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete an existing template

        :id: e4a687e5-6581-4481-ad9b-8d2ac3f2c9d5

        :expectedresults: Template is deleted successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            for template_name in generate_strings_list():
                with self.subTest(template_name):
                    entities.ConfigTemplate(
                        name=template_name,
                        organization=[self.organization],
                    ).create()
                    self.template.delete(template_name, dropdown_present=True)

    @tier1
    @upgrade
    def test_positive_update_name_and_type(self):
        """Update template name and template type

        :id: f1a7d44d-5ac8-47e1-9084-ce8f166dbde5

        :expectedresults: The template name and type should be updated
            successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        with Session(self) as session:
            make_templates(
                session,
                name=name,
                template_path=OS_TEMPLATE_DATA_FILE,
                custom_really=True,
                template_type='Provisioning template',
            )
            self.assertIsNotNone(self.template.search(name))
            self.template.update(
                name, False, new_name, None, 'PXELinux template')
            self.assertIsNotNone(self.template.search(new_name))

    @tier1
    def test_positive_update_os(self):
        """Creates new template, along with two OS's and associate list
        of OS's with created template

        :id: 160d7906-dd60-4870-8ca0-dde61ccab67c

        :expectedresults: The template should be updated with newly created
            OS's successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        os_list = [
            entities.OperatingSystem().create().name for _ in range(2)
        ]
        with Session(self) as session:
            make_templates(
                session,
                name=name,
                template_path=OS_TEMPLATE_DATA_FILE,
                custom_really=True,
                template_type='Provisioning template',
            )
            self.assertIsNotNone(self.template.search(name))
            self.template.update(name, False, new_name, new_os_list=os_list)
            self.assertIsNotNone(self.template.search(new_name))

    @tier1
    def test_positive_update_with_manager_role(self):
        """Create template providing the initial name, then update its name
        with manager user role.

        :id: 463790a2-c384-4851-99d2-78777762b6df

        :expectedresults: Provisioning Template is created, and its name can
            be updated.

        :CaseImportance: Critical

        :BZ: 1277308
        """
        new_name = gen_string('alpha')
        user_login = gen_string('alpha')
        user_password = gen_string('alpha')
        template = entities.ProvisioningTemplate(
            organization=[self.organization],
            location=[self.loc]
        ).create()
        # Create user with Manager role
        role = entities.Role().search(query={'search': 'name="Manager"'})[0]
        entities.User(
            role=[role],
            admin=False,
            login=user_login,
            password=user_password,
            organization=[self.organization],
            default_organization=self.organization,
            location=[self.loc],
        ).create()
        with Session(self, user=user_login, password=user_password):
            self.template.update(name=template.name, new_name=new_name)
            self.assertIsNotNone(self.template.search(new_name))

    @tier1
    def test_positive_advanced_search(self):
        """Create new provisioning template and associate it with specific
        organization and location. Also associate it with new hostgroup.
        Afterwards search for that template by hostgroup

        :id: 5bcecd40-28af-4913-92a4-863c8dc05ecc

        :BZ: 1386334

        :expectedresults: Template can be found successfully and no error is
            raised

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        loc = entities.Location().create()
        hostgroup = entities.HostGroup(
            organization=[org], location=[loc]).create()
        template_name = gen_string('alpha')
        with Session(self) as session:
            set_context(session, org=org.name, loc=loc.name)
            make_templates(
                session,
                name=template_name,
                template_path=OS_TEMPLATE_DATA_FILE,
                custom_really=True,
                template_type='Provisioning template',
                hostgroup=hostgroup.name,
            )
            self.assertIsNotNone(self.template.search(template_name))
            self.assertIsNotNone(
                self.template.search(
                    template_name,
                    _raw_query='hostgroup = {}'.format(hostgroup.name)
                )
            )

    @stubbed()
    @tier1
    def test_positive_export_unlocked(self):
        """Assure ability to export a unlocked template

        :id: 178c3583-1724-4eb0-ae5d-699368d4d8c2

        :Steps:
            1. Go to Provisioning template UI
            2. Choose an unlocked template and attempt to export it.

        :expectedresults: The template is exported successfully.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_export_locked(self):
        """Assure ability to export a locked template

        :id: c044ffb2-5928-4415-9332-28d6b9eeb634

        :Steps:
            1. Go to Provisioning template UI
            2. Choose a locked template and attempt to export it.

        :expectedresults: The template is exported successfully.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_display_help(self):
        """Assure template screen shows a Help Tab

        :id: 6ec548d9-da98-4649-861a-22e4b23bdb48

        :Steps:
            1. Go to Provisioning template UI
            2. Choose a template and click the Help Tab

        :expectedresults: The template Help should be shown.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_display_cloned_help(self):
        """Assure cloned template screen shows a Help Tab

        :id: e24650fe-68d9-4752-bd13-977cb09e7009

        :Steps:
            1. Go to Provisioning template UI
            2. Choose a template, clone it and click the Help Tab.

        :expectedresults: The cloned template Help should be shown.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_export_cloned_and_edited(self):
        """Assure cloned and edited template can be exported.

        :id: 93e0ebe4-fa00-4251-8429-ee85ff67b444

        :Steps:
            1. Go to Provisioning template UI
            2. Choose a template, clone it, edit it and export it.

        :expectedresults: The cloned and edited template can be exported
                          successfully.

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_export_template_disable_safe_render(self):
        """Assure templates can be exported after disabling safe render.

        :id: c4c05c13-1ea3-4963-b2dc-ec826b77c9cb

        :Steps:
            1. Go to Provisioning template UI
            2. Set Safe mode Rendering to No, from settings.
            3. The template is exported successfully.

        :expectedresults: The templates can be exported successfully
                          even after disabling safe render option.

        :CaseImportance: Critical
        """


class TemplateSyncTestCase(UITestCase):
    """Implements TemplateSync tests from UI"""

    @classmethod
    def setUpClass(cls):
        """Setup for TemplateSync functionality

        :steps:

            1. Git repository must exist (in gitlab or github) and its url
               set in ssh:// form in robottelo.constants.
               (note: git@git... form does not work, should start with ssh://)
            2. SSH key must be set to `foreman` user to access that git host
               via ssh://.
            3. Local directory /var/tmp/templatesync-{random}/ must be created.
            4. Organization and Location must be created to isolate the
               templates ownership.
        """

    @stubbed()
    @tier1
    def test_positive_settings_is_enabled(self):
        """Assure foremen-template plugin is enabled by asserting the
        Template Sync tab shows under UI Administer - > Settings.

        :id: d140c3eb-e1ef-4737-9ccd-a964d3e93639

        :Steps:
            1. Go to Administer -> Setttings

        :expectedresults:
            1. Assert "Template Sync" tab is present

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_git_settings(self):
        """Assure git configuration can be set on UI.

        :id: b9a43550-9c5a-4af7-a763-146622af7e61

        :Steps:
            1. Go to Administer -> Setttings
            2. Click Template-Sync tab
            3. Configure git settings for fields:
               branch -> develop
               repo -> e.g: ssh://git@github.com/username/community-templates
               prefix - > robottelo (or something else easy to test)

        :expectedresults:
            1. Assert settings are successfully saved after a refresh

        :CaseImportance: Critical
        """
