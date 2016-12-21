# coding: utf8

import os
import yaml
from robottelo.config import settings
from robottelo.populate.api import APIPopulator
from robottelo.populate.cli import CLIPopulator


base_path = os.path.join('tests', 'foreman', 'data')


def load_data(datafile):
    """Loads YAML file as a dictionary"""
    if not datafile.startswith('/'):
        datafile = os.path.join(base_path, datafile)
    with open(datafile) as datafile:
        return yaml.load(datafile)


def populate(data, **extra_options):
    """Given the populate_method populates the system
    using data values
    """
    if not settings.configured:
        settings.configure()

    if settings.populate_method == 'api':
        populator = APIPopulator(data=data)
    else:
        populator = CLIPopulator(data=data)

    populator.execute()
