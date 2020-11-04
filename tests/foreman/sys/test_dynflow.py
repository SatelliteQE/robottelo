"""Test class for Dynflow

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Dynflow

:Requirement: Dynflow

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo import ssh
from robottelo.test import TestCase


class DynflowTestCase(TestCase):
    """Dynflow tests"""

    @pytest.mark.tier2
    def test_positive_setup_dynflow(self):
        """Set dynflow parameters, restart it and check it adheres to them

        :id: a5aaab5e-bc18-453e-a284-64aef752ec88

        :expectedresults: Correct dynflow processes are running, respecting settings

        :CaseImportance: High
        """
        commands = [
            "cd /etc/foreman/dynflow/",
            "cp worker-hosts-queue.yml test.yml",
            "sed -i s/5/6/ test.yml",
            "systemctl restart 'dynflow-sidekiq@test'",
            "while ! systemctl status 'dynflow-sidekiq@test' -l | "  # no comma here
            "grep -q ' of 6 busy' ; do sleep 0.5 ; done",
        ]
        # if thread count is not respected or the process is not running, this should timeout
        ssh.command(" && ".join(commands))
        ssh.command("systemctl stop 'dynflow-sidekiq@test'; rm /etc/foreman/dynflow/test.yml")
