"""
Usage::

    hammer template-input [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    Subcommand
    [ARG] ...                     Subcommand arguments

Subcommands::

    create                        Create a template input
    delete                        Delete a template input
    info                          Show template input details
    list                          List template inputs
"""

from robottelo.cli.base import Base, CLIError


class TemplateInput(Base):
    """
    Manipulates template input.
    """

    command_base = 'template-input'

    @classmethod
    def create(cls, options=None, timeout=None):
        """
        Creates a new record using the arguments passed via dictionary.
        """

        cls.command_sub = 'create'

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options), output_format='csv', timeout=timeout)

        # Extract new object ID if it was successfully created
        if len(result) > 0 and 'id' in result[0]:
            obj_id = result[0]['id']

            # Fetch new object
            # Some Katello obj require the organization-id for subcommands
            info_options = {'id': obj_id, 'template-id': options['template-id']}
            if cls.command_requires_org:
                if 'organization-id' not in options:
                    tmpl = 'organization-id option is required for {0}.create'
                    raise CLIError(tmpl.format(cls.__name__))
                info_options['organization-id'] = options['organization-id']

            new_obj = cls.info(info_options)
            # stdout should be a dictionary containing the object
            if len(new_obj) > 0:
                result = new_obj

        return result
