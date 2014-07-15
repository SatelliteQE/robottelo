"""Module containing convenience functions for working with the API."""
from robottelo.api import client
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
    :rtype: list
    :raises RepositoryErrataException: If an error occurs while fetching
        the requested repository's errata.

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
    :rtype: list
    :raises RepositoryPackagesException: If an error occurs while fetching
        the requested repository's packages.

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
