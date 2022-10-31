SSH (Secure SHell)
==================

This section explains Robottelo's ssh module.

.. contents::

Introduction
------------

Robottelo uses ssh extensively to access remote servers.
Functions from ``robottello.utils.ssh`` make ssh access easier and are
explained on next sections.

Main Functions
--------------

``command`` is the main function of ssh module.
Its full signature is::

    def command(cmd, hostname=None, output_format=None, username=None,
                password=None, key_filename=None, timeout=10):
        """Executes SSH command(s) on remote hostname."""

Most of parameters can be read from ``conf/server.yaml`` file.
So in a properly configured project commands can be easily executed on host.
The function returns a result object containing the attributes: stdout, stderr, and status.
The following code was executed to generate the example of first section of
this document::

    >>> from robottelo.utils import ssh
    >>> print(ssh.command('cat /etc/redhat-release'))
    Red Hat Enterprise Linux Server release 7.2 (Maipo)

Helper Functions
----------------

The module provide some helper functions which use ``command`` internally
for common ssh operations:

- **add_authorized_key**: Add public key to remote authorized keys;
- **is_ssh_pub_key**: Validate public key.
