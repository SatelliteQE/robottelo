#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data
from ddt import ddt
from robottelo.api.users import UserApi
from tests.api.baseapi import BaseAPI
from tests.api.positive_crud_tests import PositiveCrudTestMixin


@ddt
class User(BaseAPI, PositiveCrudTestMixin):
    """Testing /api/user entrypoint"""

    def tested_class(self):
        return UserApi

    @data(
        ("login", {u'login': [u"can't be blank"]}),
        ("password", {u'password_hash': [u"can't be blank"]}),
    )
    def test_create_user_negative(self, data_tuple):
        """Try to create a new user with missing params"""
        param, result = data_tuple

        user = UserApi(generate=True)
        user = user.graylist(**{param: False})
        response = UserApi.create(json=user.opts())
        self.assertEqual(response.status_code, 422)
        self.assertFeaturing({u'user': {u'errors': result}}, response.json())
