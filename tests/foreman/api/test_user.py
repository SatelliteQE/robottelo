"""Unit tests for the ``users`` paths.

Each class tests a single URL. A full list of URLs to be tested can be found on your satellite:
http://<satellite-host>/apidoc/v2/users.html


:Requirement: User

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json
import re

import paramiko
import pytest
from nailgun import entities
from nailgun.config import ServerConfig
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.datafactory import gen_string
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import invalid_emails_list
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import invalid_usernames_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_emails_list
from robottelo.datafactory import valid_usernames_list
from robottelo.helpers import read_data_file


@pytest.fixture(scope='module')
def create_user():
    """Create a user"""
    return entities.User().create()


class TestUser:
    """Tests for the ``users`` path."""

    @pytest.mark.tier1
    @pytest.mark.parametrize('username', **parametrized(valid_usernames_list()))
    def test_positive_create_with_username(self, username):
        """Create User for all variations of Username

        :id: a9827cda-7f6d-4785-86ff-3b6969c9c00a

        :parametrized: yes

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        user = entities.User(login=username).create()
        assert user.login == username

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'firstname', **parametrized(generate_strings_list(exclude_types=['html'], max_length=50))
    )
    def test_positive_create_with_firstname(self, firstname):
        """Create User for all variations of First Name

        :id: 036bb958-227c-420c-8f2b-c607136f12e0

        :parametrized: yes

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        if len(str.encode(firstname)) > 50:
            firstname = firstname[:20]
        user = entities.User(firstname=firstname).create()
        assert user.firstname == firstname

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'lastname', **parametrized(generate_strings_list(exclude_types=['html'], max_length=50))
    )
    def test_positive_create_with_lastname(self, lastname):
        """Create User for all variations of Last Name

        :id: 95d3b571-77e7-42a1-9c48-21f242e8cdc2

        :parametrized: yes

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        if len(str.encode(lastname)) > 50:
            lastname = lastname[:20]
        user = entities.User(lastname=lastname).create()
        assert user.lastname == lastname

    @pytest.mark.tier1
    @pytest.mark.parametrize('mail', **parametrized(valid_emails_list()))
    def test_positive_create_with_email(self, mail):
        """Create User for all variations of Email

        :id: e68caf51-44ba-4d32-b79b-9ab9b67b9590

        :parametrized: yes

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        user = entities.User(mail=mail).create()
        assert user.mail == mail

    @pytest.mark.tier1
    @pytest.mark.parametrize('description', **parametrized(valid_data_list()))
    def test_positive_create_with_description(self, description):
        """Create User for all variations of Description

        :id: 1463d71c-b77d-4223-84fa-8370f77b3edf

        :parametrized: yes

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        user = entities.User(description=description).create()
        assert user.description == description

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'password', **parametrized(generate_strings_list(exclude_types=['html'], max_length=50))
    )
    def test_positive_create_with_password(self, password):
        """Create User for all variations of Password

        :id: 53d0a419-0730-4f7d-9170-d855adfc5070

        :parametrized: yes

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        user = entities.User(password=password).create()
        assert user is not None

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize('mail', **parametrized(valid_emails_list()))
    def test_positive_delete(self, mail):
        """Create random users and then delete it.

        :id: df6059e7-85c5-42fa-99b5-b7f1ef809f52

        :parametrized: yes

        :expectedresults: The user cannot be fetched after deletion.

        :CaseImportance: Critical
        """
        user = entities.User(mail=mail).create()
        user.delete()
        with pytest.raises(HTTPError):
            user.read()

    @pytest.mark.tier1
    @pytest.mark.parametrize('login', **parametrized(valid_usernames_list()))
    def test_positive_update_username(self, create_user, login):
        """Update a user and provide new username.

        :id: a8e218b1-7256-4f20-91f3-3958d58ea5a8

        :parametrized: yes

        :expectedresults: The user's ``Username`` attribute is updated.

        :CaseImportance: Critical
        """
        create_user.login = login
        user = create_user.update(['login'])
        assert user.login == login

    @pytest.mark.tier1
    @pytest.mark.parametrize('login', **parametrized(invalid_usernames_list()))
    def test_negative_update_username(self, create_user, login):
        """Update a user and provide new login.

        :id: 9eefcba6-66a3-41bf-87ba-3e032aee1db2

        :parametrized: yes

        :expectedresults: The user's ``login`` attribute is updated.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            create_user.login = login
            create_user.update(['login'])

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'firstname', **parametrized(generate_strings_list(exclude_types=['html'], max_length=50))
    )
    def test_positive_update_firstname(self, create_user, firstname):
        """Update a user and provide new firstname.

        :id: a1287d47-e7d8-4475-abe8-256e6f2034fc

        :parametrized: yes

        :expectedresults: The user's ``firstname`` attribute is updated.

        :CaseImportance: Critical
        """
        if len(str.encode(firstname)) > 50:
            firstname = firstname[:20]
        create_user.firstname = firstname
        user = create_user.update(['firstname'])
        assert user.firstname == firstname

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'lastname', **parametrized(generate_strings_list(exclude_types=['html'], max_length=50))
    )
    def test_positive_update_lastname(self, create_user, lastname):
        """Update a user and provide new lastname.

        :id: 25c6c9df-5db2-4827-89bb-b8fd0658a9b9

        :parametrized: yes

        :expectedresults: The user's ``lastname`` attribute is updated.

        :CaseImportance: Critical
        """
        if len(str.encode(lastname)) > 50:
            lastname = lastname[:20]
        create_user.lastname = lastname
        user = create_user.update(['lastname'])
        assert user.lastname == lastname

    @pytest.mark.tier1
    @pytest.mark.parametrize('mail', **parametrized(valid_emails_list()))
    def test_positive_update_email(self, create_user, mail):
        """Update a user and provide new email.

        :id: 3ae70631-7cee-4a4a-9c2f-b428273f1311

        :parametrized: yes

        :expectedresults: The user's ``mail`` attribute is updated.

        :CaseImportance: Critical
        """
        create_user.mail = mail
        user = create_user.update(['mail'])
        assert user.mail == mail

    @pytest.mark.tier1
    @pytest.mark.parametrize('mail', **parametrized(invalid_emails_list()))
    def test_negative_update_email(self, create_user, mail):
        """Update a user and provide new email.

        :id: 0631dce1-694c-4815-971d-26ff1934da98

        :parametrized: yes

        :expectedresults: The user's ``mail`` attribute is updated.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            create_user.mail = mail
            create_user.update(['mail'])

    @pytest.mark.tier1
    @pytest.mark.parametrize('description', **parametrized(valid_data_list()))
    def test_positive_update_description(self, create_user, description):
        """Update a user and provide new email.

        :id: a1d764ad-e9bb-4e5e-b8cd-3c52e1f128f6

        :parametrized: yes

        :expectedresults: The user's ``Description`` attribute is updated.

        :CaseImportance: Critical
        """
        create_user.description = description
        user = create_user.update(['description'])
        assert user.description == description

    @pytest.mark.tier1
    @pytest.mark.parametrize('admin_enable', [True, False])
    def test_positive_update_admin(self, admin_enable):
        """Update a user and provide the ``admin`` attribute.

        :id: b5fedf65-37f5-43ca-806a-ac9a7979b19d

        :parametrized: yes

        :expectedresults: The user's ``admin`` attribute is updated.

        :CaseImportance: Critical
        """
        user = entities.User(admin=admin_enable).create()
        user.admin = not admin_enable
        assert user.update().admin == (not admin_enable)

    @pytest.mark.tier1
    @pytest.mark.parametrize('mail', **parametrized(invalid_emails_list()))
    def test_negative_create_with_invalid_email(self, mail):
        """Create User with invalid Email Address

        :id: ebbd1f5f-e71f-41f4-a956-ce0071b0a21c

        :parametrized: yes

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            entities.User(mail=mail).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('invalid_name', **parametrized(invalid_usernames_list()))
    def test_negative_create_with_invalid_username(self, invalid_name):
        """Create User with invalid Username

        :id: aaf157a9-0375-4405-ad87-b13970e0609b

        :parametrized: yes

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            entities.User(login=invalid_name).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('invalid_name', **parametrized(invalid_names_list()))
    def test_negative_create_with_invalid_firstname(self, invalid_name):
        """Create User with invalid Firstname

        :id: cb1ca8a9-38b1-4d58-ae32-915b47b91657

        :parametrized: yes

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            entities.User(firstname=invalid_name).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('invalid_name', **parametrized(invalid_names_list()))
    def test_negative_create_with_invalid_lastname(self, invalid_name):
        """Create User with invalid Lastname

        :id: 59546d26-2b6b-400b-990f-0b5d1c35004e

        :parametrized: yes

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            entities.User(lastname=invalid_name).create()

    @pytest.mark.tier1
    def test_negative_create_with_blank_authorized_by(self):
        """Create User with blank authorized by

        :id: 1fe2d1e3-728c-4d89-97ae-3890e904f413

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            entities.User(auth_source='').create()


class TestUserRole:
    """Test associations between users and roles."""

    @pytest.fixture(scope='class')
    def make_roles(self):
        """Create two roles."""
        return [entities.Role().create() for _ in range(2)]

    @pytest.mark.tier1
    @pytest.mark.parametrize('number_of_roles', range(1, 3))
    def test_positive_create_with_role(self, make_roles, number_of_roles):
        """Create a user with the ``role`` attribute.

        :id: 32daacf1-eed4-49b1-81e1-ab0a5b0113f2

        :parametrized: yes

        :expectedresults: A user is created with the given role(s).

        This test targets BZ 1216239.

        :CaseImportance: Critical
        """
        chosen_roles = make_roles[:number_of_roles]
        user = entities.User(role=chosen_roles).create()
        assert len(user.role) == number_of_roles
        assert {role.id for role in user.role} == {role.id for role in chosen_roles}

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize('number_of_roles', range(1, 3))
    def test_positive_update(self, create_user, make_roles, number_of_roles):
        """Update an existing user and give it roles.

        :id: 7fdca879-d65f-44fa-b9f2-b6bb5df30c2d

        :parametrized: yes

        :expectedresults: The user has whatever roles are given.

        This test targets BZ 1216239.

        :CaseImportance: Critical
        """
        chosen_roles = make_roles[:number_of_roles]
        create_user.role = chosen_roles
        user = create_user.update(['role'])
        assert {role.id for role in user.role} == {role.id for role in chosen_roles}


class TestSshKeyInUser:
    """Implements the SSH Key in User Tests"""

    def gen_ssh_rsakey(self):
        """Generates RSA type ssh key using ssh module

        :return: string type well formatted RSA key
        """
        return 'ssh-rsa {}'.format(paramiko.RSAKey.generate(2048).get_base64())

    @pytest.fixture(scope='class')
    def create_user(self):
        """Create an user and import different keys from data json file"""
        user = entities.User().create()
        data_keys = json.loads(read_data_file('sshkeys.json'))
        return dict(user=user, data_keys=data_keys)

    @pytest.mark.tier1
    def test_positive_CRD_ssh_key(self):
        """SSH Key can be added to User

        :id: d00905f6-3a70-4e2f-a5ae-fcac18274bb7

        :steps:

            1. Create new user with all the details
            2. Add SSH key to the above user
            3. Info the above ssh key in user
            4. Delete ssh key in user

        :expectedresults: SSH key should be added to user

        :CaseImportance: Critical
        """
        user = entities.User().create()
        ssh_name = gen_string('alpha')
        ssh_key = self.gen_ssh_rsakey()
        user_sshkey = entities.SSHKey(user=user, name=ssh_name, key=ssh_key).create()
        assert ssh_name == user_sshkey.name
        assert ssh_key == user_sshkey.key
        user_sshkey.delete()
        result = entities.SSHKey(user=user).search()
        assert len(result) == 0

    @pytest.mark.tier1
    def test_negative_create_ssh_key(self, create_user):
        """Invalid ssh key can not be added in User Template

        :id: e924ff03-8b2c-4ab9-a054-ea491413e143

        :steps:

            1. Create new user with all the details
            2. Attempt to add invalid string as SSH Key to above user
                e.g blabla

        :expectedresults:

            1. Invalid SSH key should not be added in user
            2. Satellite returns 'Fingerprint could not be generated' error

        :CaseImportance: Critical
        """
        invalid_sshkey = gen_string('alpha', length=256)
        with pytest.raises(HTTPError) as context:
            entities.SSHKey(
                user=create_user['user'], name=gen_string('alpha'), key=invalid_sshkey
            ).create()
        assert re.search('Key is not a valid public ssh key', context.value.response.text)
        assert re.search('Key must be in OpenSSH public key format', context.value.response.text)
        assert re.search('Fingerprint could not be generated', context.value.response.text)
        assert re.search('Length could not be calculated', context.value.response.text)

    @pytest.mark.tier1
    def test_negative_create_invalid_length_ssh_key(self, create_user):
        """Attempt to add SSH key that has invalid length

        :id: 899f0c46-c7fe-4610-80f1-1add4a9cbc26

        :steps:

            1. Create new user with all the details
            2. Attempt to add invalid length of SSH Key to above user

        :expectedresults: Satellite should raise 'Length could not be
            calculated' error

        :CaseImportance: Critical
        """
        invalid_length_key = create_user['data_keys']['ssh_keys']['invalid_ssh_key']
        with pytest.raises(HTTPError) as context:
            entities.SSHKey(
                user=create_user['user'], name=gen_string('alpha'), key=invalid_length_key
            ).create()
        assert re.search('Length could not be calculated', context.value.response.text)
        assert not re.search('Fingerprint could not be generated', context.value.response.text)

    @pytest.mark.tier1
    def test_negative_create_ssh_key_with_invalid_name(self, create_user):
        """Attempt to add SSH key that has invalid name length

        :id: e1e17839-a392-45bb-bb1e-28d3cd9dba1c

        :steps:

            1. Create new user with all the details
            2. Attempt to add invalid ssh Key name to above user

        :expectedresults: Satellite should raise Name is too long assertion

        :CaseImportance: Critical
        """
        invalid_ssh_key_name = gen_string('alpha', length=300)
        with pytest.raises(HTTPError) as context:
            entities.SSHKey(
                user=create_user['user'], name=invalid_ssh_key_name, key=self.gen_ssh_rsakey()
            ).create()
        assert re.search("Name is too long", context.value.response.text)

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_create_multiple_ssh_key_types(self, create_user):
        """Multiple types of ssh keys can be added to user

        :id: d1ffa908-dc86-40c8-b6f0-20650cc67046

        :steps:
            1. Create user with all the details
            2. Add multiple types of supported ssh keys, type includes
                rsa, dsa, ed25519, ecdsa

        :expectedresults: Multiple types of supported ssh keys can be added to
            user
        """
        rsa = self.gen_ssh_rsakey()
        dsa = create_user['data_keys']['ssh_keys']['dsa']
        ecdsa = create_user['data_keys']['ssh_keys']['ecdsa']
        ed = create_user['data_keys']['ssh_keys']['ed']
        user = entities.User().create()
        for key in [rsa, dsa, ecdsa, ed]:
            entities.SSHKey(user=user, name=gen_string('alpha'), key=key).create()
        user_sshkeys = entities.SSHKey(user=user).search()
        assert len(user_sshkeys) == 4

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_ssh_key_in_host_enc(self):
        """SSH key appears in host ENC output

        :id: 4b70a950-e777-4b2d-a83d-29279715fe6d

        :steps:

            1. Create user with all the details
            2. Add ssh key in above user
            3. Provision a new host from the above user
            4. Check new hosts ENC output

        :expectedresults: SSH key should be added to host ENC output

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        user = entities.User(organization=[org], location=[loc]).create()
        ssh_key = self.gen_ssh_rsakey()
        entities.SSHKey(user=user, name=gen_string('alpha'), key=ssh_key).create()
        host = entities.Host(
            owner=user, owner_type='User', organization=org, location=loc
        ).create()
        sshkey_updated_for_host = f'{ssh_key} {user.login}@{settings.server.hostname}'
        host_enc_key = host.enc()['data']['parameters']['ssh_authorized_keys']
        assert sshkey_updated_for_host == host_enc_key[0]


@pytest.mark.run_in_one_thread
class TestActiveDirectoryUser:
    """Implements the LDAP auth User Tests with Active Directory"""

    @pytest.fixture(scope='module')
    def create_ldap(self, ad_data):
        """Fetch necessary properties from settings and Create ldap auth source"""
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        ad_data = ad_data()
        yield dict(
            org=org,
            loc=loc,
            sat_url=f'https://{settings.server.hostname}',
            ldap_user_name=ad_data['ldap_user_name'],
            ldap_user_passwd=ad_data['ldap_user_passwd'],
            authsource=entities.AuthSourceLDAP(
                onthefly_register=True,
                account=ad_data['ldap_user_name'],
                account_password=ad_data['ldap_user_passwd'],
                base_dn=ad_data['base_dn'],
                groups_base=ad_data['group_base_dn'],
                attr_firstname=LDAP_ATTR['firstname'],
                attr_lastname=LDAP_ATTR['surname'],
                attr_login=LDAP_ATTR['login_ad'],
                server_type=LDAP_SERVER_TYPE['API']['ad'],
                attr_mail=LDAP_ATTR['mail'],
                name=gen_string('alpha'),
                host=ad_data['ldap_hostname'],
                tls=False,
                port='389',
                location=[loc],
                organization=[org],
            ).create(),
        )
        for user in entities.User().search(query={'search': f'login={ad_data["ldap_user_name"]}'}):
            user.delete()
        org.delete()
        loc.delete()

    @pytest.mark.tier2
    @pytest.mark.upgrade
    @pytest.mark.parametrize('username', **parametrized(valid_usernames_list()))
    def test_positive_create_in_ldap_mode(self, username, create_ldap):
        """Create User in ldap mode

        :id: 6f8616b1-5380-40d2-8678-7c4434050cfb

        :parametrized: yes

        :expectedresults: User is created without specifying the password

        :CaseLevel: Integration
        """
        user = entities.User(
            login=username, auth_source=create_ldap['authsource'], password=''
        ).create()
        assert user.login == username

    @pytest.mark.tier3
    def test_positive_ad_basic_no_roles(self, create_ldap):
        """Login with LDAP Auth- AD for user with no roles/rights

        :id: 3910c6eb-6eff-4ab7-a50d-ba40f5c24c08

        :setup: assure properly functioning AD server for authentication

        :steps: Login to server with an AD user.

        :expectedresults: Log in to foreman successfully but cannot access entities.

        :CaseLevel: System
        """
        sc = ServerConfig(
            auth=(create_ldap['ldap_user_name'], create_ldap['ldap_user_passwd']),
            url=create_ldap['sat_url'],
            verify=False,
        )
        with pytest.raises(HTTPError):
            entities.Architecture(sc).search()

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_access_entities_from_ldap_org_admin(self, create_ldap):
        """LDAP User can access resources within its taxonomies if assigned
        role has permission for same taxonomies

        :id: 522063ad-8d39-4f05-bfd3-dfa0fa73f4e1

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create LDAP user with same taxonomies as role above
            3. Assign Org Admin role to user above
            4. Login with LDAP user and attempt to access resources

        :expectedresults: LDAP User should be able to access all the resources
            and permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """
        role_name = gen_string('alpha')
        default_org_admin = entities.Role().search(query={'search': 'name="Organization admin"'})
        org_admin = entities.Role(id=default_org_admin[0].id).clone(
            data={
                'role': {
                    'name': role_name,
                    'organization': create_ldap['org'].name,
                    'location': create_ldap['loc'].name,
                }
            }
        )
        sc = ServerConfig(
            auth=(create_ldap['ldap_user_name'], create_ldap['ldap_user_passwd']),
            url=create_ldap['sat_url'],
            verify=False,
        )
        with pytest.raises(HTTPError):
            entities.Architecture(sc).search()
        user = entities.User().search(
            query={'search': 'login={}'.format(create_ldap['ldap_user_name'])}
        )[0]
        user.role = [entities.Role(id=org_admin['id']).read()]
        user.update(['role'])
        for entity in [
            entities.Architecture,
            entities.Audit,
            entities.Bookmark,
            entities.CommonParameter,
            entities.LibvirtComputeResource,
            entities.OVirtComputeResource,
            entities.VMWareComputeResource,
            entities.ConfigGroup,
            entities.Errata,
            entities.OperatingSystem,
        ]:
            entity(sc).search()


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('ipa')
class TestFreeIPAUser:
    """Implements the LDAP auth User Tests with FreeIPA"""

    @pytest.fixture(scope='class')
    def create_ldap(self):
        """Fetch necessary properties from settings and Create ldap auth source"""
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        ldap_user_name = settings.ipa.username_ipa
        ldap_user_passwd = settings.ipa.password_ipa
        username = settings.ipa.user_ipa
        yield dict(
            org=org,
            loc=loc,
            ldap_user_name=ldap_user_name,
            ldap_user_passwd=ldap_user_passwd,
            sat_url=f'https://{settings.server.hostname}',
            username=username,
            authsource=entities.AuthSourceLDAP(
                onthefly_register=True,
                account=ldap_user_name,
                account_password=ldap_user_passwd,
                base_dn=settings.ipa.basedn_ipa,
                groups_base=settings.ipa.grpbasedn_ipa,
                attr_firstname=LDAP_ATTR['firstname'],
                attr_lastname=LDAP_ATTR['surname'],
                attr_login=LDAP_ATTR['login'],
                server_type=LDAP_SERVER_TYPE['API']['ipa'],
                attr_mail=LDAP_ATTR['mail'],
                name=gen_string('alpha'),
                host=settings.ipa.hostname_ipa,
                tls=False,
                port='389',
                location=[loc],
                organization=[org],
            ).create(),
        )
        for user in entities.User().search(query={'search': f'login={username}'}):
            user.delete()

    @pytest.mark.tier3
    def test_positive_ipa_basic_no_roles(self, create_ldap):
        """Login with LDAP Auth- FreeIPA for user with no roles/rights

        :id: 901a241d-aa76-4562-ab1a-a752e6fb7ed5

        :setup: assure properly functioning FreeIPA server for authentication

        :steps: Login to server with an FreeIPA user.

        :expectedresults: Log in to foreman successfully but cannot access entities.

        :CaseLevel: System
        """
        sc = ServerConfig(
            auth=(create_ldap['username'], create_ldap['ldap_user_passwd']),
            url=create_ldap['sat_url'],
            verify=False,
        )
        with pytest.raises(HTTPError):
            entities.Architecture(sc).search()

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_access_entities_from_ipa_org_admin(self, create_ldap):
        """LDAP FreeIPA User can access resources within its taxonomies if assigned
        role has permission for same taxonomies

        :id: acc48330-fc84-4970-b722-9b45a3116eed

        :steps:

            1. Create Org Admin and assign taxonomies to it
            2. Create FreeIPA user with same taxonomies as role above
            3. Assign Org Admin role to user above
            4. Login with FreeIPA user and attempt to access resources

        :expectedresults: FreeIPA User should be able to access all the resources
            and permissions in taxonomies selected in Org Admin role

        :CaseLevel: System
        """
        role_name = gen_string('alpha')
        default_org_admin = entities.Role().search(query={'search': 'name="Organization admin"'})
        org_admin = entities.Role(id=default_org_admin[0].id).clone(
            data={
                'role': {
                    'name': role_name,
                    'organization': create_ldap['org'].name,
                    'location': create_ldap['loc'].name,
                }
            }
        )
        sc = ServerConfig(
            auth=(create_ldap['username'], create_ldap['ldap_user_passwd']),
            url=create_ldap['sat_url'],
            verify=False,
        )
        with pytest.raises(HTTPError):
            entities.Architecture(sc).search()
        user = entities.User().search(
            query={'search': 'login={}'.format(create_ldap['username'])}
        )[0]
        user.role = [entities.Role(id=org_admin['id']).read()]
        user.update(['role'])
        for entity in [
            entities.Architecture,
            entities.Audit,
            entities.Bookmark,
            entities.CommonParameter,
            entities.LibvirtComputeResource,
            entities.OVirtComputeResource,
            entities.VMWareComputeResource,
            entities.ConfigGroup,
            entities.Errata,
            entities.OperatingSystem,
        ]:
            entity(sc).search()
