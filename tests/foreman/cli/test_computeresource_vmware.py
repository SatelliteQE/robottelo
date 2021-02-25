"""
:Requirement: Computeresource Vmware

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-VMWare

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.factory import make_compute_resource
from robottelo.cli.org import Org
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import VMWARE_CONSTANTS

pytestmark = pytest.mark.on_premises_provisioning


@pytest.fixture(scope='module')
def vmware(module_org, module_location):
    vmware = type('vmware', (object,), {})()
    vmware.org = module_org
    vmware.loc = module_location
    Org.add_location({'id': vmware.org.id, 'location-id': vmware.loc.id})
    vmware.vmware_server = settings.vmware.vcenter
    vmware.vmware_password = settings.vmware.password
    vmware.vmware_username = settings.vmware.username
    vmware.vmware_datacenter = settings.vmware.datacenter
    vmware.vmware_img_name = settings.vmware.image_name
    vmware.vmware_img_arch = settings.vmware.image_arch
    vmware.vmware_img_os = settings.vmware.image_os
    vmware.vmware_img_user = settings.vmware.image_username
    vmware.vmware_img_pass = settings.vmware.image_password
    vmware.vmware_vm_name = settings.vmware.vm_name
    vmware.current_interface = (
        VMWARE_CONSTANTS.get('network_interfaces') % settings.vlan_networking.bridge
    )
    return vmware


@pytest.mark.tier1
def test_positive_create_with_server(vmware):
    """Create VMware compute resource with server field

    :id: a06b02c4-fe6a-44ef-bf61-5a28c3905527

    :customerscenario: true

    :expectedresults: Compute resource is created, server field saved
        correctly

    :BZ: 1387917

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    vmware_cr = make_compute_resource(
        {
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': vmware.vmware_server,
            'user': vmware.vmware_username,
            'password': vmware.vmware_password,
            'datacenter': vmware.vmware_datacenter,
        }
    )
    assert vmware_cr['name'] == cr_name
    assert vmware_cr['server'] == vmware.vmware_server


@pytest.mark.tier1
def test_positive_create_with_org(vmware):
    """Create VMware Compute Resource with organizations

    :id: 807a1f70-4cc3-4925-b145-0c3b26c57559

    :customerscenario: true

    :expectedresults: VMware Compute resource is created

    :BZ: 1387917

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    vmware_cr = make_compute_resource(
        {
            'name': cr_name,
            'organization-ids': vmware.org.id,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': vmware.vmware_server,
            'user': vmware.vmware_username,
            'password': vmware.vmware_password,
            'datacenter': vmware.vmware_datacenter,
        }
    )
    assert vmware_cr['name'] == cr_name


@pytest.mark.tier1
def test_positive_create_with_loc(vmware):
    """Create VMware Compute Resource with locations

    :id: 214a0f54-6fc2-4e7b-91ab-a45760ffb2f2

    :customerscenario: true

    :expectedresults: VMware Compute resource is created

    :BZ: 1387917

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    vmware_cr = make_compute_resource(
        {
            'name': cr_name,
            'location-ids': vmware.loc.id,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': vmware.vmware_server,
            'user': vmware.vmware_username,
            'password': vmware.vmware_password,
            'datacenter': vmware.vmware_datacenter,
        }
    )
    assert vmware_cr['name'] == cr_name


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_with_org_and_loc(vmware):
    """Create VMware Compute Resource with organizations and locations

    :id: 96faae3f-bc64-4147-a9fc-09c858e0a68f

    :customerscenario: true

    :expectedresults: VMware Compute resource is created

    :BZ: 1387917

    :CaseAutomation: Automated

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    vmware_cr = make_compute_resource(
        {
            'name': cr_name,
            'organization-ids': vmware.org.id,
            'location-ids': vmware.loc.id,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': vmware.vmware_server,
            'user': vmware.vmware_username,
            'password': vmware.vmware_password,
            'datacenter': vmware.vmware_datacenter,
        }
    )
    assert vmware_cr['name'] == cr_name
