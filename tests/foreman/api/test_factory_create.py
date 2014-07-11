# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai


from ddt import ddt
from robottelo.common.decorators import data
from robottelo.test import APITestCase
from robottelo.factory import FactoryError
from robottelo.entities import (
    ActivationKey,
    Architecture,
    ContentView,
    LifecycleEnvironment,
    Location,
    Model,
    OperatingSystem,
    Organization,
    Product,
    User
    )


@ddt
class TestFactoryCreate(APITestCase):
    """Testing basic positive permissions"""

    @data(
        ActivationKey, Architecture, ContentView,
        LifecycleEnvironment, Location, Model,
        OperatingSystem, Organization, Product, User)
    def test_basic_create(self, test_data):
        """
        @feature: Permissions
        @test: try to create entity with the factory
        @assert: entity is created
        """
        factory = test_data()
        try:
            factory.create()
        except FactoryError as factory_error:
            self.fail(factory_error)

