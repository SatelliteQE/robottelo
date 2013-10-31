#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base

class User(Base):

    def __init__(self, conn):
        self.conn = conn

    def users(self):
        return self.execute("user list -g --noheading")

    def user(self, username):
        stdout, stderr = self.users()

        user = [user for user in stdout if username in user]

        return user

    def assign_role(self):
        pass

    def create(self, name, password, email, disabled='false', org=None, env=None, locale=None):

        cmd = "user create --username='%s' --password='%s' --email='%s' --disabled='%s'" % (name, password, email, disabled)

        if org:
            cmd =+ " --default_organization='%s'" % org
        if env:
            cmd += " --default_environment='%s'" % env
        if locale:
            cmd += " --default_locale='%s'" % locale

        cmd += " -g --noheading"

        stdout, stderr = self.execute(cmd)

        if stderr:
            return False
        else:
            return True

    def delete(self):
        pass

    def info(self):
        pass

    def list(self):
        pass

    def list_roles(self):
        pass

    def report(self):
        pass

    def sync_ldap_roles(self):
        pass

    def unassign_role(self):
        pass

    def update(self):
        pass
