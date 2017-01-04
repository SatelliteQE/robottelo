# coding: utf-8
"""
This module contains commands to interact with data populator
and validator.

Commands included:

populate
--------

A command to populate the system based in an YAML file describing the
entities::

    $ manage data populate /path/to/file.yaml

validate
--------

A command to validate the system based in an YAML file describing the
entities::

    $ manage data validate /path/to/file.yaml

"""
import sys
import click
from robottelo.populate.main import populate as execute_populate
from robottelo.populate.main import validate as execute_validate


@click.command()
@click.argument('datafile', required=True, type=click.Path())
@click.option('-v', '--verbose', count=True)
def populate(datafile, verbose):
    """Populate using the data described in `datafile`:\n
    populated the system with needed entities.\n
        example: $ manage data populate test_data.yaml\n

    verbosity:
       0 (omit all logs)
       1 -v (show populate logs)
       2 -vv (include nailgun logs)
       3 -vvv (include ssh logs)
    """
    result = execute_populate(datafile, verbose=verbose)
    result.logger.info(
        "{0} entities already existing in the system".format(
            len(result.found)
        )
    )
    result.logger.info(
        "{0} entities were created in the system".format(
            len(result.created)
        )
    )


@click.command()
@click.argument('datafile', required=True, type=click.Path())
@click.option('-v', '--verbose', count=True)
def validate(datafile, verbose):
    """Validate using the data described in `datafile`:\n
    populated the system with needed entities.\n
        example: $ manage data populate test_data.yaml\n

    verbosity:
       0 (omit all logs)
       1 -v (show populate logs)
       2 -vv (include nailgun logs)
       3 -vvv (include ssh logs)

    """

    result = execute_validate(datafile, verbose=verbose)

    if result.assertion_errors:
        for error in result.assertion_errors:
            data = error['data']
            result.logger.error(
                'assertion: %s is NOT %s to %s',
                data['value'], error['operator'], data['other']
            )
        sys.exit("System entities did not validated!")

    if result.validation_errors:
        for error in result.validation_errors:
            result.logger.error(error['message'])
            result.logger.error(error['search_query'])
        sys.exit("System entities did not validated!")
    else:
        result.logger.info(
            "{0} entities validated in the system".format(
                len(result.found)
            )
        )
