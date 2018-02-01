# -*- encoding: utf-8 -*-
"""Test class for Puppet Module UI

:Requirement: Puppet Module

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.decorators import tier1
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.session import Session


class PuppetModuleTestCase(UITestCase):
    """Implement tests for puppet modules content search via UI"""

    @classmethod
    def setUpClass(cls):
        super(PuppetModuleTestCase, cls).setUpClass()
        product = entities.Product(organization=cls.session_org).create()
        cls.repo = entities.Repository(
            product=product,
            content_type='puppet',
        ).create()
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            cls.repo.upload_content(files={'content': handle})

    @classmethod
    def set_session_org(cls):
        """Creates new organization to be used for current session the
        session_user will login automatically with this org in context
        """
        cls.session_org = entities.Organization().create()

    @tier1
    def test_positive_search_in_repo(self):
        """Create product with puppet repository assigned to it. Search for
        modules inside of it

        :id: 86af4bff-a404-453e-b05a-912ac8aeb52d

        :expectedresults: Content search functionality works as intended and
            expected puppet modules are present inside of repository

        :CaseImportance: Critical
        """
        with Session(self):
            self.assertIsNotNone(self.puppetmodule.search('ntp'))

    @tier1
    def test_positive_search_scoped(self):
        """Create product with puppet repository assigned to it. Search for
        modules inside of it using different criteria (e.g. 'author')

        :id: eb1318dd-0268-48c1-8e62-9747207698b2

        :customerscenario: true

        :expectedresults: Scoped search functionality works as intended

        :BZ: 1259374

        :CaseImportance: High
        """
        with Session(self):
            for query_type, query_value in [
                ('author', 'puppetlabs'),
                ('version', '3.2.1'),
                ('summary', 'NTP Module')
            ]:
                self.assertIsNotNone(
                    self.puppetmodule.search(
                        'ntp',
                        _raw_query='{} = "{}"'.format(query_type, query_value)
                    )
                )

    @tier1
    def test_positive_check_puppet_details(self):
        """Create product with puppet repository assigned to it. Search for
        module inside of it and then open it. Check all the details about that
        puppet module

        :id: 15dc567c-1e9a-4008-a3bc-40c1dbd69ae1

        :expectedresults: Puppet module is present inside of repository and has
            all expected values in details section

        :CaseImportance: Critical
        """
        with Session(self):
            self.puppetmodule.check_puppet_details(
                'ntp',
                [
                    ['Author', 'puppetlabs'],
                    ['Version', '3.2.1'],
                    ['Source', 'https://github.com/puppetlabs/puppetlabs-ntp'],
                    [
                        'Project Page',
                        'https://github.com/puppetlabs/puppetlabs-ntp'
                    ],
                    ['License', 'Apache Version 2.0'],
                    [
                        'Description',
                        'NTP Module for Debian, Ubuntu, CentOS, RHEL, OEL, '
                        'Fedora, FreeBSD, ArchLinux and Gentoo.'
                    ],
                    ['Summary', 'NTP Module'],
                ]
            )

    @tier1
    def test_positive_check_puppet_repo_list(self):
        """Create product with puppet repository assigned to it. Search for
        module inside of it and then open it. Check that proper repositories
        are displayed for Puppet Module in Library Repositories tab

        :id: 7de4325c-905a-4fde-8e30-01a6a40b9e31

        :expectedresults: Puppet module is present inside of repository and has
            proper repositories assigned to

        :CaseImportance: Critical
        """
        with Session(self):
            self.puppetmodule.check_repo('ntp', [self.repo.name])
