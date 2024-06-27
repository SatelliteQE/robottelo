"""Test class for Fact  UI

:Requirement: Fact

:CaseAutomation: Automated

:CaseComponent: Fact

:Team: Rocket

:CaseImportance: High

"""

import pytest

from robottelo.config import settings


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_upload_host_facts(
    module_target_sat,
    rhel_contenthost,
    module_entitlement_manifest_org,
    module_location,
    module_activation_key,
):
    """Verify Facts option is available on the Host UI and it is successfully updated in Satellite after registration

    :id: f32093d2-4088-4025-9623-adb3141bd770

    :steps:
        1. Register host to Satellite.
        2. Navigate to the Host page and click on kebab.
        3. Verify that the facts option is available and is updated on Satellite.

    :expectedresults: Facts option is available on the Host UI and all the facts of the host are updated in Satellite.

    :BZ: 2001552

    :customerscenario: true
    """
    with module_target_sat.ui_session() as session:
        session.organization.select(module_entitlement_manifest_org.name)
        session.location.select(module_location.name)
        cmd = session.host.get_register_command(
            {
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
            }
        )
        result = rhel_contenthost.execute(cmd)
        assert result.status == 0, f'Failed to register host: {result.stderr}'

        rhel_contenthost.execute('subscription-manager facts --update')
        host_facts = session.host_new.get_host_facts(rhel_contenthost.hostname, fact='network')
        assert host_facts is not None
        assert rhel_contenthost.hostname in [
            var['Value'] for var in host_facts if var['Name'] == 'networkfqdn'
        ]
