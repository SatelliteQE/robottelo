# -*- encoding: utf-8 -*-
"""Tests for Oscappolicy

:Requirement: Oscappolicy

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SCAPPlugin

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.cli.ansible import Ansible
from robottelo.constants import OSCAP_PROFILE
from robottelo.decorators import tier1


@pytest.fixture(scope="module")
def module_location(module_location):
    yield module_location
    module_location.delete()


@pytest.fixture(scope="module")
def module_org(module_org):
    yield module_org
    module_org.delete()


@pytest.fixture(scope="module")
def scap_content(module_org, module_location, oscap_content_path):
    """ Import Ansible roles, Ansible variables, create Scap content."""
    # Import Ansible roles and variables.
    Ansible.roles_import({'proxy-id': 1})
    Ansible.variables_import({'proxy-id': 1})
    sc_title = gen_string('alpha')
    entity = entities.ScapContents().search(query={'search': f'title="{sc_title}"'})
    # Create Scap content.
    if not entity:
        result = entities.ScapContents(
            title=f"{sc_title}",
            scap_file=f"{oscap_content_path}",
            organization=[module_org],
            location=[module_location],
        ).create()
    else:
        result = entities.ScapContents(id=entity[0].id).read()
    scap_profile_id_rhel7 = [
        profile['id']
        for profile in result.scap_content_profiles
        if OSCAP_PROFILE['security7'] in profile['title']
    ][0]
    return (result, scap_profile_id_rhel7)


@pytest.fixture(scope="module")
def tailoring_file(module_org, module_location, tailoring_file_path):
    """ Create Tailoring file."""
    tf_name = gen_string('alpha')
    entity = entities.TailoringFile().search(query={'search': f'name="{tf_name}"'})
    if not entity:
        result = entities.TailoringFile(
            name=f"{tf_name}",
            scap_file=f"{tailoring_file_path}",
            organization=[module_org],
            location=[module_location],
        ).create()
    else:
        result = entities.TailoringFile(id=entity[0].id).read()
    tailor_profile_id = result.tailoring_file_profiles[0]['id']
    return (result, tailor_profile_id)


class TestOscapPolicy:
    """Implements Oscap Policy tests in API."""

    @tier1
    def test_positive_crud_scap_policy(
        self, module_org, module_location, scap_content, tailoring_file
    ):
        """Perform end to end testing for oscap policy component

        :id: d0706e49-2a00-4495-86ea-1b53a6776b6f

        :expectedresults: All expected CRUD actions finished successfully

        :CaseLevel: Integration

        :CaseImportance: High
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        description = gen_string('alpha')
        hostgroup = entities.HostGroup(
            location=[module_location], organization=[module_org]
        ).create()
        # Create new oscap policy with assigned content and tailoring file
        policy = entities.CompliancePolicies(
            name=name,
            deploy_by='puppet',
            description=description,
            scap_content_id=scap_content[0].id,
            scap_content_profile_id=scap_content[1],
            tailoring_file_id=tailoring_file[0].id,
            tailoring_file_profile_id=tailoring_file[1],
            period="monthly",
            day_of_month="5",
            hostgroup=[hostgroup],
            location=[module_location],
            organization=[module_org],
        ).create()
        assert entities.CompliancePolicies().search(query={'search': f'name="{name}"'})
        # Check that created entity has expected values
        assert policy.deploy_by == 'puppet'
        assert policy.name == name
        assert policy.description == description
        assert policy.scap_content_id == scap_content[0].id
        assert policy.scap_content_profile_id == scap_content[1]
        assert policy.tailoring_file_id == tailoring_file[0].id
        assert policy.period == "monthly"
        assert policy.day_of_month == 5
        assert policy.hostgroup[0].id == hostgroup.id
        assert policy.organization[0].id == module_org.id
        assert policy.location[0].id == module_location.id
        # Update oscap policy with new name
        policy = entities.CompliancePolicies(id=policy.id, name=new_name).update()
        assert policy.name == new_name
        assert not entities.CompliancePolicies().search(query={'search': f'name="{name}"'})
        # Delete oscap policy entity
        entities.CompliancePolicies(id=policy.id).delete()
        assert not entities.CompliancePolicies().search(query={'search': f'name="{new_name}"'})
