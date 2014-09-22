# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.common.decorators import data, run_only_on
from robottelo.records.repository import CustomRepository
from robottelo.test import APITestCase


@ddt
class Repository(APITestCase):
    """Testing /katello/ap/v2/repository entrypoint"""

    # Positive Create

    @run_only_on('sat')
    @data(*CustomRepository.enumerate())
    def test_positive_create_1(self, test_data):
        """
        @feature: CustomYumRepo
        @test: Try creating custom repository with valid name/desc
        @assert: Product iscreated, sent and recieved data intersects
        """
        result = ApiCrud.record_create_recursive(test_data)
        self.assertIntersects(test_data, result)

    @run_only_on('sat')
    @data(*CustomRepository.enumerate())
    def test_positive_remove_1(self, test_data):
        """
        @feature: CustomYumRepo
        @test: Try removing custom repository with valid name/desc
        @assert: Product iscreated, sent and recieved data intersects
        """
        result = ApiCrud.record_create_recursive(test_data)
        self.assertTrue(ApiCrud.record_exists(result))
        ApiCrud.record_remove(result)
        self.assertFalse(ApiCrud.record_exists(result))

    @run_only_on('sat')
    @data(*CustomRepository.enumerate())
    def test_positive_sync_1(self, test_data):
        """
        @feature: CustomYumRepo
        @test: Create and sync repo
        @assert: repo should have more than 0 packages
        """
        result = ApiCrud.record_create_recursive(test_data)
        self.assertEqual({}, result.content_counts)
        task = result._meta.api_class.synchronize(result)
        task.poll(5, 100)
        self.assertEqual('success', task.result())
        resolved = ApiCrud.record_resolve(result)
        self.assertGreater(resolved.content_counts['rpm'], 0)
