"""Module containing convenience functions for working with the API."""
from nailgun import client, entities
from robottelo.common import helpers
from urlparse import urljoin


class RepositoryPackagesException(Exception):
    """Indicates that a repository's packages could not be fetched."""


class RepositoryErrataException(Exception):
    """Indicates that a repository's errata could not be fetched."""


def get_errata(repository_id):
    """Return all erratums belonging to repository ``repository_id``.

    :param int repository_id: A repository ID.
    :return: That repository's errata.
    :raises robottelo.api.utils.RepositoryErrataException: If an error occurs
        while fetching the requested repository's errata.

    """
    path = urljoin(
        helpers.get_server_url(),
        'katello/api/v2/repositories/{0}/errata'.format(repository_id)
    )
    response = client.get(
        path,
        auth=helpers.get_server_credentials(),
        verify=False,
    ).json()
    if 'errors' in response.keys():
        raise RepositoryErrataException(
            'Error received after issuing GET to {0}. Error received: {1}'
            ''.format(path, response['errors'])
        )
    return response['results']


def get_packages(repository_id):
    """Return all packages belonging to repository ``repository_id``.

    :param int repository_id: A repository ID.
    :return: That repository's packages.
    :raises robottelo.api.utils.RepositoryPackagesException: If an error occurs
        while fetching the requested repository's packages.

    """
    path = urljoin(
        helpers.get_server_url(),
        'katello/api/v2/repositories/{0}/packages'.format(repository_id)
    )
    response = client.get(
        path,
        auth=helpers.get_server_credentials(),
        verify=False,
    ).json()
    if 'errors' in response.keys():
        raise RepositoryPackagesException(
            'Error received after issuing GET to {0}. Error received: {1}'
            ''.format(path, response['errors'])
        )
    return response['results']


def enable_rhrepo_and_fetchid(basearch, org_id, product, repo,
                              reposet, releasever):
    """Enable a RedHat Repository and fetches it's Id.

    :param str org_id: The organization Id.
    :param str product: The product name in which repository exists.
    :param str reposet: The reposet name in which repository exists.
    :param str repo: The repository name who's Id is to be fetched.
    :param str basearch: The architecture of the repository.
    :param str releasever: The releasever of the repository.
    :return: Returns the repository Id.
    :rtype: str

    """
    prd_id = entities.Product().fetch_rhproduct_id(name=product, org_id=org_id)
    reposet_id = entities.Product(id=prd_id).fetch_reposet_id(name=reposet)
    entities.Product(id=prd_id).enable_rhrepo(
        base_arch=basearch,
        release_ver=releasever,
        reposet_id=reposet_id,
    )
    return entities.Repository().fetch_repoid(name=repo, org_id=org_id)
