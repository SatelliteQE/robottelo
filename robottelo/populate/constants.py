# coding: utf-8
"""Default base config values"""
from robottelo.populate.utils import SmartDict


REQUIRED_MODULES = {
    'fauxfactory': 'fauxfactory',
    'env': 'os.environ'
}

RAW_SEARCH_RULES = {
    # force Organization to always perform raw_search
    'organization': {'_force_raw': True},
    'user': {
        '_force_raw': True,
        'organization': {
            # rename organization Entity to organization_id
            'rename': 'organization_id',
            # and get the attr 'id' from object
            'attr': 'id',
            # using object in index 0 (because it is a list)
            'index': 0,
            # if was dict key_name here
            # 'key': 'name_of_key'
        },
        # remove fields from search
        'password': {'remove': True},
        'default_organization': {'remove': True}
    },
    'repository': {
        'url': {'remove': True},
    }
}

DEFAULT_CONFIG = SmartDict({
    'populator': 'api',
    'populators': {
        'api': {
            'module': 'robottelo.populate.api.APIPopulator'
        }
    },
    'verbose': 0
})
