"""Tests for Container Management destructive operations

:Requirement: ContainerImageManagement

:CaseAutomation: Automated

:Team: Artemis

:CaseComponent: ContainerImageManagement

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import FOREMAN_CONFIG_SETTINGS_YAML
from robottelo.logging import logger

pytestmark = [pytest.mark.destructive]


def test_destructive_container_registry_with_dns_alias(target_sat, function_org, function_product):
    """Test container registry operations with DNS alias

    :id: 10cf21a2-db65-4c02-b3b5-4a5280b4d181

    :steps:
        1. Add a DNS alias to the environment by modifying /etc/hosts
        2. Configure foreman's settings.yaml to allow the DNS alias
        3. Pull image from quay.io and use the image id during push
        4. Run podman login with the alias hostname
        5. Run podman push with the alias hostname
        6. Run podman pull with the alias hostname

    :expectedresults:
        1. Container registry operations work with DNS alias
        2. No UnsafeRedirectError occurs during blob operations
        3. Podman pull/push operations succeed with alias hostname

    :Verifies: SAT-36036

    :CaseImportance: High

    :customerscenario: true
    """
    # Generate test data
    alias_hostname = f"alias-{gen_string('alpha', 5).lower()}.example.com"
    repo_name = gen_string('alpha', 5).lower()

    # Get organization and product labels for container URI
    org_label = function_org.label
    product_label = function_product.label

    # Step 1: Add DNS alias to /etc/hosts
    assert (
        target_sat.execute(f'echo "{target_sat.ip_addr} {alias_hostname}" >> /etc/hosts').status
        == 0
    )

    # Step 2: Configure foreman's settings.yaml to allow the DNS alias
    assert (
        target_sat.execute(
            f'echo ":hosts:\n  - {alias_hostname}" >> {FOREMAN_CONFIG_SETTINGS_YAML}'
        ).status
        == 0
    )

    # Restart foreman service to apply settings
    target_sat.cli.Service.restart()

    # Step 3: Pull image from quay.io
    busybox_image = 'quay.io/quay/busybox'
    pull_result = target_sat.execute(f'podman pull {busybox_image}')
    assert pull_result.status == 0

    # Get the image ID of the pulled busybox image
    image_id_result = target_sat.execute(f'podman images -q {busybox_image}')
    assert image_id_result.status == 0, f"Could not find image ID for {busybox_image}"
    busybox_image_id = image_id_result.stdout.strip()
    assert busybox_image_id, f"Could not find image ID for {busybox_image}"

    # Step 4: Run podman login with the alias hostname
    login_result = target_sat.execute(
        f'podman login {alias_hostname} --tls-verify=false '
        f'-u {settings.server.admin_username} -p {settings.server.admin_password}'
    )
    assert login_result.status == 0

    # Step 5: Run podman push with the alias hostname using image ID
    container_uri = f'{alias_hostname}/{org_label}/{product_label}/{repo_name}'.lower()
    push_result = target_sat.execute(
        f'podman push {busybox_image_id} {container_uri} --tls-verify=false'
    )
    assert push_result.status == 0

    # Step 6: Run podman pull with the alias hostname
    pull_result = target_sat.execute(f'podman pull {container_uri} --tls-verify=false')
    assert pull_result.status == 0

    # Verify the image is available
    images_result = target_sat.execute('podman images')
    assert container_uri in images_result.stdout

    logger.info(
        f"Successfully verified container registry operations with DNS alias {alias_hostname}"
    )
