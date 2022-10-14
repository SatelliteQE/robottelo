import json
import random
from functools import cached_property
from functools import lru_cache

from box import Box
from broker.hosts import Host
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import KEY_CLOAK_CLI
from robottelo.constants import RHSSO_NEW_GROUP
from robottelo.constants import RHSSO_NEW_USER
from robottelo.constants import RHSSO_RESET_PASSWORD
from robottelo.constants import RHSSO_USER_UPDATE
from robottelo.datafactory import valid_emails_list


class SSOHost(Host):
    def __init__(self, **kwargs):
        kwargs['hostname'] = kwargs.get('hostname', settings.rhsso.host_name)
        super().__init__(**kwargs)

    def get_rhsso_client_id(self, sat_obj):
        """getter method for fetching the client id and can be used other functions"""
        client_name = f'{sat_obj.hostname}-foreman-openidc'
        self.execute(
            '{} config credentials '
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
        )

        result = self.execute(f'{KEY_CLOAK_CLI} get clients --fields id,clientId')
        result_json = json.loads(result.stdout)
        client_id = None
        for client in result_json:
            if client_name in client['clientId']:
                client_id = client['id']
                break
        return client_id

    @lru_cache
    def get_rhsso_user_details(self, username):
        """Getter method to receive the user id"""
        result = self.execute(
            f"{KEY_CLOAK_CLI} get users -r {settings.rhsso.realm} -q username={username}"
        )
        result_json = json.loads(result.stdout)
        return result_json[0]

    @lru_cache
    def get_rhsso_groups_details(self, group_name):
        """Getter method to receive the group id"""
        result = self.execute(f"{KEY_CLOAK_CLI} get groups -r {settings.rhsso.realm}")
        group_list = json.loads(result.stdout)
        query_group = [group for group in group_list if group['name'] == group_name]
        return query_group[0]

    def upload_rhsso_entity(self, json_content, entity_name):
        """Helper method upload the entity json request as file on RHSSO Server"""
        with open(entity_name, "w") as file:
            json.dump(json_content, file)
        self.session.sftp_write(entity_name)

    def create_mapper(self, json_content, client_id):
        """Helper method to create the RH-SSO Client Mapper"""
        self.upload_rhsso_entity(json_content, "mapper_file")
        self.execute(
            "{} create clients/{}/protocol-mappers/models -r {} -f {}".format(
                KEY_CLOAK_CLI, client_id, settings.rhsso.realm, "mapper_file"
            )
        )

    def create_new_rhsso_user(self, client_id, username=None):
        """create new user in RHSSO instance and set the password"""
        update_data_user = Box(RHSSO_NEW_USER)
        update_data_pass = Box(RHSSO_RESET_PASSWORD)
        if not username:
            username = gen_string('alphanumeric')
        update_data_user.username = username
        update_data_user.email = username + random.choice(valid_emails_list())
        update_data_pass.value = settings.rhsso.rhsso_password
        self.upload_rhsso_entity(update_data_user, "create_user")
        self.upload_rhsso_entity(update_data_pass, "reset_password")
        self.execute(f"{KEY_CLOAK_CLI} create users -r {settings.rhsso.realm} -f create_user")
        user_details = self.get_rhsso_user_details(update_data_user.username)
        self.execute(
            "{} update -r {} users/{}/reset-password -f {}".format(
                KEY_CLOAK_CLI, settings.rhsso.realm, user_details['id'], "reset_password"
            )
        )
        return update_data_user

    def update_rhsso_user(self, username, group_name=None):
        update_data_user = Box(RHSSO_USER_UPDATE)
        user_details = self.get_rhsso_user_details(username)
        update_data_user.realm = settings.rhsso.realm
        update_data_user.userId = f"{user_details['id']}"
        if group_name:
            group_details = self.get_rhsso_groups_details(group_name=group_name)
            update_data_user['groupId'] = f"{group_details['id']}"
            self.upload_rhsso_entity(update_data_user, "update_user")
            group_path = f"users/{user_details['id']}/groups/{group_details['id']}"
            self.execute(
                f"{KEY_CLOAK_CLI} update -r {settings.rhsso.realm} {group_path} -f update_user"
            )

    def delete_rhsso_user(self, username):
        """Delete the RHSSO user"""
        user_details = self.get_rhsso_user_details(username)
        self.execute(f"{KEY_CLOAK_CLI} delete -r {settings.rhsso.realm} users/{user_details['id']}")

    def create_group(self, group_name=None):
        """Create the RHSSO group"""
        update_user_group = Box(RHSSO_NEW_GROUP)
        if not group_name:
            group_name = gen_string('alphanumeric')
        update_user_group.name = group_name
        self.upload_rhsso_entity(update_user_group, "create_group")
        result = self.execute(
            f"{KEY_CLOAK_CLI} create groups -r {settings.rhsso.realm} -f create_group"
        )
        return result.stdout

    def delete_rhsso_group(self, group_name):
        """Delete the RHSSO group"""
        group_details = self.get_rhsso_groups_details(group_name)
        self.execute(
            f"{KEY_CLOAK_CLI} delete -r {settings.rhsso.realm} groups/{group_details['id']}"
        )

    def update_client_configuration(self, json_content, sat_obj):
        """Update the client configuration"""
        client_id = self.get_rhsso_client_id(sat_obj)
        self.upload_rhsso_entity(json_content, "update_client_info")
        update_cmd = (
            f"{KEY_CLOAK_CLI} update clients/{client_id}"
            f"-f update_client_info -s enabled=true --merge"
        )
        self.execute(update_cmd)

    @cached_property
    def oidc_token_endpoint(self):
        """getter oidc token endpoint"""
        return (
            f"https://{settings.rhsso.host_name}/auth/realms/"
            f"{settings.rhsso.realm}/protocol/openid-connect/token"
        )

    def get_oidc_client_id(self, sat_obj):
        """getter for the oidc client_id"""
        return f"{sat_obj.hostname}-foreman-openidc"

    @cached_property
    def oidc_authorization_endpoint(self):
        """getter for the oidc authorization endpoint"""
        return (
            f"https://{settings.rhsso.host_name}/auth/realms/"
            f"{settings.rhsso.realm}/protocol/openid-connect/auth"
        )

    def get_two_factor_token_rh_sso_url(self, sat_obj):
        """getter for the two factor token rh_sso url"""
        return (
            f"https://{settings.rhsso.host_name}/auth/realms/"
            f"{settings.rhsso.realm}/protocol/openid-connect/"
            f"auth?response_type=code&client_id={sat_obj.hostname}-foreman-openidc&"
            "redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=openid"
        )

    def set_the_redirect_uri(self, sat_obj):
        client_config = {
            "redirectUris": [
                "urn:ietf:wg:oauth:2.0:oob",
                f"https://{sat_obj.hostname}/users/extlogin/redirect_uri",
                f"https://{sat_obj.hostname}/users/extlogin",
            ]
        }
        self.update_client_configuration(client_config, sat_obj)


sso_host = SSOHost()
