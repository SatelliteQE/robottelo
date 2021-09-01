"""Test class for Dynflow

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Dynflow

:Assignee: lhellebr

:Requirement: Dynflow

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


@pytest.mark.tier2
def test_positive_setup_dynflow(default_sat):
    """Set dynflow parameters, restart it and check it adheres to them

    :id: a5aaab5e-bc18-453e-a284-64aef752ec88

    :expectedresults: Correct dynflow processes are running, respecting settings
    """
    commands = [
        'cd /etc/foreman/dynflow/',
        'cp worker-hosts-queue.yml test.yml',
        'sed -i s/5/6/ test.yml',
        "systemctl restart 'dynflow-sidekiq@test'",
        "while ! systemctl status 'dynflow-sidekiq@test' -l | "  # no comma here
        "grep -q ' of 6 busy' ; do sleep 0.5 ; done",
    ]
    # if thread count is not respected or the process is not running, this should timeout
    # how is this a test? Nothing is asserted.
    default_sat.execute(' && '.join(commands))
    default_sat.execute("systemctl stop 'dynflow-sidekiq@test'; rm /etc/foreman/dynflow/test.yml")
