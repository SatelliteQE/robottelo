"""Test for Medium  CLI

:Requirement: Medium

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_alphanumeric
import pytest

from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import parametrized, valid_data_list

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"
OSES = ['Archlinux', 'Debian', 'Gentoo', 'Redhat', 'Solaris', 'Suse', 'Windows']


class TestMedium:
    """Test class for Medium CLI"""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list().values()))
    def test_positive_crud_with_name(self, name, module_target_sat):
        """Check if Medium can be created, updated, deleted

        :id: 66b749b2-0248-47a8-b78f-3366f3804b29

        :parametrized: yes

        :expectedresults: Medium is created


        :CaseImportance: Critical
        """
        medium = module_target_sat.cli_factory.make_medium({'name': name})
        assert medium['name'] == name
        new_name = gen_alphanumeric(6)
        module_target_sat.cli.Medium.update({'name': medium['name'], 'new-name': new_name})
        medium = module_target_sat.cli.Medium.info({'id': medium['id']})
        assert medium['name'] == new_name
        module_target_sat.cli.Medium.delete({'id': medium['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Medium.info({'id': medium['id']})

    @pytest.mark.tier1
    def test_positive_create_with_location(self, module_target_sat):
        """Check if medium with location can be created

        :id: cbc6c586-fae7-4bb9-aeb1-e30158f16a98

        :expectedresults: Medium is created and has new location assigned


        :CaseImportance: Medium
        """
        location = module_target_sat.cli_factory.make_location()
        medium = module_target_sat.cli_factory.make_medium({'location-ids': location['id']})
        assert location['name'] in medium['locations']

    @pytest.mark.tier1
    def test_positive_create_with_organization_by_id(self, module_target_sat):
        """Check if medium with organization can be created

        :id: 631bb6ed-e42b-482a-83f0-f6ce0f20729a

        :expectedresults: Medium is created and has new organization assigned


        :CaseImportance: Medium
        """
        org = module_target_sat.cli_factory.make_org()
        medium = module_target_sat.cli_factory.make_medium({'organization-ids': org['id']})
        assert org['name'] in medium['organizations']

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_remove_os(self, module_target_sat):
        """Check if Medium can be associated with operating system and then removed from media

        :id: 23b5b55b-3624-440c-8001-75c7c5a5a004

        :expectedresults: Operating system removed


        """
        medium = module_target_sat.cli_factory.make_medium()
        os = module_target_sat.cli_factory.make_os()
        module_target_sat.cli.Medium.add_operating_system(
            {'id': medium['id'], 'operatingsystem-id': os['id']}
        )
        medium = module_target_sat.cli.Medium.info({'id': medium['id']})
        assert os['title'] in medium['operating-systems']
        module_target_sat.cli.Medium.remove_operating_system(
            {'id': medium['id'], 'operatingsystem-id': os['id']}
        )
        medium = module_target_sat.cli.Medium.info({'id': medium['id']})
        assert os['name'] not in medium['operating-systems']
