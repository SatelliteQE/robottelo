# -*- encoding: utf-8 -*-
"""Test for Medium  CLI

:Requirement: Medium

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_alphanumeric
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location, make_medium, make_org, make_os
from robottelo.cli.medium import Medium
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1, tier2, upgrade
from robottelo.test import CLITestCase

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"
OSES = [
    'Archlinux',
    'Debian',
    'Gentoo',
    'Redhat',
    'Solaris',
    'Suse',
    'Windows',
]


class MediumTestCase(CLITestCase):
    """Test class for Medium CLI"""
    @tier1
    def test_positive_create_with_name(self):
        """Check if Medium can be created

        :id: 4a1caaf8-4401-48cc-85ad-e7189944688d

        :expectedresults: Medium is created


        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                medium = make_medium({'name': name})
                self.assertEqual(medium['name'], name)

    @tier1
    def test_positive_create_with_location(self):
        """Check if medium with location can be created

        :id: cbc6c586-fae7-4bb9-aeb1-e30158f16a98

        :expectedresults: Medium is created and has new location assigned


        :CaseImportance: Medium
        """
        location = make_location()
        medium = make_medium({'location-ids': location['id']})
        self.assertIn(location['name'], medium['locations'])

    @tier1
    def test_positive_create_with_organization_by_id(self):
        """Check if medium with organization can be created

        :id: 631bb6ed-e42b-482a-83f0-f6ce0f20729a

        :expectedresults: Medium is created and has new organization assigned


        :CaseImportance: Medium
        """
        org = make_org()
        medium = make_medium({'organization-ids': org['id']})
        self.assertIn(org['name'], medium['organizations'])

    @tier1
    def test_positive_delete_by_id(self):
        """Check if Medium can be deleted

        :id: dc62c9ad-d2dc-42df-80eb-02cf8d26cdee

        :expectedresults: Medium is deleted


        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                medium = make_medium({'name': name})
                Medium.delete({'id': medium['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Medium.info({'id': medium['id']})

    # pylint: disable=no-self-use
    @tier2
    def test_positive_add_os(self):
        """Check if Medium can be associated with operating system

        :id: 47d1e6f0-d8a6-4190-b2ac-41b09a559429

        :expectedresults: Operating system added


        :CaseLevel: Integration
        """
        medium = make_medium()
        os = make_os()
        Medium.add_operating_system({
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        })

    @tier2
    @upgrade
    def test_positive_remove_os(self):
        """Check if operating system can be removed from media

        :id: 23b5b55b-3624-440c-8001-75c7c5a5a004

        :expectedresults: Operating system removed


        :CaseLevel: Integration
        """
        medium = make_medium()
        os = make_os()
        Medium.add_operating_system({
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        })
        medium = Medium.info({'id': medium['id']})
        self.assertIn(os['title'], medium['operating-systems'])
        Medium.remove_operating_system({
            'id': medium['id'],
            'operatingsystem-id': os['id'],
        })
        medium = Medium.info({'id': medium['id']})
        self.assertNotIn(os['name'], medium['operating-systems'])

    @tier1
    def test_positive_update_name(self):
        """Check if medium can be updated

        :id: 2111090a-21d3-47f7-bb81-5f19ab71a91d

        :expectedresults: Medium updated


        :CaseImportance: Medium
        """
        new_name = gen_alphanumeric(6)
        medium = make_medium()
        Medium.update({
            'name': medium['name'],
            'new-name': new_name,
        })
        medium = Medium.info({'id': medium['id']})
        self.assertEqual(medium['name'], new_name)
