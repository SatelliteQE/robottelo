# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import ddt
from robottelo.api.apicrud import ApiCrud
from robottelo.common.decorators import data, skip_if_rm_bug_open
from robottelo.records.user import User
from tests.foreman.api.baseapi import APITestCase


@ddt
class TestUser(APITestCase):
    """Testing /api/organization entrypoint"""

    @data(*User.enumerate())
    def test_add_user_1(self, test_data):
        """
        @feature: Organizations
        @test: Create different types of users then add user
        by using the organization ID
        @assert: User is added to organization
        @status: manual
        """

        ApiCrud.record_create_recursive(test_data)

    @data(*User.enumerate(admin=True))
    def test_add_user_2(self, test_data):
        """
        @feature: Organizations
        @test: Create admin users then add user by using the organization name
        @assert: User is added to organization
        @status: manual
        """

        ApiCrud.record_create_recursive(test_data)

    @skip_if_rm_bug_open('4294')
    @skip_if_rm_bug_open('4295')
    @skip_if_rm_bug_open('4296')
    @data(*User.enumerate())
    def test_remove_user_1(self, test_data):
        """
        @feature: Organizations
        @test: Create different types of users then add/remove user
        by using the organization ID
        @assert: User is added and then removed from organization
        @status: manual
        """

        u = ApiCrud.record_create_recursive(test_data)
        self.assertTrue("organizations" in u)
        u.organization_ids = []
        ur = ApiCrud.record_update(u)
        self.assertFalse("organizations" in ur)

    @skip_if_rm_bug_open('4294')
    @skip_if_rm_bug_open('4295')
    @skip_if_rm_bug_open('4296')
    @data(*User.enumerate(admin=True))
    def test_remove_user_3(self, test_data):
        """
        @feature: Organizations
        @test: Create admin users then add user and remove it
        by using the organization name
        @assert: The user is added then removed from the organization
        @status: manual
        """
        u = ApiCrud.record_create_recursive(test_data)
        self.assertTrue("organizations" in u)
        u.organization_ids = []
        ur = ApiCrud.record_update(u)
        self.assertFalse("organizations" in ur)
