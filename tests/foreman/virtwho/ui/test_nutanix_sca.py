"""Test class for Virtwho Configure UI

:Requirement: Virt-whoConfigurePlugin

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Virt-whoConfigurePlugin

:Team: Phoenix

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
def form_data(target_sat, module_sca_manifest_org):
    form = {
        'debug': True,
        'interval': 'Every hour',
        'hypervisor_id': 'hostname',
        'hypervisor_type': settings.virtwho.ahv.hypervisor_type,
        'hypervisor_content.server': settings.virtwho.ahv.hypervisor_server,
        'hypervisor_content.username': settings.virtwho.ahv.hypervisor_username,
        'hypervisor_content.password': settings.virtwho.ahv.hypervisor_password,
        'hypervisor_content.prism_flavor': "Prism Element",
    }
    return form


class TestVirtwhoConfigforNutanix:
    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_deploy_configure_by_id_script(
        self, module_sca_manifest_org, session_sca, form_data, deploy_type
    ):
        """Verify configure created and deployed with id.

        :id: 7ab8aa6a-1cdb-4b3b-859a-6fe8051d6568

        :expectedresults:
            1. Config can be created and deployed by command or script
            2. No error msg in /var/log/rhsm/rhsm.log
            3. Report is sent to satellite
            4. Config can be deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session_sca:
            print(form_data)
            session_sca.virtwho_configure.create(form_data)
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
            session_sca.virtwho_configure.delete(name)
            assert not session_sca.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_hypervisor_id_option(self, module_sca_manifest_org, session_sca, form_data):
        """Verify Hypervisor ID dropdown options.

        :id: 8f5771bd-4b74-49a7-93bb-31eb8e467477

        :expectedresults:
            1. hypervisor_id can be changed in virt-who-config-{}.conf if the
            2. dropdown option is selected to uuid/hwuuid/hostname.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session_sca:
            session_sca.virtwho_configure.create(form_data)
            values = session_sca.virtwho_configure.read(name)
            config_id = get_configure_id(name)
            command = values['deploy']['command']
            config_file = get_configure_file(config_id)
            for value in ['uuid', 'hostname']:
                session_sca.virtwho_configure.edit(name, {'hypervisor_id': value})
                results = session_sca.virtwho_configure.read(name)
                assert results['overview']['hypervisor_id'] == value
                deploy_configure_by_command(
                    command,
                    form_data['hypervisor_type'],
                    debug=True,
                    org=module_sca_manifest_org.label,
                )
                assert get_configure_option('hypervisor_id', config_file) == value
            session_sca.virtwho_configure.delete(name)
            assert not session_sca.virtwho_configure.search(name)

    @pytest.mark.tier2
    @pytest.mark.parametrize('deploy_type', ['id', 'script'])
    def test_positive_prism_central_deploy_configure_by_id_script(
        self, module_sca_manifest_org, session_sca, form_data, deploy_type
    ):
        """Verify configure created and deployed with id on nutanix prism central mode

        :id: 2e2cc394-b637-4bd5-8a52-9162638b1b4e

        :expectedresults:
            1. Config can be created and deployed by command or script
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
        with session_sca:
            session_sca.virtwho_configure.create(form_data)
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
            # Check the option "prism_central=true" should be set in etc/virt-who.d/virt-who.conf
            config_id = get_configure_id(name)
            config_file = get_configure_file(config_id)
            assert get_configure_option("prism_central", config_file) == 'true'
            assert session_sca.virtwho_configure.search(name)[0]['Status'] == 'ok'
            session_sca.virtwho_configure.delete(name)
            assert not session_sca.virtwho_configure.search(name)

    @pytest.mark.tier2
    def test_positive_prism_central_prism_flavor_option(
        self, module_sca_manifest_org, session_sca, form_data
    ):
        """Verify prism_flavor dropdown options.

        :id: 621abef9-3629-41ee-9977-0089a558e79b

        :expectedresults:
            1. prism_flavor can be changed in virt-who-config-{}.conf if the
            2. dropdown option is selected to prism central.

        :CaseLevel: Integration

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        form_data['name'] = name
        with session_sca:
            session_sca.virtwho_configure.create(form_data)
            results = session_sca.virtwho_configure.read(name)
            assert results['overview']['prism_flavor'] == "element"
            config_id = get_configure_id(name)
            config_command = get_configure_command(config_id, module_sca_manifest_org.name)
            config_file = get_configure_file(config_id)
            session_sca.virtwho_configure.edit(
                name, {'hypervisor_content.prism_flavor': "Prism Central"}
            )
            results = session_sca.virtwho_configure.read(name)
            assert results['overview']['prism_flavor'] == "central"
            deploy_configure_by_command(
                config_command, form_data['hypervisor_type'], org=module_sca_manifest_org.label
            )
            assert get_configure_option('prism_central', config_file) == 'true'
            session_sca.virtwho_configure.delete(name)
            assert not session_sca.virtwho_configure.search(name)
