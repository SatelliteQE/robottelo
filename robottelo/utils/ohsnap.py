"""Utility module to communicate with Ohsnap API"""
import requests
from box import Box
from packaging.version import Version
from wait_for import wait_for

from robottelo import constants
from robottelo.exceptions import InvalidArgumentError
from robottelo.exceptions import RepositoryDataNotFound
from robottelo.logging import logger


def ohsnap_response_hook(r, *args, **kwargs):
    """Requests response hook callback function that processes the response

    :param: obj r: The requests Response object to be processed

    """
    if not r.ok:
        logger.warning(f'Request to: {r.request.url} got response: {r.status_code}')
    r.raise_for_status()


def ohsnap_repo_url(ohsnap_repo_host, request_type, product, release, os_release, snap=''):
    """Returns a URL pointing to Ohsnap "repo_file" or "repositories" API endpoint"""
    if request_type not in ['repo_file', 'repositories']:
        raise InvalidArgumentError('Type must be one of "repo_file" or "repositories"')
    if not all([product, release, os_release]):
        raise InvalidArgumentError(
            'Arguments "product", "release" and "os_release" must be provided and must not be'
            'None or empty string.'
        )
    if release.lower() != 'client':
        if snap:
            snap = "/" + str(snap) if snap else ""
        else:
            logger.warning(
                'The snap version was not provided. Snap number will not be used in the URL.'
            )
        release = release.split('.')
        if len(release) == 2:
            release.append('0')
        release = '.'.join(release[:3])  # keep only major.minor.patch

    return (
        f'{ohsnap_repo_host}/api/releases/'
        f'{release}{snap}/el{Version(str(os_release)).major}/{product}/{request_type}'
    )


def dogfood_repofile_url(ohsnap_repo_host, product, release, os_release, snap=''):
    return ohsnap_repo_url(ohsnap_repo_host, 'repo_file', product, release, os_release, snap)


def dogfood_repository(
    ohsnap, repo, product, release, os_release, snap='', arch=None, repo_check=True
):
    """Returns a repository definition based on the arguments provided"""
    arch = arch or constants.DEFAULT_ARCHITECTURE
    res, _ = wait_for(
        lambda: requests.get(
            ohsnap_repo_url(ohsnap.host, 'repositories', product, release, os_release, snap),
            hooks={'response': ohsnap_response_hook},
        ),
        handle_exception=True,
        raise_original=True,
        timeout=ohsnap.request_retry.timeout,
        delay=ohsnap.request_retry.delay,
    )
    try:
        repository = next(r for r in res.json() if r['label'] == repo)
    except StopIteration:
        raise RepositoryDataNotFound(f'Repository "{repo}" is not provided by the given product')
    repository['baseurl'] = repository['baseurl'].replace('$basearch', arch)
    # If repo check is enabled, check that the repository actually exists on the remote server
    dogfood_req = requests.get(repository['baseurl'])
    if repo_check and not dogfood_req.ok:
        logger.warning(
            f'Unable to locate the repo at the URL: {repository["baseurl"]} ; '
            f'HTTP response: {dogfood_req.status_code}; Arguments used: {repo=}, '
            f'{product=}, {release=}, {os_release=}, {snap=}'
        )
    return Box(**repository)
