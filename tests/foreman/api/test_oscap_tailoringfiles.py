"""Test class for Tailoring Files

:Requirement: tailoringfiles

:CaseAutomation: Automated

:CaseComponent: SCAPPlugin

:Team: Endeavour

:CaseImportance: High

"""

import pytest

from robottelo.utils.datafactory import gen_string


class TestTailoringFile:
    """Implements Tailoring Files tests in API."""

    @pytest.mark.tier1
    @pytest.mark.e2e
    def test_positive_crud_tailoringfile(
        self, default_org, default_location, tailoring_file_path, target_sat
    ):
        """Perform end to end testing for oscap tailoring files component

        :id: 2441988f-2054-49f7-885e-3675336f712f

        :expectedresults: All expected CRUD actions finished successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        original_filename = gen_string('alpha')
        scap = target_sat.api.TailoringFile(
            name=name,
            scap_file=tailoring_file_path['local'],
            organization=[default_org],
            location=[default_location],
        ).create()
        assert target_sat.api.TailoringFile().search(query={'search': f'name={name}'})
        result = target_sat.api.TailoringFile(id=scap.id).read()
        assert result.name == name
        assert result.location[0].id == default_location.id
        assert result.organization[0].id == default_org.id
        scap = target_sat.api.TailoringFile(
            id=scap.id, name=new_name, original_filename=f'{original_filename}'
        ).update()
        result = target_sat.api.TailoringFile(id=scap.id).read()
        assert result.name == new_name
        assert result.original_filename == original_filename
        assert target_sat.api.TailoringFile().search(query={'search': f'name={new_name}'})
        target_sat.api.TailoringFile(id=scap.id).delete()
        assert not target_sat.api.TailoringFile().search(query={'search': f'name={new_name}'})
