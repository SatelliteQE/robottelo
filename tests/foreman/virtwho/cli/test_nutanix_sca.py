"""Test class for Virtwho Configure CLI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Team: Phoenix

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.utils.virtwho import deploy_configure_by_command
from robottelo.utils.virtwho import deploy_configure_by_script
from robottelo.utils.virtwho import get_configure_command
from robottelo.utils.virtwho import get_configure_file
from robottelo.utils.virtwho import get_configure_option


@pytest.fixture()
def form_data(target_sat, module_sca_manifest_org):
    sca_form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor-id': 'hostname',
        'hypervisor-type': settings.virtwho.ahv.hypervisor_type,
        'hypervisor-server': settings.virtwho.ahv.hypervisor_server,
        'organization-id': module_sca_manifest_org.id,
        'filtering-mode': 'none',
        'satellite-url': target_sat.hostname,
        'hypervisor-username': settings.virtwho.ahv.hypervisor_username,
        'hypervisor-password': settings.virtwho.ahv.hypervisor_password,
        'prism-flavor': settings.virtwho.ahv.prism_flavor,
    }
    return sca_form


@pytest.fixture()
def virtwho_config(form_data, target_sat):
    virtwho_config = target_sat.cli.VirtWhoConfig.create(form_data)['general-information']
    yield virtwho_config
    target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config['name']})
    assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data['name']))


class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, form_data, virtwho_config, target_sat, deploy_type
    ):
        """Verify "hammer virt-who-config deploy"

        :id: 71750104-b436-4ad4-9b6b-6f0fe8c3ee4c

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config['status'] == 'No Report Yet'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor-type'], debug=True, org=module_sca_manifest_org.label
            )
        elif deploy_type == "script":
            script = target_sat.cli.VirtWhoConfig.fetch(
                {'id': virtwho_config['id']}, output_format='base'
            )
            deploy_configure_by_script(
                script, form_data['hypervisor-type'], debug=True, org=module_sca_manifest_org.label
            )
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, form_data, virtwho_config, target_sat
    ):
        """Verify hypervisor_id option by hammer virt-who-config update"

        :id: 565228cd-2124-41ed-89b7-84ec6ff77213

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        for value in ['uuid', 'hostname']:
            target_sat.cli.VirtWhoConfig.update(
                {'id': virtwho_config['id'], 'hypervisor-id': value}
            )
            result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})
            assert result['connection']['hypervisor-id'] == value
            config_file = get_configure_file(virtwho_config['id'])
            command = get_configure_command(virtwho_config['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor-type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, module_sca_manifest_org, form_data, target_sat, deploy_type
    ):
        """Verify "hammer virt-who-config deploy" on nutanix prism central mode

        :id: 96fd691f-5b62-469c-adc7-f2739ddf4a62

        :expectedresults:
            1. Config can be created and deployed
            2. The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseLevel: Integration

        :CaseImportance: High
        """
        form_data['prism-flavor'] = "central"
        virtwho_config = target_sat.cli.VirtWhoConfig.create(form_data)['general-information']
        assert virtwho_config['status'] == 'No Report Yet'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config['id'], module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor-type'], debug=True, org=module_sca_manifest_org.label
            )
        elif deploy_type == "script":
            script = target_sat.cli.VirtWhoConfig.fetch(
                {'id': virtwho_config['id']}, output_format='base'
            )
            deploy_configure_by_script(
                script, form_data['hypervisor-type'], debug=True, org=module_sca_manifest_org.label
            )
        # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
        config_file = get_configure_file(virtwho_config['id'])
        assert get_configure_option("prism_central", config_file) == 'true'
        virt_who_instance = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})[
            'general-information'
        ]['status']
        assert virt_who_instance == 'OK'

    @pytest.mark.tier2
    def test_positive_prism_element_prism_central_option(
        self, module_sca_manifest_org, form_data, virtwho_config, target_sat
    ):
        """Verify prism_central option by hammer virt-who-config update"

        :id: 68c75ae0-0beb-483e-874a-b14f8171f40a

        :expectedresults: prism_central option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        value = 'central'
        result = target_sat.cli.VirtWhoConfig.update(
            {'id': virtwho_config['id'], 'prism-flavor': value}
        )
        assert result[0]['message'] == f"Virt Who configuration [{virtwho_config['name']}] updated"
        result = target_sat.cli.VirtWhoConfig.info({'id': virtwho_config['id']})
        assert result['general-information']['ahv-prism-flavor'] == value
        config_file = get_configure_file(virtwho_config['id'])
        command = get_configure_command(virtwho_config['id'], module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data['hypervisor-type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option("prism_central", config_file) == 'true'
