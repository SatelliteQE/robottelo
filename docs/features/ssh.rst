SSH (Secure SHell)
==================

This section explains Robottelo's ssh module.

.. contents::

Introduction
------------

Robottelo uses ssh extensively to access remote servers.
Functions from ``robottello.ssh`` make ssh access easier and are
explained on next sections.

SSHCommandResult
----------------

``SSHCommandResult`` represents the result of a ssh command.
It holds ``stdout`` on attribute with same name.
``stderr`` and ``return_code`` are available the same way.
An example of typical result is presented bellow::

    SSHCommandResult(
        stdout=['Red Hat Enterprise Linux Server release 7.2 (Maipo)', ''],
        stderr='',
        return_code=0,
        output_format=None
    )

Attribute ``output_format`` can be ``None``, ``csv`` or
``json``.
The former two options are heavily used to define output format on Hammer CLI.

Main Functions
--------------

``command`` is the main function of ssh module.
Its full signature is::

    def command(cmd, hostname=None, output_format=None, username=None,
                password=None, key_filename=None, timeout=10):
        """Executes SSH command(s) on remote hostname."""

Most of parameters can be read from ``robottelo.properties`` file.
So in a properly configured project commands can be easily executed on host.
The function returns a ``SSHCommandResult`` instance.
The following code was executed to generate the example of first section of
this document::

    >>> from robottelo import ssh
    >>> print(ssh.command('cat /etc/redhat-release'))
    SSHCommandResult(
        stdout=['Red Hat Enterprise Linux Server release 7.2 (Maipo)', ''],
        stderr='',
        return_code=0,
        output_format=None
    )

Another important function is ``execute_command``.
It is similar to ``command``.
But it reuses an existing connection.
So several commands can be executed on a single connection, saving resources
and execution time::

    with ssh.get_connection(..) as connection:
        ssh.execute_command('cp /orign /destiny', connection)
        ssh.execute_command('chmod 0777 /destiny', connection)
        ssh.execute_command("echo 'foo' > /destiny/bar")


Helper Functions
----------------

The module provide some helper functions which use ``command`` internally
for common ssh operations:

- **add_authorized_key**: Add public key to remote authorized keys;
- **upload_file**: Upload file to remote host;
- **download_file**: Download file from remote host;
- **is_ssh_pub_key**: Validate public key.
