"""
Usage::
     ansible [OPTIONS] SUBCOMMAND [ARG] ...
Parameters::
     SUBCOMMAND                    Subcommand
     [ARG] ...                     Subcommand arguments
Subcommands::
     roles                         Manage ansible roles
     variables                     Manage ansible variables
"""

from re import match, search, split

from click import unstyle

from robottelo.cli.base import Base
from robottelo.exceptions import CLIError
from robottelo.utils.ansible import AnsibleSyncTasks


class Ansible(Base):
    """Manipulates Ansible Variables and roles."""

    command_base = 'ansible'

    @classmethod
    def roles_import(cls, options=None):
        """DEPRECATED - Import ansible roles"""
        cls.command_sub = 'roles import'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def roles_sync(cls, options=None, synchronous=False, timeout=180, task_ids=None):
        """Sync Ansible roles and optionally wait for the returned task.

        :param bool synchronous: Wait for the task reported by Hammer debug output.
        :param int timeout: Maximum seconds for each SSH request, including submission.
        :param list task_ids: Record reported task IDs before waiting, for cleanup on failure.
        """
        cls.command_sub = 'roles sync'
        if not synchronous:
            return cls.execute(cls._construct_command(options), timeout=timeout * 1000)

        response = cls.execute(
            f'--debug {cls._construct_command(options)}',
            return_raw_response=True,
            timeout=timeout * 1000,
        )
        debug = unstyle(response.stderr)
        # Scope fallback parsing to the sync request, excluding earlier API responses.
        _, sync_request, sync_debug = debug.rpartition('PUT /ansible/api/ansible_roles/sync')
        debug = sync_debug if sync_request else debug
        responses = split(r'Response(?: body)?:\s*', debug)
        body = (
            responses[-1]
            if len(responses) > 1
            else debug.rpartition('PUT /ansible/api/ansible_roles/sync')[2]
        )
        body = body.split('Response headers:', 1)[0]
        task_id_regex = r'["\']id["\']\s*(?:=>|:)\s*["\']([0-9a-f-]{36})["\']'
        no_changes_regex = r'\s*\{\s*"message"\s*(?:=>|:)\s*"(?:\\.|[^"\\])*"\s*\}\s*'
        task_id = search(task_id_regex, body)
        if task_id:
            task_id = task_id.group(1)
            if task_ids is not None and task_id not in task_ids:
                task_ids.append(task_id)
        output = cls._handle_response(response, ignore_stderr=True)
        if task_id:
            # Broker's SSH bindings interpret numeric timeouts as milliseconds.
            cls.execute(f'task progress --id="{task_id}"', timeout=timeout * 1000)
        # A successful no-change response contains only a translated message.
        elif not match(no_changes_regex, body):
            if isinstance(task_ids, AnsibleSyncTasks):
                task_ids.discover()
            raise CLIError('Could not identify the Ansible role sync task in Hammer debug output')
        return output

    @classmethod
    def roles_delete(cls, options=None):
        """Delete Ansible roles"""
        cls.command_sub = 'roles delete'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def roles_list(cls, options=None):
        """List ansible roles"""
        cls.command_sub = 'roles list'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def variables_import(cls, options=None):
        """Import ansible variables"""
        cls.command_sub = 'variables import'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def variables_create(cls, options=None):
        """Create ansible variables"""
        cls.command_sub = 'variables create'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def variables_delete(cls, options=None):
        """Delete ansible variables"""
        cls.command_sub = 'variables delete'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def variables_info(cls, options=None):
        """Information about ansible variables"""
        cls.command_sub = 'variables info'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def variables_list(cls, options=None):
        """Information about ansible variables"""
        cls.command_sub = 'variables list'
        return cls.execute(cls._construct_command(options), output_format='csv')
