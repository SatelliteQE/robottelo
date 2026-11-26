"""Tests For Disconnected Satellite Installation

:Requirement: Installation (disconnected satellite installation)

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Platform

:CaseImportance: High

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
