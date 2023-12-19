"""Tests for registration.

:Requirement: Registration

:CaseLevel: Acceptance

:CaseComponent: Registration

:CaseAutomation: Automated

:CaseImportance: Critical

:Team: Rocket

:TestType: Functional

:Upstream: No
"""
from robottelo.utils.datafactory import gen_string


def test_positive_verify_default_values_for_global_registration(
    module_target_sat,
    default_org,
):
    """Check for all the Default values pre-populated in the global registration template

    :id: 34122bf3-ae23-47ca-ba3d-da0653d8fd33

    :expectedresults: Default fields in the form should be auto-populated
        e.g. organization, location, rex, insights setup, etc

    :CaseLevel: Component

    :steps:
        1. Check for the default values in the global registration template
    """
    module_target_sat.cli_factory.make_activation_key(
        {'organization-id': default_org.id, 'name': gen_string('alpha')}
    )
    with module_target_sat.ui_session() as session:
        cmd = session.host.get_register_command(
            full_read=True,
        )
    assert cmd['general']['organization'] == 'Default Organization'
    assert cmd['general']['location'] == 'Default Location'
    assert cmd['general']['capsule'] == 'Nothing to select.'
    assert cmd['advanced']['setup_rex'] == 'Inherit from host parameter (yes)'
    assert cmd['advanced']['setup_insights'] == 'Inherit from host parameter (yes)'
    assert cmd['advanced']['token_life_time'] == '4'
    assert cmd['advanced']['rex_pull_mode'] == 'Inherit from host parameter (no)'
    assert cmd['advanced']['update_packages'] is False
    assert cmd['advanced']['ignore_error'] is False
    assert cmd['advanced']['force'] is False
