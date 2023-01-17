"""
:Requirement: Computeresource RHV

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ComputeResources-RHEV

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from wait_for import wait_for
from wrapanapi import RHEVMSystem

from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import CLIReturnCodeError
from robottelo.cli.factory import make_compute_resource
from robottelo.cli.host import Host
from robottelo.config import settings


@pytest.fixture(scope='module')
def rhev():
    rhev = settings.rhev.copy()
    rhev.rhv_api = RHEVMSystem(
        hostname=rhev.hostname.split('/')[2],
        username=rhev.username,
        password=rhev.password,
        version='4.0',
        verify=False,
    )
    rhev.cluster_id = rhev.rhv_api.get_cluster(rhev.cluster).id
    rhev.storage_id = rhev.rhv_api.get_storage_domain(rhev.storage_domain).id
    rhev.quota = 'Default'
    return rhev


@pytest.mark.tier1
def test_positive_create_rhev_with_valid_name(rhev):
    """Create Compute Resource of type Rhev with valid name

    :id: 92a577db-144e-4761-a52e-e83887464986

    :expectedresults: Compute resource is created

    :CaseImportance: Critical

    :BZ: 1602835
    """
    ComputeResource.create(
        {
            'name': f'cr {gen_string(str_type="alpha")}',
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )


@pytest.mark.tier1
def test_positive_rhev_info(rhev):
    """List the info of RHEV compute resource

    :id: 1b18f6e8-c431-41ab-ae49-a2bbb74712f2

    :expectedresults: RHEV Compute resource Info is displayed

    :CaseImportance: Critical

    :BZ: 1602835
    """
    name = gen_string('utf8')
    compute_resource = make_compute_resource(
        {
            'name': name,
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )
    assert compute_resource['name'] == name


@pytest.mark.tier1
def test_positive_delete_by_name(rhev):
    """Delete the RHEV compute resource by name

    :id: ac84acbe-3e02-4f49-9695-b668df28b353

    :expectedresults: Compute resource is deleted

    :CaseImportance: Critical

    :BZ: 1602835
    """
    comp_res = make_compute_resource(
        {
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )
    assert comp_res['name']
    ComputeResource.delete({'name': comp_res['name']})
    result = ComputeResource.exists(search=('name', comp_res['name']))
    assert not result


@pytest.mark.tier1
def test_positive_delete_by_id(rhev):
    """Delete the RHEV compute resource by id

    :id: 4bcd4fa3-df8b-4773-b142-e47458116552

    :expectedresults: Compute resource is deleted

    :CaseImportance: Critical

    :BZ: 1602835
    """
    comp_res = make_compute_resource(
        {
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )
    assert comp_res['name']
    ComputeResource.delete({'id': comp_res['id']})
    result = ComputeResource.exists(search=('name', comp_res['name']))
    assert not result


@pytest.mark.tier2
def test_negative_create_rhev_with_url(rhev):
    """RHEV compute resource negative create with invalid values

    :id: 1f318a4b-8dca-491b-b56d-cff773ed624e

    :expectedresults: Compute resource is not created

    :CaseImportance: High
    """
    with pytest.raises(CLIReturnCodeError):
        ComputeResource.create(
            {
                'provider': 'Ovirt',
                'user': rhev.username,
                'password': rhev.password,
                'datacenter': rhev.datacenter,
                'url': 'invalid url',
            }
        )


@pytest.mark.tier2
def test_negative_create_with_same_name(rhev):
    """RHEV compute resource negative create with the same name

    :id: f00813ef-df31-462c-aa87-479b8272aea3

    :steps:

        1. Create a RHEV compute resource.
        2. Create another RHEV compute resource with same name.

    :expectedresults: Compute resource is not created

    :CaseImportance: High
    """
    name = gen_string('alpha')
    compute_resource = make_compute_resource(
        {
            'name': name,
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )
    assert compute_resource['name'] == name
    with pytest.raises(CLIFactoryError):
        make_compute_resource(
            {
                'name': name,
                'provider': 'Ovirt',
                'user': rhev.username,
                'password': rhev.password,
                'datacenter': rhev.datacenter,
                'url': rhev.hostname,
            }
        )


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_update_name(rhev):
    """RHEV compute resource positive update

    :id: 5ca29b81-d1f0-409f-843d-aa5daf957d7f

    :steps:

        1. Create a RHEV compute resource
        2. Update the name of the created compute resource

    :expectedresults: Compute Resource is successfully updated

    :CaseImportance: Critical

    :BZ: 1602835
    """
    new_name = gen_string('alpha')
    comp_res = make_compute_resource(
        {
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )
    assert comp_res['name']
    ComputeResource.update({'name': comp_res['name'], 'new-name': new_name})
    assert new_name == ComputeResource.info({'id': comp_res['id']})['name']


@pytest.mark.tier2
def test_positive_add_image_rhev_with_name(rhev, module_os):
    """Add images to the RHEV compute resource

    :id: 2da84165-a56f-4282-9343-94828fa69c13

    :setup: Images/templates should be present in RHEV-M itself,
        so that satellite can use them.

    :steps:

        1. Create a compute resource of type rhev.
        2. Create a image for the compute resource with valid parameter,
           compute-resource image create

    :expectedresults: The image is added to the CR successfully
    """
    if rhev.image_uuid is None:
        pytest.skip('Missing configuration for rhev.image_uuid')

    comp_res = make_compute_resource(
        {
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )
    assert comp_res['name']
    ComputeResource.image_create(
        {
            'compute-resource': comp_res['name'],
            'name': f'img {gen_string(str_type="alpha")}',
            'uuid': rhev.image_uuid,
            'operatingsystem': module_os.title,
            'architecture': rhev.image_arch,
            'username': "root",
        }
    )
    result = ComputeResource.image_list({'compute-resource': comp_res['name']})
    assert result[0]['uuid'] == rhev.image_uuid


@pytest.mark.skip_if_open("BZ:1829239")
@pytest.mark.tier2
def test_negative_add_image_rhev_with_invalid_uuid(rhev, module_os):
    """Attempt to add invalid image to the RHEV compute resource

    :id: e8a653f9-9749-4c76-95ed-2411a7c0a117

    :setup: Images/templates should be present in RHEV-M itself,
        so that satellite can use them.

    :steps:

        1. Create a compute resource of type rhev.
        2. Create a image for the compute resource with invalid value for
           uuid parameter, compute-resource image create.

    :expectedresults: The image should not be added to the CR

    :BZ: 1829239
    """
    comp_res = make_compute_resource(
        {
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )
    assert comp_res['name']
    with pytest.raises(CLIReturnCodeError):
        ComputeResource.image_create(
            {
                'compute-resource': comp_res['name'],
                'name': f'img {gen_string(str_type="alpha")}',
                'uuid': f'invalidimguuid {gen_string(str_type="alpha")}',
                'operatingsystem': module_os.title,
                'architecture': rhev.image_arch,
                'username': "root",
            }
        )


@pytest.mark.tier2
def test_negative_add_image_rhev_with_invalid_name(rhev, module_os):
    """Attempt to add invalid image name to the RHEV compute resource

    :id: 873a7d79-1e89-4e4f-81ca-b6db1e0246da

    :setup: Images/templates should be present in RHEV-M itself,
        so that satellite can use them.

    :steps:

        1. Create a compute resource of type rhev.
        2. Create a image for the compute resource with invalid value for
           name parameter, compute-resource image create.

    :expectedresults: The image should not be added to the CR

    """
    if rhev.image_uuid is None:
        pytest.skip('Missing configuration for rhev.image_uuid')

    comp_res = make_compute_resource(
        {
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
        }
    )

    assert comp_res['name']
    with pytest.raises(CLIReturnCodeError):
        ComputeResource.image_create(
            {
                'compute-resource': comp_res['name'],
                # too long string (>255 chars)
                'name': f'img {gen_string(str_type="alphanumeric", length=256)}',
                'uuid': rhev.image_uuid,
                'operatingsystem': module_os.title,
                'architecture': rhev.image_arch,
                'username': "root",
            }
        )


@pytest.mark.on_premises_provisioning
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_provision_rhev_with_host_group(
    request,
    module_provisioning_sat,
    rhev,
    module_sca_manifest_org,
    module_location,
    module_default_org_view,
    module_provisioning_rhel_content,
    module_lce_library,
    default_architecture,
    default_partitiontable,
):
    """Provision a host on RHEV compute resource with
    the help of hostgroup.

    :Requirement: Computeresource RHV

    :CaseComponent: ComputeResources-RHEV

    :Assignee: lhellebr

    :id: 97908521-3f4d-4207-93a3-23588b5a0a53

    :setup: Hostgroup and provisioning setup like domain, subnet etc.

    :steps:

        1. Create a RHEV compute resource.
        2. Create a host on RHEV compute resource using the Hostgroup
        3. Use compute-attributes parameter to specify key-value parameters
           regarding the virtual machine.
        4. Provision the host.

    :expectedresults: The host should be provisioned with host group

    :BZ: 1777992

    :customerscenario: true

    :CaseAutomation: Automated
    """
    cli = module_provisioning_sat.sat.cli
    cr_name = gen_string('alpha')
    org_name = module_sca_manifest_org.name
    loc_name = module_location.name
    rhv_cr = cli.ComputeResource.create(
        {
            'name': cr_name,
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
            'ovirt-quota': rhev.quota,
            'organizations': org_name,
            'locations': loc_name,
        }
    )
    assert rhv_cr['name'] == cr_name
    domain_name = module_provisioning_sat.domain.name
    subnet_name = module_provisioning_sat.subnet.name
    hostgroup = cli.HostGroup.create(
        {
            'name': gen_string('alpha'),
            'organization': org_name,
            'location': loc_name,
            'architecture': default_architecture.name,
            'domain': domain_name,
            'subnet': subnet_name,
            'content-source-id': module_provisioning_sat.domain.dns.id,
            'content-view-id': module_sca_manifest_org.default_content_view.id,
            'kickstart-repository-id': module_provisioning_rhel_content.ksrepo.id,
            'lifecycle-environment-id': module_sca_manifest_org.library.id,
            'operatingsystem': module_provisioning_rhel_content.os.title,
            'pxe-loader': "PXELinux BIOS",
            'partition-table': default_partitiontable.name,
            'compute-resource-id': rhv_cr.get('id'),
        }
    )
    host_name = gen_string('alpha').lower()
    host = cli.Host.create(
        {
            'name': f'{host_name}',
            'organization': org_name,
            'location': loc_name,
            'root-password': settings.provisioning.host_root_password,
            'pxe-loader': 'PXELinux BIOS',
            'hostgroup': hostgroup['name'],
            'compute-resource-id': rhv_cr.get('id'),
            'ip': None,
            'mac': None,
            'compute-attributes': f"cluster={rhev.cluster_id},"
            "cores=1,"
            "memory=4294967296,"  # 4 GiB
            "start=1",
            'interface': (
                f"compute_name=nic1, compute_network="
                f"{settings.rhev.network_prefix}{settings.provisioning.vlan_id}"
            ),
            'volume': f"size_gb=20,storage_domain={rhev.storage_domain},bootable=True",
            'provision-method': 'build',
        }
    )
    # cleanup
    request.addfinalizer(lambda: cli.Host.delete({'id': host['id']}))

    # checks
    hostname = f'{host_name}.{domain_name}'
    assert hostname == host['name']
    host_info = Host.info({'name': hostname})
    # Check on RHV, if VM exists
    assert rhev.rhv_api.does_vm_exist(hostname)
    # Get the information of created VM
    rhv_vm = rhev.rhv_api.get_vm(hostname)
    # Assert of Satellite mac address for VM and Mac of VM created is same
    assert host_info.get('network').get('mac') == rhv_vm.get_nics()[0].mac.address
    # Start to run a ping check if network was established on VM
    # If this fails, there's probably some issue with PXE booting or network setup in automation
    # TODO run the following check once https://github.com/SatelliteQE/broker/issues/161 is fixed
    # TODO note: host_provisioning_check has been changed to target_sat.ping_host(host=host_ip)
    # host_ip = host_info.get('network', {}).get('ipv4-address')
    # host_provisioning_check(ip_addr=host_ip)

    # Host should do call back to the Satellite reporting
    # the result of the installation. Wait until Satellite reports that the host is installed.
    exp_st = 'Pending installation'
    wait_for(
        lambda: cli.Host.info({'id': host['id']})['status']['build-status'] != exp_st,
        # timeout=200,  # no need to wait long, the host was already pingable
        timeout=4000,  # wait long because the ping check has not been done, TODO
        delay=10,
    )
    host = cli.Host.info({'id': host['id']})
    assert host['status']['build-status'] == 'Installed'


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_provision_rhev_without_host_group(rhev):
    """Provision a host on RHEV compute resource without
    the help of hostgroup.

    :id: 861940cb-1550-4f00-9df2-5a45683635b1

    :setup: Provisioning setup like domain, subnet etc.

    :steps:

        1. Create a RHEV compute resource.
        2. Create a host on RHEV compute resource.
        3. Use compute-attributes parameter to specify key-value parameters
           regarding the virtual machine.
        4. Provision the host.

    :expectedresults: The host should be provisioned successfully

    :CaseAutomation: NotAutomated

    :CaseLevel: Integration
    """


@pytest.mark.on_premises_provisioning
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete'], indirect=True)
def test_positive_provision_rhev_image_based_and_disassociate(
    request,
    module_provisioning_sat,
    rhev,
    module_org,
    module_location,
    module_provisioning_rhel_content,
    setting_update,
):
    """Provision a host on RHEV compute resource using image-based provisioning

    :Requirement: Computeresource RHV

    :CaseComponent: ComputeResources-RHEV

    :Assignee: lhellebr

    :id: ba78858f-5cff-462e-a35d-f5aa4d11db52

    :parametrized: yes

    :customerscenario: true

    :BZ: 1356126

    :setup: RHEV with a template on it

    :steps:

        1. Create a RHEV CR
        1. Create an image on that CR
        2. Create a new host using that CR and image
        3. Disassociate the host from the CR

    :expectedresults: Host should be provisioned with image, associated to CR, then disassociated

    :CaseAutomation: Automated
    """
    cli = module_provisioning_sat.sat.cli
    org_name = module_org.name
    loc_name = module_location.name
    name = gen_string('alpha')
    rhv_cr = cli.ComputeResource.create(
        {
            'name': name,
            'provider': 'Ovirt',
            'user': rhev.username,
            'password': rhev.password,
            'datacenter': rhev.datacenter,
            'url': rhev.hostname,
            'ovirt-quota': rhev.quota,
            'organizations': org_name,
            'locations': loc_name,
        }
    )
    assert rhv_cr['name'] == name
    host_name = gen_string('alpha').lower()
    # use some RHEL (usually latest)
    os = module_provisioning_rhel_content.os
    image = cli.ComputeResource.image_create(
        {
            'compute-resource': rhv_cr['name'],
            'name': f'img {gen_string(str_type="alpha")}',
            'uuid': rhev.image_uuid,
            'operatingsystem-id': os.id,
            'architecture': rhev.image_arch,
            'username': 'root',
            'password': rhev.image_password,
            'user-data': 'yes',  # so finish template won't be used
        }
    )
    domain_name = module_provisioning_sat.domain.name
    subnet_name = module_provisioning_sat.subnet.name
    host_name = gen_string('alpha').lower()
    host = None  # to avoid UnboundLocalError in finally block
    rhv_vm = None
    try:
        host = cli.Host.create(
            {
                'name': f'{host_name}',
                'organization': org_name,
                'location': loc_name,
                'root-password': settings.provisioning.host_root_password,
                'pxe-loader': 'PXELinux BIOS',
                'architecture': os.architecture[0].read().name,
                'domain': domain_name,
                'subnet': subnet_name,
                'compute-resource-id': rhv_cr.get('id'),
                'ip': None,
                'mac': None,
                'compute-attributes': f"cluster={rhev.cluster_id},"
                "cores=1,"
                "memory=4294967296,"  # 4 GiB
                "start=1",
                'interface': (
                    f"compute_name=nic1, compute_network="
                    f"{settings.rhev.network_prefix}{settings.provisioning.vlan_id}"
                ),
                # we already have a disk in image
                # 'volume': f"size_gb=20,storage_domain={rhev.storage_domain},bootable=True",
                'provision-method': 'image',
                'operatingsystem-id': os.id,
                'image-id': f'{image[0]["id"]}',
            }
        )
        hostname = f'{host_name}.{domain_name}'
        assert hostname == host['name']
        host_info = Host.info({'name': hostname})
        # Check on RHV, if VM exists
        assert rhev.rhv_api.does_vm_exist(hostname)
        # Get the information of created VM
        rhv_vm = rhev.rhv_api.get_vm(hostname)
        # Assert of Satellite mac address for VM and Mac of VM created is same
        assert host_info.get('network').get('mac') == rhv_vm.get_nics()[0].mac.address
        # Check the host is associated to the CR
        assert 'compute-resource' in host_info
        assert host_info['compute-resource'] == name
        # Done. Do not try to SSH, this image-based test should work even without
        # being in the same network as RHEV. We checked the VM exists and
        # that's enough.

        # Disassociate the host from the CR, check it's disassociated
        cli.Host.disassociate({'name': hostname})
        host_info = cli.Host.info({'name': hostname})
        assert 'compute-resource' not in host_info

    finally:

        # Now, let's just remove the host
        if host is not None:
            cli.Host.delete({'id': host['id']})
        # Delete the VM since the disassociated VM won't get deleted
        if rhv_vm is not None:
            rhv_vm.delete()
