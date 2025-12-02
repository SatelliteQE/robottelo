"""Module for tests related to the Pulp backend

:Requirement: Pulp

:CaseAutomation: Automated

:CaseComponent: Pulp

:Team: Artemis

:CaseImportance: High

"""

import json

import pytest

from robottelo.constants import PULP_HREF_PRN_MAP, PULP_PRN_TABLES


@pytest.mark.parametrize('table', PULP_PRN_TABLES, ids=lambda t: f"{t['name']}:{t['prn_key']}")
def test_pulp_href_prn_mapping(table, target_sat, module_prn_content_setup):
    """Verify Pulp HREF to PRN mapping for all relevant Katello tables, except for repo versions.

    :id: c840688e-9a80-491e-bc26-a4636d691662

    :parametrized: yes

    :setup:
        1. Specific content entities created to populate all relevant tables.

    :steps:
        1. Query database table for records with pulp_href.
        2. Extract UUID from pulp_href path.
        3. Verify pulp_prn matches expected format from PULP_HREF_PRN_MAP.

    :expectedresults:
        All pulp_prn values match the expected format based on pulp_href.

    :Verifies: SAT-37807, SAT-40415

    :BlockedBy: SAT-40415
    """
    records = target_sat.query_db(
        f'SELECT {table["href_key"]}, {table["prn_key"]} FROM {table["name"]} '
        f'WHERE {table["href_key"]} IS NOT NULL'
    )
    assert len(records), 'No records found in table, probably insufficient content setup'
    for row in records:
        base_path, uuid = row[table['href_key']].rstrip('/').rsplit('/', 1)
        assert row[table['prn_key']] == PULP_HREF_PRN_MAP.get(base_path, '') + uuid


def test_pulp_repoversion_href_prn_mapping(target_sat, module_prn_content_setup):
    """Verify Pulp HREF to PRN mapping for repository versions in katello_repositories table.

    :id: dc555f29-9218-4c7d-8f10-c46e0213baa6

    :setup:
        1. Specific content entities created to populate all relevant tables.

    :steps:
        1. Query katello_repositories table for records with version_href and version_prn.
        2. Get version details for each version_href via pulp cli.
        3. Verify the version_prn from the table matches the prn from pulp cli.

    :expectedresults:
        All version_prn values match the expected PRN from pulp cli.
    """
    records = target_sat.query_db(
        'SELECT version_href,version_prn FROM katello_repositories WHERE version_href IS NOT NULL'
    )
    assert len(records), 'No records found in table, probably insufficient content setup'
    for row in records:
        version = json.loads(target_sat.execute(f'pulp show --href {row["version_href"]}').stdout)
        assert row['version_prn'] == version['prn']
