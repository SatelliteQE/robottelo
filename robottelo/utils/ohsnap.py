import requests
from box import Box

from robottelo import constants
from robottelo.exceptions import InvalidArgumentError
from robottelo.exceptions import RepositoryDataNotFound
from robottelo.logging import logger


def ohsnap_repo_url(
    ohsnap_repo_host, request_type, product=None, release=None, os_release=None, snap=''
):
    """Returns a URL pointing to Ohsnap "repo_file" or "repositories" API endpoint"""
    if request_type not in ['repo_file', 'repositories']:
        raise InvalidArgumentError('Type must be one of "repo_file" or "repositories"')
    if not all(arg for arg in [product, release, os_release]):
        raise InvalidArgumentError(
            'Arguments "product", "release" and "os_release" must be provided.'
        )
    if release.lower != 'client':
        if snap:
            snap = "/" + snap if snap else ""
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
        f'{release}{snap}/el{os_release}/{product}/{request_type}'
    )


def dogfood_repofile_url(ohsnap_repo_host, product=None, release=None, os_release=None, snap=''):
    return ohsnap_repo_url(ohsnap_repo_host, 'repo_file', product, release, os_release, snap)


def dogfood_repository(
    ohsnap_repo_host, repo, arch=None, product=None, release=None, os_release=None, snap=''
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
    return Box(**repository)
