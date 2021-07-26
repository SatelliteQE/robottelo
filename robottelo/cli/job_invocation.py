"""
Usage:
    hammer job-invocation [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 cancel                        Cancel the job
 create                        Create a job invocation
 info                          Show job invocation
 list                          List job invocations
 output                        View the output for a host
 rerun                         Rerun the job

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

    @classmethod
    def create(cls, options):
        """Create a job"""
        cls.command_sub = 'create'
        return cls.execute(cls._construct_command(options), output_format='csv')
