"""Test Hostgroup related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.test import APITestCase
from upgrade_tests import pre_upgrade, post_upgrade


class scenario_positive_hostgroup(APITestCase):
    """Hostgroup is intact post upgrade and verify hostgroup update/delete

    :steps:

        1. In Preupgrade Satellite, create hostgroup with different entities
        2. Upgrade the satellite to next/latest version
        3. Update existing hostgroup with different entities
        4. Postupgrade, Verify the hostgroup is intact, update, clone and delete

    :expectedresults: Hostgroup should create, update, clone and delete successfully.
    """
    @classmethod
    def setUpClass(cls):
        cls.hostgroup_name = 'preupgrade_hostgroup'
        cls.parent_name = 'pre_upgrade_parent_hostgrp'
        cls.subnet_name = 'pre_upgrade_hostgrp_subnet'
        cls.os_name = 'pre_upgrade_hostgrp_os'
        cls.domain_name = 'pre_upgrade_hostgrp_domain'
        cls.proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]

    def setupScenario(self):
        """Create hostgroup and its dependant entities
        """
        self.org = entities.Organization().create()
        self.loc = entities.Location(organization=[self.org]).create()
        self.parent_hostgroup = entities.HostGroup(
            location=[self.loc.id],
            organization=[self.org.id],
            name=self.parent_name
        ).create()
        self.lc_env = entities.LifecycleEnvironment(
            name=gen_string('alpha'),
            organization=self.org,
        ).create()
        self.domain = entities.Domain(name=self.domain_name).create()
        self.architecture = entities.Architecture().create()
        self.ptable = entities.PartitionTable().create()
        self.operatingsystem = entities.OperatingSystem(
            architecture=[self.architecture],
            ptable=[self.ptable],
            name=self.os_name
        ).create()
        self.medium = entities.Media(operatingsystem=[self.operatingsystem]).create()
        self.subnet = entities.Subnet(
            location=[self.loc],
            organization=[self.org],
            name=self.subnet_name
        ).create()

    @pre_upgrade
    def test_pre_create_hostgroup(self):
        """Hostgroup with different data type are created

        :id: preupgrade-79958754-94b6-4bfe-af12-7d4031cd2dd2

        :steps: In Preupgrade Satellite, Create hostgroup with different entities.

        :expectedresults: Hostgroup should create successfully.
        """
        self.setupScenario()
        host_group = entities.HostGroup(
            architecture=self.architecture,
            domain=self.domain,
            location=[self.loc.id],
            medium=self.medium,
            name=self.hostgroup_name,
            operatingsystem=self.operatingsystem,
            organization=[self.org.id],
            ptable=self.ptable,
            puppet_proxy=self.proxy,
            puppet_ca_proxy=self.proxy,
            subnet=self.subnet,
            parent=self.parent_hostgroup,
            lifecycle_environment=self.lc_env,
            content_source=self.proxy,
            root_pass='rootpass'
        ).create()
        self.assertEqual(self.hostgroup_name, host_group.name)

    @post_upgrade
    def test_post_crud_hostgroup(self):
        """Hostgroup is intact post upgrade and update/delete/clone hostgroup

        :id: postupgrade-79958754-94b6-4bfe-af12-7d4031cd2dd2

        :steps:

            1. Postupgrade, Verify hostgroup has same entities associated.
            2. Update existing hostgroup with new entities
            3. Clone hostgroup.
            4. Delete hostgroup.

        :expectedresults: Hostgroup should update, clone and delete successfully.
        """
        # verify hostgroup is intact after upgrade
        hostgrp = entities.HostGroup().search(query={
            'search': 'name={0}'.format(self.hostgroup_name)
        })
        domain = entities.Domain().search(query={
            'search': 'name={0}'.format(self.domain_name)
        })
        subnet = entities.Subnet().search(query={
            'search': 'name={0}'.format(self.subnet_name)
        })
        parent = entities.HostGroup().search(query={
            'search': 'name={0}'.format(self.parent_name)
        })
        os = entities.OperatingSystem().search(query={
            'search': 'name={0}'.format(self.os_name)
        })
        self.assertEqual(self.hostgroup_name, hostgrp[0].name)
        self.assertEqual(domain[0].id, hostgrp[0].domain.id)
        self.assertEqual(subnet[0].id, hostgrp[0].subnet.id)
        self.assertEqual(parent[0].id, hostgrp[0].parent.id)
        self.assertEqual(os[0].id, hostgrp[0].operatingsystem.id)
        self.assertEqual(self.proxy.id, hostgrp[0].puppet_proxy.id)
        self.assertEqual(self.proxy.id, hostgrp[0].puppet_ca_proxy.id)

        # update hostgroup after upgrade
        new_name = gen_string('alpha')
        hostgrp[0].name = new_name
        hostgrp[0].update(['name'])
        self.assertEqual(new_name, hostgrp[0].name)
        new_subnet = entities.Subnet().create()
        hostgrp[0].subnet = new_subnet
        hostgrp[0].update(['subnet'])
        self.assertEqual(new_subnet.id, hostgrp[0].subnet.id)
        new_domain = entities.Domain().create()
        hostgrp[0].domain = new_domain
        hostgrp[0].update(['domain'])
        self.assertEqual(new_domain.id, hostgrp[0].domain.id)
        new_os = entities.OperatingSystem().create()
        hostgrp[0].operatingsystem = new_os
        hostgrp[0].update(['operatingsystem'])
        self.assertEqual(new_os.id, hostgrp[0].operatingsystem.id)

        # clone hostgroup
        hostgroup_cloned_name = gen_string('alpha')
        hostgroup_cloned = entities.HostGroup(
            id=hostgrp[0].id
        ).clone(data={'name': hostgroup_cloned_name})
        hostgroup_origin = hostgrp[0].read_json()

        # remove unset values before comparison
        unset_keys = set(hostgroup_cloned) - set(hostgroup_origin)
        for key in unset_keys:
            del hostgroup_cloned[key]

        # remove unique values before comparison
        uniqe_keys = (u'updated_at', u'created_at', u'title', u'id', u'name')
        for key in uniqe_keys:
            del hostgroup_cloned[key]
        self.assertDictContainsSubset(hostgroup_cloned, hostgroup_origin)

        # Delete hostgroup
        hostgrp[0].delete()
        with self.assertRaises(HTTPError):
            hostgrp[0].read()
