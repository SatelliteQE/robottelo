import copy
import socket

import pytest
from box import Box
from broker import Broker
from nailgun import entities

from robottelo.api.utils import update_rhsso_settings_in_satellite
from robottelo.cli.base import CLIReturnCodeError
from robottelo.config import settings
from robottelo.constants import AUDIENCE_MAPPER
from robottelo.constants import CERT_PATH
from robottelo.constants import GROUP_MEMBERSHIP_MAPPER
from robottelo.constants import HAMMER_CONFIG
from robottelo.constants import HAMMER_SESSIONS
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.datafactory import gen_string
from robottelo.hosts import ContentHost
from robottelo.rhsso_utils import create_mapper
from robottelo.rhsso_utils import get_rhsso_client_id
from robottelo.rhsso_utils import set_the_redirect_uri
from robottelo.utils.installer import InstallerCommand
from robottelo.utils.issue_handlers import is_open


@pytest.fixture()
def ldap_cleanup():
    """this is an extra step taken to clean any existing ldap source"""
    ldap_auth_sources = entities.AuthSourceLDAP().search()
    for ldap_auth in ldap_auth_sources:
        users = entities.User(auth_source=ldap_auth).search()
        for user in users:
            user.delete()
        ldap_auth.delete()
    yield


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

        return Box(ad_server_details)

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
def auth_source(ldap_cleanup, module_org, module_location, ad_data):
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
def auth_source_ipa(ldap_cleanup, module_org, module_location, ipa_data):
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
def auth_source_open_ldap(ldap_cleanup, module_org, module_location, open_ldap_data):
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
def ldap_auth_source(
    request,
    module_org,
    module_location,
    ldap_cleanup,
    ad_data,
    ipa_data,
    open_ldap_data,
    module_target_sat,
):
    auth_type = request.param.lower()
    if 'ad' in auth_type:
        ad_data = ad_data('2019') if '2019' in auth_type else ad_data()
        # entity create with AD settings
        auth_source = module_target_sat.api.AuthSourceLDAP(
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
        auth_source = module_target_sat.api.AuthSourceLDAP(
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
        auth_source = module_target_sat.api.AuthSourceLDAP(
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


@pytest.fixture
def auth_data(request, ad_data, ipa_data):
    auth_type = request.param.lower()
    if 'ad' in auth_type:
        ad_data = ad_data('2019') if '2019' in auth_type else ad_data()
        ad_data['server_type'] = LDAP_SERVER_TYPE['UI']['ad']
        ad_data['attr_login'] = LDAP_ATTR['login_ad']
        ad_data['auth_type'] = auth_type
        return ad_data
    elif auth_type == 'ipa':
        ipa_data['server_type'] = LDAP_SERVER_TYPE['UI']['ipa']
        ipa_data['attr_login'] = LDAP_ATTR['login']
        ipa_data['auth_type'] = auth_type
        return ipa_data


@pytest.fixture(scope='module')
def enroll_configure_rhsso_external_auth(module_target_sat):
    """Enroll the Satellite6 Server to an RHSSO Server."""
    module_target_sat.execute(
        'yum -y --disableplugin=foreman-protector install '
        'mod_auth_openidc keycloak-httpd-client-install'
    )
    # if target directory not given it is installing in /usr/local/lib64
    module_target_sat.execute('python3 -m pip install lxml -t /usr/lib64/python3.6/site-packages')
    module_target_sat.execute(
        f'openssl s_client -connect {settings.rhsso.host_name} -showcerts </dev/null 2>/dev/null| '
        f'sed "/BEGIN CERTIFICATE/,/END CERTIFICATE/!d" > {CERT_PATH}/rh-sso.crt'
    )
    module_target_sat.execute(
        f'sshpass -p "{settings.rhsso.rhsso_password}" scp -o "StrictHostKeyChecking no" '
        f'root@{settings.rhsso.host_name}:/root/ca_certs/*.crt {CERT_PATH}'
    )
    module_target_sat.execute('update-ca-trust')
    module_target_sat.execute(
        f'echo {settings.rhsso.rhsso_password} | keycloak-httpd-client-install --app-name foreman-openidc \
                --keycloak-server-url {settings.rhsso.host_url} \
                --keycloak-admin-username "admin" \
                --keycloak-realm "{settings.rhsso.realm}" \
                --keycloak-admin-realm master \
                --keycloak-auth-role root-admin -t openidc -l /users/extlogin --force'
    )
    if is_open('BZ:2113905'):
        module_target_sat.execute(
            r"sed -i -e '$aapache::default_mods:\n  - authn_core' "
            "/etc/foreman-installer/custom-hiera.yaml"
        )

    module_target_sat.execute(
        f'satellite-installer --foreman-keycloak true '
        f"--foreman-keycloak-app-name 'foreman-openidc' "
        f"--foreman-keycloak-realm '{settings.rhsso.realm}' ",
        timeout=1000000,
    )
    module_target_sat.execute('systemctl restart httpd')


@pytest.fixture(scope='module')
def enable_external_auth_rhsso(enroll_configure_rhsso_external_auth, module_target_sat):
    """register the satellite with RH-SSO Server for single sign-on"""
    client_id = get_rhsso_client_id(module_target_sat)
    create_mapper(GROUP_MEMBERSHIP_MAPPER, client_id)
    audience_mapper = copy.deepcopy(AUDIENCE_MAPPER)
    audience_mapper['config']['included.client.audience'] = audience_mapper['config'][
        'included.client.audience'
    ].format(rhsso_host=module_target_sat.hostname)
    create_mapper(audience_mapper, client_id)
    set_the_redirect_uri(module_target_sat)


def enroll_idm_and_configure_external_auth(sat):
    """Enroll the Satellite6 Server to an IDM Server."""
    ipa_host = ContentHost(settings.ipa.hostname)
    result = sat.execute(
        'yum -y --disableplugin=foreman-protector install ipa-client ipa-admintools'
    )
    if result.status != 0:
        raise CLIReturnCodeError(result.status, result.stderr, 'Failed to install ipa client')
    ipa_host.execute(f'echo {settings.ipa.password} | kinit admin')
    result = ipa_host.execute(f'ipa host-find {sat.hostname}')
    if result.status == 0:
        disenroll_idm(sat)
    result = ipa_host.execute(f'ipa host-add --random {sat.hostname}')
    for line in result.stdout.splitlines():
        if 'Random password' in line:
            _, password = line.split(': ', 2)
            break
    ipa_host.execute(f'ipa service-add HTTP/{sat.hostname}')
    _, domain = settings.ipa.hostname.split('.', 1)
    result = sat.execute(
        f"ipa-client-install --password '{password}' "
        f'--domain {domain} '
        f'--server {settings.ipa.hostname} '
        f'--realm {domain.upper()} -U'
    )
    if result.status not in [0, 3]:
        raise CLIReturnCodeError(result.status, result.stderr, 'Failed to enable ipa client')
    result = sat.install(InstallerCommand('foreman-ipa-authentication true'))
    assert result.status == 0, 'Installer failed to enable IPA authentication.'
    sat.cli.Service.restart()


def disenroll_idm(sat):
    ipa_host = ContentHost(settings.ipa.hostname)
    ipa_host.execute(f'ipa service-del HTTP/{sat.hostname}')
    ipa_host.execute(f'ipa host-del {sat.hostname}')


@pytest.mark.external_auth
@pytest.fixture(scope='module')
def module_enroll_idm_and_configure_external_auth(module_target_sat):
    enroll_idm_and_configure_external_auth(module_target_sat)
    yield
    disenroll_idm(module_target_sat)


@pytest.mark.external_auth
@pytest.fixture
def func_enroll_idm_and_configure_external_auth(target_sat):
    enroll_idm_and_configure_external_auth(target_sat)
    yield
    disenroll_idm(target_sat)


@pytest.fixture(scope='module')
def configure_realm(session_target_sat):
    """Configure realm"""
    realm = settings.upgrade.vm_domain.upper()
    session_target_sat.execute(f'curl -o /root/freeipa.keytab {settings.ipa.keytab_url}')
    session_target_sat.execute('mv /root/freeipa.keytab /etc/foreman-proxy')
    session_target_sat.execute(
        'chown foreman-proxy:foreman-proxy /etc/foreman-proxy/freeipa.keytab'
    )
    session_target_sat.execute(
        'satellite-installer --foreman-proxy-realm true '
        f'--foreman-proxy-realm-principal realm-proxy@{realm} '
        f'--foreman-proxy-dhcp-nameservers {socket.gethostbyname(settings.ipa.hostname)}'
    )
    session_target_sat.execute('cp /etc/ipa/ca.crt /etc/pki/ca-trust/source/anchors/ipa.crt')
    session_target_sat.execute('update-ca-trust enable ; update-ca-trust')
    session_target_sat.execute('service foreman-proxy restart')


@pytest.fixture(scope="module")
def rhsso_setting_setup(module_target_sat):
    """Update the RHSSO setting and revert it in cleanup"""
    update_rhsso_settings_in_satellite(sat=module_target_sat)
    yield
    update_rhsso_settings_in_satellite(revert=True, sat=module_target_sat)


@pytest.fixture(scope="module")
def rhsso_setting_setup_with_timeout(module_target_sat, rhsso_setting_setup):
    """Update the RHSSO setting with timeout setting and revert it in cleanup"""
    setting_entity = module_target_sat.api.Setting().search(query={'search': 'name=idle_timeout'})[
        0
    ]
    setting_entity.value = 1
    setting_entity.update({'value'})
    yield
    setting_entity.value = 30
    setting_entity.update({'value'})


def enroll_ad_and_configure_external_auth(request, ad_data, sat):
    """Enroll Satellite Server to an AD Server."""
    auth_type = getattr(request, 'param', 'AD_2016')
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
    sat.execute(f'yum -y --disableplugin=foreman-protector install {packages}')

    # update the AD name server
    sat.execute('chattr -i /etc/resolv.conf')
    line_number = int(
        sat.execute(
            "awk -v search='nameserver' '$0~search{print NR; exit}' /etc/resolv.conf"
        ).stdout
    )
    sat.execute(f'sed -i "{line_number}i nameserver {ad_data.nameserver}" /etc/resolv.conf')
    sat.execute('chattr +i /etc/resolv.conf')

    # join the realm
    sat.execute(
        f'echo {settings.ldap.password} | realm join -v {realm} --membership-software=samba'
    )
    sat.execute('touch /etc/ipa/default.conf')
    sat.execute(f'echo "{default_content}" > /etc/ipa/default.conf')
    sat.execute(f'echo "{keytab_content}" > /etc/net-keytab.conf')

    # gather the apache id
    id_apache = str(sat.execute('id -u apache')).strip()
    http_conf_content = (
        f'[service/HTTP]\nmechs = krb5\ncred_store = keytab:/etc/krb5.keytab'
        f'\ncred_store = ccache:/var/lib/gssproxy/clients/krb5cc_%U'
        f'\neuid = {id_apache}'
    )

    # register the satellite as client for external auth
    sat.execute(f'echo "{http_conf_content}" > /etc/gssproxy/00-http.conf')
    token_command = (
        'KRB5_KTNAME=FILE:/etc/httpd/conf/http.keytab net ads keytab add HTTP '
        '-U administrator -d3 -s /etc/net-keytab.conf'
    )
    sat.execute(f'echo {settings.ldap.password} | {token_command}')
    sat.execute('chown root.apache /etc/httpd/conf/http.keytab')
    sat.execute('chmod 640 /etc/httpd/conf/http.keytab')

    # enable the foreman-ipa-authentication feature
    result = sat.install(InstallerCommand('foreman-ipa-authentication true'))
    assert result.status == 0

    # add foreman ad_gp_map_service (BZ#2117523)
    line_number = int(
        sat.execute(
            "awk -v search='domain/' '$0~search{print NR; exit}' /etc/sssd/sssd.conf"
        ).stdout
    )
    sat.execute(f'sed -i "{line_number + 1}i ad_gpo_map_service = +foreman" /etc/sssd/sssd.conf')
    sat.execute('systemctl restart sssd.service')

    # unset GssapiLocalName (BZ#1787630)
    sat.execute(
        'sed -i -e "s/GssapiLocalName.*On/GssapiLocalName Off/g" '
        '/etc/httpd/conf.d/05-foreman-ssl.d/auth_gssapi.conf'
    )
    sat.execute('systemctl restart gssproxy.service')
    sat.execute('systemctl enable gssproxy.service')

    # restart the deamon and httpd services
    httpd_service_content = (
        '.include /lib/systemd/system/httpd.service\n[Service]' '\nEnvironment=GSS_USE_PROXY=1'
    )
    sat.execute(f'echo "{httpd_service_content}" > /etc/systemd/system/httpd.service')
    sat.execute('systemctl daemon-reload && systemctl restart httpd.service')


@pytest.mark.external_auth
@pytest.fixture(scope='module')
def module_enroll_ad_and_configure_external_auth(request, ad_data, module_target_sat):
    enroll_ad_and_configure_external_auth(request, ad_data, module_target_sat)


@pytest.mark.external_auth
@pytest.fixture
def func_enroll_ad_and_configure_external_auth(request, ad_data, target_sat):
    enroll_ad_and_configure_external_auth(request, ad_data, target_sat)


@pytest.mark.external_auth
@pytest.fixture
def configure_hammer_negotiate(parametrized_enrolled_sat):
    """Configures hammer to use sessions and negotitate auth."""
    parametrized_enrolled_sat.execute(f'mv {HAMMER_CONFIG} {HAMMER_CONFIG}.backup')
    cfg = ':foreman:\n  :default_auth_type: Negotiate_Auth\n  :use_sessions: true\n'
    parametrized_enrolled_sat.execute(f"echo '{cfg}' > {HAMMER_CONFIG}")
    yield
    parametrized_enrolled_sat.execute(f'mv -f {HAMMER_CONFIG}.backup {HAMMER_CONFIG}')


@pytest.fixture
def sessions_tear_down(parametrized_enrolled_sat):
    """Destroy Kerberos and hammer sessions on teardown."""
    yield
    parametrized_enrolled_sat.execute('kdestroy')
    parametrized_enrolled_sat.execute(
        f'rm -f {HAMMER_SESSIONS}/https_{parametrized_enrolled_sat.hostname}'
    )


@pytest.fixture(scope='module', params=['IDM', 'AD'])
def parametrized_enrolled_sat(
    request,
    satellite_factory,
    ad_data,
):
    """Yields a Satellite enrolled into [IDM, AD] as parameter."""
    new_sat = satellite_factory()
    new_sat.register_to_cdn()
    if 'IDM' in request.param:
        enroll_idm_and_configure_external_auth(new_sat)
        yield new_sat
        disenroll_idm(new_sat)
    else:
        enroll_ad_and_configure_external_auth(request, ad_data, new_sat)
        yield new_sat
    new_sat.unregister()
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()
