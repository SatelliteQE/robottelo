"""Tests for Oscapcontent

:Requirement: Oscapcontent

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os

import pytest

from robottelo.config import robottelo_tmp_dir
from robottelo.config import settings
from robottelo.constants import DataFile
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def oscap_content_path(module_target_sat):
    _, file_name = os.path.split(settings.oscap.content_path)

    local_file = robottelo_tmp_dir.joinpath(file_name)
    module_target_sat.get(remote_path=settings.oscap.content_path, local_path=local_file)
    return local_file


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_end_to_end(
    session, oscap_content_path, target_sat, default_org, default_location
):
    """Perform end to end testing for openscap content component

    :id: 9870555d-0b60-41ab-a481-81d4d3f78fec

    :Steps:

        1. Create an openscap content.
        2. Read values from created entity.
        3. Update the openscap content with new name.
        4. Delete openscap content

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration
    """
    title = gen_string('alpha')
    new_title = gen_string('alpha')
    with session:
        session.organization.select(org_name=default_org.name)
        session.location.select(loc_name=default_location.name)
        session.oscapcontent.create(
            {
                'file_upload.title': title,
                'file_upload.scap_file': oscap_content_path,
                'organizations.resources.assigned': [default_org.name],
                'locations.resources.assigned': [default_location.name],
            }
        )
        oscap_values = session.oscapcontent.read(title)
        assert oscap_values['file_upload']['title'] == title
        assert oscap_values['file_upload']['uploaded_scap_file'] == oscap_content_path.name
        assert default_org.name in oscap_values['organizations']['resources']['assigned']
        assert default_location.name in oscap_values['locations']['resources']['assigned']
        session.oscapcontent.update(title, {'file_upload.title': new_title})
        session.location.search('abc')  # workaround for issue SatelliteQE/airgun#382.
        assert session.oscapcontent.search(new_title)[0]['Title'] == new_title
        session.location.search('abc')
        assert not session.oscapcontent.search(title)
        session.location.search('abc')
        session.oscapcontent.delete(new_title)
        session.location.search('abc')
        assert not session.oscapcontent.search(new_title)


@pytest.mark.tier1
def test_negative_create_with_same_name(session, oscap_content_path, default_org, default_location):
    """Create OpenScap content with same name

    :id: f5c6491d-b83c-4ca2-afdf-4bb93e6dd92b

    :Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.
        3. Create openscap content with same name

    :expectedresults: Creating content for OpenScap is not successful.

    :BZ: 1474172

    :customerscenario: true

    :CaseImportance: Medium
    """
    content_name = gen_string('alpha')
    with session:
        session.organization.select(org_name=default_org.name)
        session.location.select(loc_name=default_location.name)
        session.oscapcontent.create(
            {'file_upload.title': content_name, 'file_upload.scap_file': oscap_content_path}
        )
        assert session.oscapcontent.search(content_name)[0]['Title'] == content_name
        with pytest.raises(AssertionError) as context:
            session.oscapcontent.create(
                {'file_upload.title': content_name, 'file_upload.scap_file': oscap_content_path}
            )
        assert 'has already been taken' in str(context.value)


@pytest.mark.tier1
def test_external_disa_scap_content(session, default_org, default_location):
    """Create OpenScap content with external DISA SCAP content.

    :id: 5f29254e-7c15-45e1-a2ec-4da1d3d8d74d

    :Steps:

        1. Create an openscap content with external DISA SCAP content.
        2. Assert that openscap content has been created.

    :expectedresults: External DISA SCAP content uploaded successfully.

    :BZ: 2053478

    :customerscenario: true

    :CaseImportance: Medium
    """
    content_name = gen_string('alpha')
    with session:
        session.organization.select(org_name=default_org.name)
        session.location.select(loc_name=default_location.name)
        session.oscapcontent.create(
            {
                'file_upload.title': content_name,
                'file_upload.scap_file': DataFile.DATA_DIR.joinpath(
                    'U_RHEL_7_V3R6_STIG_SCAP_1-2_Benchmark.xml'
                ),
            }
        )
        assert session.oscapcontent.search(content_name)[0]['Title'] == content_name
