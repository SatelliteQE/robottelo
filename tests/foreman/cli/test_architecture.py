# -*- encoding: utf-8 -*-
"""Test class for Architecture CLI"""

from robottelo.cli.architecture import Architecture
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_architecture
from robottelo.decorators import run_only_on
from robottelo.helpers import invalid_values_list, valid_data_list
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestArchitecture(MetaCLITestCase):
    """Architecture CLI related tests. """

    factory = make_architecture
    factory_obj = Architecture

    def test_negative_update(self):
        """@test: Create architecture then fail to update
        its name

        @feature: Architecture

        @assert: architecture name is not updated

        """
        arch = make_architecture()
        # Update the architecture name
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    Architecture.update({
                        'id': arch['id'],
                        'new-name': new_name,
                    })

    def test_positive_delete(self):
        """@test: Create architecture with valid values then delete it
        by ID

        @feature: Architecture

        @assert: architecture is deleted

        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = make_architecture({'name': name})
                Architecture.delete({'id': arch['id']})
                # Can we find the object?
                with self.assertRaises(CLIReturnCodeError):
                    Architecture.info({'id': arch['id']})
