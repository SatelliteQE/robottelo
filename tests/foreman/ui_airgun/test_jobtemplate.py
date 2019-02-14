"""Test class for Jobs Template UI

:Requirement: Job Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities

from robottelo.config import settings
from robottelo.decorators import fixture, tier2


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@tier2
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for Job Template component.

    :id: 2e0e31c5-e557-4151-83f9-21820c9cb1be

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    template_name = gen_string('alpha')
    template_new_name = gen_string('alpha')
    template_clone_name = gen_string('alpha')
    job_category = gen_string('alpha')
    description_format = gen_string('alpha')
    template_user_input_name = gen_string('alpha')
    template_editor_value = '<%= input("{0}") %>'.format(template_user_input_name)
    template_inputs = [
        {
            'name': gen_string('alpha'),
            'required': True,
            'input_type': 'Puppet parameter',
            'input_content.puppet_class_name': gen_string('alpha'),
            'input_content.puppet_parameter_name':  gen_string('alpha'),
            'input_content.description': gen_string('alpha')
        },
        {
            'name': gen_string('alpha'),
            'required': False,
            'input_type': 'Fact value',
            'input_content.fact_name': gen_string('alpha'),
            'input_content.description': gen_string('alpha')
        },
        {
            'name': template_user_input_name,
            'required': True,
            'input_type': 'User input',
            'input_content.options': gen_string('alpha'),
            'input_content.advanced': True,
            'input_content.description': gen_string('alpha')
        }
    ]
    job_foreign_input_sets = [
        {
            'target_template': 'Run Command - SSH Default',
            'include_all': True,
            'exclude': ', '.join([gen_string('alpha') for _ in range(3)])
        },
        {
            'target_template': 'Run Command - SSH Default',
            'include_all': False,
            'include': ', '.join([gen_string('alpha') for _ in range(3)])
        }
    ]
    value = gen_string('alpha')
    with session:
        session.jobtemplate.create({
            'template.name': template_name,
            'template.default': False,
            'template.template_editor.rendering_options': 'Input',
            'template.template_editor.editor': template_editor_value,
            'job.job_category': job_category,
            'job.description_format': description_format,
            'job.provider_type': 'SSH',
            'job.timeout': '6000',
            'inputs': template_inputs,
            'job.value': value,
            'job.current_user': True,
            'job.overridable': False,
            'job.foreign_input_sets': job_foreign_input_sets,
            'type.snippet': True,
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        template = session.jobtemplate.read(template_name, editor_view_option='Input')
        assert template['template']['name'] == template_name
        assert template['template']['default'] is False
        assert template['template']['template_editor']['editor'] == template_editor_value
        assert template['job']['job_category'] == job_category
        assert template['job']['description_format'] == description_format
        assert template['job']['provider_type'] == 'SSH'
        assert template['job']['timeout'] == '6000'
        assert template['job']['value'] == value
        assert template['job']['current_user']
        assert template['job']['overridable'] is False
        assert template['type']['snippet']
        assert module_org.name in template['organizations']['resources']['assigned']
        assert module_loc.name in template['locations']['resources']['assigned']
        assert len(template['inputs']) == 3
        assert template['inputs'][0]['name'] == template_inputs[0]['name']
        assert template['inputs'][0]['required'] == template_inputs[0]['required']
        assert template['inputs'][0]['input_type'] == template_inputs[0]['input_type']
        assert (template['inputs'][0]['input_content']['puppet_class_name']
                == template_inputs[0]['input_content.puppet_class_name'])
        assert (template['inputs'][0]['input_content']['puppet_parameter_name']
                == template_inputs[0]['input_content.puppet_parameter_name'])
        assert (template['inputs'][0]['input_content']['description']
                == template_inputs[0]['input_content.description'])
        assert template['inputs'][1]['name'] == template_inputs[1]['name']
        assert template['inputs'][1]['required'] == template_inputs[1]['required']
        assert template['inputs'][1]['input_type'] == template_inputs[1]['input_type']
        assert (template['inputs'][1]['input_content']['fact_name']
                == template_inputs[1]['input_content.fact_name'])
        assert (template['inputs'][1]['input_content']['description']
                == template_inputs[1]['input_content.description'])
        assert template['inputs'][2]['name'] == template_inputs[2]['name']
        assert template['inputs'][2]['required'] == template_inputs[2]['required']
        assert template['inputs'][2]['input_type'] == template_inputs[2]['input_type']
        assert (template['inputs'][2]['input_content']['options']
                == template_inputs[2]['input_content.options'])
        assert (template['inputs'][2]['input_content']['advanced']
                == template_inputs[2]['input_content.advanced'])
        assert (template['inputs'][2]['input_content']['description']
                == template_inputs[2]['input_content.description'])

        assert len(template['job']['foreign_input_sets']) == 2
        assert (template['job']['foreign_input_sets'][0]['target_template']
                == job_foreign_input_sets[0]['target_template'])
        assert (template['job']['foreign_input_sets'][0]['include_all']
                == job_foreign_input_sets[0]['include_all'])
        assert (template['job']['foreign_input_sets'][0]['exclude']
                == job_foreign_input_sets[0]['exclude'])
        assert (template['job']['foreign_input_sets'][1]['target_template']
                == job_foreign_input_sets[1]['target_template'])
        assert (template['job']['foreign_input_sets'][1]['include_all']
                == job_foreign_input_sets[1]['include_all'])
        assert (template['job']['foreign_input_sets'][1]['include']
                == job_foreign_input_sets[1]['include'])
        template_values = session.jobtemplate.read(
            template_name,
            editor_view_option='Preview',
            widget_names='template.template_editor.editor'
        )
        assert (template_values['template']['template_editor']['editor']
                == '$USER_INPUT[{0}]'.format(template_user_input_name))
        session.jobtemplate.update(
            template_name,
            {
                'template.name': template_new_name,
                'template.template_editor.rendering_options': 'Input',
                'template.template_editor.editor': '<%= foreman_url("built") %>'
            }
        )
        assert not session.jobtemplate.search(template_name)
        template_values = session.jobtemplate.read(
            template_new_name,
            editor_view_option='Preview',
            widget_names='template.template_editor.editor'
        )
        assert settings.server.hostname in template_values['template']['template_editor']['editor']
        session.jobtemplate.clone(template_new_name, {'template.name': template_clone_name})
        assert session.jobtemplate.search(template_clone_name)[0]['Name'] == template_clone_name
        for name in (template_new_name, template_clone_name):
            session.jobtemplate.delete(name)
            assert not session.jobtemplate.search(name)
