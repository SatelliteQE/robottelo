# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data, ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.records.repository import CustomRepository
from tests.foreman.api.baseapi import BaseAPI


@ddt
class Products(BaseAPI):
    """Testing /katello/ap/v2/activation_keys entrypoint"""

    # Positive Create

    @data(*CustomRepository.enumerate())
    def test_positive_create_1(self, test_data):
        """
        @feature: CustomYumRepo
        @test: Try creating custom repository with valid name/desc
        @assert: Product iscreated, sent and recieved data intersects
        """
        result = ApiCrud.record_create_recursive(test_data)
        self.assertIntersects(test_data, result)
