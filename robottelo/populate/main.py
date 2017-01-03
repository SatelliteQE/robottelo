# coding: utf8

import import_string
import os
import yaml

from robottelo.populate.constants import DEFAULT_CONFIG

base_path = os.path.join('tests', 'foreman', 'data')


def load_data(datafile):
    """Loads YAML file as a dictionary"""
    if not datafile.startswith('/'):
        datafile = os.path.join(base_path, datafile)
    with open(datafile) as datafile:
        return yaml.load(datafile)


def get_populator(data, verbose):
    config = DEFAULT_CONFIG.copy()
    config.update(data.get('config', {}))
    verbose = verbose or config.get('verbose')

    populator_name = config['populator']
    populator_module_name = config['populators'][populator_name]['module']
    populator_class = import_string(populator_module_name)
    populator = populator_class(data=data, verbose=verbose)
    return populator


def populate(data, **extra_options):
    """Given the populate_method populates the system
    using data values
    """

    if not isinstance(data, dict):
        data = load_data(data)

    verbose = extra_options.get('verbose')
    populator = get_populator(data, verbose)
    populator.execute(mode='populate')
    return populator


def validate(data, **extra_options):
    """Given the populate_method validates the system
    using data values
    """

    if not isinstance(data, dict):
        data = load_data(data)

    verbose = extra_options.get('verbose')
    populator = get_populator(data, verbose)
    populator.execute(mode='validate')

    return populator
