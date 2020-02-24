"""Unit tests for the ``users`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here: http://theforeman.org/api/apidoc/v2/users.html


:Requirement: User

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json

import paramiko
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
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_emails_list
from robottelo.datafactory import valid_usernames_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.helpers import read_data_file
from robottelo.test import APITestCase


class UserTestCase(APITestCase):
    """Tests for the ``users`` path."""

    @tier1
    def test_positive_create_with_username(self):
        """Create User for all variations of Username

        :id: a9827cda-7f6d-4785-86ff-3b6969c9c00a

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for username in valid_usernames_list():
            with self.subTest(username):
                user = entities.User(login=username).create()
                self.assertEqual(user.login, username)

    @tier1
    def test_positive_create_with_firstname(self):
        """Create User for all variations of First Name

        :id: 036bb958-227c-420c-8f2b-c607136f12e0

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for firstname in generate_strings_list(exclude_types=['html'], max_length=50):
            with self.subTest(firstname):
                user = entities.User(firstname=firstname).create()
                self.assertEqual(user.firstname, firstname)

    @tier1
    def test_positive_create_with_lastname(self):
        """Create User for all variations of Last Name

        :id: 95d3b571-77e7-42a1-9c48-21f242e8cdc2

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for lastname in generate_strings_list(exclude_types=['html'], max_length=50):
            with self.subTest(lastname):
                user = entities.User(lastname=lastname).create()
                self.assertEqual(user.lastname, lastname)

    @tier1
    def test_positive_create_with_email(self):
        """Create User for all variations of Email

        :id: e68caf51-44ba-4d32-b79b-9ab9b67b9590

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for mail in valid_emails_list():
            with self.subTest(mail):
                user = entities.User(mail=mail).create()
                self.assertEqual(user.mail, mail)

    @tier1
    def test_positive_create_with_description(self):
        """Create User for all variations of Description

        :id: 1463d71c-b77d-4223-84fa-8370f77b3edf

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for description in valid_data_list():
            with self.subTest(description):
                user = entities.User(description=description).create()
                self.assertEqual(user.description, description)

    @tier1
    def test_positive_create_with_password(self):
        """Create User for all variations of Password

        :id: 53d0a419-0730-4f7d-9170-d855adfc5070

        :expectedresults: User is created

        :CaseImportance: Critical
        """
        for password in generate_strings_list(exclude_types=['html'], max_length=50):
            with self.subTest(password):
                user = entities.User(password=password).create()
                self.assertIsNotNone(user)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create random users and then delete it.

        :id: df6059e7-85c5-42fa-99b5-b7f1ef809f52

        :expectedresults: The user cannot be fetched after deletion.

        :CaseImportance: Critical
        """
        for mail in valid_emails_list():
            with self.subTest(mail):
                user = entities.User(mail=mail).create()
                user.delete()
                with self.assertRaises(HTTPError):
                    user.read()

    @tier1
    def test_positive_update_username(self):
        """Update a user and provide new username.

        :id: a8e218b1-7256-4f20-91f3-3958d58ea5a8

        :expectedresults: The user's ``Username`` attribute is updated.

        :CaseImportance: Critical
        """
        user = entities.User().create()
        for login in valid_usernames_list():
            with self.subTest(login):
                user.login = login
                user = user.update(['login'])
                self.assertEqual(user.login, login)

    @tier1
    def test_positive_update_firstname(self):
        """Update a user and provide new firstname.

        :id: a1287d47-e7d8-4475-abe8-256e6f2034fc

        :expectedresults: The user's ``firstname`` attribute is updated.

        :CaseImportance: Critical
        """
        user = entities.User().create()
        for firstname in generate_strings_list(exclude_types=['html'], max_length=50):
            with self.subTest(firstname):
                user.firstname = firstname
                user = user.update(['firstname'])
                self.assertEqual(user.firstname, firstname)

    @tier1
    def test_positive_update_lastname(self):
        """Update a user and provide new lastname.

        :id: 25c6c9df-5db2-4827-89bb-b8fd0658a9b9

        :expectedresults: The user's ``lastname`` attribute is updated.

        :CaseImportance: Critical
        """
        user = entities.User().create()
        for lastname in generate_strings_list(exclude_types=['html'], max_length=50):
            with self.subTest(lastname):
                user.lastname = lastname
                user = user.update(['lastname'])
                self.assertEqual(user.lastname, lastname)

    @tier1
    def test_positive_update_email(self):
        """Update a user and provide new email.

        :id: 9eefcba6-66a3-41bf-87ba-3e032aee1db2

        :expectedresults: The user's ``email`` attribute is updated.

        :CaseImportance: Critical
        """
        user = entities.User().create()
        for mail in valid_emails_list():
            with self.subTest(mail):
                user.mail = mail
                user = user.update(['mail'])
                self.assertEqual(user.mail, mail)

    @tier1
    def test_positive_update_description(self):
        """Update a user and provide new email.

        :id: a1d764ad-e9bb-4e5e-b8cd-3c52e1f128f6

        :expectedresults: The user's ``Description`` attribute is updated.

        :CaseImportance: Critical
        """
        user = entities.User().create()
        for description in valid_data_list():
            with self.subTest(description):
                user.description = description
                user = user.update(['description'])
                self.assertEqual(user.description, description)

    @tier1
    def test_positive_update_admin(self):
        """Update a user and provide the ``admin`` attribute.

        :id: b5fedf65-37f5-43ca-806a-ac9a7979b19d

        :expectedresults: The user's ``admin`` attribute is updated.

        :CaseImportance: Critical
        """
        for admin_enable in (True, False):
            with self.subTest(admin_enable):
                user = entities.User(admin=admin_enable).create()
                user.admin = not admin_enable
                self.assertEqual(user.update().admin, not admin_enable)

    @tier1
    def test_negative_create_with_invalid_email(self):
        """Create User with invalid Email Address

        :id: ebbd1f5f-e71f-41f4-a956-ce0071b0a21c

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        for mail in invalid_emails_list():
            with self.subTest(mail):
                with self.assertRaises(HTTPError):
                    entities.User(mail=mail).create()

    @tier1
    def test_negative_create_with_invalid_username(self):
        """Create User with invalid Username

        :id: aaf157a9-0375-4405-ad87-b13970e0609b

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        for invalid_name in invalid_usernames_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(login=invalid_name).create()

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """Create User with invalid Firstname

        :id: cb1ca8a9-38b1-4d58-ae32-915b47b91657

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        for invalid_name in invalid_names_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(firstname=invalid_name).create()

    @tier1
    def test_negative_create_with_invalid_lastname(self):
        """Create User with invalid Lastname

        :id: 59546d26-2b6b-400b-990f-0b5d1c35004e

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        for invalid_name in invalid_names_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(lastname=invalid_name).create()

    @tier1
    def test_negative_create_with_blank_authorized_by(self):
        """Create User with blank authorized by

        :id: 1fe2d1e3-728c-4d89-97ae-3890e904f413

        :expectedresults: User is not created. Appropriate error shown.

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.User(auth_source='').create()


class UserRoleTestCase(APITestCase):
    """Test associations between users and roles."""

    @classmethod
    def setUpClass(cls):
        """Create two roles."""
        super(UserRoleTestCase, cls).setUpClass()
        cls.roles = [entities.Role().create() for _ in range(2)]

    @tier1
    def test_positive_create_with_role(self):
        """Create a user with the ``role`` attribute.

        :id: 32daacf1-eed4-49b1-81e1-ab0a5b0113f2

        :expectedresults: A user is created with the given role(s).

        This test targets BZ 1216239.

        :CaseImportance: Critical
        """
        for i in range(1, len(self.roles) + 1):
            with self.subTest(str(i)):
                chosen_roles = self.roles[:i]
                user = entities.User(role=chosen_roles).create()
                self.assertEqual(len(user.role), i)
                self.assertEqual(
                    set([role.id for role in user.role]), set([role.id for role in chosen_roles])
                )

    @tier1
    @upgrade
    def test_positive_update(self):
        """Update an existing user and give it roles.

        :id: 7fdca879-d65f-44fa-b9f2-b6bb5df30c2d

        :expectedresults: The user has whatever roles are given.

        This test targets BZ 1216239.

        :CaseImportance: Critical
        """
        user = entities.User().create()
        self.assertEqual(len(user.role), 0)  # No roles assigned
        for i in range(1, len(self.roles) + 1):
            with self.subTest(str(i)):
                chosen_roles = self.roles[:i]
                user.role = chosen_roles
                user = user.update(['role'])
                self.assertEqual(
                    set([role.id for role in user.role]), set([role.id for role in chosen_roles])
                )


class SshKeyInUserTestCase(APITestCase):
    """Implements the SSH Key in User Tests"""

    def gen_ssh_rsakey(self):
        """Generates RSA type ssh key using ssh module

        :return: string type well formatted RSA key
        """
        return 'ssh-rsa {}'.format(paramiko.RSAKey.generate(2048).get_base64())

    @classmethod
    def setUpClass(cls):
        """Create an user and import different keys from data json file"""
        super(SshKeyInUserTestCase, cls).setUpClass()
        cls.user = entities.User().create()
        cls.data_keys = json.loads(read_data_file('sshkeys.json'))

    @tier1
    def test_positive_create_ssh_key(self):
        """SSH Key can be added to User

        :id: d00905f6-3a70-4e2f-a5ae-fcac18274bb7

        :steps:

            1. Create new user with all the details
            2. Add SSH key to the above user

        :expectedresults: SSH key should be added to user

        :CaseImportance: Critical
        """
        ssh_name = gen_string('alpha')
        ssh_key = self.gen_ssh_rsakey()
        user_sshkey = entities.SSHKey(user=self.user, name=ssh_name, key=ssh_key).create()
        self.assertEqual(ssh_name, user_sshkey.name)
        self.assertEqual(ssh_key, user_sshkey.key)

    @tier1
    def test_positive_create_ssh_key_super_admin(self):
        """SSH Key can be added to Super Admin user

        :id: 397eea22-759c-4cd4-bda1-0e7835566c72

        :expectedresults: SSH Key should be added to Super Admin user

        :CaseImportance: Critical
        """
        user = entities.User().search(query={'search': 'login="admin"'})[0]
        ssh_name = gen_string('alpha')
        ssh_key = self.gen_ssh_rsakey()
        user_sshkey = entities.SSHKey(user=user, name=ssh_name, key=ssh_key).create()
        self.assertEqual(ssh_name, user_sshkey.name)
        self.assertEqual(ssh_key, user_sshkey.key)

    @tier1
    def test_negative_create_ssh_key(self):
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
        with self.assertRaises(HTTPError) as context:
            entities.SSHKey(user=self.user, name=gen_string('alpha'), key=invalid_sshkey).create()
        self.assertRegexpMatches(
            context.exception.response.text, 'Key is not a valid public ssh key'
        )
        self.assertRegexpMatches(
            context.exception.response.text, 'Key must be in OpenSSH public key format'
        )
        self.assertRegexpMatches(
            context.exception.response.text, 'Fingerprint could not be generated'
        )
        self.assertRegexpMatches(context.exception.response.text, 'Length could not be calculated')

    @tier1
    def test_negative_create_invalid_length_ssh_key(self):
        """Attempt to add SSH key that has invalid length

        :id: 899f0c46-c7fe-4610-80f1-1add4a9cbc26

        :steps:

            1. Create new user with all the details
            2. Attempt to add invalid length of SSH Key to above user

        :expectedresults: Satellite should raise 'Length could not be
            calculated' error

        :CaseImportance: Critical
        """
        invalid_length_key = self.data_keys['ssh_keys']['invalid_ssh_key']
        with self.assertRaises(HTTPError) as context:
            entities.SSHKey(
                user=self.user, name=gen_string('alpha'), key=invalid_length_key
            ).create()
        self.assertRegexpMatches(context.exception.response.text, 'Length could not be calculated')
        self.assertNotRegexpMatches(
            context.exception.response.text, 'Fingerprint could not be generated'
        )

    @tier1
    def test_negative_create_ssh_key_with_invalid_name(self):
        """Attempt to add SSH key that has invalid name length

        :id: e1e17839-a392-45bb-bb1e-28d3cd9dba1c

        :steps:

            1. Create new user with all the details
            2. Attempt to add invalid ssh Key name to above user

        :expectedresults: Satellite should raise Name is too long assertion

        :CaseImportance: Critical
        """
        invalid_ssh_key_name = gen_string('alpha', length=300)
        with self.assertRaises(HTTPError) as context:
            entities.SSHKey(
                user=self.user, name=invalid_ssh_key_name, key=self.gen_ssh_rsakey()
            ).create()
        self.assertRegexpMatches(context.exception.response.text, "Name is too long")

    @tier1
    @upgrade
    def test_positive_create_multiple_ssh_key_types(self):
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
        dsa = self.data_keys['ssh_keys']['dsa']
        ecdsa = self.data_keys['ssh_keys']['ecdsa']
        ed = self.data_keys['ssh_keys']['ed']
        user = entities.User().create()
        for key in [rsa, dsa, ecdsa, ed]:
            entities.SSHKey(user=user, name=gen_string('alpha'), key=key).create()
        user_sshkeys = entities.SSHKey(user=user).search()
        self.assertEqual(len(user_sshkeys), 4)

    @tier1
    @upgrade
    def test_positive_delete_ssh_key(self):
        """Satellite Admin can delete ssh key from user

        :id: 37da9052-83a7-440d-b24c-9d4458f011e3

        :steps:

            1. Create new user with all the details
            2. Add SSH Key to above user
            3. Delete the ssh-key from user

        :expectedresults: SSH key should be deleted from user

        :CaseImportance: Critical
        """
        user = entities.User().create()
        sshkey_name = gen_string('alpha')
        sshkey = entities.SSHKey(user=user, name=sshkey_name, key=self.gen_ssh_rsakey()).create()
        sshkey.delete()
        result = entities.SSHKey(user=user).search()
        self.assertEqual(len(result), 0)

    @tier2
    @upgrade
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
        sshkey_updated_for_host = '{0} {1}@{2}'.format(
            ssh_key, user.login, settings.server.hostname
        )
        host_enc_key = host.enc()['data']['parameters']['ssh_authorized_keys']
        self.assertEqual(sshkey_updated_for_host, host_enc_key[0])

    @tier2
    def test_positive_list_users_ssh_key(self):
        """Satellite lists users ssh keys

        :id: 8098e74a-d81e-4410-b744-435901bd70c0

        :steps:

            1. Create user with all the details
            2. Add SSH key in above user
            3. List all the ssh keys of above user

        :expectedresults: Satellite should list all the SSH keys of user

        :CaseLevel: Integration
        """
        user = entities.User().create()
        for i in range(2):
            entities.SSHKey(
                user=user, name=gen_string('alpha'), key=self.gen_ssh_rsakey()
            ).create()
        result = entities.SSHKey(user=user).search()
        self.assertEqual(len(result), 2)

    @tier1
    def test_positive_info_users_ssh_key(self):
        """Satellite returns info of user ssh key

        :id: 27c526b6-1008-47f8-98ac-4b2eb9b3d65e

        :steps:

            1. Create user with all the details
            2. Add SSH key in above user
            3. Info the above ssh key in user

        :expectedresults: Satellite should return information of SSH keys of
            user

        :CaseImportance: Critical
        """
        ssh_name = gen_string('alpha')
        ssh_key = self.gen_ssh_rsakey()
        user_sshkey = entities.SSHKey(user=self.user, name=ssh_name, key=ssh_key).create()
        self.assertEqual(ssh_name, user_sshkey.name)
        self.assertEqual(ssh_key, user_sshkey.key)


@run_in_one_thread
class ActiveDirectoryUserTestCase(APITestCase):
    """Implements the LDAP auth User Tests with Active Directory"""

    @classmethod
    @skip_if_not_set('ldap')
    def setUpClass(cls):
        """Fetch necessary properties from settings and Create ldap auth source"""
        super(ActiveDirectoryUserTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        cls.sat_url = 'https://{}'.format(settings.server.hostname)
        cls.ldap_user_name = settings.ldap.username
        cls.ldap_user_passwd = settings.ldap.password
        cls.authsource = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=cls.ldap_user_name,
            account_password=cls.ldap_user_passwd,
            base_dn=settings.ldap.basedn,
            groups_base=settings.ldap.grpbasedn,
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login_ad'],
            server_type=LDAP_SERVER_TYPE['API']['ad'],
            attr_mail=LDAP_ATTR['mail'],
            name=gen_string('alpha'),
            host=settings.ldap.hostname,
            tls=False,
            port='389',
            location=[cls.loc],
            organization=[cls.org],
        ).create()

    def tearDown(self):
        for user in entities.User().search(
            query={'search': 'login={}'.format(self.ldap_user_name)}
        ):
            user.delete()
        super(ActiveDirectoryUserTestCase, self).tearDown()

    @tier2
    @upgrade
    def test_positive_create_in_ldap_mode(self):
        """Create User in ldap mode

        :id: 6f8616b1-5380-40d2-8678-7c4434050cfb

        :expectedresults: User is created without specifying the password

        :CaseLevel: Integration
        """
        for username in valid_usernames_list():
            with self.subTest(username):
                user = entities.User(
                    login=username, auth_source=self.authsource, password=''
                ).create()
                self.assertEqual(user.login, username)

    @tier3
    @skip_if_not_set('ldap')
    def test_positive_ad_basic_no_roles(self):
        """Login with LDAP Auth- AD for user with no roles/rights

        :id: 3910c6eb-6eff-4ab7-a50d-ba40f5c24c08

        :setup: assure properly functioning AD server for authentication

        :steps: Login to server with an AD user.

        :expectedresults: Log in to foreman successfully but cannot access entities.

        :CaseLevel: System
        """
        sc = ServerConfig(
            auth=(self.ldap_user_name, self.ldap_user_passwd), url=self.sat_url, verify=False
        )
        with self.assertRaises(HTTPError):
            entities.Architecture(sc).search()

    @tier3
    @upgrade
    @skip_if_not_set('ldap')
    def test_positive_access_entities_from_ldap_org_admin(self):
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
                    'organization': self.org.name,
                    'location': self.loc.name,
                }
            }
        )
        sc = ServerConfig(
            auth=(self.ldap_user_name, self.ldap_user_passwd), url=self.sat_url, verify=False
        )
        with self.assertRaises(HTTPError):
            entities.Architecture(sc).search()
        user = entities.User().search(query={'search': 'login={}'.format(self.ldap_user_name)})[0]
        user.role = [entities.Role(id=org_admin['id']).read()]
        user.update(['role'])
        with self.assertNotRaises(HTTPError):
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


@run_in_one_thread
class FreeIPAUserTestCase(APITestCase):
    """Implements the LDAP auth User Tests with FreeIPA"""

    @classmethod
    @skip_if_not_set('ipa')
    def setUpClass(cls):
        """Fetch necessary properties from settings and Create ldap auth source"""
        super(FreeIPAUserTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        cls.sat_url = 'https://{}'.format(settings.server.hostname)
        cls.username = settings.ipa.user_ipa
        cls.ldap_user_name = settings.ipa.username_ipa
        cls.ldap_user_passwd = settings.ipa.password_ipa
        cls.authsource = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=cls.ldap_user_name,
            account_password=cls.ldap_user_passwd,
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
            location=[cls.loc],
            organization=[cls.org],
        ).create()

    def tearDown(self):
        for user in entities.User().search(query={'search': 'login={}'.format(self.username)}):
            user.delete()
        super(FreeIPAUserTestCase, self).tearDown()

    @tier3
    @skip_if_not_set('ipa')
    def test_positive_ipa_basic_no_roles(self):
        """Login with LDAP Auth- FreeIPA for user with no roles/rights

        :id: 901a241d-aa76-4562-ab1a-a752e6fb7ed5

        :setup: assure properly functioning FreeIPA server for authentication

        :steps: Login to server with an FreeIPA user.

        :expectedresults: Log in to foreman successfully but cannot access entities.

        :CaseLevel: System
        """
        sc = ServerConfig(
            auth=(self.username, self.ldap_user_passwd), url=self.sat_url, verify=False
        )
        with self.assertRaises(HTTPError):
            entities.Architecture(sc).search()

    @tier3
    @upgrade
    @skip_if_not_set('ipa')
    def test_positive_access_entities_from_ipa_org_admin(self):
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
                    'organization': self.org.name,
                    'location': self.loc.name,
                }
            }
        )
        sc = ServerConfig(
            auth=(self.username, self.ldap_user_passwd), url=self.sat_url, verify=False
        )
        with self.assertRaises(HTTPError):
            entities.Architecture(sc).search()
        user = entities.User().search(query={'search': 'login={}'.format(self.username)})[0]
        user.role = [entities.Role(id=org_admin['id']).read()]
        user.update(['role'])
        with self.assertNotRaises(HTTPError):
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
