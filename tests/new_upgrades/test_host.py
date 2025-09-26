"""Test Host/Provisioning related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Endeavour

:CaseImportance: High

"""

import random

from box import Box
from fauxfactory import gen_alpha, gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_PTABLE,
    VALID_GCE_ZONES,
)
from robottelo.utils.shared_resource import SharedResource

"""The host can be provisioned on GCE CR created in previous version

    :steps:

        1. Create a GCE Compute Resource in Pre-upgrade Satellite.
        2. Provision hosts on the GCE Compute Resource.
        3. Upgrade the Satellite to the next or latest version.
        4. After the upgrade, you can modify the attributes of Compute Resource.
        5. Provision the new host on the GCE Compute Resource upgraded Satellite.

    :expectedresults:

        1. The host should be provisioned on GCE CR created in previous version
        2. The GCE CR attributes should be manipulated
"""


@pytest.fixture
def setup_gce_cr_and_host(
    puppet_upgrade_shared_satellite,
    shared_gce_cert,
    shared_gce_latest_rhel_uuid,
    shared_googleclient,
    upgrade_action,
):
    """Host can be provisioned on Google Cloud

    :id: 889975f2-56ca-4584-95a7-21c513969630

    :CaseImportance: Critical

    :steps:
        1. Create a GCE Compute Resource
        2. Create a Host-group with all the Global and Foreman entities but
            without Compute Profile, required to provision a host
        3. Provision a Host on Google Cloud using above GCE CR and Host-group

    :expectedresults:
        1. The host should be provisioned on Google Compute Engine
        2. The host name should be the same as given in data to provision the host
        3. The host should show Installed status for provisioned host
    """
    target_sat = puppet_upgrade_shared_satellite
    with SharedResource(
        puppet_upgrade_shared_satellite.hostname,
        upgrade_action,
        target_sat=puppet_upgrade_shared_satellite,
    ) as sat_upgrade:
        test_name = f'gce_upgrade_{gen_alpha(length=8)}'
        compute_attrs = {
            'image_id': shared_gce_latest_rhel_uuid,
            'machine_type': 'g1-small',
            'network': 'default',
            'associate_external_ip': True,
            'volumes_attributes': {'0': {'size_gb': '20'}},
        }
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        compute_resource = target_sat.api.GCEComputeResource(
            name=f'{test_name}_gce_cr',
            provider='GCE',
            key_path=settings.gce.cert_path,
            zone=settings.gce.zone,
            organization=[org],
            location=[location],
        ).create()
        domain_name = f'{settings.gce.zone}.c.{shared_gce_cert["project_id"]}.internal'
        domain = target_sat.api.Domain(
            name=domain_name, location=[location], organization=[org]
        ).create()
        default_arch = (
            target_sat.api.Architecture()
            .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}'})[0]
            .read()
        )
        default_os = (
            target_sat.api.OperatingSystem()
            .search(query={'search': settings.server.default_os_search_query})[0]
            .read()
        )
        default_ptable = (
            target_sat.api.PartitionTable()
            .search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]
            .read()
        )
        hostgroup = target_sat.api.HostGroup(
            architecture=default_arch,
            compute_resource=compute_resource,
            domain=domain,
            location=[location],
            name=f'{test_name}_hostgroup',
            root_pass=gen_string('alphanumeric'),
            operatingsystem=default_os,
            organization=[org],
            ptable=default_ptable,
        ).create()
        gce_finishimg = target_sat.api.Image(
            architecture=default_arch,
            compute_resource=compute_resource,
            name=f'{test_name}_finishimg',
            operatingsystem=default_os,
            username=gen_string('alpha'),
            uuid=shared_gce_latest_rhel_uuid,
        ).create()
        # The GCE API has a 62-character limit that is exceeded by test_name.domain,
        # so we need to shorten the hostname.
        hostname = test_name.split('_')[-1]
        host = target_sat.api.Host(
            architecture=default_arch,
            compute_attributes=compute_attrs,
            domain=domain,
            hostgroup=hostgroup,
            organization=org,
            operatingsystem=default_os,
            location=location,
            name=hostname,
            provision_method='image',
            image=gce_finishimg,
            root_pass=gen_string('alphanumeric'),
        ).create()
        fullhostname = f'{hostname}.{domain_name}'.lower()
        google_host = shared_googleclient.get_vm(name='{}'.format(fullhostname.replace('.', '-')))
        assert host.name == fullhostname
        assert host.build_status_label == 'Installed'
        assert host.ip == google_host.ip

        sat_upgrade.ready()
        test_data = Box(
            {
                'satellite': target_sat,
                'org': org,
                'location': location,
                'domain': domain,
                'compute_attrs': compute_attrs,
                'compute_resource': compute_resource,
                'gce_finishimg': gce_finishimg,
                'googleclient': shared_googleclient,
                'google_host': google_host,
                'hostgroup': hostgroup,
                'architecture': default_arch,
                'os': default_os,
                'provision_host_name': fullhostname,
                'provision_host_ip': host.ip,
            }
        )
        target_sat._session = None
        yield test_data


def test_post_create_gce_cr_and_host(
    setup_gce_cr_and_host,
):
    """Host provisioned using pre-upgrade GCE CR

    :id: postupgrade-ef82143d-efef-49b2-9702-93d67ef6804c

    :steps:

        1. Postupgrade, The Compute Resource attributes can be manipulated
        2. The host can be provisioned on GCE CR created in previous satellite version

    :expectedresults:

        1. The host should be provisioned on GCE CR created in previous version
        2. The GCE CR attributes should be manipulated
    """
    target_sat = setup_gce_cr_and_host.satellite
    googleclient = setup_gce_cr_and_host.googleclient

    # Test existing host
    pre_upgrade_host = target_sat.api.Host().search(
        query={'search': f'name={setup_gce_cr_and_host.provision_host_name}'}
    )[0]
    org = target_sat.api.Organization(id=pre_upgrade_host.organization.id).read()
    loc = target_sat.api.Location(id=pre_upgrade_host.location.id).read()
    domain = target_sat.api.Domain(id=pre_upgrade_host.domain.id).read()
    image = target_sat.api.Image(
        id=pre_upgrade_host.image.id, compute_resource=pre_upgrade_host.compute_resource.id
    ).read()
    gce_hostgroup = target_sat.api.HostGroup(id=pre_upgrade_host.hostgroup.id).read()
    assert pre_upgrade_host.ip == setup_gce_cr_and_host.provision_host_ip
    assert pre_upgrade_host.build_status_label == 'Installed'
    with target_sat.api_factory.satellite_setting('destroy_vm_on_host_delete=True'):
        pre_upgrade_host.delete()
        assert not target_sat.api.Host().search(query={'search': f'name={pre_upgrade_host.name}'})
        assert pre_upgrade_host.name not in [vm.name for vm in googleclient.list_vms()]

    # Create new host
    hostname = gen_alpha(length=8)
    host = target_sat.api.Host(
        architecture=setup_gce_cr_and_host.architecture,
        compute_attributes=setup_gce_cr_and_host.compute_attrs,
        domain=domain,
        hostgroup=gce_hostgroup,
        organization=org,
        operatingsystem=setup_gce_cr_and_host.os,
        location=loc,
        name=hostname,
        provision_method='image',
        image=image,
        root_pass=gen_string('alphanumeric'),
    ).create()
    assert host.name == f'{hostname}.{domain.name}'.lower()
    assert host.build_status_label == 'Installed'
    with target_sat.api_factory.satellite_setting('destroy_vm_on_host_delete=True'):
        host.delete()
        assert not target_sat.api.Host().search(query={'search': f'name={host.name}'})
        assert host.name not in [vm.name for vm in googleclient.list_vms()]

    # Modify compute resource
    compute_resource = setup_gce_cr_and_host.compute_resource
    newgce_name = gen_string('alpha')
    newgce_zone = random.choice(VALID_GCE_ZONES)
    compute_resource.name = newgce_name
    compute_resource.zone = newgce_zone
    compute_resource.update(['name', 'zone'])
    assert compute_resource.name == newgce_name
    assert compute_resource.zone == newgce_zone
