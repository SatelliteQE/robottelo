# coding: utf-8
"""Constants for populate"""

ACTIONS_CRUD = ('create', 'update', 'delete')
ACTIONS_SPECIAL = ('register', 'unregister', 'assertion')

DEFAULT_CONFIG = {
    'populator': 'api',
    'populators': {
        'api': {
            'module': 'robottelo.populate.api.APIPopulator'
        }
    },
    'verbose': 0
}

FORCE_RAW_SEARCH = ['organization', 'user']

LOGGERS = {
    'root': 'root',
    'nailgun': 'nailgun',
    'robottelo': 'robottelo',
    'ssh': 'robottelo.ssh'
}

RAW_SEARCH_RULES = {
    'user': {
        'organization': {
            'rename': 'organization_id',
            'attr': 'id',
            'index': 0,
            # 'key': 'name_of_key'
        },
        'password': {'remove': True},
        'default_organization': {'remove': True}
    },
    'repository': {
        'url': {'remove': True},
    }
}
