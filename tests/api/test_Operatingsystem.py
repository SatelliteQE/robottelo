#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from ddt import data
from ddt import ddt
from lib.api.operating_systems import OperatingSystemApi
from tests.api.baseapi import BaseAPI
from tests.api.positive_crud_tests import PositiveCrudTestMixin

class OperatingSystem(PositiveCrudTestMixin,BaseAPI):
    """Testing /api/operatingsystems entrypoint"""

    def tested_class(self):
        return OperatingSystemApi


