"""Test class foreman_rake

:Requirement: Other

:CaseAutomation: Automated

:CaseLevel: System

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
from robottelo import ssh
from robottelo.decorators import destructive
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import tier3


@destructive
@run_in_one_thread
@tier3
def test_positive_katello_reimport():
    """Close loop bug for running katello:reimport.  Making sure
    that katello:reimport works and doesn't throw an error.

    :CaseComponent: contentManagement

    :id: b4119265-1bf0-4b0b-8b96-43f68af39708

    :Steps: Have satellite up and run 'foreman-rake katello:reimport'

    :expectedresults: Successfully reimport without errors

    :bz: 1771555
    """

    result = ssh.command('foreman-rake katello:reimport')
    assert 'NoMethodError:' not in result.stdout
    assert 'rake aborted!' not in result.stdout
