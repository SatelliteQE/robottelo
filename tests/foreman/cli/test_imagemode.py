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
from tests.foreman.api.test_host import _create_transient_packages


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


def test_containerfile_install_command(target_sat):
    """Ensure the containerfile install command returns correct output.

    :id: a1879eed-5dc3-4f96-bd9e-edad7ca4801d

    :steps:
        1. Create a host
        2. Add packages with different persistence values via SQL (2x transient, persistent, None)
        3. Retrieve the containerfile install command via hammer.
        4. Verify the command format and content.

    :expectedresults:
        1. Packages with persistence='transient' are returned with correct value.
        2. Packages with persistence='persistent' or None are not returned.

    :Verifies: SAT-36792
    """
    # Create a host
    host = target_sat.api.Host().create()

    # Add packages with different persistence values via SQL (2x transient, persistent, None)
    package_data = [
        {
            'name': 'transient-pkg-1',
            'version': '1.2.3',
            'release': '1.el9',
            'arch': 'x86_64',
            'persistence': 'transient',
        },
        {
            'name': 'transient-pkg-2',
            'version': '4.5.6',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'transient',
        },
        {
            'name': 'persistent-pkg',
            'version': '1.1.1',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'persistent',
        },
        {
            'name': 'unknown-pkg',
            'version': '2.2.2',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': None,
        },
    ]
    _create_transient_packages(target_sat, host, package_data)

    # Retrieve the containerfile install command via hammer.
    cmd = target_sat.cli.Host.package_containerfile_install_command({'host-id': host.id})

    # Verify the command format and content.
    assert cmd.startswith('RUN dnf install -y')

    transient_packages = [p for p in package_data if p['persistence'] == 'transient']
    packages_in_cmd = cmd.replace('RUN dnf install -y', '').split()
    assert len(packages_in_cmd) == len(transient_packages)

    assert all(
        f'{p["name"]}-{p["version"]}-{p["release"]}.{p["arch"]}' in cmd for p in transient_packages
    )
    assert all(
        f'{p["name"]}-{p["version"]}-{p["release"]}.{p["arch"]}' not in cmd
        for p in package_data
        if p['persistence'] != 'transient'
    )
