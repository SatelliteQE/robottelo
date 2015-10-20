# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI."""

from fauxfactory import gen_string
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.proxy import Proxy
from robottelo.cli.factory import (
    make_environment,
    make_hostgroup,
    make_location,
    make_org,
    make_os,
)
from robottelo.decorators import run_only_on
from robottelo.test import MetaCLITestCase


class TestHostGroup(MetaCLITestCase):
    """Test class for Host Group CLI"""
    factory = make_hostgroup
    factory_obj = HostGroup

    POSITIVE_UPDATE_DATA = (
        ({'id': gen_string('latin1', 10)},
         {'name': gen_string('latin1', 10)}),
        ({'id': gen_string('utf8', 10)},
         {'name': gen_string('utf8', 10)}),
        ({'id': gen_string('alpha', 10)},
         {'name': gen_string('alpha', 10)}),
        ({'id': gen_string('alphanumeric', 10)},
         {'name': gen_string('alphanumeric', 10)}),
        ({'id': gen_string('numeric', 10)},
         {'name': gen_string('numeric', 10)}),
        ({'id': gen_string('utf8', 10)},
         {'name': gen_string('html', 6)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'id': gen_string('utf8', 10)},
         {'name': gen_string('utf8', 300)}),
        ({'id': gen_string('utf8', 10)},
         {'name': ''}),
    )

    @run_only_on('sat')
    def test_create_hostgroup_with_environment(self):
        """@Test: Check if hostgroup with environment can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new environment assigned

        """
        environment = make_environment()
        hostgroup = make_hostgroup({'environment-id': environment['id']})
        self.assertEqual(environment['name'], hostgroup['environment'])

    @run_only_on('sat')
    def test_create_hostgroup_with_location(self):
        """@Test: Check if hostgroup with location can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new location assigned

        """
        location = make_location()
        hostgroup = make_hostgroup({'location-ids': location['id']})
        self.assertIn(location['name'], hostgroup['locations'])

    @run_only_on('sat')
    def test_create_hostgroup_with_operating_system(self):
        """@Test: Check if hostgroup with operating system can be created

        @Feature: Hostgroup - Create

        @Assert: Hostgroup is created and has operating system assigned

        """
        os = make_os()
        hostgroup = make_hostgroup({'operatingsystem-id': os['id']})
        self.assertEqual(hostgroup['operating-system'], os['title'])

    @run_only_on('sat')
    def test_create_hostgroup_with_organization(self):
        """@Test: Check if hostgroup with organization can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has new organization assigned

        """
        org = make_org()
        hostgroup = make_hostgroup({'organization-ids': org['id']})
        self.assertIn(org['name'], hostgroup['organizations'])

    @run_only_on('sat')
    def test_create_hostgroup_with_puppet_ca_proxy(self):
        """@Test: Check if hostgroup with puppet CA proxy server can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has puppet CA proxy server assigned

        """
        puppet_proxy = Proxy.list()[0]
        hostgroup = make_hostgroup({'puppet-ca-proxy': puppet_proxy['name']})
        self.assertEqual(puppet_proxy['id'], hostgroup['puppet-ca-proxy-id'])

    @run_only_on('sat')
    def test_create_hostgroup_with_puppet_proxy(self):
        """@Test: Check if hostgroup with puppet proxy server can be created

        @Feature: Hostgroup - Positive create

        @Assert: Hostgroup is created and has puppet proxy server assigned

        """
        puppet_proxy = Proxy.list()[0]
        hostgroup = make_hostgroup({'puppet-proxy': puppet_proxy['name']})
        self.assertEqual(
            puppet_proxy['id'],
            hostgroup['puppet-master-proxy-id'],
        )
