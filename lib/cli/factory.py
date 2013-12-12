#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.user import User
from lib.common.helpers import generate_name
import logging.config

logger = logging.getLogger("robottelo")


def make_user(self, override_args=None):
    """
    @param override_args: override dictionary object which may have one or more
    of the following key items
            login
            firstname
            lastname
            mail
            admin
            password
            auth-source-id
    @return args: dictionary object with all the above key items
    """
    login = generate_name(6)

    #Assigning default values for attributes
    args = {
            'login': login,
            'firstname': generate_name(),
            'lastname': generate_name(),
            'mail': "%s@example.com" % login,
            'admin': None,
            'password': generate_name(),
            'auth-source-id': 1,
        }

    #Update the dict with user overrides if any
    try:
        if override_args:
            for key, val in override_args.items():
                if key in args.keys():
                    args[key] = val
            result = User().create(args)
            # Check 1 - retcode
            if result.return_code is 0:
                # Check 2 - checking .exists()
                if User().exists(login):
                    return args
                else:
                    raise Exception("Failed to create User")
            else:
                raise Exception("Failed to create User")
    except Exception, e:
            logger.error("ERROR: %s" % str(e))
            return None
