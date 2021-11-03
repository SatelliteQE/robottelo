import copy
import socket

import pytest
from attrdict import AttrDict
from nailgun import entities

from robottelo.api.utils import update_rhsso_settings_in_satellite
from robottelo.cli.base import CLIReturnCodeError
from robottelo.config import settings
from robottelo.constants import AUDIENCE_MAPPER
from robottelo.constants import GROUP_MEMBERSHIP_MAPPER
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.datafactory import gen_string
from robottelo.hosts import ContentHost
from robottelo.rhsso_utils import create_mapper
from robottelo.rhsso_utils import get_rhsso_client_id
from robottelo.rhsso_utils import run_command
from robottelo.rhsso_utils import set_the_redirect_uri


@pytest.fixture(scope='session')
def ad_data():
    supported_server_versions = ['2016', '2019']

    def _ad_data(version='2016'):
        if version in supported_server_versions:
            ad_server_details = {
                'ldap_user_name': settings.ldap.username,
                'ldap_user_cn': settings.ldap.username,
                'ldap_user_passwd': settings.ldap.password,
                'base_dn': settings.ldap.basedn,
                'group_base_dn': settings.ldap.grpbasedn,
                'realm': settings.ldap.realm,
                'ldap_hostname': getattr(settings.ldap.hostname, version),
                'workgroup': getattr(settings.ldap.workgroup, version),
                'nameserver': getattr(settings.ldap.nameserver, version),
            }
        else:
            raise Exception(
                f'The currently supported AD servers are {supported_server_versions}. '
                f'Does not match with provided {version}'
            )

        return AttrDict(ad_server_details)

    return _ad_data


@pytest.fixture(scope='session')
def ipa_data():
    return {
        'ldap_user_name': settings.ipa.user,
        'ldap_user_cn': settings.ipa.username,
        'ipa_otp_username': settings.ipa.otp_user,
        'ldap_user_passwd': settings.ipa.password,
        'base_dn': settings.ipa.basedn,
        'group_base_dn': settings.ipa.grpbasedn,
        'ldap_hostname': settings.ipa.hostname,
        'time_based_secret': settings.ipa.time_based_secret,
        'disabled_user_ipa': settings.ipa.disabled_ipa_user,
        'group_users': settings.ipa.group_users,
        'groups': settings.ipa.groups,
    }


@pytest.fixture(scope='session')
def open_ldap_data():
    return {
        'ldap_user_name': settings.open_ldap.open_ldap_user,
        'ldap_user_cn': settings.open_ldap.username,
        'ldap_hostname': settings.open_ldap.hostname,
        'ldap_user_passwd': settings.open_ldap.password,
        'base_dn': settings.open_ldap.base_dn,
        'group_base_dn': settings.open_ldap.group_base_dn,
    }


@pytest.fixture(scope='function')
def auth_source(module_org, module_location, ad_data):
    ad_data = ad_data()
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
        location=[module_location],
    ).create()


@pytest.fixture(scope='function')
def auth_source_ipa(module_org, module_location, ipa_data):
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
        location=[module_location],
    ).create()


@pytest.fixture(scope='function')
def auth_source_open_ldap(module_org, module_location, open_ldap_data):
    return entities.AuthSourceLDAP(
        onthefly_register=True,
        account=open_ldap_data['ldap_user_cn'],
        account_password=open_ldap_data['ldap_user_passwd'],
        base_dn=open_ldap_data['base_dn'],
        groups_base=open_ldap_data['group_base_dn'],
        attr_firstname=LDAP_ATTR['firstname'],
        attr_lastname=LDAP_ATTR['surname'],
        attr_login=LDAP_ATTR['login'],
        server_type=LDAP_SERVER_TYPE['API']['posix'],
        attr_mail=LDAP_ATTR['mail'],
        name=gen_string('alpha'),
        host=open_ldap_data['ldap_hostname'],
        tls=False,
        port='389',
        organization=[module_org],
        location=[module_location],
    ).create()


@pytest.fixture
def ldap_auth_source(request, module_org, module_location, ad_data, ipa_data, open_ldap_data):
    auth_type = request.param.lower()
    if 'ad' in auth_type:
        ad_data = ad_data('2019') if '2019' in auth_type else ad_data()
        # entity create with AD settings
        auth_source = entities.AuthSourceLDAP(
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
            location=[module_location],
        ).create()
        ldap_data = ad_data
    elif auth_type == 'ipa':
        # entity create with IPA settings
        auth_source = entities.AuthSourceLDAP(
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
            location=[module_location],
        ).create()
        ldap_data = ipa_data
    elif auth_type == 'openldap':
        # entity create with OpenLdap settings
        auth_source = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=open_ldap_data['ldap_user_cn'],
            account_password=open_ldap_data['ldap_user_passwd'],
            base_dn=open_ldap_data['base_dn'],
            groups_base=open_ldap_data['group_base_dn'],
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login'],
            server_type=LDAP_SERVER_TYPE['API']['posix'],
            attr_mail=LDAP_ATTR['mail'],
            name=gen_string('alpha'),
            host=open_ldap_data['ldap_hostname'],
            tls=False,
            port='389',
            organization=[module_org],
            location=[module_location],
        ).create()
        ldap_data = open_ldap_data
    else:
        raise Exception('Incorrect auth source parameter used')
    ldap_data['auth_type'] = auth_type
    if ldap_data['auth_type'] == 'ipa':
        ldap_data['server_type'] = LDAP_SERVER_TYPE['UI']['ipa']
        ldap_data['attr_login'] = LDAP_ATTR['login']
    elif ldap_data['auth_type'] == 'ad':
        ldap_data['server_type'] = LDAP_SERVER_TYPE['UI']['ad']
        ldap_data['attr_login'] = LDAP_ATTR['login_ad']
    else:
        ldap_data['server_type'] = LDAP_SERVER_TYPE['UI']['posix']
        ldap_data['attr_login'] = LDAP_ATTR['login']
    yield ldap_data, auth_source


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
        cmd=f'satellite-installer --foreman-keycloak true '
        f"--foreman-keycloak-app-name 'foreman-openidc' "
        f"--foreman-keycloak-realm '{settings.rhsso.realm}' ",
        timeout=1000000,
    )
    run_command(cmd="systemctl restart httpd")


@pytest.fixture(scope='session')
def enable_external_auth_rhsso(enroll_configure_rhsso_external_auth, default_sat):
    """register the satellite with RH-SSO Server for single sign-on"""
    client_id = get_rhsso_client_id()
    create_mapper(GROUP_MEMBERSHIP_MAPPER, client_id)
    audience_mapper = copy.deepcopy(AUDIENCE_MAPPER)
    audience_mapper['config']['included.client.audience'] = audience_mapper['config'][
        'included.client.audience'
    ].format(rhsso_host=default_sat)
    create_mapper(audience_mapper, client_id)
    set_the_redirect_uri()


@pytest.mark.external_auth
@pytest.fixture(scope='session')
def enroll_idm_and_configure_external_auth(default_sat):
    """Enroll the Satellite6 Server to an IDM Server."""
    ipa_host = ContentHost(settings.ipa.hostname)
    default_sat.execute(
        'yum -y --disableplugin=foreman-protector install ipa-client ipa-admintools'
    )
    ipa_host.execute(f'echo {settings.ipa.password} | kinit admin')
    output = default_sat.execute(f'ipa host-find {default_sat.hostname}')
    if output.status != 0:
        result = ipa_host.execute(f'ipa host-add --random {default_sat.hostname}')
        for line in result.stdout.splitlines():
            if 'Random password' in line:
                _, password = line.split(': ', 2)
                break
        ipa_host.execute(f'ipa service-add HTTP/{default_sat.hostname}')
        _, domain = settings.ipa.hostname.split('.', 1)
        result = default_sat.execute(
            f"ipa-client-install --password '{password}' "
            f'--domain {domain} '
            f'--server {settings.ipa.hostname} '
            f'--realm {domain.upper()} -U'
        )
        if result.status not in [0, 3]:
            CLIReturnCodeError(
                result.status,
                result.stderr,
            )


@pytest.fixture(scope='session')
def configure_realm():
    """Configure realm"""
    realm = settings.upgrade.vm_domain.upper()
    run_command(cmd=f'echo "{settings.ipa.keytab}" > /root/freeipa.keytab')
    run_command(cmd='mv /root/freeipa.keytab /etc/foreman-proxy')
    run_command(cmd='chown foreman-proxy:foreman-proxy /etc/foreman-proxy/freeipa.keytab')
    run_command(
        cmd='satellite-installer --foreman-proxy-realm true '
        f'--foreman-proxy-realm-principal realm-proxy@{realm} '
        f'--foreman-proxy-dhcp-nameservers {socket.gethostbyname(settings.ipa.hostname)}'
    )
    run_command(cmd='cp /etc/ipa/ca.crt /etc/pki/ca-trust/source/anchors/ipa.crt')
    run_command(cmd='update-ca-trust enable ; update-ca-trust')
    run_command(cmd='service foreman-proxy restart')


@pytest.fixture()
def rhsso_setting_setup(destructive_sat, request):
    """Update the RHSSO setting and revert it in cleanup"""
    update_rhsso_settings_in_satellite()
    yield
    update_rhsso_settings_in_satellite(revert=True)


@pytest.fixture()
def rhsso_setting_setup_with_timeout(destructive_sat, rhsso_setting_setup, request):
    """Update the RHSSO setting with timeout setting and revert it in cleanup"""
    setting_entity = entities.Setting().search(query={'search': 'name=idle_timeout'})[0]
    setting_entity.value = 1
    setting_entity.update({'value'})
    yield
    setting_entity.value = 30
    setting_entity.update({'value'})


@pytest.mark.external_auth
@pytest.fixture(scope='session')
def enroll_ad_and_configure_external_auth(request, ad_data):
    """Enroll Satellite Server to an AD Server."""
    auth_type = request.param.lower()
    ad_data = ad_data('2019') if '2019' in auth_type else ad_data()
    packages = (
        'sssd adcli realmd ipa-python-compat krb5-workstation '
        'samba-common-tools gssproxy nfs-utils ipa-client'
    )
    realm = ad_data.realm
    workgroup = ad_data.workgroup

    default_content = f'[global]\nserver = unused\nrealm = {realm}'
    keytab_content = (
        f'[global]\nworkgroup = {workgroup}\nrealm = {realm}'
        f'\nkerberos method = system keytab\nsecurity = ads'
    )

    # install the required packages
    run_command(cmd=f'yum -y --disableplugin=foreman-protector install {packages}')

    # update the AD name server
    run_command(cmd='chattr -i /etc/resolv.conf')
    line_number = run_command(
        cmd="awk -v search='nameserver' '$0~search{print NR; exit}' /etc/resolv.conf"
    )
    run_command(cmd=f'sed -i "{line_number}i nameserver {ad_data.nameserver}" /etc/resolv.conf')
    run_command(cmd='chattr +i /etc/resolv.conf')

    # join the realm
    run_command(cmd=f'echo {settings.ldap.password} | realm join -v {realm}')
    run_command(cmd='touch /etc/ipa/default.conf')
    run_command(cmd=f'echo "{default_content}" > /etc/ipa/default.conf')
    run_command(cmd=f'echo "{keytab_content}" > /etc/net-keytab.conf')

    # gather the apache id
    result = run_command(cmd='id -u apache')
    id_apache = result
    http_conf_content = (
        f'[service/HTTP]\nmechs = krb5\ncred_store = keytab:/etc/krb5.keytab'
        f'\ncred_store = ccache:/var/lib/gssproxy/clients/krb5cc_%U'
        f'\neuid = {id_apache}'
    )

    # register the satellite as client for external auth
    run_command(cmd=f'echo "{http_conf_content}" > /etc/gssproxy/00-http.conf')
    token_command = (
        'KRB5_KTNAME=FILE:/etc/httpd/conf/http.keytab net ads keytab add HTTP '
        '-U administrator -d3 -s /etc/net-keytab.conf'
    )
    run_command(cmd=f'echo {settings.ldap.password} | {token_command}')
    run_command(cmd='chown root.apache /etc/httpd/conf/http.keytab')
    run_command(cmd='chmod 640 /etc/httpd/conf/http.keytab')
