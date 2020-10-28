# -*- encoding: utf-8 -*-
"""
Usage:
    hammer job-invocation [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND      subcommand
    [ARG] ...       subcommand arguments

Subcommands:

    create          Create a job invocation
    info            Show job invocation
    list            List job invocations
    output          View the output for a host
"""
from robottelo.cli.base import Base


class JobInvocation(Base):
    """
    Run remote jobs.
    """

    command_base = 'job-invocation'

    @classmethod
    def get_output(cls, options):
        """Get output of the job invocation"""
        cls.command_sub = 'output'
        return cls.execute(cls._construct_command(options))
