"""
Usage::

    hammer report-template [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    Subcommand
    [ARG] ...                     Subcommand arguments

Subcommands::

    clone                         Clone a template
    create                        Create a report template
    delete                        Delete a report template
    dump                          View report content
    generate                      Generate report
    info                          Show a report template
    list                          List all report templates
    report-data                   Downloads a generated report
    schedule                      Schedule generating of a report
    update                        Update a report template
"""
from os import chmod
from tempfile import mkstemp

from robottelo import ssh
from robottelo.cli.base import Base
from robottelo.cli.base import CLIError
from robottelo.constants import DataFile
from robottelo.constants import REPORT_TEMPLATE_FILE


class ReportTemplate(Base):
    """Manipulates with Report Template"""

    command_base = 'report-template'

    @classmethod
    def create(cls, options=None):
        """
        Creates a new record using the arguments passed via dictionary.
        """

        cls.command_sub = 'create'

        if options is None:
            options = {}

        if options['file'] is None:
            tmpl = 'file content is required for {0}.creation'
            raise CLIError(tmpl.format(cls.__name__))

        if options['file'] == REPORT_TEMPLATE_FILE:
            local_path = DataFile.REPORT_TEMPLATE_FILE
        else:
            local_path = ''

        # --- create file at remote machine --- #
        (_, layout) = mkstemp(text=True)
        chmod(layout, 0o700)

        if not local_path:
            with open(layout, 'w') as rt:
                rt.write(options['file'])
            # End - Special handling of temporary file
        else:
            with open(local_path) as file:
                file_data = file.read()
            with open(layout, 'w') as rt:
                rt.write(file_data)
        ssh.get_client().put(layout, layout)
        # -------------------------------------- #

        options['file'] = layout

        result = cls.execute(cls._construct_command(options), output_format='csv')

        # Extract new object ID if it was successfully created
        if len(result) > 0 and 'id' in result[0]:
            obj_id = result[0]['id']

            # Fetch new object
            # Some Katello obj require the organization-id for subcommands
            info_options = {'id': obj_id}
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

    @classmethod
    def generate(cls, options=None):
        """Generate a report"""
        cls.command_sub = 'generate'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def clone(cls, options=None):
        """Clone a report template"""
        cls.command_sub = 'clone'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def report_data(cls, options=None):
        """Downloads a generated report"""
        cls.command_sub = 'report-data'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def schedule(cls, options=None):
        """Schedule generating of a report"""
        cls.command_sub = 'schedule'
        return cls.execute(cls._construct_command(options))
