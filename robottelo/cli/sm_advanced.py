"""
Usage:
    satellite-maintain advanced procedure run [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    backup-accessibility-confirmation Confirm turning off services is allowed
    backup-clean                  Clean up backup directory
    backup-compress-data          Compress backup data to save space
    backup-config-files           Backup config files
    backup-enabled-repos          Stores enabled repositories in yaml file
    backup-metadata               Generate metadata
    backup-offline-candlepin-db   Backup Candlepin DB offline
    backup-offline-foreman-db     Backup Foreman DB offline
    backup-offline-pulpcore-db    Backup Pulpcore DB offline
    backup-online-candlepin-db    Backup Candlepin database online
    backup-online-foreman-db      Backup Foreman database online
    backup-online-pg-global-objects Backup Postgres global objects online
    backup-online-pulpcore-db     Backup Pulpcore database online
    backup-online-safety-confirmation Data consistency warning
    backup-prepare-directory      Prepare backup Directory
    backup-pulp                   Backup Pulp data
    backup-snapshot-clean-mount   Remove the snapshot mount points
    backup-snapshot-logical-volume-confirmation Check if backup is on different LV then the source
    backup-snapshot-mount-candlepin-db Create and mount snapshot of Candlepin DB
    backup-snapshot-mount-foreman-db Create and mount snapshot of Foreman DB
    backup-snapshot-mount-pulp    Create and mount snapshot of Pulp data
    backup-snapshot-mount-pulpcore-db Create and mount snapshot of Pulpcore DB
    backup-snapshot-prepare-mount Prepare mount point for the snapshot
    content-migration-reset       Reset the Pulp 2 to Pulp 3 migration data (pre-switchover)
    content-migration-stats       Retrieve Pulp 2 to Pulp 3 migration statistics
    content-prepare               Prepare content for Pulp 3
    content-prepare-abort         Abort all running Pulp 2 to Pulp 3 migration tasks
    disable-maintenance-mode      Remove maintenance mode table/chain from nftables/iptables
    enable-maintenance-mode       Add maintenance_mode tables/chain to nftables/iptables
    files-remove                  Remove the files
    foreman-fix-corrupted-roles   Create filters where each filter has only permissions of resource
    foreman-proxy-features        Detect features available in the local proxy
    foreman-remove-duplicate-permissions Remove duplicate permissions from database
    foreman-tasks-delete          Delete tasks
    foreman-tasks-resume          Resume paused tasks
    foreman-tasks-ui-investigate  Investigate the tasks via UI
    hammer-setup                  Setup hammer
    installer-run                 Procedures::Installer::Run
    installer-upgrade             Procedures::Installer::Upgrade
    installer-upgrade-rake-task   Execute upgrade:run rake task
    packages-check-update         Check for available package updates
    packages-install              Install packages
    packages-installer-confirmation Confirm installer run is allowed
    packages-lock-versions        Lock packages
    packages-locking-status       Check status of version locking of packages
    packages-unlock-versions      Unlock packages
    packages-update               Procedures::Packages::Update
    packages-update-all-confirmation Confirm update all is intentional
    pulp-print-remove-instructions Print pulp 2 removal instructions
    pulp-remove                   Remove pulp2
    pulpcore-migrate              Migrate pulpcore db
    puppet-remove-puppet-data     Remove Puppet data
    refresh-features              Refresh detected features
    repositories-disable          Disable repositories
    repositories-enable           Enable repositories
    repositories-setup            Setup repositories
    restore-candlepin-dump        Restore candlepin postgresql dump from backup
    restore-candlepin-reset-migrations Ensure Candlepin runs all migrations after restoring the DB
    restore-configs               Restore configs from backup
    restore-confirmation          Confirm dropping databases and running restore
    restore-drop-databases        Drop postgresql databases
    restore-extract-files         Extract any existing tar files in backup
    restore-foreman-dump          Restore foreman postgresql dump from backup
    restore-installer-reset       Run installer reset
    restore-pg-global-objects     Restore any existing postgresql global objects from backup
    restore-postgres-owner        Make postgres owner of backup directory
    restore-pulpcore-dump         Restore pulpcore postgresql dump from backup
    service-daemon-reload         Run daemon reload
    service-disable               Disable applicable services
    service-enable                Enable applicable services
    service-list                  List applicable services
    service-restart               Restart applicable services
    service-start                 Start applicable services
    service-status                Get status of applicable services
    service-stop                  Stop applicable services
    sync-plans-disable            disable active sync plans
    sync-plans-enable             re-enable sync plans

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class Advanced(Base):
    """Manipulates Satellite-maintain's advanced procedure run command"""

    command_base = 'advanced procedure run'

    @classmethod
    def run_service_restart(cls, options=None):
        """Build satellite-maintain advanced procedure run service-restart"""
        cls.command_sub = 'service-restart'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_service_stop(cls, options=None):
        """Build satellite-maintain advanced procedure run service-stop"""
        cls.command_sub = 'service-stop'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_service_start(cls, options=None):
        """Build satellite-maintain advanced procedure run service-start"""
        cls.command_sub = 'service-start'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_packages_install(cls, options=None):
        """Build satellite-maintain advanced procedure run packages-install"""
        cls.command_sub = 'packages-install'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_packages_update(cls, options=None):
        """Build satellite-maintain advanced procedure run packages-update"""
        cls.command_sub = 'packages-update'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_packages_check_update(cls, options=None):
        """Build satellite-maintain advanced procedure run packages-check-update"""
        cls.command_sub = 'packages-check-update'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_disable_maintenance_mode(cls, options=None):
        """Build satellite-maintain advanced procedure run disable-maintenance-mode"""
        cls.command_sub = 'disable-maintenance-mode'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_enable_maintenance_mode(cls, options=None):
        """Build satellite-maintain advanced procedure run enable-maintenance-mode"""
        cls.command_sub = 'enable-maintenance-mode'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_foreman_tasks_delete(cls, options=None):
        """Build satellite-maintain advanced procedure run foreman-tasks-delete"""
        cls.command_sub = 'foreman-tasks-delete'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_foreman_tasks_resume(cls, options=None):
        """Build satellite-maintain advanced procedure run foreman-tasks-resume"""
        cls.command_sub = 'foreman-tasks-resume'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_sync_plans_enable(cls, options=None):
        """Build satellite-maintain advanced procedure run sync-plans-enable"""
        cls.command_sub = 'sync-plans-enable'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_sync_plans_disable(cls, options=None):
        """Build satellite-maintain advanced procedure run sync-plans-disable"""
        cls.command_sub = 'sync-plans-disable'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def run_foreman_tasks_ui_investigate(cls, options=None, env_var=''):
        """Build satellite-maintain advanced procedure run foreman-tasks-ui-investigate"""
        cls.command_sub = 'foreman-tasks-ui-investigate'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def run_hammer_setup(cls, options=None, env_var=''):
        """Build satellite-maintain advanced procedure run hammer-setup"""
        cls.command_sub = 'hammer-setup'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def run_repositories_setup(cls, options=None, env_var=''):
        """Build satellite-maintain advanced procedure run repositories-setup"""
        cls.command_sub = 'repositories-setup'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)
