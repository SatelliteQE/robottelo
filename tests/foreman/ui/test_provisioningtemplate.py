"""Test class for Provisioning Template UI

:Requirement: Provisioning Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.constants import OS_TEMPLATE_DATA_FILE
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade
from robottelo.helpers import read_data_file


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@fixture(scope='module')
def template_data():
    return read_data_file(OS_TEMPLATE_DATA_FILE)


@tier2
def test_positive_clone(session):
    """Assure ability to clone a provisioning template

    :id: 912f1619-4bb0-4e0f-88ce-88b5726fdbe0

    :Steps:
        1.  Go to Provisioning template UI
        2.  Choose a template and attempt to clone it

    :expectedresults: The template is cloned

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    clone_name = gen_string('alpha')
    content = gen_string('alpha')
    os_list = [
        entities.OperatingSystem().create().title for _ in range(2)
    ]
    with session:
        session.provisioningtemplate.create({
            'template.name': name,
            'template.template_editor.editor': content,
            'type.template_type': 'Provisioning template'
        })
        assert session.provisioningtemplate.search(name)[0]['Name'] == name
        session.provisioningtemplate.clone(
            name,
            {
                'template.name': clone_name,
                'association.applicable_os.assigned': os_list
            }
        )
        assert session.provisioningtemplate.search(
            clone_name)[0]['Name'] == clone_name
        template = session.provisioningtemplate.read(clone_name)
        assert set(os_list) == set(
            template['association']['applicable_os']['assigned'])


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc, template_data):
    """Perform end to end testing for provisioning template component

    :id: b44d4cc8-b78e-47cf-9993-0bb871ac2c96

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    os = entities.OperatingSystem().create()
    host_group = entities.HostGroup(
        organization=[module_org], location=[module_loc]).create()
    environment = entities.Environment(
        organization=[module_org], location=[module_loc]).create()
    input_name = gen_string('alpha')
    variable_name = gen_string('alpha')
    template_input = [{
        'name': input_name,
        'required': True,
        'input_type': 'Variable',
        'input_content.variable_name': variable_name,
        'input_content.description': gen_string('alpha')
    }]
    combination = [{
        'host_group': host_group.name, 'environment': environment.name}]
    with session:
        session.provisioningtemplate.create({
            'template.name': name,
            'template.default': True,
            'template.template_editor.editor': template_data,
            'template.audit_comment': gen_string('alpha'),
            'inputs': template_input,
            'type.snippet': False,
            'type.template_type': 'iPXE template',
            'association.applicable_os.assigned': [os.title],
            'association.hg_environment_combination': combination,
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        assert session.provisioningtemplate.search(name)[0]['Name'] == name
        pt = session.provisioningtemplate.read(name)
        assert pt['template']['name'] == name
        assert pt['template']['default'] is True
        assert pt['template']['template_editor']['editor'] == template_data
        assert pt['inputs'][0]['name'] == input_name
        assert pt['inputs'][0]['required'] is True
        assert pt['inputs'][0]['input_type'] == 'Variable'
        assert pt['inputs'][0]['input_content']['variable_name'] == variable_name
        assert pt['type']['snippet'] is False
        assert pt['type']['template_type'] == 'iPXE template'
        assert pt['association']['applicable_os']['assigned'][0] == os.title
        assert pt[
            'association']['hg_environment_combination'][0]['host_group'] == host_group.name
        assert pt[
            'association']['hg_environment_combination'][0]['environment'] == environment.name
        assert pt['locations']['resources']['assigned'][0] == module_loc.name
        assert pt['organizations']['resources']['assigned'][0] == module_org.name
        session.provisioningtemplate.update(
            name,
            {'template.name': new_name, 'type.snippet': True}
        )
        assert session.provisioningtemplate.search(new_name)[0]['Name'] == new_name
        updated_pt = session.provisioningtemplate.read(new_name)
        assert updated_pt['type']['snippet'] is True
        assert not updated_pt['type']['template_type']
        session.provisioningtemplate.delete(new_name)
        assert not session.provisioningtemplate.search(new_name)
