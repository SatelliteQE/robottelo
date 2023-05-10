"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.utils.virtwho import check_message_in_rhsm_log
from robottelo.utils.virtwho import deploy_configure_by_command
from robottelo.utils.virtwho import deploy_configure_by_script
from robottelo.utils.virtwho import get_configure_command
from robottelo.utils.virtwho import get_configure_file
from robottelo.utils.virtwho import get_configure_id
from robottelo.utils.virtwho import get_configure_option
from robottelo.utils.virtwho import get_hypervisor_ahv_mapping


@pytest.fixture()
def form_data():
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.ahv.hypervisor_type,
        'hypervisor_content.server': settings.virtwho.ahv.hypervisor_server,
        'hypervisor_content.username': settings.virtwho.ahv.hypervisor_username,
        'hypervisor_content.password': settings.virtwho.ahv.hypervisor_password,
        'hypervisor_content.prism_flavor': "Prism Element",
        'ahv_internal_debug': False,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data, target_sat, session):
    name = gen_string('alpha')
    form_data['name'] = name
    with session:
        session.virtwho_configure.create(form_data)
        yield virtwho_config
        session.virtwho_configure.delete(name)
        assert not session.virtwho_configure.search(name)


class TestVirtwhoConfigforNutanix:
    @pytest.mark.tier2
    def test_positive_deploy_configure_by_id(self, default_org, virtwho_config, session, form_data):
        """Verify configure created and deployed with id.

        :id: becea4d0-db4e-4a85-93d2-d40e86da0e2f

        :expectedresults:
            1. Config can be created and deployed by command
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = form_data['name']
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

    @pytest.mark.tier2
    def test_positive_deploy_configure_by_script(
        self, default_org, virtwho_config, session, form_data
    ):
        """Verify configure created and deployed with script.

        :id: 1c1b19c9-988c-4b86-a2b2-658fded10ccb

        :expectedresults:
            1. Config can be created and deployed by script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = form_data['name']
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

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(self, default_org, virtwho_config, session, form_data):
        """Verify Hypervisor ID dropdown options.

        :id: e076a305-88f4-42fb-8ef2-cb55e38eb912

        :expectedresults:
            hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = form_data['name']
        values = session.virtwho_configure.read(name)
        config_id = get_configure_id(name)
        config_command = values['deploy']['command']
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

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, default_org, session, form_data, deploy_type
    ):
        """Verify configure created and deployed with id on nutanix prism central mode

        :id: 74fb3b05-2f88-4ebf-8d0d-4973ee8536d8

        :expectedresults:
            1. Config can be created and deployed by command
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. The prism_central has been set true in /etc/virt-who.d/vir-who.conf file
            5. Virtual sku can be generated and attached
            6. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        form_data['name'] = name
        form_data['hypervisor_content.prism_flavor'] = "Prism Central"
        with session:
            session.virtwho_configure.create(form_data)
            values = session.virtwho_configure.read(name)
            if deploy_type == "id":
                command = values['deploy']['command']
                hypervisor_name, guest_name = deploy_configure_by_command(
                    command, form_data['hypervisor_type'], debug=True, org=default_org.label
                )
            elif deploy_type == "script":
                script = values['deploy']['script']
                hypervisor_name, guest_name = deploy_configure_by_script(
                    script, form_data['hypervisor_type'], debug=True, org=default_org.label
                )
            # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
            config_id = get_configure_id(name)
            config_file = get_configure_file(config_id)
            assert get_configure_option("prism_central", config_file) == 'true'
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
    def test_positive_prism_central_prism_flavor_option(
        self, default_org, virtwho_config, session, form_data
    ):
        """Verify prism_flavor dropdown options.

        :id: c76d94dd-25da-447d-8194-44217a36808b

        :expectedresults:
            prism_flavor can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to prism central.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = form_data['name']
        results = session.virtwho_configure.read(name)
        assert results['overview']['prism_flavor'] == "element"
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, default_org.name)
        config_file = get_configure_file(config_id)
        session.virtwho_configure.edit(name, {'hypervisor_content.prism_flavor': "Prism Central"})
        results = session.virtwho_configure.read(name)
        assert results['overview']['prism_flavor'] == "central"
        deploy_configure_by_command(
            config_command, form_data['hypervisor_type'], org=default_org.label
        )
        assert get_configure_option('prism_central', config_file) == 'true'

    @pytest.mark.tier2
    def test_positive_ahv_internal_debug_option(
        self, default_org, virtwho_config, session, form_data
    ):
        """Verify ahv_internal_debug option by hammer virt-who-config"

        :id: af92b814-fe7a-4969-b2ab-7b68859de3ce155

        :expectedresults:
            1. enable-ahv-debug option has been set to false
            2. ahv_internal_debug bas been set to false in virt-who-config-X.conf
            3. warning message exist in log file /var/log/rhsm/rhsm.log
            4. ahv_internal_debug option can be updated
            5. message Host UUID {system_uuid} found for VM: {guest_uuid} exist in rhsm.log
            6. ahv_internal_debug bas been set to true in virt-who-config-X.conf
            7. warning message does not exist in log file /var/log/rhsm/rhsm.log
        :CaseLevel: Integration

        :CaseImportance: Medium

        :BZ: 2141719
        :customerscenario: true
        """
        name = form_data['name']
        config_id = get_configure_id(name)
        values = session.virtwho_configure.read(name)
        command = values['deploy']['command']
        config_file = get_configure_file(config_id)
        deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=default_org.label
        )
        results = session.virtwho_configure.read(name)
        assert str(results['overview']['ahv_internal_debug']) == 'False'
        # ahv_internal_debug does not set in virt-who-config-X.conf
        option = 'ahv_internal_debug'
        env_error = f"option {option} is not exist or not be enabled in {config_file}"
        try:
            get_configure_option("ahv_internal_debug", config_file)
        except Exception as VirtWhoError:
            assert env_error == str(VirtWhoError)
        # check message exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert check_message_in_rhsm_log(message) == message

        # Update ahv_internal_debug option to true
        session.virtwho_configure.edit(name, {'ahv-internal-debug': True})
        results = session.virtwho_configure.read(name)
        command = results['deploy']['command']
        assert str(results['overview']['ahv_internal_debug']) == 'True'
        deploy_configure_by_command(
            command, form_data['hypervisor_type'], debug=True, org=default_org.label
        )
        assert get_hypervisor_ahv_mapping(form_data['hypervisor_type']) == 'Host UUID found for VM'
        # ahv_internal_debug bas been set to true in virt-who-config-X.conf
        config_file = get_configure_file(config_id)
        assert get_configure_option("ahv_internal_debug", config_file) == 'true'
        # check message does not exist in log file /var/log/rhsm/rhsm.log
        message = 'Value for "ahv_internal_debug" not set, using default: False'
        assert str(check_message_in_rhsm_log(message)) == 'False'
