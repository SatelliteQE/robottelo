"""Tests for Container Management destructive operations

:Requirement: ContainerImageManagement

:CaseAutomation: Automated

:Team: Artemis

:CaseComponent: ContainerImageManagement

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import SETTINGS_YAML_SECRET
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

    # Step 1: Add DNS alias to the host's /etc/hosts. This is the only hosts
    # entry needed: the host-side podman client (login/push/pull) resolves the
    # alias through it, and Foreman itself only compares the Host header
    # against the :hosts: allowlist configured in step 2. The container's
    # generated /etc/hosts is deliberately not edited because the restart
    # below recreates the container and would wipe the entry.
    hosts_entry = f'{target_sat.ip_addr} {alias_hostname}'
    assert target_sat.execute(f'echo "{hosts_entry}" >> /etc/hosts').status == 0

    # Step 2: Configure foreman's settings.yaml to allow the DNS alias
    # Satellite is containerized: settings.yaml is a podman secret that is
    # re-applied to the 'foreman' container on every restart, so the alias
    # must be added to the secret itself (a direct in-container edit would
    # be reverted by the restart below). mktemp is used for the dump so the
    # file is private (0600) and has an unpredictable path.
    settings_tmp = target_sat.execute('mktemp /tmp/foreman-settings-XXXXXX').stdout.strip()
    assert settings_tmp
    try:
        assert (
            target_sat.execute(
                f"podman secret inspect --showsecret --format '{{{{.SecretData}}}}' "
                f'{SETTINGS_YAML_SECRET} > {settings_tmp}'
            ).status
            == 0
        )
        assert (
            target_sat.execute(
                # Add the alias under :hosts:, inserting the key itself if it is
                # missing (a plain sed append would silently change nothing).
                rf"grep -q '^:hosts:$' {settings_tmp} "
                rf"&& sed -i '/^:hosts:$/a\  - {alias_hostname}' {settings_tmp} "
                rf"|| printf ':hosts:\n  - {alias_hostname}\n' >> {settings_tmp}"
                f' && podman secret create --replace {SETTINGS_YAML_SECRET} {settings_tmp}'
            ).status
            == 0
        )

        # Restart the foreman quadlet unit to apply settings
        assert target_sat.execute('systemctl restart foreman.service').status == 0

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
    finally:
        # Remove the secret dump even when the test fails midway
        target_sat.execute(f'rm -f {settings_tmp}')

    logger.info(
        f"Successfully verified container registry operations with DNS alias {alias_hostname}"
    )
