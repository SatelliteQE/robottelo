#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from robottelo.lib.common.helpers import generate_name
from robottelo.lib.ui.locators import locators


class Product(BaseUI):

    def products_page(self, org_name='ACME_Corporation'):
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_organization(org_name)
        self.navigator.go_to_products()

    def test_create_user_1(self):
        "Successfully creates a new product"
        self.products_page()

        name = generate_name(10)
        provider_name = generate_name(6)
        self.product.create(name=name, provider_name=provider_name)
