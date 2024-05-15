"""Test for ProvisioningTemplates related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: ProvisioningTemplates

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings

provisioning_template_kinds = ['provision', 'PXEGrub', 'PXEGrub2', 'PXELinux', 'iPXE']


class TestScenarioPositiveProvisioningTemplates:
    """Provisioning Templates can be rendered correctly on host created in previous and upgraded versions

    :steps:
        1. Create host on Satellite and trying rendering provisioning templates
        2. Upgrade the Satellite to the next or latest version.
        3. After the upgrade, verify provisioning templates can be rendered on existing host
        4. Create host on upgraded Satellite and trying rendering provisioning templates.

    :expectedresults:
        1. Provisioning templates for host are able to render in previous and upgraded versions
    """

    @pytest.mark.pre_upgrade
    @pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
    def test_pre_scenario_provisioning_templates(
        self,
        module_target_sat,
        module_org,
        module_location,
        default_os,
        default_domain,
        default_architecture,
        default_partitiontable,
        pxe_loader,
        save_test_data,
    ):
        """Verify Host created Read the Provision template

        :id: preupgrade-3f338475-fa69-43ef-ac86-f00f4d324b21

        :steps:
            1. Create host on Satellite and trying rendering provisioning templates

        :expectedresults:
            1. Provisioning templates for host are able to render in before upgrading to new version

        :parametrized: yes
        """
        host = module_target_sat.api.Host(
            organization=module_org,
            location=module_location,
            name=gen_string('alpha'),
            operatingsystem=default_os,
            architecture=default_architecture,
            domain=default_domain,
            root_pass=settings.provisioning.host_root_password,
            ptable=default_partitiontable,
            pxe_loader=pxe_loader.pxe_loader,
        ).create()

        for kind in provisioning_template_kinds:
            assert host.read_template(data={'template_kind': kind})

        save_test_data(
            {
                'provision_host_id': host.id,
                'pxe_loader': pxe_loader.pxe_loader,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_provisioning_templates)
    @pytest.mark.parametrize('pre_upgrade_data', ['bios', 'uefi'], indirect=True)
    def test_post_scenario_provisioning_templates(
        self,
        request,
        pre_upgrade_data,
        module_target_sat,
    ):
        """Host provisioned using pre-upgrade GCE CR

        :id: postupgrade-ef82143d-efef-49b2-9702-93d67ef6805e

        :steps:
            1. Postupgrade, verify provisioning templates rendering for host
            2. Create a new host on Satellite and try rendering provisioning templates

        :expectedresults:
            1. Provisioning templates for existing and new host are able to render.

        :parametrized: yes
        """
        pxe_loader = pre_upgrade_data.pxe_loader
        pre_upgrade_host = module_target_sat.api.Host().search(
            query={'search': f'id={pre_upgrade_data.provision_host_id}'}
        )[0]
        request.addfinalizer(pre_upgrade_host.delete)
        org = module_target_sat.api.Organization(id=pre_upgrade_host.organization.id).read()
        loc = module_target_sat.api.Location(id=pre_upgrade_host.location.id).read()
        domain = module_target_sat.api.Domain(id=pre_upgrade_host.domain.id).read()
        architecture = module_target_sat.api.Architecture(
            id=pre_upgrade_host.architecture.id
        ).read()
        os = module_target_sat.api.OperatingSystem(id=pre_upgrade_host.operatingsystem.id).read()
        ptable = module_target_sat.api.PartitionTable(id=pre_upgrade_host.ptable.id).read()

        for kind in provisioning_template_kinds:
            assert pre_upgrade_host.read_template(data={'template_kind': kind})

        new_host_name = gen_string('alpha')
        new_host = module_target_sat.api.Host(
            name=new_host_name,
            organization=org,
            location=loc,
            architecture=architecture,
            domain=domain,
            operatingsystem=os,
            ptable=ptable,
            root_pass=settings.provisioning.host_root_password,
            pxe_loader=pxe_loader,
        ).create()
        request.addfinalizer(new_host.delete)

        for kind in provisioning_template_kinds:
            assert new_host.read_template(data={'template_kind': kind})
