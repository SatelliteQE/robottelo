"""Flatpak related tests being run through UI.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

import random
import re


def test_flatpak_remotes(target_sat, function_org, function_flatpak_remote):
    """Ensure Flatpak Remotes are displayed correctly.

    :id: c757094c-e817-4a1b-a8b3-d2ce3f9d6b0e

    :setup:
        1. Create a flatpak remote in an Organization and scan it.

    :steps:
        1. Select the Organization owning the remote.
        2. Navigate to Flatpak Remotes page and read the table.
        3. Navigate to the Flatpak Remote details page and read the details.

    :expectedresults:
        1. The remote is displayed correctly.
        2. All scanned repositories are displayed.
        3. Random repository can be searched and returns valid values.

    """
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        remotes = session.flatpak_remotes.read_table()
        assert len(remotes) == 1
        remote = remotes[0]
        assert remote['Name'] == function_flatpak_remote.remote.name
        assert remote['URL'] == function_flatpak_remote.remote.flatpak_index_url

        details = session.flatpak_remotes.read_remote_details(name=remote['Name'])
        assert details['title'] == remote['Name']
        assert details['url'] == remote['URL']
        match = re.search(r'of\s+(\d+)\s+items', details['pagination']['_items'])
        assert int(match.group(1)) == len(function_flatpak_remote.repos)

        random_repo = random.choice(function_flatpak_remote.repos)
        details = session.flatpak_remotes.read_remote_details(
            name=remote['Name'], repo_search=random_repo.name
        )
        assert len(details['table']) == 1
        assert details['table'][0]['Name'] == random_repo.name
        assert details['table'][0]['ID'] == random_repo.id
        assert details['table'][0]['Last mirrored'] == 'Never'
