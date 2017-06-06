# coding: utf8
"""Point of entry for populate and validate used in scripts"""
import import_string
import os
import yaml

from robottelo.populate.constants import DEFAULT_CONFIG

base_path = os.path.join('tests', 'foreman', 'data')


def load_data(datafile):
    """Loads YAML file as a dictionary"""
    if datafile.endswith(('.yml', '.yaml', 'json')):
        if not datafile.startswith('/'):
            datafile = os.path.join(base_path, datafile)
        with open(datafile) as datafile:
            return yaml.load(datafile)
    return yaml.load(datafile)


def get_populator(data, verbose):
    """Gets an instance of populator dynamically"""
    if not isinstance(data, dict):
        data = load_data(data)

    config = DEFAULT_CONFIG.copy()
    config.update(data.get('config', {}))
    verbose = verbose or config.get('verbose')

    populator_name = config['populator']
    populator_module_name = config['populators'][populator_name]['module']
    populator_class = import_string(populator_module_name)
    populator = populator_class(data=data, verbose=verbose, config=config)
    return populator


def populate(data, **extra_options):
    """Loads and execute populator in populate mode"""
    verbose = extra_options.get('verbose')
    populator = get_populator(data, verbose)
    populator.execute(mode='populate')
    populator.logger.info("Populator finished!")
    return populator


def validate(data, **extra_options):
    """Loads and execute populator in validate mode"""
    verbose = extra_options.get('verbose')
    populator = get_populator(data, verbose)
    populator.execute(mode='validate')
    populator.logger.info("Validator finished!")
    return populator


def wrap_context(result):
    """Takes the result of populator and keeps only useful data
    e.g. in decorators context.registered_name, context.config.verbose and
    context.vars.admin_username will all be available.
    """
    context = result.registry
    context.config = result.config
    context.vars = result.vars
    return context
