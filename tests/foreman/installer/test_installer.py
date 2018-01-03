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
    "--reset",  "--clear-pulp-content", "--clear-puppet-environments",
    "--disable-system-checks", "--force-upgrade-steps",
    "--certs-update-server", "--certs-update-server-ca", "--certs-update-all",
    "--certs-reset", "--certs-skip-check", "--upgrade",
    "--disable-resolve-mismatches", "--upgrade-puppet", "--[no-]colors",
    "--color-of-background", "--dont-save-answers", "--ignore-undocumented",
    "-i", "--interactive", "--log-level", "-n", "--noop", "-p", "--profile",
    "-s", "--skip-checks-i-know-better", "-v", "--verbose", "-l",
    "--verbose-log-level", "-S", "--scenario", "--disable-scenario",
    "--enable-scenario", "--list-scenarios", "--force", "--compare-scenarios",
    "--migrations-only", "--[no-]parser-cache", "-h", "--help", "--full-help",
    "--[no-]enable-certs", "--[no-]enable-foreman",
    "--[no-]enable-foreman-cli", "--[no-]enable-foreman-compute-ec2",
    "--[no-]enable-foreman-compute-gce",
    "--[no-]enable-foreman-compute-libvirt",
    "--[no-]enable-foreman-compute-openstack",
    "--[no-]enable-foreman-compute-ovirt",
    "--[no-]enable-foreman-compute-rackspace",
    "--[no-]enable-foreman-compute-vmware",
    "--[no-]enable-foreman-plugin-bootdisk",
    "--[no-]enable-foreman-plugin-discovery",
    "--[no-]enable-foreman-plugin-docker",
    "--[no-]enable-foreman-plugin-hooks",
    "--[no-]enable-foreman-plugin-openscap",
    "--[no-]enable-foreman-plugin-remote-execution",
    "--[no-]enable-foreman-plugin-tasks",
    "--[no-]enable-foreman-plugin-templates",
    "--[no-]enable-foreman-proxy", "--[no-]enable-foreman-proxy-content",
    "--[no-]enable-foreman-proxy-plugin-discovery",
    "--[no-]enable-foreman-proxy-plugin-openscap",
    "--[no-]enable-foreman-proxy-plugin-pulp",
    "--[no-]enable-foreman-proxy-plugin-remote-execution-ssh",
    "--[no-]enable-katello", "--[no-]enable-puppet", "--certs-cname",
    "--certs-node-fqdn", "--certs-server-ca-cert", "--certs-server-cert",
    "--certs-server-cert-req", "--certs-server-key",  "--foreman-admin-email",
    "--foreman-admin-first-name", "--foreman-admin-last-name",
    "--foreman-admin-password", "--foreman-admin-username",
    "--foreman-db-manage", "--foreman-db-type",
    "--foreman-email-delivery-method", "--foreman-email-smtp-address",
    "--foreman-email-smtp-authentication", "--foreman-email-smtp-domain",
    "--foreman-email-smtp-password", "--foreman-email-smtp-port",
    "--foreman-email-smtp-user-name", "--foreman-initial-location",
    "--foreman-initial-organization", "--foreman-ipa-authentication",
    "--foreman-locations-enabled", "--foreman-organizations-enabled",
    "--foreman-puppetrun", "--foreman-cli-foreman-url",
    "--foreman-cli-password", "--foreman-cli-username",
    "--foreman-compute-ec2-version", "--foreman-compute-gce-version",
    "--foreman-compute-libvirt-version", "--foreman-compute-openstack-version",
    "--foreman-compute-ovirt-version", "--foreman-compute-rackspace-version",
    "--foreman-compute-vmware-version",
    "--foreman-plugin-discovery-image-name",
    "--foreman-plugin-discovery-install-images",
    "--foreman-plugin-discovery-source-url",
    "--foreman-plugin-discovery-tftp-root", "--foreman-plugin-tasks-package",
    "--foreman-plugin-tasks-service", "--foreman-proxy-bind-host",
    "--foreman-proxy-bmc", "--foreman-proxy-bmc-default-provider",
    "--foreman-proxy-bmc-listen-on", "--foreman-proxy-custom-repo",
    "--foreman-proxy-customrun-args", "--foreman-proxy-customrun-cmd",
    "--foreman-proxy-dhcp", "--foreman-proxy-dhcp-config",
    "--foreman-proxy-dhcp-gateway", "--foreman-proxy-dhcp-interface",
    "--foreman-proxy-dhcp-key-name", "--foreman-proxy-dhcp-key-secret",
    "--foreman-proxy-dhcp-leases", "--foreman-proxy-dhcp-listen-on",
    "--foreman-proxy-dhcp-managed", "--foreman-proxy-dhcp-nameservers",
    "--foreman-proxy-dhcp-omapi-port", "--foreman-proxy-dhcp-option-domain",
    "--foreman-proxy-dhcp-provider", "--foreman-proxy-dhcp-pxeserver",
    "--foreman-proxy-dhcp-range", "--foreman-proxy-dhcp-search-domains",
    "--foreman-proxy-dhcp-server", "--foreman-proxy-dhcp-subnets",
    "--foreman-proxy-dir", "--foreman-proxy-dns",
    "--foreman-proxy-dns-forwarders", "--foreman-proxy-dns-interface",
    "--foreman-proxy-dns-listen-on", "--foreman-proxy-dns-managed",
    "--foreman-proxy-dns-provider", "--foreman-proxy-dns-reverse",
    "--foreman-proxy-dns-server", "--foreman-proxy-dns-tsig-keytab",
    "--foreman-proxy-dns-tsig-principal", "--foreman-proxy-dns-ttl",
    "--foreman-proxy-dns-zone", "--foreman-proxy-ensure-packages-version",
    "--foreman-proxy-foreman-base-url", "--foreman-proxy-foreman-ssl-ca",
    "--foreman-proxy-foreman-ssl-cert", "--foreman-proxy-foreman-ssl-key",
    "--foreman-proxy-freeipa-config", "--foreman-proxy-freeipa-remove-dns",
    "--foreman-proxy-gpgcheck", "--foreman-proxy-groups",
    "--foreman-proxy-http", "--foreman-proxy-http-port",
    "--foreman-proxy-keyfile", "--foreman-proxy-libvirt-connection",
    "--foreman-proxy-libvirt-network", "--foreman-proxy-log",
    "--foreman-proxy-log-buffer", "--foreman-proxy-log-buffer-errors",
    "--foreman-proxy-log-level", "--foreman-proxy-logs",
    "--foreman-proxy-logs-listen-on", "--foreman-proxy-manage-puppet-group",
    "--foreman-proxy-manage-sudoersd", "--foreman-proxy-mcollective-user",
    "--foreman-proxy-oauth-consumer-key",
    "--foreman-proxy-oauth-consumer-secret",
    "--foreman-proxy-oauth-effective-user", "--foreman-proxy-plugin-version",
    "--foreman-proxy-puppet", "--foreman-proxy-puppet-api-timeout",
    "--foreman-proxy-puppet-group", "--foreman-proxy-puppet-listen-on",
    "--foreman-proxy-puppet-ssl-ca", "--foreman-proxy-puppet-ssl-cert",
    "--foreman-proxy-puppet-ssl-key", "--foreman-proxy-puppet-url",
    "--foreman-proxy-puppet-use-cache",
    "--foreman-proxy-puppet-use-environment-api",
    "--foreman-proxy-puppet-user", "--foreman-proxy-puppetca",
    "--foreman-proxy-puppetca-cmd", "--foreman-proxy-puppetca-listen-on",
    "--foreman-proxy-puppetdir", "--foreman-proxy-puppetrun-cmd",
    "--foreman-proxy-puppetrun-provider", "--foreman-proxy-puppetssh-command",
    "--foreman-proxy-puppetssh-keyfile", "--foreman-proxy-puppetssh-sudo",
    "--foreman-proxy-puppetssh-user", "--foreman-proxy-puppetssh-wait",
    "--foreman-proxy-realm", "--foreman-proxy-realm-keytab",
    "--foreman-proxy-realm-listen-on", "--foreman-proxy-realm-principal",
    "--foreman-proxy-realm-provider",
    "--foreman-proxy-realm-split-config-files",
    "--foreman-proxy-register-in-foreman", "--foreman-proxy-registered-name",
    "--foreman-proxy-registered-proxy-url", "--foreman-proxy-repo",
    "--foreman-proxy-salt-puppetrun-cmd", "--foreman-proxy-ssl",
    "--foreman-proxy-ssl-ca", "--foreman-proxy-ssl-cert",
    "--foreman-proxy-ssl-disabled-ciphers", "--foreman-proxy-ssl-key",
    "--foreman-proxy-ssl-port", "--foreman-proxy-ssldir",
    "--foreman-proxy-template-url", "--foreman-proxy-templates",
    "--foreman-proxy-templates-listen-on", "--foreman-proxy-tftp",
    "--foreman-proxy-tftp-dirs", "--foreman-proxy-tftp-listen-on",
    "--foreman-proxy-tftp-manage-wget", "--foreman-proxy-tftp-managed",
    "--foreman-proxy-tftp-root", "--foreman-proxy-tftp-servername",
    "--foreman-proxy-tftp-syslinux-filenames", "--foreman-proxy-trusted-hosts",
    "--foreman-proxy-use-sudoers", "--foreman-proxy-use-sudoersd",
    "--foreman-proxy-user", "--foreman-proxy-version",
    "--foreman-proxy-content-certs-tar",
    "--foreman-proxy-content-enable-ostree",
    "--foreman-proxy-content-parent-fqdn",
    "--foreman-proxy-plugin-discovery-image-name",
    "--foreman-proxy-plugin-discovery-install-images",
    "--foreman-proxy-plugin-discovery-source-url",
    "--foreman-proxy-plugin-discovery-tftp-root",
    "--foreman-proxy-plugin-openscap-configure-openscap-repo",
    "--foreman-proxy-plugin-openscap-contentdir",
    "--foreman-proxy-plugin-openscap-failed-dir",
    "--foreman-proxy-plugin-openscap-openscap-send-log-file",
    "--foreman-proxy-plugin-openscap-reportsdir",
    "--foreman-proxy-plugin-openscap-spooldir",
    "--foreman-proxy-plugin-remote-execution-ssh-generate-keys",
    "--foreman-proxy-plugin-remote-execution-ssh-install-key",
    "--foreman-proxy-plugin-remote-execution-ssh-local-working-dir",
    "--foreman-proxy-plugin-remote-execution-ssh-remote-working-dir",
    "--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-dir",
    "--foreman-proxy-plugin-remote-execution-ssh-ssh-identity-file",
    "--foreman-proxy-plugin-remote-execution-ssh-ssh-keygen",
    "--katello-enable-ostree", "--katello-proxy-password",
    "--katello-proxy-port", "--katello-proxy-url", "--katello-proxy-username",
    "--katello-pulp-max-speed", "--katello-repo-export-dir",
    "--puppet-additional-settings", "--puppet-auth-template",
    "--puppet-autosign", "--puppet-autosign-content",
    "--puppet-autosign-entries", "--puppet-autosign-mode",
    "--puppet-ca-crl-filepath", "--puppet-ca-port", "--puppet-ca-server",
    "--puppet-classfile", "--puppet-codedir",
    "--puppet-configtimeout", "--puppet-cron-cmd", "--puppet-dir",
    "--puppet-dns-alt-names", "--puppet-group", "--puppet-hiera-config",
    "--puppet-listen", "--puppet-listen-to", "--puppet-logdir",
    "--puppet-main-template", "--puppet-manage-packages",
    "--puppet-module-repository", "--puppet-package-provider",
    "--puppet-package-source", "--puppet-pluginfactsource",
    "--puppet-pluginsource", "--puppet-pluginsync", "--puppet-port",
    "--puppet-rundir", "--puppet-runinterval", "--puppet-runmode",
    "--puppet-sharedir", "--puppet-show-diff", "--puppet-splay",
    "--puppet-splaylimit", "--puppet-srv-domain", "--puppet-ssldir",
    "--puppet-syslogfacility", "--puppet-systemd-cmd",
    "--puppet-unavailable-runmodes", "--puppet-use-srv-records",
    "--puppet-usecacheonfailure", "--puppet-user", "--puppet-vardir",
    "--puppet-version", "--full-help"
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
