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

from robottelo.config import settings
from robottelo.constants import FLATPAK_REMOTES, FLATPAK_RHEL_RELEASE_VER


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
        assert len(details['table']) == 1
        assert details['table'][0]['Name'] == random_repo.name
        assert details['table'][0]['ID'] == random_repo.id
        assert details['table'][0]['Last mirrored'] == 'Never'


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
        assert len(details['table']) == 1
        assert details['table'][0]['Name'] == repo_to_mirror

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
