# -*- encoding: utf-8 -*-
"""Test class for Architecture CLI"""

from fauxfactory import gen_string
from robottelo.cli.architecture import Architecture
from robottelo.cli.factory import make_architecture, CLIFactoryError
from robottelo.decorators import data
from robottelo.decorators import run_only_on
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestArchitecture(MetaCLITestCase):
    """Architecture CLI related tests. """

    factory = make_architecture
    factory_obj = Architecture

    @data(
        ' ',
        gen_string('alpha', 300),
        gen_string('numeric', 300),
        gen_string('alphanumeric', 300),
        gen_string('utf8', 300),
        gen_string('latin1', 300),
        gen_string('html', 300))
    def test_negative_update(self, data):
        """@test: Create architecture then fail to update
        its name

        @feature: Architecture

        @assert: architecture name is not updated

        """
        try:
            new_obj = make_architecture()
        except CLIFactoryError as err:
            self.fail(err)

        # Update the architecture name
        result = Architecture.update({
            'id': new_obj['id'],
            'new-name': data,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @data(
        gen_string("latin1", 10),
        gen_string("utf8", 10),
        gen_string("alpha", 10),
        gen_string("alphanumeric", 10),
        gen_string("numeric", 10),
        gen_string("html", 10))
    def test_positive_delete(self, data):
        """@test: Create architecture with valid values then delete it
        by ID

        @feature: Architecture

        @assert: architecture is deleted

        """
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
