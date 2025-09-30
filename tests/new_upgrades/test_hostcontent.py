"""Test Hosts-Content related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Proton

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.constants import DEFAULT_LOC
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def db_seed_host_mismatch_setup(
    content_upgrade_shared_satellite,
    rhel_contenthost,
    upgrade_action,
):
    """
    This test scenario verifies that the upgrade succeeds even when inconsistencies exist
    in the database between Organization, Location and Content Host.
    :steps:
        1. Create a Location
        2. Create an Org and ensure the Location is not in the Org
        3. Create a Content Host on Org
        4. Use rake console to assign the Content Host to the Location
        5. Ensure the mismatch is created for Content Host when Location is not in the Org
        6. Do the upgrade

    :expectedresults:
        1. The Content Host is assigned to both Location and Org, but Location is not in Org

    :BZ: 2043705, 2028786, 2019467

    :customerscenario: true
    """
    target_sat = content_upgrade_shared_satellite
    rhel_contenthost._satellite = target_sat
    with SharedResource(
        content_upgrade_shared_satellite.hostname, upgrade_action, target_sat=target_sat
    ) as sat_upgrade:
        test_name = f'content_host_upgrade_{gen_alpha(length=8)}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        default_location = target_sat.api.Location().search(
            query={'search': f'name="{DEFAULT_LOC}"'}
        )[0]
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak',
            content_view=org.default_content_view.id,
            environment=org.library.id,
            organization=org,
        ).create()
        rhel_contenthost.api_register(
            target_sat, organization=org, activation_keys=[ak.name], location=default_location.id
        )

        assert rhel_contenthost.nailgun_host.organization.id == org.id

        # Now we need to break the taxonomy between chost, org and location
        rake_host = f"host = ::Host.find({rhel_contenthost.nailgun_host.id})"
        rake_location = f"; host.location_id={location.id}"
        rake_host_save = "; host.save!"
        result = target_sat.run(
            f"echo '{rake_host}{rake_location}{rake_host_save}' | foreman-rake console"
        )

        assert 'true' in result.stdout
        assert rhel_contenthost.nailgun_host.location.id == location.id

        sat_upgrade.ready()
        test_data = Box(
            {
                'client_name': rhel_contenthost.hostname,
                'organization_id': org.id,
                'location_id': location.id,
                'target_sat': target_sat,
            }
        )
        target_sat._session = None
        yield test_data


@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
@pytest.mark.content_upgrades
def test_post_db_seed_host_mismatch(db_seed_host_mismatch_setup):
    """
    :id: 28861b9f-8abd-4efc-bfd5-40b7e825a941

    :steps:
        1. After the upgrade finishes ensure the content host data is unchanged

    :expectedresults:
        1. The upgrade succeeds and content host exists

    :BZ: 2043705, 2028786, 2019467

    :customerscenario: true
    """
    target_sat = db_seed_host_mismatch_setup.target_sat
    hostname = db_seed_host_mismatch_setup.client_name
    org_id = db_seed_host_mismatch_setup.organization_id
    loc_id = db_seed_host_mismatch_setup.location_id
    host = target_sat.api.Host().search(query={'search': hostname})

    assert org_id == host[0].organization.id
    assert loc_id == host[0].location.id
