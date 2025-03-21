"""
Usage::

    arf-report [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

     SUBCOMMAND                    subcommand
     [ARG] ...                     subcommand arguments

Subcommands::
     delete                        Delete an ARF Report
     download                      Download bzipped ARF report
     download-html                 Download ARF report in HTML
     info                          Show an ARF report
     list                          List ARF reports

"""

from robottelo.cli.base import Base


class Arfreport(Base):
    """Manipulates Satellite's arf-report."""

    command_base = 'arf-report'

    @classmethod
    def list(cls, options=None):
        """Search arf host reports

        Usage::

            hammer arf-report list [OPTIONS]

        Options::

             --location LOCATION_NAME                Location name
             --location-id LOCATION_ID
             --location-title LOCATION_TITLE         Location title
             --order ORDER                           Sort field and order, eg. ‘id DESC’
             --organization ORGANIZATION_NAME        Organization name
             --organization-id ORGANIZATION_ID       Organization ID
             --organization-title ORGANIZATION_TITLE Organization title
             --page PAGE                             Paginate results
             --per-page PER_PAGE                     Number of entries per request
             --search SEARCH                         Filter results
             -h, --help                              Print help

        """
        cls.command_sub = 'list'

        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def downloadhtml(cls, options=None):
        """Download arf report as a file

        Usage:
            hammer arf-report download-html [OPTIONS]

        Options:
         --id VALUE
         --location[-id] VALUE/NUMBER     Set the current location context for the request
         --organization[-id] VALUE/NUMBER Set the current organization context for the request
         --path VALUE                     Path to directory where downloaded file will be saved
         -h, --help                       Print help

        """
        cls.command_sub = 'download-html'

        return cls.execute(cls._construct_command(options), output_format='csv')[0]
