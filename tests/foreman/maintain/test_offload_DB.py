"""Test class for Offload DB functionality

:Requirement: Offload DBs from Satellite Server

:CaseAutomation: ManualOnly

:CaseComponent: SatelliteMaintain

:Team: Platform

:CaseImportance: High

"""

import pytest

from robottelo.config import settings


@pytest.mark.stubbed
@pytest.mark.skipif((not settings.remotedb.server), reason='Intended only for RemoteDB setup')
def test_offload_internal_db_to_external_db_host():
    """Offload internal databases content to an external database host

    :id: d07235c8-4584-469a-a87d-ace4dadb0a1f

    :steps: Run satellite-installer with foreman, candlepin and pulpcore options
        referring to external DB host

    :expectedresults: Installed successful, all services running

    :CaseComponent: Installation
    """
