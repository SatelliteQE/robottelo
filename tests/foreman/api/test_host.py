# -*- encoding: utf-8 -*-
"""Unit tests for the ``hosts`` paths.

An API reference can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html

"""
from fauxfactory import gen_integer, gen_ipaddr, gen_mac, gen_string
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.datafactory import (
    invalid_values_list,
    valid_hosts_list,
    valid_data_list,
)
from robottelo.decorators import bz_bug_is_open, run_only_on, tier1, tier2
from robottelo.test import APITestCase
from six.moves import http_client


class HostTestCase(APITestCase):
    """Tests for ``entities.Host().path()``."""

    @run_only_on('sat')
    @tier1
    def test_positive_get_search(self):
        """GET ``api/v2/hosts`` and specify the ``search`` parameter.

        @Feature: Hosts

        @Assert: HTTP 200 is returned, along with ``search`` term.
        """
        query = gen_string('utf8', gen_integer(1, 100))
        response = client.get(
            entities.Host().path(),
            auth=settings.server.get_credentials(),
            data={u'search': query},
            verify=False,
        )
        self.assertEqual(response.status_code, http_client.OK)
        self.assertEqual(response.json()['search'], query)

    @run_only_on('sat')
    @tier1
    def test_positive_get_per_page(self):
        """GET ``api/v2/hosts`` and specify the ``per_page`` parameter.

        @Feature: Hosts

        @Assert: HTTP 200 is returned, along with per ``per_page`` value.
        """
        per_page = gen_integer(1, 1000)
        response = client.get(
            entities.Host().path(),
            auth=settings.server.get_credentials(),
            data={u'per_page': per_page},
            verify=False,
        )
        self.assertEqual(response.status_code, http_client.OK)
        self.assertEqual(response.json()['per_page'], per_page)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_owner_type(self):
        """Create a host and specify an ``owner_type``.

        @Feature: Hosts

        @Assert: The host can be read back, and the ``owner_type`` attribute is
        correct.
        """
        for owner_type in ('User', 'Usergroup'):
            with self.subTest(owner_type):
                if owner_type == 'Usergroup' and bz_bug_is_open(1203865):
                    continue  # instead of skip for compatibility with py.test
                host = entities.Host()
                host.create_missing()
                host.owner_type = owner_type
                host = host.create(create_missing=False)
                self.assertEqual(host.owner_type, owner_type)

    @run_only_on('sat')
    @tier1
    def test_positive_update_owner_type(self):
        """Update a host's ``owner_type``.

        @Feature: Hosts

        @Assert: The host's ``owner_type`` attribute is updated as requested.
        """
        host = entities.Host().create()
        for owner_type in ('User', 'Usergroup'):
            with self.subTest(owner_type):
                if owner_type == 'Usergroup' and bz_bug_is_open(1210001):
                    continue  # instead of skip for compatibility with py.test
                host.owner_type = owner_type
                host = host.update(['owner_type'])
                self.assertEqual(host.owner_type, owner_type)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create a host with different names and minimal input parameters

        @feature: Hosts

        @assert: A host is created with expected name
        """
        for name in valid_hosts_list():
            with self.subTest(name):
                host = entities.Host()
                host.create_missing()
                host.name = name
                host = host.create(create_missing=False)
                self.assertEqual(
                    host.name,
                    '{0}.{1}'.format(name, host.domain.read().name).lower()
                )

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_ip(self):
        """Create a host with IP address specified

        @feature: Hosts

        @assert: A host is created with expected IP address
        """
        host = entities.Host()
        ip_addr = gen_ipaddr()
        host.create_missing()
        host.ip = ip_addr
        host = host.create(create_missing=False)
        self.assertEqual(host.ip, ip_addr)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_hostgroup(self):
        """Create a host with hostgroup specified

        @feature: Hosts

        @assert: A host is created with expected hostgroup assigned
        """
        host = entities.Host()
        host.create_missing()
        hostgroup = entities.HostGroup(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host.hostgroup = hostgroup
        host = host.create(create_missing=False)
        self.assertEqual(host.hostgroup.read().name, hostgroup.name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_proxy(self):
        """Create a host with puppet proxy specified

        @feature: Hosts

        @assert: A host is created with expected puppet proxy assigned
        """
        host = entities.Host()
        host.create_missing()
        proxy = entities.SmartProxy().search()[0]
        host.puppet_proxy = proxy
        host = host.create(create_missing=False)
        self.assertEqual(host.puppet_proxy.read().name, proxy.name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_puppet_ca_proxy(self):
        """Create a host with puppet CA proxy specified

        @feature: Hosts

        @assert: A host is created with expected puppet CA proxy assigned
        """
        host = entities.Host()
        host.create_missing()
        proxy = entities.SmartProxy().search()[0]
        host.puppet_ca_proxy = proxy
        host = host.create(create_missing=False)
        self.assertEqual(host.puppet_ca_proxy.read().name, proxy.name)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_subnet(self):
        """Create a host with subnet specified

        @feature: Hosts

        @assert: A host is created with expected subnet assigned
        """
        host = entities.Host()
        host.create_missing()
        subnet = entities.Subnet().create()
        host.subnet = subnet
        host = host.create(create_missing=False)
        self.assertEqual(host.subnet.read().name, subnet.name)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_compresource(self):
        """Create a host with compute resource specified

        @feature: Hosts

        @assert: A host is created with expected compute resource assigned
        """
        host = entities.Host()
        host.create_missing()
        compresource = entities.LibvirtComputeResource(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host.compute_resource = compresource
        host = host.create(create_missing=False)
        self.assertEqual(host.compute_resource.read().name, compresource.name)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_model(self):
        """Create a host with model specified

        @feature: Hosts

        @assert: A host is created with expected model assigned
        """
        host = entities.Host()
        host.create_missing()
        model = entities.Model().create()
        host.model = model
        host = host.create(create_missing=False)
        self.assertEqual(host.model.read().name, model.name)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_user(self):
        """Create a host with user specified

        @feature: Hosts

        @assert: A host is created with expected user assigned
        """
        host = entities.Host()
        host.create_missing()
        user = entities.User().create()
        host.owner_type = 'User'
        host.owner = user
        host = host.create(create_missing=False)
        self.assertEqual(host.owner.read().login, user.login)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_build_parameter(self):
        """Create a host with 'build' parameter specified.
        Build parameter determines whether to enable the host for provisioning

        @feature: Hosts

        @assert: A host is created with expected 'build' parameter value
        """
        host = entities.Host()
        host.create_missing()
        host.build = True
        host = host.create(create_missing=False)
        self.assertEqual(host.build, True)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_enabled_parameter(self):
        """Create a host with 'enabled' parameter specified.
        Enabled parameter determines whether to include the host within
        Satellite 6 reporting

        @feature: Hosts

        @assert: A host is created with expected 'enabled' parameter value
        """
        host = entities.Host()
        host.create_missing()
        host.enabled = False
        host = host.create(create_missing=False)
        self.assertEqual(host.enabled, False)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_managed_parameter(self):
        """Create a host with managed parameter specified.
        Managed flag shows whether the host is managed or unmanaged and
        determines whether some extra parameters are required

        @feature: Hosts

        @assert: A host is created with expected managed parameter value
        """
        host = entities.Host()
        host.create_missing()
        host.managed = True
        host = host.create(create_missing=False)
        self.assertEqual(host.managed, True)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_comment(self):
        """Create a host with a comment

        @feature: Hosts

        @assert: A host is created with expected comment
        """
        for comment in valid_data_list():
            with self.subTest(comment):
                host = entities.Host()
                host.create_missing()
                host.comment = comment
                host = host.create(create_missing=False)
                self.assertEqual(host.comment, comment)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_compute_profile(self):
        """Create a host with a compute profile specified

        @feature: Hosts

        @assert: A host is created with expected compute profile assigned
        """
        host = entities.Host()
        host.create_missing()
        profile = entities.ComputeProfile().create()
        host.compute_profile = profile
        host = host.create(create_missing=False)
        self.assertEqual(host.compute_profile.read().name, profile.name)

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete a host

        @feature: Hosts

        @assert: Host is deleted
        """
        host = entities.Host().create(create_missing=True)
        host.delete()
        with self.assertRaises(HTTPError):
            host.read()

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update a host with a new name

        @feature: Hosts

        @assert: A host is updated with expected name
        """
        host = entities.Host().create()
        for new_name in valid_hosts_list():
            with self.subTest(new_name):
                host.name = new_name
                host = host.update(['name'])
                self.assertEqual(
                    host.name,
                    '{0}.{1}'.format(new_name, host.domain.read().name).lower()
                )

    @run_only_on('sat')
    @tier1
    def test_positive_update_mac(self):
        """Update a host with a new MAC address

        @feature: Hosts

        @assert: A host is updated with a new MAC address
        """
        host = entities.Host().create()
        new_mac = gen_mac()
        host.mac = new_mac
        host = host.update(['mac'])
        self.assertEqual(host.mac, new_mac)

    @run_only_on('sat')
    @tier2
    def test_positive_update_domain(self):
        """Update a host with a new domain

        @feature: Hosts

        @assert: A host is updated with a new domain
        """
        host = entities.Host().create()
        new_domain = entities.Domain(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host.domain = new_domain
        host = host.update(['domain'])
        self.assertEqual(host.domain.read().name, new_domain.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_env(self):
        """Update a host with a new environment

        @feature: Hosts

        @assert: A host is updated with a new environment
        """
        host = entities.Host().create()
        new_env = entities.Environment(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host.environment = new_env
        host = host.update(['environment'])
        self.assertEqual(host.environment.read().name, new_env.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_arch(self):
        """Update a host with a new architecture

        @feature: Hosts

        @assert: A host is updated with a new architecture
        """
        host = entities.Host().create()
        new_arch = entities.Architecture(
            operatingsystem=[host.operatingsystem],
        ).create()
        host.architecture = new_arch
        host = host.update(['architecture'])
        self.assertEqual(host.architecture.read().name, new_arch.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_os(self):
        """Update a host with a new operating system

        @feature: Hosts

        @assert: A host is updated with a new operating system
        """
        host = entities.Host().create()
        new_os = entities.OperatingSystem(
            architecture=[host.architecture],
            ptable=[host.ptable],
        ).create()
        medium = entities.Media(id=host.medium.id).read()
        medium.operatingsystem.append(new_os)
        medium.update(['operatingsystem'])
        host.operatingsystem = new_os
        host = host.update(['operatingsystem'])
        self.assertEqual(host.operatingsystem.read().name, new_os.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_medium(self):
        """Update a host with a new medium

        @feature: Hosts

        @assert: A host is updated with a new medium
        """
        host = entities.Host().create()
        new_medium = entities.Media(
            operatingsystem=[host.operatingsystem],
            # pylint:disable=no-member
            location=[host.location],
            organization=[host.organization],
        ).create()
        new_medium.operatingsystem.append(host.operatingsystem)
        new_medium.update(['operatingsystem'])
        host.medium = new_medium
        host = host.update(['medium'])
        self.assertEqual(host.medium.read().name, new_medium.name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_ip(self):
        """Update a host with a new IP address

        @feature: Hosts

        @assert: A host is updated with a new IP address
        """
        host = entities.Host()
        host.create_missing()
        host.ip = gen_ipaddr()
        host = host.create(create_missing=False)
        new_ip = gen_ipaddr()
        host.ip = new_ip
        host = host.update(['ip'])
        self.assertEqual(host.ip, new_ip)

    @run_only_on('sat')
    @tier2
    def test_positive_update_hostgroup(self):
        """Update a host with a new hostgroup

        @feature: Hosts

        @assert: A host is updated with a new hostgroup
        """
        host = entities.Host()
        host.create_missing()
        host.hostgroup = entities.HostGroup(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host = host.create(create_missing=False)
        new_hostgroup = entities.HostGroup(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host.hostgroup = new_hostgroup
        host = host.update(['hostgroup'])
        self.assertEqual(host.hostgroup.read().name, new_hostgroup.name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_puppet_proxy(self):
        """Update a host with a new puppet proxy

        @feature: Hosts

        @assert: A host is updated with a new puppet proxy
        """
        host = entities.Host()
        host.create_missing()
        host = host.create(create_missing=False)
        new_proxy = entities.SmartProxy().search()[0]
        host.puppet_proxy = new_proxy
        host = host.update(['puppet_proxy'])
        self.assertEqual(host.puppet_proxy.read().name, new_proxy.name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_puppet_ca_proxy(self):
        """Update a host with a new puppet CA proxy

        @feature: Hosts

        @assert: A host is updated with a new puppet CA proxy
        """
        host = entities.Host()
        host.create_missing()
        host = host.create(create_missing=False)
        new_proxy = entities.SmartProxy().search()[0]
        host.puppet_ca_proxy = new_proxy
        host = host.update(['puppet_ca_proxy'])
        self.assertEqual(host.puppet_ca_proxy.read().name, new_proxy.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_subnet(self):
        """Update a host with a new subnet

        @feature: Hosts

        @assert: A host is updated with a new subnet
        """
        host = entities.Host()
        host.create_missing()
        host.subnet = entities.Subnet().create()
        host = host.create(create_missing=False)
        new_subnet = entities.Subnet().create()
        host.subnet = new_subnet
        host = host.update(['subnet'])
        self.assertEqual(host.subnet.read().name, new_subnet.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_compresource(self):
        """Update a host with a new compute resource

        @feature: Hosts

        @assert: A host is updated with a new compute resource
        """
        host = entities.Host()
        host.create_missing()
        host.compute_resource = entities.LibvirtComputeResource(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host = host.create(create_missing=False)
        new_compresource = entities.LibvirtComputeResource(
            location=[host.location],
            organization=[host.organization],
        ).create()
        host.compute_resource = new_compresource
        host = host.update(['compute_resource'])
        self.assertEqual(
            host.compute_resource.read().name, new_compresource.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_model(self):
        """Update a host with a new model

        @feature: Hosts

        @assert: A host is updated with a new model
        """
        host = entities.Host()
        host.create_missing()
        host.model = entities.Model().create()
        host = host.create(create_missing=False)
        new_model = entities.Model().create()
        host.model = new_model
        host = host.update(['model'])
        self.assertEqual(host.model.read().name, new_model.name)

    @run_only_on('sat')
    @tier2
    def test_positive_update_user(self):
        """Update a host with a new user

        @feature: Hosts

        @assert: A host is updated with a new user
        """
        host = entities.Host()
        host.create_missing()
        host.owner = entities.User().create()
        host.owner_type = 'User'
        host = host.create(create_missing=False)
        new_user = entities.User().create()
        host.owner = new_user
        host = host.update(['owner'])
        self.assertEqual(host.owner.read().login, new_user.login)

    @run_only_on('sat')
    @tier1
    def test_positive_update_build_parameter(self):
        """Update a host with a new 'build' parameter value.
        Build parameter determines whether to enable the host for provisioning

        @feature: Hosts

        @assert: A host is updated with a new 'build' parameter value
        """
        for build in (True, False):
            with self.subTest(build):
                host = entities.Host()
                host.create_missing()
                host.build = build
                host = host.create(create_missing=False)
                host.build = not build
                host = host.update(['build'])
                self.assertEqual(host.build, not build)

    @run_only_on('sat')
    @tier1
    def test_positive_update_enabled_parameter(self):
        """Update a host with a new 'enabled' parameter value.
        Enabled parameter determines whether to include the host within
        Satellite 6 reporting

        @feature: Hosts

        @assert: A host is updated with a new 'enabled' parameter value
        """
        for enabled in (True, False):
            with self.subTest(enabled):
                host = entities.Host()
                host.create_missing()
                host.enabled = enabled
                host = host.create(create_missing=False)
                host.enabled = not enabled
                host = host.update(['enabled'])
                self.assertEqual(host.enabled, not enabled)

    @run_only_on('sat')
    @tier1
    def test_positive_update_managed_parameter(self):
        """Update a host with a new 'managed' parameter value
        Managed flag shows whether the host is managed or unmanaged and
        determines whether some extra parameters are required

        @feature: Hosts

        @assert: A host is updated with a new 'managed' parameter value
        """
        for managed in (True, False):
            with self.subTest(managed):
                host = entities.Host()
                host.create_missing()
                host.managed = managed
                host = host.create(create_missing=False)
                host.managed = not managed
                host = host.update(['managed'])
                self.assertEqual(host.managed, not managed)

    @run_only_on('sat')
    @tier1
    def test_positive_update_comment(self):
        """Update a host with a new comment

        @feature: Hosts

        @assert: A host is updated with a new comment
        """
        for new_comment in valid_data_list():
            with self.subTest(new_comment):
                host = entities.Host()
                host.create_missing()
                host.comment = gen_string('alpha')
                host = host.create(create_missing=False)
                host.comment = new_comment
                host = host.update(['comment'])
                self.assertEqual(host.comment, new_comment)

    @run_only_on('sat')
    @tier2
    def test_positive_update_compute_profile(self):
        """Update a host with a new compute profile

        @feature: Hosts

        @assert: A host is updated with a new compute profile
        """
        host = entities.Host()
        host.create_missing()
        host.compute_profile = entities.ComputeProfile().create()
        host = host.create(create_missing=False)
        new_cprofile = entities.ComputeProfile().create()
        host.compute_profile = new_cprofile
        host = host.update(['compute_profile'])
        self.assertEqual(host.compute_profile.read().name, new_cprofile.name)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Attempt to update a host with invalid or empty name

        @feature: Hosts

        @assert: A host is not updated
        """
        host = entities.Host().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                host.name = new_name
                with self.assertRaises(HTTPError):
                    host.update(['name'])
                self.assertNotEqual(
                    host.read().name,
                    u'{0}.{1}'
                    .format(new_name, host.domain.read().name).lower()
                )

    @run_only_on('sat')
    @tier1
    def test_negative_update_mac(self):
        """Attempt to update a host with invalid or empty MAC address

        @feature: Hosts

        @assert: A host is not updated
        """
        host = entities.Host().create()
        for new_mac in invalid_values_list():
            with self.subTest(new_mac):
                host.mac = new_mac
                with self.assertRaises(HTTPError):
                    host.update(['mac'])
                self.assertNotEqual(host.read().mac, new_mac)

    @run_only_on('sat')
    @tier2
    def test_negative_update_arch(self):
        """Attempt to update a host with an architecture, which does not belong
        to host's operating system

        @feature: Hosts

        @assert: A host is not updated
        """
        host = entities.Host().create()
        new_arch = entities.Architecture().create()
        host.architecture = new_arch
        with self.assertRaises(HTTPError):
            host = host.update(['architecture'])
        self.assertNotEqual(
            host.read().architecture.read().name, new_arch.name)

    @run_only_on('sat')
    @tier2
    def test_negative_update_os(self):
        """Attempt to update a host with an operating system, which is not
        associated with host's medium

        @feature: Hosts

        @assert: A host is not updated
        """
        host = entities.Host().create()
        new_os = entities.OperatingSystem(
            architecture=[host.architecture],
            ptable=[host.ptable],
        ).create()
        host.operatingsystem = new_os
        with self.assertRaises(HTTPError):
            host = host.update(['operatingsystem'])
        self.assertNotEqual(
            host.read().operatingsystem.read().name, new_os.name)
