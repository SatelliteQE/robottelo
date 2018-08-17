"""Test class for Jobs Template UI

:Requirement: Job Template

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities

from robottelo.datafactory import gen_string


def test_positive_create(session):
    name = gen_string('alpha')
    job_category = gen_string('alpha')
    description_format = gen_string('alpha')
    input_name = gen_string('alpha')
    puppet_class_name = gen_string('alpha')
    puppet_parameter_name = gen_string('alpha')
    value = gen_string('alpha')
    location = entities.Location().create()
    org = entities.Organization().create()
    with session:
        session.jobtemplate.create({
            'template.name': name,
            'template.default': False,
            'template.template_editor.editor': gen_string('alpha'),
            'job.job_category': job_category,
            'job.description_format': description_format,
            'job.provider_type': 'SSH',
            'job.timeout': '6000',
            'job.template_input.name': input_name,
            'job.template_input.required': True,
            'job.template_input.input_type': 'Puppet parameter',
            'job.template_input.input_content.puppet_class_name':
                puppet_class_name,
            'job.template_input.input_content.puppet_parameter_name':
                puppet_parameter_name,
            'job.value': value,
            'job.current_user': True,
            'job.overridable': False,
            'type.snippet': True,
            'locations.resources.assigned': [location.name],
            'organizations.resources.assigned': [org.name],
        })
        template = session.jobtemplate.read(name)
        assert template['template']['name'] == name
        assert template['template']['default'] is False
        assert template['job']['job_category'] == job_category
        assert template['job']['description_format'] == description_format
        assert template['job']['provider_type'] == 'SSH'
        assert template['job']['timeout'] == '6000'
        assert template['job']['template_input']['name'] == input_name
        assert template['job']['template_input']['required']
        assert template['job']['template_input'][
            'input_type'] == 'Puppet parameter'
        assert template['job']['template_input'][
            'input_content']['puppet_class_name'] == puppet_class_name
        assert template['job']['template_input'][
            'input_content']['puppet_parameter_name'] == puppet_parameter_name
        assert template['job']['value'] == value
        assert template['job']['current_user']
        assert template['job']['overridable'] is False
        assert template['type']['snippet']
        assert location.name in template['locations']['resources']['assigned']
        assert org.name in template['organizations']['resources']['assigned']


def test_positive_update(session):
    name = gen_string('alpha')
    include_value = gen_string('alpha')
    exclude_value = gen_string('alpha')
    with session:
        session.jobtemplate.create({
            'template.name': name,
            'template.template_editor.editor': gen_string('alpha'),
        })
        assert session.jobtemplate.search(name)[0]['Name'] == name
        session.jobtemplate.update(
            name,
            {
                'job.foreign_input.target_template':
                    'Run Command - SSH Default',
                'job.foreign_input.include_all': False,
                'job.foreign_input.include': include_value,
                'job.foreign_input.exclude': exclude_value,
            }
        )
        template = session.jobtemplate.read(name)
        assert template['job']['foreign_input'][
            'target_template'] == 'Run Command - SSH Default'
        assert template['job']['foreign_input']['include_all'] is False
        assert template['job']['foreign_input']['include'] == include_value
        assert template['job']['foreign_input']['exclude'] == exclude_value


def test_positive_delete(session):
    name = gen_string('alpha')
    with session:
        session.jobtemplate.create({
            'template.name': name,
            'template.template_editor.editor': gen_string('alpha'),
        })
        assert session.jobtemplate.search(name)[0]['Name'] == name
        session.jobtemplate.delete(name)
        assert not session.jobtemplate.search(name)
