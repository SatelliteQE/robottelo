# -*- encoding: utf-8 -*-
"""Test class for Host Collection CLI"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.factory import (
    CLIFactoryError, make_org, make_host_collection, make_content_view,
    make_lifecycle_environment, make_content_host)
from robottelo.cli.hostcollection import HostCollection
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
            HostCollectionTestCase.default_cv = ContentView.info(
                {u'organization-id': HostCollectionTestCase.org['id'],
                 u'name': DEFAULT_CV}
            )
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

    @tier1
    def test_positive_create_with_name(self):
        """Check if host collection can be created with random names

        @Feature: Host Collection

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

        @Feature: Host Collection

        @Assert: Host collection is created and has random description

        """
        for desc in valid_data_list():
            with self.subTest(desc):
                new_host_col = self._new_host_collection({'description': desc})
                self.assertEqual(new_host_col['description'], desc)

    @tier1
    def test_positive_create_with_limit(self):
        """Check if host collection can be created with random limits

        @Feature: Host Collection

        @Assert: Host collection is created and has random limits

        """
        for limit in ('1', '3', '5', '10', '20'):
            with self.subTest(limit):
                new_host_col = self._new_host_collection(
                    {'max-hosts': limit})
                self.assertEqual(new_host_col['limit'], str(limit))

    @skip_if_bug_open('bugzilla', 1214675)
    @tier1
    def test_positive_create_with_unlimited_hosts(self):
        """Create Host Collection with different values of
        unlimited-hosts parameter

        @Feature: Host Collection - Unlimited Hosts

        @Assert: Host Collection is created and unlimited-hosts
        parameter is set

        @BZ: 1214675

        """
        for unlimited in (u'True', u'Yes', 1, u'False', u'No', 0):
            with self.subTest(unlimited):
                host_collection = make_host_collection({
                    u'organization-id': self.org['id'],
                    u'unlimited-hosts': unlimited,
                })
                result = HostCollection.info({
                    u'id': host_collection['id'],
                    u'organization-id': self.org['id'],
                })
                if unlimited in (u'True', u'Yes', 1):
                    self.assertEqual(
                        result['unlimited-hosts'], u'true')
                else:
                    self.assertEqual(
                        result['unlimited-hosts'], u'false')

    @tier1
    def test_negative_create_with_name(self):
        """Check if host collection can be created with random names

        @Feature: Host Collection

        @Assert: Host collection is created and has random name

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._new_host_collection({'name': name})

    @tier1
    def test_positive_update_name(self):
        """Check if host collection name can be updated

        @Feature: Host Collection

        @Assert: Host collection is created and name is updated

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
    def test_positive_update_description(self):
        """Check if host collection description can be updated

        @Feature: Host Collection

        @Assert: Host collection is created and description is updated

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

        @Feature: Host Collection

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
    def test_positive_delete_by_id(self):
        """Check if host collection can be created and deleted

        @Feature: Host Collection

        @Assert: Host collection is created and then deleted

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

        @Feature: Host Collection

        @Assert: Host collection is created and content-host is added

        """
        new_host_col = self._new_host_collection({
            'name': gen_string('alpha', 15)})
        new_system = make_content_host({
            u'content-view-id': self.default_cv['id'],
            u'lifecycle-environment-id': self.library['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.org['id'],
        })
        no_of_content_host = new_host_col['total-hosts']
        HostCollection.add_host({
            u'hosts': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertGreater(result['total-hosts'], no_of_content_host)

    @tier2
    def test_positive_remove_chost_by_id(self):
        """Check if content host can be removed from host collection

        @Feature: Host Collection

        @Assert: Host collection is created and content-host is removed

        """
        new_host_col = self._new_host_collection({
            'name': gen_string('alpha', 15)})
        new_system = make_content_host({
            u'content-view-id': self.default_cv['id'],
            u'lifecycle-environment-id': self.library['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.org['id'],
        })
        HostCollection.add_host({
            u'hosts': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        no_of_content_host = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })['total-hosts']
        HostCollection.remove_host({
            u'hosts': new_system['id'],
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

        @Feature: Host Collection

        @Assert: Content-host added to host-collection is listed

        """
        host_col_name = gen_string('alpha', 15)
        new_host_col = self._new_host_collection({'name': host_col_name})
        new_system = make_content_host({
            u'content-view-id': self.default_cv['id'],
            u'lifecycle-environment-id': self.library['id'],
            u'name': gen_string('alpha', 15),
            u'organization-id': self.org['id'],
        })
        no_of_content_host = new_host_col['total-hosts']
        HostCollection.add_host({
            u'hosts': new_system['id'],
            u'id': new_host_col['id'],
            u'organization-id': self.org['id'],
        })
        result = HostCollection.info({
            u'id': new_host_col['id'],
            u'organization-id': self.org['id']
        })
        self.assertGreater(result['total-hosts'], no_of_content_host)
        result = HostCollection.content_hosts({
            u'name': host_col_name,
            u'organization-id': self.org['id']
        })
        self.assertEqual(new_system['id'], result[0]['id'])
