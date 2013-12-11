#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.user import User
from lib.common.helpers import generate_name


def make_user(override_args=None):
    """
    Override the parameters login, firstname, lastname, mail, admin, password,
    auth-source-id by passing them as a dictionary object from the caller
    """
    login = override_args['login'] or generate_name(6)

    #Assigning default values for attributes
    args = {
            'login': generate_name(6),
            'firstname': generate_name(),
            'lastname': generate_name(),
            'mail': "%s@example.com" % login,
            'admin': None,
            'password': generate_name(),
            'auth-source-id': 1,
        }

    #Update the dict with user overrides if any
    if override_args is not None:
        args.update(override_args)

    User().create(args)

    if User().exists(login):
        return args
    else:
        return None
