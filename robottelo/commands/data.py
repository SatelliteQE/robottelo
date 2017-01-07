# coding: utf-8
"""
This module contains commands to interact with data populator
and validator.

Commands included:

populate
--------

A command to populate the system based in an YAML file describing the
entities::

    $ manage data populate /path/to/file.yaml -vv

validate
--------

A command to validate the system based in an YAML file describing the
entities::

    $ manage data validate /path/to/file.yaml -vv

Use :code:`$ manage data --help` and
:code:`$ manage data populate --help` for more info
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
        example: $ manage data populate test_data.yaml -vv\n

    verbosity:\n
       -v = INFO (only info)\n
       -vv = DEBUG\n
       -vvv = WARNING\n
       -vvvv = ERROR\n
       -vvvvv = CRITICAL\n
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
        example: $ manage data populate test_data.yaml -vv\n

    verbosity:\n
       -v = DEBUG\n
       -vv = INFO\n
       -vvv = WARNING\n
       -vvvv = ERROR\n
       -vvvvv = CRITICAL\n

    """

    result = execute_validate(datafile, verbose=verbose)
    result.logger.warning('testing')
    result.logger.critical('testing')
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
