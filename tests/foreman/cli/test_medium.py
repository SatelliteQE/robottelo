"""Test for Medium  CLI

:Requirement: Medium

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_alphanumeric

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_os
from robottelo.cli.medium import Medium
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_data_list

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"
OSES = ['Archlinux', 'Debian', 'Gentoo', 'Redhat', 'Solaris', 'Suse', 'Windows']


class TestMedium:
    """Test class for Medium CLI"""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list().values()))
    def test_positive_crud_with_name(self, name):
        """Check if Medium can be created, updated, deleted

        :id: 66b749b2-0248-47a8-b78f-3366f3804b29

        :parametrized: yes

        :expectedresults: Medium is created


        :CaseImportance: Critical
        """
        medium = make_medium({'name': name})
        assert medium['name'] == name
        new_name = gen_alphanumeric(6)
        Medium.update({'name': medium['name'], 'new-name': new_name})
        medium = Medium.info({'id': medium['id']})
        assert medium['name'] == new_name
        Medium.delete({'id': medium['id']})
        with pytest.raises(CLIReturnCodeError):
            Medium.info({'id': medium['id']})

    @pytest.mark.tier1
    def test_positive_create_with_location(self):
        """Check if medium with location can be created

        :id: cbc6c586-fae7-4bb9-aeb1-e30158f16a98

        :expectedresults: Medium is created and has new location assigned


        :CaseImportance: Medium
        """
        location = make_location()
        medium = make_medium({'location-ids': location['id']})
        assert location['name'] in medium['locations']

    @pytest.mark.tier1
    def test_positive_create_with_organization_by_id(self):
        """Check if medium with organization can be created

        :id: 631bb6ed-e42b-482a-83f0-f6ce0f20729a

        :expectedresults: Medium is created and has new organization assigned


        :CaseImportance: Medium
        """
        org = make_org()
        medium = make_medium({'organization-ids': org['id']})
        assert org['name'] in medium['organizations']

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_remove_os(self):
        """Check if Medium can be associated with operating system and then removed from media

        :id: 23b5b55b-3624-440c-8001-75c7c5a5a004

        :expectedresults: Operating system removed


        :CaseLevel: Integration
        """
        medium = make_medium()
        os = make_os()
        Medium.add_operating_system({'id': medium['id'], 'operatingsystem-id': os['id']})
        medium = Medium.info({'id': medium['id']})
        assert os['title'] in medium['operating-systems']
        Medium.remove_operating_system({'id': medium['id'], 'operatingsystem-id': os['id']})
        medium = Medium.info({'id': medium['id']})
        assert os['name'] not in medium['operating-systems']
