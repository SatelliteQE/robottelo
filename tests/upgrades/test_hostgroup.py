"""Test Hostgroup related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: HostGroup

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade

from robottelo.config import settings


class TestHostgroup:
    """
    Hostgroup with different data type are created
    """

    @pre_upgrade
    def test_pre_create_hostgroup(self, request):
        """Hostgroup with different data type are created

        :id: preupgrade-79958754-94b6-4bfe-af12-7d4031cd2dd2

        :steps: In Preupgrade Satellite, Create hostgroup with different entities.

        :expectedresults: Hostgroup should be create successfully.
        """

        proxy = entities.SmartProxy().search(
            query={'search': f'url = https://{settings.server.hostname}:9090'}
        )[0]
        test_name = request.node.name
        org = entities.Organization(name=f"{test_name}_org").create()
        loc = entities.Location(organization=[org], name=f"{test_name}_loc").create()
        parent_hostgroup = entities.HostGroup(
            location=[loc.id], organization=[org.id], name=f'{test_name}_parent_host_grp'
        ).create()
        lc_env = entities.LifecycleEnvironment(name=f"{test_name}_lce", organization=org).create()

        domain = entities.Domain(name=f"{test_name}_domain").create()
        architecture = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        operatingsystem = entities.OperatingSystem(
            architecture=[architecture], ptable=[ptable], name=f"{test_name}_os"
        ).create()
        medium = entities.Media(operatingsystem=[operatingsystem]).create()
        subnet = entities.Subnet(
            location=[loc], organization=[org], name=f"{test_name}_subnet"
        ).create()

        host_group = entities.HostGroup(
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

    @post_upgrade(depend_on=test_pre_create_hostgroup)
    def test_post_crud_hostgroup(self, request, dependent_scenario_name):
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
        org = entities.Organization().search(query={'search': f'name="{pre_test_name}_org"'})[0]
        request.addfinalizer(org.delete)
        loc = entities.Location().search(query={'search': f'name="{pre_test_name}_loc"'})[0]
        request.addfinalizer(loc.delete)
        proxy = entities.SmartProxy().search(
            query={'search': f'url = https://{settings.server.hostname}:9090'}
        )[0]
        hostgrp = entities.HostGroup().search(query={'search': f'name={pre_test_name}_host_grp'})[0]
        request.addfinalizer(hostgrp.parent.delete)
        request.addfinalizer(hostgrp.delete)
        assert f"{pre_test_name}_host_grp" == hostgrp.name
        assert proxy.id == hostgrp.puppet_proxy.id
        assert proxy.id == hostgrp.puppet_ca_proxy.id

        domain = entities.Domain().search(query={'search': f'name={pre_test_name}_domain'})[0]
        assert domain.id == hostgrp.domain.id
        request.addfinalizer(domain.delete)

        subnet = entities.Subnet().search(query={'search': f'name={pre_test_name}_subnet'})[0]
        assert subnet.id == hostgrp.subnet.id
        request.addfinalizer(subnet.delete)

        parent = entities.HostGroup().search(
            query={'search': f'name={pre_test_name}_parent_host_grp'}
        )[0]
        assert parent.id == hostgrp.parent.id

        os = entities.OperatingSystem().search(query={'search': f'name={pre_test_name}_os'})[0]
        assert os.id == hostgrp.operatingsystem.id
        request.addfinalizer(os.delete)

        # update host-group after upgrade
        new_name = gen_string('alpha')
        hostgrp.name = new_name
        hostgrp.update(['name'])
        assert new_name == hostgrp.name

        new_subnet = entities.Subnet().create()
        hostgrp.subnet = new_subnet
        hostgrp.update(['subnet'])
        assert new_subnet.id == hostgrp.subnet.id

        new_domain = entities.Domain().create()
        hostgrp.domain = new_domain
        hostgrp.update(['domain'])
        assert new_domain.id == hostgrp.domain.id

        new_os = entities.OperatingSystem().create()
        hostgrp.operatingsystem = new_os
        hostgrp.update(['operatingsystem'])
        assert new_os.id == hostgrp.operatingsystem.id

        # clone hostgroup
        hostgroup_cloned_name = gen_string('alpha')
        hostgroup_cloned = entities.HostGroup(id=hostgrp.id).clone(
            data={'name': hostgroup_cloned_name}
        )
        hostgroup_search = entities.HostGroup().search(
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
        uniqe_keys = ('updated_at', 'created_at', 'title', 'id', 'name')
        for key in uniqe_keys:
            del hostgroup_cloned[key]
        assert hostgroup_cloned.items() <= hostgroup_origin.items()
