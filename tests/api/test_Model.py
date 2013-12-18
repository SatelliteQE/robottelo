#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data
from ddt import ddt
from lib.api.models import ModelApi
from tests.api.baseapi import BaseAPI
from tests.api.positive_crud_tests import PositiveCrudTestMixin

class Model(PositiveCrudTestMixin,BaseAPI):
    """Testing /api/models entrypoint"""

    def tested_class(self):
        return ModelApi

    def post_result(self):
        return 201


