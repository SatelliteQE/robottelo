# coding: utf8

import os
import yaml

base_path = os.path.join('tests', 'foreman', 'data')


def load_data(datafile):
    if not datafile.startswith('/'):
       datafile = os.path.join(base_path, datafile)
    with open(datafile) as datafile:
        return yaml.load(datafile)


def populate(data, **extra_options):
    print data