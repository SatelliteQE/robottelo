"""Unit tests for the ``architectures`` paths.

:Requirement: Architecture

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import APITestCase


class ArchitectureTestCase(APITestCase):
    """Tests for architectures."""

    @tier2
    def test_positive_add_os(self):
        """Create an architecture and associate it with an OS.

        :id: 9943063d-34f3-4dbc-a341-474ec781e4d9

        :expectedresults: The architecture can be created, and the association
            can be read back from the server.

        :CaseLevel: Integration
        """
        operating_sys = entities.OperatingSystem().create()
        arch = entities.Architecture(operatingsystem=[operating_sys]).create()
        self.assertEqual({operating_sys.id}, {os.id for os in arch.operatingsystem})

    @tier1
    def test_positive_create_with_name(self):
        """Create an architecture providing the initial name.

        :id: acbadcda-3410-45cb-a3aa-932a0facadc1

        :expectedresults: Architecture is created and contains provided name.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                self.assertEqual(name, arch.name)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create architecture providing an invalid initial name.
        set.

        :id: c740b8c4-8ee3-4481-b041-4eff2faf9055

        :expectedresults: Architecture is not created

        :CaseImportance: Medium

        :BZ: 1401519
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Architecture(name=name).create()

    @tier1
    def test_positive_update_name(self):
        """Create architecture then update its name to another
        valid name.

        :id: 8dbbf4f8-188e-406a-9099-a707f553d6bb

        :expectedresults: Architecture is created, and its name can be updated.

        :CaseImportance: Critical
        """
        arch = entities.Architecture().create()

        for new_name in valid_data_list():
            with self.subTest(new_name):
                entities.Architecture(id=arch.id, name=new_name).update(['name'])
                updated = entities.Architecture(id=arch.id).read()
                self.assertEqual(new_name, updated.name)

    @tier1
    def test_negative_update_name(self):
        """Create architecture then update its name to an invalid name.

        :id: 301b335e-9bc1-47d9-8bef-a8ca2e9ea18e

        :expectedresults: Architecture is created, and its name is not updated.

        :CaseImportance: Medium
        """
        arch = entities.Architecture().create()
        for new_name in invalid_names_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.Architecture(id=arch.id, name=new_name).update(['name'])
                arch = entities.Architecture(id=arch.id).read()
                self.assertNotEqual(arch.name, new_name)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create architecture and then delete it.

        :id: 114a2973-a889-4a5e-bfac-de4406826258

        :expectedresults: architecture is successfully deleted.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                arch = entities.Architecture(name=name).create()
                arch.delete()
                with self.assertRaises(HTTPError):
                    entities.Architecture(id=arch.id).read()
