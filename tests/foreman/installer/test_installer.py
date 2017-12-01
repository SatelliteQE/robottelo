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
from robottelo.decorators import tier1, upgrade
from robottelo.helpers import get_host_info
from robottelo.log import LogFile
from robottelo.test import TestCase

INSTALLER_OPTIONS = set([
    u'--foreman-proxy-http-port', u'--puppet-ca-server',
    u'--foreman-proxy-dns-provider', u'--puppet-dns-alt-names',
    u'--foreman-admin-password', u'--puppet-syslogfacility',
    u'--foreman-proxy-register-in-foreman', u'--foreman-proxy-log',
    u'--dont-save-answers', u'--interactive',
    u'--foreman-proxy-dhcp-option-domain', u'--puppet-hiera-config',
    u'--puppet-autosign', u'--foreman-proxy-dns-ttl', u'-S',
    u'--foreman-proxy-puppet-ssl-ca', u'--foreman-proxy-dns-reverse',
    u'--puppet-module-repository', u'--puppet-package-source',
    u'--foreman-proxy-use-sudoersd', u'--foreman-proxy-dhcp-nameservers',
    u'--foreman-proxy-content-certs-tar', u'--disable-scenario',
    u'--foreman-proxy-use-sudoers', u'--puppet-ssldir',
    u'--katello-proxy-username', u'--[no-]enable-foreman',
    u'-l', u'--foreman-email-smtp-user-name', u'-n', u'-i', u'-h',
    u'--puppet-ca-crl-filepath', u'--foreman-compute-libvirt-version',
    u'-v', u'-p', u'-s', u'--foreman-db-type', u'--foreman-proxy-gpgcheck',
    u'--disable-system-checks', u'--foreman-compute-gce-version',
    u'--certs-server-ca-cert', u'--full-help', u'--foreman-proxy-log-buffer',
    u'--[no-]enable-foreman-plugin-bootdisk',
    u'--foreman-proxy-oauth-effective-user', u'--foreman-proxy-dhcp-provider',
    u'--puppet-port', u'--foreman-proxy-bmc-listen-on',
    u'--[no-]enable-foreman-proxy-plugin-discovery',
    u'--foreman-proxy-plugin-remote-execution-ssh-local-working-dir',
    u'--puppet-splaylimit', u'--foreman-compute-vmware-version',
    u'--foreman-plugin-discovery-source-url', u'--[no-]enable-katello',
    u'--scenario', u'--foreman-proxy-libvirt-connection',
    u'--[no-]enable-foreman-plugin-docker', u'--foreman-plugin-tasks-service',
    u'--foreman-proxy-puppetca-cmd', u'--katello-enable-ostree',
    u'--foreman-proxy-realm-provider', u'--[no-]enable-foreman-plugin-tasks',
    u'--foreman-proxy-manage-puppet-group', u'--foreman-proxy-tftp-managed',
    u'--foreman-proxy-dhcp-subnets',
    u'--foreman-proxy-plugin-discovery-source-url',
    u'--foreman-proxy-puppetrun-provider', u'--reset',
    u'--foreman-proxy-dhcp-search-domains', u'--katello-proxy-password',
    u'--puppet-splay', u'--foreman-proxy-manage-sudoersd',
    u'--certs-skip-check', u'--foreman-email-smtp-port',
    u'--foreman-proxy-version', u'--skip-checks-i-know-better',
    u'--foreman-proxy-plugin-openscap-reportsdir',
    u'--puppet-unavailable-runmodes', u'--katello-pulp-max-speed',
    u'--[no-]enable-foreman-compute-vmware',
    u'--[no-]enable-foreman-proxy', u'--foreman-proxy-ssl-key',
    u'--foreman-proxy-realm-listen-on',
    u'--[no-]enable-foreman-compute-openstack', u'--foreman-proxy-dhcp-range',
    u'--foreman-proxy-puppet-group',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-keygen',
    u'--foreman-db-manage', u'--foreman-proxy-user',
    u'--foreman-proxy-puppetssh-wait', u'--puppet-listen-to',
    u'--foreman-proxy-mcollective-user', u'--foreman-proxy-foreman-ssl-ca',
    u'--foreman-proxy-templates', u'--foreman-proxy-puppet-ssl-key',
    u'--foreman-ipa-authentication', u'--foreman-proxy-puppetdir',
    u'--noop', u'--foreman-proxy-plugin-remote-execution-ssh-generate-keys',
    u'--[no-]enable-foreman-plugin-templates',
    u'--foreman-proxy-registered-name', u'--foreman-cli-foreman-url',
    u'--puppet-rundir', u'--foreman-proxy-dhcp-omapi-port',
    u'--foreman-proxy-tftp-manage-wget', u'--puppet-ca-port',
    u'--ignore-undocumented', u'--foreman-proxy-puppetssh-sudo',
    u'--foreman-proxy-freeipa-remove-dns', u'--foreman-puppetrun',
    u'--certs-update-server', u'--puppet-runmode',
    u'--[no-]enable-foreman-compute-libvirt', u'--puppet-configtimeout',
    u'--foreman-proxy-dhcp-config',
    u'--foreman-proxy-plugin-openscap-configure-openscap-repo',
    u'--[no-]parser-cache', u'--puppet-use-srv-records', u'--[no-]colors',
    u'--puppet-manage-packages', u'--foreman-proxy-puppetca-listen-on',
    u'--puppet-systemd-cmd', u'--foreman-proxy-dhcp-listen-on',
    u'--foreman-proxy-registered-proxy-url', u'--foreman-initial-location',
    u'--puppet-logdir', u'--puppet-dir', u'--foreman-proxy-dhcp-pxeserver',
    u'--foreman-proxy-puppetca', u'--foreman-proxy-puppet-listen-on',
    u'--puppet-cron-cmd', u'--foreman-proxy-ssl-cert',
    u'--puppet-additional-settings', u'--puppet-autosign-content',
    u'--foreman-proxy-plugin-remote-execution-ssh-install-key',
    u'--foreman-email-smtp-domain', u'--certs-server-cert-req',
    u'--foreman-proxy-puppet-api-timeout', u'--disable-resolve-mismatches',
    u'--puppet-classfile', u'--puppet-runinterval',
    u'--foreman-proxy-content-parent-fqdn',
    u'--[no-]enable-foreman-proxy-plugin-pulp', u'--certs-update-all',
    u'--foreman-proxy-dns-tsig-principal', u'--foreman-proxy-dhcp-managed',
    u'--foreman-cli-username', u'--foreman-proxy-custom-repo',
    u'--foreman-proxy-realm-split-config-files',
    u'--foreman-proxy-content-enable-ostree', u'--katello-proxy-url',
    u'--certs-reset', u'--list-scenarios', u'--foreman-compute-ovirt-version',
    u'--puppet-show-diff', u'--puppet-srv-domain', u'--log-level',
    u'--foreman-proxy-logs-listen-on', u'--foreman-admin-last-name',
    u'--[no-]enable-foreman-plugin-discovery',
    u'--foreman-proxy-foreman-base-url', u'--foreman-proxy-bmc',
    u'--foreman-proxy-plugin-openscap-contentdir',
    u'--foreman-proxy-freeipa-config', u'--[no-]enable-foreman-compute-ec2',
    u'--foreman-email-smtp-address', u'--foreman-proxy-bmc-default-provider',
    u'--certs-update-server-ca', u'--foreman-proxy-keyfile',
    u'--katello-repo-export-dir',
    u'--[no-]enable-foreman-proxy-plugin-openscap', u'--verbose-log-level',
    u'--katello-proxy-port', u'--puppet-sharedir',
    u'--foreman-proxy-puppetssh-command', u'--foreman-proxy-dhcp-gateway',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-dir',
    u'--foreman-proxy-log-buffer-errors', u'--foreman-proxy-ssl',
    u'--foreman-proxy-repo', u'--foreman-proxy-puppet-user',
    u'--foreman-proxy-dns-interface', u'--foreman-proxy-dhcp-key-name',
    u'--foreman-proxy-libvirt-network',
    u'--foreman-proxy-plugin-openscap-openscap-send-log-file',
    u'--foreman-admin-first-name',
    u'--foreman-proxy-plugin-discovery-image-name',
    u'--foreman-email-smtp-password', u'--foreman-proxy-tftp-root',
    u'--foreman-proxy-bind-host', u'--foreman-proxy-foreman-ssl-key',
    u'--certs-server-cert', u'--puppet-user', u'--puppet-pluginfactsource',
    u'--foreman-proxy-dhcp-interface', u'--foreman-plugin-tasks-package',
    u'--foreman-proxy-dns', u'--foreman-proxy-tftp-servername',
    u'--[no-]enable-foreman-compute-gce',
    u'--[no-]enable-foreman-compute-ovirt',
    u'--foreman-proxy-puppet-use-cache', u'--foreman-proxy-trusted-hosts',
    u'--foreman-plugin-discovery-image-name', u'--foreman-proxy-dhcp',
    u'--foreman-proxy-puppet-ssl-cert',
    u'--foreman-proxy-plugin-remote-execution-ssh-remote-working-dir',
    u'--foreman-proxy-ssl-ca', u'--foreman-proxy-ssl-disabled-ciphers',
    u'--foreman-proxy-dhcp-key-secret', u'--foreman-proxy-realm',
    u'--foreman-proxy-tftp', u'--clear-pulp-content',
    u'--foreman-proxy-dhcp-server',
    u'--[no-]enable-foreman-plugin-remote-execution', u'--compare-scenarios',
    u'--puppet-autosign-mode', u'--foreman-proxy-customrun-args',
    u'--foreman-proxy-log-level', u'--foreman-initial-organization',
    u'--foreman-proxy-dns-zone', u'--migrations-only', u'--puppet-vardir',
    u'--enable-scenario', u'--clear-puppet-environments', u'--help',
    u'--[no-]enable-foreman-cli', u'--color-of-background',
    u'--foreman-proxy-plugin-discovery-install-images',
    u'--foreman-compute-ec2-version',
    u'--[no-]enable-foreman-proxy-plugin-remote-execution-ssh',
    u'--puppet-pluginsource', u'--foreman-proxy-plugin-openscap-failed-dir',
    u'--foreman-proxy-http', u'--verbose', u'--foreman-proxy-puppetssh-user',
    u'--foreman-proxy-tftp-syslinux-filenames',
    u'--foreman-proxy-realm-principal', u'--foreman-organizations-enabled',
    u'--foreman-proxy-template-url', u'--foreman-proxy-oauth-consumer-secret',
    u'--upgrade-puppet', u'--[no-]enable-foreman-compute-rackspace',
    u'--foreman-proxy-dhcp-leases', u'--puppet-version',
    u'--foreman-plugin-discovery-tftp-root', u'--foreman-admin-username',
    u'--foreman-proxy-plugin-version', u'--puppet-main-template',
    u'--foreman-admin-email', u'--foreman-proxy-ssl-port',
    u'--[no-]enable-foreman-plugin-openscap', u'--foreman-proxy-puppet',
    u'--puppet-pluginsync', u'--puppet-listen', u'--[no-]enable-puppet',
    u'--foreman-proxy-tftp-listen-on',
    u'--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-file',
    u'--foreman-email-smtp-authentication', u'--foreman-proxy-puppetrun-cmd',
    u'--profile', u'--certs-node-fqdn', u'--foreman-proxy-logs',
    u'--foreman-proxy-groups', u'--force', u'--foreman-locations-enabled',
    u'--foreman-compute-openstack-version',
    u'--foreman-proxy-puppet-use-environment-api',
    u'--[no-]enable-foreman-proxy-content',
    u'--[no-]enable-foreman-plugin-hooks',
    u'--foreman-proxy-templates-listen-on', u'--puppet-group',
    u'--puppet-codedir', u'--foreman-proxy-dns-forwarders',
    u'--foreman-cli-password', u'--puppet-auth-template',
    u'--foreman-proxy-dns-managed', u'--foreman-compute-rackspace-version',
    u'--foreman-proxy-dir', u'--foreman-proxy-tftp-dirs',
    u'--foreman-email-delivery-method', u'--foreman-proxy-dns-tsig-keytab',
    u'--foreman-proxy-foreman-ssl-cert',
    u'--foreman-proxy-plugin-openscap-spooldir',
    u'--foreman-proxy-puppetssh-keyfile', u'--foreman-proxy-ssldir',
    u'--upgrade', u'--certs-server-key', u'--[no-]enable-certs',
    u'--foreman-proxy-dns-server', u'--foreman-proxy-oauth-consumer-key',
    u'--foreman-proxy-realm-keytab', u'--foreman-proxy-puppet-url',
    u'--foreman-proxy-plugin-discovery-tftp-root', u'--certs-cname',
    u'--foreman-proxy-salt-puppetrun-cmd', u'--puppet-package-provider',
    u'--puppet-usecacheonfailure', u'--foreman-proxy-customrun-cmd',
    u'--foreman-proxy-ensure-packages-version', u'--puppet-autosign-entries',
    u'--foreman-proxy-dns-listen-on',
    u'--foreman-plugin-discovery-install-images', u'--force-upgrade-steps'
])


class SELinuxTestCase(TestCase):
    """Checks SELinux installation status"""

    version_regex = re.compile(r'((\d\.?)+[-.]\d)')

    @upgrade
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

    @upgrade
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
            remote_file = logfile['path']
            try:
                log = LogFile(remote_file, logfile['pattern'])
            except IOError:
                self.fail(
                    'Could not find {0} file on server'.format(remote_file)
                )
            else:
                errors = log.filter()
                self.assertEqual(
                    len(errors), 0,
                    msg='Errors found in {}: {}'.format(remote_file, errors))


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

    @upgrade
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
