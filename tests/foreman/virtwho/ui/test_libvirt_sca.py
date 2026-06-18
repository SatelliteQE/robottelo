"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseComponent: Virt-whoConfigurePlugin

:team: Proton

:BlockedBy: SAT-45010
"""

import pytest

from robottelo.utils.virtwho import (
    get_configure_file,
    get_configure_id,
    get_configure_option,
    hypervisor_guest_mapping_newcontent_ui,
)


class TestVirtwhoConfigforLibvirt:
    @pytest.mark.parametrize('deploy_type_ui', ['script'], indirect=True)
    def test_positive_deploy_configure_by_script(
        self,
        module_sca_manifest_org,
        org_session,
        form_data_ui,
        deploy_type_ui,
        default_location,
    ):
        """Verify configure created and deployed with script.

        :id: 401cfc74-6cde-4ae1-bf03-b77a7528575c

        :expectedresults:
            1. Config can be created and deployed by script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Subscription Status set to 'Simple Content Access', and generate mapping in Legacy UI
            5. Check Hypervisor host subscription status and hypervisor host and virtual guest mapping in UI
            6. Config can be deleted

        :CaseImportance: High
        """
        hypervisor_name, guest_name = deploy_type_ui
        # Check virt-who config status
        assert org_session.virtwho_configure.search(form_data_ui['name'])[0]['Status'] == 'ok'

        # Check Hypervisor host subscription status and hypervisor host and virtual guest mapping in UI
        hypervisor_guest_mapping_newcontent_ui(
            org_session, default_location, hypervisor_name, guest_name
        )

    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, virtwho_config_ui, org_session, form_data_ui, target_sat
    ):
        """Verify Hypervisor ID dropdown options.

        :id: 24012fb0-b940-4a9f-bce8-9e43fdb50d82

        :expectedresults:
            1. hypervisor_id can be changed in virt-who-config-{}.conf if the
            dropdown option is selected to uuid/hwuuid/hostname.

        :CaseImportance: Medium
        """
        name = form_data_ui['name']
        config_id = get_configure_id(name, target_sat)
        config_file = get_configure_file(config_id)
        values = ['uuid', 'hostname']
        for value in values:
            org_session.virtwho_configure.edit(name, {'hypervisor_id': value})
            results = org_session.virtwho_configure.read(name)
            assert results['overview']['hypervisor_id'] == value
            script = results['deploy']['script']
            deploy_configure_by_script(
                script,
                form_data_ui['hypervisor_type'],
                org=module_sca_manifest_org.label,
                target_sat=target_sat,
            )
            assert get_configure_option('hypervisor_id', config_file) == value
