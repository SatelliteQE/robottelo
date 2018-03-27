# -*- encoding: utf-8 -*-
"""Test class for Host CLI

:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_alphanumeric, gen_string
from math import ceil
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_lifecycle_environment, make_org
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.constants import ENVIRONMENT
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_only_on, tier1, upgrade
from robottelo.test import CLITestCase


class LifeCycleEnvironmentTestCase(CLITestCase):
    """Test class for Lifecycle Environment CLI"""

    org = None

    @classmethod
    def setUpClass(cls):
        """Create a new Test Case Organization"""
        super(LifeCycleEnvironmentTestCase, cls).setUpClass()
        cls.org = make_org()

    # Issues validation
    @run_only_on('sat')
    @tier1
    def test_verify_bugzilla_1077386(self):
        """List subcommand returns standard output

        :id: cca249d0-fb77-422b-aae3-3361887269db

        :expectedresults: There should not be an error returned


        :CaseImportance: Critical
        """

        # List available lifecycle environments using default Table
        # output
        cmd = u'lifecycle-environment list --organization-id="%s"'
        result = LifecycleEnvironment.execute(
            cmd % self.org['id'],
            None,
            None,
            False,
        )
        self.assertGreater(len(result), 0)

    @run_only_on('sat')
    @tier1
    def test_verify_bugzilla_1077333(self):
        """Search lifecycle environment via its name containing UTF-8
        chars

        :id: d15001ed-5bbf-43cf-bdd3-1e129dff14ec

        :expectedresults: Can get info for lifecycle by its name


        :CaseImportance: Critical
        """
        test_data = {
            'name': gen_string('utf8', 15),
            'organization-id': self.org['id'],
        }
        # Can we find the new object
        result = LifecycleEnvironment.info({
            'name': make_lifecycle_environment(test_data)['name'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result['name'], test_data['name'])

    # CRUD
    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create lifecycle environment with valid name, prior to
        Library

        :id: fffe67e2-9a45-478d-a538-99f04a9c40ff

        :expectedresults: Lifecycle environment is created with Library as
            prior


        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                lc_env = make_lifecycle_environment({
                    'name': name,
                    'organization-id': self.org['id'],
                })
                self.assertEqual(
                    lc_env['prior-lifecycle-environment'], ENVIRONMENT)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_description(self):
        """Create lifecycle environment with valid description prior to
        Library

        :id: 714c42f8-d09e-4e48-9f35-bbc25fe9e229

        :expectedresults: Lifecycle environment is created with Library as
            prior


        :CaseImportance: Critical
        """
        for desc in valid_data_list():
            name = gen_alphanumeric()
            with self.subTest(desc):
                lc_env = make_lifecycle_environment({
                    'description': desc,
                    'name': name,
                    'organization-id': self.org['id'],
                })
                self.assertEqual(lc_env['name'], name)
                self.assertEqual(lc_env['description'], desc)
                self.assertEqual(
                    lc_env['prior-lifecycle-environment'], ENVIRONMENT)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_label(self):
        """Create lifecycle environment with valid name and label

        :id: 8d82932f-dedf-46f0-a6dc-280cfb228f44

        :expectedresults: Lifecycle environment with label is created


        :CaseImportance: Critical
        """
        for label in (gen_string("alpha", 15), gen_string("alphanumeric", 15),
                      gen_string("numeric", 15)):
            with self.subTest(label):
                new_lce = make_lifecycle_environment({
                    'label': label,
                    'name': gen_alphanumeric(),
                    'organization-id': self.org['id'],
                })
                self.assertEqual(new_lce['label'], label)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_organization_name(self):
        """Create lifecycle environment, specifying organization name

        :id: e62ddb5a-7a38-4b7c-9346-b4dce31448c1

        :expectedresults: Lifecycle environment is created for correct
            organization


        :CaseImportance: Critical
        """
        new_lce = make_lifecycle_environment({
            'name': gen_string('alpha'),
            'organization': self.org['name'],
        })
        self.assertEqual(new_lce['organization'], self.org['name'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_organization_label(self):
        """Create lifecycle environment, specifying organization label

        :id: eb5cfc71-c83d-45ca-ba34-9ef79197691d

        :expectedresults: Lifecycle environment is created for correct
            organization


        :CaseImportance: Critical
        """
        new_lce = make_lifecycle_environment({
            'name': gen_string('alpha'),
            'organization-label': self.org['label'],
        })
        self.assertEqual(new_lce['organization'], self.org['name'])

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Create lifecycle environment with valid name, prior to
        Library

        :id: 76989039-5389-4136-9f7c-220eb38f157b

        :expectedresults: Lifecycle environment is deleted


        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_lce = make_lifecycle_environment({
                    'name': name,
                    'organization-id': self.org['id'],
                })
                LifecycleEnvironment.delete({'id': new_lce['id']})
                with self.assertRaises(CLIReturnCodeError):
                    LifecycleEnvironment.info({
                        'id': new_lce['id'],
                        'organization-id': self.org['id'],
                    })

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Create lifecycle environment then update its name

        :id: de67a44e-6c6a-430e-927b-4fa43c7c2771

        :expectedresults: Lifecycle environment name is updated


        :CaseImportance: Critical
        """
        new_lce = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })
        for new_name in valid_data_list():
            with self.subTest(new_name):
                LifecycleEnvironment.update({
                    'id': new_lce['id'],
                    'new-name': new_name,
                    'organization-id': self.org['id'],
                })
                result = LifecycleEnvironment.info({
                    'id': new_lce['id'],
                    'organization-id': self.org['id'],
                })
                self.assertGreater(len(result), 0)
                self.assertEqual(result['name'], new_name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Create lifecycle environment then update its description

        :id: 15b82949-3c3a-4942-b42b-db1de34cf5be

        :expectedresults: Lifecycle environment description is updated


        :CaseImportance: Critical
        """
        new_lce = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                LifecycleEnvironment.update({
                    'description': new_desc,
                    'id': new_lce['id'],
                    'organization-id': self.org['id'],
                })
                result = LifecycleEnvironment.info({
                    'id': new_lce['id'],
                    'organization-id': self.org['id'],
                })
                self.assertGreater(len(result), 0)
                self.assertEqual(result['description'], new_desc)

    @run_only_on('sat')
    @tier1
    def test_positve_list_paths(self):
        """List the environment paths under a given organization

        :id: 71600d6b-1ef4-4b88-8e9b-eb2481ee1fe2

        :expectedresults: Lifecycle environment paths listed


        :CaseImportance: Critical
        """
        org = make_org()
        lc_env = make_lifecycle_environment({
            'organization-id': org['id'],
        })
        # Add paths to lifecycle environments
        result = LifecycleEnvironment.paths({
            'organization-id': org['id'],
            'permission-type': 'readable',
        })
        self.assertIn(
            u'Library >> {0}'.format(lc_env['name']),
            u''.join(result)
        )


class LifeCycleEnvironmentPaginationTestCase(CLITestCase):
    """Test class for LifeCycle Environment pagination tests"""

    @classmethod
    def setUpClass(cls):
        """Create organization and lifecycle environments to reuse in tests
        """
        super(LifeCycleEnvironmentPaginationTestCase, cls).setUpClass()
        cls.lces_count = 25
        cls.org = make_org()
        env_base_name = gen_string('alpha')
        last_env_name = ENVIRONMENT
        cls.env_names = [last_env_name]
        for env_index in range(cls.lces_count):
            env_name = '{0}-{1}'.format(env_base_name, env_index)
            make_lifecycle_environment({
                'name': env_name,
                'organization-id': cls.org['id'],
                'prior': last_env_name
            })
            last_env_name = env_name
            cls.env_names.append(env_name)

        cls.lces_count += 1  # include default 'Library' lce

    @run_only_on('sat')
    @tier1
    def test_positive_list_all_with_per_page(self):
        """Attempt to list more than 20 lifecycle environment with per-page
        option.

        :id: 6e10fb0e-5e2c-45e6-85a8-0c853450257b

        :BZ: 1420503

        :expectedresults: all the Lifecycle environments are listed

        :CaseImportance: Critical
        """
        per_page_count = self.lces_count + 5

        lifecycle_environments = LifecycleEnvironment.list({
            'organization-id': self.org['id'],
            'per-page': per_page_count
        })

        self.assertEqual(len(lifecycle_environments), self.lces_count)
        env_name_set = {env['name'] for env in lifecycle_environments}
        self.assertEqual(env_name_set, set(self.env_names))

    @run_only_on('sat')
    @tier1
    def test_positive_list_with_pagination(self):
        """Make sure lces list can be displayed with different items per page
        value

        :id: 28ecbc1f-bb5c-49df-a586-8cfdc0dd57df

        :BZ: 1368590

        :expectedresults: `per-page` correctly sets amount of items displayed
            per page, different `per-page` values divide a list into correct
            number of pages

        :CaseImportance: Critical
        """
        # Test different `per-page` values
        for per_page in (1, 5, 20):
            with self.subTest(per_page):
                # Verify the first page contains exactly the same items count
                # as `per-page` value
                lces = LifecycleEnvironment.list({
                    'organization-id': self.org['id'],
                    'per-page': per_page,
                })
                self.assertEqual(len(lces), per_page)
                # Verify pagination and total amount of pages by checking the
                # items count on the last page
                last_page = ceil(self.lces_count / per_page)
                lces = LifecycleEnvironment.list({
                    'organization-id': self.org['id'],
                    'page': last_page,
                    'per-page': per_page,
                })
                self.assertEqual(
                    len(lces), self.lces_count % per_page or per_page)
