#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base

FIELDS = ['id', 'username', 'email', 'disabled', 'org', 'env', 'locale']

class User(Base):

    def __init__(self, conn):
        self.conn = conn

    def assign_role(self, username, rolename):
        cmd = "user assign_role --username='%s' --role='%s'"

        stdout, stderr = self.execute(cmd % (username, rolename))

        return False if stderr else True

    def create(self, name, password, email, disabled='false', org=None, env=None, locale=None):
        cmd = "user create --username='%s' --password='%s' --email='%s' --disabled='%s'"
        cmd = cmd % (name, password, email, disabled)

        if org:
            cmd =+ " --default_organization='%s'" % org
        if env:
            cmd += " --default_environment='%s'" % env
        if locale:
            cmd += " --default_locale='%s'" % locale

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def delete(self, username):
        cmd = "user delete --username='%s'"

        stdout, stderr = self.execute(cmd % username)

        return False if stderr else True

    def info(self, username):
        cmd = "user info --username='%s'"

        user = {}

        stdout, stderr = self.execute(cmd % username)

        if stdout:
            for key, value in zip(FIELDS, "".join(stdout).split()):
                user[key] = value
        return user

    def list(self):
        cmd = "user list"

        users = []

        stdout, stderr = self.execute(cmd)

        if stdout:
            for entry in stdout:
                user = {}
                for key, value in zip(FIELDS, "".join(entry).split()):
                    user[key] = value
                users.append(user)
        return users

    def list_roles(self, username):
        cmd = "user list_roles --username='%s'"

        roles = []

        stdout, stderr = self.execute(cmd % username)

        if stdout:
            for entry in stdout:
                role = {}
                for key, value in zip(['id', 'name'], "".join(entry).split()):
                    role[key] = value
                roles.append(role)
        return roles

    def report(self):
        pass

    def sync_ldap_roles(self):
        pass

    def unassign_role(self, username, rolename):
        cmd = "user unassign_role --username='%s' --role='%s'"

        stdout, stderr = self.execute(cmd % (username, rolename))

        return False if stderr else True

    def update(self, username, password=None, email=None, disabled=None, org=None, env=None, locale=None):
        cmd = "user update --username='%s'" % username

        if password:
            cmd += " --password='%s'" % password
        if email:
            cmd += " --email='%s'" % email
        if disabled:
            cmd += " --disabled='%s'" % disabled
        if org:
            cmd += " --default_organization='%s'" % org
        if env:
            cmd += " --default_environment='%s'" % env
        if locale:
            cmd += " --default_locale='%s'" % locale

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

