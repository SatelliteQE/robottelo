# -*- encoding: utf-8 -*-
"""
Usage:
    katello-installer [OPTIONS]

Options:

= Generic:
    --reset
    --clear-pulp-content
    --clear-puppet-environments
    --certs-update-server
    --certs-update-server-ca
    --certs-update-all
    --certs-skip-check
    --upgrade
    --[no-]colors
    --color-of-background COLOR
    -d, --dont-save-answers
    --ignore-undocumented
    -i, --interactive
    --log-level LEVEL
    -n, --noop
    -v, --verbose
    -l, --verbose-log-level LEVEL
    -h, --help
    --full-help
    --[no-]enable-capsule
    --[no-]enable-certs
    --[no-]enable-foreman
    --[no-]enable-foreman-plugin-bootdisk
    --[no-]enable-foreman-plugin-chef
    --[no-]enable-foreman-plugin-default-hostgroup
    --[no-]enable-foreman-plugin-discovery
    --[no-]enable-foreman-plugin-hooks
    --[no-]enable-foreman-plugin-puppetdb
    --[no-]enable-foreman-plugin-setup
    --[no-]enable-foreman-plugin-tasks
    --[no-]enable-foreman-plugin-templates
    --[no-]enable-katello
    --[no-]enable-katello-plugin-gutterball

= Module capsule:
    --capsule-bmc
    --capsule-bmc-default-provider
    --capsule-certs-tar
    --capsule-dhcp
    --capsule-dhcp-config
    --capsule-dhcp-gateway
    --capsule-dhcp-interface
    --capsule-dhcp-key-name
    --capsule-dhcp-key-secret
    --capsule-dhcp-leases
    --capsule-dhcp-listen-on
    --capsule-dhcp-managed
    --capsule-dhcp-nameservers
    --capsule-dhcp-option-domain
    --capsule-dhcp-range
    --capsule-dhcp-vendor
    --capsule-dns
    --capsule-dns-forwarders
    --capsule-dns-interface
    --capsule-dns-managed
    --capsule-dns-provider
    --capsule-dns-reverse
    --capsule-dns-server
    --capsule-dns-tsig-keytab
    --capsule-dns-tsig-principal
    --capsule-dns-ttl
    --capsule-dns-zone
    --capsule-foreman-oauth-effective-user
    --capsule-foreman-oauth-key
    --capsule-foreman-oauth-secret
    --capsule-foreman-proxy-http
    --capsule-foreman-proxy-http-port
    --capsule-foreman-proxy-port
    --capsule-freeipa-remove-dns
    --capsule-parent-fqdn
    --capsule-pulp
    --capsule-pulp-admin-password
    --capsule-pulp-master
    --capsule-pulp-oauth-effective-user
    --capsule-pulp-oauth-key
    --capsule-pulp-oauth-secret
    --capsule-puppet
    --capsule-puppet-ca-proxy
    --capsule-puppetca
    --capsule-qpid-router
    --capsule-qpid-router-agent-addr
    --capsule-qpid-router-agent-port
    --capsule-qpid-router-broker-addr
    --capsule-qpid-router-broker-port
    --capsule-qpid-router-hub-addr
    --capsule-qpid-router-hub-port
    --capsule-realm
    --capsule-realm-keytab
    --capsule-realm-principal
    --capsule-realm-provider
    --capsule-register-in-foreman
    --capsule-reverse-proxy
    --capsule-reverse-proxy-port
    --capsule-rhsm-url
    --capsule-templates
    --capsule-tftp
    --capsule-tftp-dirs
    --capsule-tftp-root
    --capsule-tftp-servername
    --capsule-tftp-syslinux-files
    --capsule-tftp-syslinux-root
    --capsule-virsh-network

= Module certs:
    --certs-ca-common-name
    --certs-ca-expiration
    --certs-city
    --certs-country
    --certs-default-ca-name
    --certs-deploy
    --certs-expiration
    --certs-generate
    --certs-group
    --certs-log-dir
    --certs-node-fqdn
    --certs-org
    --certs-org-unit
    --certs-password-file-dir
    --certs-pki-dir
    --certs-regenerate
    --certs-regenerate-ca
    --certs-server-ca-cert
    --certs-server-ca-name
    --certs-server-cert
    --certs-server-cert-req
    --certs-server-key
    --certs-ssl-build-dir
    --certs-state
    --certs-user

= Module foreman:
    --foreman-admin-email
    --foreman-admin-first-name
    --foreman-admin-last-name
    --foreman-admin-password
    --foreman-admin-username
    --foreman-app-root
    --foreman-authentication
    --foreman-configure-brightbox-repo
    --foreman-configure-epel-repo
    --foreman-configure-ipa-repo
    --foreman-configure-scl-repo
    --foreman-custom-repo
    --foreman-db-adapter
    --foreman-db-database
    --foreman-db-host
    --foreman-db-manage
    --foreman-db-password
    --foreman-db-port
    --foreman-db-sslmode
    --foreman-db-type
    --foreman-db-username
    --foreman-environment
    --foreman-foreman-url
    --foreman-gpgcheck
    --foreman-group
    --foreman-http-keytab
    --foreman-initial-location
    --foreman-initial-organization
    --foreman-ipa-authentication
    --foreman-ipa-manage-sssd
    --foreman-locations-enabled
    --foreman-oauth-active
    --foreman-oauth-consumer-key
    --foreman-oauth-consumer-secret
    --foreman-oauth-map-users
    --foreman-organizations-enabled
    --foreman-pam-service
    --foreman-passenger
    --foreman-passenger-interface
    --foreman-passenger-min-instances
    --foreman-passenger-prestart
    --foreman-passenger-ruby
    --foreman-passenger-ruby-package
    --foreman-passenger-scl
    --foreman-passenger-start-timeout
    --foreman-puppet-home
    --foreman-repo
    --foreman-selinux
    --foreman-server-ssl-ca
    --foreman-server-ssl-cert
    --foreman-server-ssl-chain
    --foreman-server-ssl-key
    --foreman-servername
    --foreman-ssl
    --foreman-unattended
    --foreman-use-vhost
    --foreman-user
    --foreman-user-groups
    --foreman-version
    --foreman-websockets-encrypt
    --foreman-websockets-ssl-cert
    --foreman-websockets-ssl-key

= Module katello:
    --katello-cdn-ssl-version
    --katello-config-dir
    --katello-group
    --katello-log-dir
    --katello-oauth-key
    --katello-oauth-secret
    --katello-package-names
    --katello-post-sync-token
    --katello-proxy-password
    --katello-proxy-port
    --katello-proxy-url
    --katello-proxy-username
    --katello-use-passenger
    --katello-user
    --katello-user-groups
"""
from robottelo.install.base import Base


class InstallerError(Base.InstallError):
    """Indicates that a install command could not be run."""


class Installer(Base):
    """katello-installer command"""
    command_base = 'katello-installer'
    command_service = 'katello'

    @classmethod
    def configure_generic(cls, options=None):
        """dummy"""
        return cls.execute(cls._construct_command(options))

    @classmethod
    def configure_capsule(cls, options=None):
        """dummy"""
        return cls.execute(cls._construct_command(options))

    @classmethod
    def configure_certs(cls, options=None):
        """dummy"""
        return cls.execute(cls._construct_command(options))

    @classmethod
    def configure_foreman(cls, options=None):
        """dummy"""
        return cls.execute(cls._construct_command(options))

    @classmethod
    def configure_katello(cls, options=None):
        """dummy"""
        return cls.execute(cls._construct_command(options))
