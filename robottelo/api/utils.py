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
    :rtype: list
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


def status_code_error(path, desired, response):
    """Compose an error message using ``path``, ``desired`` and ``response``.

    ``desired`` and ``path`` are used as-is. The following must be present on
    ``response``:

    * ``response.status_code``
    * ``response.json()``

    :param str path: The path to which a request was sent.
    :param int desired: The desired return status code.
    :param response: The ``Response`` object returned.
    :return: An error message.
    :rtype: str

    """
    # Decode response into JSON format, if possible.
    try:
        json_response = response.json()
    except ValueError:
        json_response = None

    # Generate error message.
    if json_response is None:
        err_msg = 'Could not decode response; not in JSON format.'
    else:
        if 'error' in json_response.keys():
            err_msg = json_response['error']
        elif 'errors' in json_response.keys():
            err_msg = json_response['errors']
        else:
            err_msg = 'Response in JSON format, but contains no error message.'
    return u'Desired HTTP {0} but received HTTP {1} after sending request ' \
        'to {2}. {3}'.format(desired, response.status_code, path, err_msg)
