# -*- encoding: utf-8 -*-
"""Test class for GlobalParameters UI

:Requirement: GlobalParameters

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities

from robottelo.datafactory import valid_names_list
from robottelo.decorators import tier1, upgrade
from robottelo.ui.factory import make_global_parameter
from robottelo.test import UITestCase
from robottelo.ui.session import Session


def global_parameters_valid_names_list():
    """"Return valid names for Global Parameters"""
    # global parameters does not support names with spaces
    return [name.replace(' ', '_') for name in valid_names_list()]


class GlobalParametersTestCase(UITestCase):
    """Implements Global Parameters tests in UI"""

    @tier1
    def test_positive_create_with_name(self):
        """Create a new Global Parameter with different names

        :id: a0b8798b-2363-4534-970a-b6e1c13efa54

        :expectedresults: Global Parameter is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in global_parameters_valid_names_list():
                with self.subTest(name):
                    make_global_parameter(session, name=name)
                    self.assertIsNotNone(self.globalparameters.search(name))

    @tier1
    def test_positive_create_with_value(self):
        """Create a new Global Parameter with value

        :id: f64a67f5-5412-4d62-852c-e189bb969dc8

        :expectedresults: Global Parameter is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        value = gen_string('alpha')
        with Session(self) as session:
            make_global_parameter(session, name=name, value=value)
            self.assertIsNotNone(self.globalparameters.search(name))

    @tier1
    def test_positive_create_with_hidden_value(self):
        """Create a new Global Parameter with hidden value

        :id: 837ed2a6-a7af-4251-95a5-23d9fccaa2ff

        :expectedresults: Global Parameter is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_global_parameter(session, name=name, hidden_value=True)
            self.assertIsNotNone(self.globalparameters.search(name))

    @tier1
    def test_positive_update_name(self):
        """Create a Global Parameter with valid values then update its name

        :id: de17d5ad-2c1a-4a75-8a20-5e3cd9d08205

        :expectedresults: Global Parameter name is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_global_parameter(session, name=name)
            self.assertIsNotNone(self.globalparameters.search(name))
            for new_name in global_parameters_valid_names_list():
                with self.subTest(new_name):
                    self.globalparameters.update(name, new_name=new_name)
                    self.assertIsNotNone(
                        self.globalparameters.search(new_name))
                name = new_name

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create Global Parameter with valid values then delete it.

        :id: 1406d572-9e30-44e8-8637-2abe573e8958

        :expectedresults: Global Parameter is deleted

        :CaseImportance: Critical
        """
        with Session(self):
            for name in global_parameters_valid_names_list():
                with self.subTest(name):
                    entities.CommonParameter(name=name).create()
                    self.globalparameters.delete(name)
