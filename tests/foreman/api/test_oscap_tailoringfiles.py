"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo.datafactory import gen_string


class TestTailoringFile:
    """Implements Tailoring Files tests in API."""

    @pytest.mark.tier1
    def test_positive_crud_tailoringfile(self, default_org, default_location, tailoring_file_path):
        """Perform end to end testing for oscap tailoring files component

        :id: 2441988f-2054-49f7-885e-3675336f712f

        :expectedresults: All expected CRUD actions finished successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        original_filename = gen_string('alpha')
        scap = entities.TailoringFile(
            name=name,
            scap_file=tailoring_file_path['local'],
            organization=[default_org],
            location=[default_location],
        ).create()
        assert entities.TailoringFile().search(query={'search': f'name={name}'})
        result = entities.TailoringFile(id=scap.id).read()
        assert result.name == name
        assert result.location[0].id == default_location.id
        assert result.organization[0].id == default_org.id
        scap = entities.TailoringFile(
            id=scap.id, name=new_name, original_filename=f'{original_filename}'
        ).update()
        result = entities.TailoringFile(id=scap.id).read()
        assert result.name == new_name
        assert result.original_filename == original_filename
        assert entities.TailoringFile().search(query={'search': f'name={new_name}'})
        entities.TailoringFile(id=scap.id).delete()
        assert not entities.TailoringFile().search(query={'search': f'name={new_name}'})
