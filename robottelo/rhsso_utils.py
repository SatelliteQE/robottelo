"""Utility module to handle the rhsso-satellite configure UI/CLI/API testing"""
import json
import random

from fauxfactory import gen_string

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.config import settings
from robottelo.constants import KEY_CLOAK_CLI
from robottelo.constants import RHSSO_NEW_USER
from robottelo.constants import RHSSO_RESET_PASSWORD
from robottelo.datafactory import valid_emails_list

satellite = settings.server.hostname
rhsso_host = settings.rhsso.host_name
realm = settings.rhsso.realm
rhsso_user = settings.rhsso.rhsso_user
rhsso_password = settings.rhsso.password


def run_command(cmd, hostname=satellite, timeout=None):
    """helper function for ssh command and avoiding the return code check in called function"""
    if timeout:
        result = ssh.command(cmd=cmd, hostname=hostname, timeout=timeout)
    else:
        result = ssh.command(cmd=cmd, hostname=hostname)
    if result.return_code != 0:
        raise CLIReturnCodeError(
            result.return_code, result.stderr, f"Failed to run the command : {cmd}",
        )
    else:
        return result.stdout


def get_rhsso_client_id():
    """Getter method for fetching the client id and can be used other functions"""
    client_name = f"{satellite}-foreman-openidc"
    run_command(
        cmd="{0} config credentials "
        "--server {1}/auth "
        "--realm {2} "
        "--user {3} "
        "--password {4}".format(
            KEY_CLOAK_CLI,
            settings.rhsso.host_url.replace("https://", "http://"),
            realm,
            rhsso_user,
            rhsso_password,
        ),
        hostname=rhsso_host,
    )

    result = run_command(
        cmd=f"{KEY_CLOAK_CLI} get clients --fields id,clientId", hostname=rhsso_host,
    )
    result_json = json.loads("[{{{0}".format("".join(result)))
    client_id = None
    for client in result_json:
        if client_name in client['clientId']:
            client_id = client['id']
            break
    return client_id


def get_rhsso_user_details(username):
    """Getter method to receive the user id"""
    result = run_command(
        cmd=f"{KEY_CLOAK_CLI} get users -r {realm} -q username={username}", hostname=rhsso_host,
    )
    result_json = json.loads("[{{{0}".format("".join(result)))
    return result_json[0]


def upload_rhsso_entity(json_content, entity_name):
    """Helper method upload the entity json request as file on RHSSO Server"""
    with open(entity_name, "w") as file:
        json.dump(json_content, file)
    ssh.upload_file(entity_name, entity_name, hostname=rhsso_host)


def create_mapper(json_content, client_id):
    """Helper method to create the RH-SSO Client Mapper"""
    upload_rhsso_entity(json_content, "mapper_file")
    run_command(
        cmd="{} create clients/{}/protocol-mappers/models -r {} -f {}".format(
            KEY_CLOAK_CLI, client_id, realm, "mapper_file"
        ),
        hostname=rhsso_host,
    )


def create_new_rhsso_user(client_id, username=None):
    """create new user in RHSSO instance and set the password"""
    if not username:
        username = gen_string('alphanumeric')
    RHSSO_NEW_USER['username'] = username
    RHSSO_NEW_USER['email'] = random.choice(valid_emails_list())
    RHSSO_RESET_PASSWORD['value'] = rhsso_password
    upload_rhsso_entity(RHSSO_NEW_USER, "create_user")
    upload_rhsso_entity(RHSSO_RESET_PASSWORD, "reset_password")
    run_command(
        cmd=f"{KEY_CLOAK_CLI} create users -r {realm} -f create_user", hostname=rhsso_host,
    )
    user_details = get_rhsso_user_details(RHSSO_NEW_USER['username'])
    run_command(
        cmd="{} update -r {} users/{}/reset-password -f {}".format(
            KEY_CLOAK_CLI, realm, user_details['id'], "reset_password"
        ),
        hostname=rhsso_host,
    )
    return RHSSO_NEW_USER


def delete_rhsso_user(username):
    """Delete the RHSSO user"""
    user_details = get_rhsso_user_details(username)
    run_command(
        cmd=f"{KEY_CLOAK_CLI} delete -r {realm} users/{user_details['id']}", hostname=rhsso_host,
    )
