"""Unit tests for the ``environments`` paths.

Documentation for these paths is available here:
http://www.katello.org/docs/api/apidoc/lifecycle_environments.html

"""
from nailgun import entities
from robottelo.decorators import run_only_on
from robottelo.test import APITestCase


@run_only_on('sat')
class LifecycleEnvironmentTestCase(APITestCase):
    """Tests for ``katello/api/v2/environments``."""

    def test_get_all(self):
        """@Test: Search for a lifecycle environment and specify an org ID.

        @Feature: LifecycleEnvironment

        @Steps:

        1. Create an organization.
        1. Create a lifecycle environment belonging to the organization.
        2. Search for lifecycle environments in the organization.

        @Assert: Only "Library" and the lifecycle environment just created are
        in the search results.

        """
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        lc_envs = lc_env.search({'organization'})
        self.assertEqual(len(lc_envs), 2)
        self.assertEqual(
            {lc_env_.name for lc_env_ in lc_envs},
            {u'Library', lc_env.name},
        )
