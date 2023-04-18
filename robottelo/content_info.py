"""Miscellaneous content helper functions"""
import os
import re

import requests

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError


def get_repo_files(repo_path, extension='rpm', hostname=None):
    """Returns a list of repo files (for example rpms) in specific repository
    directory.

    :param str repo_path: unix path to the repo, e.g. '/var/lib/pulp/fooRepo/'
    :param str extension: extension of searched files. Defaults to 'rpm'
    :param str optional hostname: hostname or IP address of the remote host. If
        ``None`` the hostname will be get from ``main.server.hostname`` config.
    :return: list representing rpm package names
    :rtype: list
    """
    if not repo_path.endswith('/'):
        repo_path += '/'
    result = ssh.command(
        f"find {repo_path} -name '*.{extension}' | awk -F/ '{{print $NF}}'",
        hostname=hostname,
    )
    if result.status != 0:
        raise CLIReturnCodeError(result.status, result.stderr, f'No .{extension} found')
    # strip empty lines and sort alphabetically (as order may be wrong because
    # of different paths)
    return sorted(repo_file for repo_file in result.stdout.splitlines() if repo_file)


def get_repo_files_urls_by_url(url, extension='rpm'):
    """Returns a list of URLs of repo files (for example rpms) in a specific repository
    published at some URL.
    :param url: URL where the repo or CV is published
    :param extension: extension of searched files. Defaults to 'rpm'
    :return:  list representing package URLs
    """
    if not url.endswith('/'):
        url += '/'

    result = requests.get(url, verify=False)
    if result.status_code != 200:
        raise requests.HTTPError(f'{url} is not accessible')

    links = re.findall(r'(?<=href=").*?(?=">)', result.text)
    if 'Packages/' not in links:
        files = sorted(line for line in links if extension in line)
        return [f'{url}{file}' for file in files]

    files = []
    subs = get_repo_files_urls_by_url(f'{url}Packages/', extension='/')
    for sub in subs:
        files.extend(get_repo_files_urls_by_url(sub, extension))
    return sorted(files)


def get_repo_files_by_url(url, extension='rpm'):
    """Returns a list of repo files (for example rpms) in a specific repository
    published at some URL.
    :param url: URL where the repo or CV is published
    :param extension: extension of searched files. Defaults to 'rpm'
    :return:  list representing package names
    """
    return sorted([os.path.basename(f) for f in get_repo_files_urls_by_url(url, extension)])


def get_repomd(repo_url):
    """Fetches content of the repomd file of a repository

    :param repo_url: the 'Published_At' link of a repo
    :return: string with repomd content
    """
    repomd_path = 'repodata/repomd.xml'
    result = requests.get(f'{repo_url}/{repomd_path}', verify=False)
    if result.status_code != 200:
        raise requests.HTTPError(f'{repo_url}/{repomd_path} is not accessible')

    return result.text


def get_repomd_revision(repo_url):
    """Fetches a revision of a repository.

    :param str repo_url: the 'Published_At' link of a repo
    :return: string containing repository revision
    :rtype: str
    """
    match = re.search('(?<=<revision>).*?(?=</revision>)', get_repomd(repo_url))
    if not match:
        raise ValueError(f'<revision> not found in repomd file of {repo_url}')

    return match.group(0)
