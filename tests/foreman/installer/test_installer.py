"""Smoke tests to check installation health

:Requirement: Installer

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Installer

:Team: Platform

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest

from robottelo import ssh
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.hosts import setup_capsule


PREVIOUS_INSTALLER_OPTIONS = {
    '-',
    '--[no-]colors',
    '--[no-]enable-certs',
    '--[no-]enable-foreman',
    '--[no-]enable-foreman-cli',
    '--[no-]enable-foreman-cli-ansible',
    '--[no-]enable-foreman-cli-azure',
    '--[no-]enable-foreman-cli-google',
    '--[no-]enable-foreman-cli-katello',
    '--[no-]enable-foreman-cli-kubevirt',
    '--[no-]enable-foreman-cli-puppet',
    '--[no-]enable-foreman-cli-remote-execution',
    '--[no-]enable-foreman-cli-virt-who-configure',
    '--[no-]enable-foreman-cli-webhooks',
    '--[no-]enable-foreman-compute-ec2',
    '--[no-]enable-foreman-compute-libvirt',
    '--[no-]enable-foreman-compute-openstack',
    '--[no-]enable-foreman-compute-ovirt',
    '--[no-]enable-foreman-compute-vmware',
    '--[no-]enable-foreman-plugin-ansible',
    '--[no-]enable-foreman-plugin-azure',
    '--[no-]enable-foreman-plugin-bootdisk',
    '--[no-]enable-foreman-plugin-discovery',
    '--[no-]enable-foreman-plugin-google',
    '--[no-]enable-foreman-plugin-kubevirt',
    '--[no-]enable-foreman-plugin-leapp',
    '--[no-]enable-foreman-plugin-openscap',
    '--[no-]enable-foreman-plugin-puppet',
    '--[no-]enable-foreman-plugin-remote-execution',
    '--[no-]enable-foreman-plugin-remote-execution-cockpit',
    '--[no-]enable-foreman-plugin-rh-cloud',
    '--[no-]enable-foreman-plugin-tasks',
    '--[no-]enable-foreman-plugin-templates',
    '--[no-]enable-foreman-plugin-virt-who-configure',
    '--[no-]enable-foreman-plugin-webhooks',
    '--[no-]enable-foreman-proxy',
    '--[no-]enable-foreman-proxy-content',
    '--[no-]enable-foreman-proxy-plugin-ansible',
    '--[no-]enable-foreman-proxy-plugin-dhcp-infoblox',
    '--[no-]enable-foreman-proxy-plugin-dhcp-remote-isc',
    '--[no-]enable-foreman-proxy-plugin-discovery',
    '--[no-]enable-foreman-proxy-plugin-dns-infoblox',
    '--[no-]enable-foreman-proxy-plugin-openscap',
    '--[no-]enable-foreman-proxy-plugin-remote-execution-script',
    '--[no-]enable-foreman-proxy-plugin-shellhooks',
    '--[no-]enable-katello',
    '--[no-]enable-puppet',
    '--[no-]lock-package-versions',
    '--[no-]parser-cache',
    '--[no-]verbose',
    '--certs-ca-common-name',
    '--certs-ca-expiration',
    '--certs-city',
    '--certs-cname',
    '--certs-country',
    '--certs-default-ca-name',
    '--certs-deploy',
    '--certs-expiration',
    '--certs-generate',
    '--certs-group',
    '--certs-node-fqdn',
    '--certs-org',
    '--certs-org-unit',
    '--certs-pki-dir',
    '--certs-regenerate',
    '--certs-reset',
    '--certs-server-ca-cert',
    '--certs-server-ca-name',
    '--certs-server-cert',
    '--certs-server-cert-req',
    '--certs-server-key',
    '--certs-skip-check',
    '--certs-ssl-build-dir',
    '--certs-state',
    '--certs-tar-file',
    '--certs-update-all',
    '--certs-update-server',
    '--certs-update-server-ca',
    '--certs-user',
    '--color-of-background',
    '--compare-scenarios',
    '--detailed-exitcodes',
    '--disable-scenario',
    '--dont-save-answers',
    '--enable-scenario',
    '--force',
    '--foreman-apache',
    '--foreman-cli-foreman-url',
    '--foreman-cli-manage-root-config',
    '--foreman-cli-password',
    '--foreman-cli-refresh-cache',
    '--foreman-cli-request-timeout',
    '--foreman-cli-ssl-ca-file',
    '--foreman-cli-use-sessions',
    '--foreman-cli-username',
    '--foreman-cli-version',
    '--foreman-client-ssl-ca',
    '--foreman-client-ssl-cert',
    '--foreman-client-ssl-key',
    '--foreman-compute-ec2-version',
    '--foreman-compute-libvirt-version',
    '--foreman-compute-openstack-version',
    '--foreman-compute-ovirt-version',
    '--foreman-compute-vmware-version',
    '--foreman-cors-domains',
    '--foreman-db-database',
    '--foreman-db-host',
    '--foreman-db-manage',
    '--foreman-db-manage-rake',
    '--foreman-db-password',
    '--foreman-db-pool',
    '--foreman-db-port',
    '--foreman-db-root-cert',
    '--foreman-db-sslmode',
    '--foreman-db-username',
    '--foreman-dynflow-manage-services',
    '--foreman-dynflow-orchestrator-ensure',
    '--foreman-dynflow-redis-url',
    '--foreman-dynflow-worker-concurrency',
    '--foreman-dynflow-worker-instances',
    '--foreman-email-delivery-method',
    '--foreman-email-reply-address',
    '--foreman-email-sendmail-arguments',
    '--foreman-email-sendmail-location',
    '--foreman-email-smtp-address',
    '--foreman-email-smtp-authentication',
    '--foreman-email-smtp-domain',
    '--foreman-email-smtp-password',
    '--foreman-email-smtp-port',
    '--foreman-email-smtp-user-name',
    '--foreman-email-subject-prefix',
    '--foreman-foreman-service-puma-threads-max',
    '--foreman-foreman-service-puma-threads-min',
    '--foreman-foreman-service-puma-workers',
    '--foreman-foreman-url',
    '--foreman-gssapi-local-name',
    '--foreman-hsts-enabled',
    '--foreman-http-keytab',
    '--foreman-initial-admin-email',
    '--foreman-initial-admin-first-name',
    '--foreman-initial-admin-last-name',
    '--foreman-initial-admin-locale',
    '--foreman-initial-admin-password',
    '--foreman-initial-admin-timezone',
    '--foreman-initial-admin-username',
    '--foreman-initial-location',
    '--foreman-initial-organization',
    '--foreman-ipa-authentication',
    '--foreman-ipa-authentication-api',
    '--foreman-ipa-manage-sssd',
    '--foreman-keycloak',
    '--foreman-keycloak-app-name',
    '--foreman-keycloak-realm',
    '--foreman-loggers',
    '--foreman-logging-layout',
    '--foreman-logging-level',
    '--foreman-logging-type',
    '--foreman-oauth-active',
    '--foreman-oauth-consumer-key',
    '--foreman-oauth-consumer-secret',
    '--foreman-oauth-effective-user',
    '--foreman-oauth-map-users',
    '--foreman-pam-service',
    '--foreman-plugin-remote-execution-cockpit-origins',
    '--foreman-plugin-tasks-automatic-cleanup',
    '--foreman-plugin-tasks-backup',
    '--foreman-plugin-tasks-cron-line',
    '--foreman-plugin-version',
    '--foreman-proxy-autosignfile',
    '--foreman-proxy-bind-host',
    '--foreman-proxy-bmc',
    '--foreman-proxy-bmc-default-provider',
    '--foreman-proxy-bmc-listen-on',
    '--foreman-proxy-bmc-redfish-verify-ssl',
    '--foreman-proxy-bmc-ssh-key',
    '--foreman-proxy-bmc-ssh-powercycle',
    '--foreman-proxy-bmc-ssh-poweroff',
    '--foreman-proxy-bmc-ssh-poweron',
    '--foreman-proxy-bmc-ssh-powerstatus',
    '--foreman-proxy-bmc-ssh-user',
    '--foreman-proxy-content-enable-ansible',
    '--foreman-proxy-content-enable-deb',
    '--foreman-proxy-content-enable-docker',
    '--foreman-proxy-content-enable-file',
    '--foreman-proxy-content-enable-katello-agent',
    '--foreman-proxy-content-enable-ostree',
    '--foreman-proxy-content-enable-python',
    '--foreman-proxy-content-enable-yum',
    '--foreman-proxy-content-pulpcore-additional-export-paths',
    '--foreman-proxy-content-pulpcore-additional-import-paths',
    '--foreman-proxy-content-pulpcore-allowed-content-checksums',
    '--foreman-proxy-content-pulpcore-api-service-worker-timeout',
    '--foreman-proxy-content-pulpcore-cache-enabled',
    '--foreman-proxy-content-pulpcore-cache-expires-ttl',
    '--foreman-proxy-content-pulpcore-content-service-worker-timeout',
    '--foreman-proxy-content-pulpcore-django-secret-key',
    '--foreman-proxy-content-pulpcore-manage-postgresql',
    '--foreman-proxy-content-pulpcore-mirror',
    '--foreman-proxy-content-pulpcore-postgresql-db-name',
    '--foreman-proxy-content-pulpcore-postgresql-host',
    '--foreman-proxy-content-pulpcore-postgresql-password',
    '--foreman-proxy-content-pulpcore-postgresql-port',
    '--foreman-proxy-content-pulpcore-postgresql-ssl',
    '--foreman-proxy-content-pulpcore-postgresql-ssl-cert',
    '--foreman-proxy-content-pulpcore-postgresql-ssl-key',
    '--foreman-proxy-content-pulpcore-postgresql-ssl-require',
    '--foreman-proxy-content-pulpcore-postgresql-ssl-root-ca',
    '--foreman-proxy-content-pulpcore-postgresql-user',
    '--foreman-proxy-content-pulpcore-telemetry',
    '--foreman-proxy-content-pulpcore-worker-count',
    '--foreman-proxy-content-puppet',
    '--foreman-proxy-content-qpid-router-agent-addr',
    '--foreman-proxy-content-qpid-router-agent-port',
    '--foreman-proxy-content-qpid-router-broker-addr',
    '--foreman-proxy-content-qpid-router-broker-port',
    '--foreman-proxy-content-qpid-router-hub-addr',
    '--foreman-proxy-content-qpid-router-hub-port',
    '--foreman-proxy-content-qpid-router-logging',
    '--foreman-proxy-content-qpid-router-logging-level',
    '--foreman-proxy-content-qpid-router-logging-path',
    '--foreman-proxy-content-qpid-router-ssl-ciphers',
    '--foreman-proxy-content-qpid-router-ssl-protocols',
    '--foreman-proxy-content-reverse-proxy',
    '--foreman-proxy-content-reverse-proxy-port',
    '--foreman-proxy-dhcp',
    '--foreman-proxy-dhcp-additional-interfaces',
    '--foreman-proxy-dhcp-config',
    '--foreman-proxy-dhcp-failover-address',
    '--foreman-proxy-dhcp-failover-port',
    '--foreman-proxy-dhcp-gateway',
    '--foreman-proxy-dhcp-interface',
    '--foreman-proxy-dhcp-ipxe-bootstrap',
    '--foreman-proxy-dhcp-ipxefilename',
    '--foreman-proxy-dhcp-key-name',
    '--foreman-proxy-dhcp-key-secret',
    '--foreman-proxy-dhcp-leases',
    '--foreman-proxy-dhcp-listen-on',
    '--foreman-proxy-dhcp-load-balance',
    '--foreman-proxy-dhcp-load-split',
    '--foreman-proxy-dhcp-manage-acls',
    '--foreman-proxy-dhcp-managed',
    '--foreman-proxy-dhcp-max-response-delay',
    '--foreman-proxy-dhcp-max-unacked-updates',
    '--foreman-proxy-dhcp-mclt',
    '--foreman-proxy-dhcp-nameservers',
    '--foreman-proxy-dhcp-netmask',
    '--foreman-proxy-dhcp-network',
    '--foreman-proxy-dhcp-node-type',
    '--foreman-proxy-dhcp-omapi-port',
    '--foreman-proxy-dhcp-option-domain',
    '--foreman-proxy-dhcp-peer-address',
    '--foreman-proxy-dhcp-ping-free-ip',
    '--foreman-proxy-dhcp-provider',
    '--foreman-proxy-dhcp-pxefilename',
    '--foreman-proxy-dhcp-pxeserver',
    '--foreman-proxy-dhcp-range',
    '--foreman-proxy-dhcp-search-domains',
    '--foreman-proxy-dhcp-server',
    '--foreman-proxy-dhcp-subnets',
    '--foreman-proxy-dns',
    '--foreman-proxy-dns-forwarders',
    '--foreman-proxy-dns-interface',
    '--foreman-proxy-dns-listen-on',
    '--foreman-proxy-dns-managed',
    '--foreman-proxy-dns-provider',
    '--foreman-proxy-dns-reverse',
    '--foreman-proxy-dns-server',
    '--foreman-proxy-dns-tsig-keytab',
    '--foreman-proxy-dns-tsig-principal',
    '--foreman-proxy-dns-ttl',
    '--foreman-proxy-dns-zone',
    '--foreman-proxy-ensure-packages-version',
    '--foreman-proxy-foreman-base-url',
    '--foreman-proxy-foreman-ssl-ca',
    '--foreman-proxy-foreman-ssl-cert',
    '--foreman-proxy-foreman-ssl-key',
    '--foreman-proxy-freeipa-config',
    '--foreman-proxy-freeipa-remove-dns',
    '--foreman-proxy-groups',
    '--foreman-proxy-http',
    '--foreman-proxy-http-port',
    '--foreman-proxy-httpboot',
    '--foreman-proxy-httpboot-listen-on',
    '--foreman-proxy-keyfile',
    '--foreman-proxy-libvirt-connection',
    '--foreman-proxy-libvirt-network',
    '--foreman-proxy-log',
    '--foreman-proxy-log-buffer',
    '--foreman-proxy-log-buffer-errors',
    '--foreman-proxy-log-level',
    '--foreman-proxy-logs',
    '--foreman-proxy-logs-listen-on',
    '--foreman-proxy-manage-puppet-group',
    '--foreman-proxy-oauth-consumer-key',
    '--foreman-proxy-oauth-consumer-secret',
    '--foreman-proxy-oauth-effective-user',
    '--foreman-proxy-plugin-ansible-ansible-dir',
    '--foreman-proxy-plugin-ansible-callback',
    '--foreman-proxy-plugin-ansible-collections-paths',
    '--foreman-proxy-plugin-ansible-enabled',
    '--foreman-proxy-plugin-ansible-host-key-checking',
    '--foreman-proxy-plugin-ansible-install-runner',
    '--foreman-proxy-plugin-ansible-listen-on',
    '--foreman-proxy-plugin-ansible-roles-path',
    '--foreman-proxy-plugin-ansible-runner-package-name',
    '--foreman-proxy-plugin-ansible-ssh-args',
    '--foreman-proxy-plugin-ansible-working-dir',
    '--foreman-proxy-plugin-dhcp-infoblox-dns-view',
    '--foreman-proxy-plugin-dhcp-infoblox-network-view',
    '--foreman-proxy-plugin-dhcp-infoblox-password',
    '--foreman-proxy-plugin-dhcp-infoblox-record-type',
    '--foreman-proxy-plugin-dhcp-infoblox-used-ips-search-type',
    '--foreman-proxy-plugin-dhcp-infoblox-username',
    '--foreman-proxy-plugin-dhcp-remote-isc-dhcp-config',
    '--foreman-proxy-plugin-dhcp-remote-isc-dhcp-leases',
    '--foreman-proxy-plugin-dhcp-remote-isc-key-name',
    '--foreman-proxy-plugin-dhcp-remote-isc-key-secret',
    '--foreman-proxy-plugin-dhcp-remote-isc-omapi-port',
    '--foreman-proxy-plugin-discovery-enabled',
    '--foreman-proxy-plugin-discovery-image-name',
    '--foreman-proxy-plugin-discovery-install-images',
    '--foreman-proxy-plugin-discovery-listen-on',
    '--foreman-proxy-plugin-discovery-source-url',
    '--foreman-proxy-plugin-discovery-tftp-root',
    '--foreman-proxy-plugin-discovery-version',
    '--foreman-proxy-plugin-dns-infoblox-dns-server',
    '--foreman-proxy-plugin-dns-infoblox-dns-view',
    '--foreman-proxy-plugin-dns-infoblox-password',
    '--foreman-proxy-plugin-dns-infoblox-username',
    '--foreman-proxy-plugin-openscap-contentdir',
    '--foreman-proxy-plugin-openscap-corrupted-dir',
    '--foreman-proxy-plugin-openscap-enabled',
    '--foreman-proxy-plugin-openscap-failed-dir',
    '--foreman-proxy-plugin-openscap-listen-on',
    '--foreman-proxy-plugin-openscap-openscap-send-log-file',
    '--foreman-proxy-plugin-openscap-proxy-name',
    '--foreman-proxy-plugin-openscap-puppet-module',
    '--foreman-proxy-plugin-openscap-puppet-module-ensure',
    '--foreman-proxy-plugin-openscap-reportsdir',
    '--foreman-proxy-plugin-openscap-spooldir',
    '--foreman-proxy-plugin-openscap-timeout',
    '--foreman-proxy-plugin-openscap-version',
    '--foreman-proxy-plugin-remote-execution-script-cockpit-integration',
    '--foreman-proxy-plugin-remote-execution-script-enabled',
    '--foreman-proxy-plugin-remote-execution-script-generate-keys',
    '--foreman-proxy-plugin-remote-execution-script-install-key',
    '--foreman-proxy-plugin-remote-execution-script-listen-on',
    '--foreman-proxy-plugin-remote-execution-script-local-working-dir',
    '--foreman-proxy-plugin-remote-execution-script-mode',
    '--foreman-proxy-plugin-remote-execution-script-mqtt-rate-limit',
    '--foreman-proxy-plugin-remote-execution-script-mqtt-resend-interval',
    '--foreman-proxy-plugin-remote-execution-script-mqtt-ttl',
    '--foreman-proxy-plugin-remote-execution-script-remote-working-dir',
    '--foreman-proxy-plugin-remote-execution-script-ssh-identity-dir',
    '--foreman-proxy-plugin-remote-execution-script-ssh-identity-file',
    '--foreman-proxy-plugin-remote-execution-script-ssh-kerberos-auth',
    '--foreman-proxy-plugin-remote-execution-script-ssh-keygen',
    '--foreman-proxy-plugin-remote-execution-script-ssh-log-level',
    '--foreman-proxy-plugin-shellhooks-directory',
    '--foreman-proxy-plugin-shellhooks-enabled',
    '--foreman-proxy-plugin-shellhooks-listen-on',
    '--foreman-proxy-plugin-shellhooks-version',
    '--foreman-proxy-puppet',
    '--foreman-proxy-puppet-api-timeout',
    '--foreman-proxy-puppet-group',
    '--foreman-proxy-puppet-listen-on',
    '--foreman-proxy-puppet-ssl-ca',
    '--foreman-proxy-puppet-ssl-cert',
    '--foreman-proxy-puppet-ssl-key',
    '--foreman-proxy-puppet-url',
    '--foreman-proxy-puppetca',
    '--foreman-proxy-puppetca-certificate',
    '--foreman-proxy-puppetca-listen-on',
    '--foreman-proxy-puppetca-provider',
    '--foreman-proxy-puppetca-sign-all',
    '--foreman-proxy-puppetca-token-ttl',
    '--foreman-proxy-puppetca-tokens-file',
    '--foreman-proxy-puppetdir',
    '--foreman-proxy-realm',
    '--foreman-proxy-realm-keytab',
    '--foreman-proxy-realm-listen-on',
    '--foreman-proxy-realm-principal',
    '--foreman-proxy-realm-provider',
    '--foreman-proxy-register-in-foreman',
    '--foreman-proxy-registered-name',
    '--foreman-proxy-registered-proxy-url',
    '--foreman-proxy-registration',
    '--foreman-proxy-registration-listen-on',
    '--foreman-proxy-registration-url',
    '--foreman-proxy-ssl',
    '--foreman-proxy-ssl-ca',
    '--foreman-proxy-ssl-cert',
    '--foreman-proxy-ssl-disabled-ciphers',
    '--foreman-proxy-ssl-key',
    '--foreman-proxy-ssl-port',
    '--foreman-proxy-ssldir',
    '--foreman-proxy-template-url',
    '--foreman-proxy-templates',
    '--foreman-proxy-templates-listen-on',
    '--foreman-proxy-tftp',
    '--foreman-proxy-tftp-dirs',
    '--foreman-proxy-tftp-listen-on',
    '--foreman-proxy-tftp-manage-wget',
    '--foreman-proxy-tftp-managed',
    '--foreman-proxy-tftp-replace-grub2-cfg',
    '--foreman-proxy-tftp-root',
    '--foreman-proxy-tftp-servername',
    '--foreman-proxy-tls-disabled-versions',
    '--foreman-proxy-trusted-hosts',
    '--foreman-proxy-version',
    '--foreman-rails-cache-store',
    '--foreman-register-in-foreman',
    '--foreman-server-port',
    '--foreman-server-ssl-ca',
    '--foreman-server-ssl-cert',
    '--foreman-server-ssl-chain',
    '--foreman-server-ssl-crl',
    '--foreman-server-ssl-key',
    '--foreman-server-ssl-port',
    '--foreman-server-ssl-protocol',
    '--foreman-server-ssl-verify-client',
    '--foreman-serveraliases',
    '--foreman-servername',
    '--foreman-ssl',
    '--foreman-telemetry-logger-enabled',
    '--foreman-telemetry-logger-level',
    '--foreman-telemetry-prefix',
    '--foreman-telemetry-prometheus-enabled',
    '--foreman-telemetry-statsd-enabled',
    '--foreman-telemetry-statsd-host',
    '--foreman-telemetry-statsd-protocol',
    '--foreman-trusted-proxies',
    '--foreman-unattended',
    '--foreman-unattended-url',
    '--foreman-version',
    '--foreman-websockets-encrypt',
    '--foreman-websockets-ssl-cert',
    '--foreman-websockets-ssl-key',
    '--full-help',
    '--help',
    '--ignore-undocumented',
    '--interactive',
    '--katello-candlepin-db-host',
    '--katello-candlepin-db-name',
    '--katello-candlepin-db-password',
    '--katello-candlepin-db-port',
    '--katello-candlepin-db-ssl',
    '--katello-candlepin-db-ssl-ca',
    '--katello-candlepin-db-ssl-verify',
    '--katello-candlepin-db-user',
    '--katello-candlepin-manage-db',
    '--katello-candlepin-oauth-key',
    '--katello-candlepin-oauth-secret',
    '--katello-hosts-queue-workers',
    '--katello-qpid-hostname',
    '--katello-qpid-interface',
    '--katello-qpid-wcache-page-size',
    '--katello-rest-client-timeout',
    '--list-scenarios',
    '--log-level',
    '--migrations-only',
    '--noop',
    '--profile',
    '--puppet-additional-settings',
    '--puppet-agent',
    '--puppet-agent-additional-settings',
    '--puppet-agent-default-schedules',
    '--puppet-agent-noop',
    '--puppet-agent-restart-command',
    '--puppet-allow-any-crl-auth',
    '--puppet-auth-allowed',
    '--puppet-auth-template',
    '--puppet-autosign',
    '--puppet-autosign-content',
    '--puppet-autosign-entries',
    '--puppet-autosign-mode',
    '--puppet-autosign-source',
    '--puppet-ca-crl-filepath',
    '--puppet-ca-port',
    '--puppet-ca-server',
    '--puppet-classfile',
    '--puppet-client-certname',
    '--puppet-client-package',
    '--puppet-codedir',
    '--puppet-cron-cmd',
    '--puppet-dir',
    '--puppet-dir-group',
    '--puppet-dir-owner',
    '--puppet-dns-alt-names',
    '--puppet-environment',
    '--puppet-group',
    '--puppet-hiera-config',
    '--puppet-http-connect-timeout',
    '--puppet-http-read-timeout',
    '--puppet-localconfig',
    '--puppet-logdir',
    '--puppet-manage-packages',
    '--puppet-module-repository',
    '--puppet-package-install-options',
    '--puppet-package-provider',
    '--puppet-package-source',
    '--puppet-pluginfactsource',
    '--puppet-pluginsource',
    '--puppet-port',
    '--puppet-postrun-command',
    '--puppet-prerun-command',
    '--puppet-puppetconf-mode',
    '--puppet-puppetmaster',
    '--puppet-report',
    '--puppet-run-hour',
    '--puppet-run-minute',
    '--puppet-rundir',
    '--puppet-runinterval',
    '--puppet-runmode',
    '--puppet-server',
    '--puppet-server-acceptor-threads',
    '--puppet-server-additional-settings',
    '--puppet-server-admin-api-whitelist',
    '--puppet-server-allow-header-cert-info',
    '--puppet-server-ca',
    '--puppet-server-ca-allow-auth-extensions',
    '--puppet-server-ca-allow-sans',
    '--puppet-server-ca-auth-required',
    '--puppet-server-ca-client-self-delete',
    '--puppet-server-ca-client-whitelist',
    '--puppet-server-ca-crl-sync',
    '--puppet-server-ca-enable-infra-crl',
    '--puppet-server-certname',
    '--puppet-server-check-for-updates',
    '--puppet-server-cipher-suites',
    '--puppet-server-common-modules-path',
    '--puppet-server-compile-mode',
    '--puppet-server-connect-timeout',
    '--puppet-server-crl-enable',
    '--puppet-server-custom-trusted-oid-mapping',
    '--puppet-server-default-manifest',
    '--puppet-server-default-manifest-content',
    '--puppet-server-default-manifest-path',
    '--puppet-server-dir',
    '--puppet-server-environment-class-cache-enabled',
    '--puppet-server-environment-timeout',
    '--puppet-server-environment-vars',
    '--puppet-server-environments-group',
    '--puppet-server-environments-mode',
    '--puppet-server-environments-owner',
    '--puppet-server-environments-recurse',
    '--puppet-server-envs-dir',
    '--puppet-server-envs-target',
    '--puppet-server-external-nodes',
    '--puppet-server-foreman',
    '--puppet-server-foreman-facts',
    '--puppet-server-foreman-ssl-ca',
    '--puppet-server-foreman-ssl-cert',
    '--puppet-server-foreman-ssl-key',
    '--puppet-server-foreman-url',
    '--puppet-server-git-branch-map',
    '--puppet-server-git-repo',
    '--puppet-server-git-repo-group',
    '--puppet-server-git-repo-mode',
    '--puppet-server-git-repo-path',
    '--puppet-server-git-repo-user',
    '--puppet-server-group',
    '--puppet-server-http',
    '--puppet-server-http-port',
    '--puppet-server-idle-timeout',
    '--puppet-server-ip',
    '--puppet-server-jolokia-metrics-whitelist',
    '--puppet-server-jruby-gem-home',
    '--puppet-server-jvm-cli-args',
    '--puppet-server-jvm-config',
    '--puppet-server-jvm-extra-args',
    '--puppet-server-jvm-java-bin',
    '--puppet-server-jvm-max-heap-size',
    '--puppet-server-jvm-min-heap-size',
    '--puppet-server-manage-user',
    '--puppet-server-max-active-instances',
    '--puppet-server-max-open-files',
    '--puppet-server-max-queued-requests',
    '--puppet-server-max-requests-per-instance',
    '--puppet-server-max-retry-delay',
    '--puppet-server-max-threads',
    '--puppet-server-metrics-allowed',
    '--puppet-server-metrics-graphite-enable',
    '--puppet-server-metrics-graphite-host',
    '--puppet-server-metrics-graphite-interval',
    '--puppet-server-metrics-graphite-port',
    '--puppet-server-metrics-jmx-enable',
    '--puppet-server-metrics-server-id',
    '--puppet-server-multithreaded',
    '--puppet-server-package',
    '--puppet-server-parser',
    '--puppet-server-port',
    '--puppet-server-post-hook-content',
    '--puppet-server-post-hook-name',
    '--puppet-server-puppet-basedir',
    '--puppet-server-puppetserver-auth-template',
    '--puppet-server-puppetserver-dir',
    '--puppet-server-puppetserver-experimental',
    '--puppet-server-puppetserver-logdir',
    '--puppet-server-puppetserver-metrics',
    '--puppet-server-puppetserver-profiler',
    '--puppet-server-puppetserver-rundir',
    '--puppet-server-puppetserver-telemetry',
    '--puppet-server-puppetserver-trusted-agents',
    '--puppet-server-puppetserver-trusted-certificate-extensions',
    '--puppet-server-puppetserver-vardir',
    '--puppet-server-puppetserver-version',
    '--puppet-server-reports',
    '--puppet-server-request-timeout',
    '--puppet-server-ruby-load-paths',
    '--puppet-server-selector-threads',
    '--puppet-server-ssl-acceptor-threads',
    '--puppet-server-ssl-chain-filepath',
    '--puppet-server-ssl-dir',
    '--puppet-server-ssl-dir-manage',
    '--puppet-server-ssl-key-manage',
    '--puppet-server-ssl-protocols',
    '--puppet-server-ssl-selector-threads',
    '--puppet-server-storeconfigs',
    '--puppet-server-strict-variables',
    '--puppet-server-trusted-external-command',
    '--puppet-server-use-legacy-auth-conf',
    '--puppet-server-user',
    '--puppet-server-version',
    '--puppet-server-versioned-code-content',
    '--puppet-server-versioned-code-id',
    '--puppet-server-web-idle-timeout',
    '--puppet-service-name',
    '--puppet-sharedir',
    '--puppet-show-diff',
    '--puppet-splay',
    '--puppet-splaylimit',
    '--puppet-srv-domain',
    '--puppet-ssldir',
    '--puppet-syslogfacility',
    '--puppet-systemd-cmd',
    '--puppet-systemd-randomizeddelaysec',
    '--puppet-systemd-unit-name',
    '--puppet-unavailable-runmodes',
    '--puppet-use-srv-records',
    '--puppet-usecacheonfailure',
    '--puppet-user',
    '--puppet-vardir',
    '--puppet-version',
    '--register-with-insights',
    '--reset-certs-ca-common-name',
    '--reset-certs-ca-expiration',
    '--reset-certs-city',
    '--reset-certs-cname',
    '--reset-certs-country',
    '--reset-certs-default-ca-name',
    '--reset-certs-deploy',
    '--reset-certs-expiration',
    '--reset-certs-generate',
    '--reset-certs-group',
    '--reset-certs-node-fqdn',
    '--reset-certs-org',
    '--reset-certs-org-unit',
    '--reset-certs-pki-dir',
    '--reset-certs-regenerate',
    '--reset-certs-server-ca-cert',
    '--reset-certs-server-ca-name',
    '--reset-certs-server-cert',
    '--reset-certs-server-cert-req',
    '--reset-certs-server-key',
    '--reset-certs-ssl-build-dir',
    '--reset-certs-state',
    '--reset-certs-tar-file',
    '--reset-certs-user',
    '--reset-data',
    '--reset-foreman-apache',
    '--reset-foreman-cli-foreman-url',
    '--reset-foreman-cli-manage-root-config',
    '--reset-foreman-cli-password',
    '--reset-foreman-cli-refresh-cache',
    '--reset-foreman-cli-request-timeout',
    '--reset-foreman-cli-ssl-ca-file',
    '--reset-foreman-cli-use-sessions',
    '--reset-foreman-cli-username',
    '--reset-foreman-cli-version',
    '--reset-foreman-client-ssl-ca',
    '--reset-foreman-client-ssl-cert',
    '--reset-foreman-client-ssl-key',
    '--reset-foreman-compute-ec2-version',
    '--reset-foreman-compute-libvirt-version',
    '--reset-foreman-compute-openstack-version',
    '--reset-foreman-compute-ovirt-version',
    '--reset-foreman-compute-vmware-version',
    '--reset-foreman-cors-domains',
    '--reset-foreman-db-database',
    '--reset-foreman-db-host',
    '--reset-foreman-db-manage',
    '--reset-foreman-db-manage-rake',
    '--reset-foreman-db-password',
    '--reset-foreman-db-pool',
    '--reset-foreman-db-port',
    '--reset-foreman-db-root-cert',
    '--reset-foreman-db-sslmode',
    '--reset-foreman-db-username',
    '--reset-foreman-dynflow-manage-services',
    '--reset-foreman-dynflow-orchestrator-ensure',
    '--reset-foreman-dynflow-redis-url',
    '--reset-foreman-dynflow-worker-concurrency',
    '--reset-foreman-dynflow-worker-instances',
    '--reset-foreman-email-delivery-method',
    '--reset-foreman-email-reply-address',
    '--reset-foreman-email-sendmail-arguments',
    '--reset-foreman-email-sendmail-location',
    '--reset-foreman-email-smtp-address',
    '--reset-foreman-email-smtp-authentication',
    '--reset-foreman-email-smtp-domain',
    '--reset-foreman-email-smtp-password',
    '--reset-foreman-email-smtp-port',
    '--reset-foreman-email-smtp-user-name',
    '--reset-foreman-email-subject-prefix',
    '--reset-foreman-foreman-service-puma-threads-max',
    '--reset-foreman-foreman-service-puma-threads-min',
    '--reset-foreman-foreman-service-puma-workers',
    '--reset-foreman-foreman-url',
    '--reset-foreman-gssapi-local-name',
    '--reset-foreman-hsts-enabled',
    '--reset-foreman-http-keytab',
    '--reset-foreman-initial-admin-email',
    '--reset-foreman-initial-admin-first-name',
    '--reset-foreman-initial-admin-last-name',
    '--reset-foreman-initial-admin-locale',
    '--reset-foreman-initial-admin-password',
    '--reset-foreman-initial-admin-timezone',
    '--reset-foreman-initial-admin-username',
    '--reset-foreman-initial-location',
    '--reset-foreman-initial-organization',
    '--reset-foreman-ipa-authentication',
    '--reset-foreman-ipa-authentication-api',
    '--reset-foreman-ipa-manage-sssd',
    '--reset-foreman-keycloak',
    '--reset-foreman-keycloak-app-name',
    '--reset-foreman-keycloak-realm',
    '--reset-foreman-loggers',
    '--reset-foreman-logging-layout',
    '--reset-foreman-logging-level',
    '--reset-foreman-logging-type',
    '--reset-foreman-oauth-active',
    '--reset-foreman-oauth-consumer-key',
    '--reset-foreman-oauth-consumer-secret',
    '--reset-foreman-oauth-effective-user',
    '--reset-foreman-oauth-map-users',
    '--reset-foreman-pam-service',
    '--reset-foreman-plugin-remote-execution-cockpit-origins',
    '--reset-foreman-plugin-tasks-automatic-cleanup',
    '--reset-foreman-plugin-tasks-backup',
    '--reset-foreman-plugin-tasks-cron-line',
    '--reset-foreman-plugin-version',
    '--reset-foreman-proxy-autosignfile',
    '--reset-foreman-proxy-bind-host',
    '--reset-foreman-proxy-bmc',
    '--reset-foreman-proxy-bmc-default-provider',
    '--reset-foreman-proxy-bmc-listen-on',
    '--reset-foreman-proxy-bmc-redfish-verify-ssl',
    '--reset-foreman-proxy-bmc-ssh-key',
    '--reset-foreman-proxy-bmc-ssh-powercycle',
    '--reset-foreman-proxy-bmc-ssh-poweroff',
    '--reset-foreman-proxy-bmc-ssh-poweron',
    '--reset-foreman-proxy-bmc-ssh-powerstatus',
    '--reset-foreman-proxy-bmc-ssh-user',
    '--reset-foreman-proxy-content-enable-ansible',
    '--reset-foreman-proxy-content-enable-deb',
    '--reset-foreman-proxy-content-enable-docker',
    '--reset-foreman-proxy-content-enable-file',
    '--reset-foreman-proxy-content-enable-katello-agent',
    '--reset-foreman-proxy-content-enable-ostree',
    '--reset-foreman-proxy-content-enable-python',
    '--reset-foreman-proxy-content-enable-yum',
    '--reset-foreman-proxy-content-pulpcore-additional-export-paths',
    '--reset-foreman-proxy-content-pulpcore-additional-import-paths',
    '--reset-foreman-proxy-content-pulpcore-allowed-content-checksums',
    '--reset-foreman-proxy-content-pulpcore-api-service-worker-timeout',
    '--reset-foreman-proxy-content-pulpcore-cache-enabled',
    '--reset-foreman-proxy-content-pulpcore-cache-expires-ttl',
    '--reset-foreman-proxy-content-pulpcore-content-service-worker-timeout',
    '--reset-foreman-proxy-content-pulpcore-django-secret-key',
    '--reset-foreman-proxy-content-pulpcore-manage-postgresql',
    '--reset-foreman-proxy-content-pulpcore-mirror',
    '--reset-foreman-proxy-content-pulpcore-postgresql-db-name',
    '--reset-foreman-proxy-content-pulpcore-postgresql-host',
    '--reset-foreman-proxy-content-pulpcore-postgresql-password',
    '--reset-foreman-proxy-content-pulpcore-postgresql-port',
    '--reset-foreman-proxy-content-pulpcore-postgresql-ssl',
    '--reset-foreman-proxy-content-pulpcore-postgresql-ssl-cert',
    '--reset-foreman-proxy-content-pulpcore-postgresql-ssl-key',
    '--reset-foreman-proxy-content-pulpcore-postgresql-ssl-require',
    '--reset-foreman-proxy-content-pulpcore-postgresql-ssl-root-ca',
    '--reset-foreman-proxy-content-pulpcore-postgresql-user',
    '--reset-foreman-proxy-content-pulpcore-telemetry',
    '--reset-foreman-proxy-content-pulpcore-worker-count',
    '--reset-foreman-proxy-content-puppet',
    '--reset-foreman-proxy-content-qpid-router-agent-addr',
    '--reset-foreman-proxy-content-qpid-router-agent-port',
    '--reset-foreman-proxy-content-qpid-router-broker-addr',
    '--reset-foreman-proxy-content-qpid-router-broker-port',
    '--reset-foreman-proxy-content-qpid-router-hub-addr',
    '--reset-foreman-proxy-content-qpid-router-hub-port',
    '--reset-foreman-proxy-content-qpid-router-logging',
    '--reset-foreman-proxy-content-qpid-router-logging-level',
    '--reset-foreman-proxy-content-qpid-router-logging-path',
    '--reset-foreman-proxy-content-qpid-router-ssl-ciphers',
    '--reset-foreman-proxy-content-qpid-router-ssl-protocols',
    '--reset-foreman-proxy-content-reverse-proxy',
    '--reset-foreman-proxy-content-reverse-proxy-port',
    '--reset-foreman-proxy-dhcp',
    '--reset-foreman-proxy-dhcp-additional-interfaces',
    '--reset-foreman-proxy-dhcp-config',
    '--reset-foreman-proxy-dhcp-failover-address',
    '--reset-foreman-proxy-dhcp-failover-port',
    '--reset-foreman-proxy-dhcp-gateway',
    '--reset-foreman-proxy-dhcp-interface',
    '--reset-foreman-proxy-dhcp-ipxe-bootstrap',
    '--reset-foreman-proxy-dhcp-ipxefilename',
    '--reset-foreman-proxy-dhcp-key-name',
    '--reset-foreman-proxy-dhcp-key-secret',
    '--reset-foreman-proxy-dhcp-leases',
    '--reset-foreman-proxy-dhcp-listen-on',
    '--reset-foreman-proxy-dhcp-load-balance',
    '--reset-foreman-proxy-dhcp-load-split',
    '--reset-foreman-proxy-dhcp-manage-acls',
    '--reset-foreman-proxy-dhcp-managed',
    '--reset-foreman-proxy-dhcp-max-response-delay',
    '--reset-foreman-proxy-dhcp-max-unacked-updates',
    '--reset-foreman-proxy-dhcp-mclt',
    '--reset-foreman-proxy-dhcp-nameservers',
    '--reset-foreman-proxy-dhcp-netmask',
    '--reset-foreman-proxy-dhcp-network',
    '--reset-foreman-proxy-dhcp-node-type',
    '--reset-foreman-proxy-dhcp-omapi-port',
    '--reset-foreman-proxy-dhcp-option-domain',
    '--reset-foreman-proxy-dhcp-peer-address',
    '--reset-foreman-proxy-dhcp-ping-free-ip',
    '--reset-foreman-proxy-dhcp-provider',
    '--reset-foreman-proxy-dhcp-pxefilename',
    '--reset-foreman-proxy-dhcp-pxeserver',
    '--reset-foreman-proxy-dhcp-range',
    '--reset-foreman-proxy-dhcp-search-domains',
    '--reset-foreman-proxy-dhcp-server',
    '--reset-foreman-proxy-dhcp-subnets',
    '--reset-foreman-proxy-dns',
    '--reset-foreman-proxy-dns-forwarders',
    '--reset-foreman-proxy-dns-interface',
    '--reset-foreman-proxy-dns-listen-on',
    '--reset-foreman-proxy-dns-managed',
    '--reset-foreman-proxy-dns-provider',
    '--reset-foreman-proxy-dns-reverse',
    '--reset-foreman-proxy-dns-server',
    '--reset-foreman-proxy-dns-tsig-keytab',
    '--reset-foreman-proxy-dns-tsig-principal',
    '--reset-foreman-proxy-dns-ttl',
    '--reset-foreman-proxy-dns-zone',
    '--reset-foreman-proxy-ensure-packages-version',
    '--reset-foreman-proxy-foreman-base-url',
    '--reset-foreman-proxy-foreman-ssl-ca',
    '--reset-foreman-proxy-foreman-ssl-cert',
    '--reset-foreman-proxy-foreman-ssl-key',
    '--reset-foreman-proxy-freeipa-config',
    '--reset-foreman-proxy-freeipa-remove-dns',
    '--reset-foreman-proxy-groups',
    '--reset-foreman-proxy-http',
    '--reset-foreman-proxy-http-port',
    '--reset-foreman-proxy-httpboot',
    '--reset-foreman-proxy-httpboot-listen-on',
    '--reset-foreman-proxy-keyfile',
    '--reset-foreman-proxy-libvirt-connection',
    '--reset-foreman-proxy-libvirt-network',
    '--reset-foreman-proxy-log',
    '--reset-foreman-proxy-log-buffer',
    '--reset-foreman-proxy-log-buffer-errors',
    '--reset-foreman-proxy-log-level',
    '--reset-foreman-proxy-logs',
    '--reset-foreman-proxy-logs-listen-on',
    '--reset-foreman-proxy-manage-puppet-group',
    '--reset-foreman-proxy-oauth-consumer-key',
    '--reset-foreman-proxy-oauth-consumer-secret',
    '--reset-foreman-proxy-oauth-effective-user',
    '--reset-foreman-proxy-plugin-ansible-ansible-dir',
    '--reset-foreman-proxy-plugin-ansible-callback',
    '--reset-foreman-proxy-plugin-ansible-collections-paths',
    '--reset-foreman-proxy-plugin-ansible-enabled',
    '--reset-foreman-proxy-plugin-ansible-host-key-checking',
    '--reset-foreman-proxy-plugin-ansible-install-runner',
    '--reset-foreman-proxy-plugin-ansible-listen-on',
    '--reset-foreman-proxy-plugin-ansible-roles-path',
    '--reset-foreman-proxy-plugin-ansible-runner-package-name',
    '--reset-foreman-proxy-plugin-ansible-ssh-args',
    '--reset-foreman-proxy-plugin-ansible-working-dir',
    '--reset-foreman-proxy-plugin-dhcp-infoblox-dns-view',
    '--reset-foreman-proxy-plugin-dhcp-infoblox-network-view',
    '--reset-foreman-proxy-plugin-dhcp-infoblox-password',
    '--reset-foreman-proxy-plugin-dhcp-infoblox-record-type',
    '--reset-foreman-proxy-plugin-dhcp-infoblox-used-ips-search-type',
    '--reset-foreman-proxy-plugin-dhcp-infoblox-username',
    '--reset-foreman-proxy-plugin-dhcp-remote-isc-dhcp-config',
    '--reset-foreman-proxy-plugin-dhcp-remote-isc-dhcp-leases',
    '--reset-foreman-proxy-plugin-dhcp-remote-isc-key-name',
    '--reset-foreman-proxy-plugin-dhcp-remote-isc-key-secret',
    '--reset-foreman-proxy-plugin-dhcp-remote-isc-omapi-port',
    '--reset-foreman-proxy-plugin-discovery-enabled',
    '--reset-foreman-proxy-plugin-discovery-image-name',
    '--reset-foreman-proxy-plugin-discovery-install-images',
    '--reset-foreman-proxy-plugin-discovery-listen-on',
    '--reset-foreman-proxy-plugin-discovery-source-url',
    '--reset-foreman-proxy-plugin-discovery-tftp-root',
    '--reset-foreman-proxy-plugin-discovery-version',
    '--reset-foreman-proxy-plugin-dns-infoblox-dns-server',
    '--reset-foreman-proxy-plugin-dns-infoblox-dns-view',
    '--reset-foreman-proxy-plugin-dns-infoblox-password',
    '--reset-foreman-proxy-plugin-dns-infoblox-username',
    '--reset-foreman-proxy-plugin-openscap-contentdir',
    '--reset-foreman-proxy-plugin-openscap-corrupted-dir',
    '--reset-foreman-proxy-plugin-openscap-enabled',
    '--reset-foreman-proxy-plugin-openscap-failed-dir',
    '--reset-foreman-proxy-plugin-openscap-listen-on',
    '--reset-foreman-proxy-plugin-openscap-openscap-send-log-file',
    '--reset-foreman-proxy-plugin-openscap-proxy-name',
    '--reset-foreman-proxy-plugin-openscap-puppet-module',
    '--reset-foreman-proxy-plugin-openscap-puppet-module-ensure',
    '--reset-foreman-proxy-plugin-openscap-reportsdir',
    '--reset-foreman-proxy-plugin-openscap-spooldir',
    '--reset-foreman-proxy-plugin-openscap-timeout',
    '--reset-foreman-proxy-plugin-openscap-version',
    '--reset-foreman-proxy-plugin-remote-execution-script-cockpit-integration',
    '--reset-foreman-proxy-plugin-remote-execution-script-enabled',
    '--reset-foreman-proxy-plugin-remote-execution-script-generate-keys',
    '--reset-foreman-proxy-plugin-remote-execution-script-install-key',
    '--reset-foreman-proxy-plugin-remote-execution-script-listen-on',
    '--reset-foreman-proxy-plugin-remote-execution-script-local-working-dir',
    '--reset-foreman-proxy-plugin-remote-execution-script-mode',
    '--reset-foreman-proxy-plugin-remote-execution-script-mqtt-rate-limit',
    '--reset-foreman-proxy-plugin-remote-execution-script-mqtt-resend-interval',
    '--reset-foreman-proxy-plugin-remote-execution-script-mqtt-ttl',
    '--reset-foreman-proxy-plugin-remote-execution-script-remote-working-dir',
    '--reset-foreman-proxy-plugin-remote-execution-script-ssh-identity-dir',
    '--reset-foreman-proxy-plugin-remote-execution-script-ssh-identity-file',
    '--reset-foreman-proxy-plugin-remote-execution-script-ssh-kerberos-auth',
    '--reset-foreman-proxy-plugin-remote-execution-script-ssh-keygen',
    '--reset-foreman-proxy-plugin-remote-execution-script-ssh-log-level',
    '--reset-foreman-proxy-plugin-shellhooks-directory',
    '--reset-foreman-proxy-plugin-shellhooks-enabled',
    '--reset-foreman-proxy-plugin-shellhooks-listen-on',
    '--reset-foreman-proxy-plugin-shellhooks-version',
    '--reset-foreman-proxy-puppet',
    '--reset-foreman-proxy-puppet-api-timeout',
    '--reset-foreman-proxy-puppet-group',
    '--reset-foreman-proxy-puppet-listen-on',
    '--reset-foreman-proxy-puppet-ssl-ca',
    '--reset-foreman-proxy-puppet-ssl-cert',
    '--reset-foreman-proxy-puppet-ssl-key',
    '--reset-foreman-proxy-puppet-url',
    '--reset-foreman-proxy-puppetca',
    '--reset-foreman-proxy-puppetca-certificate',
    '--reset-foreman-proxy-puppetca-listen-on',
    '--reset-foreman-proxy-puppetca-provider',
    '--reset-foreman-proxy-puppetca-sign-all',
    '--reset-foreman-proxy-puppetca-token-ttl',
    '--reset-foreman-proxy-puppetca-tokens-file',
    '--reset-foreman-proxy-puppetdir',
    '--reset-foreman-proxy-realm',
    '--reset-foreman-proxy-realm-keytab',
    '--reset-foreman-proxy-realm-listen-on',
    '--reset-foreman-proxy-realm-principal',
    '--reset-foreman-proxy-realm-provider',
    '--reset-foreman-proxy-register-in-foreman',
    '--reset-foreman-proxy-registered-name',
    '--reset-foreman-proxy-registered-proxy-url',
    '--reset-foreman-proxy-registration',
    '--reset-foreman-proxy-registration-listen-on',
    '--reset-foreman-proxy-registration-url',
    '--reset-foreman-proxy-ssl',
    '--reset-foreman-proxy-ssl-ca',
    '--reset-foreman-proxy-ssl-cert',
    '--reset-foreman-proxy-ssl-disabled-ciphers',
    '--reset-foreman-proxy-ssl-key',
    '--reset-foreman-proxy-ssl-port',
    '--reset-foreman-proxy-ssldir',
    '--reset-foreman-proxy-template-url',
    '--reset-foreman-proxy-templates',
    '--reset-foreman-proxy-templates-listen-on',
    '--reset-foreman-proxy-tftp',
    '--reset-foreman-proxy-tftp-dirs',
    '--reset-foreman-proxy-tftp-listen-on',
    '--reset-foreman-proxy-tftp-manage-wget',
    '--reset-foreman-proxy-tftp-managed',
    '--reset-foreman-proxy-tftp-replace-grub2-cfg',
    '--reset-foreman-proxy-tftp-root',
    '--reset-foreman-proxy-tftp-servername',
    '--reset-foreman-proxy-tls-disabled-versions',
    '--reset-foreman-proxy-trusted-hosts',
    '--reset-foreman-proxy-version',
    '--reset-foreman-rails-cache-store',
    '--reset-foreman-register-in-foreman',
    '--reset-foreman-server-port',
    '--reset-foreman-server-ssl-ca',
    '--reset-foreman-server-ssl-cert',
    '--reset-foreman-server-ssl-chain',
    '--reset-foreman-server-ssl-crl',
    '--reset-foreman-server-ssl-key',
    '--reset-foreman-server-ssl-port',
    '--reset-foreman-server-ssl-protocol',
    '--reset-foreman-server-ssl-verify-client',
    '--reset-foreman-serveraliases',
    '--reset-foreman-servername',
    '--reset-foreman-ssl',
    '--reset-foreman-telemetry-logger-enabled',
    '--reset-foreman-telemetry-logger-level',
    '--reset-foreman-telemetry-prefix',
    '--reset-foreman-telemetry-prometheus-enabled',
    '--reset-foreman-telemetry-statsd-enabled',
    '--reset-foreman-telemetry-statsd-host',
    '--reset-foreman-telemetry-statsd-protocol',
    '--reset-foreman-trusted-proxies',
    '--reset-foreman-unattended',
    '--reset-foreman-unattended-url',
    '--reset-foreman-version',
    '--reset-foreman-websockets-encrypt',
    '--reset-foreman-websockets-ssl-cert',
    '--reset-foreman-websockets-ssl-key',
    '--reset-katello-candlepin-db-host',
    '--reset-katello-candlepin-db-name',
    '--reset-katello-candlepin-db-password',
    '--reset-katello-candlepin-db-port',
    '--reset-katello-candlepin-db-ssl',
    '--reset-katello-candlepin-db-ssl-ca',
    '--reset-katello-candlepin-db-ssl-verify',
    '--reset-katello-candlepin-db-user',
    '--reset-katello-candlepin-manage-db',
    '--reset-katello-candlepin-oauth-key',
    '--reset-katello-candlepin-oauth-secret',
    '--reset-katello-hosts-queue-workers',
    '--reset-katello-qpid-hostname',
    '--reset-katello-qpid-interface',
    '--reset-katello-qpid-wcache-page-size',
    '--reset-katello-rest-client-timeout',
    '--reset-puppet-additional-settings',
    '--reset-puppet-agent',
    '--reset-puppet-agent-additional-settings',
    '--reset-puppet-agent-default-schedules',
    '--reset-puppet-agent-noop',
    '--reset-puppet-agent-restart-command',
    '--reset-puppet-allow-any-crl-auth',
    '--reset-puppet-auth-allowed',
    '--reset-puppet-auth-template',
    '--reset-puppet-autosign',
    '--reset-puppet-autosign-content',
    '--reset-puppet-autosign-entries',
    '--reset-puppet-autosign-mode',
    '--reset-puppet-autosign-source',
    '--reset-puppet-ca-crl-filepath',
    '--reset-puppet-ca-port',
    '--reset-puppet-ca-server',
    '--reset-puppet-classfile',
    '--reset-puppet-client-certname',
    '--reset-puppet-client-package',
    '--reset-puppet-codedir',
    '--reset-puppet-cron-cmd',
    '--reset-puppet-dir',
    '--reset-puppet-dir-group',
    '--reset-puppet-dir-owner',
    '--reset-puppet-dns-alt-names',
    '--reset-puppet-environment',
    '--reset-puppet-group',
    '--reset-puppet-hiera-config',
    '--reset-puppet-http-connect-timeout',
    '--reset-puppet-http-read-timeout',
    '--reset-puppet-localconfig',
    '--reset-puppet-logdir',
    '--reset-puppet-manage-packages',
    '--reset-puppet-module-repository',
    '--reset-puppet-package-install-options',
    '--reset-puppet-package-provider',
    '--reset-puppet-package-source',
    '--reset-puppet-pluginfactsource',
    '--reset-puppet-pluginsource',
    '--reset-puppet-port',
    '--reset-puppet-postrun-command',
    '--reset-puppet-prerun-command',
    '--reset-puppet-puppetconf-mode',
    '--reset-puppet-puppetmaster',
    '--reset-puppet-report',
    '--reset-puppet-run-hour',
    '--reset-puppet-run-minute',
    '--reset-puppet-rundir',
    '--reset-puppet-runinterval',
    '--reset-puppet-runmode',
    '--reset-puppet-server',
    '--reset-puppet-server-acceptor-threads',
    '--reset-puppet-server-additional-settings',
    '--reset-puppet-server-admin-api-whitelist',
    '--reset-puppet-server-allow-header-cert-info',
    '--reset-puppet-server-ca',
    '--reset-puppet-server-ca-allow-auth-extensions',
    '--reset-puppet-server-ca-allow-sans',
    '--reset-puppet-server-ca-auth-required',
    '--reset-puppet-server-ca-client-self-delete',
    '--reset-puppet-server-ca-client-whitelist',
    '--reset-puppet-server-ca-crl-sync',
    '--reset-puppet-server-ca-enable-infra-crl',
    '--reset-puppet-server-certname',
    '--reset-puppet-server-check-for-updates',
    '--reset-puppet-server-cipher-suites',
    '--reset-puppet-server-common-modules-path',
    '--reset-puppet-server-compile-mode',
    '--reset-puppet-server-connect-timeout',
    '--reset-puppet-server-crl-enable',
    '--reset-puppet-server-custom-trusted-oid-mapping',
    '--reset-puppet-server-default-manifest',
    '--reset-puppet-server-default-manifest-content',
    '--reset-puppet-server-default-manifest-path',
    '--reset-puppet-server-dir',
    '--reset-puppet-server-environment-class-cache-enabled',
    '--reset-puppet-server-environment-timeout',
    '--reset-puppet-server-environment-vars',
    '--reset-puppet-server-environments-group',
    '--reset-puppet-server-environments-mode',
    '--reset-puppet-server-environments-owner',
    '--reset-puppet-server-environments-recurse',
    '--reset-puppet-server-envs-dir',
    '--reset-puppet-server-envs-target',
    '--reset-puppet-server-external-nodes',
    '--reset-puppet-server-foreman',
    '--reset-puppet-server-foreman-facts',
    '--reset-puppet-server-foreman-ssl-ca',
    '--reset-puppet-server-foreman-ssl-cert',
    '--reset-puppet-server-foreman-ssl-key',
    '--reset-puppet-server-foreman-url',
    '--reset-puppet-server-git-branch-map',
    '--reset-puppet-server-git-repo',
    '--reset-puppet-server-git-repo-group',
    '--reset-puppet-server-git-repo-mode',
    '--reset-puppet-server-git-repo-path',
    '--reset-puppet-server-git-repo-user',
    '--reset-puppet-server-group',
    '--reset-puppet-server-http',
    '--reset-puppet-server-http-port',
    '--reset-puppet-server-idle-timeout',
    '--reset-puppet-server-ip',
    '--reset-puppet-server-jolokia-metrics-whitelist',
    '--reset-puppet-server-jruby-gem-home',
    '--reset-puppet-server-jvm-cli-args',
    '--reset-puppet-server-jvm-config',
    '--reset-puppet-server-jvm-extra-args',
    '--reset-puppet-server-jvm-java-bin',
    '--reset-puppet-server-jvm-max-heap-size',
    '--reset-puppet-server-jvm-min-heap-size',
    '--reset-puppet-server-manage-user',
    '--reset-puppet-server-max-active-instances',
    '--reset-puppet-server-max-open-files',
    '--reset-puppet-server-max-queued-requests',
    '--reset-puppet-server-max-requests-per-instance',
    '--reset-puppet-server-max-retry-delay',
    '--reset-puppet-server-max-threads',
    '--reset-puppet-server-metrics-allowed',
    '--reset-puppet-server-metrics-graphite-enable',
    '--reset-puppet-server-metrics-graphite-host',
    '--reset-puppet-server-metrics-graphite-interval',
    '--reset-puppet-server-metrics-graphite-port',
    '--reset-puppet-server-metrics-jmx-enable',
    '--reset-puppet-server-metrics-server-id',
    '--reset-puppet-server-multithreaded',
    '--reset-puppet-server-package',
    '--reset-puppet-server-parser',
    '--reset-puppet-server-port',
    '--reset-puppet-server-post-hook-content',
    '--reset-puppet-server-post-hook-name',
    '--reset-puppet-server-puppet-basedir',
    '--reset-puppet-server-puppetserver-auth-template',
    '--reset-puppet-server-puppetserver-dir',
    '--reset-puppet-server-puppetserver-experimental',
    '--reset-puppet-server-puppetserver-logdir',
    '--reset-puppet-server-puppetserver-metrics',
    '--reset-puppet-server-puppetserver-profiler',
    '--reset-puppet-server-puppetserver-rundir',
    '--reset-puppet-server-puppetserver-telemetry',
    '--reset-puppet-server-puppetserver-trusted-agents',
    '--reset-puppet-server-puppetserver-trusted-certificate-extensions',
    '--reset-puppet-server-puppetserver-vardir',
    '--reset-puppet-server-puppetserver-version',
    '--reset-puppet-server-reports',
    '--reset-puppet-server-request-timeout',
    '--reset-puppet-server-ruby-load-paths',
    '--reset-puppet-server-selector-threads',
    '--reset-puppet-server-ssl-acceptor-threads',
    '--reset-puppet-server-ssl-chain-filepath',
    '--reset-puppet-server-ssl-dir',
    '--reset-puppet-server-ssl-dir-manage',
    '--reset-puppet-server-ssl-key-manage',
    '--reset-puppet-server-ssl-protocols',
    '--reset-puppet-server-ssl-selector-threads',
    '--reset-puppet-server-storeconfigs',
    '--reset-puppet-server-strict-variables',
    '--reset-puppet-server-trusted-external-command',
    '--reset-puppet-server-use-legacy-auth-conf',
    '--reset-puppet-server-user',
    '--reset-puppet-server-version',
    '--reset-puppet-server-versioned-code-content',
    '--reset-puppet-server-versioned-code-id',
    '--reset-puppet-server-web-idle-timeout',
    '--reset-puppet-service-name',
    '--reset-puppet-sharedir',
    '--reset-puppet-show-diff',
    '--reset-puppet-splay',
    '--reset-puppet-splaylimit',
    '--reset-puppet-srv-domain',
    '--reset-puppet-ssldir',
    '--reset-puppet-syslogfacility',
    '--reset-puppet-systemd-cmd',
    '--reset-puppet-systemd-randomizeddelaysec',
    '--reset-puppet-systemd-unit-name',
    '--reset-puppet-unavailable-runmodes',
    '--reset-puppet-use-srv-records',
    '--reset-puppet-usecacheonfailure',
    '--reset-puppet-user',
    '--reset-puppet-vardir',
    '--reset-puppet-version',
    '--scenario',
    '--skip-checks-i-know-better',
    '--skip-puppet-version-check',
    '--tuning',
    '--verbose-log-level',
    '-S',
    '-h',
    '-i',
    '-l',
    '-n',
    '-p',
    '-s',
    '-v',
}

LAST_SAVED_SECTIONS = {
    '= Generic:',
    '= Module certs:',
    '= Module foreman:',
    '= Module foreman_cli:',
    '= Module foreman_compute_ec2:',
    '= Module foreman_compute_libvirt:',
    '= Module foreman_compute_openstack:',
    '= Module foreman_compute_ovirt:',
    '= Module foreman_compute_vmware:',
    '= Module foreman_plugin_remote_execution_cockpit:',
    '= Module foreman_plugin_tasks:',
    '= Module foreman_proxy:',
    '= Module foreman_proxy_content:',
    '= Module foreman_proxy_plugin_ansible:',
    '= Module foreman_proxy_plugin_dhcp_infoblox:',
    '= Module foreman_proxy_plugin_dhcp_remote_isc:',
    '= Module foreman_proxy_plugin_discovery:',
    '= Module foreman_proxy_plugin_dns_infoblox:',
    '= Module foreman_proxy_plugin_openscap:',
    '= Module foreman_proxy_plugin_shellhooks:',
    '= Module foreman_proxy_plugin_remote_execution_script:',
    '= Module katello:',
    '= Module puppet:',
}

SATELLITE_SERVICES = [
    'dynflow-sidekiq@orchestrator',
    'dynflow-sidekiq@worker-1',
    'dynflow-sidekiq@worker-hosts-queue-1',
    'foreman-proxy',
    'foreman',
    'httpd',
    'postgresql',
    'pulpcore-api',
    'pulpcore-content',
    'pulpcore-worker@*',
    'tomcat',
]


def extract_help(filter='params'):
    """Generator function to extract satellite installer params and sections from lines
    of help text. In general lst is cmd.stdout, e.g., a list of strings representing host stdout.

    :param string filter: Filter `sections` or `params` in full help, default is params
    :return: generator with params or sections depends on filter parameter
    """
    stdout = ssh.command('satellite-installer --full-help').stdout
    for line in stdout.splitlines() or []:
        line = line.strip()
        if filter == 'sections':
            if line.startswith('= '):
                yield line
        else:
            first_2_tokens = line.split()[:2]
            for token in first_2_tokens:
                if token[0] == '-':
                    yield token.replace(',', '')


@pytest.mark.upgrade
@pytest.mark.tier1
def test_positive_selinux_foreman_module(target_sat):
    """Check if SELinux foreman module is installed on Satellite

    :id: a0736b3a-3d42-4a09-a11a-28c1d58214a5

    :steps:
        1. Check "foreman-selinux" package availability on satellite.
        2. Check SELinux foreman module on satellite.

    :CaseLevel: System

    :expectedresults: Foreman RPM and SELinux module are both present on the satellite
    """
    rpm_result = target_sat.execute('rpm -q foreman-selinux')
    assert rpm_result.status == 0

    semodule_result = target_sat.execute('semodule -l | grep foreman')
    assert semodule_result.status == 0


@pytest.mark.upgrade
@pytest.mark.tier1
@pytest.mark.parametrize('service', SATELLITE_SERVICES)
def test_positive_check_installer_service_running(target_sat, service):
    """Check if a service is running

    :id: 5389c174-7ab1-4e9d-b2aa-66d80fd6dc5f

    :steps:
        1. Verify a service is active with systemctl is-active

    :expectedresults: The service is active

    :CaseImportance: Medium
    """
    is_active = target_sat.execute(f'systemctl is-active {service}')
    status = target_sat.execute(f'systemctl status {service}')
    assert is_active.status == 0, status.stdout


@pytest.mark.upgrade
@pytest.mark.tier1
def test_positive_check_installer_hammer_ping(target_sat):
    """Check if hammer ping reports all services as ok

    :id: 85fd4388-6d94-42f5-bed2-24be38e9f104

    :steps:
        1. Run the 'hammer ping' command on satellite.

    :BZ: 1964394

    :customerscenario: true

    :expectedresults: All services are active (running)

    :CaseLevel: System
    """
    # check status reported by hammer ping command
    result = target_sat.execute('hammer ping')
    test_result = {}
    service = None
    for line in result.stdout.strip().replace(' ', '').split('\n'):
        if line.split(':')[0] not in ('Status', 'ServerResponse', 'message'):
            service = line.split(':')[0]
            test_result[service] = {}
        else:
            key, value = line.split(":", 1)
            test_result[service][key] = value

    not_ok = {svc: result for svc, result in test_result.items() if result['Status'] != 'ok'}
    assert not not_ok


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.parametrize('filter', ['params', 'sections'])
def test_installer_options_and_sections(filter):
    """Look for changes on installer sections and options/flags

    :id: a51d3b9f-f347-4a96-a31a-770349db08c7

    :parametrized: yes

    :steps:
        1. parse installer sections and options/flags
        2. compare with last saved data

    :expectedresults: Ideally sections and options should not change on zstreams.
        Documentation must be updated accordingly when such changes occur.
        So when this test fail we QE can act on it, asking dev if
        changes occurs on zstream and checking docs are up to date.

    :CaseImportance: Medium
    """
    current = set(extract_help(filter=filter))
    previous = PREVIOUS_INSTALLER_OPTIONS if filter == 'params' else LAST_SAVED_SECTIONS
    removed = list(previous - current)
    removed.sort()
    added = list(current - previous)
    added.sort()
    msg = f"###Removed {filter}:\n{removed}\n###Added {filter}:\n{added}"
    assert previous == current, msg


@pytest.mark.tier1
@pytest.mark.build_sanity
@pytest.mark.first_sanity
@pytest.mark.parametrize(
    "installer_satellite", [settings.server.version.rhel_version], indirect=True
)
def test_satellite_installation(installer_satellite):
    """Run a basic Satellite installation

    :id: 661206f3-2eec-403c-af26-3c5cadcd5766

    :steps:
        1. Get RHEL Host
        2. Configure satellite repos
        3. Enable satellite module
        4. Install satellite
        5. Run satellite-installer

    :expectedresults:
        1. Correct satellite packaged is installed
        2. satellite-installer runs successfully
        3. satellite-maintain health check runs successfully

    :CaseImportance: Critical

    """
    result = installer_satellite.execute(
        r'grep "\[ERROR" --after-context=100 /var/log/foreman-installer/satellite.log'
    )
    assert len(result.stdout) == 0
    result = installer_satellite.cli.Health.check()
    assert 'FAIL' not in result.stdout


@pytest.mark.e2e
@pytest.mark.tier1
@pytest.mark.parametrize(
    "installer_satellite", [settings.server.version.rhel_version], indirect=True
)
def test_satellite_and_capsule_installation(installer_satellite, cap_ready_rhel):
    """Run a basic Satellite and Capsule installation

    :id: bbab30a6-6861-494f-96dd-23b883c2c906

    :steps:
        1. Get 2 RHEL hosts
        2. Configure satellite repos
        3. Enable satellite module
        4. Install satellite
        5. Run satellite-installer
        6. Configure capsule repos
        7. Enable capsule module
        8. Install and setup capsule

    :expectedresults:
        1. Correct satellite packaged is installed
        2. satellite-installer runs successfully
        3. satellite-maintain health check runs successfully
        4. Capsule is installed and setup correctly

    :CaseImportance: Critical
    """
    # Get Capsule repofile, and enable and download satellite-capsule
    cap_ready_rhel.register_to_cdn()
    cap_ready_rhel.download_repofile(product='capsule', release=settings.server.version.release)
    cap_ready_rhel.execute(
        'dnf -y module enable satellite-capsule:el8 && dnf -y install satellite-capsule'
    )
    # Configure Satellite firewall to open communication
    installer_satellite.execute(
        'firewall-cmd --permanent --add-service RH-Satellite-6 && '
        'firewall-cmd --add-service RH-Satellite-6'
    )
    # Setup Capsule
    org = installer_satellite.api.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[
        0
    ]
    setup_capsule(installer_satellite, cap_ready_rhel, org)
    assert installer_satellite.api.Capsule().search(
        query={'search': f'name={cap_ready_rhel.hostname}'}
    )[0]
    result = cap_ready_rhel.execute(
        r'grep "\[ERROR" --after-context=100 /var/log/foreman-installer/satellite.log'
    )
    assert len(result.stdout) == 0
    result = cap_ready_rhel.cli.Health.check()
    assert 'FAIL' not in result.stdout


@pytest.mark.stubbed
@pytest.mark.tier3
def test_satellite_installation_on_ipv6():
    """
    Check the satellite installation on ipv6 machine.

    :id: 24fa5ef0-1673-427c-82ab-740758683cff

    :steps:
        1. Install satellite on ipv6 machine.

    :expectedresults:
        1: Installation should be successful.
        2: After installation, All the services should be up and running.
        3. Status of hammer ping should be ok.
        4: Satellite service restart should work.
        5: After system reboot all the services comes to up state.

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_capsule_installation_on_ipv6():
    """
    Check the capsule installation over ipv6 machine

    :id: 75341e29-342f-41fc-aaa8-cda013b7dfa1

    :steps:
        1. Install capsule on ipv6 machine.

    :expectedresults:
        1. Capsule installation should be successful.
        2. After installation, All the Services should be up and running.
        3. Satellite service restart should work.
        4. After system reboot all the services come to up state.

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_installer_check_on_ipv6():
    """
    Check the satellite-installer command execution with tuning options and updated config file.

    :id: 411bbffb-027f-4df0-8566-1719d1d0651a

    :steps:
        1. Install satellite on ipv6 machine
        2. Trigger the satellite-installer command with "--tuning medium" flag.
        3. Update the custom-hira.yaml file(add any supportable config parameter).
        4. Trigger the satellite-installer command with no option.

    :expectedresults:
        1. Tuning parameter set successfully for medium size.
        2. custom-hiera.yaml related changes should be successfully applied.

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_installer_verbose_stdout():
    """Look for Satellite installer verbose STDOUT

    :id: 5d0fb30a-4a63-41b3-bc6f-c4057942ce3c

    :steps:
        1. Install satellite package.
        2. Run Satellite installer
        3. Observe installer STDOUT.

    :expectedresults:
        1. Installer STDOUTs following groups hooks completion.
            pre_migrations, boot, init, pre_values, pre_validations, pre_commit, pre, post
        2. Installer STDOUTs system configuration completion.
        3. Finally, Installer informs running satellite url, credentials,
            external capsule installation pre-requisite, upgrade capsule instruction,
            running internal capsule url, log file.

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_installer_answers_file():
    """Answers file to configure plugins and hooks

    :id: 5cb40e4b-1acb-49f9-a085-a7dead1664b5

    :steps:
        1. Install satellte package
        2. Modify `/etc/foreman-installer/scenarios.d/satellite-answers.yaml` file to
            configure hook/plugin on satellite
        3. Run Satellite installer

    :expectedresults: Installer configures plugins and hooks in answers file.

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier1
def test_capsule_installer_verbose_stdout():
    """Look for Capsule installer verbose STDOUT

    :id: 323e85e3-2ad1-4018-aa35-1d51f1e7f5a2

    :steps:
        1. Install capsule package.
        2. Run Satellite installer --scenario capsule
        3. Observe installer STDOUT.

    :expectedresults:
        1. Installer STDOUTs following groups hooks completion.
            pre_migrations, boot, init, pre_values, pre_validations, pre_commit, pre, post
        2. Installer STDOUTs system configuration completion.
        3. Finally, Installer informs running capsule url, log file.

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_installer_timestamp_logs():
    """Look for Satellite installer timestamp based logs

    :id: 9b4d32f6-d471-4bdb-8a79-9bb20ecb86aa

    :steps:
        1. Install satellite package.
        2. Run Satellite installer
        3. Observe installer log file `/var/log/foreman-installer/satellite.log`.

    :expectedresults:
        1. Installer logs satellite installation with timestamps in following format
            YYYY-MM-DD HH:MM:SS

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_capsule_installer_and_register():
    """Verify the capsule installation and their registration with the satellite.

    :id: efd03442-5a08-445d-b257-e4d346084379

    :steps:
        1. Install the satellite.
        2. Add all the required cdn and custom repositories in satellite to
           install the capsule.
        3. Create life-cycle environment,content view and activation key.
        4. Subscribe the capsule with created activation key.
        5. Run 'yum update -y' on capsule.
        6. Run 'yum install -y satellite-capsule' on capsule.
        7. Create a certificate on satellite for new installed capsule.
        8. Copy capsule certificate from satellite to capsule.
        9. Run the satellite-installer(copy the satellite-installer command from step7'th
            generated output) command on capsule to integrate the capsule with satellite.
        10. Check the newly added capsule is reflected in the satellite or not.
        11. Check the capsule sync.

    :expectedresults:

        1. Capsule integrate successfully with satellite.
        2. Capsule sync should be worked properly.

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_satellite_installer_logfile_check():
    """Verify the no ERROR or FATAL messages appears in the log file during the satellite
    installation

    :id: c2f10f43-c52e-4f32-b3e9-7bc4b07e3b00

    :steps:
        1. Configure all the repositories(custom and cdn) for satellite installation.
        2. Run yum update -y
        3. Run satellite-installer -y
        4. Check all the relevant log-files for ERROR/FATAL

    :expectedresults: No Unexpected ERROR/FATAL message should appear in the following log
        files during the satellite-installation.

        1. /var/log/messages,
        2. /var/log/foreman/production.log
        3. /var/log/foreman-installer/satellite.log
        4. /var/log/httpd,
        5. /var/log/candlepin

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_capsule_installer_logfile_check():
    """Verify the no ERROR or FATAL messages appears in the log file during the capsule
        installation

    :id: cd505a5e-141e-47eb-98d8-a05acd74c3b3

    :steps:
        1. Install the satellite.
        2. Add all the required cdn and custom repositories in satellite to install
            the capsule.
        3. Create life-cycle environment,content view and activation key.
        4. Subscribe the capsule with created activation key.
        5. Run 'yum update -y' on capsule.
        6. Run 'yum install -y satellite-capsule' on capsule.
        7. Create a certificate on satellite for new installed capsule.
        8. Copy capsule certificate from satellite to capsule.
        9. Run the satellite-installer(copy the satellite-installer command from step-7'th
            generated output) command on capsule to integrate the capsule with satellite.
        10. Check all the relevant log-files for ERROR/FATAL

    :expectedresults: No Unexpected ERROR/FATAL message should appear in the following log
        files during the capsule-installation.

        1. /var/log/messages
        2. /var/log/foreman-installer/capsule.log
        3. /var/log/httpd
        4. /var/log/foreman-proxy

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.tier3
def test_installer_cap_pub_directory_accessibility(capsule_configured):
    """Verify the public directory accessibility from capsule url after disabling it from the
    custom-hiera

    :id: b5ca742b-24be-47b3-9bd9-bc5f079409ca

    :steps:
        1. Prepare the satellite and capsule and integrate them.
        2. Check the public directory accessibility from http and https capsule url
        3. Add the 'foreman_proxy_content::pub_dir::pub_dir_options:"+FollowSymLinks -Indexes"'
            in custom-hiera.yaml file on capsule.
        4. Run the satellite-installer on capsule.
        5. Check the public directory accessibility from http and https capsule url.

    :expectedresults: Public directory accessibility from http and https capsule url
        1. It should be accessible if accessibility is enabled(by default it is enabled).
        2. It should not be accessible if accessibility is disabled in custom_hiera.yaml file.

    :CaseImportance: High

    :CaseLevel: System

    :BZ: 1860519

    :customerscenario: true
    """
    custom_hiera_location = '/etc/foreman-installer/custom-hiera.yaml'
    custom_hiera_settings = (
        'foreman_proxy_content::pub_dir::pub_dir_options: "+FollowSymLinks -Indexes"'
    )
    http_curl_command = f'curl -i {capsule_configured.url.replace("https", "http")}/pub/ -k'
    https_curl_command = f'curl -i {capsule_configured.url}/pub/ -k'
    for command in [http_curl_command, https_curl_command]:
        accessibility_check = capsule_configured.execute(command)
        assert 'HTTP/1.1 200 OK' or 'HTTP/2 200 ' in accessibility_check.stdout.split('\r\n')
    capsule_configured.get(
        local_path='custom-hiera-capsule.yaml',
        remote_path=f'{custom_hiera_location}',
    )
    _ = capsule_configured.execute(f'echo {custom_hiera_settings} >> {custom_hiera_location}')
    command_output = capsule_configured.execute('satellite-installer', timeout='20m')
    assert 'Success!' in command_output.stdout
    for command in [http_curl_command, https_curl_command]:
        accessibility_check = capsule_configured.execute(command)
        assert 'HTTP/1.1 200 OK' or 'HTTP/2 200 ' not in accessibility_check.stdout.split('\r\n')
    capsule_configured.put(
        local_path='custom-hiera-capsule.yaml',
        remote_path=f'{custom_hiera_location}',
    )
    command_output = capsule_configured.execute('satellite-installer', timeout='20m')
    assert 'Success!' in command_output.stdout
