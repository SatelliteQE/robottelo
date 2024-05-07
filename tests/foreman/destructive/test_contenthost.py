"""Test class for Content Hosts UI

:Requirement: Content Host

:CaseAutomation: Automated

:CaseComponent: Hosts-Content

:team: Phoenix-subscriptions

:CaseImportance: High

"""

import pytest

from robottelo.config import settings
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE, FAKE_1_CUSTOM_PACKAGE

pytestmark = pytest.mark.destructive


@pytest.mark.run_in_one_thread
@pytest.mark.upgrade
def test_content_access_after_stopped_foreman(target_sat, rhel7_contenthost):
    """Install a package even after foreman service is stopped

    :id: 71ae6a56-30bb-11eb-8489-d46d6dd3b5b2

    :expectedresults: Package should get installed even after foreman service is stopped

    :CaseImportance: Medium

    :CaseComponent: Infrastructure

    :Team: Platform

    :parametrized: yes
    """
    org = target_sat.api.Organization().create()
    org.sca_disable()
    lce = target_sat.api.LifecycleEnvironment(organization=org).create()
    repos_collection = target_sat.cli_factory.RepositoryCollection(
        distro='rhel7',
        repositories=[
            target_sat.cli_factory.YumRepository(url=settings.repos.yum_1.url),
        ],
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=False, override=True)
    repos_collection.setup_virtual_machine(rhel7_contenthost)
    result = rhel7_contenthost.execute(f'yum -y install {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status == 0
    assert target_sat.cli.Service.stop(options={'only': 'foreman'}).status == 0
    assert target_sat.cli.Service.status(options={'only': 'foreman'}).status == 1
    result = rhel7_contenthost.execute(f'yum -y install {FAKE_0_CUSTOM_PACKAGE}')
    assert result.status == 0
    assert target_sat.cli.Service.start(options={'only': 'foreman'}).status == 0
    assert target_sat.cli.Service.status(options={'only': 'foreman'}).status == 0
