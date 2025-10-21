"""Test for Pulp related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Pulp

:Team: Artemis

:CaseImportance: High

"""

import json

from manifester import Manifester
import pytest

from pytest_fixtures.component.pulp import _setup_prn_content
from robottelo.config import settings
from robottelo.constants import PULP_HREF_PRN_MAP, PULP_PRN_TABLES
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture(scope='module')
def pulp_upgrade_manifest():
    with Manifester(manifest_category=settings.manifest.golden_ticket) as manifest:
        yield manifest


@pytest.fixture(scope='module')
def pulp_upgrade_setup(pulp_upgrade_shared_satellite, upgrade_action, pulp_upgrade_manifest):
    """Fixture to set up content entities to properly test pulp HREF to PRN mapping."""
    target_sat = pulp_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = _setup_prn_content(
            target_sat, pulp_upgrade_manifest, test_name='pulp_href_prn_migration'
        )
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.pulp_upgrades
@pytest.mark.parametrize('table', PULP_PRN_TABLES, ids=lambda t: f"{t['name']}:{t['prn_key']}")
def test_pulp_href_prn_migration_scenario(pulp_upgrade_setup, table):
    """Verify Pulp HREF to PRN migration for all relevant Katello tables, except for repo versions.

    :id: postupgrade-8306165e-7666-43c7-911f-75c803c20e45

    :parametrized: yes

    :setup:
        1. Specific content entities created before upgrade to populate all relevant tables.

    :steps:
        1. Query database table for records with pulp_href.
        2. Extract UUID from pulp_href path.
        3. Verify pulp_prn matches expected format from PULP_HREF_PRN_MAP.

    :expectedresults:
        All pulp_prn values match the expected format based on pulp_href after upgrade.
    """
    target_sat = pulp_upgrade_setup.target_sat

    records = target_sat.query_db(
        f'SELECT {table["href_key"]}, {table["prn_key"]} FROM {table["name"]} '
        f'WHERE {table["href_key"]} IS NOT NULL'
    )
    assert len(records), 'No records found in table, probably insufficient content setup'
    for row in records:
        base_path, uuid = row[table['href_key']].rstrip('/').rsplit('/', 1)
        assert row[table['prn_key']] == PULP_HREF_PRN_MAP.get(base_path, '') + uuid


def test_pulp_repoversion_href_prn_migration_scenario(pulp_upgrade_setup):
    """Verify Pulp HREF to PRN migration for repository versions in katello_repositories table.

    :id: 0cc9ebf7-dff5-4fa0-892b-90a46ad1e800

    :setup:
        1. Specific content entities created to populate all relevant tables.

    :steps:
        1. Query katello_repositories table for records with version_href and version_prn.
        2. Get version details for each version_href via pulp cli.
        3. Verify the version_prn from the table matches the prn from pulp cli.

    :expectedresults:
        All version_prn values match the expected PRN from pulp cli.
    """
    target_sat = pulp_upgrade_setup.target_sat

    records = target_sat.query_db(
        'SELECT version_href,version_prn FROM katello_repositories WHERE version_href IS NOT NULL'
    )
    assert len(records), 'No records found in table, probably insufficient content setup'
    for row in records:
        version = json.loads(target_sat.execute(f'pulp show --href {row["version_href"]}').stdout)
        assert row['version_prn'] == version['prn']
