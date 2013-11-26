#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from lib.common.helpers import csv_to_dictionary


class Architecture(Base):

    def __init__(self, conn):
        self.conn = conn

    def add_operating_system(self, arch_id, name, operating_system_id):
        """
        Adds existing OS to architecture.
        """

        cmd = "architecture add_operatingsystem"

        if arch_id:
            cmd += " --id=%s " % arch_id
        if name:
            cmd += " --name='%s'" % name

        cmd += " --operatingsystem-id=%s" % operating_system_id

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def architecture(self, name):
        """
        Search for architecture by name.
        """

        archs = self.list()
        match = [arch for arch in archs if name in arch['Name']]

        if match:
            match = match[0]

        return match

    def create(self, name, operating_system_id=None):
        """
        Creates a new architecture.
        """

        cmd = "architecture create --name='%s' " % name

        if operating_system_id:
            cmd += " --operatingsystem-ids=%s" % operating_system_id

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def delete(self, arch_id=None, name=None):
        """
        Deletes an existing architecture.
        """

        cmd = "architecture delete"

        if arch_id:
            cmd += " --id=%s" % arch_id
        if name:
            cmd += " --name='%s'" % name

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def exists(self, name):
        """
        Returns True or False depending whether the architecute exists
        in the system or not.
        """

        archs = self.list()
        return name in [
            arch['Name'] for arch in archs
        ]

    def info(self, arch_id=None, name=None):
        """
        Gets information about existing architecture.
        """

        cmd = "architecture info"

        if arch_id:
            cmd += " --id=%s" % arch_id
        if name:
            cmd += " --name='%s'" % name

        archs = {}

        stdout, stderr = self.execute(cmd)

        if stdout:
            archs = csv_to_dictionary(stdout)

        return archs

    def list(self, per_page=10000):
        """
        Lists all existing Archs.
        """

        # Returns up to 10000 hits to avoid pagination.
        cmd = "architecture list --per-page %d" % per_page

        archs = []

        stdout, stderr = self.execute(cmd)

        if stdout:
            archs = csv_to_dictionary(stdout)

        return archs

    def remove_operating_system(self, arch_id, name, operating_system_id):
        """
        Removes OS from architecture.
        """

        cmd = "architecture remove_operatingsystem"

        if arch_id:
            cmd += " --id=%s " % arch_id
        if name:
            cmd += " --name='%s'" % name

        cmd += " --operatingsystem-id=%s" % operating_system_id

        stdout, stderr = self.execute(cmd)

        return False if stderr else True

    def update(self, arch_id, name=None, new_name=None,
               operating_system_ids=None):
        """
        Updates existing architecture.
        """

        cmd = "architecture update"

        if arch_id:
            cmd += " --id='%s'" % arch_id
        if name:
            cmd += " --name='%s'" % name
        if new_name:
            cmd += " --new-name='%s'" % new_name
        if operating_system_ids:
            cmd += " --operatingsystem-ids=%s" % operating_system_ids

        stdout, stderr = self.execute(cmd)

        return False if stderr else True
