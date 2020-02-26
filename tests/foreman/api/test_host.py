# -*- encoding: utf-8 -*-
"""Unit tests for the ``hosts`` paths.

An API reference can be found here:
http://theforeman.org/api/apidoc/v2/hosts.html


:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from requests.exceptions import HTTPError
from six.moves import http_client

from robottelo.api.utils import promote
from robottelo.api.utils import publish_puppet_module
from robottelo.config import settings
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.constants import ENVIRONMENT
from robottelo.datafactory import invalid_interfaces_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_hosts_list
from robottelo.datafactory import valid_interfaces_list
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.decorators.func_locker import lock_function
from robottelo.test import APITestCase


class HostTestCase(APITestCase):
    """Tests for ``entities.Host().path()``."""

    @classmethod
    @lock_function
    def setUpClass(cls):
        """Setup common entities."""
        super(HostTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        # Content View and repository related entities
        cls.cv = publish_puppet_module(
            [{'author': 'robottelo', 'name': 'generic_1'}],
            CUSTOM_PUPPET_REPO,
            organization_id=cls.org.id,
        )
        cls.env = (
            entities.Environment()
            .search(
                query={
                    'search': u'content_view="{0}" and organization_id={1}'.format(
                        cls.cv.name, cls.org.id
                    )
                }
            )[0]
            .read()
        )
        cls.env.location.append(cls.loc)
        cls.env.update(['location'])
        cls.lce = (
            entities.LifecycleEnvironment()
            .search(
                query={
                    'search': 'name={0} and organization_id={1}'.format(ENVIRONMENT, cls.org.id)
                }
            )[0]
            .read()
        )
        cls.puppet_classes = entities.PuppetClass().search(
            query={
                'search': u'name ~ "{0}" and environment = "{1}"'.format('generic_1', cls.env.name)
            }
        )
        # Compute Resource related entities
        cls.compresource_libvirt = entities.LibvirtComputeResource(
            organization=[cls.org], location=[cls.loc]
        ).create()
        cls.image = entities.Image(compute_resource=cls.compresource_libvirt).create()

    @tier1
    def test_positive_get_search(self):
        """GET ``api/v2/hosts`` and specify the ``search`` parameter.

        :id: d63f87e5-66e6-4886-8b44-4129259493a6

        :expectedresults: HTTP 200 is returned, along with ``search`` term.

        :CaseImportance: Critical
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

    @tier1
    def test_positive_get_per_page(self):
        """GET ``api/v2/hosts`` and specify the ``per_page`` parameter.

        :id: 9086f41c-b3b9-4af2-b6c4-46b80b4d1cfd

        :expectedresults: HTTP 200 is returned, along with per ``per_page``
            value.

        :CaseImportance: Critical
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

    @tier1
    def test_negative_create_with_owner_type(self):
        """Create a host and specify only ``owner_type``.

        :id: cdf9d16f-1c47-498a-be48-901355385dde

        :expectedresults: The host can't be created as ``owner`` is required.

        :CaseImportance: Critical
        """
        for owner_type in ('User', 'Usergroup'):
            with self.subTest(owner_type):
                with self.assertRaises(HTTPError) as context:
                    entities.Host(owner_type=owner_type).create()
                self.assertEqual(context.exception.response.status_code, 422)
                self.assertRegexpMatches(
                    context.exception.response.text, "owner must be specified"
                )

    @tier1
    def test_positive_update_owner_type(self):
        """Update a host's ``owner_type``.

        :id: b72cd8ef-3a0b-4d2d-94f9-9b64908d699a

        :expectedresults: The host's ``owner_type`` attribute is updated as
            requested.

        :CaseImportance: Critical

        :BZ: 1210001
        """
        owners = {
            'User': entities.User(organization=[self.org], location=[self.loc]).create(),
            'Usergroup': entities.UserGroup().create(),
        }
        host = entities.Host(organization=self.org, location=self.loc).create()
        for owner_type in owners:
            with self.subTest(owner_type):
                host.owner_type = owner_type
                host.owner = owners[owner_type]
                host = host.update(['owner_type', 'owner'])
                self.assertEqual(host.owner_type, owner_type)
                self.assertEqual(host.owner.read(), owners[owner_type])

    @tier1
    def test_positive_create_with_name(self):
        """Create a host with different names and minimal input parameters

        :id: a7c0e8ec-3816-4092-88b1-0324cb271752

        :expectedresults: A host is created with expected name

        :CaseImportance: Critical
        """
        for name in valid_hosts_list():
            with self.subTest(name):
                host = entities.Host(name=name).create()
                self.assertEqual(host.name, '{0}.{1}'.format(name, host.domain.read().name))

    @tier1
    def test_positive_create_with_ip(self):
        """Create a host with IP address specified

        :id: 3f266906-c509-42ce-9b20-def448bf8d86

        :expectedresults: A host is created with expected IP address

        :CaseImportance: Critical
        """
        ip_addr = gen_ipaddr()
        host = entities.Host(ip=ip_addr).create()
        self.assertEqual(host.ip, ip_addr)

    @tier2
    def test_positive_create_with_hostgroup(self):
        """Create a host with hostgroup specified

        :id: 8f9601f9-afd8-4a88-8f28-a5cbc996e805

        :expectedresults: A host is created with expected hostgroup assigned

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], environment_id=lce.id)
        loc = entities.Location(organization=[org]).create()
        hostgroup = entities.HostGroup(location=[loc], organization=[org]).create()
        host = entities.Host(
            hostgroup=hostgroup,
            location=loc,
            organization=org,
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lce.id,
            },
        ).create()
        self.assertEqual(host.hostgroup.read().name, hostgroup.name)

    @tier2
    def test_positive_create_inherit_lce_cv(self):
        """Create a host with hostgroup specified. Make sure host inherited
        hostgroup's lifecycle environment and content-view

        :id: 229cbdbc-838b-456c-bc6f-4ac895badfbc

        :expectedresults: Host's lifecycle environment and content view match
            the ones specified in hostgroup

        :CaseLevel: Integration

        :BZ: 1391656
        """
        hostgroup = entities.HostGroup(
            content_view=self.cv, lifecycle_environment=self.lce, organization=[self.org]
        ).create()
        host = entities.Host(hostgroup=hostgroup, organization=self.org).create()
        self.assertEqual(
            host.content_facet_attributes['lifecycle_environment_id'],
            hostgroup.lifecycle_environment.id,
        )
        self.assertEqual(
            host.content_facet_attributes['content_view_id'], hostgroup.content_view.id
        )

    @tier2
    def test_positive_create_with_inherited_params(self):
        """Create a new Host in organization and location with parameters

        :BZ: 1287223

        :id: 5e17e968-7fe2-4e5b-90ca-ae66f4e5307a

        :customerscenario: true

        :expectedresults: Host has inherited parameters from organization and
            location as well as global parameters

        :CaseImportance: High
        """
        org = entities.Organization().create()
        org_param = entities.Parameter(organization=org).create()
        loc = entities.Location().create()
        loc_param = entities.Parameter(location=loc).create()
        host = entities.Host(location=loc, organization=org).create()
        # get global parameters
        glob_param_list = {
            (param.name, param.value) for param in entities.CommonParameter().search()
        }
        # if there are no global parameters, create one
        if len(glob_param_list) == 0:
            param_name = gen_string('alpha')
            param_global_value = gen_string('numeric')
            entities.CommonParameter(name=param_name, value=param_global_value).create()
            glob_param_list = {
                (param.name, param.value) for param in entities.CommonParameter().search()
            }
        self.assertEqual(len(host.all_parameters), 2 + len(glob_param_list))
        innerited_params = {(org_param.name, org_param.value), (loc_param.name, loc_param.value)}
        expected_params = innerited_params.union(glob_param_list)
        self.assertEqual(
            expected_params, {(param['name'], param['value']) for param in host.all_parameters}
        )

    @tier1
    def test_positive_create_with_puppet_proxy(self):
        """Create a host with puppet proxy specified

        :id: 9269d87b-abb9-48e0-b0d1-9b8e258e1ae3

        :expectedresults: A host is created with expected puppet proxy assigned

        :CaseImportance: Critical
        """
        proxy = entities.SmartProxy().search(
            query={'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host = entities.Host(puppet_proxy=proxy).create()
        self.assertEqual(host.puppet_proxy.read().name, proxy.name)

    @tier1
    def test_positive_create_with_puppet_ca_proxy(self):
        """Create a host with puppet CA proxy specified

        :id: 1b73dd35-c2e8-44bd-b8f8-9e51428a6239

        :expectedresults: A host is created with expected puppet CA proxy
            assigned

        :CaseImportance: Critical
        """
        proxy = entities.SmartProxy().search(
            query={'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host = entities.Host(puppet_ca_proxy=proxy).create()
        self.assertEqual(host.puppet_ca_proxy.read().name, proxy.name)

    @tier2
    def test_positive_create_with_puppet_class(self):
        """Create a host with associated puppet classes

        :id: 2690d6b0-441b-44c5-b7d2-4093616e037e

        :expectedresults: A host is created with expected puppet classes
        """
        host = entities.Host(
            organization=self.org,
            location=self.loc,
            environment=self.env,
            puppetclass=self.puppet_classes,
        ).create()
        self.assertEqual(
            {puppet_class.id for puppet_class in host.puppetclass},
            {puppet_class.id for puppet_class in self.puppet_classes},
        )

    @tier2
    def test_positive_create_with_subnet(self):
        """Create a host with subnet specified

        :id: 9aa97aff-8439-4027-89ee-01c643fbf7d1

        :expectedresults: A host is created with expected subnet assigned

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        subnet = entities.Subnet(location=[loc], organization=[org]).create()
        host = entities.Host(location=loc, organization=org, subnet=subnet).create()
        self.assertEqual(host.subnet.read().name, subnet.name)

    @tier2
    def test_positive_create_with_compresource(self):
        """Create a host with compute resource specified

        :id: 53069f2e-67a7-4d57-9846-acf6d8ce03cb

        :expectedresults: A host is created with expected compute resource
            assigned

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        compresource = entities.LibvirtComputeResource(location=[loc], organization=[org]).create()
        host = entities.Host(
            compute_resource=compresource, location=loc, organization=org
        ).create()
        self.assertEqual(host.compute_resource.read().name, compresource.name)

    @tier2
    def test_positive_create_with_model(self):
        """Create a host with model specified

        :id: 7a912a19-71e4-4843-87fd-bab98c156f4a

        :expectedresults: A host is created with expected model assigned

        :CaseLevel: Integration
        """
        model = entities.Model().create()
        host = entities.Host(model=model).create()
        self.assertEqual(host.model.read().name, model.name)

    @tier2
    def test_positive_create_with_user(self):
        """Create a host with user specified

        :id: 72e20f8f-17dc-4e38-8ac1-d08df8758f56

        :expectedresults: A host is created with expected user assigned

        :CaseLevel: Integration
        """
        user = entities.User(organization=[self.org], location=[self.loc]).create()
        host = entities.Host(
            owner=user, owner_type='User', organization=self.org, location=self.loc
        ).create()
        self.assertEqual(host.owner.read(), user)

    @tier2
    def test_positive_create_with_usergroup(self):
        """Create a host with user group specified

        :id: 706e860c-8c05-4ddc-be20-0ecd9f0da813

        :expectedresults: A host is created with expected user group assigned

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        role = entities.Role().create()
        user = entities.User(location=[loc], organization=[org], role=[role]).create()
        usergroup = entities.UserGroup(role=[role], user=[user]).create()
        host = entities.Host(
            location=loc, organization=org, owner=usergroup, owner_type='Usergroup'
        ).create()
        self.assertEqual(host.owner.read().name, usergroup.name)

    @tier1
    def test_positive_create_with_build_parameter(self):
        """Create a host with 'build' parameter specified.
        Build parameter determines whether to enable the host for provisioning

        :id: de30cf62-5036-4247-a5f0-37dd2b4aae23

        :expectedresults: A host is created with expected 'build' parameter
            value

        :CaseImportance: Critical
        """
        host = entities.Host(build=True).create()
        self.assertEqual(host.build, True)

    @tier1
    def test_positive_create_with_enabled_parameter(self):
        """Create a host with 'enabled' parameter specified.
        Enabled parameter determines whether to include the host within
        Satellite 6 reporting

        :id: bd8d33f9-37de-4b8d-863e-9f73cd8dcec1

        :expectedresults: A host is created with expected 'enabled' parameter
            value

        :CaseImportance: Critical
        """
        host = entities.Host(enabled=False).create()
        self.assertEqual(host.enabled, False)

    @tier1
    def test_positive_create_with_managed_parameter(self):
        """Create a host with managed parameter specified.
        Managed flag shows whether the host is managed or unmanaged and
        determines whether some extra parameters are required

        :id: 00dcfaed-6f54-4b6a-a022-9c97fb992324

        :expectedresults: A host is created with expected managed parameter
            value

        :CaseImportance: Critical
        """
        host = entities.Host(managed=True).create()
        self.assertEqual(host.managed, True)

    @tier1
    def test_positive_create_with_comment(self):
        """Create a host with a comment

        :id: 9b78663f-139c-4d0b-9115-180624b0d41b

        :expectedresults: A host is created with expected comment

        :CaseImportance: Critical
        """
        for comment in valid_data_list():
            with self.subTest(comment):
                host = entities.Host(comment=comment).create()
                self.assertEqual(host.comment, comment)

    @tier2
    def test_positive_create_with_compute_profile(self):
        """Create a host with a compute profile specified

        :id: 94be25e8-035d-42c5-b1f3-3aa20030410d

        :expectedresults: A host is created with expected compute profile
            assigned

        :CaseLevel: Integration
        """
        profile = entities.ComputeProfile().create()
        host = entities.Host(compute_profile=profile).create()
        self.assertEqual(host.compute_profile.read().name, profile.name)

    @tier2
    def test_positive_create_with_content_view(self):
        """Create a host with a content view specified

        :id: 10f69c7a-088e-474c-b869-1ad12deda2ad

        :expectedresults: A host is created with expected content view assigned

        :CaseLevel: Integration
        """
        host = entities.Host(
            organization=self.org,
            location=self.loc,
            content_facet_attributes={
                'content_view_id': self.cv.id,
                'lifecycle_environment_id': self.lce.id,
            },
        ).create()
        self.assertEqual(host.content_facet_attributes['content_view_id'], self.cv.id)
        self.assertEqual(host.content_facet_attributes['lifecycle_environment_id'], self.lce.id)

    @tier1
    def test_positive_create_with_host_parameters(self):
        """Create a host with a host parameters specified

        :id: e3af6718-4016-4756-bbb0-e3c24ac1e340

        :expectedresults: A host is created with expected host parameters

        :CaseImportance: Critical
        """
        parameters = [{'name': gen_string('alpha'), 'value': gen_string('alpha')}]
        host = entities.Host(
            organization=self.org, location=self.loc, host_parameters_attributes=parameters
        ).create()
        self.assertEqual(host.host_parameters_attributes[0]['name'], parameters[0]['name'])
        self.assertEqual(host.host_parameters_attributes[0]['value'], parameters[0]['value'])
        self.assertIn('id', host.host_parameters_attributes[0])

    @tier2
    def test_positive_create_with_image(self):
        """Create a host with an image specified

        :id: 38b17b4d-d9d8-4ea1-aa0f-558496b990fc

        :expectedresults: A host is created with expected image

        :CaseLevel: Integration
        """
        host = entities.Host(
            organization=self.org,
            location=self.loc,
            compute_resource=self.compresource_libvirt,
            image=self.image,
        ).create()
        self.assertEqual(host.image.id, self.image.id)

    @tier1
    def test_positive_create_with_provision_method(self):
        """Create a host with provision method specified

        :id: c2243c30-f70a-4063-a4a4-f67b598a892b

        :expectedresults: A host is created with expected provision method

        :CaseImportance: Critical
        """
        for method in ['build', 'image']:
            with self.subTest(method):
                # Compute resource is required for 'image' method
                host = entities.Host(
                    organization=self.org,
                    location=self.loc,
                    compute_resource=self.compresource_libvirt,
                    provision_method=method,
                ).create()
                self.assertEqual(host.provision_method, method)

    @tier1
    def test_positive_delete(self):
        """Delete a host

        :id: ec725359-a75e-498c-9da8-f5abd2343dd3

        :expectedresults: Host is deleted

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        host.delete()
        with self.assertRaises(HTTPError):
            host.read()

    @tier1
    def test_positive_update_name(self):
        """Update a host with a new name

        :id: a82b606c-d683-44ba-9086-684396ef1c10

        :expectedresults: A host is updated with expected name

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        for new_name in valid_hosts_list():
            with self.subTest(new_name):
                host.name = new_name
                host = host.update(['name'])
                self.assertEqual(host.name, '{0}.{1}'.format(new_name, host.domain.read().name))

    @tier1
    def test_positive_update_mac(self):
        """Update a host with a new MAC address

        :id: 72e3b020-7347-4500-8669-c6ddf6dfd0b6

        :expectedresults: A host is updated with a new MAC address

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        new_mac = gen_mac(multicast=False)
        host.mac = new_mac
        host = host.update(['mac'])
        self.assertEqual(host.mac, new_mac)

    @tier2
    def test_positive_update_domain(self):
        """Update a host with a new domain

        :id: 8ca9f67c-4c11-40f9-b434-4f200bad000f

        :expectedresults: A host is updated with a new domain

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        new_domain = entities.Domain(
            location=[host.location], organization=[host.organization]
        ).create()
        host.domain = new_domain
        host = host.update(['domain'])
        self.assertEqual(host.domain.read().name, new_domain.name)

    @tier2
    def test_positive_update_env(self):
        """Update a host with a new environment

        :id: 87a08dbf-fd4c-4b6c-bf73-98ab70756fc6

        :expectedresults: A host is updated with a new environment

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        new_env = entities.Environment(
            location=[host.location], organization=[host.organization]
        ).create()
        host.environment = new_env
        host = host.update(['environment'])
        self.assertEqual(host.environment.read().name, new_env.name)

    @tier2
    def test_positive_update_arch(self):
        """Update a host with a new architecture

        :id: 5f190b14-e6db-46e1-8cd1-e94e048e6a77

        :expectedresults: A host is updated with a new architecture

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        new_arch = entities.Architecture(operatingsystem=[host.operatingsystem]).create()
        host.architecture = new_arch
        host = host.update(['architecture'])
        self.assertEqual(host.architecture.read().name, new_arch.name)

    @tier2
    def test_positive_update_os(self):
        """Update a host with a new operating system

        :id: 46edced1-8909-4066-b196-b8e22512341f

        :expectedresults: A host is updated with a new operating system

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        new_os = entities.OperatingSystem(
            architecture=[host.architecture], ptable=[host.ptable]
        ).create()
        medium = entities.Media(id=host.medium.id).read()
        medium.operatingsystem.append(new_os)
        medium.update(['operatingsystem'])
        host.operatingsystem = new_os
        host = host.update(['operatingsystem'])
        self.assertEqual(host.operatingsystem.read().name, new_os.name)

    @tier2
    def test_positive_update_medium(self):
        """Update a host with a new medium

        :id: d81cb65c-48b3-4ce3-971e-51b9dd123697

        :expectedresults: A host is updated with a new medium

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        new_medium = entities.Media(
            operatingsystem=[host.operatingsystem],
            location=[host.location],
            organization=[host.organization],
        ).create()
        new_medium.operatingsystem.append(host.operatingsystem)
        new_medium.update(['operatingsystem'])
        host.medium = new_medium
        host = host.update(['medium'])
        self.assertEqual(host.medium.read().name, new_medium.name)

    @tier1
    def test_positive_update_ip(self):
        """Update a host with a new IP address

        :id: 4c009db9-d720-429e-8150-bebf246d3a43

        :expectedresults: A host is updated with a new IP address

        :CaseImportance: Critical
        """
        host = entities.Host(ip=gen_ipaddr()).create()
        new_ip = gen_ipaddr()
        host.ip = new_ip
        host = host.update(['ip'])
        self.assertEqual(host.ip, new_ip)

    @tier2
    def test_positive_update_hostgroup(self):
        """Update a host with a new hostgroup

        :id: dbe15f9a-242e-40f1-be90-d4f135596790

        :expectedresults: A host is updated with a new hostgroup

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        content_view = entities.ContentView(organization=org).create()
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], environment_id=lce.id)
        loc = entities.Location(organization=[org]).create()
        hostgroup = entities.HostGroup(location=[loc], organization=[org]).create()
        host = entities.Host(
            hostgroup=hostgroup,
            location=loc,
            organization=org,
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lce.id,
            },
        ).create()
        new_hostgroup = entities.HostGroup(
            location=[host.location], organization=[host.organization]
        ).create()
        host.hostgroup = new_hostgroup
        host.content_facet_attributes = {
            'content_view_id': content_view.id,
            'lifecycle_environment_id': lce.id,
        }
        host = host.update(['hostgroup', 'content_facet_attributes'])
        self.assertEqual(host.hostgroup.read().name, new_hostgroup.name)

    @tier1
    def test_positive_update_puppet_proxy(self):
        """Update a host with a new puppet proxy

        :id: 98c11e9b-54b0-4f1f-819c-4ff1863457ff

        :expectedresults: A host is updated with a new puppet proxy

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        new_proxy = entities.SmartProxy().search(
            query={'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host.puppet_proxy = new_proxy
        host = host.update(['puppet_proxy'])
        self.assertEqual(host.puppet_proxy.read().name, new_proxy.name)

    @tier1
    def test_positive_update_puppet_ca_proxy(self):
        """Update a host with a new puppet CA proxy

        :id: 82eacf60-cf89-4035-ad9a-3f78ceb41d39

        :expectedresults: A host is updated with a new puppet CA proxy

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        new_proxy = entities.SmartProxy().search(
            query={'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host.puppet_ca_proxy = new_proxy
        host = host.update(['puppet_ca_proxy'])
        self.assertEqual(host.puppet_ca_proxy.read().name, new_proxy.name)

    @tier1
    def test_positive_update_puppet_class(self):
        """Update a host with a new puppet classes

        :id: 73f9efce-3807-4196-b4e3-a6bfbfe95c99

        :expectedresults: A host is update with a new puppet classes

        :CaseImportance: Critical
        """
        host = entities.Host(organization=self.org, location=self.loc).create()
        self.assertEqual(len(host.puppetclass), 0)
        host.environment = self.env
        host.puppetclass = self.puppet_classes
        host = host.update(['environment', 'puppetclass'])
        self.assertEqual(
            {puppet_class.id for puppet_class in host.puppetclass},
            {puppet_class.id for puppet_class in self.puppet_classes},
        )

    @tier2
    def test_positive_update_subnet(self):
        """Update a host with a new subnet

        :id: c938e6b2-dbc0-4cd2-894a-8f2cc0e31063

        :expectedresults: A host is updated with a new subnet

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        old_subnet = entities.Subnet(location=[loc], organization=[org]).create()
        host = entities.Host(location=loc, organization=org, subnet=old_subnet).create()
        new_subnet = entities.Subnet(location=[loc], organization=[org]).create()
        host.subnet = new_subnet
        host = host.update(['subnet'])
        self.assertEqual(host.subnet.read().name, new_subnet.name)

    @tier2
    def test_positive_update_compresource(self):
        """Update a host with a new compute resource

        :id: 422f5db1-4eb6-43c2-a908-af9f8b5358f0

        :expectedresults: A host is updated with a new compute resource

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        compute_resource = entities.LibvirtComputeResource(
            location=[loc], organization=[org]
        ).create()
        host = entities.Host(
            compute_resource=compute_resource, location=loc, organization=org
        ).create()
        new_compresource = entities.LibvirtComputeResource(
            location=[host.location], organization=[host.organization]
        ).create()
        host.compute_resource = new_compresource
        host = host.update(['compute_resource'])
        self.assertEqual(host.compute_resource.read().name, new_compresource.name)

    @tier2
    def test_positive_update_model(self):
        """Update a host with a new model

        :id: da584445-ec24-4bed-82d0-d964bafa49bf

        :expectedresults: A host is updated with a new model

        :CaseLevel: Integration
        """
        host = entities.Host(model=entities.Model().create()).create()
        new_model = entities.Model().create()
        host.model = new_model
        host = host.update(['model'])
        self.assertEqual(host.model.read().name, new_model.name)

    @tier2
    def test_positive_update_user(self):
        """Update a host with a new user

        :id: afb3a9d1-61ba-43c4-a00f-a1887441b8d0

        :expectedresults: A host is updated with a new user

        :CaseLevel: Integration
        """
        user = entities.User(organization=[self.org], location=[self.loc]).create()
        host = entities.Host(
            owner=user, owner_type='User', organization=self.org, location=self.loc
        ).create()
        new_user = entities.User(organization=[self.org], location=[self.loc]).create()
        host.owner = new_user
        host = host.update(['owner'])
        self.assertEqual(host.owner.read(), new_user)

    @tier2
    def test_positive_update_usergroup(self):
        """Update a host with a new user group

        :id: a8d702ee-592a-4b5d-9fec-2fa07d3fda1b

        :expectedresults: A host is updated with a new user group

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        role = entities.Role().create()
        user = entities.User(location=[loc], organization=[org], role=[role]).create()
        usergroup = entities.UserGroup(role=[role], user=[user]).create()
        host = entities.Host(
            location=loc, organization=org, owner=usergroup, owner_type='Usergroup'
        ).create()
        new_usergroup = entities.UserGroup(role=[role], user=[user]).create()
        host.owner = new_usergroup
        host = host.update(['owner'])
        self.assertEqual(host.owner.read().name, new_usergroup.name)

    @tier1
    def test_positive_update_build_parameter(self):
        """Update a host with a new 'build' parameter value.
        Build parameter determines whether to enable the host for provisioning

        :id: f176ebc9-0406-4a7e-8e20-5325808d33db

        :expectedresults: A host is updated with a new 'build' parameter value

        :CaseImportance: Critical
        """
        for build in (True, False):
            with self.subTest(build):
                host = entities.Host(build=build).create()
                host.build = not build
                host = host.update(['build'])
                self.assertEqual(host.build, not build)

    @tier1
    def test_positive_update_enabled_parameter(self):
        """Update a host with a new 'enabled' parameter value.
        Enabled parameter determines whether to include the host within
        Satellite 6 reporting

        :id: 8a84e842-3537-46d5-8275-1c593c2171b3

        :expectedresults: A host is updated with a new 'enabled' parameter
            value

        :CaseImportance: Critical
        """
        for enabled in (True, False):
            with self.subTest(enabled):
                host = entities.Host(enabled=enabled).create()
                host.enabled = not enabled
                host = host.update(['enabled'])
                self.assertEqual(host.enabled, not enabled)

    @tier1
    def test_positive_update_managed_parameter(self):
        """Update a host with a new 'managed' parameter value
        Managed flag shows whether the host is managed or unmanaged and
        determines whether some extra parameters are required

        :id: 623064aa-db84-4470-ac13-63f32d9f81b6

        :expectedresults: A host is updated with a new 'managed' parameter
            value

        :CaseImportance: Critical
        """
        for managed in (True, False):
            with self.subTest(managed):
                host = entities.Host(managed=managed).create()
                host.managed = not managed
                host = host.update(['managed'])
                self.assertEqual(host.managed, not managed)

    @tier1
    def test_positive_update_comment(self):
        """Update a host with a new comment

        :id: ceca20ce-5ecc-4f7f-b920-28b7bd74d351

        :expectedresults: A host is updated with a new comment

        :CaseImportance: Critical
        """
        for new_comment in valid_data_list():
            with self.subTest(new_comment):
                host = entities.Host(comment=gen_string('alpha')).create()
                host.comment = new_comment
                host = host.update(['comment'])
                self.assertEqual(host.comment, new_comment)

    @tier2
    def test_positive_update_compute_profile(self):
        """Update a host with a new compute profile

        :id: a634c8a5-11ef-4d92-9df1-1f7e065f162e

        :expectedresults: A host is updated with a new compute profile

        :CaseLevel: Integration
        """
        host = entities.Host(compute_profile=entities.ComputeProfile().create()).create()
        new_cprofile = entities.ComputeProfile().create()
        host.compute_profile = new_cprofile
        host = host.update(['compute_profile'])
        self.assertEqual(host.compute_profile.read().name, new_cprofile.name)

    @tier2
    def test_positive_update_content_view(self):
        """Update a host with a new content view

        :id: f51612fd-cbbc-4f9f-b85b-a4104a0501e5

        :expectedresults: A host is updated with a new content view

        :CaseLevel: Integration
        """
        host = entities.Host(organization=self.org, location=self.loc).create()
        self.assertFalse(hasattr(host, 'content_facet_attributes'))
        host.content_facet_attributes = {
            'content_view_id': self.cv.id,
            'lifecycle_environment_id': self.lce.id,
        }
        host = host.update(['content_facet_attributes'])
        self.assertEqual(host.content_facet_attributes['content_view_id'], self.cv.id)
        self.assertEqual(host.content_facet_attributes['lifecycle_environment_id'], self.lce.id)

    @tier1
    def test_positive_update_host_parameters(self):
        """Update a host with a new host parameters

        :id: db0f5731-b0cc-4429-85fb-4032cb43ce4a

        :expectedresults: A host is updated with a new host parameters

        :CaseImportance: Critical
        """
        parameters = [{'name': gen_string('alpha'), 'value': gen_string('alpha')}]
        host = entities.Host(organization=self.org, location=self.loc).create()
        self.assertEqual(host.host_parameters_attributes, [])
        host.host_parameters_attributes = parameters
        host = host.update(['host_parameters_attributes'])
        self.assertEqual(host.host_parameters_attributes[0]['name'], parameters[0]['name'])
        self.assertEqual(host.host_parameters_attributes[0]['value'], parameters[0]['value'])
        self.assertIn('id', host.host_parameters_attributes[0])

    @tier2
    def test_positive_update_image(self):
        """Update a host with a new image

        :id: e5d8a5b0-7834-4099-9047-8290c7008931

        :expectedresults: A host is updated with a new image

        :CaseLevel: Integration
        """
        host = entities.Host(organization=self.org, location=self.loc).create()
        host = entities.Host(
            organization=self.org, location=self.loc, compute_resource=self.compresource_libvirt
        ).create()
        self.assertIsNone(host.image)
        host.image = self.image
        host = host.update(['image'])
        self.assertEqual(host.image.id, self.image.id)

    @tier1
    def test_negative_update_name(self):
        """Attempt to update a host with invalid or empty name

        :id: 1c46b44c-a2ea-43a6-b4d9-244101b081e8

        :expectedresults: A host is not updated

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                host.name = new_name
                with self.assertRaises(HTTPError):
                    host.update(['name'])
                self.assertNotEqual(
                    host.read().name, u'{0}.{1}'.format(new_name, host.domain.read().name).lower()
                )

    @tier1
    def test_negative_update_mac(self):
        """Attempt to update a host with invalid or empty MAC address

        :id: 1954ea4e-e0c2-475f-af67-557e91ebc1e2

        :expectedresults: A host is not updated

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        for new_mac in invalid_values_list():
            with self.subTest(new_mac):
                host.mac = new_mac
                with self.assertRaises(HTTPError):
                    host.update(['mac'])
                self.assertNotEqual(host.read().mac, new_mac)

    @tier2
    def test_negative_update_arch(self):
        """Attempt to update a host with an architecture, which does not belong
        to host's operating system

        :id: 07b9c0e7-f02b-4aff-99ae-5c203255aba1

        :expectedresults: A host is not updated

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        new_arch = entities.Architecture().create()
        host.architecture = new_arch
        with self.assertRaises(HTTPError):
            host = host.update(['architecture'])
        self.assertNotEqual(host.read().architecture.read().name, new_arch.name)

    @tier2
    def test_negative_update_os(self):
        """Attempt to update a host with an operating system, which is not
        associated with host's medium

        :id: 40e79f73-6356-4d61-9806-7ade2f4f8829

        :expectedresults: A host is not updated

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        new_os = entities.OperatingSystem(
            architecture=[host.architecture], ptable=[host.ptable]
        ).create()
        host.operatingsystem = new_os
        with self.assertRaises(HTTPError):
            host = host.update(['operatingsystem'])
        self.assertNotEqual(host.read().operatingsystem.read().name, new_os.name)

    @tier3
    def test_positive_read_content_source_id(self):
        """Read the host content_source_id attribute from the read request
        response

        :id: 0a7fd8d4-1ea8-4b21-8c46-10579644fd11

        :customerscenario: true

        :expectedresults: content_source_id is present in GET host request
            response

        :BZ: 1339613, 1488130

        :CaseLevel: System
        """
        proxy = (
            entities.SmartProxy()
            .search(query={'url': 'https://{0}:9090'.format(settings.server.hostname)})[0]
            .read()
        )
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        content_view = entities.ContentView(organization=self.org).create()
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], environment_id=lce.id)
        host = entities.Host(
            organization=self.org,
            location=self.loc,
            content_facet_attributes={
                'content_source_id': proxy.id,
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lce.id,
            },
        ).create()
        content_facet_attributes = getattr(host, 'content_facet_attributes')
        self.assertIsNotNone(content_facet_attributes)
        content_source_id = content_facet_attributes.get('content_source_id')
        self.assertIsNotNone(content_source_id)
        self.assertEqual(content_source_id, proxy.id)

    @tier3
    def test_positive_update_content_source_id(self):
        """Read the host content_source_id attribute from the update request
        response

        :id: d47214d2-a54c-4385-abfb-a0607ecb6ec7

        :customerscenario: true

        :expectedresults: content_source_id is present in PUT host request
            response

        :BZ: 1339613, 1488130

        :CaseLevel: System
        """
        proxy = entities.SmartProxy().search(
            query={'url': 'https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        content_view = entities.ContentView(organization=self.org).create()
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], environment_id=lce.id)
        host = entities.Host(
            organization=self.org,
            location=self.loc,
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lce.id,
            },
        ).create()
        host.content_facet_attributes['content_source_id'] = proxy.id
        # we need to ensure that content_source_id is returned by PUT request,
        # we will use entity update_json as entity update method will invoke
        # read method after PUT request completion
        response = host.update_json(['content_facet_attributes'])
        content_facet_attributes = response.get('content_facet_attributes')
        self.assertIsNotNone(content_facet_attributes)
        content_source_id = content_facet_attributes.get('content_source_id')
        self.assertIsNotNone(content_source_id)
        self.assertEqual(content_source_id, proxy.id)

    @upgrade
    @tier2
    def test_positive_read_enc_information(self):
        """Attempt to read host ENC information

        :id: 0d5047ab-2686-43de-8f04-cfe12b62eebf

        :customerscenario: true

        :expectedresults: host ENC information read successfully

        :BZ: 1362372

        :CaseLevel: Integration
        """
        # create 2 parameters
        host_parameters_attributes = []
        for _ in range(2):
            host_parameters_attributes.append(
                dict(name=gen_string('alpha'), value=gen_string('alphanumeric'))
            )
        host = entities.Host(
            organization=self.org,
            location=self.loc,
            environment=self.env,
            puppetclass=self.puppet_classes,
            content_facet_attributes={
                'content_view_id': self.cv.id,
                'lifecycle_environment_id': self.lce.id,
            },
            host_parameters_attributes=host_parameters_attributes,
        ).create()
        host_enc_info = host.enc()
        self.assertEqual(
            {puppet_class.name for puppet_class in self.puppet_classes},
            set(host_enc_info['data']['classes']),
        )
        self.assertEqual(host_enc_info['data']['environment'], self.env.name)
        self.assertIn('parameters', host_enc_info['data'])
        host_enc_parameters = host_enc_info['data']['parameters']
        self.assertEqual(host_enc_parameters['organization'], self.org.name)
        self.assertEqual(host_enc_parameters['location'], self.loc.name)
        self.assertEqual(host_enc_parameters['content_view'], self.cv.name)
        self.assertEqual(host_enc_parameters['lifecycle_environment'], self.lce.name)
        for param in host_parameters_attributes:
            self.assertIn(param['name'], host_enc_parameters)
            self.assertEqual(host_enc_parameters[param['name']], param['value'])

    @tier2
    @stubbed()
    def test_positive_add_future_subscription(self):
        """Attempt to add a future-dated subscription to a content host.

        :id: 603bb8eb-3435-4259-a036-400f2767de66

        :steps:

            1. Import a manifest with a future-dated subscription
            2. Add the subscription to the content host

        :expectedresults: The future-dated subscription was added to the host

        :CaseLevel: Integration
        """

    @upgrade
    @tier2
    @stubbed()
    def test_positive_add_future_subscription_with_ak(self):
        """Register a content host with an activation key that has a
        future-dated subscription.

        :id: f5286a44-0891-4605-8a6f-787f4754b3c0

        :steps:

            1. Import a manifest with a future-dated subscription
            2. Add the subscription to an activation key
            3. Register a new content host with the activation key

        :expectedresults: The host was registered and future subscription added

        :CaseLevel: Integration
        """

    @tier2
    @stubbed()
    def test_negative_auto_attach_future_subscription(self):
        """Run auto-attach on a content host, with a current and future-dated
        subscription.

        :id: f4a6feec-baf8-40c6-acb3-474b34419a62

        :steps:

            1. Import a manifest with a future-dated and current subscription
            2. Register a content host to the organization
            3. Run auto-attach on the content host

        :expectedresults: Only the current subscription was added to the host

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    def test_positive_create_baremetal_with_bios(self):
        """Create a new Host from provided MAC address

        :id: 9d74ed70-3197-4825-bf96-21eeb4a765f9

        :setup: Create a PXE-based VM with BIOS boot mode (outside of
            Satellite).

        :steps: Create a new host using 'BareMetal' option and MAC address of
            the pre-created VM

        :expectedresults: Host is created

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_baremetal_with_uefi(self):
        """Create a new Host from provided MAC address

        :id: 9b852c4d-a94f-4ba9-b666-ea4718320a42

        :setup: Create a PXE-based VM with UEFI boot mode (outside of
            Satellite).

        :steps: Create a new host using 'BareMetal' option and MAC address of
            the pre-created VM

        :expectedresults: Host is created

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_verify_files_with_pxegrub_uefi(self):
        """Provision a new Host and verify the tftp and dhcpd file
        structure is correct

        :id: 0c51c8ad-858c-44e1-8b14-8e0c52c29da1

        :steps:

            1. Associate a pxegrub-type provisioning template with the os
            2. Create new host (can be fictive bare metal) with the above OS
               and PXE loader set to Grub UEFI
            3. Build the host

        :expectedresults: Verify [/var/lib/tftpboot/] contains the following
            dir/file structure:

                grub/bootia32.efi
                grtest_positive_verify_files_with_pxegrub_uefiub/bootx64.efi
                grub/01-AA-BB-CC-DD-EE-FF
                grub/efidefault
                grub/shim.efi

            And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_verify_files_with_pxegrub_uefi_secureboot(self):
        """Provision a new Host and verify the tftp and dhcpd file structure is
        correct

        :id: ac4d535f-09bb-49db-b38b-90f9bad5fa19

        :steps:

            1. Associate a pxegrub-type provisioning template with the os
            2. Create new host (can be fictive bare metal) with the above OS
               and PXE loader set to Grub UEFI SecureBoot
            3. Build the host

        :expectedresults: Verify [/var/lib/tftpboot/] contains the following
            dir/file structure:

                grub/bootia32.efi
                grub/bootx64.efi
                grub/01-AA-BB-CC-DD-EE-FF
                grub/efidefault
                grub/shim.efi

            And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        :CaseAutomation: notautomated

        :CaseComponent: TFTP

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    def test_positive_verify_files_with_pxegrub2_uefi(self):
        """Provision a new UEFI Host and verify the tftp and dhcpd file
        structure is correct

        :id: fb951256-e173-4c2a-a812-92db80443cec

        :steps:
            1. Associate a pxegrub-type provisioning template with the os
            2. Create new host (can be fictive bare metal) with the above OS
               and PXE loader set to Grub2 UEFI
            3. Build the host

        :expectedresults: Verify [/var/lib/tftpboot/] contains the following
            dir/file structure:

                pxegrub2
                grub2/grub.cfg-01-aa-bb-cc-dd-ee-ff
                grub2/grub.cfg
                grub2/grubx32.efi
                grub2/grubx64.efi
                grub/shim.efi

            And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        :CaseAutomation: notautomated

        :CaseComponent: TFTP

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    def test_positive_verify_files_with_pxegrub2_uefi_secureboot(self):
        """Provision a new UEFI Host and verify the tftp and dhcpd file
        structure is correct

        :id: c0ea18df-d8c0-403a-b053-f5e500f8e3a3

        :steps:
            1. Associate a pxegrub-type provisioning template with the os
            2. Create new host (can be fictive bare metal) with the above OS
               and PXE loader set to Grub2 UEFI SecureBoot
            3. Build the host

        :expectedresults: Verify [/var/lib/tftpboot/] contains the following
            dir/file structure:

                pxegrub2
                grub2/grub.cfg-01-aa-bb-cc-dd-ee-ff
                grub2/grub.cfg
                grub2/grubx32.efi
                grub2/grubx64.efi
                grub/shim.efi

            And record in /var/lib/dhcpd/dhcpd.leases points to the bootloader

        :CaseAutomation: notautomated

        :CaseLevel: Integration

        :CaseComponent: TFTP
        """

    @tier1
    def test_positive_read_puppet_proxy_name(self):
        """Read a hostgroup created with puppet proxy and inspect server's
        response

        :id: 8825462e-f1dc-4054-b7fb-69c2b10722a2

        :expectedresults: Field 'puppet_proxy_name' is returned

        :BZ: 1371900

        :CaseImportance: Critical
        """
        proxy = entities.SmartProxy().search(
            query={'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host = entities.Host(puppet_proxy=proxy).create().read_json()
        self.assertIn('puppet_proxy_name', host)
        self.assertEqual(proxy.name, host['puppet_proxy_name'])

    @tier1
    def test_positive_read_puppet_ca_proxy_name(self):
        """Read a hostgroup created with puppet ca proxy and inspect server's
        response

        :id: 8941395f-8040-4705-a981-5da21c47efd1

        :expectedresults: Field 'puppet_ca_proxy_name' is returned

        :BZ: 1371900

        :CaseImportance: Critical
        """
        proxy = entities.SmartProxy().search(
            query={'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )[0]
        host = entities.Host(puppet_ca_proxy=proxy).create().read_json()
        self.assertIn('puppet_ca_proxy_name', host)
        self.assertEqual(proxy.name, host['puppet_ca_proxy_name'])

    @tier2
    def test_positive_search_by_org_id(self):
        """Search for host by specifying host's organization id

        :id: 56353f7c-b77e-4b6c-9ec3-51b58f9a18d8

        :customerscenario: true

        :expectedresults: Search functionality works as expected and correct
            result is returned

        :BZ: 1447958

        :CaseLevel: Integration
        """
        host = entities.Host().create()
        # adding org id as GET parameter for correspondence with BZ
        query = entities.Host()
        query._meta['api_path'] += '?organization_id={}'.format(host.organization.id)
        results = query.search()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, host.id)


class HostInterfaceTestCase(APITestCase):
    """Tests for Host Interfaces"""

    @classmethod
    def setUpClass(cls):
        """Create a host to reuse in tests"""
        super(HostInterfaceTestCase, cls).setUpClass()
        cls.host = entities.Host().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create an interface with different names and minimal input
        parameters

        :id: a45ee576-bec6-47a6-a018-a00e555eb2ad

        :expectedresults: An interface is created with expected name

        :CaseImportance: Critical
        """
        for name in valid_interfaces_list():
            with self.subTest(name):
                interface = entities.Interface(host=self.host, name=name).create()
                self.assertEqual(interface.name, name)

    @tier1
    def test_negative_create_with_name(self):
        """Attempt to create an interface with different invalid entries as
        names (>255 chars, unsupported string types)

        :id: 6fae26d8-8f62-41ba-a1cc-0185137ef70f

        :expectedresults: An interface is not created

        :CaseImportance: Critical
        """
        for name in invalid_interfaces_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError) as error:
                    entities.Interface(host=self.host, name=name).create()
                self.assertEqual(error.exception.response.status_code, 422)

    @tier1
    def test_positive_update_name(self):
        """Update interface name with different valid inputs

        :id: c5034b04-097e-47a4-908b-ee78de1699a4

        :expectedresults: Interface name is successfully updated

        :CaseImportance: Critical
        """
        interface = entities.Interface(host=self.host).create()
        for new_name in valid_interfaces_list():
            with self.subTest(new_name):
                interface.name = new_name
                interface = interface.update(['name'])
                self.assertEqual(interface.name, new_name)

    @tier1
    def test_negative_update_name(self):
        """Attempt to update interface name with different invalid entries
        (>255 chars, unsupported string types)

        :id: 6a1fb718-adfb-47cb-b28c-fb3cd01f99b0

        :expectedresults: An interface is not updated

        :CaseImportance: Critical
        """
        interface = entities.Interface(host=self.host).create()
        for new_name in invalid_interfaces_list():
            with self.subTest(new_name):
                interface.name = new_name
                with self.assertRaises(HTTPError) as error:
                    interface.update(['name'])
                self.assertNotEqual(interface.read().name, new_name)
                self.assertEqual(error.exception.response.status_code, 422)

    @tier1
    def test_positive_delete(self):
        """Delete host's interface (not primary)

        :id: 9bf83c3a-a4dc-420e-8d47-8572e5ae1dd6

        :expectedresults: An interface is successfully deleted

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        interface = entities.Interface(host=host).create()
        interface.delete()
        with self.assertRaises(HTTPError):
            interface.read()

    @tier1
    def test_negative_delete(self):
        """Attempt to delete host's primary interface

        :id: 716a9dfd-0f31-45aa-a6d1-42add032a15c

        :expectedresults: An interface is not deleted

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        primary_interface = next(
            interface for interface in host.interface if interface.read().primary
        )
        with self.assertRaises(HTTPError):
            primary_interface.delete()
        with self.assertNotRaises(HTTPError, expected_value=404):
            primary_interface.read()

    @upgrade
    @tier1
    def test_positive_delete_and_check_host(self):
        """Delete host's interface (not primary) and make sure the host was not
        accidentally removed altogether with the interface

        :BZ: 1285669

        :id: 3b3e9b3f-cfb2-433f-bd1f-0a8e1d9f0b34

        :expectedresults: An interface was successfully deleted, host was not
            deleted

        :CaseImportance: Critical
        """
        host = entities.Host().create()
        interface = entities.Interface(host=host, primary=False).create()
        interface.delete()
        with self.assertRaises(HTTPError):
            interface.read()
        with self.assertNotRaises(HTTPError, expected_value=404):
            host.read()
