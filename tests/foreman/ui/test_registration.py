"""Tests for registration.

:Requirement: Registration

:CaseComponent: Registration

:CaseAutomation: Automated

:CaseImportance: Critical

:Team: Rocket
"""
import pytest

from robottelo.utils.datafactory import gen_string


def test_positive_verify_default_values_for_global_registration(
    module_target_sat,
    default_org,
    default_os,
):
    """Check for all the Default values pre-populated in the global registration template

    :id: 34122bf3-ae23-47ca-ba3d-da0653d8fd33

    :expectedresults: Default fields in the form should be auto-populated
        e.g. organization, location, rex, insights setup, etc

    :steps:
        1. Check for the default values in the global registration template
    """
    ak = module_target_sat.cli_factory.make_activation_key(
        {'organization-id': default_org.id, 'name': gen_string('alpha')}
    )
    with module_target_sat.ui_session() as session:
        cmd = session.host.get_register_command(
            {'general.activation_keys': ak.name, 'general.operating_system': default_os.title},
            full_read=True,
        )
    assert cmd['general']['organization'] == 'Default Organization'
    assert cmd['general']['location'] == 'Default Location'
    assert cmd['general']['capsule'] == 'Nothing to select.'
    assert cmd['general']['operating_system'] == default_os.title
    assert cmd['general']['host_group'] == 'Nothing to select.'
    assert cmd['general']['insecure'] is False
    assert cmd['general']['activation_keys'][0] == ak.name
    assert cmd['advanced']['setup_rex'] == 'Inherit from host parameter (yes)'
    assert cmd['advanced']['setup_insights'] == 'Inherit from host parameter (yes)'
    assert cmd['advanced']['token_life_time'] == '4'
    assert cmd['advanced']['rex_pull_mode'] == 'Inherit from host parameter (no)'
    assert cmd['advanced']['update_packages'] is False
    assert cmd['advanced']['ignore_error'] is False
    assert cmd['advanced']['force'] is False


@pytest.mark.tier2
def test_positive_org_loc_change_for_registration(
    module_activation_key,
    module_org,
    module_location,
    target_sat,
    default_os,
):
    """Changing the organization and location to check if correct org and loc is updated on the global registration page as well as in the command

    :id: e83ed6bc-ceae-4021-87fe-3ecde1cbf347

    :expectedresults: organization and location is updated correctly on the global registration page as well as in the command.

    :CaseImportance: Medium
    """
    new_org = target_sat.api.Organization().create()
    new_loc = target_sat.api.Location().create()
    new_ak = target_sat.api.ActivationKey(organization=new_org).create()
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        cmd = session.host.get_register_command(
            {
                'general.activation_keys': module_activation_key.name,
                'general.operating_system': default_os.title,
            }
        )
        expected_pairs = [
            f'organization_id={module_org.id}',
            f'location_id={module_location.id}',
        ]
        for pair in expected_pairs:
            assert pair in cmd
        # changing the org and loc to check if correct org and loc is updated on the registration command
        session.organization.select(org_name=new_org.name)
        session.location.select(loc_name=new_loc.name)
        cmd = session.host.get_register_command(
            {
                'general.activation_keys': new_ak.name,
                'general.operating_system': default_os.title,
            }
        )
        expected_pairs = [
            f'organization_id={new_org.id}',
            f'location_id={new_loc.id}',
        ]
        for pair in expected_pairs:
            assert pair in cmd
