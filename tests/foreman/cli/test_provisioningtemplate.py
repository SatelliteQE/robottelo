"""Test class for Template CLI

:Requirement: Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ProvisioningTemplates

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
from random import randint

import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo import constants
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_template
from robottelo.cli.template import Template
from robottelo.cli.user import User


@pytest.fixture(scope='module')
def module_os_with_minor():
    return entities.OperatingSystem(minor=randint(0, 10)).create()


@pytest.mark.e2e
def test_positive_end_to_end_crud(module_org, module_location, module_os, target_sat):
    """Create a new provisioning template with several attributes, list, update them,
       clone the provisioning template and then delete it

    :id: 5f2e487c-07a5-423d-98ce-92ef1ad3b08d

    :steps:
        1. Create a provisioning template with several attributes.
        2. Assert if all attributes are associated with the created template.
        3. List the template.
        4. Update the template and assert if it is properly updated.
        5. Clone the template.
        6. Assert if the cloned template contains all the attributes of parent template.
        7. Delete the template.

    :expectedresults: Template is created with all the given attributes, listed, updated,
                      cloned and deleted.
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    cloned_template_name = gen_string('alpha')
    template_type = random.choice(constants.TEMPLATE_TYPES)
    # create
    template = target_sat.cli_factory.make_template(
        {
            'name': name,
            'audit-comment': gen_string('alpha'),
            'description': gen_string('alpha'),
            'locked': 'no',
            'type': template_type,
            'operatingsystem-ids': module_os.id,
            'organization-ids': module_org.id,
            'location-ids': module_location.id,
        }
    )
    assert template['name'] == name
    assert template['locked'] == 'no'
    assert template['type'] == template_type
    assert module_os.title in template['operating-systems']
    assert module_org.name in template['organizations']
    assert module_location.name in template['locations']
    # list
    template_list = target_sat.cli.Template.list({'search': f'name={name}'})
    assert template_list[0]['name'] == name
    assert template_list[0]['type'] == template_type
    # update
    updated_pt = target_sat.cli.Template.update({'id': template['id'], 'name': new_name})
    template = target_sat.cli.Template.info({'id': updated_pt[0]['id']})
    assert new_name == template['name'], "The Provisioning template wasn't properly renamed"
    # clone
    template_clone = target_sat.cli.Template.clone(
        {'id': template['id'], 'new-name': cloned_template_name}
    )
    new_template = target_sat.cli.Template.info({'id': template_clone[0]['id']})
    assert new_template['name'] == cloned_template_name
    assert new_template['locked'] == template['locked']
    assert new_template['type'] == template['type']
    assert new_template['operating-systems'] == template['operating-systems']
    assert new_template['organizations'] == template['organizations']
    assert new_template['locations'] == template['locations']
    # delete
    target_sat.cli.Template.delete({'id': template['id']})
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Template.info({'id': template['id']})


@pytest.mark.tier1
def test_positive_create_with_name():
    """Check if Template can be created

    :id: 77deaae8-447b-47cc-8af3-8b17476c905f

    :expectedresults: Template is created

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    template = make_template({'name': name})
    assert template['name'] == name


@pytest.mark.tier1
def test_positive_update_name():
    """Check if Template can be updated

    :id: 99bdab7b-1279-4349-a655-4294395ecbe1

    :expectedresults: Template is updated

    :CaseImportance: Critical
    """
    template = make_template()
    updated_name = gen_string('alpha')
    Template.update({'id': template['id'], 'name': updated_name})
    template = Template.info({'id': template['id']})
    assert updated_name == template['name']


@pytest.mark.tier1
def test_positive_update_with_manager_role(module_location, module_org):
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
    template = make_template(
        {'organization-ids': module_org.id, 'location-ids': module_location.id}
    )
    # Create user with Manager role
    user = entities.User(
        login=username,
        password=password,
        admin=False,
        organization=[module_org.id],
        location=[module_location.id],
    ).create()
    User.add_role({'id': user.id, 'role': "Manager"})
    # Update template name with that user
    Template.with_user(username=username, password=password).update(
        {'id': template['id'], 'name': new_name}
    )
    template = Template.info({'id': template['id']})
    assert new_name == template['name']


@pytest.mark.tier1
def test_positive_create_with_loc(module_location):
    """Check if Template with Location can be created

    :id: 263aba0e-4f54-4227-af97-f4bc8f5c0788

    :expectedresults: Template is created and new Location has been
        assigned

    :CaseImportance: Medium
    """
    new_template = make_template({'location-ids': module_location.id})
    assert module_location.name in new_template['locations']


@pytest.mark.tier1
def test_positive_create_locked():
    """Check that locked Template can be created

    :id: ff10e369-85c6-45f3-9cda-7e1c17a6632d

    :expectedresults: The locked template is created successfully


    :CaseImportance: Medium
    """
    new_template = make_template({'locked': 'true', 'name': gen_string('alpha')})
    assert new_template['locked'] == 'yes'


@pytest.mark.tier2
def test_positive_create_with_org(module_org):
    """Check if Template with Organization can be created

    :id: 5de5ca76-1a39-46ac-8dd4-5d41b4b49076

    :expectedresults: Template is created and new Organization has been
        assigned

    :CaseImportance: Medium
    """
    new_template = make_template({'name': gen_string('alpha'), 'organization-ids': module_org.id})
    assert module_org.name in new_template['organizations']


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_add_os_by_id(module_os_with_minor):
    """Check if operating system can be added to a template

    :id: d9f481b3-9757-4208-b451-baf4792d4d70

    :expectedresults: Operating system is added to the template

    :CaseLevel: Integration
    """
    new_template = make_template()
    Template.add_operatingsystem(
        {'id': new_template['id'], 'operatingsystem-id': module_os_with_minor.id}
    )
    new_template = Template.info({'id': new_template['id']})
    os_string = (
        f'{module_os_with_minor.name} {module_os_with_minor.major}.{module_os_with_minor.minor}'
    )
    assert os_string in new_template['operating-systems']


@pytest.mark.tier2
def test_positive_remove_os_by_id(module_os_with_minor):
    """Check if operating system can be removed from a template

    :id: b5362565-6dce-4770-81e1-4fe3ec6f6cee

    :expectedresults: Operating system is removed from template

    :CaseLevel: Integration

    :CaseImportance: Medium

    :BZ: 1395229
    """
    template = make_template()
    Template.add_operatingsystem(
        {'id': template['id'], 'operatingsystem-id': module_os_with_minor.id}
    )
    template = Template.info({'id': template['id']})
    os_string = (
        f'{module_os_with_minor.name} {module_os_with_minor.major}.{module_os_with_minor.minor}'
    )
    assert os_string in template['operating-systems']
    Template.remove_operatingsystem(
        {'id': template['id'], 'operatingsystem-id': module_os_with_minor.id}
    )
    template = Template.info({'id': template['id']})
    assert os_string not in template['operating-systems']


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_with_content():
    """Check if Template can be created with specific content

    :id: 0fcfc46d-5e97-4451-936a-e8684acac275

    :expectedresults: Template is created with specific content

    :CaseImportance: Critical
    """
    content = gen_string('alpha')
    name = gen_string('alpha')
    template = make_template({'content': content, 'name': name})
    assert template['name'] == name
    template_content = Template.dump({'id': template['id']})
    assert content in template_content


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_by_id():
    """Check if Template can be deleted

    :id: 8e5245ee-13dd-44d4-8111-d4382cacf005

    :expectedresults: Template is deleted

    :CaseImportance: Critical
    """
    template = make_template()
    Template.delete({'id': template['id']})
    with pytest.raises(CLIReturnCodeError):
        Template.info({'id': template['id']})


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_clone():
    """Assure ability to clone a provisioning template

    :id: 27d69c1e-0d83-4b99-8a3c-4f1bdec3d261

    :expectedresults: The template is cloned successfully

    :CaseLevel: Integration
    """
    cloned_template_name = gen_string('alpha')
    template = make_template()
    result = Template.clone({'id': template['id'], 'new-name': cloned_template_name})
    new_template = Template.info({'id': result[0]['id']})
    assert new_template['name'] == cloned_template_name
