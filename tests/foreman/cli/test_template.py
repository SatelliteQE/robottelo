# -*- encoding: utf-8 -*-
"""Test class for Template CLI

:Requirement: Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ProvisioningTemplates

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_template
from robottelo.cli.factory import make_user
from robottelo.cli.template import Template
from robottelo.cli.user import User
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class TemplateTestCase(CLITestCase):
    """Test class for Config Template CLI."""

    @tier1
    def test_positive_create_with_name(self):
        """Check if Template can be created

        :id: 77deaae8-447b-47cc-8af3-8b17476c905f

        :expectedresults: Template is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        template = make_template({'name': name})
        self.assertEqual(template['name'], name)

    @tier1
    def test_positive_update_name(self):
        """Check if Template can be updated

        :id: 99bdab7b-1279-4349-a655-4294395ecbe1

        :expectedresults: Template is updated

        :CaseImportance: Critical
        """
        template = make_template()
        updated_name = gen_string('alpha')
        Template.update({'id': template['id'], 'name': updated_name})
        template = Template.info({'id': template['id']})
        self.assertEqual(updated_name, template['name'])

    @tier1
    def test_positive_update_with_manager_role(self):
        """Create template providing the initial name, then update its name
        with manager user role.

        :id: 28c4357a-93cb-4b01-a445-5db50435bcc0

        :expectedresults: Provisioning Template is created, and its name can
            be updated.

        :CaseImportance: Medium

        :BZ: 1277308
        """
        new_name = gen_string('alpha')
        username = gen_string('alpha')
        password = gen_string('alpha')
        org = make_org()
        loc = make_location()
        template = make_template({'organization-ids': org['id'], 'location-ids': loc['id']})
        # Create user with Manager role
        user = make_user(
            {
                'login': username,
                'password': password,
                'admin': False,
                'organization-ids': org['id'],
                'location-ids': loc['id'],
            }
        )
        User.add_role({'id': user['id'], 'role': "Manager"})
        # Update template name with that user
        Template.with_user(username=username, password=password).update(
            {'id': template['id'], 'name': new_name}
        )
        template = Template.info({'id': template['id']})
        self.assertEqual(new_name, template['name'])

    @tier1
    def test_positive_create_with_loc(self):
        """Check if Template with Location can be created

        :id: 263aba0e-4f54-4227-af97-f4bc8f5c0788

        :expectedresults: Template is created and new Location has been
            assigned

        :CaseImportance: Medium
        """
        new_loc = make_location()
        new_template = make_template({'location-ids': new_loc['id']})
        self.assertIn(new_loc['name'], new_template['locations'])

    @tier1
    def test_positive_create_locked(self):
        """Check that locked Template can be created

        :id: ff10e369-85c6-45f3-9cda-7e1c17a6632d

        :expectedresults: The locked template is created successfully


        :CaseImportance: Medium
        """
        new_template = make_template({'locked': 'true', 'name': gen_string('alpha')})
        self.assertEqual(new_template['locked'], 'yes')

    @tier2
    def test_positive_create_with_org(self):
        """Check if Template with Organization can be created

        :id: 5de5ca76-1a39-46ac-8dd4-5d41b4b49076

        :expectedresults: Template is created and new Organization has been
            assigned

        :CaseImportance: Medium
        """
        new_org = make_org()
        new_template = make_template(
            {'name': gen_string('alpha'), 'organization-ids': new_org['id']}
        )
        self.assertIn(new_org['name'], new_template['organizations'])

    @tier2
    @upgrade
    def test_positive_add_os_by_id(self):
        """Check if operating system can be added to a template

        :id: d9f481b3-9757-4208-b451-baf4792d4d70

        :expectedresults: Operating system is added to the template

        :CaseLevel: Integration
        """
        new_template = make_template()
        new_os = make_os()
        Template.add_operatingsystem(
            {'id': new_template['id'], 'operatingsystem-id': new_os['id']}
        )
        new_template = Template.info({'id': new_template['id']})
        os_string = '{0} {1}.{2}'.format(
            new_os['name'], new_os['major-version'], new_os['minor-version']
        )
        self.assertIn(os_string, new_template['operating-systems'])

    @tier2
    def test_positive_remove_os_by_id(self):
        """Check if operating system can be removed from a template

        :id: b5362565-6dce-4770-81e1-4fe3ec6f6cee

        :expectedresults: Operating system is removed from template

        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 1395229
        """
        template = make_template()
        new_os = make_os()
        Template.add_operatingsystem({'id': template['id'], 'operatingsystem-id': new_os['id']})
        template = Template.info({'id': template['id']})
        os_string = '{0} {1}.{2}'.format(
            new_os['name'], new_os['major-version'], new_os['minor-version']
        )
        self.assertIn(os_string, template['operating-systems'])
        Template.remove_operatingsystem({'id': template['id'], 'operatingsystem-id': new_os['id']})
        template = Template.info({'id': template['id']})
        self.assertNotIn(os_string, template['operating-systems'])

    @tier1
    @upgrade
    def test_positive_create_with_content(self):
        """Check if Template can be created with specific content

        :id: 0fcfc46d-5e97-4451-936a-e8684acac275

        :expectedresults: Template is created with specific content

        :CaseImportance: Critical
        """
        content = gen_string('alpha')
        name = gen_string('alpha')
        template = make_template({'content': content, 'name': name})
        self.assertEqual(template['name'], name)
        template_content = Template.dump({'id': template['id']})
        self.assertIn(content, template_content[0])

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Check if Template can be deleted

        :id: 8e5245ee-13dd-44d4-8111-d4382cacf005

        :expectedresults: Template is deleted

        :CaseImportance: Critical
        """
        template = make_template()
        Template.delete({'id': template['id']})
        with self.assertRaises(CLIReturnCodeError):
            Template.info({'id': template['id']})

    @tier2
    @upgrade
    def test_positive_clone(self):
        """Assure ability to clone a provisioning template

        :id: 27d69c1e-0d83-4b99-8a3c-4f1bdec3d261

        :expectedresults: The template is cloned successfully

        :CaseLevel: Integration
        """
        cloned_template_name = gen_string('alpha')
        template = make_template()
        result = Template.clone({'id': template['id'], 'new-name': cloned_template_name})
        new_template = Template.info({'id': result[0]['id']})
        self.assertEqual(new_template['name'], cloned_template_name)
