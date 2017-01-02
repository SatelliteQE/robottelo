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
from robottelo.populate.main import load_data
from robottelo.populate.main import populate as execute_populate
from robottelo.populate.main import validate as execute_validate


@click.command()
@click.argument('datafile', required=True, type=click.Path())
def populate(datafile):
    """Populate using the data described in `datafile`:\n
    populated the system with needed entities.\n
        example: $ manage data populate test_data.yaml\n
    """
    data = load_data(datafile)
    result = execute_populate(data)
    result.logger.info(
        "{0} entities already existing in the system".format(
            result.total_existing
        )
    )
    result.logger.info(
        "{0} entities were created in the system".format(
            result.total_created
        )
    )


@click.command()
@click.argument('datafile', required=True, type=click.Path())
def validate(datafile):
    """Validate using the data described in `datafile`:\n
    populated the system with needed entities.\n
        example: $ manage data populate test_data.yaml\n
    """
    data = load_data(datafile)
    result = execute_validate(data)

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
            "{0} entities found in the system".format(
                result.total_existing
            )
        )
