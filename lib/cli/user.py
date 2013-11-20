#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from lib.common.helpers import csv_to_dictionary


class User(Base):

    def __init__(self, conn):
        self.conn = conn

    def user(self, user_name):
        """
        Search for a user by login.
        """

        users = self.list()
        match = [user for user in users if user_name in user['Login']]

        if match:
            match = match[0]

        return match

    def create(self, login, fname, lname, email, admin, password, auth_id=1):
        """
        Creates a new user.
        """

        cmd = "user create --login='%s' --firstname='%s' --lastname='%s'" \
              " --mail='%s' --admin='%s' --password='%s'" \
              " --auth-source-id='%d'"

        cmd = cmd % (login, fname, lname, email, admin, password, auth_id)

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def delete(self, user_id):
        """
        Deletes an existing user.
        """

        cmd = "user delete --id='%s'"

        stdout, stderr = self.execute(cmd % user_id)

        return False if stderr else True

    def info(self, user_id):
        """
        Gets information about existing user.
        """

        cmd = "user info --id='%s'"

        user = {}

        stdout, stderr = self.execute(cmd % user_id)

        if stdout:
            user = csv_to_dictionary(stdout)

        return user

    def list(self):
        """
        Lists all existing users.
        """

        cmd = "user list"

        users = []

        stdout, stderr = self.execute(cmd)

        if stdout:
            users = csv_to_dictionary(stdout)

        return users

    def update(self, user_id, login=None, fname=None, lname=None,
               email=None, admin=None, password=None):
        """
        Updates existing users.
        """

        cmd = "user update --id='%s'" % user_id

        if login:
            cmd += " --login='%s'" % login
        if fname:
            cmd += " --fname='%s'" % fname
        if lname:
            cmd += " --lname='%s'" % lname
        if email:
            cmd += " --mail='%s'" % email
        if admin:
            cmd += " --admin='%s'" % admin
        if password:
            cmd += " --password='%s'" % password

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def exists(self, user_name):
        """
        Returns True or False depending whether a user exists
        in the system or not.
        """

        users = self.list()
        return user_name in [
            user['Login'] for user in users
        ]
