"""Tests for the Docker Compute Resource feature

:Requirement: Provisioning

:CaseAutomation: Automated

:CaseLevel: Component

:TestType: Functional

:Team: Rocket

:CaseComponent: Provisioning

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.factory import make_product_wait
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import Repository
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import REPO_TYPE


@pytest.mark.skip_if_not_set('docker')
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_upload_image(module_org, target_sat, container_contenthost):
    """A Docker-enabled client can create a new ``Dockerfile``
    pointing to an existing Docker image from a Satellite 6 and modify it.
    Then, using ``docker build`` generate a new image which can then be
    uploaded back onto the Satellite 6 as a new repository.

    :id: 2c47559c-b27f-436e-9b1e-df5c3633b007

    :Steps:

        1. Create a local docker compute resource
        2. Create a container and start it
        3. [on docker host] Commit a new image from the container
        4. [on docker host] Export the image to tar
        5. scp the image to satellite box
        6. create a new docker repo
        7. upload the image to the new repo

    :expectedresults: Client can create a new image based off an existing
        Docker image from a Satellite instance, add a new package and
        upload the modified image (plus layer) back to the Satellite.

    :parametrized: yes
    """
    try:
        """
        These functions were removed, but let's leave them here
        to maintain overall test logic - in case required functionality
        is eventually implemented

        compute_resource = make_compute_resource({
            'organization-ids': [module_org.id],
            'provider': 'Docker',
            'url': f'http://{container_contenthost.ip_addr}:2375',
        })
        container = make_container({
            'compute-resource-id': compute_resource['id'],
            'organization-ids': [module_org.id],
        })
        Docker.container.start({'id': container['id']})
        """
        container = {'uuid': 'stubbed test'}
        repo_name = gen_string('alphanumeric').lower()

        # Commit a new docker image and verify image was created
        image_name = f'{repo_name}/{CONTAINER_UPSTREAM_NAME}'
        result = container_contenthost.execute(
            f'docker commit {container["uuid"]} {image_name}:latest && '
            f'docker images --all | grep {image_name}'
        )
        assert result.status == 0

        # Save the image to a tar archive
        result = container_contenthost.execute(f'docker save -o {repo_name}.tar {image_name}')
        assert result.status == 0

        tar_file = f'{repo_name}.tar'
        container_contenthost.get(remote_path=tar_file)
        target_sat.put(
            local_path=tar_file,
            remote_path=f'/tmp/{tar_file}',
        )

        # Upload tarred repository
        product = make_product_wait({'organization-id': module_org.id})
        repo = make_repository(
            {
                'content-type': REPO_TYPE['docker'],
                'docker-upstream-name': CONTAINER_UPSTREAM_NAME,
                'name': gen_string('alpha', 5),
                'product-id': product['id'],
                'url': CONTAINER_REGISTRY_HUB,
            }
        )
        Repository.upload_content({'id': repo['id'], 'path': f'/tmp/{tar_file}'})

        # Verify repository was uploaded successfully
        repo = Repository.info({'id': repo['id']})
        assert target_sat.hostname == repo['published-at']

        repo_name = '-'.join((module_org.label, product['label'], repo['label'])).lower()
        assert repo_name in repo['published-at']
    finally:
        # Remove the archive
        target_sat.execute(f'rm -f /tmp/{tar_file}')
