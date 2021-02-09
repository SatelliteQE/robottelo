"""Test for Compute Resource UI

:Requirement: Computeresource

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: ComputeResources

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
import requests
from nailgun import entities
from wait_for import wait_for

from robottelo.api.utils import check_create_os_with_title
from robottelo.config import settings
from robottelo.constants import COMPUTE_PROFILE_LARGE
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.datafactory import gen_string
from robottelo.decorators import setting_is_set
from robottelo.decorators import skip_if_not_set


# TODO mark this on the module with a lambda for skip condition
# so that this is executed during the session at run loop, instead of at module import
if not setting_is_set('rhev'):
    pytest.skip('skipping tests due to missing rhev settings', allow_module_level=True)


@pytest.fixture(scope='module')
def module_ca_cert():
    return (
        None
        if settings.rhev.ca_cert is None
        else requests.get(settings.rhev.ca_cert).content.decode()
    )


@pytest.fixture(scope='module')
def rhev_data():
    return {
        'rhev_url': settings.rhev.hostname,
        'username': settings.rhev.username,
        'password': settings.rhev.password,
        'datacenter': settings.rhev.datacenter,
        'vm_name': settings.rhev.vm_name,
        'image_name': settings.rhev.image_name,
        'image_os': settings.rhev.image_os,
        'image_arch': settings.rhev.image_arch,
        'image_username': settings.rhev.image_username,
        'image_password': settings.rhev.image_password,
        'storage_domain': settings.rhev.storage_domain,
    }


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_loc():
    return entities.Location().create()


@pytest.mark.tier2
@pytest.mark.parametrize('version', [True, False])
def test_positive_end_to_end(session, rhev_data, module_org, module_loc, module_ca_cert, version):
    """Perform end to end testing for compute resource RHEV.

    :id: 3c079675-e5d3-490e-9b7e-1c2950f9965d

    :parametrized: yes

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    with session:
        session.computeresource.create(
            {
                'name': name,
                'description': description,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': version,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        resource_values = session.computeresource.read(name)
        assert resource_values['name'] == name
        assert resource_values['description'] == description
        assert resource_values['provider'] == FOREMAN_PROVIDERS['rhev']
        assert resource_values['provider_content']['user'] == rhev_data['username']
        assert (
            resource_values['provider_content']['datacenter']['value'] == rhev_data['datacenter']
        )
        assert resource_values['provider_content']['api4'] == version
        session.computeresource.edit(name, {'name': new_name})
        assert not session.computeresource.search(name)
        assert session.computeresource.search(new_name)[0]['Name'] == new_name
        session.computeresource.delete(new_name)
        assert not session.computeresource.search(new_name)


@pytest.mark.tier2
@pytest.mark.parametrize('version', [True, False])
def test_positive_add_resource(session, module_ca_cert, rhev_data, version):
    """Create new RHEV Compute Resource using APIv3/APIv4 and autoloaded cert

    :id: f75e994a-6da1-40a3-9685-42387388b300

    :parametrized: yes

    :expectedresults: resource created successfully and has expected protocol
        version

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    # Our RHEV testing uses custom cert which we specify manually.
    # That means we're not testing the ability to automatically fill a
    # self-signed certificate upon clicking Load Datacenters / Test Connection.
    name = gen_string('alpha')
    with session:
        session.computeresource.create(
            {
                'name': name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': version,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        resource_values = session.computeresource.read(name)
        assert resource_values['name'] == name
        assert resource_values['provider_content']['api4'] == version


@pytest.mark.tier2
@pytest.mark.parametrize('version', [True, False])
def test_positive_edit_resource_description(session, module_ca_cert, rhev_data, version):
    """Edit RHEV Compute Resource with another description

    :id: f75544b1-3943-4cc6-98d1-f2d0fbe7244c

    :parametrized: yes

    :expectedresults: resource updated successfully and has new description

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    description = gen_string('alpha')
    new_description = gen_string('alpha')
    with session:
        session.computeresource.create(
            {
                'name': name,
                'description': description,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': version,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        resource_values = session.computeresource.read(name)
        assert resource_values['description'] == description
        session.computeresource.edit(name, {'description': new_description})
        resource_values = session.computeresource.read(name)
        assert resource_values['description'] == new_description


@pytest.mark.tier2
@pytest.mark.parametrize('version', [True, False])
def test_positive_list_resource_vms(session, module_ca_cert, rhev_data, version):
    """List VMs for RHEV Compute Resource

    :id: eea2f2b1-e9f4-448d-8c54-51fb25af3d5f

    :parametrized: yes

    :expectedresults: VMs listed for provided compute resource

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    with session:
        session.computeresource.create(
            {
                'name': name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': version,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        vm = session.computeresource.list_vms(name, rhev_data['vm_name'])
        assert vm['Name'].read() == rhev_data['vm_name']


@pytest.mark.tier2
def test_positive_edit_resource_version(session, module_ca_cert, rhev_data):
    """Edit RHEV Compute Resource with another protocol version

    :id: 6e7985b6-a605-4fb8-8710-17a046bdac53

    :expectedresults: resource updated successfully and switched to another
        protocol version

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    with session:
        session.computeresource.create(
            {
                'name': name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': False,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        resource_values = session.computeresource.read(name)
        assert not resource_values['provider_content']['api4']
        session.computeresource.edit(name, {'provider_content.api4': True})
        resource_values = session.computeresource.read(name)
        assert resource_values['provider_content']['api4']


@pytest.mark.tier2
@pytest.mark.parametrize('version', [True, False])
@pytest.mark.run_in_one_thread
def test_positive_resource_vm_power_management(session, module_ca_cert, rhev_data, version):
    """Read current RHEV Compute Resource virtual machine power status and
    change it to opposite one

    :id: 47aea4b7-9258-4863-8966-900bc9e94116

    :parametrized: yes

    :expectedresults: virtual machine is powered on or powered off depending on
        its initial state

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    with session:
        session.computeresource.create(
            {
                'name': name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': version,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        status = session.computeresource.vm_status(name, rhev_data['vm_name'])
        if status:
            session.computeresource.vm_poweroff(name, rhev_data['vm_name'])
        else:
            session.computeresource.vm_poweron(name, rhev_data['vm_name'])

        wait_for(
            lambda: (
                session.browser.refresh(),
                session.computeresource.vm_status(name, rhev_data['vm_name']),
            )[1]
            is not status,
            timeout=180,
            delay=1,
        )
        assert session.computeresource.vm_status(name, rhev_data['vm_name']) is not status


@pytest.mark.tier3
@pytest.mark.parametrize('version', [True, False])
def test_positive_VM_import(session, module_ca_cert, module_org, module_loc, rhev_data, version):
    """Import an existing VM as a Host

    :id: 47aea4b7-9258-4863-8966-9a0bc9e94116

    :parametrized: yes

    :expectedresults: VM is shown as Host in Foreman

    :CaseLevel: Integration

    :CaseImportance: Medium

    :BZ: 1636067
    """
    # create entities for hostgroup
    default_loc_id = entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0].id
    entities.SmartProxy(id=1, location=[default_loc_id, module_loc.id]).update()
    domain = entities.Domain(organization=[module_org.id], location=[module_loc]).create()
    subnet = entities.Subnet(
        organization=[module_org.id], location=[module_loc], domain=[domain]
    ).create()
    architecture = entities.Architecture().create()
    ptable = entities.PartitionTable(organization=[module_org.id], location=[module_loc]).create()
    operatingsystem = entities.OperatingSystem(
        architecture=[architecture], ptable=[ptable]
    ).create()
    medium = entities.Media(
        organization=[module_org.id], location=[module_loc], operatingsystem=[operatingsystem]
    ).create()
    le = (
        entities.LifecycleEnvironment(name="Library", organization=module_org.id)
        .search()[0]
        .read()
        .id
    )
    cv = entities.ContentView(organization=[module_org.id]).create()
    cv.publish()

    # create hostgroup
    hostgroup_name = gen_string('alpha')
    entities.HostGroup(
        name=hostgroup_name,
        architecture=architecture,
        domain=domain,
        subnet=subnet,
        location=[module_loc.id],
        medium=medium,
        operatingsystem=operatingsystem,
        organization=[module_org],
        ptable=ptable,
        lifecycle_environment=le,
        content_view=cv,
        content_source=1,
    ).create()

    name = gen_string('alpha')
    with session:

        session.computeresource.create(
            {
                'name': name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': version,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
                'locations.resources.assigned': [module_loc.name],
            }
        )
        session.hostgroup.update(hostgroup_name, {'host_group.deploy': name + " (RHV)"})
        session.computeresource.vm_import(
            name, rhev_data['vm_name'], hostgroup_name, module_loc.name
        )
        assert session.host.search(rhev_data['vm_name']) is not None
    # disassociate the host so the corresponding VM doesn't get removed from the CR on host delete
    entities.Host().search(query={'search': f"name~{rhev_data['vm_name']}"})[0].disassociate()
    entities.Host(name=rhev_data['vm_name']).search()[0].delete()


@pytest.mark.tier3
@pytest.mark.parametrize('version', [True, False])
def test_positive_update_organization(session, rhev_data, module_loc, module_ca_cert, version):
    """Update a rhev Compute Resource organization

    :id: f6656c8e-70a3-40e5-8dda-2154f2eeb042

    :parametrized: yes

    :setup: rhev hostname and credentials.

    :steps:

        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Provide a valid name to rhev Compute Resource.
        4. Test the connection using Load Datacenter and submit.
        5. Create a new organization.
        6. Add the new CR to organization that is created.

    :CaseAutomation: Automated

    :CaseImportance: Medium

    :expectedresults: The rhev Compute Resource is updated
    """
    name = gen_string('alpha')
    new_organization = entities.Organization().create()
    with session:
        session.computeresource.create(
            {
                'name': name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.api4': version,
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        assert session.computeresource.search(name)[0]['Name'] == name
        session.computeresource.edit(
            name, {'organizations.resources.assigned': [new_organization.name]}
        )
        session.organization.select(new_organization.name)
        resource_values = session.computeresource.read(name)
        assert new_organization.name in resource_values['organizations']['resources']['assigned']


@pytest.mark.tier2
def test_positive_image_end_to_end(session, rhev_data, module_loc, module_ca_cert):
    """Perform end to end testing for compute resource RHV component image.

    :id: 62a5c52f-dd15-45e7-8200-c64bb335474f

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    cr_name = gen_string('alpha')
    image_name = gen_string('alpha')
    new_image_name = gen_string('alpha')
    check_create_os_with_title(rhev_data['image_os'])
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        session.computeresource.create_image(
            cr_name,
            dict(
                name=image_name,
                operating_system=rhev_data['image_os'],
                architecture=rhev_data['image_arch'],
                username=rhev_data['image_username'],
                user_data=False,
                password=rhev_data['image_password'],
                image=rhev_data['image_name'],
            ),
        )
        values = session.computeresource.read_image(cr_name, image_name)
        assert values['name'] == image_name
        assert values['operating_system'] == rhev_data['image_os']
        assert values['architecture'] == rhev_data['image_arch']
        assert values['username'] == rhev_data['image_username']
        assert values['user_data'] is False
        assert values['image'] == rhev_data['image_name']
        session.computeresource.update_image(cr_name, image_name, dict(name=new_image_name))
        assert session.computeresource.search_images(cr_name, image_name)[0] != image_name
        assert (
            session.computeresource.search_images(cr_name, new_image_name)[0]['Name']
            == new_image_name
        )
        session.computeresource.delete_image(cr_name, new_image_name)
        assert (
            session.computeresource.search_images(cr_name, new_image_name)[0]['Name']
            != new_image_name
        )


@skip_if_not_set('vlan_networking')
@pytest.mark.tier2
def test_positive_associate_with_custom_profile(session, rhev_data, module_ca_cert):
    """ "Associate custom default (3-Large) compute profile to RHV compute resource.

    :id: e7698154-62ff-492b-8e56-c5dc70f0c9df

    :customerscenario: true

    :setup: rhev hostname and credentials.

    :steps:

        1. Create a compute resource of type RHV.
        2. Provide it with the valid hostname, username and password.
        3. Select the created rhv CR.
        4. Click Compute Profile tab.
        5. Edit (3-Large) with valid configurations and submit.

    :expectedresults: The Compute Resource created and associated to compute profile (3-Large)
        with provided values.

    :BZ: 1286033

    :CaseAutomation: Automated
    """
    cr_name = gen_string('alpha')
    cr_profile_data = dict(
        cluster=rhev_data['datacenter'],
        cores='2',
        sockets='2',
        memory='1 GB',
        network_interfaces=[
            dict(name='nic1', network=settings.vlan_networking.bridge),
            dict(name='nic2', network=settings.vlan_networking.bridge),
            dict(name='nic3', network=settings.vlan_networking.bridge),
        ],
        storage=[
            dict(size='10', bootable=False, preallocate_disk=True),
            dict(size='20', bootable=True, preallocate_disk=True),
            dict(size='5', bootable=False, preallocate_disk=False),
        ],
    )
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        session.computeresource.update_computeprofile(
            cr_name,
            COMPUTE_PROFILE_LARGE,
            {f'provider_content.{key}': value for key, value in cr_profile_data.items()},
        )
        provider_content_values = session.computeresource.read_computeprofile(
            cr_name, COMPUTE_PROFILE_LARGE
        )['provider_content']
        # assert main compute resource profile data updated updated successfully.
        excluded_keys = ['network_interfaces', 'storage']
        expected_value = {
            key: value for key, value in cr_profile_data.items() if key not in excluded_keys
        }
        provided_value = {
            key: value
            for key, value in provider_content_values.items()
            if key not in excluded_keys and key in cr_profile_data
        }
        assert provided_value == expected_value
        # assert compute resource profile network and storage data updated successfully.
        for excluded_key in excluded_keys:
            for index, expected_value in enumerate(cr_profile_data[excluded_key]):
                provided_value = {
                    key: value
                    for key, value in provider_content_values[excluded_key][index].items()
                    if key in expected_value
                }
                assert provided_value == expected_value


@pytest.mark.tier3
def test_positive_associate_with_custom_profile_with_template(session, rhev_data, module_ca_cert):
    """Associate custom default (3-Large) compute profile to rhev compute
     resource, with template

    :id: bb9794cc-6335-4621-92fd-fdc815f23263

    :setup: rhev hostname and credentials.

    :steps:

        1. Create a compute resource of type rhev.
        2. Provide it with the valid hostname, username and password.
        3. Select the created rhev CR.
        4. Click Compute Profile tab.
        5. Edit (3-Large) with valid configuration and template and submit.

    :expectedresults: The Compute Resource created and opened successfully

    :BZ: 1452534

    :CaseImportance: Medium

    :CaseAutomation: Automated
    """
    cr_name = gen_string('alpha')
    cr_profile_data = dict(
        cluster=rhev_data['datacenter'],
        template=f"{rhev_data['image_name']} (base version)",
        cores='2',
        memory='1 GB',
    )
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['rhev'],
                'provider_content.url': rhev_data['rhev_url'],
                'provider_content.user': rhev_data['username'],
                'provider_content.password': rhev_data['password'],
                'provider_content.datacenter.value': rhev_data['datacenter'],
                'provider_content.certification_authorities': module_ca_cert,
            }
        )
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        session.computeresource.update_computeprofile(
            cr_name,
            COMPUTE_PROFILE_LARGE,
            {f'provider_content.{key}': value for key, value in cr_profile_data.items()},
        )
        values = session.computeresource.read_computeprofile(cr_name, COMPUTE_PROFILE_LARGE)
        assert cr_profile_data == {
            key: value
            for key, value in values['provider_content'].items()
            if key in cr_profile_data
        }
