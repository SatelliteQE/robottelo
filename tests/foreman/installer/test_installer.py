"""Smoke tests to check installation health

@Requirement: Installer

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: INSTALLER

@TestType: Functional

@CaseImportance: High

@Upstream: No
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
    u'--foreman-proxy-plugin-openscap-reportsdir', u'-S',
    u'--capsule-qpid-router-broker-addr', u'-d', u'--katello-user-groups',
    u'--[no-]enable-foreman', u'-l', u'-n', u'-i', u'-h', u'-v', u'-p', u'-s',
    u'--foreman-ipa-manage-sssd', u'--foreman-admin-password',
    u'--foreman-proxy-log-buffer', u'--certs-ca-common-name',
    u'--foreman-proxy-bmc-listen-on', u'--foreman-plugin-discovery-source-url',
    u'--foreman-proxy-foreman-ssl-cert', u'--foreman-passenger-interface',
    u'--katello-oauth-secret', u'--foreman-proxy-realm-listen-on',
    u'--foreman-websockets-encrypt', u'--foreman-http-keytab',
    u'--skip-checks-i-know-better', u'--certs-user',
    u'--foreman-proxy-ssl-key', u'--foreman-proxy-puppetrun-provider',
    u'--foreman-proxy-puppet-group', u'--foreman-proxy-puppetrun',
    u'--foreman-proxy-foreman-ssl-ca', u'--foreman-proxy-plugin-pulp-pulp-dir',
    u'--capsule-qpid-router-hub-addr',
    u'--foreman-proxy-plugin-pulp-mongodb-dir', u'--foreman-authentication',
    u'--certs-generate', u'--foreman-proxy-plugin-discovery-tftp-root',
    u'--foreman-proxy-puppetssh-keyfile', u'--foreman-proxy-customrun-args',
    u'--foreman-configure-epel-repo', u'--foreman-proxy-dhcp-nameservers',
    u'--[no-]colors', u'--disable-scenario', u'--foreman-selinux',
    u'--foreman-proxy-plugin-remote-execution-ssh-listen-on',
    u'--foreman-proxy-plugin-pulp-group', u'--certs-ca-expiration',
    u'--foreman-passenger-prestart', u'--foreman-proxy-template-url',
    u'--certs-server-cert-req', u'--foreman-initial-location',
    u'--foreman-puppet-home', u'--capsule-certs-tar', u'--foreman-proxy-bmc',
    u'--foreman-proxy-plugin-pulp-listen-on', u'--certs-update-server-ca',
    u'--foreman-proxy-keyfile', u'--foreman-proxy-plugin-pulp-enabled',
    u'--foreman-proxy-plugin-discovery-image-name',
    u'--foreman-proxy-trusted-hosts', u'--foreman-proxy-dhcp-key-name',
    u'--foreman-proxy-freeipa-remove-dns', u'--foreman-version',
    u'--capsule-pulp-oauth-secret', u'--certs-pki-dir',
    u'--foreman-plugin-tasks-package',
    u'--foreman-plugin-discovery-image-name', u'--foreman-user-groups',
    u'--foreman-proxy-dhcp', u'--foreman-proxy-dhcp-key-secret',
    u'--foreman-proxy-puppet-ssl-key', u'--foreman-proxy-dhcp-server',
    u'--foreman-initial-organization', u'--foreman-repo', u'--full-help',
    u'--foreman-oauth-consumer-key', u'--foreman-proxy-puppetssh-user',
    u'--foreman-proxy-tftp-syslinux-filenames',
    u'--foreman-proxy-realm-principal', u'--foreman-organizations-enabled',
    u'--foreman-plugin-discovery-tftp-root', u'--foreman-admin-email',
    u'--foreman-email-smtp-authentication',
    u'--foreman-proxy-plugin-remote-execution-ssh-enabled',
    u'--foreman-passenger-ruby', u'--foreman-proxy-logs', u'--certs-group',
    u'--foreman-app-root', u'--foreman-proxy-dir', u'--katello-max-keep-alive',
    u'--katello-oauth-key',
    u'--foreman-proxy-plugin-remote-execution-ssh-local-working-dir',
    u'--foreman-oauth-active', u'--[no-]enable-certs',
    u'--foreman-environment', u'--foreman-proxy-realm-keytab',
    u'--foreman-proxy-ssl-port', u'--foreman-proxy-plugin-pulp-pulp-url',
    u'--certs-log-dir', u'--capsule-pulp-master', u'--certs-server-ca-name',
    u'--certs-org-unit', u'--foreman-proxy-plugin-openscap-enabled',
    u'--foreman-apipie-task', u'--foreman-proxy-puppet-ssl-ca', u'--certs-org',
    u'--foreman-proxy-dns-split-config-files',
    u'--foreman-email-smtp-user-name', u'--foreman-proxy-version',
    u'--foreman-db-type', u'--foreman-proxy-tftp-listen-on',
    u'--[no-]enable-katello', u'--scenario', u'--capsule-parent-fqdn',
    u'--[no-]enable-foreman-plugin-tasks', u'--foreman-oauth-map-users',
    u'--foreman-email-smtp-port', u'--foreman-db-host',
    u'--foreman-proxy-tftp-servername', u'--foreman-proxy-tftp-syslinux-root',
    u'--force', u'--[no-]enable-foreman-proxy',
    u'--foreman-proxy-plugin-remote-execution-ssh-remote-working-dir',
    u'--foreman-proxy-dns', u'--foreman-db-username',
    u'--foreman-ipa-authentication',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-file',
    u'--foreman-server-ssl-ca', u'--foreman-locations-enabled',
    u'--foreman-proxy-oauth-consumer-secret', u'--foreman-db-adapter',
    u'--foreman-passenger', u'--foreman-proxy-plugin-pulp-pulpnode-enabled',
    u'--foreman-proxy-dhcp-listen-on', u'--certs-deploy',
    u'--foreman-proxy-puppetca', u'--foreman-proxy-user',
    u'--katello-cdn-ssl-version', u'--foreman-proxy-plugin-pulp-version',
    u'--[no-]enable-foreman-proxy-plugin-openscap',
    u'--foreman-proxy-custom-repo', u'--katello-proxy-url',
    u'--list-scenarios', u'--foreman-proxy-plugin-openscap-contentdir',
    u'--foreman-db-pool', u'--foreman-email-smtp-address',
    u'--foreman-proxy-bmc-default-provider',
    u'--foreman-proxy-dns-tsig-keytab', u'--foreman-proxy-virsh-network',
    u'--verbose-log-level', u'--foreman-proxy-log-buffer-errors',
    u'--foreman-proxy-puppet-user',
    u'--foreman-proxy-plugin-openscap-openscap-send-log-file',
    u'--capsule-qpid-router-agent-port', u'--foreman-proxy-foreman-ssl-key',
    u'--foreman-passenger-ruby-package', u'--foreman-servername',
    u'--foreman-proxy-plugin-openscap-version',
    u'--[no-]enable-foreman-plugin-remote-execution', u'--foreman-db-sslmode',
    u'--foreman-proxy-puppet-cache-location', u'--help',
    u'--foreman-proxy-plugin-discovery-install-images',
    u'--katello-proxy-password', u'--foreman-proxy-plugin-openscap-failed-dir',
    u'--certs-regenerate-ca', u'--foreman-proxy-templates',
    u'--foreman-foreman-url', u'--foreman-admin-username',
    u'--foreman-email-source', u'--[no-]enable-foreman-plugin-openscap',
    u'--katello-config-dir', u'--foreman-proxy-tftp',
    u'--foreman-proxy-puppetrun-listen-on', u'--certs-node-fqdn',
    u'--foreman-proxy-customrun-cmd', u'--foreman-configure-brightbox-repo',
    u'--foreman-proxy-templates-listen-on', u'--capsule-puppet-ca-proxy',
    u'--foreman-proxy-tftp-syslinux-files',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-dir',
    u'--certs-password-file-dir', u'--foreman-proxy-port',
    u'--foreman-proxy-oauth-consumer-key', u'--foreman-gpgcheck',
    u'--foreman-user', u'--foreman-server-ssl-crl',
    u'--foreman-proxy-dns-listen-on', u'--force-upgrade-steps',
    u'--foreman-proxy-http-port', u'--foreman-proxy-dns-provider',
    u'--katello-proxy-port', u'--interactive',
    u'--foreman-proxy-dhcp-option-domain', u'--foreman-loggers',
    u'--foreman-proxy-dns-ttl', u'--foreman-proxy-dns-reverse',
    u'--katello-num-pulp-workers', u'--katello-proxy-username',
    u'--certs-server-ca-cert', u'--[no-]enable-foreman-plugin-bootdisk',
    u'--foreman-proxy-dhcp-vendor',
    u'--[no-]enable-foreman-proxy-plugin-discovery', u'--foreman-proxy-log',
    u'--foreman-plugin-tasks-service',
    u'--foreman-plugin-openscap-configure-openscap-repo',
    u'--capsule-pulp-oauth-key', u'--foreman-proxy-autosign-location',
    u'--certs-skip-check', u'--foreman-manage-user', u'--foreman-proxy-ssl',
    u'--capsule-reverse-proxy', u'--foreman-proxy-puppetssh-wait',
    u'--foreman-db-port', u'--capsule-qpid-router-hub-port',
    u'--certs-default-ca-name', u'--ignore-undocumented',
    u'--capsule-pulp-admin-password', u'--foreman-proxy-puppetssh-sudo',
    u'--foreman-puppetrun', u'--foreman-proxy-dhcp-config',
    u'--foreman-passenger-min-instances', u'--certs-update-all',
    u'--foreman-proxy-logs-listen-on', u'--foreman-passenger-start-timeout',
    u'--capsule-enable-ostree', u'--katello-repo-export-dir', u'--log-level',
    u'--[no-]enable-foreman-plugin-discovery',
    u'--foreman-proxy-foreman-base-url', u'--certs-state',
    u'--foreman-proxy-dns-tsig-principal', u'--foreman-proxy-dhcp-gateway',
    u'--[no-]enable-foreman-proxy-plugin-remote-execution-ssh',
    u'--foreman-proxy-repo', u'--foreman-pam-service',
    u'--foreman-email-smtp-password', u'--foreman-proxy-bind-host',
    u'--certs-server-cert', u'--foreman-proxy-puppet-use-cache',
    u'--foreman-server-ssl-chain', u'--foreman-proxy-ssl-ca',
    u'--foreman-proxy-realm', u'--clear-pulp-content',
    u'--foreman-proxy-plugin-remote-execution-ssh-generate-keys',
    u'--foreman-proxy-ssl-disabled-ciphers', u'--foreman-proxy-log-level',
    u'--migrations-only', u'--clear-puppet-environments',
    u'--color-of-background', u'--katello-user', u'--foreman-email-conf',
    u'--verbose', u'--foreman-proxy-dhcp-split-config-files',
    u'--foreman-use-vhost', u'--foreman-proxy-plugin-version',
    u'--foreman-proxy-tftp-root', u'--foreman-proxy-puppetrun-cmd',
    u'--profile', u'--certs-country',
    u'--foreman-proxy-puppet-use-environment-api',
    u'--foreman-proxy-dns-forwarders', u'--foreman-email-delivery-method',
    u'--capsule-qpid-router-broker-port',
    u'--foreman-proxy-plugin-openscap-spooldir', u'--katello-post-sync-token',
    u'--certs-server-key', u'--foreman-proxy-dns-server',
    u'--foreman-plugin-prefix', u'--foreman-proxy-plugin-discovery-source-url',
    u'--foreman-proxy-use-sudoersd', u'--foreman-proxy-register-in-foreman',
    u'--dont-save-answers', u'--foreman-proxy-registered-name',
    u'--capsule-pulp-oauth-effective-user', u'--capsule-reverse-proxy-port',
    u'--[no-]enable-capsule', u'--foreman-proxy-realm-provider',
    u'--foreman-server-ssl-cert', u'--enable-scenario',
    u'--foreman-proxy-registered-proxy-url',
    u'--foreman-proxy-oauth-effective-user', u'--foreman-proxy-dhcp-managed',
    u'--katello-use-passenger', u'--foreman-db-password',
    u'--certs-expiration', u'--foreman-proxy-puppetca-cmd',
    u'--katello-enable-ostree', u'--reset', u'--certs-ssl-build-dir',
    u'--foreman-oauth-consumer-secret', u'--foreman-proxy-manage-sudoersd',
    u'--certs-update-server', u'--foreman-websockets-ssl-key',
    u'--foreman-unattended', u'--foreman-proxy-dhcp-range',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-keygen',
    u'--foreman-proxy-puppetdir', u'--capsule-rhsm-url',
    u'--capsule-qpid-router-agent-addr', u'--foreman-proxy-gpgcheck',
    u'--foreman-proxy-dhcp-omapi-port', u'--foreman-proxy-tftp-manage-wget',
    u'--foreman-websockets-ssl-cert', u'--capsule-qpid-router',
    u'--foreman-proxy-puppetca-listen-on', u'--foreman-proxy-ssl-cert',
    u'--foreman-server-ssl-key', u'--foreman-email-smtp-domain',
    u'--[no-]enable-foreman-proxy-plugin-pulp', u'--katello-log-dir',
    u'--foreman-proxy-puppet-ssl-cert', u'--certs-city',
    u'--foreman-proxy-dhcp-provider', u'--katello-package-names',
    u'--foreman-admin-last-name', u'--foreman-db-database',
    u'--foreman-proxy-puppetssh-command', u'--foreman-server-ssl-certs-dir',
    u'--foreman-serveraliases', u'--foreman-proxy-dns-interface',
    u'--foreman-proxy-plugin-openscap-listen-on',
    u'--foreman-admin-first-name', u'--foreman-proxy-dhcp-interface',
    u'--foreman-db-manage', u'--katello-group', u'--foreman-ssl',
    u'--foreman-configure-scl-repo', u'--compare-scenarios',
    u'--foreman-proxy-dns-zone', u'--foreman-proxy-salt-puppetrun-cmd',
    u'--foreman-logging-level', u'--foreman-proxy-http',
    u'--foreman-proxy-dhcp-leases', u'--foreman-proxy-puppet-url',
    u'--foreman-custom-repo', u'--foreman-proxy-tftp-dirs',
    u'--foreman-proxy-plugin-pulp-pulp-content-dir', u'--noop',
    u'--foreman-proxy-dns-managed', u'--katello-max-tasks-per-pulp-worker',
    u'--foreman-group', u'--foreman-proxy-ssldir', u'--upgrade',
    u'--certs-regenerate', u'--capsule-puppet',
    u'--foreman-plugin-discovery-install-images',
    u'--disable-resolve-mismatches'
])


class SELinuxTestCase(TestCase):
    """Checks SELinux installation status"""

    version_regex = re.compile(r'((\d\.?)+[-.]\d)')

    @tier1
    def test_positive_foreman_module(self):
        """Check if SELinux foreman module has the right version

        :id: a0736b3a-3d42-4a09-a11a-28c1d58214a5

        @expectedresults: Foreman RPM and SELinux module versions match

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

        @id: 85fd4388-6d94-42f5-bed2-24be38e9f104

        @expectedresults: All services {'elasticsearch', 'foreman-proxy',
        'foreman-tasks', 'httpd', 'mongod', 'postgresql', 'pulp_celerybeat',
        'pulp_resource_manager', 'pulp_workers', 'qdrouterd', 'qpidd',
        'tomcat'} are started

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

        @id: 80537809-8be4-42db-9cc8-5155378ee4d4

        @Steps:

        1. search all relevant logfiles for ERROR/FATAL

        @expectedresults: No ERROR/FATAL notifcations occur in {katello-jobs,
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
    """Generator function to extract satellite installer params from lst.
    In general lst is cmd.stdout, e.g., a list of strings representing host
    stdout

    :param lst: list  of strings
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

        @id: a51d3b9f-f347-4a96-a31a-770349db08c7

        @Steps:
            1. parse installer options and flags
            2. compare with last options

        @expectedresults: Ideally options should not change on zstreams.
            Documentation must be updated accordingly when such changes occur.
            So when this test fail we QE can act on it, asking dev if
            changes occurs on zstream and checking docs are up to date.
        """
        stdout = ssh.command('satellite-installer --help').stdout

        self.assertEqual(
            INSTALLER_OPTIONS,
            set(extract_params(stdout or []))
        )
