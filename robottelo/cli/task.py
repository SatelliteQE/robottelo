"""
Usage::

    hammer task [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    list                          List tasks
    progress                      Show the progress of the task
    resume                        Resume all tasks paused in error state
"""
from robottelo.cli.base import Base


class Task(Base):
    """
    Manipulates Foreman's task.
    """

    command_base = 'task'

    @classmethod
    def progress(cls, options=None, return_raw_response=None):
        """Shows a task progress

        Usage::
            hammer task progress [OPTIONS]

        Options::
            --id ID                       UUID of the task
            --name NAME                   Name to search by
        """
        cls.command_sub = 'progress'
        return cls.execute(cls._construct_command(options), return_raw_response=return_raw_response)

    @classmethod
    def resume(cls, options=None):
        """Resumes a task

        Usage:
            hammer task resume [OPTIONS]

        Options:
            --search SEARCH               Resume tasks matching search string
            --task-ids TASK_IDS           Comma separated list of values.
            --tasks TASK_NAMES            Comma separated list of values.
        """
        cls.command_sub = 'resume'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def list_tasks(cls, options=None):
        """List tasks

        Usage:
            hammer task list [OPTIONS]

        Options:
            --search SEARCH               List tasks matching search string
        """
        cls.command_sub = 'list'
        return cls.execute(cls._construct_command(options), output_format='csv')
