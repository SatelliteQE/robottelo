"""Module that gather several informations about host"""
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


def get_repo_files_by_url(url, extension='rpm'):
    """Returns a list of repo files (for example rpms) in a specific repository
    published at some url.
    :param url: url where the repo or CV is published
    :param extension: extension of searched files. Defaults to 'rpm'
    :return:  list representing rpm package names
    """
    if not url.endswith('/'):
        url += '/'

    result = requests.get(url, verify=False)
    if result.status_code != 200:
        raise requests.HTTPError(f'{url} is not accessible')

    links = re.findall(r'(?<=href=").*?(?=">)', result.text)

    if 'Packages/' not in links:
        return sorted(line for line in links if extension in line)

    files = []
    subs = get_repo_files_by_url(f'{url}Packages/', extension='/')
    for sub in subs:
        files.extend(get_repo_files_by_url(f'{url}Packages/{sub}', extension))

    return sorted(files)


def get_repomd_revision(repo_url):
    """Fetches a revision of a repository.

    :param str repo_url: the 'Published_At' link of a repo
    :return: string containing repository revision
    :rtype: str
    """
    repomd_path = 'repodata/repomd.xml'
    result = requests.get(f'{repo_url}/{repomd_path}', verify=False)
    if result.status_code != 200:
        raise requests.HTTPError(f'{repo_url}/{repomd_path} is not accessible')

    match = re.search('(?<=<revision>).*?(?=</revision>)', result.text)
    if not match:
        raise ValueError(f'<revision> not found in {repo_url}/{repomd_path}')

    return match.group(0)
