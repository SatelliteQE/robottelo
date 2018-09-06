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


class scenario_positive_default_role_added_permission_intact(APITestCase):
    """Default role extra added permission with filter should be intact post upgrade

    :id:

    :steps:

        1. In Preupgrade Satellite, Update existing 'Default role' by adding new permission with filter
        2. Upgrade the satellite to next/latest version
        3. Postupgrade, Verify the permission with filter in existing 'Default role' is intact

    :expectedresults: The added permission with filter in existing 'Default role' is intact post upgrade
    """

    @pre_upgrade
    def test_pre_default_role_added_permission(self):
        """New permission with filter is added to Default Role

        :steps: New permission is added to existing 'Default role' with filter

        :expectedresults: Permission with filter is added to existing 'Default role'.

        """
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        entities.Filter(
            permission=entities.Permission(
                resource_type='Domain').search(
                filters={'name': 'view_domains'}),
            unlimited=False,
            role=defaultrole,
            search='name ~ a'
        ).create()


    @post_upgrade
    def test_post_default_role_added_permission(self):
        """The new permission with filter in 'Default role' is intact post upgrade

        :expectedresults: The added permission with filter in existing 'Default role' is intact post upgrade
        """
        defaultrole = entities.Role().search(query={'search': 'name="Default role"'})[0]
        filt = entities.Filter().search(query={'search': 'role_id={} and permission="view_domains"'.format(defaultrole.id)})
        self.assertTrue(filt)
        self.assertEqual(filt[0].search, 'name ~ a')
        # Teardown
        filt[0].delete()