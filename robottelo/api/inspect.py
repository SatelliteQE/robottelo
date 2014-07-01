"""This module contains functions that ease the process of inpecting API
information from the Foreman server.

"""
import requests

from robottelo.common.helpers import get_server_url
from urlparse import urljoin


def get_api_doc():
    """Go to Foreman server and grabs and returns its apidoc information

    :return: A dictionary with the apidoc information
    :rtype: dict

    """
    response = requests.get(
        urljoin(get_server_url(), '/apidoc/v2.json'), verify=False)
    return response.json()['docs']


def get_resource_create_info(api_doc=None):
    """Returns just the relevant API resources creation information from
    ``api_doc``.

    If ``api_doc`` is not provided it will request it from the server.

    :return: A dictionary with the API resources creation information
    :rtype: dict

    """
    if api_doc is None:
        api_doc = get_api_doc()

    entities = {}

    for resource in api_doc['resources']:
        for method in api_doc['resources'][resource]['methods']:
            if method['name'] == u'create':
                entities[resource] = {}
                entities[resource]['apis'] = method['apis']
                entities[resource]['params'] = method['params']
    return entities
