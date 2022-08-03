"""Utility module to handle the rhsso-satellite configure UI/CLI/API testing"""
import json
import random
from contextlib import contextmanager

from fauxfactory import gen_string
from pexpect import pxssh

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.config import settings
from robottelo.constants import KEY_CLOAK_CLI
from robottelo.constants import RHSSO_NEW_GROUP
from robottelo.constants import RHSSO_NEW_USER
from robottelo.constants import RHSSO_RESET_PASSWORD
from robottelo.constants import RHSSO_USER_UPDATE
from robottelo.datafactory import valid_emails_list


def run_command(cmd, hostname=None, timeout=None):
    """helper function for ssh command and avoiding the return code check in called function"""
    hostname = hostname or settings.server.hostname
    if timeout:
        result = ssh.command(cmd=cmd, hostname=hostname, timeout=timeout)
    else:
        result = ssh.command(cmd=cmd, hostname=hostname)
    if result.status != 0:
        raise CLIReturnCodeError(
            result.status,
            result.stderr,
            f"Failed to run the command : {cmd}",
        )
    else:
        return result.stdout


def get_rhsso_client_id(sat):
    """Getter method for fetching the client id and can be used other functions"""
    client_name = f'{sat.hostname}-foreman-openidc'
    run_command(
        cmd='{} config credentials '
        '--server {}/auth '
        '--realm {} '
        '--user {} '
        '--password {}'.format(
            KEY_CLOAK_CLI,
            settings.rhsso.host_url.replace('https://', 'http://'),
            settings.rhsso.realm,
            settings.rhsso.rhsso_user,
            settings.rhsso.rhsso_password,
        ),
        hostname=settings.rhsso.host_name,
    )

    result = run_command(
        cmd=f'{KEY_CLOAK_CLI} get clients --fields id,clientId',
        hostname=settings.rhsso.host_name,
    )
    result_json = json.loads(result)
    client_id = None
    for client in result_json:
        if client_name in client['clientId']:
            client_id = client['id']
            break
    return client_id


def get_rhsso_user_details(username):
    """Getter method to receive the user id"""
    result = run_command(
        cmd=f"{KEY_CLOAK_CLI} get users -r {settings.rhsso.realm} -q username={username}",
        hostname=settings.rhsso.host_name,
    )
    result_json = json.loads(result)
    return result_json[0]


def get_rhsso_groups_details(group_name):
    """Getter method to receive the group id"""
    result = run_command(
        cmd=f"{KEY_CLOAK_CLI} get groups -r {settings.rhsso.realm} -q group_name={group_name}",
        hostname=settings.rhsso.host_name,
    )
    result_json = json.loads(result)
    return result_json[0]


def upload_rhsso_entity(json_content, entity_name):
    """Helper method upload the entity json request as file on RHSSO Server"""
    with open(entity_name, "w") as file:
        json.dump(json_content, file)
    ssh.get_client(hostname=settings.rhsso.host_name).put(entity_name)


def create_mapper(json_content, client_id):
    """Helper method to create the RH-SSO Client Mapper"""
    upload_rhsso_entity(json_content, "mapper_file")
    run_command(
        cmd="{} create clients/{}/protocol-mappers/models -r {} -f {}".format(
            KEY_CLOAK_CLI, client_id, settings.rhsso.realm, "mapper_file"
        ),
        hostname=settings.rhsso.host_name,
    )


def create_new_rhsso_user(client_id, username=None):
    """create new user in RHSSO instance and set the password"""
    if not username:
        username = gen_string('alphanumeric')
    RHSSO_NEW_USER['username'] = username
    RHSSO_NEW_USER['email'] = random.choice(valid_emails_list())
    RHSSO_RESET_PASSWORD['value'] = settings.rhsso.rhsso_password
    upload_rhsso_entity(RHSSO_NEW_USER, "create_user")
    upload_rhsso_entity(RHSSO_RESET_PASSWORD, "reset_password")
    run_command(
        cmd=f"{KEY_CLOAK_CLI} create users -r {settings.rhsso.realm} -f create_user",
        hostname=settings.rhsso.host_name,
    )
    user_details = get_rhsso_user_details(RHSSO_NEW_USER['username'])
    run_command(
        cmd="{} update -r {} users/{}/reset-password -f {}".format(
            KEY_CLOAK_CLI, settings.rhsso.realm, user_details['id'], "reset_password"
        ),
        hostname=settings.rhsso.host_name,
    )
    return RHSSO_NEW_USER


def update_rhsso_user(username, group_name=None):
    user_details = get_rhsso_user_details(username)
    RHSSO_USER_UPDATE['realm'] = f"{settings.rhsso.realm}"
    RHSSO_USER_UPDATE['userId'] = f"{user_details['id']}"
    if group_name:
        group_details = get_rhsso_groups_details(group_name=group_name)
        RHSSO_USER_UPDATE['groupId'] = f"{group_details['id']}"
        upload_rhsso_entity(RHSSO_USER_UPDATE, "update_user")
        group_path = f"users/{user_details['id']}/groups/{group_details['id']}"
        run_command(
            cmd=f"{KEY_CLOAK_CLI} update -r {settings.rhsso.realm} {group_path} -f update_user",
            hostname=settings.rhsso.host_name,
        )


def delete_rhsso_user(username):
    """Delete the RHSSO user"""
    user_details = get_rhsso_user_details(username)
    run_command(
        cmd=f"{KEY_CLOAK_CLI} delete -r {settings.rhsso.realm} users/{user_details['id']}",
        hostname=settings.rhsso.host_name,
    )


def create_group(group_name=None):
    """Create the RHSSO group"""
    if not group_name:
        group_name = gen_string('alphanumeric')
    RHSSO_NEW_GROUP['name'] = group_name
    upload_rhsso_entity(RHSSO_NEW_GROUP, "create_group")
    result = run_command(
        cmd=f"{KEY_CLOAK_CLI} create groups -r {settings.rhsso.realm} -f create_group",
        hostname=settings.rhsso.host_name,
    )
    return result


def delete_rhsso_group(group_name):
    """Delete the RHSSO group"""
    group_details = get_rhsso_groups_details(group_name)
    run_command(
        cmd=f"{KEY_CLOAK_CLI} delete -r {settings.rhsso.realm} groups/{group_details['id']}",
        hostname=settings.rhsso.host_name,
    )


def update_client_configuration(sat, json_content):
    """Update the client configuration"""
    client_id = get_rhsso_client_id(sat)
    upload_rhsso_entity(json_content, "update_client_info")
    update_cmd = (
        f"{KEY_CLOAK_CLI} update clients/{client_id} -f update_client_info -s enabled=true --merge"
    )
    run_command(cmd=update_cmd, hostname=settings.rhsso.host_name)


def get_oidc_token_endpoint():
    """getter oidc token endpoint"""
    return (
        f"https://{settings.rhsso.host_name}/auth/realms/"
        f"{settings.rhsso.realm}/protocol/openid-connect/token"
    )


def get_oidc_client_id(sat):
    """getter for the oidc client_id"""
    return f"{sat.hostname}-foreman-openidc"


def get_oidc_authorization_endpoint():
    """getter for the oidc authorization endpoint"""
    return (
        f"https://{settings.rhsso.host_name}/auth/realms/"
        f"{settings.rhsso.realm}/protocol/openid-connect/auth"
    )


def get_two_factor_token_rh_sso_url(sat):
    """getter for the two factor token rh_sso url"""
    return (
        f"https://{settings.rhsso.host_name}/auth/realms/"
        f"{settings.rhsso.realm}/protocol/openid-connect/"
        f"auth?response_type=code&client_id={sat.hostname}-foreman-openidc&"
        f"redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=openid"
    )


@contextmanager
def open_pxssh_session(
    ssh_key=settings.server.ssh_key,
    hostname=settings.server.get('hostname', None),
    username=settings.server.ssh_username,
):
    ssh_options = {'IdentityAgent': ssh_key}
    ssh_session = pxssh.pxssh(options=ssh_options)
    ssh_session.login(hostname, username, sync_multiplier=5)
    yield ssh_session
    ssh_session.logout()


def set_the_redirect_uri(sat):
    client_config = {
        "redirectUris": [
            "urn:ietf:wg:oauth:2.0:oob",
            f"https://{sat.hostname}/users/extlogin/redirect_uri",
            f"https://{sat.hostname}/users/extlogin",
        ]
    }
    update_client_configuration(sat, client_config)
