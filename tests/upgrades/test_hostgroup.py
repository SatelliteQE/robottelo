"""Test Hostgroup related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: HostGroup

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string


class TestHostgroup:
    """
    Hostgroup with different data type are created
    """

    @pytest.mark.pre_upgrade
    def test_pre_create_hostgroup(self, request, default_sat):
        """Hostgroup with different data type are created

        :id: preupgrade-79958754-94b6-4bfe-af12-7d4031cd2dd2

        :steps: In Preupgrade Satellite, Create hostgroup with different entities.

        :expectedresults: Hostgroup should be create successfully.
        """

        proxy = default_sat.api.SmartProxy().search(
            query={'search': f'url = {default_sat.url}:9090'}
        )[0]
        test_name = request.node.name
        org = default_sat.api.Organization(name=f"{test_name}_org").create()
        loc = default_sat.api.Location(organization=[org], name=f"{test_name}_loc").create()
        parent_hostgroup = default_sat.api.HostGroup(
            location=[loc.id], organization=[org.id], name=f'{test_name}_parent_host_grp'
        ).create()
        lc_env = default_sat.api.LifecycleEnvironment(
            name=f"{test_name}_lce", organization=org
        ).create()

        domain = default_sat.api.Domain(name=f"{test_name}_domain").create()
        architecture = default_sat.api.Architecture().create()
        ptable = default_sat.api.PartitionTable().create()
        operatingsystem = default_sat.api.OperatingSystem(
            architecture=[architecture], ptable=[ptable], name=f"{test_name}_os"
        ).create()
        medium = default_sat.api.Media(operatingsystem=[operatingsystem]).create()
        subnet = default_sat.api.Subnet(
            location=[loc], organization=[org], name=f"{test_name}_subnet"
        ).create()

        host_group = default_sat.api.HostGroup(
            architecture=architecture,
            domain=domain,
            location=[loc.id],
            medium=medium,
            name=f"{test_name}_host_grp",
            operatingsystem=operatingsystem,
            organization=[org.id],
            ptable=ptable,
            puppet_proxy=proxy,
            puppet_ca_proxy=proxy,
            subnet=subnet,
            parent=parent_hostgroup,
            lifecycle_environment=lc_env,
            content_source=proxy,
            root_pass='rootpass',
        ).create()
        assert host_group.name == f"{test_name}_host_grp"

    @pytest.mark.post_upgrade(depend_on=test_pre_create_hostgroup)
    def test_post_crud_hostgroup(self, request, dependent_scenario_name, default_sat):
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
        pre_test_name = dependent_scenario_name
        # verify host-group is intact after upgrade
        org = default_sat.api.Organization().search(
            query={'search': f'name="{pre_test_name}_org"'}
        )[0]
        request.addfinalizer(org.delete)
        loc = default_sat.api.Location().search(query={'search': f'name="{pre_test_name}_loc"'})[0]
        request.addfinalizer(loc.delete)
        proxy = default_sat.api.SmartProxy().search(
            query={'search': f'url = {default_sat.url}:9090'}
        )[0]
        hostgrp = default_sat.api.HostGroup().search(
            query={'search': f'name={pre_test_name}_host_grp'}
        )[0]
        request.addfinalizer(hostgrp.parent.delete)
        request.addfinalizer(hostgrp.delete)
        assert f"{pre_test_name}_host_grp" == hostgrp.name
        assert proxy.id == hostgrp.puppet_proxy.id
        assert proxy.id == hostgrp.puppet_ca_proxy.id

        domain = default_sat.api.Domain().search(query={'search': f'name={pre_test_name}_domain'})[
            0
        ]
        assert domain.id == hostgrp.domain.id
        request.addfinalizer(domain.delete)

        subnet = default_sat.api.Subnet().search(query={'search': f'name={pre_test_name}_subnet'})[
            0
        ]
        assert subnet.id == hostgrp.subnet.id
        request.addfinalizer(subnet.delete)

        parent = default_sat.api.HostGroup().search(
            query={'search': f'name={pre_test_name}_parent_host_grp'}
        )[0]
        assert parent.id == hostgrp.parent.id

        os = default_sat.api.OperatingSystem().search(query={'search': f'name={pre_test_name}_os'})[
            0
        ]
        assert os.id == hostgrp.operatingsystem.id
        request.addfinalizer(os.delete)

        # update host-group after upgrade
        new_name = gen_string('alpha')
        hostgrp.name = new_name
        hostgrp.update(['name'])
        assert new_name == hostgrp.name

        new_subnet = default_sat.api.Subnet().create()
        hostgrp.subnet = new_subnet
        hostgrp.update(['subnet'])
        assert new_subnet.id == hostgrp.subnet.id

        new_domain = default_sat.api.Domain().create()
        hostgrp.domain = new_domain
        hostgrp.update(['domain'])
        assert new_domain.id == hostgrp.domain.id

        new_os = default_sat.api.OperatingSystem().create()
        hostgrp.operatingsystem = new_os
        hostgrp.update(['operatingsystem'])
        assert new_os.id == hostgrp.operatingsystem.id

        # clone hostgroup
        hostgroup_cloned_name = gen_string('alpha')
        hostgroup_cloned = default_sat.api.HostGroup(id=hostgrp.id).clone(
            data={'name': hostgroup_cloned_name}
        )
        hostgroup_search = default_sat.api.HostGroup().search(
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
