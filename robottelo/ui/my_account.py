# -*- encoding: utf-8 -*-
"""Implements My Account UI."""
from robottelo.ui.base import Base
from robottelo.ui.navigator import Navigator


class MyAccount(Base):
    """Implements navigation to My Account."""

    def navigate_to_entity(self):
        """Navigate to My Account page"""
        Navigator(self.browser).go_to_my_account()
