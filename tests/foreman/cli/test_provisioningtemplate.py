"""Test class for Template CLI

:Requirement: Template

:CaseAutomation: Automated

:CaseComponent: ProvisioningTemplates

:Team: Rocket

:CaseImportance: High

"""

import random
from random import randint

from fauxfactory import gen_string
import pytest

from robottelo import constants
from robottelo.exceptions import CLIReturnCodeError


@pytest.fixture(scope='module')
def module_os_with_minor(module_target_sat):
    return module_target_sat.api.OperatingSystem(minor=randint(0, 10)).create()


@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_end_to_end_crud(
    module_org, module_location, module_os_with_minor, module_target_sat
):
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
    template = module_target_sat.cli_factory.make_template(
        {
            'name': name,
            'audit-comment': gen_string('alpha'),
            'description': gen_string('alpha'),
            'locked': 'no',
            'type': template_type,
            'operatingsystem-ids': module_os_with_minor.id,
            'organization-ids': module_org.id,
            'location-ids': module_location.id,
        }
    )
    assert template['name'] == name
    assert template['locked'] == 'no'
    assert template['type'] == template_type
    assert module_os_with_minor.title in template['operating-systems']
    assert module_org.name in template['organizations']
    assert module_location.name in template['locations']
    # list
    template_list = module_target_sat.cli.Template.list({'search': f'name={name}'})
    assert template_list[0]['name'] == name
    assert template_list[0]['type'] == template_type
    # update
    updated_pt = module_target_sat.cli.Template.update({'id': template['id'], 'name': new_name})
    template = module_target_sat.cli.Template.info({'id': updated_pt[0]['id']})
    assert new_name == template['name'], "The Provisioning template wasn't properly renamed"
    # clone
    template_clone = module_target_sat.cli.Template.clone(
        {'id': template['id'], 'new-name': cloned_template_name}
    )
    new_template = module_target_sat.cli.Template.info({'id': template_clone[0]['id']})
    assert new_template['name'] == cloned_template_name
    assert new_template['locked'] == template['locked']
    assert new_template['type'] == template['type']
    assert new_template['operating-systems'] == template['operating-systems']
    assert new_template['organizations'] == template['organizations']
    assert new_template['locations'] == template['locations']
    # delete
    module_target_sat.cli.Template.delete({'id': template['id']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Template.info({'id': template['id']})


@pytest.mark.tier1
@pytest.mark.parametrize('role_name', ['Manager', 'Organization admin'])
def test_positive_update_with_role(module_target_sat, module_location, module_org, role_name):
    """Create template providing the initial name, then update its name
    with manager/organization admin user roles.

    :id: 28c4357a-93cb-4b01-a445-5db50435bcc0

    :expectedresults: Provisioning Template is created, and its name can
        be updated.

    :CaseImportance: Medium

    :BZ: 1277308

    :parametrized: yes
    """
    new_name = gen_string('alpha')
    username = gen_string('alpha')
    password = gen_string('alpha')
    template = module_target_sat.cli_factory.make_template(
        {'organization-ids': module_org.id, 'location-ids': module_location.id}
    )
    # Create user with Manager/Organization admin role
    user = module_target_sat.api.User(
        login=username,
        password=password,
        admin=False,
        organization=[module_org.id],
        location=[module_location.id],
    ).create()
    module_target_sat.cli.User.add_role({'id': user.id, 'role': role_name})
    # Update template name with that user
    module_target_sat.cli.Template.with_user(username=username, password=password).update(
        {'id': template['id'], 'name': new_name}
    )
    template = module_target_sat.cli.Template.info({'id': template['id']})
    assert new_name == template['name']


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_locked(module_target_sat):
    """Check that locked Template can be created

    :id: ff10e369-85c6-45f3-9cda-7e1c17a6632d

    :expectedresults: The locked template is created successfully


    :CaseImportance: Medium
    """
    new_template = module_target_sat.cli_factory.make_template(
        {'locked': 'true', 'name': gen_string('alpha')}
    )
    assert new_template['locked'] == 'yes'


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_add_remove_os_by_id(module_target_sat, module_os_with_minor):
    """Check if operating system can be added and removed to a template

    :id: d9f481b3-9757-4208-b451-baf4792d4d70

    :expectedresults: Operating system is added/removed from the template
    """
    os = module_os_with_minor
    os_string = f'{os.name} {os.major}.{os.minor}'
    new_template = module_target_sat.cli_factory.make_template()
    module_target_sat.cli.Template.add_operatingsystem(
        {'id': new_template['id'], 'operatingsystem-id': os.id}
    )
    new_template = module_target_sat.cli.Template.info({'id': new_template['id']})
    assert os_string in new_template['operating-systems']
    module_target_sat.cli.Template.remove_operatingsystem(
        {'id': new_template['id'], 'operatingsystem-id': os.id}
    )
    new_template = module_target_sat.cli.Template.info({'id': new_template['id']})
    assert os_string not in new_template['operating-systems']


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_with_content(module_target_sat):
    """Check if Template can be created with specific content

    :id: 0fcfc46d-5e97-4451-936a-e8684acac275

    :expectedresults: Template is created with specific content

    :CaseImportance: Critical
    """
    content = gen_string('alpha')
    name = gen_string('alpha')
    template = module_target_sat.cli_factory.make_template({'content': content, 'name': name})
    assert template['name'] == name
    template_content = module_target_sat.cli.Template.dump({'id': template['id']})
    assert content in template_content


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_clone(module_target_sat):
    """Assure ability to clone a provisioning template

    :id: 27d69c1e-0d83-4b99-8a3c-4f1bdec3d261

    :expectedresults: The template is cloned successfully
    """
    cloned_template_name = gen_string('alpha')
    template = module_target_sat.cli_factory.make_template()
    result = module_target_sat.cli.Template.clone(
        {'id': template['id'], 'new-name': cloned_template_name}
    )
    new_template = module_target_sat.cli.Template.info({'id': result[0]['id']})
    assert new_template['name'] == cloned_template_name
