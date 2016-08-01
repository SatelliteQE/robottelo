# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI

@Requirement: Host collection

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    CLIFactoryError, make_org, make_host_collection, make_content_view,
    make_lifecycle_environment, make_content_host)
from robottelo.cli.hostcollection import HostCollection
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.constants import DEFAULT_CV, ENVIRONMENT
from robottelo.datafactory import valid_data_list, invalid_values_list
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.test import CLITestCase


class HostCollectionTestCase(CLITestCase):
    """Host Collection CLI tests."""

    org = None
    new_cv = None
    promoted_cv = None
    new_lifecycle = None
    library = None
    default_cv = None

    # pylint: disable=unexpected-keyword-arg
    def setUp(self):
        """Tests for Host Collections via Hammer CLI"""
        super(HostCollectionTestCase, self).setUp()

        if HostCollectionTestCase.org is None:
            HostCollectionTestCase.org = make_org(cached=True)
        if HostCollectionTestCase.new_lifecycle is None:
            HostCollectionTestCase.new_lifecycle = make_lifecycle_environment(
                {u'organization-id': HostCollectionTestCase.org['id']},
                cached=True
            )
        if HostCollectionTestCase.library is None:
            HostCollectionTestCase.library = LifecycleEnvironment.info({
                u'organization-id': HostCollectionTestCase.org['id'],
                u'name': ENVIRONMENT,
            })
        if HostCollectionTestCase.default_cv is None:
            HostCollectionTestCase.default_cv = ContentView.info({
                u'organization-id': HostCollectionTestCase.org['id'],
                u'name': DEFAULT_CV
            })
        if HostCollectionTestCase.new_cv is None:
            HostCollectionTestCase.new_cv = make_content_view(
                {u'organization-id': HostCollectionTestCase.org['id']}
            )
            HostCollectionTestCase.promoted_cv = None
            cv_id = HostCollectionTestCase.new_cv['id']
            ContentView.publish({u'id': cv_id})
            result = ContentView.version_list({u'content-view-id': cv_id})
            version_id = result[0]['id']
            ContentView.version_promote({
                u'id': version_id,
                u'organization-id': HostCollectionTestCase.org['id'],
                u'to-lifecycle-environment-id': (
                    HostCollectionTestCase.new_lifecycle['id']),
            })
            HostCollectionTestCase.promoted_cv = HostCollectionTestCase.new_cv

    def _new_host_collection(self, options=None):
        """Make a host collection and asserts its success"""
        if options is None:
            options = {}
        if not options.get('organization-id', None):
            options['organization-id'] = self.org['id']

        return make_host_collection(options)

    def _make_content_host_helper(self):
        """Make a new content host"""
        return make_content_host({
            u'content-view-id': self.default_cv['id'],
            u'lifecycle-environment-id': self.library['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.org['id'],
        })

    @tier1
    def test_positive_create_with_name(self):
        """Check if host collection can be created with random names

        @id: 40f1095a-cc1d-426e-b255-38319f5bd221

        @Assert: Host collection is created and has random name

        """
        for name in valid_data_list():
            with self.subTest(name):
                new_host_col = self._new_host_collection({'name': name})
                self.assertEqual(new_host_col['name'], name)

    @tier1
    def test_positive_create_with_description(self):
        """Check if host collection can be created with random
        description

        @id: 9736e3aa-bbc1-4c5f-98e9-b9dd18ba47ca

        @Assert: Host collection is created and has random description

        """
        for desc in valid_data_list():
            with self.subTest(desc):
                new_host_col = self._new_host_collection({'description': desc})
                self.assertEqual(new_host_col['description'], desc)

    @tier1
    def test_positive_create_with_limit(self):
        """Check if host collection can be created with random limits

        @id: 682b5624-1095-48e6-a0dd-c76e70ca6540

        @Assert: Host collection is created and has random limits

        """
        for limit in ('1', '3', '5', '10', '20'):
            with self.subTest(limit):
                new_host_col = self._new_host_collection(
                    {'max-hosts': limit})
                self.assertEqual(new_host_col['limit'], str(limit))

    @tier1
    def test_positive_create_with_unlimited_hosts(self):
        """Create Host Collection with different values of
        unlimited-hosts parameter

        @id: d688fd4a-88eb-484e-9e90-854e0595edd0

        @Assert: Host Collection is created and unlimited-hosts
        parameter is set
        """
        for unlimited in ('True', 'Yes', 1, 'False', 'No', 0):
            with self.subTest(unlimited):
                host_collection = make_host_collection({
                    'max-hosts':
                        1 if unlimited in ('False', 'No', 0) else None,
                    'organization-id': self.org['id'],
                    'unlimited-hosts': unlimited,
                })
                result = HostCollection.info({
                    'id': host_collection['id'],
                    'organization-id': self.org['id'],
                })
                if unlimited in ('True', 'Yes', 1):
                    self.assertEqual(result['limit'], 'None')
                else:
                    self.assertEqual(result['limit'], '1')

    @tier1
    def test_negative_create_with_name(self):
        """Check if host collection can be created with random names

        @id: 92a9eff0-693f-4ab8-b2c4-de08e5f709a7

        @Assert: Host collection is created and has random name

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._new_host_collection({'name': name})

    @tier1
    @skip_if_bug_open('bugzilla', 1328925)
    def test_positive_update_name(self):
        """Check if host collection name can be updated

        @id: 10d395e6-4ac6-4c35-a78c-c59a78c55799

        @Assert: Host collection is created and name is updated

        @BZ: 1328925
        """
        new_host_col = self._new_host_collection()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                HostCollection.update({
                    'id': new_host_col['id'],
                    'name': new_name,
                    'organization-id': self.org['id'],
                })
                result = HostCollection.info({'id': new_host_col['id']})
                self.assertEqual(result['name'], new_name)

    @tier1
    @skip_if_bug_open('bugzilla', 1328925)
    def test_positive_update_description(self):
        """Check if host collection description can be updated

        @id: 298b1f86-d4ab-4e10-a948-a0034826505f

        @Assert: Host collection is created and description is updated

        @BZ: 1328925
        """
        new_host_col = self._new_host_collection()
        for desc in valid_data_list():
            with self.subTest(desc):
                HostCollection.update({
                    'description': desc,
                    'id': new_host_col['id'],
                    'organization-id': self.org['id'],
                })
                result = HostCollection.info({'id': new_host_col['id']})
                self.assertEqual(result['description'], desc)

    @skip_if_bug_open('bugzilla', 1245334)
    @tier1
    def test_positive_update_limit(self):
        """Check if host collection limits be updated

        @id: 4c0e0c3b-82ac-4aa2-8378-6adc7946d4ec

        @Assert: Host collection limits is updated

        @BZ: 1245334

        """
        new_host_col = self._new_host_collection()
        for limit in ('3', '6', '9', '12', '15', '17', '19'):
            with self.subTest(limit):
                HostCollection.update({
                    'id': new_host_col['id'],
                    'max-hosts': limit,
                    'organization-id': self.org['id'],
                })
                result = HostCollection.info({'id': new_host_col['id']})
                self.assertEqual(result['limit'], limit)

    @tier1
    @skip_if_bug_open('bugzilla', 1328925)
    def test_positive_delete_by_id(self):
        """Check if host collection can be created and deleted

        @id: ef54a26e-a18f-4f29-8ef4-a7124785dbae

        @Assert: Host collection is created and then deleted

        @BZ: 1328925
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_host_col = self._new_host_collection({'name': name})
                HostCollection.delete({
                    'id': new_host_col['id'],
                    'organization-id': self.org['id'],
                })
                with self.assertRaises(CLIReturnCodeError):
                    HostCollection.info({'id': new_host_col['id']})

    @tier2
    def test_positive_add_host_by_id(self):
        """Check if content host can be added to host collection

        @id: db987da4-6326-43d5-a4c5-93a0c4da7f00

        @Assert: Host collection is created and content-host is added

        @CaseLevel: Integration
        """
        new_host_col = self._new_host_collection({
            'name': gen_string('alpha', 15)
        })
        new_system = self._make_content_host_helper()
        no_of_content_host = new_host_col['total-hosts']
        HostCollection.add_host({
            u'host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertGreater(result['total-hosts'], no_of_content_host)

    @tier2
    def test_positive_remove_host_by_id(self):
        """Check if content host can be removed from host collection

        @id: 61f4aab1-398b-4d3a-a4f4-f558ad8d2679

        @Assert: Host collection is created and content-host is removed

        @CaseLevel: Integration
        """
        new_host_col = self._new_host_collection({
            'name': gen_string('alpha', 15)
        })
        new_system = self._make_content_host_helper()
        HostCollection.add_host({
            u'host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        no_of_content_host = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })['total-hosts']
        HostCollection.remove_host({
            u'host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        self.assertGreater(no_of_content_host, result['total-hosts'])

    @tier2
    def test_positive_list_hosts(self):
        """Check if content hosts added to host collection is listed

        @id: 3075cb97-8448-4358-8ffc-0d5cd0078ca3

        @Assert: Content-host added to host-collection is listed

        @CaseLevel: Integration
        """
        host_col_name = gen_string('alpha', 15)
        new_host_col = self._new_host_collection({'name': host_col_name})
        new_system = self._make_content_host_helper()
        no_of_content_host = new_host_col['total-hosts']
        HostCollection.add_host({
            u'host-ids': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertGreater(result['total-hosts'], no_of_content_host)
        result = HostCollection.hosts({
            u'name': host_col_name,
            u'organization-id': self.org['id']
        })
        self.assertEqual(new_system['name'].lower(), result[0]['name'])

    @tier2
    def test_positive_host_collection_host_pagination(self):
        """Check if pagination configured on per-page param defined in hammer
        host-collection hosts command overrides global configuration defined
        on /etc/hammer/cli_config.yml, which default is 20 per page

        @BZ: 1343583

        @id: bbe1108b-bfb2-4a03-94ef-8fd1b5a0ec82

        @Assert: Number of host per page follows per_page configuration
        restriction

        @CaseLevel: Integration
        """
        host_collection = self._new_host_collection({
            'name': gen_string('alpha', 15)
        })
        host_ids = ','.join(
            self._make_content_host_helper()['id'] for i in range(2)
        )
        HostCollection.add_host({
            u'host-ids': host_ids,
            u'id': host_collection['id'],
            u'organization-id': self.org['id'],
        })

        for number in range(1, 3):
            listed_hosts = HostCollection.hosts({
                u'id': host_collection['id'],
                u'organization-id': self.org['id'],
                u'per-page': number
            })
            self.assertEqual(len(listed_hosts), number)
