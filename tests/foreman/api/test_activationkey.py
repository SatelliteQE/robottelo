# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data, ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.common.decorators import redminebug
from robottelo.records.activation_key import ActivationKey
from tests.api.baseapi import BaseAPI


@ddt
class ActivationKeys(BaseAPI):
    """Testing /katello/ap/v2/activation_keys entrypoint"""

    # Positive Create

    @redminebug('4793')
    @data(*ActivationKey.enumerate())
    def test_positive_create_1(self, test_data):
        """
        @feature: ActivationKey
        @test: Try creating activation keys with valid name/label/desc
        @assert: ActivationKeyis created, sent and recieved data intersects
        """
        result = ApiCrud.record_create(test_data)
        self.assertIntersects(test_data, result)

    @redminebug('4793')
    @data(*ActivationKey.enumerate())
    def test_update(self, ak):
        """
        @feature: ActivationKey
        @test: Verify, that update funkcionality works as intended
        @assert: different description is created after update.
        """
        update_desc = ak.description
        ak.description = "empty"
        ak_cr = ApiCrud.record_create(ak)
        self.assertIntersects(ak_cr, ak)
        ak_cr.description = update_desc
        ak_u = ApiCrud.record_update(ak_cr)
        self.assertEquals(ak_u.description, ak_cr.description)
