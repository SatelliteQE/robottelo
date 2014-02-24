# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data, ddt
from robottelo.api.apicrud import ApiCrud
from tests.api.baseapi import BaseAPI
from robottelo.records.organization import Organization


@ddt
class Organization(BaseAPI):
    """Testing /api/organization entrypoint"""

    # Positive Create

    @data(*Organization.enumerate(label="", description=""))
    def test_positive_create_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name only
        @assert: organization is created, label is auto-generated
        """
        ApiCrud.record_create(test_data)

    @data(*Organization.enumerate(name="", description=""))
    def test_positive_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid matching name and label only
        @assert: organization is created, label matches name
        """
        test_data.name = test_data.label
        result = ApiCrud.record_create(test_data)
        self.assertEquals(result.name, result.label)

    @data(*Organization.enumerate(description=""))
    def test_positive_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid unmatching name and label only
        @assert: organization is created, label does not match name
        """
        result = ApiCrud.record_create(test_data)
        self.assertNotEqual (result.name, result.label)

    @data(*Organization.enumerate(label=""))
    def test_positive_create_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name and description only
        @assert: organization is created, label is auto-generated
        """

        ApiCrud.record_create(test_data)

    @data(*Organization.enumerate())
    def test_positive_create_5(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name, label and description
        @assert: organization is created
        """
        ApiCrud.record_create(test_data)
