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
from .utils import get_form_data


@tier2
def test_positive_deploy_configure_by_id(session):
    """ Verify configure created and deployed with id.

    :id: 8930849f-37dc-43a6-b734-51db146c7f2e

    :steps:
        1. Register guest to the satellite by CLI
        2. Create virtwho configure and get the deploy command in UI
        3. Run the above command by CLI
        4. Attach physical vdc to hypervisor, check the virtual
           vdc is generated and attachable in guest by UI
        5. Delete config by UI

    :expectedresults:
        1. Config can be created and deployed
        2. No error msg in /var/log/rhsm/rhsm.log
        3. Report is sent to satellite
        4. Virtual sku can be generated and attached
        5. Config can be deleted
    """
    name = gen_string('alpha')
    form_data = get_form_data(name)
    with session:
        session.virtwho_configure.create(form_data)
        assert session.virtwho_configure.search(name)[0]['Name'] == name
        session.virtwho_configure.edit(name, {'hypervisor_id': 'uuid'})
        values = session.virtwho_configure.read(name)
        assert values['overview']['hypervisor_id'] == 'uuid'
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@tier2
def test_positive_deploy_configure_by_script(session):
    """ Verify configure created and deployed with script.

    :id: 8930849f-37dc-43a6-b734-51db146c7f2e

    :steps:
        1. Register guest to the satellite by CLI
        2. Create virtwho configure and get the deploy script in UI
        3. Run the above command by CLI
        4. Attach physical vdc to hypervisor, check the virtual
           vdc is generated and attachable in guest by UI
        5. Delete config by UI

    :expectedresults:
        1. Config can be created and deployed
        2. No error msg in /var/log/rhsm/rhsm.log
        3. Report is sent to satellite
        4. Virtual sku can be generated and attached
        5. Config can be deleted

    :CaseAutomation: notautomated
    """
