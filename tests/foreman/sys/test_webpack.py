"""Test class for Webpack

:CaseAutomation: Automated

:CaseComponent: Installation

:Requirement: Installation

:Team: Endeavour

:CaseImportance: High

"""

import pytest


@pytest.mark.tier2
def test_positive_webpack5(target_sat):
    """Check whether Webpack 5 was used at packaging time

    :id: b7f3fbb2-ef4b-4634-877f-b8ea10373e04

    :Verifies: SAT-5741

    :expectedresults: There is a file "public/webpack/foreman_tasks/foreman_tasks_remoteEntry.js" when Webpack 5 has been used. It used to be "public/webpack/foreman-tasks-<ID>.js" before.
    """
    assert (
        target_sat.execute(
            "find /usr/share/gems | grep public/webpack/foreman_tasks/foreman_tasks_remoteEntry.js"
        ).status
        == 0
    )
