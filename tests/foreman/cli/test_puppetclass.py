"""Test class for Puppet Classes CLI

:Requirement: Puppetclass

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.config import settings


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason="Missing repos_hosting_url")
def test_positive_list_smart_class_parameters(
    module_import_puppet_module, session_puppet_enabled_sat
):
    """List smart class parameters associated with the puppet class.

    :id: 56b370c2-8fc6-49be-9676-242178cc709a

    :expectedresults: Smart class parameters listed for the class.
    """
    class_sc_parameters = session_puppet_enabled_sat.cli.Puppet.sc_params(
        {'puppet-class': module_import_puppet_module['puppet_class']}
    )
    assert len(class_sc_parameters) == 200
