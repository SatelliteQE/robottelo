"""Test for Performance Tuning related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Performance

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from unittest2.case import TestCase
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade

from robottelo import ssh
from robottelo.decorators import destructive


DEFAULT_CUSTOM_HIERA_DATA = [
    "---",
    "# This YAML file lets you set your own custom configuration in Hiera for the",
    "# installer puppet modules that might not be exposed to users directly through",
    "# installer arguments.",
    "#",
    "# For example, to set 'TraceEnable Off' in Apache, a common requirement for",
    "# security auditors, add this to this file:",
    "#",
    "#   apache::trace_enable: Off",
    "#",
    "# Consult the full module documentation on http://forge.puppetlabs.com,",
    "# or the actual puppet classes themselves, to discover options to configure.",
    "#",
    "# Do note, setting some values may have unintended consequences that affect the",
    "# performance or functionality of the application. Consider the impact of your",
    "# changes before applying them, and test them in a non-production environment",
    "# first.",
    "#",
    "# Here are some examples of how you tune the Apache options if needed:",
    "#",
    "# apache::mod::prefork::startservers: 8",
    "# apache::mod::prefork::minspareservers: 5",
    "# apache::mod::prefork::maxspareservers: 20",
    "# apache::mod::prefork::serverlimit: 256",
    "# apache::mod::prefork::maxclients: 256",
    "# apache::mod::prefork::maxrequestsperchild: 4000",
    "# Here are some examples of how you tune the PostgreSQL options if needed:",
    "#",
    "# postgresql::server::config_entries:",
    "#   max_connections: 600",
    "#   shared_buffers: 1024MB",
]

MEDIUM_TUNING_DATA = [
    "apache::mod::passenger::passenger_max_pool_size: 30",
    "apache::mod::passenger::passenger_max_request_queue_size: 1000",
    "apache::mod::passenger::passenger_max_requests: 1000",
    " ",
    "apache::mod::prefork::serverlimit: 1024",
    "apache::mod::prefork::maxclients: 1024",
    "apache::mod::prefork::maxrequestsperchild: 4000",
    " ",
    "qpid::open_file_limit: 65536",
    "qpid::router::open_file_limit: 150100",
    " ",
    "postgresql::server::config_entries:",
    "  max_connections: 1000",
    "  shared_buffers: 4GB",
    "  work_mem: 4MB",
    "  checkpoint_segments: 32",
    "  checkpoint_completion_target: 0.9",
    "  effective_cache_size: 16GB",
    "  autovacuum_vacuum_cost_limit: 2000",
    "  log_min_duration_statement: 500 ",
]

MMPV1_MONGODB = [
    "# Added by foreman-installer during upgrade, run the "
    "installer with --upgrade-mongo-storage to upgrade to WiredTiger.",
    "mongodb::server::storage_engine: 'mmapv1'",
]

WIREDTIGER_MONGODB = ["# Do not remove", "mongodb::server::storage_engine: 'wiredTiger'"]


@destructive
class ScenarioPerformanceTuning(TestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    Performance Tuning utility

    Test Steps:

    1. Before Satellite upgrade, we will apply the medium tune size.
    2. Once the size get apply we will wait for post upgrade test case to check
    whether the size is same or not.
    3. In post upgrade we will check whether satellite installer was able to change
    the size or not

    :expectedresults: The performance parameter should not be changed after upgrade.
    """

    @staticmethod
    def _create_custom_hiera_file(mongodb_type, tune_size="default"):
        """
        This function we will use to create a custom-hiera.yaml file
        as per users requirement"
        :param int mongodb_type: Use to select  MMPV1 or WiredTiger data.
        :param str tune_size: tune size would be medium, large, extra-large,
        extra-extra-large.
        """
        with open('custom-hiera.yaml', 'w') as fd:
            fd.write("\n".join(DEFAULT_CUSTOM_HIERA_DATA))
            if mongodb_type:
                fd.write("\n".join(MMPV1_MONGODB))
            else:
                fd.write("\n".join(WIREDTIGER_MONGODB))
            if tune_size == "medium":
                fd.write("\n".join(MEDIUM_TUNING_DATA))

    @pre_upgrade
    def test_pre_performance_tuning_apply(self):
        """In preupgrade scenario we will apply the medium tuning size.

        :id: preupgrade-83404326-20b7-11ea-a370-48f17f1fc2e1

        :steps:
            1. Run satellite-installer --disable-system-checks.

        :expectedresults: Medium tuning parameter should be applied.

         """
        cmd = (
            'grep "mongodb::server::storage_engine: \'wiredTiger\'" '
            '/etc/foreman-installer/custom-hiera.yaml'
        )
        mongodb_type = ssh.command(cmd).return_code
        self._create_custom_hiera_file(mongodb_type, "medium")
        try:
            ssh.upload_file('custom-hiera.yaml', '/etc/foreman-installer')
            command_output = ssh.command(
                'satellite-installer -s --disable-system-checks', connection_timeout=1000
            ).stdout
            assert '  Success!' in command_output
        except Exception:
            self._create_custom_hiera_file(mongodb_type, "default")
            ssh.upload_file('custom-hiera.yaml', '/etc/foreman-installer')
            command_output = ssh.command(
                'satellite-installer -s --disable-system-checks', connection_timeout=1000
            ).stdout
            assert '  Success!' in command_output
            raise

    @post_upgrade(depend_on=test_pre_performance_tuning_apply)
    def test_post_performance_tuning_apply(self):
        """In postupgrade scenario, we will check the tune parameter state after upgrade

        :id: postupgrade-31e26b08-2157-11ea-9223-001a4a1601d8

        :steps:
            1. Collect the current tuning state from satellite.yaml file.
            2. Compare it with the expected value.
            3. If Expected value get match then this scenario would be passed.
            1. Run satellite-installer --tuning medium --disable-system-checks.

        :expectedresults: Medium tuning parameter should be applied.

         """
        cmd = (
            'grep "mongodb::server::storage_engine: \'wiredTiger\'" '
            '/etc/foreman-installer/custom-hiera.yaml'
        )
        mongodb_type = ssh.command(cmd).return_code
        try:
            self._create_custom_hiera_file(mongodb_type)
            cmd = 'grep "tuning: medium" /etc/foreman-installer/scenarios.d/satellite.yaml'
            tuning_state_after_upgrade = ssh.command(cmd).return_code
            assert tuning_state_after_upgrade == 0
            ssh.upload_file('custom-hiera.yaml', '/etc/foreman-installer')
            command_output = ssh.command(
                'satellite-installer --tuning default ' '-s --disable-system-checks',
                connection_timeout=1000,
            ).stdout
            assert "  Success!" in command_output
        finally:
            ssh.upload_file('custom-hiera.yaml', '/etc/foreman-installer')
            command_output = ssh.command(
                'satellite-installer -s ' '--disable-system-checks', connection_timeout=1000
            ).stdout
            assert "  Success!" in command_output


class ScenarioCustomFileCheck(TestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test
       Custom-hiera.yaml files default content.

       Test Steps:

       1. Before Satellite upgrade, we will collect the custom-hiera file details.
       2. And after that we will compare it with the default customer-hiera.yaml
       file.
       3. If some changes happens in the custom-hiera.yaml file then we mark the test
       case fail.
       4- We will perform the same step1 and step2 after post upgrade too.

      :expectedresults: Custom-hiera.yaml file should not be changed after upgrade.
    """

    @pre_upgrade
    def test_pre_custom_hiera_file_validation(self):
        """ In preupgrade scenario we will validate the default custom-hiera file
        parameter with expected custom-hiera file.

        :id: preupgrade-844a8478-289d-11ea-9030-48f17f1fc2e1

        steps:
            1. Collect the custom-hiera.yaml file from current setup.
            2. Compare it with default custom-hiera.yaml file.
            3. If the content of both the file have same then sceanrio would be
            passed.

        expectedresults: Content of default custom-hiera file should be same.

        """
        actual_custom_hiera = ssh.command("cat /etc/foreman-installer/custom-hiera.yaml").stdout
        actual_custom_hiera = set([data.strip() for data in actual_custom_hiera if data != ''])
        cmd = (
            'grep "mongodb::server::storage_engine: \'wiredTiger\'" '
            '/etc/foreman-installer/custom-hiera.yaml'
        )
        mongodb_type = ssh.command(cmd).return_code
        if mongodb_type:
            expected_custom_hiera = set(DEFAULT_CUSTOM_HIERA_DATA + MMPV1_MONGODB)
        else:
            expected_custom_hiera = set(DEFAULT_CUSTOM_HIERA_DATA + WIREDTIGER_MONGODB)

        assert expected_custom_hiera == actual_custom_hiera

    @post_upgrade(depend_on=test_pre_custom_hiera_file_validation)
    def test_post_custom_hiera_file_validation(self):
        """ In postupgrade scenario we will validate the default custom hiera file
        parameter with expected custom_hiera file after the upgrade.

        :id: preupgrade-ba33bef6-289d-11ea-9030-48f17f1fc2e1

        steps:
            1. Collect the custom-hiera.yaml file from current setup.
            2. Compare it with default custom-hiera.yaml file.
            3. If the content of both the file have same then sceanrio would be passed.

        expectedresults: Content of default custom-hiera file should be same.

        """
        actual_custom_hiera = ssh.command("cat /etc/foreman-installer/custom-hiera.yaml").stdout
        actual_custom_hiera = set([data.strip() for data in actual_custom_hiera if data != ''])
        cmd = (
            'grep "mongodb::server::storage_engine: \'wiredTiger\'" '
            '/etc/foreman-installer/custom-hiera.yaml'
        )
        mongodb_type = ssh.command(cmd).return_code
        if mongodb_type:
            expected_custom_hiera = set(DEFAULT_CUSTOM_HIERA_DATA + MMPV1_MONGODB)
        else:
            expected_custom_hiera = set(DEFAULT_CUSTOM_HIERA_DATA + WIREDTIGER_MONGODB)

        assert expected_custom_hiera == actual_custom_hiera
