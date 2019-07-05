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
from robottelo.config import settings
from robottelo.decorators import stubbed, fixture, tier2


@fixture(scope='module')
def form_data():
    hypervisor_type = settings.virtwho.hypervisor_type
    hypervisor_server = settings.virtwho.hypervisor_server
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': hypervisor_type,
        'hypervisor_content.server': hypervisor_server,
    }
    if hypervisor_type == 'libvirt':
        form['hypervisor_content.username'] = (
            settings.virtwho.hypervisor_username)
    elif hypervisor_type == 'kubevirt':
        form['hypervisor_content.kubeconfig'] = (
            settings.virtwho.hypervisor_config_file)
    else:
        form['hypervisor_content.username'] = (
            settings.virtwho.hypervisor_username)
        form['hypervisor_content.password'] = (
            settings.virtwho.hypervisor_password)
    return form


@tier2
def test_positive_deploy_configure_by_id(session, form_data):
    """ Verify configure created and deployed with id.

    :id: c5385f69-aa7e-4fc0-b126-08aacb14bfb8

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
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        assert session.virtwho_configure.search(name)[0]['Name'] == name
        session.virtwho_configure.edit(name, {'hypervisor_id': 'uuid'})
        values = session.virtwho_configure.read(name)
        assert values['overview']['hypervisor_id'] == 'uuid'
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


@stubbed()
@tier2
def test_positive_deploy_configure_by_script(session):
    """ Verify configure created and deployed with script.

    :id: cae3671c-a583-4e67-a0de-95d191d2174c

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
