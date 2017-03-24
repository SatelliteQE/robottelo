# -*- encoding: utf-8 -*-
"""Test class for Template UI

@Requirement: Template

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import OS_TEMPLATE_DATA_FILE, SNIPPET_DATA_FILE
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1, tier2
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

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new template using different valid names

        @id: 12767d13-2531-4a3c-9527-3191bc9a1149

        @expectedresults: New template of type 'Provisioning template' should
        be created successfully
        """
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create a new template with invalid names

        @id: cfbc8e10-96b3-425c-ac21-f995a8b038e8

        @expectedresults: Template is not created
        """
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Template - Create a new template with same name

        @id: 52382553-2708-47d0-97b2-fce6ddb366ad

        @expectedresults: Template is not created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_negative_create_without_type(self):
        """Template - Create a new template without selecting its type

        @id: 370af6a5-0814-4474-b758-46ec25ccbc4a

        @expectedresults: Template is not created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            with self.assertRaises(UIError) as context:
                make_templates(
                    session,
                    name=name,
                    template_path=OS_TEMPLATE_DATA_FILE,
                    custom_really=True,
                    template_type='',
                )
                self.assertEqual(
                    context.exception.message,
                    'Could not create template "{0}" without type'.format(name)
                )

    @run_only_on('sat')
    @tier1
    def test_negative_create_without_upload(self):
        """Template - Create a new template without uploading a template

        @id: dd4bb3cb-a7a0-46fa-bc16-e2d117ce79d8

        @expectedresults: Template is not created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            with self.assertRaises(UIError) as context:
                make_templates(
                    session,
                    name=name,
                    template_path='',
                    custom_really=True,
                    template_type='PXELinux template',
                )
                self.assertEqual(
                    context.exception.message,
                    'Could not create blank template "{0}"'.format(name)
                )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_too_long_audit(self):
        """Create a new template with 256 characters in audit comments

        @id: 62b06765-f9d5-4e69-967f-76f2649f83ff

        @expectedresults: Template is not created
        """
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_snippet_type(self):
        """Create new template of type snippet

        @id: 56f62153-6dd2-4120-9f23-386442f643c4

        @expectedresults: New provisioning template of type 'snippet' should be
        created successfully
        """
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete an existing template

        @id: e4a687e5-6581-4481-ad9b-8d2ac3f2c9d5

        @expectedresults: Template is deleted successfully
        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            for template_name in generate_strings_list():
                with self.subTest(template_name):
                    entities.ConfigTemplate(
                        name=template_name,
                        organization=[self.organization],
                    ).create()
                    self.template.delete(template_name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name_and_type(self):
        """Update template name and template type

        @id: f1a7d44d-5ac8-47e1-9084-ce8f166dbde5

        @expectedresults: The template name and type should be updated
        successfully
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_update_os(self):
        """Creates new template, along with two OS's and associate list
        of OS's with created template

        @id: 160d7906-dd60-4870-8ca0-dde61ccab67c

        @expectedresults: The template should be updated with newly created
        OS's successfully
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        os_list = [
            entities.OperatingSystem().create().name for _ in range(2)
        ]
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier2
    def test_positive_clone(self):
        """Assure ability to clone a provisioning template

        @id: 912f1619-4bb0-4e0f-88ce-88b5726fdbe0

        @Steps:
         1.  Go to Provisioning template UI
         2.  Choose a template and attempt to clone it

        @expectedresults: The template is cloned

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        clone_name = gen_string('alpha')
        os_list = [
            entities.OperatingSystem().create().name for _ in range(2)
        ]
        with Session(self.browser) as session:
            make_templates(
                session,
                name=name,
                template_path=OS_TEMPLATE_DATA_FILE,
                custom_really=True,
                template_type='Provisioning template',
            )
            self.assertIsNotNone(self.template.search(name))
            self.template.clone(
                name,
                custom_really=False,
                clone_name=clone_name,
                os_list=os_list,
            )
            self.assertIsNotNone(self.template.search(clone_name))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1386334)
    @tier1
    def test_positive_advanced_search(self):
        """Create new provisioning template and associate it with specific
        organization and location. Also associate it with new hostgroup.
        Afterwards search for that template by hostgroup

        @id: 5bcecd40-28af-4913-92a4-863c8dc05ecc

        @BZ: 1386334

        @expectedresults: Template can be found successfully and no error is
        raised
        """
        org = entities.Organization().create()
        loc = entities.Location().create()
        hostgroup = entities.HostGroup(
            organization=[org], location=[loc]).create()
        template_name = gen_string('alpha')
        with Session(self.browser) as session:
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
