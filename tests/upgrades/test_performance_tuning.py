"""Test for Performance Tuning related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Performance

:Assignee: psuriset

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import filecmp
import os

import pytest
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade


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
    "#",
    "# Here are some examples of how you tune the PostgreSQL options if needed:",
    "#",
    "# postgresql::server::config_entries:",
    "#   max_connections: 600",
    "#   shared_buffers: 1024MB",
]

MEDIUM_TUNING_DATA = [
    "",
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
    "  log_min_duration_statement: 500",
]

MMPV1_MONGODB = [
    "",
    "# Added by foreman-installer during upgrade, run the "
    "installer with --upgrade-mongo-storage to upgrade to WiredTiger.",
    "mongodb::server::storage_engine: 'mmapv1'",
]

WIREDTIGER_MONGODB = [
    "",
    "# Do not remove",
    "mongodb::server::storage_engine: 'wiredTiger'",
]

MEDIUM_TUNE_PARAM_GROUPS = {
    "apache_params": [
        "apachemodpassengerpassenger_max_pool_size",
        "apachemodpassengerpassenger_max_request_queue_size",
        "apachemodpassengerpassenger_max_requests",
        "_",
    ],
    "pre_fork_param": [
        "apachemodpreforkserverlimit",
        "apachemodpreforkmaxclients",
        "apachemodpreforkmaxrequestsperchild",
        "_",
    ],
    'open_file_params': ["qpidopen_file_limit", "_"],
    'qpid_open_params': ["qpidrouteropen_file_limit", "_"],
    'postgre_params': [
        "max_connections",
        "shared_buffers",
        "checkpoint_completion_target",
        "work_mem",
        "log_min_duration_statement",
        "checkpoint_segments",
        "effective_cache_size",
        "autovacuum_vacuum_cost_limit",
        "_",
    ],
}

TUNE_DATA_COLLECTION_REGEX = {
    "apache_params": " awk '/MaxPoolSize|PassengerMaxRequestQueueSize|"
    "PassengerMaxRequests/ {print $NF}' "
    "/etc/httpd/conf.modules.d/passenger_extra.conf",
    "pre_fork_param": "awk '/ServerLimit|MaxClients|MaxRequestsPerChild/ {print $NF}'"
    " /etc/httpd/conf.modules.d/prefork.conf",
    "qpid_open_params": "awk -F'=' '/LimitNOFILE/ {print $NF}' "
    "/etc/systemd/system/qdrouterd.service.d/90-limits.conf",
    "open_file_params": "awk -F'=' '/LimitNOFILE/ {print $NF}' "
    "/etc/systemd/system/qpidd.service.d/90-limits.conf",
    "postgre_params": "awk -F'= ||#' '/^max_connections|^shared_buffers|^work_mem|"
    "^checkpoint_segments|^checkpoint_completion_target|"
    "^effective_cache_size|^autovacuum_vacuum_cost_limit|"
    "^log_min_duration_statement/ {print $2}' "
    "/var/lib/pgsql/data/postgresql.conf",
}


@pytest.mark.destructive
class TestScenarioPerformanceTuning:
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    Performance Tuning utility

    Test Steps::

        1. Before satellite upgrade.
           - Apply the medium tune size using satellite-installer.
           - Check the tuning status and their set tuning parameters after applying the new size.
        2. Upgrade the satellite.
        3. Verify the following points.
              Before Upgrade:
                 - Satellite-installer work correctly with selected tune size.
                 - tune parameter set correctly on the satellite server.
              After Upgrade:
                 - Custom-hiera file should be unchanged.
                 - tune parameter should be unchanged.
                 - satellite-installer restore the default tune parameter with new approach.

    :expectedresults: Set tuning parameters and custom-hiera.yaml file should be unchanged after
    upgrade.
    """

    @staticmethod
    def _create_custom_hiera_file(mongodb_type, tune_size="default"):
        """
        This method is used to create a custom-hiera.yaml file based on the
        mongo database type and their provided tune size.

        :param int mongodb_type: Use to select  MMPV1 or WiredTiger data.
        :param str tune_size: Tune size would be medium, large, extra-large,
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

    @staticmethod
    def _data_creation_of_set_tune_params(
        tune_size_data, tune_params_collection_regex, tune_params_group, satellite
    ):
        """
        This method is used to create the key(tune-param)-value(set value) pair of applied
        parameters and set parameters(on satellite)

        :param list tune_size_data: List of parameters of selected tune size.
        :param dict tune_params_collection_regex: Key, value mapped regex expression based on
        selected tune size.
        :param dict tune_params_group: Key, value mapped group of param's of selected size.

        :returns dict: Return the created & collected key value pair of tune parameters.
        """
        tune_param = dict()
        mapped_tune_param = dict()
        for tune_data in tune_size_data:
            tune_data = tune_data.replace("::", "").strip()
            if len(tune_data):
                tune_data = tune_data.split(':')
                if tune_data[1].strip():
                    tune_param[tune_data[0]] = tune_data[1].strip()

        for tune_name, tune_cmd in tune_params_collection_regex.items():
            tune_cmd_output = satellite.execute(f'{tune_cmd}').stdout
            tune_module = {
                key: value.strip()
                for key, value in zip(tune_params_group[tune_name], tune_cmd_output.split('\n'))
            }
            mapped_tune_param.update(tune_module)
        mapped_tune_param.pop("_")
        return tune_param, mapped_tune_param

    @pre_upgrade
    def test_pre_performance_tuning_apply(self, default_sat):
        """In preupgrade scenario we apply the medium tuning size.

        :id: preupgrade-83404326-20b7-11ea-a370-48f17f1fc2e1

        :steps:
            1. Create the custom-hiera.yaml file based on mongodb type and selected tune size.
            2. Run the satellite-installer --disable-system-checks to apply the medium tune size.
            3. Check the satellite-installer command status
            4. Check the applied parameter's value, to make sure the values are set successfully
            or not.
            5. If something gets wrong with updated tune parameter restore the system states with
             default custom-hiera.yaml file.

        :expectedresults: Medium tuning parameter should be applied.

        """
        cmd = (
            'grep "mongodb::server::storage_engine: \'wiredTiger\'" '
            '/etc/foreman-installer/custom-hiera.yaml'
        )
        mongodb_type = default_sat.execute(cmd).status
        self._create_custom_hiera_file(mongodb_type, "medium")
        try:
            default_sat.put(
                local_path='custom-hiera.yaml',
                remote_path='/etc/foreman-installer/custom-hiera.yaml',
            )
            command_output = default_sat.execute(
                'satellite-installer -s --disable-system-checks', timeout=1000000
            )
            assert 'Success!' in command_output.stdout

            expected_tune_size, actual_tune_size = self._data_creation_of_set_tune_params(
                MEDIUM_TUNING_DATA,
                TUNE_DATA_COLLECTION_REGEX,
                MEDIUM_TUNE_PARAM_GROUPS,
                default_sat,
            )

            assert actual_tune_size == expected_tune_size

        except Exception:
            self._create_custom_hiera_file(mongodb_type, "default")
            default_sat.put(
                local_path='custom-hiera.yaml',
                remote_path='/etc/foreman-installer/custom-hiera.yaml',
            )
            command_output = default_sat.execute(
                'satellite-installer -s --disable-system-checks', timeout=1000000
            )
            assert 'Success!' in command_output.stdout
            raise

    @post_upgrade(depend_on=test_pre_performance_tuning_apply)
    def test_post_performance_tuning_apply(self, default_sat):
        """In postupgrade scenario, we verify the set tuning parameters and custom-hiera.yaml
        file's content.

        :id: postupgrade-31e26b08-2157-11ea-9223-001a4a1601d8

        :steps:
            1: Download the custom-hiera.yaml after upgrade from upgraded setup.
            2: Compare it with the medium tune custom-hiera file.
            3. Check the tune settings in scenario.yaml file, it should be set as
            "default" with updated medium tune parameters.
            4. Upload the default custom-hiera.yaml file on the upgrade setup.
            5. Run the satellite installer with "default" tune argument(satellite-installer
            --tuning default -s --disable-system-checks).
            6. If something gets wrong with the default tune parameters then we restore the
            default original tune parameter.

        :expectedresults: medium tune parameter should be unchanged after upgrade.

        """
        cmd = (
            'grep "mongodb::server::storage_engine: \'wiredTiger\'" '
            '/etc/foreman-installer/custom-hiera.yaml'
        )
        mongodb_type = default_sat.execute(cmd).status
        try:
            self._create_custom_hiera_file(mongodb_type, "medium")
            default_sat.get(
                local_path="custom-hiera-after-upgrade.yaml",
                remote_path="/etc/foreman-installer/custom-hiera.yaml",
            )
            assert filecmp.cmp('custom-hiera.yaml', 'custom-hiera-after-upgrade.yaml')

            cmd = 'grep "tuning: default" /etc/foreman-installer/scenarios.d/satellite.yaml'
            assert default_sat.execute(cmd).status == 0

            expected_tune_size, actual_tune_size = self._data_creation_of_set_tune_params(
                MEDIUM_TUNING_DATA,
                TUNE_DATA_COLLECTION_REGEX,
                MEDIUM_TUNE_PARAM_GROUPS,
                default_sat,
            )

            assert actual_tune_size == expected_tune_size

            self._create_custom_hiera_file(mongodb_type)
            default_sat.put(
                local_path='custom-hiera.yaml',
                remote_path='/etc/foreman-installer/custom-hiera.yaml',
            )
            command_output = default_sat.execute(
                'satellite-installer --tuning default -s --disable-system-checks',
                timeout=1000000,
            )
            assert 'Success!' in command_output.stdout
        finally:
            self._create_custom_hiera_file(mongodb_type)
            default_sat.put(
                local_path='custom-hiera.yaml',
                remote_path='/etc/foreman-installer/custom-hiera.yaml',
            )
            os.remove("custom-hiera.yaml")
            command_output = default_sat.execute(
                'satellite-installer -s --disable-system-checks', timeout=1000000
            )
            assert 'Success!' in command_output.stdout
