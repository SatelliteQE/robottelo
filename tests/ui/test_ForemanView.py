#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
#from robottelo.lib.common.helpers import generate_name
from robottelo.lib.ui.locators import *

class Foreman(BaseUI):

    def test_switch_to_foreman_view(self):
        "Switches to foreman view"
        self.login.login("admin","admin")
        self.navigator.go_to_foreman()
