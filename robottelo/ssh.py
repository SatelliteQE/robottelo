"""Utility module to handle the shared ssh connection."""

from robottelo.cli import hammer


def get_client(
    hostname=None,
    username=None,
    password=None,
    port=22,
    net_type=None,
):
    """Returns a host object that provides an ssh connection

    Processes ssh credentials in the order: password, key_filename, ssh_key
    Config validation enforces one of the three must be set in settings.server
    """
    from robottelo.config import settings
    from robottelo.hosts import ContentHost

    return ContentHost(
        hostname=hostname or settings.server.hostname,
        username=username or settings.server.ssh_username,
        password=password or settings.server.ssh_password,
        port=port or settings.server.ssh_client.port,
        # TODO(ogajduse): we better get rid of the ssh module entirely
        net_type=net_type or settings.server.network_type,
    )


def command(
    cmd,
    hostname=None,
    output_format=None,
    username=None,
    password=None,
    timeout=None,
    port=22,
    net_type=None,
):
    """Executes SSH command(s) on remote hostname.

    kwargs are passed through to get_connection

    :param str cmd: The command to run
    :param str output_format: json, csv or None
    :param int timeout: Time to wait for the ssh command to finish.
    :param connection_timeout: Time to wait for establishing the connection.
    """
    client = get_client(
        hostname=hostname,
        username=username,
        password=password,
        port=port,
        net_type=net_type,
    )
    result = client.execute(cmd, timeout=timeout)

    if output_format and result.status == 0:
        if output_format == 'csv':
            result.stdout = hammer.parse_csv(result.stdout) if result.stdout else {}
        if output_format == 'json':
            result.stdout = hammer.parse_json(result.stdout) if result.stdout else None
    return result
