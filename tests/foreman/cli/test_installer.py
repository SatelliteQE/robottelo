"""Tests For Disconnected Satellite Installation

:Requirement: Installer (disconnected satellite installation)

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Installer

:Assignee: rmynar

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

pytestmark = [pytest.mark.stubbed]


# Notes for installer testing:
# Perhaps there is a convenient log analyzer library out there
# that can parse logs? It would be better (and possibly less
# error-prone) than simply grepping for ERROR/FATAL


def test_positive_server_installer_from_iso():
    """Can install product from ISO

    :id: 38c08646-9f71-48d9-a9c2-66bd94c3e5bb

    :expectedresults: Install from ISO is successful.

    :CaseAutomation: NotAutomated
    """


def test_positive_disconnected_util_installer():
    """Can install  satellite disconnected utility successfully
    via RPM

    :id: b738cf2a-9c5f-4865-b134-102a4688534c

    :expectedresults: Install of disconnected utility successful.

    :CaseAutomation: NotAutomated
    """
