# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data, ddt
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import redminebug
from robottelo.api.apicrud import ApiCrud
from tests.api.baseapi import BaseAPI


@ddt
class Organization(BaseAPI):
    """Testing /api/organization entrypoint"""

    # Positive Create

    @data("""DATADRIVENGOESHERE
        name is alpha, label and description are blank
        name is numeric, label and description are blank
        name is alphanumeric, label and description are blank
        name is utf-8, label and description are blank
        name is latin1, label and description are blank
        name is html, label and description are blank
        """)
    def test_positive_create_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name only
        @assert: organization is created, label is auto-generated
        @status: manual
        """
        ApiCrud.record_create(test_data)

    @data("""DATADRIVENGOESHERE
        name and label are alpha and match, description is blank
        name and label are numeric and match, description is blank
        name and label are alphanumeric and match, description is blank
        name and label are utf-8 and match, description is blank
        name and label are latin1 and match, description is blank
        name and label are html and match, description is blank
        """)
    def test_positive_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid matching name and label only
        @assert: organization is created, label matches name
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name and label are alpha, description is blank
        name and label are numeric, description is blank
        name and label are alphanumeric, description is blank
        name and label are utf-8, description is blank
        name and label are latin1, description is blank
        name and label are html, description is blank
        """)
    def test_positive_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid unmatching name and label only
        @assert: organization is created, label does not match name
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name and description are alpha, label is blank
        name and description are numeric, label is blank
        name and description are alphanumeric, label is blank
        name and description are utf-8, label is blank
        name and description are latin1, label is blank
        name and description are html, label is blank
        """)
    def test_positive_create_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name and description only
        @assert: organization is created, label is auto-generated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are alpha, name and label match
        name, label and description are numeric, name and label match
        name, label and description are alphanumeric, name and label match
        name, label and description are utf-8, name and label match
        name, label and description are latin1, name and label match
        name, label and description are html, name and label match
        """)
    def test_positive_create_5(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name, label and description
        @assert: organization is created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

        #Negative Create

    @data("""DATADRIVENGOESHERE
        label and description are alpha, update name is alpha 300 chars
        label and description are alpha, update name is numeric 300 chars
        label and description are alpha, update name is alphanumeric 300 chars
        label and description are alpha, update name is utf-8 300 chars
        label and description are alpha, update name is latin1 300 chars
        label and description are alpha, update name is html 300 chars

    """)
    def test_negative_create_0(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        too long
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        label and description are alpha, name is blank
        label and description are numeric, name is blank
        label and description are alphanumeric, name is blank
        label and description are utf-8, name is blank
        label and description are latin1, name is blank
        label and description are html, name is blank
    """)
    def test_negative_create_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        blank
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        label and description are alpha, name is whitespace
        label and description are numeric, name is whitespace
        label and description are alphanumeric, name is whitespace
        label and description are utf-8, name is whitespace
        label and description are latin1, name is whitespace
        label and description are html, name is whitespace
    """)
    def test_negative_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        whitespace
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are alpha
        name, label and description are numeric
        name, label and description are alphanumeric
        name, label and description are utf-8
        name, label and description are latin1
        name, label and description are html
    """)
    def test_negative_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values, then create a new one
        with same values.
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Positive Delete

    @data("""DATADRIVENGOESHERE
        name, label and description are alpha
        name, label and description are numeric
        name, label and description are alphanumeric
        name, label and description are utf-8
        name, label and description are latin1
        name, label and description are html
    """)
    def test_positive_delete_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then delete it
        @assert: organization is deleted
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Negative Delete

    # Positive Update

    @data("""DATADRIVENGOESHERE
        update name is alpha
        update name is numeric
        update name is alphanumeric
        update name is utf-8
        update name is latin1
        update name is html
    """)
    def test_positive_update_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its name
        @assert: organization name is updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update label is alpha
        update label is numeric
        update label is alphanumeric
        update label is utf-8
        update label is latin1
        update label is html
    """)
    def test_positive_update_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its label
        @assert: organization label is updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update description is alpha
        update description is numeric
        update description is alphanumeric
        update description is utf-8
        update description is latin1
        update description is html
    """)
    def test_positive_update_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its
        description
        @assert: organization description is updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update name, label and description are alpha
        update name, label and description are numeric
        update name, label and description are alphanumeric
        update name, label and description are utf-8
        update name, label and description are latin1
        update name, label and description are html
    """)
    def test_positive_update_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update all values
        @assert: organization name, label and description are updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Negative Update

    @data("""DATADRIVENGOESHERE
        update name is whitespace
        update name is alpha 300 chars long
        update name is numeric 300 chars long
        update name is alphanumeric 300 chars long
        update name is utf-8 300 chars long
        update name is latin1 300 chars long
        update name is html 300 chars long
    """)
    def test_negative_update_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its name
        @assert: organization name is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update label is whitespace
        update label is alpha 300 chars long
        update label is numeric 300 chars long
        update label is alphanumeric 300 chars long
        update label is utf-8 300 chars long
        update label is latin1 300 chars long
        update label is html 300 chars long
    """)
    def test_negative_update_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its label
        @assert: organization label is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update description is alpha 300 chars long
        update description is numeric 300 chars long
        update description is alphanumeric 300 chars long
        update description is utf-8 300 chars long
        update description is latin1 300 chars long
        update description is html 300 chars long
    """)
    def test_negative_update_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its description
        @assert: organization description is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    #Miscelaneous

    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_list_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization and list it
        @assert: organization is displayed/listed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_search_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization and search/find it
        @assert: organization can be found
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_info_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create single organization and get its info
        @assert: specific information for organization matches the
        creation values
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

