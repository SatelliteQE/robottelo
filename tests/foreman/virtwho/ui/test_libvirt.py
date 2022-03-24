"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Assignee: kuhuang

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.virtwho_utils import deploy_configure_by_command
from robottelo.virtwho_utils import deploy_configure_by_script
from robottelo.virtwho_utils import get_configure_command
from robottelo.virtwho_utils import get_configure_file
from robottelo.virtwho_utils import get_configure_id
from robottelo.virtwho_utils import get_configure_option


@pytest.fixture()
def form_data():
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.libvirt.hypervisor_type,
        'hypervisor_content.server': settings.virtwho.libvirt.hypervisor_server,
        'hypervisor_content.username': settings.virtwho.libvirt.hypervisor_username,
    }
    return form


class TestVirtwhoConfigforLibvirt:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(self, default_org, session, form_data):
        """Verify configure created and deployed with id.

        :id: ae37ea79-f99c-4511-ace9-a7de26d6db40

        :expectedresults:
            1. Config can be created and deployed by command
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(name)
            command = values['deploy']['command']
            hypervisor_name, guest_name = deploy_configure_by_command(
                command, form_data['hypervisor_type'], debug=True, org=default_org.label
            )
            assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            hypervisor_display_name = session.contenthost.search(hypervisor_name)[0]['Name']
            vdc_physical = f'product_id = {settings.virtwho.sku.vdc_physical} and type=NORMAL'
            vdc_virtual = f'product_id = {settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'
            session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
            assert session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
            session.contenthost.add_subscription(guest_name, vdc_virtual)
            assert session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(self, default_org, session, form_data):
        """Verify configure created and deployed with script.

        :id: 3655a501-ab05-4724-945a-7f6e6878091d

        :expectedresults:
            1. Config can be created and deployed by script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(name)
            script = values['deploy']['script']
            hypervisor_name, guest_name = deploy_configure_by_script(
                script, form_data['hypervisor_type'], debug=True, org=default_org.label
            )
            assert session.virtwho_configure.search(name)[0]['Status'] == 'ok'
            hypervisor_display_name = session.contenthost.search(hypervisor_name)[0]['Name']
            vdc_physical = f'product_id = {settings.virtwho.sku.vdc_physical} and type=NORMAL'
            vdc_virtual = f'product_id = {settings.virtwho.sku.vdc_physical} and type=STACK_DERIVED'
            session.contenthost.add_subscription(hypervisor_display_name, vdc_physical)
            assert session.contenthost.search(hypervisor_name)[0]['Subscription Status'] == 'green'
            session.contenthost.add_subscription(guest_name, vdc_virtual)
            assert session.contenthost.search(guest_name)[0]['Subscription Status'] == 'green'
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(self, default_org, session, form_data):
        """Verify Hypervisor ID dropdown options.

        :id: b8b2b272-89f2-45d0-b922-6e988b20808b

        :expectedresults:
            hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session:
            session.virtwho_configure.create(form_data)
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id, default_org.label)
            config_file = get_configure_file(config_id)
            values = ['uuid', 'hostname']
            for value in values:
                session.virtwho_configure.edit(name, {'hypervisor_id': value})
                results = session.virtwho_configure.read(name)
                assert results['overview']['hypervisor_id'] == value
                deploy_configure_by_command(
                    config_command, form_data['hypervisor_type'], org=default_org.label
                )
                assert get_configure_option('hypervisor_id', config_file) == value
            session.virtwho_configure.delete(name)
            assert not session.virtwho_configure.search(name)
