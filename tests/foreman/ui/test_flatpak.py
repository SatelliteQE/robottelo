"""Flatpak related tests being run through UI.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Artemis

:CaseImportance: High

"""

import random
import re

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import FLATPAK_REMOTES, FLATPAK_RHEL_RELEASE_VER
from robottelo.logging import logger


def test_view_flatpak_remotes(target_sat, function_org, function_flatpak_remote):
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
        # search for "of X items" in pagination to ensure all scanned repos are available
        match = re.search(r'of\s+(\d+)\s+items', details['pagination']['_items'])
        assert int(match.group(1)) == len(function_flatpak_remote.repos)

        random_repo = random.choice(function_flatpak_remote.repos)
        details = session.flatpak_remotes.read_remote_details(
            name=remote['Name'], repo_search=random_repo.name
        )
        # Search can return multiple results due to partial matching (e.g., searching "kicad"
        # returns both "org.kicad.kicad" and "org.kicad.kicad.Library")
        assert len(details['table']) > 0
        matching_rows = [row for row in details['table'] if row['Name'] == random_repo.name]
        assert len(matching_rows) == 1
        assert matching_rows[0]['Name'] == random_repo.name
        assert matching_rows[0]['ID'] == random_repo.id
        assert matching_rows[0]['Last mirrored'] == 'Never'
        assert not details['last_scan_words_text']
        assert not details['last_scan_text']


def test_CRUD_scan_and_mirror_flatpak_remote(target_sat, function_org, function_product):
    """Exercise the basic CRUD, Scan and Mirror actions via UI.

    :id: e82f7bbd-15fe-4c04-b772-cdb9fe91506a

    :setup:
        1. Create an Organization with a Product within.

    :steps:
        1. Create, read, update, scan, mirror and delete the flatpak remote via UI.

    :expectedresults:
        1. All CRUD, scan and mirror operations work via UI properly.

    """
    init_name = gen_string('alpha')
    init_url = 'https://some.fakeurl.com'
    fr_name = gen_string('alpha')
    repo_to_mirror = f'rhel{FLATPAK_RHEL_RELEASE_VER}/flatpak-runtime'
    logger.info(f"{repo_to_mirror=}")

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)

        # Create
        session.flatpak_remotes.create(
            {
                'name': init_name,
                'url': init_url,
                'username': 'wrong_user',
                'password': 'wrong_pass',
            },
        )

        # Read
        remotes = session.flatpak_remotes.read_table()
        assert len(remotes) == 1
        remote = remotes[0]
        assert remote['Name'] == init_name
        assert remote['URL'] == init_url

        # Update
        session.flatpak_remotes.edit(
            init_name,
            {
                'name': fr_name,
                'url': FLATPAK_REMOTES['RedHat']['url'],
                'username': settings.container_repo.registries.redhat.username,
                'password': settings.container_repo.registries.redhat.password,
            },
        )
        details = session.flatpak_remotes.read_remote_details(name=fr_name)
        assert details['title'] == fr_name
        assert details['url'] == FLATPAK_REMOTES['RedHat']['url']

        # Scan
        session.flatpak_remotes.scan(fr_name)
        target_sat.wait_for_tasks(
            search_query='Actions::Katello::Flatpak::ScanRemote',
            max_tries=5,
            search_rate=5,
            poll_rate=10,
            poll_timeout=30,
        )
        details = session.flatpak_remotes.read_remote_details(
            name=fr_name, repo_search=repo_to_mirror
        )
        logger.info(f"{details=}")
        assert len(details['table']) == 1
        assert details['table'][0]['Name'] == repo_to_mirror
        assert 'ago' in details['last_scan_words_text']
        assert details['last_scan_text']

        # Mirror
        session.flatpak_remotes.mirror(
            remote=fr_name, repo=repo_to_mirror, product=function_product
        )
        target_sat.wait_for_tasks(
            search_query='Actions::Katello::Flatpak::MirrorRemoteRepository',
            max_tries=5,
            search_rate=5,
            poll_rate=10,
            poll_timeout=30,
        )
        details = session.flatpak_remotes.read_remote_details(
            name=fr_name, repo_search=repo_to_mirror
        )
        assert len(details['table']) == 1
        assert 'minute ago' in details['table'][0]['Last mirrored']

        # Delete
        session.flatpak_remotes.delete(fr_name)
        remotes = session.flatpak_remotes.read()
        assert 'no_results' in remotes
        assert 'No Results' in str(remotes['table'])


def test_rh_flatpak_remote_info_alert(target_sat, function_org):
    """Test correct information and function of the Red Hat Flatpak remote banner.

    :id: b12d8f10-c496-44ad-bf20-f1e6cd32e522

    :setup:
        1. Create a new Organization.

    :steps:
        1. Open Create Flatpak Remote modal, ensure correct information is displayed.
        2. Create Red Hat flatpak remote using shortcut button, ensure correct link is used.
        3. Open Create Flatpak Remote modal again, ensure the information alert is not displayed.

    :expectedresults:
        1. Create Flatpak Remote modal shows info alert with correct information.
        2. The shortcut button provides correct link to Red Hat flatpak registry.
        3. No info alert is displayed when RH Flatpak Remote already exists.

    :verifies: SAT-36751
    """
    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)

        # Open Create Flatpak Remote modal, ensure correct information is displayed.
        rh_info = session.flatpak_remotes.read_create_modal_alert()
        assert rh_info
        assert 'Add Red Hat Flatpak remote' in rh_info['title']
        assert (
            'To continue with Red Hat Flatpak remote, you need to generate your username and password in access.redhat.com/terms-based-registry/'
            in rh_info['body']
        )

        # Create Red Hat flatpak remote using shortcut button, ensure correct link is used.
        session.flatpak_remotes.create_redhat_remote({'name': gen_string('alpha')})
        remotes = session.flatpak_remotes.read_table()
        assert len(remotes) == 1
        assert remotes[0]['URL'] in FLATPAK_REMOTES['RedHat']['url']

        # Open Create Flatpak Remote modal again, ensure the information alert is not displayed.
        rh_info = session.flatpak_remotes.read_create_modal_alert()
        assert not rh_info


@pytest.mark.parametrize('function_flatpak_remote', ['RedHat'], indirect=True)
def test_rh_flatpak_mirror_repo_dependancy_alert(
    target_sat, function_org, function_product, function_flatpak_remote
):
    """Verify dependency detection in the Flatpak mirror modal.

    :id: 1f4d8a0a-1a67-4ac6-98c3-0ac8d787b419

    :setup:
        1. Create a Red Hat flatpak remote in an Organization and scan it.

    :steps:
        1. Navigate to Flatpak Remotes and open a remote repository with dependencies.
        2. Open the Mirror modal and verify the dependency alert and checkboxes.
        3. Select dependency repositories, choose a product, and mirror.
        4. Verify a toast indicates mirroring with dependencies started.
        5. Verify the main repository and selected dependencies are mirrored.

    :expectedresults:
        1. Dependency alert is displayed with dependency checkboxes.
        2. Mirroring starts with dependencies included.
        3. Selected repositories are mirrored into the chosen product.

    :verifies: SAT-28473
    """
    candidate_repos = [
        repo
        for repo in function_flatpak_remote.repos
        if 'flatpak' in repo.name and 'runtime' not in repo.name and 'sdk' not in repo.name
    ]
    assert candidate_repos, 'No flatpak app repositories found to mirror'

    with target_sat.ui_session() as session:
        session.organization.select(function_org.name)
        mirror_modal = None
        dependency_info = None
        app_repo = None
        for repo in candidate_repos:
            mirror_modal = session.flatpak_remotes.open_mirror_modal(
                remote=function_flatpak_remote.remote.name,
                repo=repo.name,
            )
            dependency_info = session.flatpak_remotes.read_mirror_dependency_alert(mirror_modal)
            if not dependency_info:
                mirror_modal.searchbar.fill(function_product.name)
                session.browser.plugin.ensure_page_safe()
                dependency_info = session.flatpak_remotes.read_mirror_dependency_alert(mirror_modal)
            if dependency_info:
                app_repo = repo
                break
            mirror_modal.cancel_btn.click()
            session.browser.plugin.ensure_page_safe()
        assert dependency_info, (
            'No dependency alert displayed for candidate repos: '
            f'{", ".join(repo.name for repo in candidate_repos)}'
        )
        assert 'Dependency found' in dependency_info['title']
        assert 'Ensure the runtime dependency' in dependency_info['body']
        assert dependency_info['dependencies']

        dependencies_to_mirror = dependency_info['dependencies'][:1]
        details_view = session.flatpak_remotes.submit_mirror_modal(
            mirror_modal=mirror_modal,
            product=function_product,
            dependencies=dependencies_to_mirror,
        )
        expected_toast = 'Mirroring flatpak repository with dependencies has started'

        wait_for(
            lambda: any(expected_toast in msg.text for msg in details_view.flash.messages()),
            timeout=30,
            delay=2,
            handle_exception=True,
        )
        assert any(expected_toast in msg.text for msg in details_view.flash.messages())

        target_sat.wait_for_tasks(
            search_query='Actions::Katello::Flatpak::MirrorRemoteRepository',
            max_tries=5,
            search_rate=5,
            poll_rate=10,
            poll_timeout=30,
        )
        for repo_name in [app_repo.name, *dependencies_to_mirror]:
            details = session.flatpak_remotes.read_remote_details(
                name=function_flatpak_remote.remote.name, repo_search=repo_name
            )
            assert len(details['table']) == 1
            assert details['table'][0]['Name'] == repo_name
            assert details['table'][0]['Last mirrored'] != 'Never'
