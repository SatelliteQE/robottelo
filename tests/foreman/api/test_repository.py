# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data, ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.records.repository import CustomRepository
from tests.foreman.api.baseapi import BaseAPI


@ddt
class Repository(BaseAPI):
    """Testing /katello/ap/v2/repository entrypoint"""

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
