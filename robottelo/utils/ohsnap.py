"""Utility module to communicate with Ohsnap API"""
import requests
from box import Box
from packaging.version import Version

from robottelo import constants
from robottelo.exceptions import InvalidArgumentError
from robottelo.exceptions import RepositoryDataNotFound
from robottelo.logging import logger


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
            logger.warn(
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
    ohsnap_repo_host, repo, product, release, os_release, snap='', arch=None, repo_check=True
):
    """Returns a repository definition based on the arguments provided"""
    arch = arch or constants.DEFAULT_ARCHITECTURE
    res = requests.get(
        ohsnap_repo_url(ohsnap_repo_host, 'repositories', product, release, os_release, snap)
    )
    res.raise_for_status()
    try:
        repository = next(r for r in res.json() if r['label'] == repo)
    except StopIteration:
        raise RepositoryDataNotFound(f'Repository "{repo}" is not provided by the given product')
    repository['baseurl'] = repository['baseurl'].replace('$basearch', arch)
    # If repo check is enabled, check that the repository actually exists on the remote server
    if repo_check and not requests.get(repository['baseurl']).ok:
        logger.warn(
            f'Repository was not found on the URL: {repository["baseurl"]} ; Arguments used: '
            f'repo={repo}, product={product}, release={release}, os_release={os_release}, '
            f'snap={snap}'
        )
    return Box(**repository)
