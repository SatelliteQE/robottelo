"""
Export

Usage::
    hammer export-templates [OPTIONS]

Options::
    branch                        Branch in Git repo.
    commit-msg                    Custom commit message for templates export
    dirname                       The directory within Git repo containing the templates
    filter                        Export templates with names matching this regex ( \
                                  case-insensitive; snippets are not filtered).
    location[-id|-title]          Name/Title/Id of associated location
    location[s|-ids|-titles]      REPLACE locations with given Names/Titles/Ids
    metadata-export-mode          Specify how to handle metadata
    negate                        Negate the prefix (for purging).
    organization[-id|-title]      Name/Title/Id of associated organization
    organization[s|-ids|-titles]  REPLACE organizations with given Names/Titles/Ids.
    repo                          Override the default repo from settings.


Import

Usage::
    hammer import-templates [OPTIONS]

Options::
    associate                     Associate to OS's, Locations & Organizations. Options are: always
    branch                        Branch in Git repo.
    dirname                       The directory within Git repo containing the templates
    filter                        Export templates with names matching this regex
    force                         Update templates that are locked
    location[-id|-title]          Name/Title/Id of associated location
    location[s|-ids|-titles]      REPLACE locations with given Names/Titles/Ids
    lock                          Lock imported templates
    negate                        Negate the prefix (for purging).
    organization[-id|-title]      Name/Title/Id of associated organization
    organization[s|-ids|-titles]  REPLACE organizations with given Names/Titles/Ids.
    prefix                        The string all imported templates should begin with.
    repo                          Override the default repo from settings.
"""

from robottelo.cli.base import Base


class TemplateSync(Base):
    """Export/Import Satellite Templates to Git/Local Directory."""

    @classmethod
    def exports(cls, options=None):
        """Export Satellite Templates to Git/Local Directory."""
        cls.command_base = 'export-templates'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def imports(cls, options=None):
        """Import Satellite Templates to Git/Local Directory."""
        cls.command_base = 'import-templates'

        return cls.execute(cls._construct_command(options))
