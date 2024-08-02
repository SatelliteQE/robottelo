"""Tests for leapp upgrade of content hosts with Satellite

:Requirement: leapp

:CaseComponent: Leappintegration

:Team: Rocket

:CaseImportance: Critical

:CaseAutomation: Automated

"""

import pytest

RHEL7_VER = '7.9'
RHEL8_VER = '8.10'
RHEL9_VER = '9.4'


@pytest.mark.tier3
@pytest.mark.parametrize(
    'upgrade_path',
    [
        {'source_version': RHEL8_VER, 'target_version': RHEL9_VER},
    ],
    ids=lambda upgrade_path: f'{upgrade_path["source_version"]}'
    f'_to_{upgrade_path["target_version"]}',
)
def test_leapp_preupgrade_report(
    module_target_sat,
    custom_leapp_host,
    upgrade_path,
    verify_target_repo_on_satellite,
    precondition_check_upgrade_and_install_leapp_tool,
    module_sca_manifest_org,
):
    """Test to verify leapp preupgrade report gets generated.

    :id: cbbd38a5-65bc-4491-831a-f1bfeb119d92

    :BZ: 2168494

    :Verifies: SAT-15889

    :customerscenario: true

    :steps:
        1. Import a subscription manifest and enable, sync source & target repositories
        2. Create LCE, Create CV, add repositories to it, publish and promote CV, Create AK, etc.
        3. Register content host with AK
        4. Verify that target rhel repositories are enabled on Satellite
        5. Update all packages, install leapp tool and fix inhibitors
        6. Run Leapp Preupgrade and verify report gets generated for the job.

    :expectedresults:
        1. Leapp preupgrade job is generated.
    """
    hostname = custom_leapp_host.hostname
    with module_target_sat.ui_session() as session:
        session.organization.select(module_sca_manifest_org.name)
        session.jobinvocation.run(
            {
                'category_and_template.job_category': 'Leapp - Preupgrade',
                'category_and_template.job_template': 'Run preupgrade via Leapp',
                'target_hosts_and_inputs.targetting_type': 'Hosts',
                'target_hosts_and_inputs.targets': hostname,
            }
        )
        session.jobinvocation.wait_job_invocation_state(
            entity_name='Upgradeability check for rhel host', host_name=hostname
        )
        status = session.jobinvocation.read(
            entity_name='Upgradeability check for rhel host', host_name=hostname
        )
        assert status['overview']['hosts_table'][0]['Status'] == 'success'
