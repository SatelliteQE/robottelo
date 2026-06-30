"""Utility module to communicate with Ohsnap API"""

from box import Box
from packaging.version import Version
import requests
from wait_for import wait_for

from robottelo import constants
from robottelo.exceptions import InvalidArgumentError, RepositoryDataNotFound
from robottelo.logging import logger


def ohsnap_response_hook(r, *args, **kwargs):
    """Requests response hook callback function that processes the response

    :param: obj r: The requests Response object to be processed

    """
    if not r.ok:
        logger.warning(f'Request to: {r.request.url} got response: {r.status_code}')
    r.raise_for_status()


def ohsnap_repo_url(ohsnap, request_type, product, release, os_release, snap=''):
    """Returns a URL pointing to Ohsnap "repo_file" or "repositories" API endpoint"""
    if request_type not in ['repo_file', 'repositories']:
        raise InvalidArgumentError('Type must be one of "repo_file" or "repositories"')
    if not all([product, release, os_release]):
        raise InvalidArgumentError(
            'Arguments "product", "release" and "os_release" must be provided and must not be'
            'None or empty string.'
        )
    if snap:
        snap = "/" + str(snap)
    if release.lower() != 'client':
        if len(release.split('.')) == 2:
            logger.warning(
                f'.z version component not provided in the release ({release}),'
                f' fetching the recent z-stream from ohsnap'
            )
            request_query = {
                'url': f'{ohsnap.host}/api/streams',
                'hooks': {'response': ohsnap_response_hook},
            }
            res, _ = wait_for(
                lambda: requests.get(**request_query),
                handle_exception=True,
                raise_original=True,
                timeout=ohsnap.request_retry.timeout,
                delay=ohsnap.request_retry.delay,
            )
            logger.debug(f'List of releases returned by Ohsnap: {res.json()}')
            # filter the stream for our release and set it only if it has at least 1 snap
            if (streams := [stream for stream in res.json() if stream['id'] == release]) and len(
                streams[0]['release_ids']
            ) > 0:
                # get the recent snap id (last in the list)
                release = streams[0]['release_ids'][-1]
            else:
                logger.warning(f'Ohsnap returned no releases for the given stream: {release}')

        logger.debug(f'Release string after processing: {release}')
    return (
        f'{ohsnap.host}/api/releases/'
        f'{release}{snap}/el{Version(str(os_release)).major}/{product}/{request_type}'
    )


def dogfood_repofile_url(ohsnap, product, release, os_release, snap=''):
    return ohsnap_repo_url(ohsnap, 'repo_file', product, release, os_release, snap)


def dogfood_repository(
    ohsnap, repo, product, release, os_release, snap='', arch=None, repo_check=True
):
    """Returns a repository definition based on the arguments provided"""
    arch = arch or constants.DEFAULT_ARCHITECTURE
    res, _ = wait_for(
        lambda: requests.get(
            ohsnap_repo_url(ohsnap, 'repositories', product, release, os_release, snap),
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
        raise RepositoryDataNotFound(
            f'Repository "{repo}" is not provided by the given product'
        ) from None
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


def parse_container_image_ref(image_ref):
    """Parse a container image reference into registry, image name, and tag/digest."""
    registry, _, remainder = image_ref.partition('/')
    if not remainder:
        return '', image_ref, ''
    name_with_tag = remainder.split('/')[-1]
    if '@' in name_with_tag:
        name, tag = name_with_tag.split('@', 1)
    elif ':' in name_with_tag:
        name, tag = name_with_tag.rsplit(':', 1)
    else:
        name, tag = name_with_tag, ''
    return registry, name, tag


def ohsnap_container_images(ohsnap, release, snap_version, is_all=True):
    """Return container image metadata from Ohsnap for a release and snap version."""
    url = f'{ohsnap.host}/api/releases/{release}/snaps/{snap_version}/container_images'
    if is_all:
        url += '?all=true'
    try:
        res, _ = wait_for(
            lambda: requests.get(url, hooks={'response': ohsnap_response_hook}),
            handle_exception=True,
            raise_original=True,
            timeout=ohsnap.request_retry.timeout,
            delay=ohsnap.request_retry.delay,
        )
        if res.status_code != 200:
            logger.warning(
                'Ohsnap container images request failed: url=%s status=%s',
                url,
                res.status_code,
            )
            return []
        container_images = res.json().get('container_images', [])
        logger.info(
            'Fetched %s container images from Ohsnap for release=%s snap=%s',
            len(container_images),
            release,
            snap_version,
        )
        for image_data in container_images:
            image_ref = image_data.get('image', '')
            registry, name, tag = parse_container_image_ref(image_ref)
            logger.info(
                'Ohsnap container image metadata: name=%s image=%s registry=%s tag=%s vcs_ref=%s '
                'source_url=%s build_date=%s',
                name,
                image_ref,
                registry,
                tag,
                image_data.get('vcs_ref', ''),
                image_data.get('source_url', ''),
                image_data.get('build_date', ''),
            )
        return container_images
    except Exception as err:
        logger.warning(
            'Failed to fetch Ohsnap container images for release=%s snap=%s: %s',
            release,
            snap_version,
            err,
        )
        return []


def container_image_properties(ohsnap, release, snap_version):
    """Build property name/value pairs for Ohsnap container image metadata."""
    properties = []
    for image_data in ohsnap_container_images(ohsnap, release, snap_version):
        image_ref = image_data['image']
        _, name, _ = parse_container_image_ref(image_ref)
        prefix = f'Container_{name}'
        properties.append((f'{prefix}_Image', image_ref))
        properties.append((f'{prefix}_VCS', image_data.get('vcs_ref', '')))
    return properties


def ohsnap_snap_rpms(ohsnap, sat_version, snap_version, os_major, is_all=True):
    sat_xy = '.'.join(sat_version.split('.')[:2])
    url = f'{ohsnap.host}/api/releases/{sat_version}/snaps/{snap_version}/rpms'
    if is_all:
        url += '?all=true'
    res, _ = wait_for(
        lambda: requests.get(url, hooks={'response': ohsnap_response_hook}),
        handle_exception=True,
        raise_original=True,
        timeout=ohsnap.request_retry.timeout,
        delay=ohsnap.request_retry.delay,
    )
    rpms = []
    rpm_repos = [f'satellite {sat_xy}', f'maintenance {sat_xy}']
    if res.status_code == 200:
        for repo_data in res.json():
            if repo_data['rhel'] == os_major and any(
                repo in repo_data['repository'].lower() for repo in rpm_repos
            ):
                rpms += repo_data['rpms']
    return rpms
