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
