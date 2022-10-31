"""Tests for module ``robottelo.utils.datafactory``."""
import itertools
import random
from unittest import mock

import pytest

from robottelo.config import settings
from robottelo.constants import STRING_TYPES
from robottelo.utils import datafactory


class TestFilteredDataPoint:
    """Tests for :meth:`robottelo.utils.datafactory.filtered_datapoint` decorator"""

    @pytest.fixture(scope="function")
    def run_one_datapoint(self, request):
        # Modify run_one_datapoint on settings singleton based on the indirect param
        # default to false when not parametrized
        original = settings.robottelo.run_one_datapoint
        settings.robottelo.run_one_datapoint = getattr(request, 'param', False)
        yield settings.robottelo.run_one_datapoint
        settings.robottelo.run_one_datapoint = original

    @pytest.mark.parametrize('run_one_datapoint', [True, False], indirect=True)
    def test_filtered_datapoint(self, run_one_datapoint):
        """Tests if run_one_datapoint=false returns all data points"""
        if run_one_datapoint:
            assert len(datafactory.generate_strings_list()) == 1
            assert len(datafactory.invalid_emails_list()) == 1
            assert len(datafactory.invalid_environments_list()) == 1
            assert len(datafactory.invalid_id_list()) == 1
            assert len(datafactory.invalid_interfaces_list()) == 1
            assert len(datafactory.invalid_names_list()) == 1
            assert len(datafactory.invalid_values_list()) == 1
            assert len(datafactory.valid_data_list()) == 1
            assert len(datafactory.valid_docker_repository_names()) == 1
            assert len(datafactory.valid_emails_list()) == 1
            assert len(datafactory.valid_environments_list()) == 1
            assert len(datafactory.valid_hosts_list()) == 1
            assert len(datafactory.valid_hostgroups_list()) == 1
            assert len(datafactory.valid_interfaces_list()) == 1
            assert len(datafactory.valid_labels_list()) == 1
            assert len(datafactory.valid_names_list()) == 1
            assert len(datafactory.valid_org_names_list()) == 1
            assert len(datafactory.valid_usernames_list()) == 1
            assert len(datafactory.valid_cron_expressions()) == 1
        else:
            assert len(datafactory.generate_strings_list()) == 7
            assert len(datafactory.invalid_emails_list()) == 8
            assert len(datafactory.invalid_environments_list()) == 4
            assert len(datafactory.invalid_id_list()) == 4
            assert len(datafactory.invalid_interfaces_list()) == 8
            assert len(datafactory.invalid_names_list()) == 7
            assert len(datafactory.invalid_values_list()) == 10
            assert len(datafactory.invalid_usernames_list()) == 4
            assert len(datafactory.valid_labels_list()) == 2
            assert len(datafactory.valid_data_list()) == 7
            assert len(datafactory.valid_emails_list()) == 8
            assert len(datafactory.valid_environments_list()) == 4
            assert len(datafactory.valid_hosts_list()) == 3
            assert len(datafactory.valid_hostgroups_list()) == 7
            assert len(datafactory.valid_interfaces_list()) == 3
            assert len(datafactory.valid_names_list()) == 15
            assert len(datafactory.valid_org_names_list()) == 7
            assert len(datafactory.valid_usernames_list()) == 6
            assert len(datafactory.valid_cron_expressions()) == 4
            assert len(datafactory.valid_docker_repository_names()) == 7

    @mock.patch('robottelo.utils.datafactory.gen_string')
    def test_generate_strings_list_remove_str(self, gen_string, run_one_datapoint):
        gen_string.side_effect = lambda str_type, _: str_type
        str_types = STRING_TYPES[:]
        remove_type = random.choice(str_types)
        str_types.remove(remove_type)
        str_types.sort()
        string_list = datafactory.generate_strings_list(exclude_types=[remove_type])
        string_list.sort()
        assert string_list == str_types


class TestReturnTypes:
    """Tests for validating return types for different data factory
    functions."""

    def test_return_type(self):
        """This test validates return types for functions:

        1. :meth:`robottelo.utils.datafactory.generate_strings_list`
        2. :meth:`robottelo.utils.datafactory.invalid_emails_list`
        3. :meth:`robottelo.utils.datafactory.invalid_environments_list`
        4. :meth:`robottelo.utils.datafactory.invalid_names_list`
        5. :meth:`robottelo.utils.datafactory.valid_data_list`
        6. :meth:`robottelo.utils.datafactory.valid_docker_repository_names`
        7. :meth:`robottelo.utils.datafactory.valid_emails_list`
        8. :meth:`robottelo.utils.datafactory.valid_environments_list`
        9. :meth:`robottelo.utils.datafactory.valid_hosts_list`
        10. :meth:`robottelo.utils.datafactory.valid_hostgroups_list`
        11. :meth:`robottelo.utils.datafactory.valid_labels_list`
        12. :meth:`robottelo.utils.datafactory.valid_names_list`
        13. :meth:`robottelo.utils.datafactory.valid_org_names_list`
        14. :meth:`robottelo.utils.datafactory.valid_usernames_list`
        15. :meth:`robottelo.utils.datafactory.invalid_id_list`
        16. :meth:`robottelo.utils.datafactory.invalid_interfaces_list`
        17. :meth:`robottelo.utils.datafactory.valid_interfaces_list`
        18. :meth:`robottelo.utils.datafactory.valid_cron_expressions`

        """
        for item in itertools.chain(
            datafactory.generate_strings_list(),
            datafactory.invalid_emails_list(),
            datafactory.invalid_environments_list(),
            datafactory.invalid_interfaces_list(),
            datafactory.invalid_names_list(),
            datafactory.valid_data_list(),
            datafactory.valid_docker_repository_names(),
            datafactory.valid_emails_list(),
            datafactory.valid_environments_list(),
            datafactory.valid_hosts_list(),
            datafactory.valid_hostgroups_list(),
            datafactory.valid_interfaces_list(),
            datafactory.valid_labels_list(),
            datafactory.valid_names_list(),
            datafactory.valid_org_names_list(),
            datafactory.valid_cron_expressions(),
            datafactory.valid_usernames_list(),
        ):
            assert isinstance(item, str)
        for item in datafactory.invalid_id_list():
            if not (isinstance(item, (str, int)) or item is None):
                pytest.fail('Unexpected data type')


class TestInvalidValuesList:
    """Tests for :meth:`robottelo.datafactory.invalid_values_list`"""

    def test_return_values(self):
        """Tests if invalid values list returns right values based on input"""
        # Test valid values
        for value in 'api', 'cli', 'ui', None:
            return_value = datafactory.invalid_values_list(value)
            assert isinstance(return_value, list)
            if value == 'ui':
                assert len(return_value) == 9
            else:
                assert len(return_value) == 10

            # test uppercase values, which are invalid
            with pytest.raises(datafactory.InvalidArgumentError):
                datafactory.invalid_values_list(value.upper() if isinstance(value, str) else ' ')

        # Test invalid value
        with pytest.raises(datafactory.InvalidArgumentError):
            datafactory.invalid_values_list('invalid')
