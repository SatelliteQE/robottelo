"""CLI tests for RH Cloud - Inventory, aka Insights Inventory Upload

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


@pytest.mark.stubbed
def test_positive_inventory_generate_upload_cli():
    """Tests Insights inventory generation and upload via foreman-rake commands:
    https://github.com/theforeman/foreman_rh_cloud/blob/master/README.md

    :id: f2da9506-97d4-4d1c-b373-9f71a52b8ab8

    :Steps:

        0. Create a VM and register to insights within org having manifest.

        1. Generate and upload report for all organizations
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:generate_upload

        2. Generate and upload report for specific organization
            # export organization_id=1
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:generate_upload

        3. Generate report for specific organization (don't upload)
            # export organization_id=1
            # export target=/var/lib/foreman/red_hat_inventory/generated_reports/
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:generate

        4. Upload previously generated report
            (needs to be named 'report_for_#{organization_id}.tar.gz')
            # export organization_id=1
            # export target=/var/lib/foreman/red_hat_inventory/generated_reports/
            # /usr/sbin/foreman-rake rh_cloud_inventory:report:upload


    :expectedresults: Inventory is generated and uploaded to cloud.redhat.com.

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
    pass
