"""Test class for Virtwho Configure API

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
def form_data(module_sca_manifest_org, target_sat):
    form = {
        'name': gen_string('alpha'),
        'debug': 1,
        'interval': '60',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.ahv.hypervisor_type,
        'hypervisor_server': settings.virtwho.ahv.hypervisor_server,
        'organization_id': module_sca_manifest_org.id,
        'filtering_mode': 'none',
        'satellite_url': target_sat.hostname,
        'hypervisor_username': settings.virtwho.ahv.hypervisor_username,
        'hypervisor_password': settings.virtwho.ahv.hypervisor_password,
        'prism_flavor': settings.virtwho.ahv.prism_flavor,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data, target_sat):
    virtwho_config = target_sat.api.VirtWhoConfig(**form_data).create()
    yield virtwho_config
    virtwho_config.delete()
    assert not target_sat.api.VirtWhoConfig().search(query={'search': f"name={form_data['name']}"})


class TestVirtWhoConfigforNutanix:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, form_data, virtwho_config, target_sat, deploy_type
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: 81731df9-9bfc-411b-9836-ff298fd5228d

        :expectedresults: Config can be created and deployed

        :CaseLevel: Integration

        :CaseImportance: High
        """
        assert virtwho_config.status == 'unknown'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor_type'], debug=True, org=module_sca_manifest_org.label
            )
        elif deploy_type == "script":
            script = virtwho_config.deploy_script()
            deploy_configure_by_script(
                script['virt_who_config_script'],
                form_data['hypervisor_type'],
                debug=True,
                org=module_sca_manifest_org.label,
            )
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, form_data, virtwho_config, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 850cc280-3f5a-498e-9132-5672dfe2f865

        :expectedresults: hypervisor_id option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        for value in ['uuid', 'hostname']:
            virtwho_config.hypervisor_id = value
            virtwho_config.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config.id)
            command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, module_sca_manifest_org, form_data, target_sat, deploy_type
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs" on nutanix prism central mode

        :id: 14b87abb-9355-4669-929a-20e656cdf446

        :expectedresults:
            Config can be created and deployed
            The prism_central has been set in /etc/virt-who.d/vir-who.conf file

        :CaseLevel: Integration

        :CaseImportance: High
        """
        form_data['prism_flavor'] = "central"
        virtwho_config = target_sat.api.VirtWhoConfig(**form_data).create()
        assert virtwho_config.status == 'unknown'
        if deploy_type == "id":
            command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
            deploy_configure_by_command(
                command, form_data['hypervisor_type'], debug=True, org=module_sca_manifest_org.label
            )
        elif deploy_type == "script":
            script = virtwho_config.deploy_script()
            deploy_configure_by_script(
                script['virt_who_config_script'],
                form_data['hypervisor_type'],
                debug=True,
                org=module_sca_manifest_org.label,
            )
        # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
        config_file = get_configure_file(virtwho_config.id)
        assert get_configure_option("prism_central", config_file) == 'true'
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'

    @pytest.mark.tier2
    def test_positive_prism_central_prism_central_option(
        self, module_sca_manifest_org, form_data, virtwho_config, target_sat
    ):
        """Verify prism_flavor option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: f6ca8722-8f39-47b2-b7c0-e0c554aa7c65

        :expectedresults: prism_flavor option can be updated.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        value = 'central'
        virtwho_config.prism_flavor = value
        virtwho_config.update(['prism_flavor'])
        config_file = get_configure_file(virtwho_config.id)
        command = get_configure_command(virtwho_config.id, module_sca_manifest_org.name)
        deploy_configure_by_command(
            command, form_data['hypervisor_type'], org=module_sca_manifest_org.label
        )
        assert get_configure_option("prism_central", config_file) == 'true'
