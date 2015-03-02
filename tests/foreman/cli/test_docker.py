"""Tests related to the docker hammer sub-command"""

from robottelo.cli.docker import Docker
from robottelo.cli.factory import (
    CLIFactoryError,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.repository import Repository
from robottelo.common.constants import DOCKER_REGISTRY_HUB
from robottelo.test import CLITestCase


class DockerImageTestCase(CLITestCase):
    """Tests related to docker image command"""

    def test_bugzilla_1190122(self):
        """@Test: docker image displays tags information for a docker image

        @Feature: Docker

        @Assert: docker image displays tags information for a docker image

        """
        try:
            organization = make_org()
            product = make_product({
                u'organization-id': organization['id'],
            })
            repository = make_repository({
                u'content-type': u'docker',
                u'docker-upstream-name': u'busybox',
                u'product-id': product['id'],
                u'url': DOCKER_REGISTRY_HUB,
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = Repository.synchronize({'id': repository['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Grab all available images related to repository
        result = Docker.image.list({
            u'repository-id': repository['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Some images do not have tags associated with it, ignore those because
        # we want to check the tag information
        images = [
            image for image in result.stdout if int(image['tags']) > 0
        ]
        for image in images:
            result = Docker.image.info({'id': image['id']})
            self.assertEqual(result.return_code, 0)
            self.assertEqual(len(result.stderr), 0)

            # Extract the list of repository ids of the available image's tags
            tag_repository_ids = [
                tag['repository-id'] for tag in result.stdout['tags']
            ]
            self.assertIn(repository['id'], tag_repository_ids)
