from inspect import getmembers, isfunction
import json
from pathlib import Path
import sys

from box import Box

from robottelo.logging import logger
from robottelo.utils.ohsnap import dogfood_repository
from robottelo.utils.url import is_url


def post(settings):
    settings_cache_path = Path(f'settings_cache-{settings.server.version.release}.json')
    if getattr(settings.robottelo.settings, 'get_fresh', True):
        data = get_repos_config(settings)
        write_cache(settings_cache_path, data)
    else:
        try:
            data = read_cache(settings_cache_path)
        except FileNotFoundError:
            # no settings cache file exists
            logger.warning(
                f'The [{settings_cache_path}] cache file was not found.'
                'Config will be fetched now.'
            )
            data = get_repos_config(settings)
            write_cache(settings_cache_path, data)
    config_migrations(settings, data)
    data['dynaconf_merge'] = True
    return data


def write_cache(path, data):
    path.write_text(json.dumps(data, indent=4))
    logger.info(f'Generated settings cache file {path}')


def read_cache(path):
    logger.info(f'Using settings cache file: {path}')
    return Box(json.loads(path.read_text()))


def config_migrations(settings, data):
    """Run config migrations

    Fetch the config migrations from the conf/migrations.py file and run them.

    :param settings: dynaconf settings object
    :type settings: LazySettings
    :param data: settings data to be merged with the rest of the settings
    :type data: dict
    """
    logger.info('Running config migration hooks')
    sys.path.append(str(Path(__file__).parent))
    from conf import migrations

    migration_functions = [
        mf for mf in getmembers(migrations, isfunction) if mf[0].startswith('migration_')
    ]
    # migration_functions is a sorted list of tuples (name, function)
    for name, func in migration_functions:
        logger.debug(f'Running {name}')
        func(settings, data)
        logger.debug(f'Finished running {name}')
    logger.info('Finished running config migration hooks')


def get_repos_config(settings):
    data = {}
    # check if the Ohsnap URL is valid, our sample configuration does not contain a valid URL
    if is_url(settings.ohsnap.host):
        data.update(get_ohsnap_repos(settings))
    else:
        logger.error(
            'The Ohsnap URL is invalid! Post-configuration hooks will not run. '
            'Default configuration will be used.'
        )
    return Box({'REPOS': data})


def get_ohsnap_repos(settings):
    data = {}
    data['CAPSULE_REPO'] = get_ohsnap_repo_url(
        settings,
        repo='capsule',
        product='capsule',
        release=settings.server.version.release,
        os_release=settings.server.version.rhel_version,
        snap=settings.server.version.snap,
    )

    data['SATELLITE_REPO'] = get_ohsnap_repo_url(
        settings,
        repo='satellite',
        product='satellite',
        release=settings.server.version.release,
        os_release=settings.server.version.rhel_version,
        snap=settings.server.version.snap,
    )

    data['SATCLIENT_REPO'] = get_dogfood_satclient_repos(settings)

    data['SATUTILS_REPO'] = get_ohsnap_repo_url(
        settings,
        repo='utils',
        product='utils',
        release=settings.server.version.release,
        os_release=settings.server.version.rhel_version,
        snap=settings.server.version.snap,
    )

    data['SATMAINTENANCE_REPO'] = get_ohsnap_repo_url(
        settings,
        repo='maintenance',
        product='satellite',
        release=settings.server.version.release,
        os_release=settings.server.version.rhel_version,
        snap=settings.server.version.snap,
    )
    return data


def supported_rhel_versions(settings):
    return [
        ver for ver in settings.supportability.content_hosts.rhel.versions if isinstance(ver, int)
    ]


def get_dogfood_sattools_repos(settings):
    data = {}
    rhels = supported_rhel_versions(settings)
    for ver in rhels:
        data[f'RHEL{ver}'] = get_ohsnap_repo_url(
            settings,
            repo='tools',
            product='tools',
            release=settings.server.version.release,
            os_release=ver,
            snap=settings.server.version.snap,
        )
    return data


def get_dogfood_satclient_repos(settings):
    data = {}
    rhels = supported_rhel_versions(settings)
    for ver in rhels:
        data[f'RHEL{ver}'] = get_ohsnap_repo_url(
            settings,
            repo='client',
            product='client',
            release='client',
            os_release=ver,
        )
    return data


def get_ohsnap_repo_url(settings, repo, product=None, release=None, os_release=None, snap=''):
    return dogfood_repository(
        settings.ohsnap,
        repo=repo,
        product=product,
        release=release,
        os_release=os_release,
        snap=snap,
    ).baseurl
