"""Test Hostgroup related Upgrade Scenario's

:CaseAutomation: Automated

:CaseComponent: HostGroup

:Team: Proton

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha, gen_string
import pytest

from robottelo.constants import HTTPS_MEDIUM_URL
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def hostgroup_upgrade_setup(hostgroup_upgrade_shared_satellite, upgrade_action):
    """Hostgroup with different data type are created

    :id: preupgrade-79958754-94b6-4bfe-af12-7d4031cd2dd2

    :steps: In Preupgrade Satellite, Create hostgroup with different entities.

    :expectedresults: Hostgroup should be create successfully.
    """
    target_sat = hostgroup_upgrade_shared_satellite
    test_name = f'hostgroup_upgrade{gen_alpha()}'
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'test_name': test_name,
                'architecture': None,
                'ptable': None,
            }
        )
        proxy = target_sat.api.SmartProxy().search(
            query={'search': f'url = {target_sat.url}:9090'}
        )[0]
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        loc = target_sat.api.Location(organization=[org], name=f'{test_name}_loc').create()
        parent_hostgroup = target_sat.api.HostGroup(
            location=[loc.id], organization=[org.id], name=f'{test_name}_parent_host_grp'
        ).create()
        lc_env = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=2
        ).create()

        domain = target_sat.api.Domain(name=f'{test_name}_domain').create()
        architecture = target_sat.api.Architecture(name=f'{test_name}_arch').create()
        test_data.architecture = architecture
        ptable_layout = gen_alpha()
        ptable = target_sat.api.PartitionTable(
            name=f'{test_name}_ptable', layout=ptable_layout
        ).create()
        test_data.ptable = ptable
        operatingsystem = target_sat.api.OperatingSystem(
            architecture=[architecture], ptable=[ptable], name=f'{test_name}_os', major='9'
        ).create()
        medium = target_sat.api.Media(
            operatingsystem=[operatingsystem], name=f'{test_name}_medium', path_=HTTPS_MEDIUM_URL
        ).create()
        subnet = target_sat.api.Subnet(
            location=[loc],
            organization=[org],
            name=f"{test_name}_subnet",
            network='192.168.1.0',
            mask='255.255.255.0',
            cidr='24',
        ).create()

        host_group = target_sat.api.HostGroup(
            architecture=architecture,
            domain=domain,
            location=[loc.id],
            medium=medium,
            name=f"{test_name}_host_grp",
            operatingsystem=operatingsystem,
            organization=[org.id],
            ptable=ptable,
            subnet=subnet,
            parent=parent_hostgroup,
            lifecycle_environment=lc_env,
            content_source=proxy,
            root_pass='rootpass',
        ).create()
        assert host_group.name == f"{test_name}_host_grp"
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


def test_post_crud_hostgroup(hostgroup_upgrade_setup, request):
    """After upgrade, Update, delete and clone should work on existing hostgroup(created before
    upgrade)

    :id: postupgrade-79958754-94b6-4bfe-af12-7d4031cd2dd2

    :steps:

        1. After upgrade, check hostgroup entities.
        2. Update existing hostgroup with new entities
        3. Clone hostgroup.
        4. Delete hostgroup, parent hostgroup, cloned hostgroup, domain, subnet, os, loc, org.

    :expectedresults: After upgrade
        1- Hostgroup remain same.
        2- Hostgroup entities update should work.
        3- Hostgroup cloned should work.
        4- Cloned hostgroup should be the subset of original hostgroup.
        5- Hostgroup entities deletion should work

    """
    pre_test_name = hostgroup_upgrade_setup.test_name
    target_sat = hostgroup_upgrade_setup.target_sat
    # verify host-group is intact after upgrade
    org = target_sat.api.Organization().search(query={'search': f'name="{pre_test_name}_org"'})[0]
    request.addfinalizer(org.delete)
    loc = target_sat.api.Location().search(query={'search': f'name="{pre_test_name}_loc"'})[0]
    request.addfinalizer(loc.delete)
    hostgrp = target_sat.api.HostGroup().search(query={'search': f'name={pre_test_name}_host_grp'})[
        0
    ]
    request.addfinalizer(hostgrp.parent.delete)
    request.addfinalizer(hostgrp.delete)
    assert f"{pre_test_name}_host_grp" == hostgrp.name

    domain = target_sat.api.Domain().search(query={'search': f'name={pre_test_name}_domain'})[0]
    assert domain.id == hostgrp.domain.id
    request.addfinalizer(domain.delete)

    subnet = target_sat.api.Subnet().search(query={'search': f'name={pre_test_name}_subnet'})[0]
    assert subnet.id == hostgrp.subnet.id
    request.addfinalizer(subnet.delete)

    parent = target_sat.api.HostGroup().search(
        query={'search': f'name={pre_test_name}_parent_host_grp'}
    )[0]
    assert parent.id == hostgrp.parent.id

    os = target_sat.api.OperatingSystem().search(query={'search': f'name={pre_test_name}_os'})[0]
    assert os.id == hostgrp.operatingsystem.id
    request.addfinalizer(os.delete)

    # update host-group after upgrade
    new_name = gen_string('alpha')
    hostgrp.name = new_name
    hostgrp.update(['name'])
    assert new_name == hostgrp.name

    new_subnet = target_sat.api.Subnet(
        location=[loc],
        organization=[org],
        name=f"{pre_test_name}_subnet_2",
        network='192.168.2.0',
        mask='255.255.255.0',
        cidr='24',
    ).create()
    hostgrp.subnet = new_subnet
    hostgrp.update(['subnet'])
    assert new_subnet.id == hostgrp.subnet.id

    new_domain = target_sat.api.Domain(name=f'{pre_test_name}_domain_2').create()
    hostgrp.domain = new_domain
    hostgrp.update(['domain'])
    assert new_domain.id == hostgrp.domain.id

    new_os = target_sat.api.OperatingSystem(
        architecture=[hostgroup_upgrade_setup.architecture],
        ptable=[hostgroup_upgrade_setup.ptable],
        name=f'{pre_test_name}_os_2',
        major='9',
    ).create()
    hostgrp.operatingsystem = new_os
    hostgrp.update(['operatingsystem'])
    assert new_os.id == hostgrp.operatingsystem.id

    # clone hostgroup
    hostgroup_cloned_name = gen_string('alpha')
    hostgroup_cloned = target_sat.api.HostGroup(id=hostgrp.id).clone(
        data={'name': hostgroup_cloned_name}
    )
    hostgroup_search = target_sat.api.HostGroup().search(
        query={'search': f'name={hostgroup_cloned_name}'}
    )
    assert len(hostgroup_search) == 1
    hostgroup_cloned_object = hostgroup_search[0]

    request.addfinalizer(hostgroup_cloned_object.delete)
    hostgroup_origin = hostgrp.read_json()
    # remove unset values before comparison
    unset_keys = set(hostgroup_cloned) - set(hostgroup_origin)
    for key in unset_keys:
        del hostgroup_cloned[key]

    # remove unique values before comparison
    for key in ('updated_at', 'created_at', 'title', 'id', 'name'):
        del hostgroup_cloned[key]
    assert hostgroup_cloned.items() <= hostgroup_origin.items()
