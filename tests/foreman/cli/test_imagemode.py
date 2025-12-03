"""CLI tests for Image Mode Hosts

:Requirement: ImageMode

:CaseAutomation: Automated

:CaseComponent: ImageMode

:Team: Artemis

:CaseImportance: High
"""

import json

import pytest

from robottelo.constants import DUMMY_BOOTC_FACTS


@pytest.mark.e2e
def test_positive_bootc_cli_actions(
    target_sat, dummy_bootc_host, function_ak_with_cv, function_org
):
    """Register a bootc host and validate CLI information

    :id: d9557843-4cc7-4e70-a035-7b2c4008dd5e

    :expectedresults: Upon registering a Bootc host, the facts are attached to the host, and are accurate. Hammer host bootc also returns proper info.

    :Verifies: SAT-27168, SAT-27170, SAT-30211
    """
    bootc_dummy_info = json.loads(DUMMY_BOOTC_FACTS)
    assert (
        dummy_bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status
        == 0
    )
    assert dummy_bootc_host.subscribed
    bootc_info = target_sat.cli.Host.info({'name': dummy_bootc_host.hostname})[
        'bootc-image-information'
    ]
    assert bootc_info['running-image'] == bootc_dummy_info['bootc.booted.image']
    assert bootc_info['running-image-digest'] == bootc_dummy_info['bootc.booted.digest']
    assert bootc_info['rollback-image'] == bootc_dummy_info['bootc.rollback.image']
    assert bootc_info['rollback-image-digest'] == bootc_dummy_info['bootc.rollback.digest']
    # Verify hammer host bootc images - verify the test host's image appears in the booted images list
    all_bootc_images = target_sat.cli.Host.bootc_images()
    # The bootc_images command returns aggregated data, so we need to find our specific image
    # Since we already validated the host-specific info above, here we just verify it appears in the booted images list
    assert any(
        img.get('running-image') == bootc_dummy_info['bootc.booted.image']
        for img in all_bootc_images
    ), (
        f'Expected bootc image {bootc_dummy_info["bootc.booted.image"]} not found in booted bootc images list. '
        f'Available images: {[img.get("running-image") for img in all_bootc_images]}'
    )
