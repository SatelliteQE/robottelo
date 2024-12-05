"""Flatpak related tests being run through CLI.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

import pytest
import requests

from robottelo.config import settings
from robottelo.constants import FLATPAK_REMOTES
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import gen_string


@pytest.fixture
def function_role(target_sat):
    """An empty Role, no permissions"""
    role = target_sat.api.Role().create()
    yield role
    role.delete()


@pytest.fixture
def function_user(target_sat, function_role, function_org):
    """Non-admin user with an empty role assigned."""
    password = gen_string('alphanumeric')
    user = target_sat.api.User(
        login=gen_string('alpha'),
        password=password,
        role=[function_role],
        organization=[function_org],
    ).create()
    user.password = password
    yield user
    user.delete()


def test_CRUD_and_sync_flatpak_remote_with_permissions(
    target_sat, function_user, function_role, function_org
):
    """Verify that Flatpak remote can be created, read, updated, scanned and deleted
        only with appropriate permissions.

    :id: 3a8df09f-49bf-498f-8d71-7c0c3b4c505d

    :setup:
        1. Non-admin user with an empty role (no permissions yet) assigned.

    :steps:
        Ensure that Flatpak remote can be
        1. listed only with proper permissions.
        2. created only with proper permissions.
        3. updated and scanned only with proper permissions.
        4. deleted only with proper permissions.

    :expectedresults:
        1. Every action succeeds only with the proper permission.
        2. The required permission is mentioned in the error message correctly.

    """
    emsg = 'Missing one of the required permissions: {}'
    usr, pwd = function_user.login, function_user.password

    # 1. Ensure that remotes can be listed only with proper permissions.
    p = 'view_flatpak_remotes'
    with pytest.raises(CLIReturnCodeError) as e:
        target_sat.cli.FlatpakRemote().with_user(usr, pwd).list()
    assert emsg.format(p) in str(e)

    target_sat.api_factory.create_role_permissions(function_role, {'Katello::FlatpakRemote': [p]})
    res = (
        target_sat.cli.FlatpakRemote()
        .with_user(usr, pwd)
        .list({'organization-id': function_org.id})
    )
    assert len(res) == 0, f'Expected no remotes yet in the {function_org.name} org, but got {res}'

    # 2. Ensure that remotes can be created only with proper permissions.
    p = 'create_flatpak_remotes'
    with pytest.raises(CLIReturnCodeError) as e:
        target_sat.cli.FlatpakRemote().with_user(usr, pwd).create(
            {
                'organization-id': function_org.id,
                'url': FLATPAK_REMOTES['Fedora']['url'],
                'name': gen_string('alpha'),
            }
        )
    assert emsg.format(p) in str(e)

    target_sat.api_factory.create_role_permissions(function_role, {'Katello::FlatpakRemote': [p]})
    remote = (
        target_sat.cli.FlatpakRemote()
        .with_user(usr, pwd)
        .create(
            {
                'organization-id': function_org.id,
                'url': FLATPAK_REMOTES['Fedora']['url'],
                'name': gen_string('alpha'),
            }
        )
    )
    res = (
        target_sat.cli.FlatpakRemote()
        .with_user(usr, pwd)
        .info({'organization-id': function_org.id, 'name': remote['name']})
    )
    assert res == remote, 'Read values differ from the created ones'

    # 3. Ensure that remotes can be updated and scanned only with proper permissions.
    p = 'edit_flatpak_remotes'
    desc = gen_string('alpha')
    with pytest.raises(CLIReturnCodeError) as e:
        target_sat.cli.FlatpakRemote().with_user(usr, pwd).update(
            {'organization-id': function_org.id, 'name': remote['name'], 'description': desc}
        )
    assert emsg.format(p) in str(e)
    with pytest.raises(CLIReturnCodeError) as e:
        target_sat.cli.FlatpakRemote().with_user(usr, pwd).scan({'name': remote['name']})
    assert emsg.format(p) in str(e)

    target_sat.api_factory.create_role_permissions(function_role, {'Katello::FlatpakRemote': [p]})
    target_sat.cli.FlatpakRemote().with_user(usr, pwd).update(
        {'organization-id': function_org.id, 'name': remote['name'], 'description': desc}
    )
    target_sat.cli.FlatpakRemote().with_user(usr, pwd).scan({'name': remote['name']})
    res = (
        target_sat.cli.FlatpakRemote()
        .with_user(usr, pwd)
        .info({'organization-id': function_org.id, 'name': remote['name']})
    )
    assert res['description'] == desc, 'Description was not updated'
    assert 'http' in res['registry-url'], 'Scan of flatpak remote failed'

    # 4. Ensure that remotes can be deleted only with proper permissions.
    p = 'destroy_flatpak_remotes'
    with pytest.raises(CLIReturnCodeError) as e:
        target_sat.cli.FlatpakRemote().with_user(usr, pwd).delete({'name': remote['name']})
    assert emsg.format(p) in str(e)

    target_sat.api_factory.create_role_permissions(function_role, {'Katello::FlatpakRemote': [p]})
    res = target_sat.cli.FlatpakRemote().with_user(usr, pwd).delete({'name': remote['name']})
    assert 'Flatpak Remote deleted' in res
    with pytest.raises(CLIReturnCodeError) as e:
        target_sat.cli.FlatpakRemote().with_user(usr, pwd).info({'name': remote['name']})
    assert 'Error: flatpak_remote not found' in str(e)


@pytest.mark.parametrize('remote', FLATPAK_REMOTES.values(), ids=FLATPAK_REMOTES)
def test_scan_flatpak_remote(target_sat, function_org, function_product, remote):
    """Verify flatpak remote scan detects all repos available in the remote index.

    :id: 3dff23f3-f415-4fb2-a41c-7cdcae617bb0

    :parametrized: yes

    :steps:
        1. Create a flatpak remote and scan it.
        2. Read the remote index via its API.
        3. Compare the scanned repos match the repos in the remote index.

    :expectedresults:
        1. Repos scanned by flatpak remote match the repos available in the remote index.

    """
    # 1. Create a flatpak remote and scan it.
    create_opts = {
        'organization-id': function_org.id,
        'url': remote['url'],
        'name': gen_string('alpha'),
    }
    if remote['authenticated']:
        create_opts['username'] = settings.container_repo.registries.redhat.username
        create_opts['token'] = settings.container_repo.registries.redhat.password

    fr = target_sat.cli.FlatpakRemote().create(create_opts)
    target_sat.cli.FlatpakRemote().scan({'id': fr['id']})

    scanned_repos = target_sat.cli.FlatpakRemote().repository_list({'flatpak-remote-id': fr['id']})
    scanned_repo_names = [item['name'] for item in scanned_repos]

    # 2. Read the remote index via its API.
    rq = requests.get(remote['index_url']).json()
    index_repo_names = [item['Name'] for item in rq['Results']]

    # 3. Compare the scanned repos match the repos in the remote index.
    assert sorted(scanned_repo_names) == sorted(index_repo_names)
