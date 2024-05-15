"""Test class for Provisioning Template UI

:Requirement: Provisioning Template

:CaseAutomation: Automated

:CaseComponent: ProvisioningTemplates

:Team: Rocket

:CaseImportance: High

"""

import pytest

from robottelo.constants import DataFile
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def template_data():
    return DataFile.OS_TEMPLATE_DATA_FILE.read_text()


@pytest.fixture
def clone_setup(target_sat, module_org, module_location):
    name = gen_string('alpha')
    content = gen_string('alpha')
    os_list = [target_sat.api.OperatingSystem().create().title for _ in range(2)]
    return {
        'pt': target_sat.api.ProvisioningTemplate(
            name=name,
            organization=[module_org],
            location=[module_location],
            template=content,
            snippet=False,
        ).create(),
        'os_list': os_list,
    }


@pytest.mark.tier2
def test_positive_clone(module_org, module_location, target_sat, clone_setup):
    """Assure ability to clone a provisioning template

    :id: 912f1619-4bb0-4e0f-88ce-88b5726fdbe0

    :steps:
        1.  Go to Provisioning template UI
        2.  Choose a template and attempt to clone it

    :expectedresults: The template is cloned
    """
    clone_name = gen_string('alpha')
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        session.provisioningtemplate.clone(
            clone_setup['pt'].name,
            {
                'template.name': clone_name,
                'association.applicable_os.assigned': clone_setup['os_list'],
            },
        )
        pt = target_sat.api.ProvisioningTemplate().search(query={'search': f'name=={clone_name}'})
        assigned_oses = [os.read() for os in pt[0].read().operatingsystem]
        assert pt, f'Template {clone_name} expected to exist but is not included in the search'
        assert set(clone_setup['os_list']) == {f'{os.name} {os.major}' for os in assigned_oses}


@pytest.mark.tier2
def test_positive_clone_locked(target_sat):
    """Assure ability to clone a locked provisioning template

    :id: 2df8550a-fe7d-405f-ab48-2896554cda12

    :steps:
        1.  Go to Provisioning template UI
        2.  Choose a locked provisioning template and attempt to clone it

    :expectedresults: The template is cloned
    """
    clone_name = gen_string('alpha')
    with target_sat.ui_session() as session:
        session.provisioningtemplate.clone(
            'Kickstart default',
            {
                'template.name': clone_name,
            },
        )
        assert target_sat.api.ProvisioningTemplate().search(
            query={'search': f'name=={clone_name}'}
        ), f'Template {clone_name} expected to exist but is not included in the search'


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.e2e
def test_positive_end_to_end(module_org, module_location, template_data, target_sat):
    """Perform end to end testing for provisioning template component

    :id: b44d4cc8-b78e-47cf-9993-0bb871ac2c96

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    os = target_sat.api.OperatingSystem().create()
    host_group = target_sat.api.HostGroup(
        organization=[module_org], location=[module_location]
    ).create()
    input_name = gen_string('alpha')
    variable_name = gen_string('alpha')
    template_input = [
        {
            'name': input_name,
            'required': True,
            'input_type': 'Variable',
            'input_content.variable_name': variable_name,
            'input_content.description': gen_string('alpha'),
        }
    ]
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        session.provisioningtemplate.create(
            {
                'template.name': name,
                'template.default': True,
                'template.template_editor.editor': template_data,
                'template.audit_comment': gen_string('alpha'),
                'inputs': template_input,
                'type.snippet': False,
                'type.template_type': 'iPXE template',
                'association.applicable_os.assigned': [os.title],
                'association.valid_hostgroups': [{'host_group': host_group.name}],
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        assert target_sat.api.ProvisioningTemplate().search(
            query={'search': f'name=={name}'}
        ), f'Provisioning template {name} expected to exist but is not included in the search'
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
        assert pt['association']['valid_hostgroups'][0]['host_group'] == host_group.name
        assert pt['locations']['resources']['assigned'][0] == module_location.name
        assert pt['organizations']['resources']['assigned'][0] == module_org.name
        session.provisioningtemplate.update(name, {'template.name': new_name, 'type.snippet': True})
        updated_pt = target_sat.api.ProvisioningTemplate().search(
            query={'search': f'name=={new_name}'}
        )
        assert (
            updated_pt
        ), f'Provisioning template {new_name} expected to exist but is not included in the search'
        updated_pt = updated_pt[0].read()
        assert updated_pt.snippet is True, 'Snippet attribute not updated for Provisioning Template'
        assert not updated_pt.template_kind, f'Snippet template is {updated_pt.template_kind}'
        session.provisioningtemplate.delete(new_name)
        assert not target_sat.api.ProvisioningTemplate().search(
            query={'search': f'name=={new_name}'}
        ), f'Provisioning template {new_name} expected to be removed but is included in the search'


@pytest.mark.tier2
def test_positive_verify_supported_templates_rhlogo(target_sat, module_org, module_location):
    """Verify presense of RH logo on supported provisioning template

    :id: 2df8550a-fe7d-405f-ab48-2896554cda14

    :steps:
        1.  Go to Provisioning template UI
        2.  Choose a any provisioning template and check if its supported or not

    :expectedresults: Supported templates will have the RH logo and not supported will have no logo.

    :BZ: 2211210, 2238346
    """
    template_name = '"Kickstart default"'
    pt = target_sat.api.ProvisioningTemplate().search(query={'search': f'name={template_name}'})[0]
    pt_clone = pt.clone(data={'name': f'{pt.name} {gen_string("alpha")}'})

    random_templates = {
        'ansible_provisioning_callback': {'supported': True, 'locked': True},
        pt.name: {'supported': True, 'locked': True},
        pt_clone['name']: {'supported': False, 'locked': False},
        'Windows default provision': {'supported': False, 'locked': True},
    }
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        for template in random_templates:
            assert (
                session.provisioningtemplate.is_locked(template)
                == random_templates[template]['locked']
            )
            assert (
                session.provisioningtemplate.is_supported(template)
                == random_templates[template]['supported']
            )
