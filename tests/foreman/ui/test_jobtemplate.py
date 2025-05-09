"""Test class for Jobs Template UI

:Requirement: Job Template

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_alpha, gen_string
import pytest


@pytest.mark.e2e
def test_positive_end_to_end(session, module_org, module_location, target_sat):
    """Perform end to end testing for Job Template component.

    :id: 2e0e31c5-e557-4151-83f9-21820c9cb1be

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: High
    """
    template_name = gen_string('alpha')
    template_description = gen_string('alpha')
    template_new_name = gen_string('alpha')
    template_clone_name = gen_string('alpha')
    job_category = 'Miscellaneous'
    description_format = gen_string('alpha')
    template_user_input_name = gen_string('alpha')
    template_editor_value = f'<%= input("{template_user_input_name}") %>'
    template_inputs = [
        {
            'name': gen_string('alpha'),
            'required': True,
            'input_type': 'Variable',
            'input_content.variable_name': gen_string('alpha'),
            'input_content.description': gen_string('alpha'),
        },
        {
            'name': gen_string('alpha'),
            'required': False,
            'input_type': 'Fact value',
            'input_content.fact_name': gen_string('alpha'),
            'input_content.description': gen_string('alpha'),
        },
        {
            'name': template_user_input_name,
            'required': True,
            'input_type': 'User input',
            'input_content.options': gen_string('alpha'),
            'input_content.advanced': True,
            'input_content.description': gen_string('alpha'),
        },
    ]
    job_foreign_input_sets = [
        {
            'target_template': 'Run Command - Script Default',
            'include_all': True,
            'exclude': ', '.join([gen_string('alpha') for _ in range(3)]),
        },
        {
            'target_template': 'Run Command - Script Default',
            'include_all': False,
            'include': ', '.join([gen_string('alpha') for _ in range(3)]),
        },
    ]
    value = gen_string('alpha')
    with session:
        session.jobtemplate.create(
            {
                'template.name': template_name,
                'template.default': False,
                'template.template_editor.rendering_options': 'Editor',
                'template.template_editor.editor': template_editor_value,
                'template.description': template_description,
                'job.job_category': 'Miscellaneous',
                'job.description_format': description_format,
                'job.provider_type': 'Script',
                'job.timeout': '6000',
                'inputs': template_inputs,
                'job.value': value,
                'job.current_user': True,
                'job.foreign_input_sets': job_foreign_input_sets,
                'type.snippet': True,
                'organizations.resources.assigned': [module_org.name, "Default Organization"],
                'locations.resources.assigned': [module_location.name],
            }
        )
        template = session.jobtemplate.read(template_name, editor_view_option='Editor')
        assert template['template']['name'] == template_name
        assert template['template']['default'] is False
        assert template['template']['template_editor']['editor'] == template_editor_value
        assert template['template']['description'] == template_description
        assert template['job']['job_category'] == job_category
        assert template['job']['description_format'] == description_format
        assert template['job']['provider_type'] == 'Script'
        assert template['job']['timeout'] == '6000'
        assert template['job']['value'] == value
        assert template['job']['current_user']
        assert template['type']['snippet']
        assert module_org.name in template['organizations']['resources']['assigned']
        assert module_location.name in template['locations']['resources']['assigned']
        assert len(template['inputs']) == 3
        assert template['inputs'][0]['name'] == template_inputs[0]['name']
        assert template['inputs'][0]['required'] == template_inputs[0]['required']
        assert template['inputs'][0]['input_type'] == template_inputs[0]['input_type']
        assert (
            template['inputs'][0]['input_content']['variable_name']
            == template_inputs[0]['input_content.variable_name']
        )
        assert (
            template['inputs'][0]['input_content']['description']
            == template_inputs[0]['input_content.description']
        )
        assert template['inputs'][1]['name'] == template_inputs[1]['name']
        assert template['inputs'][1]['required'] == template_inputs[1]['required']
        assert template['inputs'][1]['input_type'] == template_inputs[1]['input_type']
        assert (
            template['inputs'][1]['input_content']['fact_name']
            == template_inputs[1]['input_content.fact_name']
        )
        assert (
            template['inputs'][1]['input_content']['description']
            == template_inputs[1]['input_content.description']
        )
        assert template['inputs'][2]['name'] == template_inputs[2]['name']
        assert template['inputs'][2]['required'] == template_inputs[2]['required']
        assert template['inputs'][2]['input_type'] == template_inputs[2]['input_type']
        assert (
            template['inputs'][2]['input_content']['options']
            == template_inputs[2]['input_content.options']
        )
        assert (
            template['inputs'][2]['input_content']['advanced']
            == template_inputs[2]['input_content.advanced']
        )
        assert (
            template['inputs'][2]['input_content']['description']
            == template_inputs[2]['input_content.description']
        )

        assert len(template['job']['foreign_input_sets']) == 2
        assert (
            template['job']['foreign_input_sets'][0]['target_template']
            == job_foreign_input_sets[0]['target_template']
        )
        assert (
            template['job']['foreign_input_sets'][0]['include_all']
            == job_foreign_input_sets[0]['include_all']
        )
        assert (
            template['job']['foreign_input_sets'][0]['exclude']
            == job_foreign_input_sets[0]['exclude']
        )
        assert (
            template['job']['foreign_input_sets'][1]['target_template']
            == job_foreign_input_sets[1]['target_template']
        )
        assert (
            template['job']['foreign_input_sets'][1]['include_all']
            == job_foreign_input_sets[1]['include_all']
        )
        assert (
            template['job']['foreign_input_sets'][1]['include']
            == job_foreign_input_sets[1]['include']
        )
        session.organization.select(org_name="Default Organization")
        session.location.select(loc_name="Any location")
        template_values = session.jobtemplate.read(
            template_name,
            editor_view_option='Preview',
            widget_names='template.template_editor.editor',
        )
        assert (
            template_values['template']['template_editor']['editor']
            == f'$USER_INPUT[{template_user_input_name}]'
        )
        session.jobtemplate.update(
            template_name,
            {
                'template.name': template_new_name,
                'template.template_editor.rendering_options': 'Editor',
                'template.template_editor.editor': '<%= foreman_url("built") %>',
            },
        )
        assert not session.jobtemplate.search(template_name)
        template_values = session.jobtemplate.read(
            template_new_name,
            editor_view_option='Preview',
            widget_names='template.template_editor.editor',
        )
        assert target_sat.hostname in template_values['template']['template_editor']['editor']
        session.jobtemplate.clone(template_new_name, {'template.name': template_clone_name})
        assert session.jobtemplate.search(template_clone_name)[0]['Name'] == template_clone_name
        dumped_content = target_sat.cli.JobTemplate.dump({'name': template_clone_name})
        assert len(dumped_content) > 0
        for name in (template_new_name, template_clone_name):
            session.jobtemplate.delete(name)
            assert not session.jobtemplate.search(name)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
@pytest.mark.parametrize(
    'content',
    [
        '''<% load_users(joins: "LEFT JOIN hosts ON 1=1", select: 'hosts.name AS login,hosts.id AS id', limit: 100_000).each_record do |h| %>
<%= h.id %> - <%= h.login %>
<% end %>
    ''',
        '''<% load_users(joins: ["LEFT JOIN hosts ON 1=1"], select: ['hosts.name AS login,hosts.id AS id'],limit: 100_000).each_record do |h| %>
<%= h.id %> - <%= h.login %>
<% end %>''',
    ],
    ids=['v1', 'v2'],
)
def test_positive_preview_template_check_for_injection(
    module_target_sat, module_org, module_location, rhel_contenthost, module_ak_with_cv, content
):
    """Preview a report and check for injection as per CVE-2024-8553

    :id: df7e7913-630b-4235-9464-5a45f1db244b

    :setup:
        0. Create a report template containing an exploit

    :steps:
        0. In WebUI, preview a report

    :expectedresults:
        Failure with a correct error message

    :CaseImportance: Critical
    """
    name = gen_alpha()
    filename = gen_alpha()
    module_target_sat.execute(f'''cat << EOF > {filename}
{content}
EOF
''')
    module_target_sat.cli.JobTemplate.create(
        {
            'name': name,
            'organization-id': module_org.id,
            'location-id': module_location.id,
            'file': filename,
            'job-category': 'Commands',
            'provider-type': 'script',
        }
    )
    rhel_contenthost.register(
        module_org, module_location, module_ak_with_cv.name, module_target_sat
    )
    with module_target_sat.ui_session() as session:
        session.organization.select(module_org.name)
        session.location.select(module_location.name)
        rendered = session.jobtemplate.read(
            name,
            editor_view_option='Preview',
            widget_names=['template.template_editor.editor', 'template.template_editor.error'],
        )
    assert (
        "Problem with previewing the template: error during rendering: Value of 'select' passed to load_users must be Symbol or Array of Symbols. Note that you must save template input changes before you try to preview it."
        in rendered['template']['template_editor']['error']
    )
    assert (
        "Error during rendering, Return to Editor tab."
        in rendered['template']['template_editor']['editor']
    )
