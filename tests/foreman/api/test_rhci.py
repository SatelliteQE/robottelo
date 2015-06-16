"""Unit tests for the ``fusor/api/v21/deployments`` paths."""
from ddt import data, ddt
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.test import APITestCase
# pylint:disable=too-many-public-methods


@ddt
class RHCIDeploymentTestCase(APITestCase):
    """Tests for the RHCI deployment API."""

    @classmethod
    def setUpClass(cls):
        """ Setup the base entities for all tests. """
        super(RHCIDeploymentTestCase, cls).setUpClass()
        org_id = entities.Organization().create_json()['organization']['id']
        cls.org = entities.Organization(id=org_id)
        cls.lc_env = entities.LifecycleEnvironment(
            organization=cls.org).create()
        cls.rhev_engine_host = entities.Host(id=3)
        cls.to_delete = []

    @classmethod
    def tearDownClass(cls):
        """ Delete deployments designated during testing. """
        super(RHCIDeploymentTestCase, cls).tearDownClass()
        print cls.to_delete
        for deployment in cls.to_delete:
            deployment.delete()

    @data(
        gen_string(str_type='alpha'),
        gen_string(str_type='alphanumeric'),
        gen_string(str_type='cjk'),
        gen_string(str_type='latin1'),
    )
    def test_positive_create_deployment(self, data):
        """@Test: Create a simple deployment.

        @Assert: An RHCI deployment is created with a random name.

        @Feature: RHCI Deployment

        """
        deployment = entities.RHCIDeployment(
            name=data,
            organization=self.org,
            lifecycle_environment=self.lc_env,
            deploy_rhev=True,
            rhev_engine_host=self.rhev_engine_host,
            rhev_storage_type='NFS',
            rhev_engine_admin_password='changeme',
        ).create()
        self.assertEquals(deployment.name, data)
        self.assertEqual(deployment.organization.id, self.org.id)
        self.assertEqual(deployment.lifecycle_environment.id, self.lc_env.id)
        self.to_delete.append(deployment)

    @data(
        {'name': gen_string(str_type='alpha'),
         'new-name': gen_string(str_type='alpha')},
        {'name': gen_string(str_type='alphanumeric'),
         'new-name': gen_string(str_type='alphanumeric')},
        {'name': gen_string(str_type='cjk'),
         'new-name': gen_string(str_type='cjk')},
        {'name': gen_string(str_type='latin1'),
         'new-name': gen_string(str_type='latin1')},
    )
    def test_positive_update_name(self, data):
        """@Test: Update a deployment's name.

        @Assert: An RHCI deployment is updated with a random name.

        @Feature: RHCI Deployment

        """
        deployment = entities.RHCIDeployment(
            name=data['name'],
            organization=self.org,
            lifecycle_environment=self.lc_env,
            deploy_rhev=True,
            rhev_engine_host=self.rhev_engine_host,
            rhev_storage_type='NFS',
            rhev_engine_admin_password='changeme',
        ).create()
        self.assertEquals(deployment.name, data['name'])

        # perform the update
        deployment.name = data['new-name']
        deployment = deployment.update(['name'])
        self.assertEqual(deployment.name, data['new-name'])
        self.to_delete.append(deployment)

    @data(
        gen_string(str_type='alpha'),
    )
    def test_positive_delete_deployment(self, data):
        """@Test: Create and delete a simple deployment.

        @Assert: An RHCI deployment is deleted.

        @Feature: RHCI Deployment

        """
        deployment = entities.RHCIDeployment(
            name=data,
            organization=self.org,
            lifecycle_environment=self.lc_env,
            deploy_rhev=True,
            rhev_engine_host=self.rhev_engine_host,
            rhev_storage_type='NFS',
            rhev_engine_admin_password='changeme',
        ).create()
        self.assertEquals(deployment.name, data)

        # Perform the delete
        deployment.delete()

        # Check to make sure the deployment has been deleted
        with self.assertRaises(HTTPError):
            deployment.read()
