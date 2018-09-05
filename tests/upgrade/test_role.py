"""Test Roles related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from robottelo.test import APITestCase
from upgrade_tests import pre_upgrade, post_upgrade


class scenario_positive_default_role_added_permission(APITestCase):
    """Default role extra added permission should be intact post upgrade

    :id: 3a350e4a-96b3-4033-b562-3130fc43a4bc

    :steps:

        1. In Preupgrade Satellite, Update existing 'Default role' by adding
            new permission
        2. Upgrade the satellite to next/latest version
        3. Postupgrade, Verify the permission in existing 'Default role' intact

    :expectedresults: The added permission in existing 'Default role' is intact
        post upgrade
    """

    @pre_upgrade
    def test_pre_default_role_added_permission(self):
        """New permission is added to Default Role

        :steps: New permission is added to existing 'Default role'

        :expectedresults: Permission is added to existing 'Default role'.

        """
        defaultrole = entities.Role().search(
            query={'search': 'name="Default role"'})[0]
        subnetfilter = entities.Filter(
            permission=entities.Permission(
                resource_type='Subnet').search(
                filters={'name': 'view_subnets'}),
            role=defaultrole
        ).create()
        self.assertIn(
            subnetfilter.id, [filt.id for filt in defaultrole.read().filters])

    @post_upgrade
    def test_post_default_role_added_permission(self):
        """The new permission in 'Default role' is intact post upgrade

        :expectedresults: The added permission in existing 'Default role' is
            intact post upgrade
        """
        defaultrole = entities.Role().search(
            query={'search': 'name="Default role"'})[0]
        subnetfilt = entities.Filter().search(query={
            'search': 'role_id={} and permission="view_subnets"'.format(
                defaultrole.id)})
        self.assertTrue(subnetfilt)
        # Teardown
        subnetfilt[0].delete()


class scenario_positive_default_role_added_permission_with_filter(APITestCase):
    """Default role extra added permission with filter should be intact post
        upgrade

    :id: b287b71c-42fd-4612-a67a-b93d47dbbb33

    :steps:

        1. In Preupgrade Satellite, Update existing 'Default role' by adding
            new permission with filter
        2. Upgrade the satellite to next/latest version
        3. Postupgrade, Verify the permission with filter in existing
            'Default role' is intact

    :expectedresults: The added permission with filter in existing
        'Default role' is intact post upgrade
    """

    @pre_upgrade
    def test_pre_default_role_added_permission_with_filter(self):
        """New permission with filter is added to Default Role

        :steps: New permission is added to existing 'Default role' with filter

        :expectedresults: Permission with filter is added to existing
            'Default role'

        """
        defaultrole = entities.Role().search(
            query={'search': 'name="Default role"'})[0]
        domainfilter = entities.Filter(
            permission=entities.Permission(
                resource_type='Domain').search(
                filters={'name': 'view_domains'}),
            unlimited=False,
            role=defaultrole,
            search='name ~ a'
        ).create()
        self.assertIn(
            domainfilter.id, [filt.id for filt in defaultrole.read().filters])

    @post_upgrade
    def test_post_default_role_added_permission_with_filter(self):
        """The new permission with filter in 'Default role' is intact post
            upgrade

        :expectedresults: The added permission with filter in existing
            'Default role' is intact post upgrade
        """
        defaultrole = entities.Role().search(
            query={'search': 'name="Default role"'})[0]
        domainfilt = entities.Filter().search(query={
            'search': 'role_id={} and permission="view_domains"'.format(
                defaultrole.id)})
        self.assertTrue(domainfilt)
        self.assertEqual(domainfilt[0].search, 'name ~ a')
        # Teardown
        domainfilt[0].delete()
