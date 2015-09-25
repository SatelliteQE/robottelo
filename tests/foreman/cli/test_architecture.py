# -*- encoding: utf-8 -*-
"""Test class for Architecture CLI"""

from robottelo.cli.architecture import Architecture
from robottelo.cli.factory import make_architecture, CLIFactoryError
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
        try:
            new_obj = make_architecture()
        except CLIFactoryError as err:
            self.fail(err)
        for data in invalid_values_list():
            with self.subTest(data):
                # Update the architecture name
                result = Architecture.update({
                    'id': new_obj['id'],
                    'new-name': data,
                })
                self.assertNotEqual(result.return_code, 0)
                self.assertGreater(len(result.stderr), 0)

    def test_positive_delete(self):
        """@test: Create architecture with valid values then delete it
        by ID

        @feature: Architecture

        @assert: architecture is deleted

        """
        for data in valid_data_list():
            with self.subTest(data):
                try:
                    new_obj = make_architecture({'name': data})
                except CLIFactoryError as err:
                    self.fail(err)

                return_value = Architecture.delete({'id': new_obj['id']})
                self.assertEqual(return_value.return_code, 0)
                self.assertEqual(len(return_value.stderr), 0)

                # Can we find the object?
                result = Architecture.info({'id': new_obj['id']})
                self.assertNotEqual(result.return_code, 0)
                self.assertGreater(len(result.stderr), 0)
                self.assertEqual(len(result.stdout), 0)
