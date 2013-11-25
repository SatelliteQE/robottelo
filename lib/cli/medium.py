#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from lib.common.helpers import csv_to_dictionary


class Medium(Base):

    def __init__(self, conn):
        self.conn = conn

    def add_operating_system(self, medium_id, name, operating_system_id):
        """
        Adds existing OS to medium.
        """

        cmd = "medium add_operatingsystem"

        if medium_id:
            cmd += " --id=%s" % medium_id
        if name:
            cmd += " --name='%s'" % name

        cmd += " --operatingsystem-id=%s" % operating_system_id

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def medium(self, name):
        """
        Search for medium by name.
        """

        medium = self.list()
        match = [media for media in medium if name in media['Name']]

        if match:
            match = match[0]

        return match

    def create(self, name, path, os_family=None, operating_system_ids=None):
        """
        Creates a new medium.
        """

        cmd = "medium create --name='%s' --path='%s'" % (name, path)

        if os_family:
            cmd += " --os-family='%s'" % os_family

        if operating_system_ids:
            cmd += " --operatingsystem-ids=%s" % operating_system_ids

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def delete(self, medium_id=None, name=None):
        """
        Deletes an existing medium.
        """

        cmd = "medium delete"

        if medium_id:
            cmd += " --id=%s" % medium_id
        if name:
            cmd += " --name='%s'" % name

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def exists(self, name):
        """
        Returns True or False depending whether the medium exists
        in the system or not.
        """

        medium = self.list()
        return name in [
            media['Name'] for media in medium
        ]

    def info(self, medium_id=None, name=None):
        """
        Gets information about existing medium.
        """

        cmd = "medium info"

        if medium_id:
            cmd += " --id=%s" % medium_id
        if name:
            cmd += " --name='%s'" % name

        medium = {}

        stdout, stderr = self.execute(cmd)

        if stdout:
            medium = csv_to_dictionary(stdout)

        return medium

    def list(self, per_page=10000):
        """
        Lists all existing Medium.
        """

        # Returns up to 10000 hits to avoid pagination.
        cmd = "medium list --per-page %d" % per_page

        medium = []

        stdout, stderr = self.execute(cmd)

        if stdout:
            medium = csv_to_dictionary(stdout)

        return medium

    def remove_operating_system(self, medium_id, name, operating_system_id):
        """
        Removes OS from medium.
        """

        cmd = "medium remove_operatingsystem"

        if medium_id:
            cmd += " --id=%s" % medium_id
        if name:
            cmd += " --name='%s'" % name

        cmd += " --operatingsystem-id=%s" % operating_system_id

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def update(self, medium_id, name=None, new_name=None,
               operating_system_ids=None):
        """
        Updates existing medium.
        """

        cmd = "medium update"

        if medium_id:
            cmd += " --id='%s'" % medium_id
        if name:
            cmd += " --name='%s'" % name
        if new_name:
            cmd += " --new-name='%s'" % new_name
        if operating_system_ids:
            cmd += " --operatingsystem-ids=%s" % operating_system_ids

        stdout, stderr = self.execute(cmd)

        return False if stderr else True
