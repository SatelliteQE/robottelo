"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:team: Phoenix-subscriptions

:TestType: Functional

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.utils.virtwho import deploy_configure_by_command
from robottelo.utils.virtwho import deploy_configure_by_script
from robottelo.utils.virtwho import get_configure_command
from robottelo.utils.virtwho import get_configure_file
from robottelo.utils.virtwho import get_configure_id
from robottelo.utils.virtwho import get_configure_option


@pytest.fixture()
def form_data():
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.hyperv.hypervisor_type,
        'hypervisor_content.server': settings.virtwho.hyperv.hypervisor_server,
        'hypervisor_content.username': settings.virtwho.hyperv.hypervisor_username,
        'hypervisor_content.password': settings.virtwho.hyperv.hypervisor_password,
    }
    return form


@pytest.fixture()
def virtwho_config(form_data, target_sat, session_sca):
    name = gen_string('alpha')
    form_data['name'] = name
    with session_sca:
        session_sca.virtwho_configure.create(form_data)
        yield virtwho_config
        session_sca.virtwho_configure.delete(name)
        assert not session_sca.virtwho_configure.search(name)


class TestVirtwhoConfigforHyperv:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, virtwho_config, session_sca, form_data, deploy_type
    ):
        """Verify configure created and deployed with id.

        :id: b7620f1b-8fef-4e5e-a3cb-447cf914d0e6

        :expectedresults:
            1. Config can be created and deployed by command or script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Virtual sku can be generated and attached
            5. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = form_data['name']
        values = session_sca.virtwho_configure.read(name)
        if deploy_type == "id":
            command = values['deploy']['command']
            deploy_configure_by_command(
                command,
                form_data['hypervisor_type'],
                debug=True,
                org=module_sca_manifest_org.label,
            )
        elif deploy_type == "script":
            script = values['deploy']['script']
            deploy_configure_by_script(
                script,
                form_data['hypervisor_type'],
                debug=True,
                org=module_sca_manifest_org.label,
            )
        assert session_sca.virtwho_configure.search(name)[0]['Status'] == 'ok'

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(
        self, module_sca_manifest_org, virtwho_config, session_sca, form_data
    ):
        """Verify Hypervisor ID dropdown options.

        :id: 98fbd3e4-339f-459d-95dd-f0dbbca56dcd

        :expectedresults:
            1. hypervisor_id can be changed in virt-who-config-{}.conf if the
                dropdown option is selected to uuid/hwuuid/hostname.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = form_data['name']
        config_id = get_configure_id(name)
        config_command = get_configure_command(config_id, module_sca_manifest_org.name)
        config_file = get_configure_file(config_id)
        values = ['uuid', 'hostname']
        for value in values:
            session_sca.virtwho_configure.edit(name, {'hypervisor_id': value})
            results = session_sca.virtwho_configure.read(name)
            assert results['overview']['hypervisor_id'] == value
            deploy_configure_by_command(
                config_command, form_data['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('hypervisor_id', config_file) == value
