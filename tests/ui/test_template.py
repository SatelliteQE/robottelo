# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Template UI
"""

import unittest
from tests.ui.baseui import BaseUI


class Template(BaseUI):

    @unittest.skip("Test needs to create other required stuff")
    def test_create_template(self):
        "Create new Template"
        # Some hard coded values just for now to test the CRUD if needed
        name = "fedora18"
        os_list = ["rhel 6.5", "rhel64 6.4"]
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_provisioning_templates()
        self.template.create(name, os_list, True,
                             template_path="~/anaconda-ks.cfg",
                             template_type="provision")
        search = self.template.search(name)
        self.assertIsNotNone(search)
