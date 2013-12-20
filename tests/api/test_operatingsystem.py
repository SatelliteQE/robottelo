# -*- encoding: utf-8 -*-

from robottelo.api.operating_systems import OperatingSystemApi
from tests.api.baseapi import BaseAPI
from tests.api.positive_crud_tests import PositiveCrudTestMixin


class OperatingSystem(BaseAPI, PositiveCrudTestMixin):
    """Testing /api/operatingsystems entrypoint"""

    def tested_class(self):
        return OperatingSystemApi
