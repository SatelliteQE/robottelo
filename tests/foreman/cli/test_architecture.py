# -*- encoding: utf-8 -*-
"""Test class for Architecture CLI"""

from fauxfactory import gen_string
from robottelo.cli.architecture import Architecture
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_architecture
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
    def test_negative_update(self, new_name):
        """@test: Create architecture then fail to update
        its name

        @feature: Architecture

        @assert: architecture name is not updated

        """
        arch = make_architecture()
        # Update the architecture name
        with self.assertRaises(CLIReturnCodeError):
            Architecture.update({
                'id': arch['id'],
                'new-name': new_name,
            })

    @data(
        gen_string("latin1", 10),
        gen_string("utf8", 10),
        gen_string("alpha", 10),
        gen_string("alphanumeric", 10),
        gen_string("numeric", 10),
        gen_string("html", 10))
    def test_positive_delete(self, name):
        """@test: Create architecture with valid values then delete it
        by ID

        @feature: Architecture

        @assert: architecture is deleted

        """
        arch = make_architecture({'name': name})
        Architecture.delete({'id': arch['id']})
        # Can we find the object?
        with self.assertRaises(CLIReturnCodeError):
            Architecture.info({'id': arch['id']})
