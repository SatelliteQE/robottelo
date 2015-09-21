"""Unit tests for sample json settings"""
import json
import os

from unittest2 import TestCase

JSON_INVALID_ITEMS = ['hostname ', ' scheme', 'None', '']
JSON_SAMPLE_CONFIG = 'settings.json.sample'
JSON_VALID_KEYS = ['server', 'ldap', 'robottelo', 'tests', 'manifest',
                   'clients', 'docker', 'foreman', 'insights', 'transitions',
                   'performance']
JSON_VALID_VALUES = ['hostname', 'scheme', 'port', 'ssh_key',
                     'ssh_username', 'ldaphost', 'ldapuser', 'ldappwd',
                     'basedn', 'grpbasedn', 'project', 'locale', 'remote',
                     'smoke', 'upstream', 'verbosity', 'screenshots.base_path',
                     'virtual_display', 'window_manager_command', 'manifests',
                     'provisioning', 'fake_url', 'key_url', 'cert_url',
                     'provisioning_server', 'image_dir', 'rhel6_repo',
                     'rhel7_repo', 'external_url', 'admin.username',
                     'admin.password', 'insights_el6repo', 'insights_el7repo',
                     'export_tar.url', 'test.foreman.perf', 'test.cdn.address',
                     'test.virtual_machines_list',
                     'test.savepoint1_fresh_install',
                     'test.savepoint2_enabled_repos', 'csv.num_buckets',
                     'test.target_repos', 'test.num_syncs', 'test.sync_type']


class SettingsTestCase(TestCase):
    """Unit tests for sample json settings"""
    @classmethod
    def get_app_root(cls):
        """Returns the path of the application's root directory.

        :return: A directory path.
        :rtype: str

        """
        return os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            os.pardir
        ))

    @classmethod
    def setUpClass(cls):
        config_path = os.path.join(cls.get_app_root(), JSON_SAMPLE_CONFIG)
        with open(config_path) as json_data_file:
            cls.json_data = json.load(json_data_file)

    @classmethod
    def search_recursive_dict(cls, dataset, item):
        """Recursively checks for the presence of an item in the nested
        dictionary

        :dataset: input dataset - dictionary
        :item: the item to search in the dataset
        :rtype: boolean

        """
        return_value = False
        if not return_value:
            for key, value in dataset.iteritems():
                if return_value:
                    break
                if key == item:
                    return_value = True
                elif isinstance(value, dict):
                    return_value = cls.search_recursive_dict(value, item)
        return return_value

    def test_valid_json_settings(self):
        """Test for valid json settings attributes"""
        for key in JSON_VALID_KEYS + JSON_VALID_VALUES:
            self.assertTrue(self.search_recursive_dict(self.json_data, key),
                            '{0} is not found in the config'.format(key))

    def test_invalid_json_settings(self):
        """Test for invalid json settings attributes"""
        for key in JSON_INVALID_ITEMS:
            self.assertFalse(self.search_recursive_dict(self.json_data, key),
                             '{0} is found in the config'.format(key))
