"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.decorators import tier2
from robottelo.virtwho import get_form_data


@tier2
def test_positive_end_to_end(session):
    """Perform end to end testing for Virt-whoConfigurePlugin component

    :id: 8930849f-37dc-43a6-b734-51db146c7f2e

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Acceptance

    :CaseImportance: High
    """
    name = gen_string('alpha')
    with session:
        form_data = get_form_data(name)
        session.virtwho_configure.create(form_data)
        assert session.virtwho_configure.search(name)[0]['Name'] == name
        session.virtwho_configure.edit(name, {'hypervisor_id': 'uuid'})
        values = session.virtwho_configure.read(name)
        assert values['overview']['hypervisor_id'] == 'uuid'
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)
