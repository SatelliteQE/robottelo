"""Flatpak related tests being run through UI.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""


def test_flatpak_remotes(target_sat, function_org, function_flatpak_remote):
    """Ensure Flatpak Remotes are displayed correctly.

    :id: c757094c-e817-4a1b-a8b3-d2ce3f9d6b0e

    :setup:
        1. Create a flatpak remote in an Organization and scan it.

    :steps:
        1. Select the Organization owning the remote.
        2. Navigate to Flatpak Remotes page and read the table.

    :expectedresults:
        1. The remote is displayed correctly.

    """
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        remotes = session.flatpak_remotes.read_table()
        assert len(remotes) == 1
        remote = remotes[0]
        assert remote['Name'] == function_flatpak_remote.remote.name
        assert remote['URL'] == function_flatpak_remote.remote.flatpak_index_url
