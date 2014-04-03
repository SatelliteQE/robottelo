# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data, ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.common.decorators import redminebug
from robottelo.records.activation_key import ActivationKey
from robottelo.records.system_group import SystemGroupDefOrg
from tests.foreman.api.baseapi import BaseAPI


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

    @data(*ActivationKey.enumerate())
    def test_sysgroup(self, test_data):
        """
        @feature: ActivationKey
        @test: Verify, that you can add systemgroups
        @assert: there was no system group and you have added one
        """
        acc = ApiCrud.record_create(test_data)
        self.assertEqual(len(acc.system_groups), 0)
        sg = SystemGroupDefOrg()
        sgc = ApiCrud.record_create(sg)
        r = acc._meta.api_class.add_sysgroups(acc, [sgc.id])
        self.assertTrue(r.ok)
        acr = ApiCrud.record_resolve(acc)
        self.assertEqual(len(acr.system_groups), 1)
