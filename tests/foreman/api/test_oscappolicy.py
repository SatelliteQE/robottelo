"""Tests for Oscappolicy

:Requirement: Oscappolicy

:CaseAutomation: Automated

:CaseComponent: SCAPPlugin

:Team: Endeavour

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest


class TestOscapPolicy:
    """Implements Oscap Policy tests in API."""

    @pytest.mark.tier1
    @pytest.mark.e2e
    def test_positive_crud_scap_policy(
        self, default_org, default_location, scap_content, tailoring_file, target_sat
    ):
        """Perform end to end testing for oscap policy component

        :id: d0706e49-2a00-4495-86ea-1b53a6776b6f

        :expectedresults: All expected CRUD actions finished successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        description = gen_string('alpha')
        hostgroup = target_sat.api.HostGroup(
            location=[default_location], organization=[default_org]
        ).create()
        # Create new oscap policy with assigned content and tailoring file
        policy = target_sat.api.CompliancePolicies(
            name=name,
            deploy_by='ansible',
            description=description,
            scap_content_id=scap_content["scap_id"],
            scap_content_profile_id=scap_content["scap_profile_id"],
            tailoring_file_id=tailoring_file["tailoring_file_id"],
            tailoring_file_profile_id=tailoring_file["tailoring_file_profile_id"],
            period="monthly",
            day_of_month="5",
            hostgroup=[hostgroup],
            location=[default_location],
            organization=[default_org],
        ).create()
        assert target_sat.api.CompliancePolicies().search(query={'search': f'name="{name}"'})
        # Check that created entity has expected values
        assert policy.deploy_by == 'ansible'
        assert policy.name == name
        assert policy.description == description
        assert str(policy.scap_content_id) == str(scap_content["scap_id"])
        assert str(policy.scap_content_profile_id) == str(scap_content["scap_profile_id"])
        assert str(policy.tailoring_file_id) == str(tailoring_file["tailoring_file_id"])
        assert policy.period == "monthly"
        assert int(policy.day_of_month) == 5
        assert str(policy.hostgroup[0].id) == str(hostgroup.id)
        assert str(policy.organization[0].id) == str(default_org.id)
        assert str(policy.location[0].id) == str(default_location.id)
        # Update oscap policy with new name
        policy = target_sat.api.CompliancePolicies(id=policy.id, name=new_name).update()
        assert policy.name == new_name
        assert not target_sat.api.CompliancePolicies().search(query={'search': f'name="{name}"'})
        # Delete oscap policy entity
        target_sat.api.CompliancePolicies(id=policy.id).delete()
        assert not target_sat.api.CompliancePolicies().search(
            query={'search': f'name="{new_name}"'}
        )
