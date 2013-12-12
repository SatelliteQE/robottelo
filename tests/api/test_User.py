#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import lib.api.users as user
from tests.api.baseapi import BaseAPI, assertFeaturing
from lib.common.helpers import generate_name
from lib.common.helpers import generate_email_address


class User(BaseAPI):
    """Testing /api/user entrypoint"""

    def test_create_user(self):
        """Create a new User"""
        name = unicode(generate_name(6))
        password = unicode(generate_name(8))
        email = unicode(generate_email_address())
        opts = {u'user' : {u'login' : name,
			  u'password' : password,
			  u'mail' : email,
              u'auth_source_id' : 1
			}}
        result = user.raw_create(opts)
        del opts[u'user'][u'password']
        self.assertEqual(result.status_code, 200)
        assertFeaturing(opts, result.json())

