"""Test class for Location CLI

:Requirement: Location

:CaseAutomation: Automated

:CaseComponent: OrganizationsandLocations

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError


def _proxy(request, target_sat):
    """Create a Proxy"""
    proxy = target_sat.cli_factory.make_proxy()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.Proxy.exists(search=('name', proxy['name'])):
            target_sat.cli.Proxy.delete(options={'id': proxy['id']})

    return proxy


def _location(request, target_sat, options=None):
    location = target_sat.cli_factory.make_location(options)

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.Location.exists(search=('id', location['id'])):
            target_sat.cli.Location.delete(options={'id': location['id']})

    return location


def _subnet(request, target_sat):
    subnet = target_sat.cli_factory.make_subnet()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.Subnet.exists(search=('name', subnet['name'])):
            target_sat.cli.Subnet.delete(options={'id': subnet['id']})

    return subnet


def _environment(request, target_sat):
    environment = target_sat.cli_factory.make_environment()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.Environment.exists(search=('name', environment['name'])):
            target_sat.cli.Environment.delete(options={'id': environment['id']})

    return environment


def _domain(request, target_sat):
    domain = target_sat.cli_factory.make_domain()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.Domain.exists(search=('name', domain['name'])):
            target_sat.cli.Domain.delete(options={'id': domain['id']})

    return domain


def _medium(request, target_sat):
    medium = target_sat.cli_factory.make_medium()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.Medium.exists(search=('name', medium['name'])):
            target_sat.cli.Medium.delete(options={'id': medium['id']})

    return medium


def _host_group(request, target_sat):
    host_group = target_sat.cli_factory.hostgroup()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.HostGroup.exists(search=('id', host_group['id'])):
            target_sat.cli.HostGroup.delete(options={'id': host_group['id']})

    return host_group


def _compute_resource(request, target_sat):
    compute_resource = target_sat.cli_factory.compute_resource(
        {
            'provider': 'Libvirt',
            'url': 'qemu+tcp://localhost:16509/system',
        }
    )

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.ComputeResource.exists(search=('id', compute_resource['id'])):
            target_sat.cli.ComputeResource.delete(options={'id': compute_resource['id']})

    return compute_resource


def _template(request, target_sat):
    template = target_sat.cli_factory.make_template()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.Template.exists(search=('name', template['name'])):
            target_sat.cli.Template.delete(options={'id': template['id']})

    return template


def _user(request, target_sat):
    user = target_sat.cli_factory.user()

    @request.addfinalizer
    def _cleanup():
        if target_sat.cli.User.exists(search=('login', user['login'])):
            target_sat.cli.User.delete(options={'id': user['id']})

    return user


class TestLocation:
    """Tests for Location via Hammer CLI"""

    @pytest.mark.e2e
    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_create_update_delete(self, request, target_sat):
        """Create new location with attributes, update and delete it

        :id: e1844d9d-ec4a-44b3-9743-e932cc70020d

        :BZ: 1233612, 1234287

        :expectedresults: Location created successfully and has expected and
            correct attributes. Attributes can be updated and the location
            can be deleted.

        :CaseImportance: Critical
        """
        # Create
        description = gen_string('utf8')
        subnet = _subnet(request, target_sat)
        domains = [_domain(request, target_sat) for _ in range(0, 2)]
        host_groups = [_host_group(request, target_sat) for _ in range(0, 3)]
        medium = _medium(request, target_sat)
        compute_resource = _compute_resource(request, target_sat)
        template = _template(request, target_sat)
        user = _user(request, target_sat)

        location = _location(
            request,
            target_sat,
            {
                'description': description,
                'subnet-ids': subnet['id'],
                'domain-ids': [domains[0]['id'], domains[1]['id']],
                'hostgroup-ids': [host_groups[0]['id'], host_groups[1]['id']],
                'medium-ids': medium['id'],
                'compute-resource-ids': compute_resource['id'],
                'provisioning-templates': template['name'],
                'user-ids': user['id'],
            },
        )

        assert location['description'][0] == description
        assert location['subnets'][0] == (
            f"{subnet['name']} ({subnet['network-addr']}/{subnet['network-prefix']})"
        )
        assert domains[0]['name'] in location['domains']
        assert domains[1]['name'] in location['domains']
        assert host_groups[0]['name'] in location['hostgroups']
        assert host_groups[1]['name'] in location['hostgroups']
        assert len(location['installation-media']) > 0
        assert location['installation-media'][0] == medium['name']
        assert location['compute-resources'][0] == compute_resource['name']
        assert len(location['templates']) >= 1

        template_search = (
            (f"{template['name']} ({template['type']})")
            if template.get('type')
            else template['name']
        )

        assert template_search in location['templates']
        assert location['users'][0] == user['login']

        # Update
        target_sat.cli.Location.update(
            {
                'id': location['id'],
                'domain-ids': domains[1]['id'],
                'hostgroup-ids': [host_groups[1]['id'], host_groups[2]['id']],
            }
        )
        location = target_sat.cli.Location.info({'id': location['id']})
        assert host_groups[1]['name'] in location['hostgroups']
        assert host_groups[2]['name'] in location['hostgroups']
        assert location['domains'][0] == domains[1]['name']

        # Delete
        target_sat.cli.Location.delete({'id': location['id']})
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.Location.info({'id': location['id']})

    @pytest.mark.tier1
    def test_positive_create_with_parent(self, request, target_sat):
        """Create new location with parent location specified

        :id: 49b34733-103a-4fee-818b-6a3386253af1

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location created successfully and has correct and
            expected parent location set

        """
        parent_location = _location(request, target_sat)
        location = _location(request, target_sat, {'parent-id': parent_location['id']})
        assert location['parent'] == parent_location['name']

    @pytest.mark.tier1
    def test_negative_create_with_same_name(self, request, target_sat):
        """Try to create location using same name twice

        :id: 4fbaea41-9775-40a2-85a5-4dc05cc95134

        :expectedresults: Second location is not created

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        location = _location(request, target_sat, options={'name': name})
        assert location['name'] == name
        with pytest.raises(CLIFactoryError):
            _location(request, target_sat, options={'name': name})

    @pytest.mark.tier1
    def test_negative_create_with_user_by_name(self, request, target_sat):
        """Try to create new location with incorrect user assigned to it
        Use user login as a parameter

        :id: fa892edf-8c42-44dc-8f36-bed50798b59b

        :expectedresults: Location is not created

        :CaseImportance: Critical
        """
        with pytest.raises(CLIFactoryError):
            _location(request, target_sat, options={'users': gen_string('utf8', 80)})

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_add_and_remove_capsule(self, request, target_sat):
        """Add a capsule to location and remove it

        :id: 15e3c1e6-4fa3-4965-8808-a9ba01d1c050

        :expectedresults: Capsule is added to the org

        :BZ: 1398695

        """
        location = _location(request, target_sat)
        proxy = _proxy(request, target_sat)

        target_sat.cli.Location.add_smart_proxy(
            {'name': location['name'], 'smart-proxy-id': proxy['id']}
        )
        location = target_sat.cli.Location.info({'name': location['name']})
        assert proxy['name'] in location['smart-proxies']

        target_sat.cli.Location.remove_smart_proxy(
            {'name': location['name'], 'smart-proxy': proxy['name']}
        )
        location = target_sat.cli.Location.info({'name': location['name']})
        assert proxy['name'] not in location['smart-proxies']

    @pytest.mark.tier1
    def test_positive_add_update_remove_parameter(self, request, target_sat):
        """Add, update and remove parameter to location

        :id: 61b564f2-a42a-48de-833d-bec3a127d0f5

        :expectedresults: Parameter is added to the location

        :CaseImportance: Critical
        """
        # Create
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        param_new_value = gen_string('alpha')
        location = _location(request, target_sat)
        target_sat.cli.Location.set_parameter(
            {'name': param_name, 'value': param_value, 'location-id': location['id']}
        )
        location = target_sat.cli.Location.info({'id': location['id']})
        assert len(location['parameters']) == 1
        assert param_value == location['parameters'][param_name.lower()]

        # Update
        target_sat.cli.Location.set_parameter(
            {'name': param_name, 'value': param_new_value, 'location': location['name']}
        )
        location = target_sat.cli.Location.info({'id': location['id']})
        assert len(location['parameters']) == 1
        assert param_new_value == location['parameters'][param_name.lower()]

        # Remove
        target_sat.cli.Location.delete_parameter({'name': param_name, 'location': location['name']})
        location = target_sat.cli.Location.info({'id': location['id']})
        assert len(location['parameters']) == 0
        assert param_name.lower() not in location['parameters']

    @pytest.mark.tier2
    def test_positive_update_parent(self, request, target_sat):
        """Update location's parent location

        :id: 34522d1a-1190-48d8-9285-fc9a9bcf6c6a

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location was updated successfully

        :CaseImportance: High
        """
        parent_location = _location(request, target_sat)
        location = _location(request, target_sat, {'parent-id': parent_location['id']})

        parent_location_2 = _location(request, target_sat)
        target_sat.cli.Location.update({'id': location['id'], 'parent-id': parent_location_2['id']})
        location = target_sat.cli.Location.info({'id': location['id']})
        assert location['parent'] == parent_location_2['name']

    @pytest.mark.tier1
    def test_negative_update_parent_with_child(self, request, target_sat):
        """Attempt to set child location as a parent and vice versa

        :id: fd4cb1cf-377f-4b48-b7f4-d4f6ca56f544

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location was not updated

        :CaseImportance: High
        """
        parent_location = _location(request, target_sat)
        location = _location(request, target_sat, {'parent-id': parent_location['id']})

        # set parent as child
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.Location.update(
                {'id': parent_location['id'], 'parent-id': location['id']}
            )
        parent_location = target_sat.cli.Location.info({'id': parent_location['id']})
        assert parent_location.get('parent') is None

        # set child as parent
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.Location.update({'id': location['id'], 'parent-id': location['id']})
        location = target_sat.cli.Location.info({'id': location['id']})
        assert location['parent'] == parent_location['name']
