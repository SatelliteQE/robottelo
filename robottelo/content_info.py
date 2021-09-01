"""Module that gather several informations about host"""
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


def get_repomd_revision(repo_path, hostname=None):
    """Fetches a revision of repository.

    :param str repo_path: unix path to the repo, e.g. '/var/lib/pulp/fooRepo'
    :param str optional hostname: hostname or IP address of the remote host. If
        ``None`` the hostname will be get from ``main.server.hostname`` config.
    :return: string containing repository revision
    :rtype: str
    """
    repomd_path = 'repodata/repomd.xml'
    result = ssh.command(
        f"grep -oP '(?<=<revision>).*?(?=</revision>)' {repo_path}/{repomd_path}",
        hostname=hostname,
    )
    # strip empty lines
    stdout = [line for line in result.stdout.splitlines() if line]
    if result.status != 0 or len(stdout) != 1:
        raise CLIReturnCodeError(
            result.status,
            result.stderr,
            f'Unable to fetch revision for {repo_path}. Please double check your '
            'hostname, path and contents of repomd.xml',
        )
    return stdout[0]
