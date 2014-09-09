# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Roles CLI"""
from ddt import ddt
from robottelo.cli.factory import CLIFactoryError, make_role
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.helpers import generate_string
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestRole(CLITestCase):

    @skip_if_bug_open('bugzilla', 1046206)
    @skip_if_bug_open('bugzilla', 1138551)
    @skip_if_bug_open('bugzilla', 1138553)
    @data(
        generate_string('alpha', 15),
        generate_string('alphanumeric', 15),
        generate_string('numeric', 15),
        generate_string('latin1', 15),
        generate_string('utf8', 15),
    )
    def test_positive_create_role_1(self, data):
        """@Test: Create new roles and assign to the custom user

        @Feature: Roles

        @Assert: Assert creation of roles

        """
        try:
            role = make_role({'name': data})
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(
            role['name'],
            data, "Input and output name should be consistent")

    @skip_if_bug_open('bugzilla', 1046208)
    @skip_if_bug_open('bugzilla', 1138559)
    def test_create_role_permission_1(self):
        """@test: Create new roles Use different set of permission

           @feature: Roles

           @assert: Assert creation of roles with set of permission

           @status: manual

        """

        self.fail(NOT_IMPLEMENTED)
