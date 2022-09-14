"""Test class for Provisioning Template UI

:Requirement: Provisioning Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ProvisioningTemplates

:Assignee: sganar

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from airgun.session import Session
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import DataFile
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def template_data():
    return DataFile.OS_TEMPLATE_DATA_FILE.read_bytes()


@pytest.fixture(scope='function', autouse=False)
def clone_setup(module_org, module_location):
    name = gen_string('alpha')
    content = gen_string('alpha')
    os_list = [entities.OperatingSystem().create().title for _ in range(2)]
    return {
        'pt': entities.ProvisioningTemplate(
            name=name,
            organization=[module_org],
            location=[module_location],
            template=content,
            snippet=False,
        ).create(),
        'os_list': os_list,
    }


@pytest.mark.tier2
def test_positive_clone(session, clone_setup):
    """Assure ability to clone a provisioning template

    :id: 912f1619-4bb0-4e0f-88ce-88b5726fdbe0

    :Steps:
        1.  Go to Provisioning template UI
        2.  Choose a template and attempt to clone it

    :expectedresults: The template is cloned

    :CaseLevel: Integration
    """
    clone_name = gen_string('alpha')
    with session:
        session.provisioningtemplate.clone(
            clone_setup['pt'].name,
            {
                'template.name': clone_name,
                'association.applicable_os.assigned': clone_setup['os_list'],
            },
        )
        pt = entities.ProvisioningTemplate().search(query={'search': f'name=={clone_name}'})
        assigned_oses = [os.read() for os in pt[0].read().operatingsystem]
        assert (
            pt
        ), 'Template {} expected to exist but is not included in the search' 'results'.format(
            clone_name
        )
        assert set(clone_setup['os_list']) == {f'{os.name} {os.major}' for os in assigned_oses}


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_org, module_location, template_data):
    """Perform end to end testing for provisioning template component

    :id: b44d4cc8-b78e-47cf-9993-0bb871ac2c96

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    os = entities.OperatingSystem().create()
    host_group = entities.HostGroup(organization=[module_org], location=[module_location]).create()
    environment = entities.Environment(
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
    combination = [{'host_group': host_group.name, 'environment': environment.name}]
    with session:
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
                'association.hg_environment_combination': combination,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        assert entities.ProvisioningTemplate().search(query={'search': f'name=={name}'}), (
            'Provisioning template {} expected to exist but is not included in the search'
            'results'.format(name)
        )
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
        assert pt['association']['hg_environment_combination'][0]['host_group'] == host_group.name
        assert pt['association']['hg_environment_combination'][0]['environment'] == environment.name
        assert pt['locations']['resources']['assigned'][0] == module_location.name
        assert pt['organizations']['resources']['assigned'][0] == module_org.name
        session.provisioningtemplate.update(name, {'template.name': new_name, 'type.snippet': True})
        updated_pt = entities.ProvisioningTemplate().search(query={'search': f'name=={new_name}'})
        assert updated_pt, (
            'Provisioning template {} expected to exist but is not included in the search'
            'results'.format(new_name)
        )
        updated_pt = updated_pt[0].read()
        assert updated_pt.snippet is True, 'Snippet attribute not updated for Provisioning Template'
        assert not updated_pt.template_kind, 'Snippet template is {}'.format(
            updated_pt.template_kind
        )
        session.provisioningtemplate.delete(new_name)
        assert not entities.ProvisioningTemplate().search(query={'search': f'name=={new_name}'}), (
            'Provisioning template {} expected to be removed but is included in the search '
            'results'.format(new_name)
        )


@pytest.mark.skip_if_open("BZ:1767040")
@pytest.mark.tier3
def test_negative_template_search_using_url():
    """Satellite should not show full trace on web_browser after invalid search in url

    :id: aeb365dc-49de-11eb-bf99-d46d6dd3b5b2

    :customerscenario: true

    :expectedresults: Satellite should not show full trace and show correct error message

    :CaseLevel: Integration

    :CaseImportance: High

    :BZ: 1767040
    """
    with Session(
        url='/templates/provisioning_templates?search=&page=1"sadfasf', login=False
    ) as session:
        login_details = {
            'username': settings.server.admin_username,
            'password': settings.server.admin_password,
        }
        session.login.login(login_details)
        error_page = session.browser.selenium.page_source
        error_helper_message = (
            "Please include in your report the full error log that can be acquired by running"
        )
        trace_link_word = "Full trace"
        assert error_helper_message in error_page
        assert trace_link_word not in error_page
        assert "foreman-rake errors:fetch_log request_id=" in error_page
