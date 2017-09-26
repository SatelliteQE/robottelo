# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six
import unittest2

from robottelo.ui.location import Location
from robottelo.ui.locators import common_locators
from robottelo.ui.locators import locators

if six.PY2:
    import mock
else:
    from unittest import mock


class LocationTestCase(unittest2.TestCase):
    def test_creation_without_parent_and_without_unassigned_host(self):
        location = Location(None)
        location.click = mock.Mock()
        location.assign_value = mock.Mock()
        location.wait_until_element = mock.Mock(return_value=None)
        location._configure_location = mock.Mock()
        location.select = mock.Mock()
        location.create('foo')
        click_calls = [
            mock.call(locators['location.new']),
            mock.call(common_locators['submit']),
            mock.call(common_locators['submit'])
        ]
        self.assertEqual(3, location.click.call_count)
        location.click.assert_has_calls(click_calls, any_order=False)
        location.assign_value.assert_called_once_with(
            locators['location.name'], 'foo')
        # not called if parent is None
        location.select.assert_not_called()
        location._configure_location.assert_called_once_with(
            capsules=None, all_capsules=None, domains=None, envs=None,
            hostgroups=None, medias=None, organizations=None, ptables=None,
            resources=None, select=True, subnets=None, templates=None,
            users=None, params=None
        )

    def test_creation_with_parent_and_unassigned_host(self):
        location = Location(None)
        location.click = mock.Mock()
        location.assign_value = mock.Mock()
        location.wait_until_element = mock.Mock()
        location._configure_location = mock.Mock()
        location.select = mock.Mock()
        configure_arguments = {
            arg: arg for arg in
            'capsules all_capsules domains hostgroups medias organizations '
            'envs ptables resources select subnets templates users params '
            'select'.split()
        }
        location.create('foo', 'parent', **configure_arguments)
        click_calls = [
            mock.call(locators['location.new']),
            mock.call(common_locators['submit']),
            mock.call(locators['location.proceed_to_edit']),
            mock.call(common_locators['submit'])
        ]
        self.assertEqual(4, location.click.call_count)
        location.click.assert_has_calls(click_calls, any_order=False)
        location.assign_value.assert_called_once_with(
            locators['location.name'], 'foo')
        # called only if parent is not None
        location.select.assert_called_once_with(
            locators['location.parent'], 'parent'
        )
        location._configure_location.assert_called_once_with(
            **configure_arguments)
