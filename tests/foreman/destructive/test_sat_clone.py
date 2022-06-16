"""Test class for ``satellite clone``

:Requirement: SatClone

:CaseAutomation: NotAutomated

:CaseLevel: System

:CaseComponent: SatelliteClone

:Assignee: lpramuk

:TestType: functional

:CaseImportance: High

:Upstream: No

:Setup:
    1. Upload manifest
    2. Enable and sync RH products
    3. Create content views - publish, promote"
    4. Create Activation keys
    5. Create custom products, custom repos (both yum and puppet), sync,
       create content views - publish, promote
    6. Provision and Register content hosts
    7. Create an other test org
    8. Create a new user
    9. Create a Discovery rule

"""
import pytest

pytestmark = pytest.mark.destructive


@pytest.mark.stubbed
def test_clone_without_rename(self):
    """Clone the satellite to other box

    :id: 8dc01d48-5930-43a1-8a34-2fc150482541

    :Steps:
        1. Refresh the manifest
        2. Enable & sync new RH repo
        3. Resync an existing RH repo
        4. Create a new custom product & repo
        5. Resync an existing custom repo
        6. Create, Publish and Promote a new CV
        7. Publish and Promote an existing CV
        8. Create a new AK
        9. Update an existing AK
        10. Refresh the content hosts
        11. Provision new content hosts
        12. Create a new Discovery rule
        13. Update an existing Discovery rule


    :expectedresults: The backup succeeds  and the host gets the requested
        content.

    :CaseAutomation: NotAutomated

    """


@pytest.mark.stubbed
def test_clone_with_rename(self):
    """Clone the satellite to other box

    :id: 466efe11-de87-4a53-a539-8f9cc52baf87

    :Steps:
        1. Refresh the manifest
        2. Enable & sync new RH repo
        3. Resync an existing RH repo
        4. Create a new custom product & repo
        5. Resync an existing custom repo
        6. Create, Publish and Promote a new CV
        7. Publish and Promote an existing CV
        8. Create a new AK
        9. Update an existing AK
        10. Refresh the content hosts
        11. Provision new content hosts
        12. Create a new Discovery rule
        13. Update an existing Discovery rule


    :expectedresults: The backup succeeds  and the host gets the requested
        content.

    :CaseAutomation: NotAutomated

    """


@pytest.mark.stubbed
def test_migrate_with_rename(self):
    """Migrate the satellite from RHEL6 box to a RHEL7 one

    :id: 9928a5cd-8ad4-43e1-820b-08bc1e6cd8a8

    :Steps:
        1. Refresh the manifest
        2. Enable & sync new RH repo
        3. Resync an existing RH repo
        4. Create a new custom product & repo
        5. Resync an existing custom repo
        6. Create, Publish and Promote a new CV
        7. Publish and Promote an existing CV
        8. Create a new AK
        9. Update an existing AK
        10. Refresh the content hosts
        11. Provision new content hosts
        12. Create a new Discovery rule
        13. Update an existing Discovery rule


    :expectedresults: The backup succeeds  and the host gets the requested
        content.

    :CaseAutomation: NotAutomated

    """
