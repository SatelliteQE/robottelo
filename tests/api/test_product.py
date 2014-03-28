# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data, ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.records.product import CustomProduct
from tests.api.baseapi import BaseAPI


@ddt
class Products(BaseAPI):
    """Testing /katello/ap/v2/activation_keys entrypoint"""

    # Positive Create

    @data(*CustomProduct.enumerate())
    def test_positive_create_1(self, test_data):
        """
        @feature: CustomProduct
        @test: Try creating custom product with valid name/desc
        @assert: Product iscreated, sent and recieved data intersects
        """
        result = ApiCrud.record_create_recursive(test_data)
        self.assertIntersects(test_data, result)

    @data(*CustomProduct.enumerate())
    def test_update(self, test_data):
        """
        @feature: CustomProduct
        @test: Verify, that update funkcionality works as intended
        @assert: different description is created after update.
        """
        update_desc = test_data.description
        test_data.description = "empty"
        ak_cr = ApiCrud.record_create_recursive(test_data)
        self.assertIntersects(ak_cr, test_data)
        ak_cr.description = update_desc
        ak_u = ApiCrud.record_update(ak_cr)
        self.assertEquals(ak_u.description, ak_cr.description)

    @data(*CustomProduct.enumerate())
    def test_positive_remove_1(self, test_data):
        """
        @feature: CustomProduct
        @test: Try creating custom repository with valid name/desc
        @assert: Product iscreated, sent and recieved data intersects
        """
        result = ApiCrud.record_create_recursive(test_data)
        self.assertTrue(ApiCrud.record_exists(result))
        ApiCrud.record_remove(result)
        self.assertFalse(ApiCrud.record_exists(result))
