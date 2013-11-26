#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.common.helpers import generate_name
from lib.common.helpers import generate_string


class Organization(BaseCLI):

    def _create_organization(self, org_name, admin=None):

        admin=admin
        org_name = org_name or generate_string('alpha', 6)
        
        self.organization.create(
            org_name)
        self.assertTrue(self.organization.exists(org_name))

    def test_create_organization_1(self):
        "Successfully creates a new organization"

        org_name = generate_string('alpha', 6)
        self._create_organization(org_name, None)

    def test_delete_organization_1(self):
        "Creates and immediately deletes organization."

        org_name = generate_string('alpha', 6)
        self._create_organization(org_name)

        self.organization.delete(org_name)
        self.assertFalse(self.organization.exists(org_name))

    def test_create_organization_utf8(self):
        "Create utf8 organization"

        org_name = generate_string('utf8', 6).encode('utf-8')
        self._create_organization(org_name, None)
    
    def test_create_user_latin1(self):
        "Create latin1 organization"

        org_name = generate_string('latin1', 6).encode('utf-8')
        self._create_organization(org_name, None)

