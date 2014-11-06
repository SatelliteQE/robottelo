"""Module containing convenience functions for working with the API."""
from robottelo.api import client
from robottelo.common import helpers
from robottelo import entities
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
    task_result = entities.Product(id=prd_id).enable_rhrepo(
        base_arch=basearch,
        release_ver=releasever,
        reposet_id=reposet_id,
    )['result']
    if task_result != "success":
        raise entities.APIResponseError(
            "Enabling the RedHat Repository '{0}' failed".format(repo))
    return entities.Repository().fetch_repoid(name=repo, org_id=org_id)
