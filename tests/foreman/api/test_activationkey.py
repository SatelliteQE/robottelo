# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.common.decorators import data, skip_if_bug_open, stubbed
from robottelo.records.activation_key import ActivationKey
from robottelo.test import APITestCase


@ddt
class ActivationKeys(APITestCase):
    """Testing /katello/ap/v2/activation_keys entrypoint"""

    # Positive Create

    @skip_if_bug_open('redmine', 4793)
    @data(*ActivationKey.enumerate())
    def test_positive_create_1(self, test_data):
        """
        @feature: ActivationKey
        @test: Try creating activation keys with valid name/label/desc
        @assert: ActivationKeyis created, sent and recieved data intersects
        """
        result = ApiCrud.record_create(test_data)
        self.assertIntersects(test_data, result)

    @skip_if_bug_open('redmine', 4793)
    @data(*ActivationKey.enumerate())
    def test_update(self, test_data):
        """
        @feature: ActivationKey
        @test: Verify, that update funkcionality works as intended
        @assert: different description is created after update.
        """
        update_desc = test_data.description
        test_data.description = "empty"
        ak_cr = ApiCrud.record_create(test_data)
        self.assertIntersects(ak_cr, test_data)
        ak_cr.description = update_desc
        ak_u = ApiCrud.record_update(ak_cr)
        self.assertEquals(ak_u.description, ak_cr.description)

    @stubbed
    @data(*ActivationKey.enumerate())
    def test_host_collections(self, test_data):
        """
        @test: Verify, that you can add host collections
        @feature: ActivationKey
        @assert: there was no system group and you have added one
        """
        # See method test_set_host_collection in file test_activationkey_v2.py
