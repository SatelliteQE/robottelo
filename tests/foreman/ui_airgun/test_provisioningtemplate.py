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

from robottelo.datafactory import gen_string
from robottelo.decorators import tier2


def test_positive_create(session):
    name = gen_string('alpha')
    with session:
        session.provisioningtemplate.create({
            'template.name': name,
            'template.template_editor.editor': gen_string('alpha'),
            'type.template_type': 'Provisioning template'
        })
        assert session.provisioningtemplate.search(name) == name


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
        entities.OperatingSystem().create().name for _ in range(2)
    ]
    with session:
        session.provisioningtemplate.create({
            'template.name': name,
            'template.template_editor.editor': content,
            'type.template_type': 'Provisioning template'
        })
        assert session.provisioningtemplate.search(name) == name
        session.provisioningtemplate.clone(
            name,
            {
                'template.name': clone_name,
                'association.applicable_os.assigned': os_list
            }
        )
        assert session.provisioningtemplate.search(clone_name) == clone_name
        template = session.provisioningtemplate.read(clone_name)
        input_os_list = sorted(os_list)
        cloned_template_os_list = sorted(
            template['association']['applicable_os']['assigned'])
        for i in range(len(os_list)):
            assert input_os_list[i] in cloned_template_os_list[i]
