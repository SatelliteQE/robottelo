import copy

import pytest
from nailgun import entities

from robottelo.api.utils import update_rhsso_settings_in_satellite
from robottelo.config import settings
from robottelo.constants import AUDIENCE_MAPPER
from robottelo.constants import GROUP_MEMBERSHIP_MAPPER
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.datafactory import gen_string
from robottelo.rhsso_utils import create_mapper
from robottelo.rhsso_utils import get_rhsso_client_id
from robottelo.rhsso_utils import run_command
from robottelo.rhsso_utils import set_the_redirect_uri


@pytest.fixture(scope='session')
def ad_data():
    return {
        'ldap_user_name': settings.ldap.username,
        'ldap_user_passwd': settings.ldap.password,
        'base_dn': settings.ldap.basedn,
        'group_base_dn': settings.ldap.grpbasedn,
        'ldap_hostname': settings.ldap.hostname,
    }


@pytest.fixture(scope='session')
def ipa_data():
    return {
        'ldap_user_name': settings.ipa.user_ipa,
        'ldap_user_cn': settings.ipa.username_ipa,
        'ipa_otp_username': settings.ipa.otp_user,
        'ldap_user_passwd': settings.ipa.password_ipa,
        'base_dn': settings.ipa.basedn_ipa,
        'group_base_dn': settings.ipa.grpbasedn_ipa,
        'ldap_hostname': settings.ipa.hostname_ipa,
        'time_based_secret': settings.ipa.time_based_secret,
        'disabled_user_ipa': settings.ipa.disabled_user_ipa,
    }


@pytest.fixture(scope='session')
def open_ldap_data():
    return settings.open_ldap


@pytest.fixture(scope='function')
def auth_source(module_org, module_loc, ad_data):
    return entities.AuthSourceLDAP(
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
        organization=[module_org],
        location=[module_loc],
    ).create()


@pytest.fixture(scope='function')
def auth_source_ipa(module_org, module_loc, ipa_data):
    return entities.AuthSourceLDAP(
        onthefly_register=True,
        account=ipa_data['ldap_user_cn'],
        account_password=ipa_data['ldap_user_passwd'],
        base_dn=ipa_data['base_dn'],
        groups_base=ipa_data['group_base_dn'],
        attr_firstname=LDAP_ATTR['firstname'],
        attr_lastname=LDAP_ATTR['surname'],
        attr_login=LDAP_ATTR['login'],
        server_type=LDAP_SERVER_TYPE['API']['ipa'],
        attr_mail=LDAP_ATTR['mail'],
        name=gen_string('alpha'),
        host=ipa_data['ldap_hostname'],
        tls=False,
        port='389',
        organization=[module_org],
        location=[module_loc],
    ).create()


@pytest.fixture
def ldap_auth_source(request, module_org, module_loc, ad_data, ipa_data):
    if request.param.lower() == 'ad':
        # entity create with AD settings
        entities.AuthSourceLDAP(
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
            organization=[module_org],
            location=[module_loc],
        ).create()
        ldap_data = ad_data
    elif request.param.lower() == 'ipa':
        # entity create with IPA settings
        entities.AuthSourceLDAP(
            onthefly_register=True,
            account=ipa_data['ldap_user_cn'],
            account_password=ipa_data['ldap_user_passwd'],
            base_dn=ipa_data['base_dn'],
            groups_base=ipa_data['group_base_dn'],
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login'],
            server_type=LDAP_SERVER_TYPE['API']['ipa'],
            attr_mail=LDAP_ATTR['mail'],
            name=gen_string('alpha'),
            host=ipa_data['ldap_hostname'],
            tls=False,
            port='389',
            organization=[module_org],
            location=[module_loc],
        ).create()
        ldap_data = ipa_data
    else:
        # default auth server settings
        raise Exception('Incorrect auth source parameter used')
    yield ldap_data


@pytest.fixture(scope='function')
def auth_source_open_ldap(module_org, module_loc, open_ldap_data):
    return entities.AuthSourceLDAP(
        onthefly_register=True,
        account=open_ldap_data.username,
        account_password=open_ldap_data.password,
        base_dn=open_ldap_data.base_dn,
        attr_firstname=LDAP_ATTR['firstname'],
        attr_lastname=LDAP_ATTR['surname'],
        attr_login=LDAP_ATTR['login'],
        server_type=LDAP_SERVER_TYPE['API']['posix'],
        attr_mail=LDAP_ATTR['mail'],
        name=gen_string('alpha'),
        host=open_ldap_data.hostname,
        tls=False,
        port='389',
        organization=[module_org],
        location=[module_loc],
    ).create()


@pytest.fixture(scope='session')
def enroll_configure_rhsso_external_auth():
    """Enroll the Satellite6 Server to an RHSSO Server."""
    run_command(
        cmd='yum -y --disableplugin=foreman-protector install '
        'mod_auth_openidc keycloak-httpd-client-install'
    )
    run_command(
        cmd=f'echo {settings.rhsso.password} | keycloak-httpd-client-install --app-name foreman-openidc \
                --keycloak-server-url {settings.rhsso.host_url} \
                --keycloak-admin-username "admin" \
                --keycloak-realm "{settings.rhsso.realm}" \
                --keycloak-admin-realm master \
                --keycloak-auth-role root-admin -t openidc -l /users/extlogin --force'
    )
    run_command(
        cmd=f"satellite-installer --foreman-keycloak true "
        f"--foreman-keycloak-app-name 'foreman-openidc' "
        f"--foreman-keycloak-realm '{settings.rhsso.realm}' ",
        timeout=1000,
    )
    run_command(cmd="systemctl restart httpd")


@pytest.fixture(scope='session')
def enable_external_auth_rhsso(enroll_configure_rhsso_external_auth):
    """register the satellite with RH-SSO Server for single sign-on"""
    client_id = get_rhsso_client_id()
    create_mapper(GROUP_MEMBERSHIP_MAPPER, client_id)
    audience_mapper = copy.deepcopy(AUDIENCE_MAPPER)
    audience_mapper["config"]["included.client.audience"] = audience_mapper["config"][
        "included.client.audience"
    ].format(rhsso_host=settings.server.hostname)
    create_mapper(audience_mapper, client_id)
    set_the_redirect_uri()


@pytest.fixture(scope='session')
def enroll_idm_and_configure_external_auth():
    """Enroll the Satellite6 Server to an IDM Server."""
    run_command(cmd='yum -y --disableplugin=foreman-protector install ipa-client ipa-admintools')

    run_command(
        cmd=f"echo {settings.ipa.password_ipa} | kinit admin",
        hostname=settings.ipa.hostname_ipa,
    )
    result = run_command(
        cmd=f"ipa host-add --random {settings.server.hostname}",
        hostname=settings.ipa.hostname_ipa,
    )

    for line in result:
        if "Random password" in line:
            _, password = line.split(': ', 2)
            break
    run_command(
        cmd=f"ipa service-add HTTP/{settings.server.hostname}",
        hostname=settings.ipa.hostname_ipa,
    )
    _, domain = settings.ipa.hostname_ipa.split('.', 1)
    run_command(
        cmd=f"ipa-client-install --password '{password}' "
        f"--domain {domain} "
        f"--server {settings.ipa.hostname_ipa} "
        f"--realm {domain.upper()} -U"
    )


@pytest.fixture()
def rhsso_setting_setup(request):
    """Update the RHSSO setting and revert it in cleanup"""
    update_rhsso_settings_in_satellite()
    yield
    update_rhsso_settings_in_satellite(revert=True)


@pytest.fixture()
def rhsso_setting_setup_with_timeout(rhsso_setting_setup, request):
    """Update the RHSSO setting with timeout setting and revert it in cleanup"""
    setting_entity = entities.Setting().search(query={'search': f'name=idle_timeout'})[0]
    setting_entity.value = 1
    setting_entity.update({'value'})
    yield
    setting_entity.value = 30
    setting_entity.update({'value'})


@pytest.fixture(scope='session')
def enroll_ad_and_configure_external_auth():
    """Enroll Satellite Server to an AD Server."""
    packages = (
        'sssd adcli realmd ipa-python-compat krb5-workstation '
        'samba-common-tools gssproxy nfs-utils ipa-client'
    )
    realm = settings.ldap.realm
    workgroup = realm.split(".")[0]

    default_content = f"[global]\nserver = unused\nrealm = {realm}"
    keytab_content = (
        f"[global]\nworkgroup = {workgroup}\nrealm = {realm}"
        f"\nkerberos method = system keytab\nsecurity = ads"
    )

    # install the required packages
    run_command(cmd=f'yum -y --disableplugin=foreman-protector install {packages}')

    # update the AD name server
    run_command(cmd="chattr -i /etc/resolv.conf")
    result = run_command(
        cmd="awk -v search='nameserver' '$0~search{print NR; exit}' /etc/resolv.conf"
    )
    line_number = int(''.join(result))
    run_command(
        cmd=f'sed -i "{line_number}i nameserver {settings.ldap.nameserver}" /etc/resolv.conf'
    )
    run_command(cmd="chattr +i /etc/resolv.conf")

    # join the realm
    run_command(cmd=f"echo {settings.ldap.password} | realm join -v {realm}")
    run_command(cmd="touch /etc/ipa/default.conf")
    run_command(cmd=f'echo "{default_content}" > /etc/ipa/default.conf')
    run_command(cmd=f'echo "{keytab_content}" > /etc/net-keytab.conf')

    # gather the apache id
    result = run_command(cmd="id -u apache")
    id_apache = "".join(result)
    http_conf_content = (
        f"[service/HTTP]\nmechs = krb5\ncred_store = keytab:/etc/krb5.keytab"
        f"\ncred_store = ccache:/var/lib/gssproxy/clients/krb5cc_%U"
        f"\neuid = {id_apache}"
    )

    # register the satellite as client for external auth
    run_command(cmd=f'echo "{http_conf_content}" > /etc/gssproxy/00-http.conf')
    token_command = (
        "KRB5_KTNAME=FILE:/etc/httpd/conf/http.keytab net ads keytab add HTTP "
        "-U administrator -d3 -s /etc/net-keytab.conf"
    )
    run_command(cmd=f"echo {settings.ldap.password} | {token_command}")
    run_command(cmd="chown root.apache /etc/httpd/conf/http.keytab")
    run_command(cmd="chmod 640 /etc/httpd/conf/http.keytab")
