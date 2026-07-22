"""Test class for Virtwho Configure API

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Proton

:BlockedBy: SAT-36027, SAT-45010
"""


from robottelo.utils.virtwho import (
    deploy_configure_by_script,
    get_configure_file,
    get_configure_option,
)


class TestVirtWhoConfigforKubevirt:
    def test_positive_deploy_configure_by_job(
        self,
        module_sca_manifest_org,
        deploy_via_job_api,
    ):
        """Verify virt-who configuration deployed via Ansible REX job using API.

        :id: de336fbb-01c9-4f37-b558-09d4e098e3c3

        :steps:
            1. Run the 'Deploy virt-who Config' Ansible REX job targeting the Satellite via API
            2. Verify virt-who service is running and reporting

        :expectedresults:
            1. Ansible REX job completes successfully
            2. virt-who service reports hypervisor-guest mapping

        :Verifies: SAT-46996

        :CaseImportance: High
        """
        hypervisor_name, guest_name = deploy_via_job_api
        assert hypervisor_name
        assert guest_name

    def test_positive_deploy_configure_by_script(
        self, module_sca_manifest_org, virtwho_config_api, target_sat, deploy_type_api
    ):
        """Verify "POST /foreman_virt_who_configure/api/v2/configs"

        :id: bf736822-2353-49c2-a8e6-79d9b3feddc5

        :expectedresults: Config can be created and deployed by script

        :CaseImportance: High
        """
        assert virtwho_config_api.status == 'unknown'
        virt_who_instance = (
            target_sat.api.VirtWhoConfig()
            .search(query={'search': f'name={virtwho_config_api.name}'})[0]
            .status
        )
        assert virt_who_instance == 'ok'

    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, form_data_api, virtwho_config_api, target_sat
    ):
        """Verify hypervisor_id option by "PUT

        /foreman_virt_who_configure/api/v2/configs/:id"

        :id: 9072c1c8-1ea3-4311-99c9-94d3d3a0e8d8

        :expectedresults: hypervisor_id option can be updated.

        :CaseImportance: Medium
        """
        for value in ['uuid', 'hostname']:
            virtwho_config_api.hypervisor_id = value
            virtwho_config_api.update(['hypervisor_id'])
            config_file = get_configure_file(virtwho_config_api.id)
            script = virtwho_config_api.deploy_script()
            deploy_configure_by_script(
                script['virt_who_config_script'],
                form_data_api['hypervisor_type'],
                org=module_sca_manifest_org.label,
                target_sat=target_sat,
            )
            assert get_configure_option('hypervisor_id', config_file) == value
