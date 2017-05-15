"""Smoke tests to check installation health

:Requirement: Installer

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: INSTALLER

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re
from six.moves import zip

from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION
from robottelo.decorators import tier1
from robottelo.helpers import get_host_info
from robottelo.log import LogFile
from robottelo.test import TestCase

INSTALLER_OPTIONS = set([
    u'--foreman-proxy-oauth-consumer-key', u'--foreman-proxy-http-port',
    u'--foreman-db-password', u'--foreman-admin-password',
    u'--foreman-proxy-libvirt-connection', u'--certs-server-ca-name',
    u'--certs-org-unit', u'--dont-save-answers', u'--interactive',
    u'--foreman-proxy-dhcp-option-domain', u'--foreman-loggers',
    u'--foreman-proxy-dns-ttl', u'-S', u'--foreman-client-ssl-ca',
    u'--katello-user', u'--foreman-proxy-dns-reverse',
    u'--katello-num-pulp-workers', u'--foreman-proxy-dns-provider', u'-d',
    u'--disable-scenario', u'--certs-org',
    u'--foreman-proxy-tftp-servername', u'--[no-]enable-foreman', u'-l',
    u'--foreman-email-smtp-user-name', u'-n', u'-i', u'-h', u'-v', u'-p',
    u'-s', u'--foreman-db-type', u'--foreman-proxy-dns-forwarders',
    u'--foreman-proxy-gpgcheck', u'--foreman-ipa-manage-sssd',
    u'--disable-system-checks', u'--certs-server-ca-cert', u'--full-help',
    u'--foreman-user-groups', u'--foreman-proxy-log-buffer',
    u'--[no-]enable-foreman-plugin-bootdisk',
    u'--foreman-proxy-oauth-effective-user',
    u'--foreman-proxy-dhcp-provider', u'--foreman-proxy-puppetrun-cmd',
    u'--certs-ca-common-name', u'--foreman-proxy-bmc-listen-on',
    u'--[no-]enable-foreman-proxy-plugin-discovery',
    u'--foreman-proxy-log', u'--foreman-proxy-tftp-listen-on',
    u'--foreman-plugin-discovery-source-url', u'--[no-]enable-katello',
    u'--scenario', u'--certs-node-fqdn', u'--foreman-passenger-interface',
    u'--capsule-parent-fqdn', u'--foreman-proxy-puppetca-cmd',
    u'--katello-enable-ostree', u'--foreman-proxy-realm-provider',
    u'--[no-]enable-foreman-plugin-tasks', u'--katello-log-dir',
    u'--katello-oauth-secret', u'--foreman-proxy-manage-puppet-group',
    u'--foreman-proxy-tftp-managed', u'--foreman-proxy-dhcp-subnets',
    u'--foreman-proxy-plugin-discovery-source-url',
    u'--foreman-proxy-puppetrun-provider', u'--reset',
    u'--foreman-db-username', u'--certs-ssl-build-dir',
    u'--foreman-oauth-consumer-secret', u'--foreman-proxy-manage-sudoersd',
    u'--certs-skip-check', u'--foreman-email-smtp-port',
    u'--foreman-server-ssl-port', u'--foreman-db-host',
    u'--foreman-proxy-version', u'--skip-checks-i-know-better',
    u'--foreman-proxy-dhcp-nameservers', u'--katello-user-groups',
    u'--foreman-proxy-dhcp-key-secret', u'--certs-user',
    u'--foreman-websockets-ssl-key', u'--foreman-unattended',
    u'--[no-]enable-foreman-proxy', u'--foreman-proxy-ssl-key',
    u'--foreman-vhost-priority', u'--foreman-proxy-libvirt-network',
    u'--foreman-proxy-dhcp-range', u'--foreman-proxy-puppet-group',
    u'--foreman-server-port', u'--foreman-db-manage',
    u'--foreman-oauth-map-users', u'--foreman-proxy-puppetssh-wait',
    u'--foreman-proxy-mcollective-user', u'--foreman-proxy-foreman-ssl-ca',
    u'--foreman-db-port', u'--foreman-proxy-puppet-ssl-key',
    u'--foreman-ipa-authentication', u'--foreman-authentication',
    u'--foreman-proxy-puppet-use-cache',
    u'--foreman-proxy-puppet-use-environment-api', u'--noop',
    u'--certs-generate', u'--foreman-proxy-oauth-consumer-secret',
    u'--foreman-proxy-registered-name',
    u'--foreman-proxy-puppetssh-keyfile', u'--foreman-db-adapter',
    u'--foreman-proxy-tftp-manage-wget', u'--ignore-undocumented',
    u'--foreman-websockets-ssl-cert', u'--foreman-proxy-puppetssh-sudo',
    u'--foreman-proxy-freeipa-remove-dns', u'--foreman-puppetrun',
    u'--certs-update-server', u'--foreman-configure-epel-repo',
    u'--foreman-http-keytab', u'--foreman-proxy-bmc-default-provider',
    u'--foreman-proxy-dhcp-config', u'--foreman-keepalive-timeout',
    u'--certs-default-ca-name', u'--[no-]colors',
    u'--foreman-proxy-puppetssh-user',
    u'--foreman-proxy-puppetca-listen-on', u'--foreman-websockets-encrypt',
    u'--foreman-proxy-dhcp-listen-on',
    u'--foreman-proxy-registered-proxy-url', u'--certs-deploy',
    u'--certs-group', u'--foreman-passenger-min-instances',
    u'--foreman-proxy-dns-tsig-principal',
    u'--foreman-proxy-salt-puppetrun-cmd', u'--foreman-plugin-version',
    u'--foreman-selinux', u'--foreman-server-ssl-cert',
    u'--foreman-proxy-puppetca', u'--foreman-proxy-puppet-listen-on',
    u'--foreman-db-sslmode', u'--foreman-proxy-ssl-cert',
    u'--foreman-proxy-puppetdir', u'--foreman-proxy-dns-server',
    u'--foreman-passenger-prestart',
    u'--foreman-proxy-plugin-remote-execution-ssh-local-working-dir',
    u'--foreman-server-ssl-key', u'--foreman-email-smtp-domain',
    u'--foreman-proxy-user', u'--certs-server-cert-req',
    u'--katello-group', u'--foreman-initial-location',
    u'--foreman-puppet-home', u'--[no-]enable-foreman-proxy-plugin-pulp',
    u'--certs-update-all', u'--capsule-certs-tar',
    u'--foreman-db-database', u'--foreman-passenger-start-timeout',
    u'--foreman-proxy-custom-repo', u'--capsule-enable-ostree',
    u'--certs-city', u'--katello-proxy-url', u'--foreman-puppet-ssldir',
    u'--foreman-proxy-dhcp-omapi-port', u'--katello-max-keep-alive',
    u'--list-scenarios', u'--katello-package-names', u'--log-level',
    u'--foreman-admin-last-name',
    u'--[no-]enable-foreman-plugin-discovery',
    u'--foreman-proxy-puppet-ssl-ca', u'--foreman-group',
    u'--foreman-proxy-foreman-base-url', u'--foreman-proxy-bmc',
    u'--foreman-proxy-plugin-openscap-contentdir', u'--foreman-db-pool',
    u'--certs-state', u'--foreman-email-smtp-address',
    u'--foreman-passenger', u'--certs-update-server-ca',
    u'--foreman-proxy-keyfile', u'--katello-repo-export-dir',
    u'--foreman-plugin-discovery-install-images',
    u'--[no-]enable-foreman-proxy-plugin-openscap', u'--verbose-log-level',
    u'--katello-proxy-port', u'--katello-proxy-password',
    u'--foreman-proxy-puppetssh-command', u'--foreman-keepalive',
    u'--foreman-server-ssl-certs-dir', u'--foreman-proxy-dhcp-gateway',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-dir',
    u'--foreman-proxy-log-buffer-errors', u'--foreman-serveraliases',
    u'--foreman-proxy-repo', u'--foreman-proxy-logs',
    u'--foreman-proxy-dns-interface', u'--foreman-proxy-dhcp-key-name',
    u'--foreman-proxy-plugin-openscap-openscap-send-log-file',
    u'--foreman-admin-first-name', u'--katello-oauth-key',
    u'--foreman-proxy-plugin-discovery-image-name',
    u'--foreman-pam-service', u'--foreman-email-smtp-password',
    u'--foreman-version',
    u'--foreman-proxy-plugin-remote-execution-ssh-generate-keys',
    u'--foreman-repo', u'--foreman-proxy-foreman-ssl-key',
    u'--certs-server-cert', u'--foreman-proxy-use-sudoersd',
    u'--foreman-servername',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-keygen',
    u'--certs-pki-dir', u'--foreman-oauth-active',
    u'--foreman-plugin-tasks-package', u'--foreman-proxy-dns',
    u'--foreman-plugin-tasks-service', u'--foreman-proxy-puppet-user',
    u'--enable-scenario', u'--foreman-proxy-trusted-hosts',
    u'--foreman-plugin-discovery-image-name',
    u'--foreman-server-ssl-chain', u'--foreman-ssl',
    u'--foreman-proxy-dhcp', u'--foreman-proxy-puppet-ssl-cert',
    u'--foreman-configure-scl-repo',
    u'--foreman-proxy-plugin-remote-execution-ssh-remote-working-dir',
    u'--foreman-proxy-ssl-ca', u'--foreman-proxy-ssl-disabled-ciphers',
    u'--foreman-max-keepalive-requests', u'--foreman-proxy-realm',
    u'--clear-pulp-content', u'--foreman-proxy-dhcp-server',
    u'--[no-]enable-foreman-plugin-remote-execution',
    u'--compare-scenarios', u'--foreman-proxy-customrun-args',
    u'--foreman-rails-env', u'--foreman-proxy-log-level',
    u'--foreman-initial-organization', u'--foreman-proxy-dns-zone',
    u'--migrations-only', u'--foreman-proxy-register-in-foreman',
    u'--certs-ca-expiration', u'--clear-puppet-environments', u'--help',
    u'--foreman-logging-level', u'--color-of-background',
    u'--foreman-proxy-plugin-discovery-install-images',
    u'--foreman-oauth-consumer-key', u'--foreman-client-ssl-key',
    u'--[no-]enable-foreman-proxy-plugin-remote-execution-ssh',
    u'--foreman-email-conf', u'--foreman-proxy-plugin-openscap-failed-dir',
    u'--foreman-proxy-http', u'--verbose', u'--certs-regenerate-ca',
    u'--foreman-proxy-templates',
    u'--foreman-proxy-tftp-syslinux-filenames',
    u'--foreman-proxy-realm-principal', u'--foreman-foreman-url',
    u'--foreman-proxy-template-url', u'--katello-cdn-ssl-version',
    u'--upgrade-puppet', u'--foreman-admin-username',
    u'--foreman-proxy-dhcp-leases', u'--foreman-proxy-dhcp-search-domains',
    u'--foreman-plugin-discovery-tftp-root', u'--foreman-use-vhost',
    u'--foreman-proxy-plugin-openscap-reportsdir',
    u'--foreman-proxy-plugin-version', u'--foreman-email-source',
    u'--foreman-admin-email', u'--foreman-proxy-ssl-port',
    u'--[no-]enable-foreman-plugin-openscap', u'--foreman-proxy-puppet',
    u'--foreman-proxy-customrun-cmd', u'--katello-config-dir',
    u'--foreman-proxy-realm-listen-on', u'--foreman-proxy-tftp',
    u'--foreman-proxy-tftp-root', u'--[no-]enable-capsule',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-file',
    u'--foreman-email-smtp-authentication', u'--foreman-proxy-bind-host',
    u'--profile', u'--certs-expiration', u'--foreman-passenger-ruby',
    u'--certs-country', u'--force', u'--foreman-locations-enabled',
    u'--foreman-passenger-ruby-package', u'--foreman-server-ssl-ca',
    u'--foreman-proxy-templates-listen-on', u'--foreman-app-root',
    u'--capsule-puppet-ca-proxy', u'--foreman-proxy-dhcp-managed',
    u'--foreman-proxy-dns-managed',
    u'--capsule-puppet-server-implementation', u'--katello-proxy-username',
    u'--foreman-proxy-dir', u'--foreman-proxy-tftp-dirs',
    u'--foreman-email-delivery-method', u'--foreman-proxy-dns-tsig-keytab',
    u'--foreman-proxy-foreman-ssl-cert',
    u'--foreman-proxy-plugin-openscap-configure-openscap-repo',
    u'--foreman-proxy-plugin-openscap-spooldir', u'--foreman-manage-user',
    u'--foreman-proxy-ssl', u'--foreman-proxy-ssldir',
    u'--katello-post-sync-token', u'--upgrade', u'--certs-server-key',
    u'--[no-]enable-certs', u'--foreman-proxy-dhcp-interface',
    u'--foreman-client-ssl-cert', u'--foreman-organizations-enabled',
    u'--foreman-proxy-realm-keytab', u'--foreman-proxy-puppet-url',
    u'--foreman-proxy-plugin-discovery-tftp-root',
    u'--foreman-proxy-logs-listen-on', u'--foreman-custom-repo',
    u'--foreman-gpgcheck', u'--certs-regenerate',
    u'--foreman-plugin-prefix', u'--foreman-user',
    u'--foreman-server-ssl-crl',
    u'--foreman-proxy-ensure-packages-version',
    u'--foreman-proxy-dns-listen-on', u'--force-upgrade-steps',
    u'--capsule-puppet', u'--certs-log-dir'
])


class SELinuxTestCase(TestCase):
    """Checks SELinux installation status"""

    version_regex = re.compile(r'((\d\.?)+[-.]\d)')

    @tier1
    def test_positive_foreman_module(self):
        """Check if SELinux foreman module has the right version

        :id: a0736b3a-3d42-4a09-a11a-28c1d58214a5

        :expectedresults: Foreman RPM and SELinux module versions match
        """
        rpm_result = ssh.command('rpm -q foreman-selinux')
        self.assertEqual(rpm_result.return_code, 0)
        semodule_result = ssh.command('semodule -l | grep foreman')
        self.assertEqual(semodule_result.return_code, 0)

        # Sample rpm output: foreman-selinux-1.7.2.8-1.el7sat.noarch
        rpm_version = self.version_regex.search(
            ''.join(rpm_result.stdout)).group(1)
        # Sample semodule output: foreman        1.7.2.8
        semodule_version = self.version_regex.search(
            ''.join(semodule_result.stdout)).group(1)

        rpm_version = rpm_version[:-2]
        self.assertEqual(rpm_version.replace('-', '.'), semodule_version)

    @tier1
    def test_positive_check_installer_services(self):
        """Check if services start correctly

        :id: 85fd4388-6d94-42f5-bed2-24be38e9f104

        :expectedresults: All services {'elasticsearch', 'foreman-proxy',
            'foreman-tasks', 'httpd', 'mongod', 'postgresql',
            'pulp_celerybeat', 'pulp_resource_manager', 'pulp_workers',
            'qdrouterd', 'qpidd', 'tomcat'} are started
        """
        major_version = get_host_info()[1]
        services = (
            'foreman-proxy',
            'foreman-tasks',
            'httpd',
            'mongod',
            'postgresql',
            'pulp_celerybeat',
            'pulp_resource_manager',
            'pulp_streamer',
            'pulp_workers',
            'qdrouterd',
            'qpidd',
            'smart_proxy_dynflow_core',
            'squid',
            'tomcat6' if major_version == RHEL_6_MAJOR_VERSION else 'tomcat',
        )

        # check `services` status using service command
        if major_version >= RHEL_7_MAJOR_VERSION:
            status_format = 'systemctl status {0}'
        else:
            status_format = 'service {0} status'

        for service in services:
            with self.subTest(service):
                result = ssh.command(status_format.format(service))
                self.assertEqual(result.return_code, 0)
                self.assertEqual(len(result.stderr), 0)

        # check status reported by hammer ping command
        result = ssh.command(u'hammer -u {0[0]} -p {0[1]} ping'.format(
            settings.server.get_credentials()
        ))

        # iterate over the lines grouping every 3 lines
        # example [1, 2, 3, 4, 5, 6] will return [(1, 2, 3), (4, 5, 6)]
        for service, status, server_response in zip(
                *[iter(result.stdout)] * 3):
            service = service.replace(':', '').strip()
            status = status.split(':')[1].strip().lower()
            server_response = server_response.split(':', 1)[1].strip()
            self.assertEqual(
                status, 'ok',
                '{0} responded with {1}'.format(service, server_response)
            )

    @tier1
    def test_positive_check_installer_logfile(self):
        """Look for ERROR or FATAL references in logfiles

        :id: 80537809-8be4-42db-9cc8-5155378ee4d4

        :Steps: search all relevant logfiles for ERROR/FATAL

        :expectedresults: No ERROR/FATAL notifcations occur in {katello-jobs,
            tomcat6, foreman, pulp, passenger-analytics, httpd, foreman_proxy,
            elasticsearch, postgresql, mongod} logfiles.
        """
        logfiles = (
            {
                'path': '/var/log/candlepin/error.log',
                'pattern': r'ERROR'
            },
            {
                'path': '/var/log/foreman-installer/satellite.log',
                'pattern': r'\[\s*(ERROR|FATAL)'
            },
        )

        for logfile in logfiles:
            try:
                log = LogFile(logfile['path'], logfile['pattern'])
            except IOError:
                self.fail(
                    'Could not find {0} file on server'.format(logfile['path'])
                )
            self.assertEqual(len(log.filter()), 0)


def extract_params(lst):
    """Generator funcion to extract satellite installer params

    :param lst: list of string
    :return: generator with all params
    """
    for line in lst:
        line = line.strip()
        first_2_tokens = line.split()[:2]
        for token in first_2_tokens:
            if token[0] == '-':
                yield token.replace(',', '')


class InstallerParamsTestCase(TestCase):
    """Checks installer API changes"""

    @tier1
    def test_installer_options_and_flags(self):
        """Look for changes on installer options and flags

        :id: a51d3b9f-f347-4a96-a31a-770349db08c7

        :Steps:
            1. parse installer options and flags
            2. compare with last options

        :expectedresults: Ideally options should not change on zstreams.
            Documentation must be updated accordingly when such changes occur.
            So when this test fail we QE can act on it, asking dev if
            changes occurs on zstream and checking docs are up to date.
        """
        stdout = ssh.command('satellite-installer --help').stdout

        self.assertEqual(
            INSTALLER_OPTIONS,
            set(extract_params(stdout or []))
        )
