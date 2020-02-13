# -*- encoding: utf-8 -*-
"""Test class for Architecture CLI

:Requirement: Architecture

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.cli.architecture import Architecture
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_architecture
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class ArchitectureTestCase(CLITestCase):
    """Architecture CLI related tests."""

    @tier1
    def test_positive_create_with_name(self):
        """Successfully creates an Architecture.

        :id: a3955346-cfc0-428d-8871-a10386fe7c59

        :expectedresults: Architecture is created.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                architecture = make_architecture({'name': name})
                self.assertEqual(architecture['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an Architecture with invalid data.

        :id: cfed972e-9b09-4852-bdd2-b5a8a8aed170

        :expectedresults: Architecture is not created.

        :CaseImportance: Medium
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError) as raise_ctx:
                    Architecture.create({'name': name})
                self.assert_error_msg(raise_ctx,
                                      u'Could not create the architecture:')

    @tier1
    def test_positive_update_name(self):
        """Successfully update an Architecture.

        :id: 67f1e60b-29e2-44a4-8019-498e5ad0e201

        :expectedresults: Architecture is updated.

        :CaseImportance: Critical
        """
        architecture = make_architecture()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                Architecture.update({
                    'id': architecture['id'],
                    'new-name': new_name,
                })
                architecture = Architecture.info({'id': architecture['id']})
                self.assertEqual(architecture['name'], new_name)

    @tier1
    def test_negative_update_name(self):
        """Create Architecture then fail to update its name

        :id: 037c4892-5e62-46dd-a2ed-92243e870e40

        :expectedresults: Architecture name is not updated

        :CaseImportance: Medium
        """
        architecture = make_architecture()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError) as raise_ctx:
                    Architecture.update({
                        'id': architecture['id'],
                        'new-name': new_name,
                    })
                self.assert_error_msg(raise_ctx,
                                      u'Could not update the architecture:')
                result = Architecture.info({'id': architecture['id']})
                self.assertEqual(architecture['name'], result['name'])

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Create Architecture with valid values then delete it
        by ID

        :id: df699e29-29a3-417a-a6ee-81e74b7211a4

        :expectedresults: Architecture is deleted

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                architecture = make_architecture({'name': name})
                Architecture.delete({'id': architecture['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Architecture.info({'id': architecture['id']})

    @tier1
    def test_negative_delete_by_id(self):
        """Create Architecture then delete it by wrong ID

        :id: 78bae664-6493-4c74-a587-94170f20746e

        :expectedresults: Architecture is not deleted

        :CaseImportance: Medium
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError) as raise_ctx:
                    Architecture.delete({'id': entity_id})
                self.assert_error_msg(raise_ctx,
                                      "Could not delete the architecture")
