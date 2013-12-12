#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import lib.api.users as user
import unittest
from tests.api.baseapi import assertFeaturing
from lib.common.helpers import generate_name
from lib.common.helpers import generate_email_address


class User(unittest.TestCase):

    def test_create_user(self):
        "Create a new User"
        name = unicode(generate_name(6))
        password = unicode(generate_name(8))
        email = unicode(generate_email_address())
        opts = {u'user' : {u'login' : name,
			  u'password' : password,
			  u'mail' : email,
              u'auth_source_id' : 1
			}}
        result = user.create(opts)
        del opts[u'user'][u'password']
        assertFeaturing(opts, result)

