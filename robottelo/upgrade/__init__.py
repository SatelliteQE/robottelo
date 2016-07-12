# -*- encoding: utf-8 -*-
"""Implements Upgrade functions."""
import yaml

from robottelo.config import settings
from robottelo.helpers import download_server_file


def get_all_yaml_data():
    """Downloads and fetches all data from YAML file.

    :return: Dict type contains data fetched from yaml in the form of
        {node:{subnode:{fields:data}}}
    """
    yaml_path = download_server_file('yml', settings.upgrade.upgrade_data)
    with open(yaml_path) as handler:
        yamldata = yaml.load(handler)
    return yamldata


def get_yaml_field_value(section, subsection, field, default=None):
    """Fetches field value from dict format of yaml file

    :param str section: Topmost section of yaml file
    :param str subsection: Second most section under top of yaml file
    :param str field: Field under second most section of yaml file of which
        value will be fetched
    :return: String/List for given field e.g id of org
    """
    try:
        yamldata = get_all_yaml_data()
        if field not in yamldata[section][subsection]:
            return
        result = yamldata[section][subsection][field]
    except KeyError:
        result = default
    return result
