"""Test class for Host Collection CLI

:Requirement: Host collection

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: HostCollections

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_fake_host
from robottelo.cli.factory import make_host_collection
from robottelo.cli.factory import make_org
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.constants import DEFAULT_CV
from robottelo.constants import ENVIRONMENT
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.test import CLITestCase


class HostCollectionTestCase(CLITestCase):
    """Tests for Host Collections via Hammer CLI"""

    @classmethod
    def setUpClass(cls):
        """Prepare some data to be used in tests"""
        super().setUpClass()
        cls.organization = make_org()
        cls.library = LifecycleEnvironment.info(
            {'organization-id': cls.organization['id'], 'name': ENVIRONMENT}
        )
        cls.default_cv = ContentView.info(
            {'organization-id': cls.organization['id'], 'name': DEFAULT_CV}
        )
        make_host_collection({'organization-id': cls.organization['id']})

    def _make_fake_host_helper(self):
        """Make a new fake host"""
        return make_fake_host(
            {
                'content-view-id': self.default_cv['id'],
                'lifecycle-environment-id': self.library['id'],
                'name': gen_string('alpha', 15),
                'organization-id': self.organization['id'],
            }
        )

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_end_to_end(self):
        """Check if host collection can be created with name and description,
        content host can be added and removed, host collection can be listed,
        updated and deleted

        :id: 2d3b718e-6f57-4c83-aedb-15604cc8a4bd

        :expectedresults: Host collection is created and has expected name and
            description, content-host is added and removed, host collection is
            updated and deleted.

        :CaseImportance: Critical
        """
        name = list(valid_data_list().values())[0]
        desc = list(valid_data_list().values())[0]
        new_host_col = make_host_collection(
            {'description': desc, 'name': name, 'organization-id': self.organization['id']}
        )
        self.assertEqual(new_host_col['name'], name)
        self.assertEqual(new_host_col['description'], desc)

        # add host
        new_system = self._make_fake_host_helper()
        no_of_content_host = new_host_col['total-hosts']
        HostCollection.add_host({'host-ids': new_system['id'], 'id': new_host_col['id']})
        result = HostCollection.info({'id': new_host_col['id']})
        self.assertGreater(result['total-hosts'], no_of_content_host)

        # list hosts
        result = HostCollection.hosts({'name': name, 'organization-id': self.organization['id']})
        self.assertEqual(new_system['name'].lower(), result[0]['name'])
        # List all host collections within organization
        result = HostCollection.list({'organization': self.organization['name']})
        self.assertGreaterEqual(len(result), 2)
        # Filter list by name
        result = HostCollection.list({'name': name, 'organization-id': self.organization['id']})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], new_host_col['id'])
        # Filter list by associated host name
        result = HostCollection.list(
            {'organization': self.organization['name'], 'host': new_system['name']}
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], new_host_col['name'])

        # remove host
        no_of_content_host = HostCollection.info({'id': new_host_col['id']})['total-hosts']
        HostCollection.remove_host({'host-ids': new_system['id'], 'id': new_host_col['id']})
        result = HostCollection.info({'id': new_host_col['id']})
        self.assertGreater(no_of_content_host, result['total-hosts'])

        # update
        new_name = list(valid_data_list().values())[0]
        new_desc = list(valid_data_list().values())[0]
        HostCollection.update(
            {'description': new_desc, 'id': new_host_col['id'], 'new-name': new_name}
        )
        result = HostCollection.info({'id': new_host_col['id']})
        self.assertEqual(result['name'], new_name)
        self.assertEqual(result['description'], new_desc)

        # delete
        HostCollection.delete({'id': new_host_col['id']})
        with self.assertRaises(CLIReturnCodeError):
            HostCollection.info({'id': new_host_col['id']})

    @pytest.mark.tier1
    def test_positive_create_with_limit(self):
        """Check if host collection can be created with correct limits

        :id: 682b5624-1095-48e6-a0dd-c76e70ca6540

        :expectedresults: Host collection is created and has expected limits

        :CaseImportance: Critical
        """
        for limit in ('1', '3', '5', '10', '20'):
            with self.subTest(limit):
                new_host_col = make_host_collection(
                    {'max-hosts': limit, 'organization-id': self.organization['id']}
                )
                self.assertEqual(new_host_col['limit'], limit)

    @pytest.mark.tier1
    def test_positive_create_with_unlimited_hosts(self):
        """Create Host Collection with different values of unlimited-hosts
        parameter

        :id: d688fd4a-88eb-484e-9e90-854e0595edd0

        :expectedresults: Host Collection is created and unlimited-hosts
            parameter is set

        :CaseImportance: Critical
        """
        for unlimited in ('True', 'Yes', 1, 'False', 'No', 0):
            with self.subTest(unlimited):
                host_collection = make_host_collection(
                    {
                        'max-hosts': 1 if unlimited in ('False', 'No', 0) else None,
                        'organization-id': self.organization['id'],
                        'unlimited-hosts': unlimited,
                    }
                )
                result = HostCollection.info(
                    {'name': host_collection['name'], 'organization-id': self.organization['id']}
                )
                if unlimited in ('True', 'Yes', 1):
                    self.assertEqual(result['limit'], 'None')
                else:
                    self.assertEqual(result['limit'], '1')

    @pytest.mark.tier1
    def test_negative_create_with_name(self):
        """Attempt to create host collection with invalid name of different
        types

        :id: 92a9eff0-693f-4ab8-b2c4-de08e5f709a7

        :expectedresults: Host collection is not created and error is raised

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_host_collection(
                        {'name': name, 'organization-id': self.organization['id']}
                    )

    @pytest.mark.tier1
    def test_positive_update_limit(self):
        """Check if host collection limits can be updated

        :id: 4c0e0c3b-82ac-4aa2-8378-6adc7946d4ec

        :expectedresults: Host collection limits is updated

        :BZ: 1245334

        :CaseImportance: Critical
        """
        new_host_col = make_host_collection({'organization-id': self.organization['id']})
        for limit in ('3', '6', '9', '12', '15', '17', '19'):
            with self.subTest(limit):
                HostCollection.update(
                    {'id': new_host_col['id'], 'max-hosts': limit, 'unlimited-hosts': 0}
                )
                result = HostCollection.info({'id': new_host_col['id']})
                self.assertEqual(result['limit'], limit)

    @pytest.mark.tier2
    def test_positive_list_by_org_id(self):
        """Check if host collection list can be filtered by organization id

        :id: afbe077a-0de1-432c-a0c4-082129aab92e

        :expectedresults: Only host-collection within specific org is listed

        :CaseLevel: Integration
        """
        # Create two host collections within different organizations
        new_org = make_org()
        host_col = make_host_collection({'organization-id': new_org['id']})
        # List all host collections
        self.assertGreaterEqual(len(HostCollection.list()), 2)
        # Filter list by org id
        result = HostCollection.list({'organization-id': new_org['id']})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], host_col['id'])

    @pytest.mark.tier2
    def test_positive_host_collection_host_pagination(self):
        """Check if pagination configured on per-page param defined in hammer
        host-collection hosts command overrides global configuration defined
        on /etc/hammer/cli_config.yml, which default is 20 per page

        :BZ: 1343583

        :id: bbe1108b-bfb2-4a03-94ef-8fd1b5a0ec82

        :expectedresults: Number of host per page follows per_page
            configuration restriction

        :CaseLevel: Integration
        """
        host_collection = make_host_collection({'organization-id': self.organization['id']})
        host_ids = ','.join(self._make_fake_host_helper()['id'] for _ in range(2))
        HostCollection.add_host({'host-ids': host_ids, 'id': host_collection['id']})
        for number in range(1, 3):
            listed_hosts = HostCollection.hosts(
                {
                    'id': host_collection['id'],
                    'organization-id': self.organization['id'],
                    'per-page': number,
                }
            )
            self.assertEqual(len(listed_hosts), number)

    @pytest.mark.tier2
    def test_positive_copy_by_id(self):
        """Check if host collection can be cloned by id

        :id: fd7cea50-bc56-4938-a81d-4f7a60711814

        :customerscenario: true

        :expectedresults: Host collection is cloned successfully

        :BZ: 1328925

        :CaseLevel: Integration
        """
        host_collection = make_host_collection(
            {'name': gen_string('alpha', 15), 'organization-id': self.organization['id']}
        )
        new_name = gen_string('numeric')
        new_host_collection = HostCollection.copy(
            {'id': host_collection['id'], 'new-name': new_name}
        )
        result = HostCollection.info({'id': new_host_collection[0]['id']})
        self.assertEqual(result['name'], new_name)
